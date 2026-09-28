import time
import sqlite3
import traceback
from typing import Callable, Any, Optional, Dict
from datetime import datetime, date
from pathlib import Path

from config.settings import settings
from utils.logger import logger


def classify_error(exc: Exception) -> str:
    """
    Classifies errors into operational categories:
    - TRANSIENT: Temporary glitch (timeout, 500/502/503/504, connection dropped) -> Safe to retry immediately or with short backoff.
    - QUOTA: Rate limit or daily allocation exceeded (429, ResourceExhausted, ZeroGPU) -> Wait or switch provider.
    - PERMANENT: Bad auth, permission denied, invalid request syntax (401, 403, 400) -> Do not retry.
    - DEGRADED: Partial processing failure.
    """
    msg = str(exc).lower()
    
    if any(k in msg for k in ["429", "resource_exhausted", "quota", "rate limit", "zerogpu", "exceeded"]):
        return "QUOTA"
    if any(k in msg for k in ["401", "403", "forbidden", "unauthorized", "invalid_api_key", "permission"]):
        return "PERMANENT"
    if any(k in msg for k in ["500", "502", "503", "504", "timeout", "timed out", "connection", "reset by peer", "broken pipe", "unavailable"]):
        return "TRANSIENT"
    
    return "TRANSIENT"


def resilient_call(
    func: Callable[..., Any],
    *args,
    max_retries: int = 3,
    backoff_base: float = 4.0,
    fallback_value: Any = None,
    error_category_override: Optional[str] = None,
    service_name: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Executes a callable with intelligent retries, backoff, and categorization.
    Ensures that a single failing service NEVER crashes the pipeline.
    """
    attempt = 0
    last_exception = None

    while attempt < max_retries:
        try:
            attempt += 1
            result = func(*args, **kwargs)
            if service_name:
                quota_tracker.record_use(service_name)
            return result
        except Exception as e:
            last_exception = e
            category = error_category_override or classify_error(e)
            logger.warning(
                f"[Resilience] Call '{func.__name__}' attempt {attempt}/{max_retries} failed. "
                f"Category: {category}. Error: {str(e)[:120]}"
            )

            if category == "PERMANENT":
                logger.error(f"[Resilience] Non-retryable error in '{func.__name__}': {e}")
                break

            if attempt >= max_retries:
                break

            sleep_time = backoff_base * (2 ** (attempt - 1))
            if category == "QUOTA":
                sleep_time = max(sleep_time, 30.0)

            logger.info(f"[Resilience] Backing off for {sleep_time:.1f}s before retry...")
            time.sleep(sleep_time)

    logger.error(f"[Resilience] All {max_retries} attempts failed for '{func.__name__}'. Falling back.")
    return fallback_value


class QuotaTracker:
    """
    Tracks and persists daily API quotas across sessions.
    Prevents hard stops by tracking usage and switching fallbacks proactively.
    """
    DAILY_LIMITS = {
        "gemini": 1500,
        "openrouter": 50,
        "pexels": 650,
        "hf_flux": 15,
        "edge_tts": 999999
    }

    def __init__(self):
        self.db_path = settings.LOGS_DIR / "studio_memory.db"
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute("""
                CREATE TABLE IF NOT EXISTS api_quotas (
                    date TEXT,
                    service TEXT,
                    used_count INTEGER DEFAULT 0,
                    PRIMARY KEY (date, service)
                )
            """)
            conn.commit()

    def _today(self) -> str:
        return date.today().isoformat()

    def can_use(self, service: str) -> bool:
        limit = self.DAILY_LIMITS.get(service, 1000)
        used = self.get_used(service)
        return used < limit

    def record_use(self, service: str, count: int = 1):
        today = self._today()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.cursor().execute("""
                    INSERT INTO api_quotas (date, service, used_count)
                    VALUES (?, ?, ?)
                    ON CONFLICT(date, service) DO UPDATE SET used_count = used_count + ?
                """, (today, service, count, count))
                conn.commit()
        except Exception as e:
            logger.warning(f"[QuotaTracker] Failed to record usage: {e}")

    def get_used(self, service: str) -> int:
        today = self._today()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT used_count FROM api_quotas WHERE date = ? AND service = ?",
                    (today, service)
                )
                row = cursor.fetchone()
                return row[0] if row else 0
        except Exception:
            return 0

    def get_remaining(self, service: str) -> int:
        limit = self.DAILY_LIMITS.get(service, 1000)
        return max(0, limit - self.get_used(service))

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        status = {}
        for srv, limit in self.DAILY_LIMITS.items():
            used = self.get_used(srv)
            status[srv] = {
                "used": used,
                "limit": limit,
                "remaining": max(0, limit - used),
                "healthy": used < limit
            }
        return status


class HealthWatchdog:
    """
    Monitors overall subsystem health, system resources, and service statuses.
    """
    def __init__(self):
        self.last_checked: Dict[str, datetime] = {}
        self.last_status: Dict[str, bool] = {}

    def get_system_health(self) -> Dict[str, Any]:
        import shutil
        disk = shutil.disk_usage(str(settings.BASE_DIR))
        temp_dir = Path("/tmp/autodirector_production")
        temp_size_mb = 0.0
        if temp_dir.exists():
            temp_size_mb = sum(f.stat().st_size for f in temp_dir.rglob('*') if f.is_file()) / (1024 * 1024)

        return {
            "disk_free_gb": round(disk.free / (1024 ** 3), 2),
            "disk_total_gb": round(disk.total / (1024 ** 3), 2),
            "disk_used_percent": round((disk.used / disk.total) * 100, 1),
            "temp_cache_mb": round(temp_size_mb, 2),
            "quotas": quota_tracker.get_all_status()
        }


quota_tracker = QuotaTracker()
watchdog = HealthWatchdog()

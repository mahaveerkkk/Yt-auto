import sqlite3
import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from config.settings import settings
from utils.logger import logger


class StudioMemory:
    """
    Studio Memory & Autonomous Performance Tracker (SQLite DB).
    Tracks:
    - Uploaded videos, titles, tags, and thumbnails
    - Performance history (Views, Likes, Comments)
    - High-performing niche memory (Which topics perform best)
    - Strategy decisions & pivots (autonomous AI records)
    - Worker status & task telemetry
    - Daily reports & content calendar
    """

    def __init__(self):
        self.db_path = settings.LOGS_DIR / "studio_memory.db"
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Videos table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE,
                    title TEXT,
                    category TEXT,
                    description TEXT,
                    youtube_url TEXT,
                    local_video_path TEXT,
                    thumbnail_path TEXT,
                    uploaded_at TIMESTAMP,
                    last_checked_at TIMESTAMP,
                    views_6h INTEGER DEFAULT 0,
                    views_24h INTEGER DEFAULT 0,
                    views_total INTEGER DEFAULT 0,
                    likes_total INTEGER DEFAULT 0,
                    ab_swap_count INTEGER DEFAULT 0
                )
            """)

            # 2. Niche stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS niche_stats (
                    category TEXT PRIMARY KEY,
                    total_videos INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    avg_engagement REAL DEFAULT 0.0
                )
            """)

            # 3. Strategy decisions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_type TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    reason TEXT,
                    data_snapshot TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_by_boss INTEGER DEFAULT 0
                )
            """)

            # 4. Worker status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS worker_status (
                    worker_name TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'idle',
                    current_task TEXT DEFAULT '',
                    last_active TIMESTAMP,
                    last_success TIMESTAMP,
                    last_error TEXT DEFAULT '',
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    total_tasks INTEGER DEFAULT 0
                )
            """)

            # 5. Daily reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date TEXT UNIQUE,
                    videos_produced INTEGER DEFAULT 0,
                    videos_uploaded INTEGER DEFAULT 0,
                    videos_failed INTEGER DEFAULT 0,
                    total_views_gained INTEGER DEFAULT 0,
                    total_new_subs INTEGER DEFAULT 0,
                    best_video_id TEXT DEFAULT '',
                    worst_video_id TEXT DEFAULT '',
                    strategy_changes INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    report_json TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 6. Content calendar
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_calendar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    planned_date TEXT,
                    planned_time TEXT,
                    topic TEXT,
                    category TEXT,
                    target_duration_sec INTEGER DEFAULT 600,
                    status TEXT DEFAULT 'planned',
                    video_id TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    # ---------------- Video Records ----------------
    def record_upload(self, video_id: str, title: str, category: str, youtube_url: str, thumb_path: str = ""):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO videos 
                    (video_id, title, category, youtube_url, thumbnail_path, uploaded_at, last_checked_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (video_id, title, category, youtube_url, thumb_path, datetime.utcnow(), datetime.utcnow()))
                
                cursor.execute("""
                    INSERT INTO niche_stats (category, total_videos, total_views)
                    VALUES (?, 1, 0)
                    ON CONFLICT(category) DO UPDATE SET total_videos = total_videos + 1
                """, (category,))
                conn.commit()
            logger.info(f"[StudioMemory] Saved video record '{title}' ({video_id}) to DB.")
        except Exception as e:
            logger.error(f"[StudioMemory] Error recording upload: {e}")

    def get_all_videos(self) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM videos ORDER BY id DESC")
                return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[StudioMemory] Fetch error: {e}")
            return []

    def update_stats(self, video_id: str, views: int, likes: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE videos 
                    SET views_total = ?, likes_total = ?, last_checked_at = ?
                    WHERE video_id = ?
                """, (views, likes, datetime.utcnow(), video_id))
                conn.commit()
        except Exception as e:
            logger.error(f"[StudioMemory] Stats update error: {e}")

    # ---------------- Strategy Decisions ----------------
    def log_strategy_decision(self, decision_type: str, old_value: str, new_value: str, reason: str, data_snapshot: Optional[Dict] = None):
        try:
            snapshot_str = json.dumps(data_snapshot or {})
            with sqlite3.connect(self.db_path) as conn:
                conn.cursor().execute("""
                    INSERT INTO strategy_decisions (decision_type, old_value, new_value, reason, data_snapshot)
                    VALUES (?, ?, ?, ?, ?)
                """, (decision_type, old_value, new_value, reason, snapshot_str))
                conn.commit()
            logger.info(f"[StudioMemory] 🧠 Strategy Decision Logged: {decision_type} -> {new_value} (Reason: {reason})")
        except Exception as e:
            logger.error(f"[StudioMemory] Error logging strategy decision: {e}")

    def get_recent_strategy_decisions(self, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM strategy_decisions ORDER BY id DESC LIMIT ?", (limit,))
                return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[StudioMemory] Strategy decisions fetch error: {e}")
            return []

    # ---------------- Worker Management ----------------
    def update_worker_status(self, worker_name: str, status: str, current_task: str = "", error_msg: str = ""):
        now = datetime.utcnow()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT success_count, error_count, total_tasks FROM worker_status WHERE worker_name = ?", (worker_name,))
                row = cursor.fetchone()
                
                success_count = (row[0] if row else 0) + (1 if status == 'idle' and not error_msg else 0)
                error_count = (row[1] if row else 0) + (1 if status == 'error' or error_msg else 0)
                total_tasks = (row[2] if row else 0) + (1 if status == 'working' else 0)
                last_success = now if (status == 'idle' and not error_msg) else (None if not row else None)

                cursor.execute("""
                    INSERT INTO worker_status 
                    (worker_name, status, current_task, last_active, last_error, success_count, error_count, total_tasks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(worker_name) DO UPDATE SET
                        status = excluded.status,
                        current_task = excluded.current_task,
                        last_active = excluded.last_active,
                        last_error = CASE WHEN ? != '' THEN ? ELSE last_error END,
                        success_count = ?,
                        error_count = ?,
                        total_tasks = ?
                """, (worker_name, status, current_task, now, error_msg, success_count, error_count, total_tasks,
                      error_msg, error_msg, success_count, error_count, total_tasks))
                conn.commit()
        except Exception as e:
            logger.error(f"[StudioMemory] Worker status update failed: {e}")

    def get_worker_status(self, worker_name: Optional[str] = None) -> Any:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if worker_name:
                    cursor.execute("SELECT * FROM worker_status WHERE worker_name = ?", (worker_name,))
                    row = cursor.fetchone()
                    return dict(row) if row else None
                cursor.execute("SELECT * FROM worker_status")
                return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[StudioMemory] Get worker status failed: {e}")
            return [] if not worker_name else None

    # ---------------- Niche & Category Analytics ----------------
    def get_category_performance(self) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        category,
                        COUNT(id) as total_videos,
                        SUM(views_total) as total_views,
                        ROUND(AVG(views_total), 1) as avg_views,
                        ROUND(AVG(likes_total), 1) as avg_likes
                    FROM videos
                    GROUP BY category
                    ORDER BY avg_views DESC
                """)
                return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[StudioMemory] Category performance query failed: {e}")
            return []

    # ---------------- Calendar ----------------
    def add_to_calendar(self, planned_date: str, planned_time: str, topic: str, category: str, target_duration: int = 600):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.cursor().execute("""
                    INSERT INTO content_calendar (planned_date, planned_time, topic, category, target_duration_sec)
                    VALUES (?, ?, ?, ?, ?)
                """, (planned_date, planned_time, topic, category, target_duration))
                conn.commit()
        except Exception as e:
            logger.error(f"[StudioMemory] Add calendar failed: {e}")

    def get_calendar(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        d = date_str or date.today().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM content_calendar WHERE planned_date = ? ORDER BY planned_time ASC", (d,))
                return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[StudioMemory] Calendar fetch failed: {e}")
            return []


studio_memory = StudioMemory()

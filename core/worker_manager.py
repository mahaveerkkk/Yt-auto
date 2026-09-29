from datetime import datetime
from typing import Dict, Any, List, Optional
from core.studio_memory import studio_memory
from utils.logger import logger


class WorkerManager:
    """
    Manages autonomous pipeline workers (Scout, Director, Producer, Uploader, ABOptimizer, Brain).
    Provides company-like telemetry:
    - Current state (idle, working, error, disabled)
    - Success/Failure rates
    - Live task assignment
    - Self-healing recovery
    """
    WORKERS = [
        "scout",
        "director",
        "producer",
        "uploader",
        "thumbnail",
        "ab_optimizer",
        "ai_brain",
        "qc"
    ]

    WORKER_ICONS = {
        "scout": "🕵️‍♂️",
        "director": "✍️",
        "producer": "🎨",
        "uploader": "🚀",
        "thumbnail": "🖼️",
        "ab_optimizer": "📊",
        "ai_brain": "🧠",
        "qc": "🛡️"
    }

    def __init__(self):
        self.notify_callback = None
        # Initialize default records for all workers if not present
        for w in self.WORKERS:
            status = studio_memory.get_worker_status(w)
            if not status:
                studio_memory.update_worker_status(w, status="idle", current_task="Standby for instructions")

    def set_notify_callback(self, callback):
        """Sets external callback (e.g. Telegram send_tg) for real-time telemetry broadcasts."""
        self.notify_callback = callback

    def start_task(self, worker_name: str, task_desc: str):
        """Marks a worker as actively executing a task and broadcasts to War Room."""
        logger.info(f"[WorkerManager] 👷 Worker '{worker_name}' STARTED task: {task_desc}")
        studio_memory.update_worker_status(worker_name, status="working", current_task=task_desc)
        if self.notify_callback:
            try:
                icon = self.WORKER_ICONS.get(worker_name.lower(), "👷")
                self.notify_callback(f"{icon} *{worker_name.title()} Agent:* {task_desc}")
            except Exception as e:
                logger.debug(f"[WorkerManager] Broadcast failed: {e}")

    def complete_task(self, worker_name: str, result_summary: str = "Task completed successfully"):
        """Marks a worker as finished and returned to idle."""
        logger.info(f"[WorkerManager] ✅ Worker '{worker_name}' COMPLETED task: {result_summary}")
        studio_memory.update_worker_status(worker_name, status="idle", current_task=f"Idle (Last: {result_summary[:40]})")
        if self.notify_callback and result_summary != "Task completed successfully":
            try:
                self.notify_callback(f"✅ *{worker_name.title()} Complete:* {result_summary}")
            except Exception as e:
                logger.debug(f"[WorkerManager] Broadcast failed: {e}")

    def report_error(self, worker_name: str, error_msg: str):
        """Flags an error on a worker."""
        logger.error(f"[WorkerManager] ❌ Worker '{worker_name}' encountered ERROR: {error_msg}")
        studio_memory.update_worker_status(worker_name, status="error", error_msg=error_msg[:200])
        if self.notify_callback:
            try:
                self.notify_callback(f"⚠️ *{worker_name.title()} Alert:* {error_msg}")
            except Exception as e:
                logger.debug(f"[WorkerManager] Broadcast failed: {e}")

    def get_status_overview(self) -> Dict[str, Any]:
        """Returns structured health of all workers."""
        workers_data = studio_memory.get_worker_status()
        summary = {}
        for w in workers_data:
            total = w.get("total_tasks", 0)
            success = w.get("success_count", 0)
            rate = round((success / total) * 100, 1) if total > 0 else 100.0
            summary[w["worker_name"]] = {
                "status": w.get("status", "idle"),
                "task": w.get("current_task", ""),
                "last_active": w.get("last_active", "N/A"),
                "success_rate": f"{rate}%",
                "error": w.get("last_error", "")
            }
        return summary

    def format_telegram_report(self) -> str:
        """Generates a clean Telegram dashboard of all studio workers."""
        overview = self.get_status_overview()
        lines = ["👥 *Studio Workers Telemetry:*", ""]
        icons = {"idle": "🟢", "working": "🟡", "error": "🔴", "disabled": "⚪"}

        for name, data in overview.items():
            icon = icons.get(data['status'], "⚪")
            lines.append(f"{icon} *{name.upper()}*: `{data['status']}` ({data['success_rate']} success)")
            if data['task']:
                lines.append(f"   _{data['task'][:60]}_")
        return "\n".join(lines)


worker_manager = WorkerManager()

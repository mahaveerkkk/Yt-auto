import json
from datetime import datetime, date
from typing import Dict, Any, Optional
from core.omni_router import omni_router
from core.studio_memory import studio_memory
from core.resilience import quota_tracker, watchdog
from core.strategy import strategy_engine
from core.worker_manager import worker_manager
from utils.logger import logger


class AIBrain:
    """
    The Executive Thinking Engine for the AI CEO.
    Combines:
    - Real calendar date & seasonal awareness (Halloween, Equinox, Discovery Anniversaries)
    - Channel health & quota tracking
    - Algorithmic decision making on KAB aur KYA banayein
    - 100% autonomous operation without human intervention
    """

    def __init__(self):
        pass

    def get_seasonal_context(self) -> Dict[str, Any]:
        """
        Calculates seasonal/astronomical hooks for relevant documentary curation.
        """
        now = datetime.now()
        month = now.month
        
        # Determine current seasonal focus
        seasonal_angle = "Deep Space & Unexplained Physical Phenomena"
        if month in [10]:
            seasonal_angle = "Forbidden Folklore, Paranormal Anomalies, & Ancient Curses"
        elif month in [11, 12]:
            seasonal_angle = "Arctic Abyss, Deep Space Voids, & Extreme Isolations"
        elif month in [6, 7, 8]:
            seasonal_angle = "Deep Sea Trench Mysteries & Bermuda Triangle Maritime Events"
        
        return {
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M IST"),
            "month": now.strftime("%B"),
            "seasonal_angle": seasonal_angle
        }

    def should_produce_now(self) -> Dict[str, Any]:
        """
        Determines if the studio should immediately trigger an autonomous production run.
        Considers:
        - Quota availability (Pexels, Gemini, etc.)
        - Daily upload count to avoid YouTube spam filters (Max 2 videos/day for new channel)
        """
        worker_manager.start_task("ai_brain", "Evaluating studio readiness and upload quota")

        # 1. Check quotas
        if not quota_tracker.can_use("gemini"):
            worker_manager.complete_task("ai_brain", "Gemini quota exhausted")
            return {"allowed": False, "reason": "Gemini API daily limit reached"}
        
        if not quota_tracker.can_use("pexels"):
            worker_manager.complete_task("ai_brain", "Pexels quota exhausted")
            return {"allowed": False, "reason": "Pexels API limit reached"}

        # 2. Check daily uploads from actual video records (not just planned calendar)
        today = date.today().isoformat()
        recent_videos = studio_memory.get_recent_videos(limit=10)
        completed_today = sum(1 for v in recent_videos if v.get("uploaded_at", "").startswith(today))

        if completed_today >= 1:
            worker_manager.complete_task("ai_brain", "Daily upload limit (1/1) reached")
            return {"allowed": False, "reason": "Target 1 high-retention master documentary upload for today already completed"}

        worker_manager.complete_task("ai_brain", "Production approved")
        return {"allowed": True, "reason": "All systems healthy. Quotas and schedule clear."}

    def synthesize_topic_decision(self, scouted_topic: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes a scouted topic and determines its monetization viability and documentary format.
        """
        topic_title = scouted_topic.get("topic", "The Ocean Acoustic Anomaly")
        category = scouted_topic.get("category", "Deep Ocean Abyss")
        seasonal = self.get_seasonal_context()
        target_runtime = strategy_engine.decide_runtime(topic_title, category)

        logger.info(f"[AIBrain] 🧠 Planning documentary: '{topic_title}' | Target Duration: {target_runtime}s (~{target_runtime//60} mins)")

        return {
            "topic": topic_title,
            "category": category,
            "angle": scouted_topic.get("angle", ""),
            "target_duration_sec": target_runtime,
            "seasonal_context": seasonal["seasonal_angle"]
        }


ai_brain = AIBrain()

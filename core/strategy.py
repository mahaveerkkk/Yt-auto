import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.studio_memory import studio_memory
from core.omni_router import omni_router
from utils.logger import logger


class StrategyEngine:
    """
    Autonomous Channel Strategy & Evolution Engine.
    Responsibilities:
    - Analyzes performance per category (Space, Deep Ocean, Ancient Secrets, Quantum, etc.)
    - Dynamically pivots focus towards high-converting niches
    - Decides optimal documentary runtime (8-12 mins) based on narrative depth
    - Proactively advises CEO and owner on trajectory adjustments
    """

    CATEGORIES = [
        "Dark Space & Astronomy",
        "Deep Ocean Abyss",
        "Forbidden Ancient Civilizations",
        "Classified Aviation & Maritime",
        "Quantum & Cosmic Anomalies"
    ]

    def __init__(self):
        pass

    def evaluate_channel_trajectory(self) -> Dict[str, Any]:
        """
        Gathers DB stats and performs an automated assessment of channel direction.
        """
        performance = studio_memory.get_category_performance()
        total_vids = sum(p.get("total_videos", 0) for p in performance)

        # If we have little or no data yet, maintain exploration balance
        if total_vids < 3:
            return {
                "phase": "EXPLORATION",
                "recommended_focus": "Multi-Niche Testing",
                "reason": "Channel is in testing phase. Sampling Space, Ocean, and Ancient mysteries equally.",
                "pivot_needed": False
            }

        # Find best and worst performing categories
        sorted_cats = sorted(performance, key=lambda x: x.get("avg_views", 0), reverse=True)
        top_cat = sorted_cats[0]
        bottom_cat = sorted_cats[-1]

        # Trigger pivot if top category performs significantly better (> 2.5x)
        top_avg = top_cat.get("avg_views", 0)
        bot_avg = bottom_cat.get("avg_views", 0)

        pivot_needed = False
        pivot_reason = ""

        if top_avg >= 50 and bot_avg < 20 and top_cat["category"] != bottom_cat["category"]:
            pivot_needed = True
            pivot_reason = (
                f"'{top_cat['category']}' is averaging {top_avg} views vs "
                f"'{bottom_cat['category']}' with only {bot_avg} views. Pivoting quota to high-traction themes."
            )
            studio_memory.log_strategy_decision(
                decision_type="content_pivot",
                old_value=bottom_cat["category"],
                new_value=top_cat["category"],
                reason=pivot_reason,
                data_snapshot={"top": top_cat, "bottom": bottom_cat}
            )

        return {
            "phase": "GROWTH" if top_avg > 100 else "OPTIMIZATION",
            "top_category": top_cat["category"],
            "top_avg_views": top_avg,
            "underperforming_category": bottom_cat["category"],
            "pivot_needed": pivot_needed,
            "pivot_reason": pivot_reason
        }

    def decide_runtime(self, topic: str, category: str) -> int:
        """
        Dynamically decides target duration in seconds.
        For high monetization yield:
        Target is 8 to 12 minutes (480s to 720s) to unlock YouTube mid-roll advertisements.
        Returns duration in seconds.
        """
        # Minimum 480 seconds (8 minutes) for mid-roll ad monetization
        # High depth themes (ancient ruins, complex cosmic mysteries) get 10-12 mins
        deep_themes = ["Ancient", "Quantum", "Cosmic", "Civilization", "Universe"]
        if any(w.lower() in topic.lower() or w.lower() in category.lower() for w in deep_themes):
            return 600  # 10 minutes (approx 1400-1500 words script)
        return 480  # 8 minutes baseline (approx 1100-1200 words script)

    def generate_proactive_briefing(self) -> str:
        """
        Uses OmniRouter/Gemini to craft a sharp executive briefing for the Boss on Telegram.
        """
        traj = self.evaluate_channel_trajectory()
        perf = studio_memory.get_category_performance()
        
        prompt = (
            f"You are the AI CEO of the YouTube documentary channel 'Void Archive'. "
            f"Channel Trajectory Analysis:\n"
            f"- Phase: {traj.get('phase')}\n"
            f"- Category Stats: {json.dumps(perf)}\n"
            f"- Strategic Pivot: {traj.get('pivot_reason') or 'Steady course across primary mystery niches'}\n\n"
            f"Write a sharp, high-level Hinglish strategic status report to your Boss (Veer) under 100 words. "
            f"Tell him our monetization plan (reaching 4000 watch hours), our 8-12 min video approach, and current focus."
        )

        resp = omni_router.query(prompt=prompt)
        if resp:
            return resp.strip()
        
        return (
            "👑 *CEO Strategy Update:*\n\n"
            "Boss, Void Archive ko monetize karne ke liye hum 8-12 min long-form documentaries pe switch kar chuke hain taaki 4000 watch hours aur mid-roll ads jaldi unlock ho sakein. "
            "Pexels HD footage aur natural BBC voiceover ke saath visual retention maximize ki ja rahi hai. Studio autopilot mode me hai! 🚀"
        )


strategy_engine = StrategyEngine()

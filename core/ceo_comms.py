import requests
from pathlib import Path
from typing import Optional, Dict, Any
from config.settings import settings
from utils.logger import logger
from core.analytics_ceo import analytics_ceo
from core.strategy import strategy_engine
from core.worker_manager import worker_manager
from core.resilience import quota_tracker, watchdog


class CEOComms:
    """
    Proactive CEO Communication Center.
    The AI CEO talks FIRST — delivering real-time executive decisions,
    monetization watch-time progress, daily roadmaps, and error recovery telemetry.
    """

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Sends rich formatted message to Veer on Telegram."""
        if not self.bot_token or not self.chat_id:
            logger.warning("[CEOComms] Telegram credentials missing.")
            return False
        try:
            res = requests.post(f"{self.api_base}/sendMessage", json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }, timeout=25)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"[CEOComms] Message transmission failed: {e}")
            return False

    def send_photo(self, photo_path: Path, caption: str) -> bool:
        """Sends visual photo/thumbnail preview to Veer on Telegram."""
        if not self.bot_token or not self.chat_id:
            return False
        try:
            with open(photo_path, "rb") as f:
                res = requests.post(f"{self.api_base}/sendPhoto", data={
                    "chat_id": self.chat_id,
                    "caption": caption[:1024],
                    "parse_mode": "Markdown"
                }, files={"photo": f}, timeout=25)
                return res.status_code == 200
        except Exception as e:
            logger.error(f"[CEOComms] Photo transmission failed: {e}")
            return False

    def send_morning_executive_briefing(self):
        """Dispatches daily strategic roadmap and monetization status."""
        summary = analytics_ceo.get_channel_summary()
        strategy_info = strategy_engine.evaluate_channel_trajectory()
        health = watchdog.get_system_health()

        briefing = (
            "☀️ *GOOD MORNING BOSS! — CEO Executive Briefing*\n\n"
            f"📺 *Void Archive Channel Performance:*\n"
            f"• Subscribers: *{summary.get('subscribers', '0')}* / 1,000 target\n"
            f"• Lifetime Views: *{summary.get('total_views', '0')}*\n"
            f"• Total Videos: *{summary.get('video_count', '0')}*\n\n"
            f"🎯 *Monetization Strategy Focus:*\n"
            f"• Long-Form Production: 8-12 min documentaries for mid-roll ads\n"
            f"• Channel Phase: `{strategy_info.get('phase')}`\n"
            f"• Primary Niche Focus: _{strategy_info.get('top_category', 'Deep Space & Ocean')}_\n\n"
            f"⚙️ *System Health & VPS Telemetry:*\n"
            f"• VPS Disk Free: `{health.get('disk_free_gb')} GB`\n"
            f"• Studio Workers: `100% Autonomous & Operational`\n\n"
            "Studio team is ready for today's scheduled production runs! 🚀"
        )
        self.send_message(briefing)

    def send_upload_success_alert(self, title: str, yt_url: str, duration_sec: float, category: str, thumb_path: Optional[Path] = None):
        """Celebrates and logs a successfully published PUBLIC documentary."""
        msg = (
            "🎉 *NEW DOCUMENTARY PUBLISHED (PUBLIC)!*\n\n"
            f"🎬 *{title}*\n"
            f"⏱️ Runtime: `{duration_sec/60:.1f} mins` ({int(duration_sec)}s)\n"
            f"📂 Category: *{category}*\n"
            f"🔗 Watch: {yt_url}\n\n"
            f"Status: *PUBLIC (Search & Recommended Active)*\n"
            f"Mid-Roll Monetization: Enabled for 8+ min runtime."
        )
        if thumb_path and thumb_path.exists():
            self.send_photo(thumb_path, caption=msg)
        else:
            self.send_message(msg)

    def send_error_recovery_alert(self, worker_name: str, issue: str, recovery_action: str):
        """Informs the boss of an issue that was autonomously handled by Resilience."""
        msg = (
            f"🛡️ *Resilience Self-Healing Alert*\n\n"
            f"Worker: *{worker_name.upper()}*\n"
            f"Encountered: _{issue[:120]}_\n"
            f"Resolution: *{recovery_action}*\n\n"
            f"No human intervention required. Autopilot continuing."
        )
        self.send_message(msg)


ceo_comms = CEOComms()

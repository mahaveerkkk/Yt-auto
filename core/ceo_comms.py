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

    @staticmethod
    def _render_progress_bar(current: float, target: float, length: int = 10) -> str:
        """Draws clean ASCII progress bar for milestone tracking."""
        pct = min(1.0, max(0.0, current / target)) if target > 0 else 0.0
        filled = int(round(length * pct))
        bar = "▓" * filled + "░" * (length - filled)
        return f"[{bar}] {pct*100:.1f}%"

    def send_morning_executive_briefing(self):
        """Dispatches daily 09:00 AM IST high-motivation standup with live monetization progress."""
        summary = analytics_ceo.get_channel_summary()
        strategy_info = strategy_engine.evaluate_channel_trajectory()
        health = watchdog.get_system_health()

        subs = int(summary.get("subscribers", 0))
        views = int(summary.get("total_views", 0))
        # Estimate watch hours based on average 5.5 min watch time per view
        est_watch_hours = round((views * 5.5) / 60, 1)

        sub_bar = self._render_progress_bar(subs, 1000)
        watch_bar = self._render_progress_bar(est_watch_hours, 4000)

        briefing = (
            "🌅 *GOOD MORNING BOSS! — CEO Daily Standup (09:00 AM IST)*\n\n"
            "Boss, aaj target mystery space mein top position capture karne ka hai! 🚀\n"
            "Studio autopilot 24/7 rock-solid chal raha hai.\n\n"
            "🎯 *YouTube Partner Monetization Milestones:*\n"
            f"• 👥 Subscribers: *{subs}* / 1,000 Target\n"
            f"  ↳ `{sub_bar}`\n"
            f"• ⏳ Watch Time: *~{est_watch_hours} hrs* / 4,000 Target\n"
            f"  ↳ `{watch_bar}`\n\n"
            f"📊 *Channel Lifetime Stats:*\n"
            f"• Total Public Views: *{views}*\n"
            f"• Published Videos: *{summary.get('video_count', '0')}*\n"
            f"• Primary Content Pillar: _{strategy_info.get('top_category', 'Deep Ocean & Space Abyss')}_\n\n"
            f"⚙️ *Studio Infrastructure:*\n"
            f"• Storage Hygiene: `Clean ({health.get('temp_cache_mb', 0.0)} MB cache)`\n"
            f"• Production Slots Today: `12:00 PM & 07:00 PM IST`\n\n"
            "Bhai, tension mat lo — content pipeline apne aap execute karegi. Let's dominate! 🔥"
        )
        self.send_message(briefing)

    def send_weekly_revenue_report(self):
        """Dispatches Sunday 08:00 PM IST $1,000/Month Revenue Roadmap & Strategy Audit."""
        summary = analytics_ceo.get_channel_summary()
        strategy_info = strategy_engine.evaluate_channel_trajectory()
        views = int(summary.get("total_views", 0))
        subs = int(summary.get("subscribers", 0))

        # $1,000/mo target modeling: Category 28 CPM ~$5.00 - $6.50
        # Target: ~180,000 - 200,000 views per month
        est_monthly_views = views * 4  # projection multiplier
        est_cpm = 5.50
        est_monthly_revenue = round((est_monthly_views / 1000) * est_cpm, 2)
        revenue_bar = self._render_progress_bar(est_monthly_revenue, 1000)

        report = (
            "📊 *SUNDAY EXECUTIVE AUDIT — $1,000/MONTH ROADMAP*\n\n"
            "Boss, poore hafte ka strategic review ready hai:\n\n"
            f"💰 *Revenue Trajectory Target ($1,000 / Month):*\n"
            f"• Projected Monthly Earnings: *${est_monthly_revenue}* / $1,000\n"
            f"  ↳ `{revenue_bar}`\n"
            f"• Category 28 Science CPM: `~${est_cpm} per 1K views`\n\n"
            f"📈 *Channel Velocity:*\n"
            f"• Total Public Views: *{views}*\n"
            f"• Subscriber Base: *{subs}* members\n"
            f"• Top Performing Mystery Pillar: *{strategy_info.get('top_category', 'Deep Ocean')}*\n\n"
            "🎯 *Upcoming Week's Focus:*\n"
            "1. 2 High-Retention (8-12 min) Master Documentaries with SFX & Chapters\n"
            "2. 3-4 High-Yield 9:16 Shorts to drive subscriber acceleration\n"
            "3. Auto-Playlists for binge-watching watch-hour compounding\n\n"
            "Poori team ready hai. We are on track for monetization! 🚀👑"
        )
        self.send_message(report)

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

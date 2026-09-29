import requests
from config.settings import settings
from utils.logger import logger


class TelegramNotifier:
    """Sends real-time mobile heartbeat & alert messages to your Telegram."""

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID

    @staticmethod
    def _escape_markdown(text: str) -> str:
        """Escape special Markdown characters in dynamic content to prevent Telegram 400 errors."""
        for ch in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            text = text.replace(ch, f'\\{ch}')
        return text

    def send_alert(self, text: str) -> bool:
        """Sends a text message to Telegram with Markdown fallback to plain text."""
        if not self.bot_token or not self.chat_id:
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code == 200:
                return True
            # Markdown parsing failed — retry as plain text
            logger.debug(f"[Telegram] Markdown rejected ({res.status_code}), retrying as plain text")
            payload["parse_mode"] = ""
            res2 = requests.post(url, json=payload, timeout=15)
            return res2.status_code == 200
        except Exception as e:
            logger.warning(f"[Telegram Alert] Failed to send: {e}")
            return False

    def notify_success(self, title: str, duration: float, scene_count: int):
        msg = (
            f"🎬 *New Video Generated!*\n\n"
            f"📌 *Title:* {title}\n"
            f"⏱️ *Duration:* {duration:.1f}s\n"
            f"🎞️ *Scenes:* {scene_count}\n"
            f"✅ *Status:* Delivered & Ready"
        )
        self.send_alert(msg)

    def notify_failure(self, step: str, error: str):
        msg = (
            f"⚠️ *AutoDirector Alert: Task Failed*\n\n"
            f"❌ *Stage:* {step}\n"
            f"📋 *Reason:* `{error[:200]}`\n"
            f"🔄 *Action:* Cleanup initiated."
        )
        self.send_alert(msg)


notifier = TelegramNotifier()

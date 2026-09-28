import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from config.settings import settings
from utils.logger import logger

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]


class Uploader:
    """
    Delivery & Upload Engine.
    Primary: Sends ready video + caption directly to your Telegram bot.
    Secondary: YouTube Data API v3 integration for 100% automated channel publishing.
    """

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.token_file = settings.BASE_DIR / "config" / "youtube_token.json"

    def send_to_telegram(self, video_path: Path, caption: str) -> bool:
        """
        Sends the final video to the configured Telegram chat with caption.
        Uses pure requests (no heavy telegram bot dependencies).
        """
        if not self.bot_token or not self.chat_id:
            logger.warning("[Telegram] Bot token or Chat ID missing in configuration. Skipping Telegram send.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"
        logger.info(f"[Telegram] Uploading video '{video_path.name}' to Telegram...")

        try:
            with open(video_path, "rb") as video_file:
                files = {"video": (video_path.name, video_file, "video/mp4")}
                data = {
                    "chat_id": self.chat_id,
                    "caption": caption[:1024],
                    "supports_streaming": "true"
                }
                response = requests.post(url, data=data, files=files, timeout=120)

                if response.status_code == 200:
                    logger.info("✅ Video successfully delivered to Telegram!")
                    return True
                else:
                    logger.error(f"[Telegram] Failed to send: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"[Telegram] Network error during upload: {e}")
            return False

    def get_youtube_service(self):
        """Builds authenticated YouTube Data API v3 service."""
        if not self.token_file.exists():
            logger.warning("[YouTube] youtube_token.json not found. Run python authenticate_youtube.py first.")
            return None

        try:
            creds = Credentials.from_authorized_user_file(str(self.token_file), YOUTUBE_SCOPES)
            if creds and creds.expired and creds.refresh_token:
                logger.info("[YouTube] Refreshing expired OAuth token...")
                creds.refresh(Request())
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())

            return build("youtube", "v3", credentials=creds)
        except Exception as e:
            logger.error(f"[YouTube] Auth error: {e}")
            return None

    def upload_to_youtube(
        self,
        video_path: Path,
        manifest: Dict[str, Any],
        privacy_status: str = "public",
        thumbnail_path: Optional[Path] = None
    ) -> Optional[str]:
        """
        Uploads a video to YouTube with title, description, and tags.
        Returns the public YouTube video URL if successful.
        """
        youtube = self.get_youtube_service()
        if not youtube:
            return None

        title = manifest.get("title", "Untitled Mystery Documentary")
        description = manifest.get("description", "")
        tags = [t.replace("#", "").strip() for t in manifest.get("hashtags", ["Mystery", "Documentary"])]

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags,
                "categoryId": "28"  # Science & Technology (High CPM)
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        try:
            logger.info(f"[YouTube] Starting upload of '{video_path.name}' to channel ({privacy_status})...")
            media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"[YouTube] Uploading: {int(status.progress() * 100)}%")

            video_id = response.get("id")
            video_url = f"https://youtu.be/{video_id}"
            logger.info(f"🎉 Successfully published to YouTube: {video_url}")

            # Auto-Set Custom Thumbnail if provided
            if thumbnail_path and Path(thumbnail_path).exists():
                try:
                    logger.info(f"[YouTube] Uploading custom thumbnail for video {video_id}...")
                    thumb_media = MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg")
                    youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
                    logger.info("🎉 Custom Thumbnail successfully set on YouTube!")
                except Exception as th_err:
                    logger.warning(f"[YouTube] Thumbnail upload warning (Channel may need phone verification): {th_err}")

            return video_url
        except Exception as e:
            logger.error(f"[YouTube] Upload failed: {e}")
            return None


uploader = Uploader()

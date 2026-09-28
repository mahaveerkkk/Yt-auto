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
    "https://www.googleapis.com/auth/youtube.readonly"
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
        try:
            size_mb = video_path.stat().st_size / (1024 * 1024)
            if size_mb > 49.0:
                logger.info(f"[Telegram] Video size is {size_mb:.1f} MB (exceeds Telegram 50MB bot upload limit). Delivering via message notification.")
                notice = (
                    f"🎬 *Full Documentary Master Rendered ({size_mb:.1f} MB)*\n\n"
                    f"{caption}\n\n"
                    f"_Note: Master file exceeds Telegram's 50MB direct bot transfer limit. Publishing to YouTube!_"
                )
                requests.post(f"https://api.telegram.org/bot{self.bot_token}/sendMessage", json={
                    "chat_id": self.chat_id,
                    "text": notice,
                    "parse_mode": "Markdown"
                }, timeout=20)
                return True

            logger.info(f"[Telegram] Uploading video '{video_path.name}' ({size_mb:.1f} MB) to Telegram...")
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
        token_env = os.getenv("YOUTUBE_TOKEN_JSON")
        if not self.token_file.exists() and token_env:
            try:
                self.token_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_file, "w") as tf:
                    tf.write(token_env)
                logger.info("[YouTube] Restored youtube_token.json from environment variable.")
            except Exception as e:
                logger.warning(f"[YouTube] Could not write token from env: {e}")

        if not self.token_file.exists():
            logger.warning("[YouTube] youtube_token.json not found. Run python authenticate_youtube.py first or set YOUTUBE_TOKEN_JSON env var.")
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

    def post_pinned_comment(self, video_id: str, comment_text: str) -> bool:
        """Posts an engagement starter question as a comment on the published video."""
        youtube = self.get_youtube_service()
        if not youtube or not video_id:
            return False
        try:
            body = {
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": comment_text
                        }
                    }
                }
            }
            youtube.commentThreads().insert(part="snippet", body=body).execute()
            logger.info(f"💬 Pinned engagement comment posted under YouTube video {video_id}!")
            return True
        except Exception as e:
            logger.warning(f"[YouTube] Auto-comment skipped: {e}")
            return False


uploader = Uploader()

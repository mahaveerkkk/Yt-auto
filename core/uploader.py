import os
import json
import time
import subprocess
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
        try:
            size_mb = video_path.stat().st_size / (1024 * 1024)
            if size_mb > 49.0:
                logger.info(f"[Telegram] Video size is {size_mb:.1f} MB (exceeds Telegram 50MB bot upload limit). Delivering via message notification.")
                notice = (
                    f"🎬 *Full Documentary Master Rendered ({size_mb:.1f} MB)*\n\n"
                    f"{caption}\n\n"
                    f"_Note: Master file exceeds Telegram's 50MB direct bot transfer limit. Publishing to YouTube!_"
                )
                r_tg = requests.post(f"https://api.telegram.org/bot{self.bot_token}/sendMessage", json={
                    "chat_id": self.chat_id,
                    "text": notice,
                    "parse_mode": "Markdown"
                }, timeout=20)
                if r_tg.status_code != 200:
                    requests.post(f"https://api.telegram.org/bot{self.bot_token}/sendMessage", json={
                        "chat_id": self.chat_id,
                        "text": notice
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
            creds = Credentials.from_authorized_user_file(str(self.token_file))
            if creds and not creds.valid and creds.refresh_token:
                logger.info("[YouTube] Refreshing expired OAuth token...")
                creds.refresh(Request())
                temp_token = self.token_file.with_suffix(".tmp")
                with open(temp_token, "w") as token:
                    token.write(creds.to_json())
                temp_token.replace(self.token_file)

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
        raw_desc = manifest.get("description", "").strip()
        raw_hashtags = manifest.get("hashtags", ["#Mystery", "#Documentary", "#VoidArchive", "#Science"])
        raw_ai_tags = manifest.get("tags", [])
        
        # Format clean hashtags for description text (e.g. #Mystery #DeepSea)
        formatted_hashtags = []
        for h in raw_hashtags:
            clean_word = h.replace("#", "").strip()
            if clean_word and f"#{clean_word}" not in formatted_hashtags:
                formatted_hashtags.append(f"#{clean_word}")

        # Combine AI-generated tags (15-25 topic-specific tags) + hashtags + core channel tags for YouTube backend SEO
        clean_tags = []
        # 1. AI-generated specific search terms
        for t in raw_ai_tags:
            ct = t.replace("#", "").strip()
            if ct and ct not in clean_tags:
                clean_tags.append(ct)
        # 2. Add hashtag words
        for h in raw_hashtags:
            cw = h.replace("#", "").strip()
            if cw and cw not in clean_tags:
                clean_tags.append(cw)
        # 3. Channel anchor tags
        core_channel_tags = ["VoidArchive", "Void Archive", "Documentary", "Mystery", "Unsolved Mystery", "Science Investigation"]
        for ct in core_channel_tags:
            if ct not in clean_tags:
                clean_tags.append(ct)

        # Ensure hashtags are guaranteed at the end of the description text
        hashtag_line = " ".join(formatted_hashtags)
        if hashtag_line and hashtag_line not in raw_desc:
            full_description = f"{raw_desc}\n\n{hashtag_line}\n\n📡 Subscribe to Void Archive for weekly declassified documentaries."
        else:
            full_description = raw_desc

        body = {
            "snippet": {
                "title": title[:100],
                "description": full_description[:5000],
                "tags": clean_tags[:30],
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
            retry_count = 0
            max_retries = 5
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        logger.info(f"[YouTube] Uploading: {int(status.progress() * 100)}%")
                    retry_count = 0  # Reset on success
                except Exception as chunk_err:
                    err_str = str(chunk_err).lower()
                    if "quotaexceeded" in err_str or "daily limit" in err_str:
                        logger.critical("[YouTube] ❌ Daily YouTube API upload quota exceeded! Halting upload immediately.")
                        return None
                    if "401" in err_str or "unauthorized" in err_str or "invalid_grant" in err_str:
                        logger.critical("[YouTube] ❌ OAuth credentials invalid or revoked. Halting upload.")
                        return None
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error(f"[YouTube] Upload failed after {max_retries} retries: {chunk_err}")
                        raise
                    wait_time = min(2 ** retry_count * 5, 120)  # 10s, 20s, 40s, 80s, 120s
                    logger.warning(f"[YouTube] Chunk upload error (retry {retry_count}/{max_retries}, waiting {wait_time}s): {chunk_err}")
                    import time
                    time.sleep(wait_time)

            video_id = response.get("id") if isinstance(response, dict) else None
            if not video_id:
                logger.error(f"[YouTube] Upload response did not contain a valid video ID: {response}")
                return None

            video_url = f"https://youtu.be/{video_id}"
            logger.info(f"🎉 Successfully published to YouTube: {video_url}")

            # Auto-Set Custom Thumbnail if provided
            if thumbnail_path and Path(thumbnail_path).exists():
                try:
                    th_file = Path(thumbnail_path)
                    upload_target = th_file

                    # YouTube strictly limits custom thumbnails to 2MB (2,097,152 bytes)
                    if th_file.stat().st_size >= 1950000:
                        logger.info(f"[YouTube] Thumbnail size ({th_file.stat().st_size / (1024*1024):.2f}MB) exceeds 1.95MB safe limit. Recompressing...")
                        recompressed = th_file.with_name(f"{th_file.stem}_safe.jpg")
                        cmd = [
                            "ffmpeg", "-y",
                            "-i", str(th_file),
                            "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
                            "-q:v", "3",
                            str(recompressed)
                        ]
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                        if recompressed.exists() and recompressed.stat().st_size < 1950000:
                            upload_target = recompressed

                    logger.info(f"[YouTube] Uploading custom thumbnail ({upload_target.stat().st_size / 1024:.1f} KB) for video {video_id}...")
                    thumb_media = MediaFileUpload(str(upload_target), mimetype="image/jpeg")
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

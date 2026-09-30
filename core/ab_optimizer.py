import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from config.settings import settings
from utils.logger import logger
from core.uploader import uploader
from core.thumbnail import thumbnail_designer
from core.studio_memory import studio_memory
from core.omni_router import omni_router

class ABOptimizer:
    """
    Auto A/B Testing & Optimization Engine.
    Inspects videos uploaded > 12 hours ago.
    If views or engagement are critically low:
    - Generates a sharper, more click-worthy title using Gemini / OmniRouter.
    - Generates a higher-contrast, punchier thumbnail.
    - Updates YouTube video metadata and thumbnail automatically via YouTube API.
    """

    def check_and_optimize_videos(self) -> Optional[str]:
        """Scans tracked videos and performs A/B overhaul on underperformers."""
        service = uploader.get_youtube_service()
        if not service:
            return None

        tracked = studio_memory.get_all_videos()
        if not tracked:
            return None

        now = datetime.now(timezone.utc)
        for v in tracked:
            uploaded_str = v.get("uploaded_at")
            if not uploaded_str:
                continue

            try:
                uploaded_dt = datetime.fromisoformat(uploaded_str)
                if uploaded_dt.tzinfo is None:
                    uploaded_dt = uploaded_dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue

            age_hours = (now - uploaded_dt).total_seconds() / 3600.0
            swap_count = v.get("ab_swap_count", 0)

            # Algorithmic Safety Guard: Allow full 14 days (336h) for natural YouTube testing.
            # Only trigger A/B overhaul if video is completely flatlined (< 15 views after 14 days)
            # and has never been swapped before (swap_count == 0).
            if age_hours >= 336.0 and swap_count == 0:
                vid = v.get("video_id")
                # Fetch fresh views from YouTube API
                try:
                    res = service.videos().list(id=vid, part="statistics,snippet").execute()
                    items = res.get("items", [])
                    if not items:
                        continue
                    stats = items[0].get("statistics", {})
                    views = int(stats.get("viewCount", 0))
                    studio_memory.update_stats(vid, views=views, likes=int(stats.get("likeCount", 0)))

                    # If video is flatlined (< 15 views after 14 full days), trigger single strategic overhaul!
                    if views < 15:
                        logger.info(f"[ABOptimizer] Video '{v.get('title')}' is completely flatlined ({views} views in {age_hours/24:.1f} days). Triggering Strategic 14-Day Overhaul...")
                        return self._execute_swap(service, vid, v)
                except Exception as e:
                    logger.error(f"[ABOptimizer] Error inspecting video {vid}: {e}")
        return None

    def _execute_swap(self, service, video_id: str, video_record: Dict[str, Any]) -> str:
        """Executes title rewrite and thumbnail swap on YouTube."""
        old_title = video_record.get("title", "")
        category = video_record.get("category", "Mystery")

        # 1. Ask Gemini / OmniRouter for high-CTR title rewrite
        prompt = f"The YouTube title '{old_title}' about {category} has low views. Rewrite it into an extreme, shocking, high-CTR mystery title under 65 characters with intrigue. Return ONLY the new title text."
        new_title = omni_router.query(prompt=prompt)
        if not new_title:
            new_title = f"The Terrifying Secret of {old_title[:40]}"
        new_title = new_title.strip().replace('"', '')[:65]

        # 2. Update YouTube Video Title
        try:
            curr_res = service.videos().list(id=video_id, part="snippet").execute()
            curr_items = curr_res.get("items", [])
            if not curr_items:
                logger.warning(f"[ABOptimizer] Video {video_id} not found or deleted. Skipping swap.")
                return None
            curr = curr_items[0]
            snippet = curr["snippet"]
            snippet["title"] = new_title
            service.videos().update(part="snippet", body={"id": video_id, "snippet": snippet}).execute()
            logger.info(f"[ABOptimizer] YouTube Title updated to: '{new_title}'")
        except Exception as e:
            logger.error(f"[ABOptimizer] Failed to update title on YouTube: {e}")

        # 3. Generate and set New High-Contrast Thumbnail via Frontier Engine
        new_thumb = thumbnail_designer.generate_thumbnail(
            title=new_title,
            hook_text="",
            visual_prompt=f"classified technical anomaly in {category}, sonar spectrogram waterfall readout, extreme scale perspective contrast, dark atmospheric abyss"
        )
        if new_thumb and new_thumb.exists():
            try:
                from googleapiclient.http import MediaFileUpload
                thumb_media = MediaFileUpload(str(new_thumb), mimetype="image/jpeg")
                service.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
                logger.info("[ABOptimizer] YouTube Thumbnail replaced successfully!")
            except Exception as e:
                logger.warning(f"[ABOptimizer] Thumbnail swap warning: {e}")

        # 4. Update Studio DB swap count via studio_memory
        studio_memory.record_ab_swap(video_id=video_id, new_title=new_title)

        report = (
            f"🔄 **CEO A/B Optimization Alert!**\n\n"
            f"Video was underperforming. I have automatically overhauled it:\n"
            f"❌ Old Title: _{old_title}_\n"
            f"✨ **New High-CTR Title:** *{new_title}*\n"
            f"🖼️ Fresh high-contrast thumbnail published to YouTube!"
        )
        return report

ab_optimizer = ABOptimizer()

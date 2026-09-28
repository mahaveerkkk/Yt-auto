import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from config.settings import settings
from utils.logger import logger
from core.uploader import uploader

class AnalyticsCEO:
    """
    Analytics & Autonomous Strategy Agent.
    Monitors uploaded videos, checks view counts, calculates estimated CTR,
    and conducts automatic post-mortems if a video underperforms.
    """

    def __init__(self):
        self.stats_file = settings.BASE_DIR / "logs" / "video_analytics.json"
        self._cached_summary = None
        self._cache_time = 0
        self._cached_recent = None
        self._recent_time = 0

    def get_channel_summary(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetches total channel views, subscriber count, and video count (cached for 15 mins)."""
        import time
        if not force_refresh and self._cached_summary and (time.time() - self._cache_time < 900):
            return self._cached_summary

        service = uploader.get_youtube_service()
        if not service:
            return self._cached_summary or {"error": "YouTube API not connected"}

        try:
            res = service.channels().list(mine=True, part="snippet,statistics").execute()
            items = res.get("items", [])
            if not items:
                return self._cached_summary or {"error": "Channel not found"}

            ch = items[0]
            stats = ch.get("statistics", {})
            snippet = ch.get("snippet", {})
            self._cached_summary = {
                "channel_name": snippet.get("title", "Void Archive"),
                "total_views": stats.get("viewCount", "0"),
                "subscribers": stats.get("subscriberCount", "0"),
                "video_count": stats.get("videoCount", "0")
            }
            self._cache_time = time.time()
            return self._cached_summary
        except Exception as e:
            logger.error(f"[Analytics] Failed to fetch channel summary: {e}")
            return self._cached_summary or {"error": str(e)}

    def get_recent_videos(self, limit: int = 5, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Fetches the latest videos uploaded to the channel (cached for 15 mins)."""
        import time
        if not force_refresh and self._cached_recent and (time.time() - self._recent_time < 900):
            return self._cached_recent

        service = uploader.get_youtube_service()
        if not service:
            return self._cached_recent or []
        if not service:
            return []

        try:
            # Search channel's uploads
            res = service.search().list(
                forMine=True,
                type="video",
                part="snippet",
                order="date",
                maxResults=limit
            ).execute()

            video_ids = [item["id"]["videoId"] for item in res.get("items", []) if "videoId" in item.get("id", {})]
            if not video_ids:
                return []

            # Get video statistics
            vstats = service.videos().list(
                id=",".join(video_ids),
                part="snippet,statistics"
            ).execute()

            results = []
            for item in vstats.get("items", []):
                vid = item["id"]
                s = item.get("snippet", {})
                st = item.get("statistics", {})
                results.append({
                    "id": vid,
                    "title": s.get("title", ""),
                    "published_at": s.get("publishedAt", ""),
                    "views": int(st.get("viewCount", 0)),
                    "likes": int(st.get("likeCount", 0)),
                    "comments": int(st.get("commentCount", 0)),
                    "url": f"https://youtu.be/{vid}"
                })
            return results
        except Exception as e:
            logger.error(f"[Analytics] Failed to fetch recent videos: {e}")
            return []

    def conduct_diagnostic(self, video_data: Dict[str, Any]) -> str:
        """Analyzes why a video might have low views or how to boost it."""
        views = video_data.get("views", 0)
        likes = video_data.get("likes", 0)
        
        if views == 0:
            return (
                "🔍 **Diagnostic:** Video abhi initial discovery phase me hai. "
                "YouTube algorithm naye channels par 24-48 hours testing impressions bhejta hai. "
                "Advise: Thumbnail aur Title ko sharp rakhein, video delete mat karein."
            )
        elif views < 50:
            return (
                "⚠️ **Diagnostic:** CTR (Click Through Rate) kam ho sakta hai. "
                "Hook text thoda aur dramatic banayein. Video ke pehle 3 seconds me suspense build hona chahiye."
            )
        else:
            engagement_ratio = (likes / views) * 100 if views > 0 else 0
            if engagement_ratio > 8:
                return f"🔥 **Diagnostic:** Excellent engagement ({engagement_ratio:.1f}% like ratio)! Next video is topic se related banayein."
            else:
                return "📈 **Diagnostic:** Views aa rahe hain par viewers interact nahi kar rahe. End me strong Call to Action deinge."

analytics_ceo = AnalyticsCEO()

#!/usr/bin/env python3
"""
🗂️ Void Archive Auto-Playlists Manager
Drives binge-watching sessions to fast-track 4,000 watch hours for monetization.
- Categorizes newly published documentaries into 5 Channel Pillars
- Automatically creates YouTube playlists via YouTube Data API
- Auto-inserts new videos into the matching themed playlist
- Caches playlist states and telemetry in SQLite (studio_memory.db)
"""

from typing import Dict, Any, List, Optional
from utils.logger import logger
from core.uploader import uploader
from core.studio_memory import studio_memory


class PlaylistManager:
    """Automates creation and management of themed binge-watching playlists."""

    PILLAR_PLAYLISTS = [
        {
            "name": "Deep Ocean Abyss & Point Nemo Archives",
            "category": "Ocean",
            "description": "Declassified deep-sea hydrophone anomalies, Point Nemo recordings, and abyssal discoveries.",
            "keywords": ["ocean", "sea", "bloop", "trench", "underwater", "submarine", "abyss"]
        },
        {
            "name": "Cosmic Anomalies & Starless Voids",
            "category": "Space",
            "description": "Investigations into inexplicable deep space radio transmissions, cosmic voids, and astronomical mysteries.",
            "keywords": ["space", "universe", "galaxy", "signal", "astronomy", "cosmic", "void", "wow"]
        },
        {
            "name": "Forbidden Ancient Archaeology & Megaliths",
            "category": "Ancient",
            "description": "Pre-historic stone monuments, submerged lost cities, and ancient engineering anomalies.",
            "keywords": ["ancient", "civilization", "pyramid", "ruins", "history", "atlantis", "megalith"]
        },
        {
            "name": "Classified Aviation & Maritime Disappearances",
            "category": "Aviation",
            "description": "Vanished squadrons, ghost cargo ships, and Bermuda Triangle radar anomalies.",
            "keywords": ["flight", "plane", "maritime", "ship", "bermuda", "radar", "classified", "disappearance"]
        },
        {
            "name": "Quantum Paradoxes & Cosmic Glitches",
            "category": "Quantum",
            "description": "The boundaries of physical law, simulation hypotheses, and quantum mechanical paradoxes.",
            "keywords": ["quantum", "physics", "universe", "reality", "paradox", "glitch"]
        }
    ]

    def _match_pillar(self, title: str, category: str = "") -> Dict[str, Any]:
        """Matches title and category to the most relevant channel pillar."""
        combined = f"{title} {category}".lower()
        for pillar in self.PILLAR_PLAYLISTS:
            if any(k in combined for k in pillar["keywords"]):
                return pillar
        return self.PILLAR_PLAYLISTS[0]  # Default to Deep Ocean

    def get_or_create_playlist(self, pillar: Dict[str, Any]) -> Optional[str]:
        """Fetches existing playlist ID or creates it on YouTube."""
        # 1. Check local DB
        cached = studio_memory.get_playlist_by_category(pillar["category"])
        if cached and cached.get("playlist_id"):
            return cached["playlist_id"]

        service = uploader.get_youtube_service()
        if not service:
            # Fallback to local tracking ID
            local_id = f"PL_LOCAL_{pillar['category'].upper()}"
            studio_memory.save_playlist(local_id, pillar["name"], pillar["category"], "", 0)
            return local_id

        # 2. Check on YouTube
        try:
            res = service.playlists().list(part="snippet", mine=True, maxResults=25).execute()
            for item in res.get("items", []):
                p_title = item.get("snippet", {}).get("title", "")
                if pillar["name"].lower() in p_title.lower() or pillar["category"].lower() in p_title.lower():
                    pid = item.get("id")
                    url = f"https://www.youtube.com/playlist?list={pid}"
                    studio_memory.save_playlist(pid, p_title, pillar["category"], url, 0)
                    return pid
        except Exception as e:
            logger.warning(f"[PlaylistManager] Could not list YouTube playlists: {e}")

        # 3. Create Playlist on YouTube
        try:
            body = {
                "snippet": {
                    "title": pillar["name"],
                    "description": pillar["description"]
                },
                "status": {
                    "privacyStatus": "public"
                }
            }
            created = service.playlists().insert(part="snippet,status", body=body).execute()
            pid = created.get("id")
            url = f"https://www.youtube.com/playlist?list={pid}"
            studio_memory.save_playlist(pid, pillar["name"], pillar["category"], url, 0)
            logger.info(f"[PlaylistManager] 🎉 Created new YouTube playlist: '{pillar['name']}' (ID: {pid})")
            return pid
        except Exception as e:
            logger.warning(f"[PlaylistManager] YouTube API playlist creation skipped (token scope): {e}")
            # Cache virtual playlist for internal organization
            local_id = f"PL_LOCAL_{pillar['category'].upper()}"
            studio_memory.save_playlist(local_id, pillar["name"], pillar["category"], "", 0)
            return local_id

    def slot_video_into_playlist(self, video_id: str, title: str, category: str = "") -> Optional[str]:
        """Slots a newly published documentary into its themed playlist."""
        pillar = self._match_pillar(title, category)
        playlist_id = self.get_or_create_playlist(pillar)

        if not playlist_id:
            return None

        # Add item to YouTube playlist if not local-only
        if not playlist_id.startswith("PL_LOCAL_"):
            service = uploader.get_youtube_service()
            if service:
                try:
                    # Check if already present to avoid duplicates
                    check = service.playlistItems().list(
                        part="id",
                        playlistId=playlist_id,
                        videoId=video_id,
                        maxResults=1
                    ).execute()
                    if check.get("items"):
                        logger.info(f"[PlaylistManager] Video already in playlist '{pillar['name']}', skipping duplicate insert.")
                        return playlist_id

                    body = {
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id
                            }
                        }
                    }
                    service.playlistItems().insert(part="snippet", body=body).execute()
                    logger.info(f"[PlaylistManager] 🗂️ Added '{title[:35]}' to playlist '{pillar['name']}'!")
                except Exception as e:
                    logger.warning(f"[PlaylistManager] Playlist item insert skipped: {e}")

        studio_memory.increment_playlist_count(playlist_id)
        return playlist_id

    def format_playlists_telegram_summary(self) -> str:
        """Formats all playlists and counts for Telegram /playlists command."""
        playlists = studio_memory.get_playlists()
        if not playlists:
            return (
                "🗂️ *Void Archive Pillar Playlists:*\n\n"
                "• 🌊 *Deep Ocean Abyss Archives*\n"
                "• 🌌 *Cosmic Anomalies & Voids*\n"
                "• 🏛️ *Forbidden Ancient Megaliths*\n"
                "• ✈️ *Classified Aviation Disappearances*\n"
                "• ⚛️ *Quantum Paradoxes*\n\n"
                "_Playlists are auto-initialized upon documentary uploads!_"
            )

        lines = ["🗂️ *Void Archive Binge-Watch Playlists:*", ""]
        for p in playlists:
            url_part = f" [Watch]({p['youtube_url']})" if p.get('youtube_url') else ""
            lines.append(f"📁 *{p.get('title')}* — `{p.get('video_count', 0)} videos`{url_part}")

        lines.append("\n_Videos are auto-slotted upon upload to drive 4,000 watch hours!_")
        return "\n".join(lines)


playlist_manager = PlaylistManager()

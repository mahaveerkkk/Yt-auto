#!/usr/bin/env python3
"""
💬 Void Archive Comment Responder & Viewer Idea Hunter
- Scans recent audience comments on channel videos
- Mined viewer topic requests (e.g. 'Please cover Dyatlov Pass') and feeds the Scout candidate pool
- Drafts fascinating, in-character replies in the mysterious BBC/NatGeo narrator voice
- Caches all interactions and reports audience intelligence to Boss via Telegram
"""

import re
from typing import Dict, Any, List, Optional
from utils.logger import logger
from config.settings import settings
from core.uploader import uploader
from core.studio_memory import studio_memory
from core.omni_router import omni_router
from core.worker_manager import worker_manager


class CommentResponder:
    """Automates audience comment engagement and topic mining."""

    TOPIC_TRIGGER_PATTERNS = [
        r"(?:make|do|cover|create)\s+(?:a\s+)?video\s+(?:on|about)\s+([a-zA-Z0-9\s\-\'\"]+)",
        r"(?:please|can\s+you)\s+(?:cover|explain|investigate)\s+([a-zA-Z0-9\s\-\'\"]+)",
        r"(?:what\s+about|next\s+topic\s+should\s+be)\s+([a-zA-Z0-9\s\-\'\"]+)"
    ]

    def _extract_topic_suggestion(self, text: str) -> Optional[str]:
        """Detects if viewer suggested a documentary topic."""
        for pattern in self.TOPIC_TRIGGER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                # Clean punctuation
                candidate = re.sub(r"[?!.,;:]", "", candidate).strip()
                if len(candidate) > 3 and len(candidate) < 70:
                    return candidate

        # Quick check for mystery keywords
        lower = text.lower()
        if any(w in lower for w in ["next video", "please make", "cover this"]):
            return text[:60]
        return None

    def scan_and_respond(self) -> Dict[str, Any]:
        """Scans comments across tracked videos, mines ideas, and drafts replies."""
        worker_manager.start_task("scout", "Scanning YouTube comments for viewer topic ideas")
        service = uploader.get_youtube_service()
        if not service:
            worker_manager.complete_task("scout", "YouTube service unavailable")
            return {"scanned": 0, "topics_mined": 0, "replies_drafted": 0}

        tracked_videos = studio_memory.get_all_videos()
        if not tracked_videos:
            worker_manager.complete_task("scout", "No tracked videos yet")
            return {"scanned": 0, "topics_mined": 0, "replies_drafted": 0}

        new_topics = []
        new_replies = []
        scanned_count = 0

        for v in tracked_videos[:5]:  # Focus on latest 5 videos
            vid = v.get("video_id")
            if not vid:
                continue

            try:
                res = service.commentThreads().list(
                    part="snippet",
                    videoId=vid,
                    maxResults=10,
                    textFormat="plainText"
                ).execute()

                items = res.get("items", [])
                scanned_count += len(items)

                for item in items:
                    snip = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                    cid = item.get("id")
                    author = snip.get("authorDisplayName", "Viewer")
                    text = snip.get("textDisplay", "")

                    if not text:
                        continue

                    # Check for topic suggestion
                    suggested_topic = self._extract_topic_suggestion(text)
                    is_suggestion = 1 if suggested_topic else 0

                    if suggested_topic:
                        new_topics.append({"author": author, "topic": suggested_topic, "video": v.get("title", "")})
                        # Add to content calendar as viewer suggested
                        from datetime import date
                        studio_memory.add_to_calendar(
                            planned_date=date.today().isoformat(),
                            planned_time="19:00",
                            topic=suggested_topic,
                            category=v.get("category", "Viewer Request"),
                            target_duration=600
                        )

                    # Draft smart reply using OmniRouter
                    prompt = (
                        f"A YouTube viewer named {author} left this comment on our mystery documentary '{v.get('title')}':\n"
                        f"\"{text}\"\n\n"
                        f"Write a 1-2 sentence fascinating, appreciative, and thought-provoking reply from 'Void Archive'. "
                        f"Stay in character as an authoritative yet welcoming classified archive. Under 40 words."
                    )
                    reply_text = omni_router.query(prompt=prompt)
                    if not reply_text:
                        reply_text = f"Fascinating observation, {author}. The records on this phenomenon continue to yield unanswered questions."
                    reply_text = reply_text.strip().replace('"', '')[:250]

                    # Save to DB
                    studio_memory.save_viewer_comment(
                        comment_id=cid,
                        video_id=vid,
                        author=author,
                        text=text,
                        is_topic_suggestion=is_suggestion,
                        extracted_topic=suggested_topic or "",
                        reply_text=reply_text,
                        replied=0
                    )
                    new_replies.append({"author": author, "comment": text, "reply": reply_text})

            except Exception as e:
                logger.debug(f"[CommentResponder] Video {vid} comments inspect skipped: {e}")

        worker_manager.complete_task("scout", f"Mined {len(new_topics)} topics from {scanned_count} comments")
        return {
            "scanned": scanned_count,
            "topics_mined": len(new_topics),
            "new_topics": new_topics,
            "replies_drafted": len(new_replies)
        }

    def format_comments_telegram_summary(self) -> str:
        """Formats recent viewer comments and mined topics for Telegram /comments command."""
        topics = studio_memory.get_suggested_topics(limit=5)
        comments = studio_memory.get_recent_comments(limit=6)

        if not comments and not topics:
            return (
                "💬 *Audience Engagement & Idea Radar:*\n\n"
                "Abhi tak channel par naye comments nahi hain.\n"
                "Jaise hi viewers video par comments karenge, bot unke ideas scan karega aur yahan report karega!"
            )

        lines = ["💬 *Audience Feedback & Topic Ideas Radar:*", ""]
        if topics:
            lines.append("💡 *Viewer-Requested Topics (Auto-Added to Pool):*")
            for t in topics:
                lines.append(f"• *{t.get('extracted_topic')}* (by `{t.get('author')}`)")
            lines.append("")

        if comments:
            lines.append("📝 *Recent Viewer Comments & Drafted Replies:*")
            for c in comments[:3]:
                lines.append(f"👤 *{c.get('author')}:* _{c.get('text')[:80]}_")
                if c.get("reply_text"):
                    lines.append(f"   ↳ 👑 *AI Reply:* \"{c.get('reply_text')[:100]}\"")
                lines.append("")

        return "\n".join(lines)


comment_responder = CommentResponder()

#!/usr/bin/env python3
"""
📊 Void Archive Community Tab Manager
Generates high-engagement mystery polls and community posts to warm up the YouTube algorithm:
- Pre-upload teaser polls to create curiosity gaps
- Audience debate questions
- Formatted ready-to-post or automated Community Tab integration
"""

import json
import re
from typing import Dict, Any, Optional
from utils.logger import logger
from core.omni_router import omni_router
from core.scout import scout


class CommunityManager:
    """Generates viral community polls and engagement teasers."""

    def generate_poll_for_topic(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """Generates a 4-option psychological curiosity poll based on topic."""
        chosen_topic = topic
        if not chosen_topic:
            scout_cand = scout.pick_next_viral_topic()
            chosen_topic = scout_cand.get("topic", "The Mariana Trench Acoustic Anomaly")

        prompt = (
            f"Generate an irresistible, high-engagement YouTube Community Tab Poll for the mystery topic: '{chosen_topic}'.\n"
            f"The poll must create an intense debate among mystery & science enthusiasts.\n"
            f"Return ONLY a valid JSON object matching this schema:\n"
            f"{{\n"
            f'  "question": "A suspenseful 1-2 sentence question (under 120 chars)",\n'
            f'  "options": [\n'
            f'    "Option 1 (Plausible scientific theory)",\n'
            f'    "Option 2 (Shocking biological or physical hypothesis)",\n'
            f'    "Option 3 (Classified or extraterrestrial angle)",\n'
            f'    "Option 4 (Chilling alternative)"\n'
            f"  ],\n"
            f'  "teaser_text": "Short 2-line teaser mentioning that the full investigation drops soon on Void Archive."\n'
            f"}}"
        )

        res = omni_router.query(prompt=prompt)
        if res:
            try:
                clean_json = res.strip()
                if "```json" in clean_json:
                    clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json:
                    clean_json = clean_json.split("```")[1].split("```")[0].strip()

                match = re.search(r'(\{[\s\S]*\})', clean_json)
                if match:
                    clean_json = match.group(1)

                parsed = json.loads(clean_json)
                if "question" in parsed and "options" in parsed:
                    return parsed
            except Exception as e:
                logger.warning(f"[CommunityManager] Poll JSON parsing error: {e}")

        # Fallback Poll
        return {
            "question": f"What do you believe actually caused {chosen_topic}?",
            "options": [
                "Uncataloged deep-sea / cosmic organism",
                "Natural geophysical fracture / anomaly",
                "Classified government / military technology",
                "Something beyond current physical models"
            ],
            "teaser_text": "Full declassified documentary dropping on Void Archive. Cast your vote!"
        }

    def format_poll_for_telegram(self, topic: Optional[str] = None) -> str:
        """Formats poll with one-tap copyable text for Telegram /poll command."""
        data = self.generate_poll_for_topic(topic)
        q = data.get("question", "")
        options = data.get("options", [])
        teaser = data.get("teaser_text", "")

        lines = [
            "📊 *YouTube Community Tab Viral Poll Generated!*",
            "",
            f"❓ *Question:*",
            f"`{q}`",
            "",
            "🔘 *Options:*",
        ]
        for i, opt in enumerate(options, start=1):
            lines.append(f"{i}. `{opt}`")

        lines.extend([
            "",
            f"📝 *Post Caption:*",
            f"_{teaser}_",
            "",
            "👉 _Post this on your YouTube Studio -> Community tab to trigger algorithm impressions before the video drops!_"
        ])
        return "\n".join(lines)


community_manager = CommunityManager()

#!/usr/bin/env python3
"""
🔬 Void Archive Autonomous R&D Tech Scout Agent
Continuously monitors emerging open-source tools, GitHub repositories, free AI APIs,
and YouTube algorithm shifts to keep Void Archive ahead of competitors.
Logs all discoveries into studio_memory.db and delivers executive briefings via /tech_radar.
"""

import json
from typing import Dict, Any, List, Optional
from utils.logger import logger
from core.studio_memory import studio_memory
from core.omni_router import omni_router
from core.worker_manager import worker_manager


class TechScout:
    """
    R&D Department Agent:
    - Mines new open-source models (TTS, image gen, faster video rendering).
    - Caches tech intelligence for Boss review.
    - Enables future 1-click codebase upgrades.
    """

    CORE_INNOVATIONS = [
        {
            "tool_name": "Kokoro-82M TTS",
            "category": "voice_tts",
            "source_url": "https://github.com/hexgrad/kokoro",
            "description": "Ultra-lightweight 82M parameter open-source TTS delivering near-ElevenLabs natural voice quality completely offline.",
            "potential_benefit": "Zero cloud reliance, 100% offline BBC narrator voice synthesis with zero API limits."
        },
        {
            "tool_name": "Pollinations FLUX-Schnell",
            "category": "image_gen",
            "source_url": "https://pollinations.ai",
            "description": "High-throughput open AI visual generation API powered by Black Forest Labs FLUX.1 architecture.",
            "potential_benefit": "100% free unlimited 1280x720 photorealistic documentary B-roll with zero GPU cost."
        },
        {
            "tool_name": "Faster-Whisper Subtitle Sync",
            "category": "subtitles_audio",
            "source_url": "https://github.com/SYSTRAN/faster-whisper",
            "description": "Reimplementation of OpenAI Whisper using CTranslate2, delivering 4x faster transcription speed.",
            "potential_benefit": "Word-level kinetic animated subtitles burned into documentaries with zero render lag."
        },
        {
            "tool_name": "FFmpeg VAAPI / NVENC Accelerated Engine",
            "category": "video_rendering",
            "source_url": "https://ffmpeg.org",
            "description": "Hardware-accelerated video transcoding engine utilizing container GPU passes.",
            "potential_benefit": "Reduces 10-minute 1080p documentary rendering time from 4 minutes to under 45 seconds."
        },
        {
            "tool_name": "YouTube Shorts 9:16 Kinetic Hook Looper",
            "category": "viral_algorithm",
            "source_url": "https://voidarchive.internal/shorts-looper",
            "description": "Algorithmic framing that matches first 3 seconds of a Short with the final 2 seconds for a seamless infinite loop.",
            "potential_benefit": "Boosts Shorts Average Percentage Viewed (APV) past 110%, triggering the YouTube Shorts viral shelf."
        }
    ]

    def __init__(self):
        # Seed foundational innovations on first run
        existing = studio_memory.get_tech_discoveries(limit=1)
        if not existing:
            for item in self.CORE_INNOVATIONS:
                studio_memory.record_tech_discovery(
                    tool_name=item["tool_name"],
                    category=item["category"],
                    source_url=item["source_url"],
                    description=item["description"],
                    potential_benefit=item["potential_benefit"]
                )

    def run_tech_scan(self) -> List[Dict[str, Any]]:
        """
        Uses Gemini to research and formulate new AI documentary automation tools and techniques.
        """
        worker_manager.start_task("ai_brain", "Scanning GitHub & AI releases for studio upgrades")

        prompt = (
            "You are the Chief Technology Officer (CTO) for 'Void Archive', an autonomous AI YouTube documentary studio.\n"
            "Identify 2 innovative, 100% free or open-source technologies, Python libraries, or GitHub tools that could "
            "substantially enhance: (1) Voice realism, (2) Video generation speed, (3) Automated sound design, or (4) High-CTR visuals.\n\n"
            "Return ONLY a valid JSON array of 2 objects with this schema:\n"
            "[\n"
            "  {\n"
            "    \"tool_name\": \"Name of tool / model / repo\",\n"
            "    \"category\": \"voice_tts / video_fx / image_gen / seo_tool / github_repo\",\n"
            "    \"source_url\": \"Official github or project url\",\n"
            "    \"description\": \"1 sentence describing what it does\",\n"
            "    \"potential_benefit\": \"How it improves Void Archive quality or efficiency\"\n"
            "  }\n"
            "]"
        )

        discoveries = []
        try:
            res = omni_router.query(prompt=prompt)
            if res:
                clean = res.strip()
                if "[" in clean and "]" in clean:
                    clean = clean[clean.find("["):clean.rfind("]")+1]
                    items = json.loads(clean)
                    for it in items:
                        if it.get("tool_name"):
                            studio_memory.record_tech_discovery(
                                tool_name=it["tool_name"],
                                category=it.get("category", "github_repo"),
                                source_url=it.get("source_url", "https://github.com"),
                                description=it.get("description", ""),
                                potential_benefit=it.get("potential_benefit", "")
                            )
                            discoveries.append(it)
        except Exception as e:
            logger.warning(f"[TechScout] R&D scan error: {e}")

        worker_manager.complete_task("ai_brain", f"Discovered {len(discoveries)} tech upgrades")
        return discoveries

    def format_tech_radar_telegram(self) -> str:
        """
        Formats an executive R&D upgrade briefing for Boss.
        """
        discoveries = studio_memory.get_tech_discoveries(limit=6)
        if not discoveries:
            return "🔬 *R&D Tech Radar:*\nNo discoveries recorded yet. Running scan now..."

        lines = [
            "🔬 *Void Archive — R&D Tech Radar (Future Upgrades)*",
            "Autonomous scout scan of GitHub repos & free AI APIs:\n"
        ]

        cat_icons = {
            "voice_tts": "🎙️",
            "image_gen": "🎨",
            "video_fx": "🎬",
            "subtitles_audio": "📝",
            "video_rendering": "⚡",
            "viral_algorithm": "📈",
            "seo_tool": "🔍",
            "github_repo": "📦"
        }

        for idx, d in enumerate(discoveries, start=1):
            icon = cat_icons.get(d.get("category", ""), "💡")
            lines.append(f"{icon} *{idx}. {d.get('tool_name')}* (`{d.get('category')}`)")
            lines.append(f"   _{d.get('description')}_")
            lines.append(f"   🚀 *Benefit:* {d.get('potential_benefit')}")
            if d.get("source_url"):
                lines.append(f"   🔗 [Project Link]({d.get('source_url')})")
            lines.append("")

        lines.append("👑 *Boss Note:* Yeh saari tools database mein logged hain. Jab aap bologe, hum codebase upgrade execute karenge!")
        return "\n".join(lines)


tech_scout = TechScout()

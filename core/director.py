import json
import re
from typing import Dict, Any, Optional
from config.settings import settings
from utils.logger import logger
from core.omni_router import omni_router
from core.worker_manager import worker_manager


class Director:
    """
    Master Documentary Script & Narrative Director Agent.
    Specialized in Long-Form YouTube Documentaries (8-12 Minutes)
    Designed for High Retention, Watch Time, and Mid-Roll Ad Monetization:
    - 6-Act Hollywood/BBC Documentary Structure
    - Rich atmospheric storytelling (1100-1400 words)
    - 14-18 Distinct Visual Scene Cues with precise Pexels keywords
    - High-CTR Title, SEO tags, and YouTube Chapter Timestamps
    """

    def _build_system_prompt(self, topic: Optional[str] = None, target_duration_sec: int = 480) -> str:
        topic_clause = f"on the mystery topic: '{topic}'" if topic else "on an astonishing, viral cosmic/ocean anomaly"
        target_words = max(800, int((target_duration_sec / 60) * 135))

        return f"""
You are an award-winning BBC / National Geographic documentary screenwriter and YouTube retention architect.
Your mission is to produce a deep, suspenseful, authoritative long-form documentary script {topic_clause}.
Target Duration: ~{target_duration_sec // 60} minutes ({target_words} words minimum).

Structure the narrative into 6 immersive documentary chapters:
1. HOOK (0:00): A startling revelation, emergency transmission, or chilling fact that hooks the audience within 15 seconds.
2. CHAPTER 1 - THE DISCOVERY: The historical incident, geographical isolation, or classified coordinates.
3. CHAPTER 2 - THE SENSOR LOGS: Hard technical/scientific data, audio waveforms, radar recordings, radar blips.
4. CHAPTER 3 - THE EXPEDITION: Human eyewitness accounts, scientific teams, deep-sea submersibles, or deep-space telescopes.
5. CHAPTER 4 - THE COMPETING THEORIES: Mainstream scientific consensus vs. chilling unexplained hypotheses.
6. CONCLUSION & OUTRO: Philosophical reflection on human vulnerability in the cosmos, and Call To Action: "Subscribe to Void Archive for more records from the edge of reality."

CRITICAL JSON SPECIFICATION:
You must output ONLY a valid JSON object without markdown formatting, code ticks, or conversational preamble:
{{
  "title": "A high-CTR, psychological curiosity title under 65 chars (e.g. They Found Something Lurking in the Challenger Deep)",
  "description": "Compelling 3-paragraph SEO documentary synopsis including timestamps and mystery keywords.",
  "hashtags": ["#Mystery", "#DeepSea", "#Documentary", "#VoidArchive", "#Science"],
  "pinned_comment": "A thought-provoking question for the audience to debate in the comments section.",
  "voice_script": "The complete, continuous, immersive documentary narrative ({target_words} words). Write in rich, cinematic English suitable for a deep authoritative narrator. No scene labels or speaker tags in this text.",
  "scenes": [
    {{
      "index": 1,
      "chapter": "Hook",
      "prompt": "Cinematic 8k movie still, eerie isolation, dramatic cinematic lighting",
      "keywords": "space dark galaxy stars"
    }},
    {{
      "index": 2,
      "chapter": "The Event",
      "prompt": "Naval research ship in violent stormy ocean at night, spotlights beaming into black water",
      "keywords": "storm ocean waves ship"
    }},
    {{
      "index": 3,
      "chapter": "Sensor Readings",
      "prompt": "Glowing underwater sonar radar screen showing anomaly signature, green phosphor glow",
      "keywords": "radar screen technology data"
    }},
    {{
      "index": 4,
      "chapter": "The Abyss",
      "prompt": "Deep sea trench underwater camera view, bioluminescent creatures, pure black abyss",
      "keywords": "underwater deep sea ocean"
    }},
    {{
      "index": 5,
      "chapter": "Observatory",
      "prompt": "Astronomical telescope dome open at night under infinite starry sky, cold blue moonlight",
      "keywords": "observatory telescope night stars"
    }},
    {{
      "index": 6,
      "chapter": "Investigation",
      "prompt": "Classified government dossier documents with redacted black ink bars and scientific photographs",
      "keywords": "classified documents desk vintage"
    }},
    {{
      "index": 7,
      "chapter": "Submersible",
      "prompt": "Deep sea exploration submarine lights piercing through murky dark ocean depths",
      "keywords": "submarine underwater deep ocean"
    }},
    {{
      "index": 8,
      "chapter": "Cosmic Anomaly",
      "prompt": "Gigantic mysterious cosmic void in space, glowing nebula edge, cinematic unreal engine 5",
      "keywords": "nebula cosmos outer space"
    }},
    {{
      "index": 9,
      "chapter": "Evidence",
      "prompt": "Vintage 1970s audio reel-to-reel magnetic tape recorder spinning in dark laboratory",
      "keywords": "audio tape recorder laboratory"
    }},
    {{
      "index": 10,
      "chapter": "The Reveal",
      "prompt": "Massive ancient geometric structure submerged beneath shifting ocean sands, 8k render",
      "keywords": "ancient ruins ocean underwater"
    }},
    {{
      "index": 11,
      "chapter": "Theoretical Horizon",
      "prompt": "Theoretical physicists chalkboard covered with complex quantum field equations, chalk dust",
      "keywords": "physics blackboard science formulas"
    }},
    {{
      "index": 12,
      "chapter": "Outro",
      "prompt": "Infinite starfield receding into deep black cosmic horizon, cinematic masterpiece",
      "keywords": "universe space stars horizon"
    }}
  ]
}}
"""

    def generate_manifest(self, topic: Optional[str] = None, target_duration_sec: int = 480) -> Dict[str, Any]:
        """Generates full documentary production manifest using OmniRouter (Gemini / OpenRouter)."""
        worker_manager.start_task("director", f"Directing screenplay for '{topic}' ({target_duration_sec}s)")
        
        sys_prompt = self._build_system_prompt(topic, target_duration_sec)
        user_prompt = (
            f"Generate the comprehensive, long-form documentary screenplay manifest for topic: '{topic}'. "
            f"Ensure rich detail, dramatic pacing, and complete JSON schema compliance."
        )

        raw_output = omni_router.query(prompt=user_prompt, system_prompt=sys_prompt)

        if raw_output:
            try:
                clean_json = raw_output.strip()
                if "```json" in clean_json:
                    clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json:
                    clean_json = clean_json.split("```")[1].split("```")[0].strip()

                match = re.search(r'(\{[\s\S]*\})', clean_json)
                if match:
                    clean_json = match.group(1)

                parsed = json.loads(clean_json)
                if "title" in parsed and "scenes" in parsed and "voice_script" in parsed:
                    logger.info(f"[Director] ✅ Successfully drafted documentary: '{parsed['title']}' ({len(parsed['scenes'])} scenes)")
                    worker_manager.complete_task("director", f"Script complete: {parsed['title']}")
                    return parsed
            except Exception as e:
                logger.warning(f"[Director] JSON parsing error from LLM output: {e}")

        # High-Quality Fallback Manifest
        chosen_topic = topic or "The 1997 Pacific Acoustic Anomaly"
        logger.info(f"[Director] ⚠️ Deploying high-retention structured fallback manifest for '{chosen_topic}'")
        
        fallback = {
            "title": f"The Terrifying Truth Behind {chosen_topic}",
            "description": (
                f"Thousands of meters beneath the desolate surface of the Pacific, sensors recorded a signal that defied all known physics.\n\n"
                f"00:00 - The Isolated Abyss\n"
                f"02:15 - Hydrophone Array 4\n"
                f"04:30 - The Organic Signature\n"
                f"07:00 - Classified Conclusions\n\n"
                f"Subscribe to Void Archive for more investigative records."
            ),
            "hashtags": ["#Mystery", "#OceanAbyss", "#Documentary", "#VoidArchive", "#Science"],
            "pinned_comment": f"Do you believe the mystery of {chosen_topic} was natural, or is something deliberate being hidden? Share your theory below.",
            "voice_script": (
                f"For decades, the deepest trenches of our oceans remained a silent, frozen frontier. "
                f"Yet in the remote coordinates of {chosen_topic}, underwater surveillance arrays detected an anomaly. "
                "The acoustic signature registered over five thousand miles away, exhibiting patterns inconsistent with seismic friction. "
                "Biologists confirmed no known marine organism possessed the physical resonance capable of generating such amplitude. "
                "When oceanographic teams deployed deep submersibles into the coordinates, telemetry data grew erratic. "
                "To this day, the complete military sensor logs remain classified. "
                "As modern science continues to probe the abyssal plains, one sobering question lingers: "
                "are we truly alone in the dark, or is the ocean guarding something ancient and awake? "
                "Subscribe to Void Archive for more classified records from the edge of reality."
            ),
            "scenes": [
                {"index": 1, "prompt": "Deep dark ocean surface at midnight", "keywords": "dark ocean night water"},
                {"index": 2, "prompt": "Underwater sonar military installation", "keywords": "sonar radar underwater screen"},
                {"index": 3, "prompt": "Deep sea research submarine spotlights in dark abyss", "keywords": "submarine underwater deep ocean"},
                {"index": 4, "prompt": "Scientific monitoring waveforms on vintage displays", "keywords": "laboratory audio oscilloscope screen"},
                {"index": 5, "prompt": "Enormous shadow moving in deep oceanic waters", "keywords": "ocean abyss dark water"},
                {"index": 6, "prompt": "Night sky over calm infinite ocean horizon", "keywords": "ocean stars night horizon"}
            ]
        }
        worker_manager.complete_task("director", "Fallback screenplay generated")
        return fallback


director = Director()

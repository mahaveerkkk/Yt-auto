import asyncio
from pathlib import Path
from typing import Tuple, Optional
from config.settings import settings
from utils.logger import logger


class VoiceEngine:
    """
    Text-to-Speech & Subtitle Generator using Microsoft Edge Neural Voices (edge-tts).
    Zero cost, no API key required, natural Indian Hindi and English accents.
    """

    def __init__(self):
        self.temp_dir = settings.TEMP_DIR

    def get_voice(self, language: str = "hi", gender: str = "male") -> str:
        """Selects appropriate natural voice based on language and gender."""
        lang = language.lower()
        if "hi" in lang:
            return settings.VOICE_HI_MALE if gender == "male" else settings.VOICE_HI_FEMALE
        else:
            return settings.VOICE_EN_MALE if gender == "male" else settings.VOICE_EN_FEMALE

    async def _generate_async(self, text: str, voice: str, audio_path: Path, srt_path: Path) -> bool:
        """Async implementation calling edge_tts."""
        try:
            import edge_tts

            logger.info(f"[VoiceEngine] Synthesizing speech with voice '{voice}'...")
            communicate = edge_tts.Communicate(text, voice)

            sub_maker = edge_tts.SubMaker()
            with open(audio_path, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
                    elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                        sub_maker.feed(chunk)

            # Generate SRT subtitle content
            srt_content = sub_maker.get_srt()
            with open(srt_path, "w", encoding="utf-8") as srt_file:
                srt_file.write(srt_content)

            logger.info(f"[VoiceEngine] Audio saved to {audio_path.name}, Subtitles to {srt_path.name}")
            return True
        except Exception as e:
            logger.error(f"[VoiceEngine] Error in speech synthesis: {e}")
            return False

    def generate_voiceover(
        self,
        script_text: str,
        language: str = "hi",
        gender: str = "male"
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Synchronous wrapper:
        Takes script text -> Returns (audio_path, srt_path)
        """
        if not script_text or not script_text.strip():
            logger.warning("[VoiceEngine] Empty script provided, skipping voiceover.")
            return None, None

        audio_path = self.temp_dir / "voice.mp3"
        srt_path = self.temp_dir / "subtitles.srt"
        voice = self.get_voice(language, gender)

        success = asyncio.run(self._generate_async(script_text, voice, audio_path, srt_path))
        if success and audio_path.exists():
            return audio_path, srt_path
        return None, None


voice_engine = VoiceEngine()

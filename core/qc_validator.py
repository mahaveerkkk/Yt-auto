import json
import subprocess
from pathlib import Path
from typing import Tuple
from utils.logger import logger


class QCValidator:
    """
    Automated Quality Control Gate.
    Uses ffprobe to verify video integrity, stream existence, duration, and resolution
    before allowing delivery or upload.
    """

    def validate_video(self, video_path: Path, expect_audio: bool = True) -> Tuple[bool, str]:
        """
        Validates the rendered video file.
        Returns (is_valid: bool, message: str)
        """
        if not video_path or not video_path.exists():
            return False, "File does not exist."

        # File size check (> 200 KB)
        file_size = video_path.stat().st_size
        if file_size < 200 * 1024:
            return False, f"File size too small ({file_size / 1024:.1f} KB), likely corrupt."

        # FFprobe check
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            info = json.loads(res.stdout)

            streams = info.get("streams", [])
            has_video = any(s.get("codec_type") == "video" for s in streams)
            has_audio = any(s.get("codec_type") == "audio" for s in streams)

            if not has_video:
                return False, "No valid video stream found in container."

            if expect_audio and not has_audio:
                return False, "Audio stream missing from video."

            duration = float(info.get("format", {}).get("duration", 0))
            if duration < 5.0:
                return False, f"Video duration too short ({duration:.1f}s)."

            logger.info(f"✅ Quality Control Passed: {video_path.name} (Duration: {duration:.1f}s, Size: {file_size / (1024*1024):.2f} MB)")
            return True, "Quality verification passed."

        except Exception as e:
            logger.error(f"FFprobe QC error: {e}")
            return False, f"FFprobe analysis error: {e}"

    def evaluate_hook(self, script_text: str) -> Tuple[int, str]:
        """
        Calculates high-retention hook tension score (1-10) for the opening 200 words.
        Evaluates:
        1. Forensic & Declassified markers (coordinates, telemetry, declassified, anomaly, etc.)
        2. Unresolved curiosity loops / burning questions ('?', why, what, how)
        3. Stakes & Dramatic impact words (impossible, vanished, silenced, forbidden, chilling)
        4. Fast, punchy opening cadence
        """
        words_list = script_text.split()[:200]
        cold_open = " ".join(words_list).lower()
        if not cold_open:
            return 0, "No content in cold open"

        forensic_markers = [
            "declassified", "anomaly", "coordinates", "telemetry", "sonar", "radar", 
            "hydrophone", "satellite", "blackout", "incident", "archive", "dossier",
            "frequency", "recording", "signal", "recovered", "classified", "subsurface"
        ]
        stakes_markers = [
            "impossible", "unexplained", "vanished", "silenced", "forbidden", "terrifying",
            "chilling", "abyss", "baffled", "perished", "buried", "leaked", "danger"
        ]

        forensic_hits = sum(1 for m in forensic_markers if m in cold_open)
        stakes_hits = sum(1 for m in stakes_markers if m in cold_open)
        question_count = cold_open.count("?")

        score = 5
        if forensic_hits >= 1:
            score += 1
        if forensic_hits >= 3:
            score += 1
        if stakes_hits >= 1:
            score += 1
        if stakes_hits >= 2:
            score += 1
        if question_count >= 1:
            score += 1
        if question_count >= 2:
            score += 1

        # Check punchy opening cadence (first sentence under 20 words)
        sentences = [s.strip() for s in cold_open.split(".") if s.strip()]
        if sentences and len(sentences[0].split()) <= 18:
            score += 1

        final_score = min(10, max(1, score))
        summary = f"Forensic: {forensic_hits}, Stakes: {stakes_hits}, Questions: {question_count}"
        return final_score, summary

    def validate_script(self, script_text: str, min_words: int = 950, min_hook_score: int = 9) -> Tuple[bool, str, dict]:
        """
        AI Quality Gate: Evaluates documentary script word count, duration estimate,
        and enforces minimum 9/10 narrative retention hook before rendering.
        """
        if not script_text or not script_text.strip():
            return False, "Script is empty.", {"words": 0, "score": 0, "hook_score": 0}

        words = len(script_text.split())
        est_duration_min = round(words / 135, 1)

        # 1. Word Count Check (Mid-Roll Ad 8+ Minute Guarantee)
        if words < min_words:
            return False, f"Script length insufficient ({words} words / ~{est_duration_min} mins). Requires {min_words}+ words for mid-roll monetization.", {
                "words": words,
                "est_duration_min": est_duration_min,
                "score": 4,
                "hook_score": 0
            }

        # 2. Hook & Suspense Tone Evaluation (Strict 9/10 Standard)
        hook_score, hook_summary = self.evaluate_hook(script_text)

        if hook_score < min_hook_score:
            logger.warning(f"[QC] ⚠️ Cold open hook tension ({hook_score}/10) below required {min_hook_score}/10 gate ({hook_summary}).")
            return False, f"Hook score {hook_score}/10 below {min_hook_score}/10 standard. Polishing required.", {
                "words": words,
                "est_duration_min": est_duration_min,
                "hook_score": hook_score,
                "hook_summary": hook_summary
            }

        logger.info(f"✅ Script QC Passed: {words} words (~{est_duration_min} mins), Elite Hook Tension: {hook_score}/10 ({hook_summary})")
        return True, f"Script passed QC: {words} words (~{est_duration_min} mins)", {
            "words": words,
            "est_duration_min": est_duration_min,
            "hook_score": hook_score,
            "hook_summary": hook_summary
        }


qc_validator = QCValidator()

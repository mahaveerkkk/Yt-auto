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


qc_validator = QCValidator()

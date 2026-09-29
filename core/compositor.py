import os
import time
import subprocess
from pathlib import Path
from typing import List, Optional
from config.settings import settings
from utils.logger import logger

settings.ensure_directories()


class Compositor:
    """
    Video Assembly & Post-Production Engine.
    Conforms all clips to standardized 9:16 Shorts format, merges clips without lag,
    mixes narrator voice & background music, and handles subtitle burning.
    """

    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.target_w = settings.VIDEO_WIDTH
        self.target_h = settings.VIDEO_HEIGHT
        self.target_fps = settings.VIDEO_FPS

    def _run_ffmpeg(self, cmd: List[str]) -> bool:
        """Executes FFmpeg command with standard error logging."""
        try:
            logger.info(f"Running FFmpeg: {' '.join(cmd[:6])}...")
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr[-300:] if e.stderr else e}")
            return False

    def normalize_clip(self, input_clip: Path, output_clip: Path, duration: int = 5, width: Optional[int] = None, height: Optional[int] = None) -> bool:
        """
        Normalizes any clip to standard resolution (default 1280x720 landscape, or 720x1280 portrait), 30 FPS, H.264/AAC.
        Maintains original aspect ratio with neat pillarbox/letterbox padding.
        """
        w = width or self.target_w
        h = height or self.target_h
        vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_clip),
            "-t", str(duration),
            "-vf", vf,
            "-r", str(self.target_fps),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-ar", "48000",
            "-pix_fmt", "yuv420p",
            str(output_clip)
        ]
        return self._run_ffmpeg(cmd)

    def concat_clips(self, clips: List[Path], output_path: Path) -> bool:
        """
        Fast-concatenates a list of already normalized clips using concat demuxer.
        """
        if not clips:
            logger.error("No clips provided for concatenation.")
            return False

        list_file = settings.TEMP_DIR / "concat_list.txt"
        with open(list_file, "w") as f:
            for clip in clips:
                f.write(f"file '{clip.resolve()}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path)
        ]
        success = self._run_ffmpeg(cmd)
        if list_file.exists():
            list_file.unlink()
        return success

    def add_voice_and_music(
        self,
        video_path: Path,
        voice_path: Optional[Path],
        music_path: Optional[Path],
        output_path: Path
    ) -> bool:
        """
        Mixes narrator voice with optional background music.
        Ducks background music to 15% volume when narrator voice is present.
        """
        if not voice_path and not music_path:
            # No additional audio needed
            import shutil
            shutil.copy(video_path, output_path)
            return True

        if voice_path and not music_path:
            # Just overlay voice
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(voice_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(output_path)
            ]
            return self._run_ffmpeg(cmd)

        if voice_path and music_path:
            # Mix voice (100% volume) with background music (15% volume)
            filter_complex = "[1:a]volume=1.0[v];[2:a]volume=0.15[m];[v][m]amix=inputs=2:duration=first[a]"
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(voice_path),
                "-i", str(music_path),
                "-filter_complex", filter_complex,
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(output_path)
            ]
            return self._run_ffmpeg(cmd)

        if music_path and not voice_path:
            # Just background music
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(music_path),
                "-filter_complex", "[1:a]volume=0.4[a]",
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(output_path)
            ]
            return self._run_ffmpeg(cmd)

        return False

    def burn_subtitles(self, video_path: Path, srt_path: Path, output_path: Path) -> bool:
        """
        Hardcodes styled subtitles (Bold yellow text with black border) onto video.
        """
        if not srt_path or not srt_path.exists():
            import shutil
            shutil.copy(video_path, output_path)
            return True

        # Viral style: Yellow bold text with black border
        sub_style = "force_style='FontSize=26,Bold=1,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=50'"
        vf = f"subtitles={srt_path.resolve()}:{sub_style}"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "copy",
            str(output_path)
        ]
        return self._run_ffmpeg(cmd)

    def assemble_full_video(
        self,
        raw_clips: List[Path],
        voice_audio: Optional[Path] = None,
        subtitles_srt: Optional[Path] = None,
        bg_music: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Master Pipeline Method:
        1. Normalizes all raw clips
        2. Merges them into one video
        3. Layers voice & music
        4. Burns styled subtitles
        Returns path to final ready-to-upload MP4.
        """
        if not raw_clips:
            logger.error("No video clips available to assemble.")
            return None

        # Step 1: Normalize all clips
        normalized_clips = []
        logger.info(f"Normalizing {len(raw_clips)} clips to standard 9:16 Shorts format...")
        for i, clip in enumerate(raw_clips):
            norm_path = settings.TEMP_DIR / f"norm_{i:02d}.mp4"
            if self.normalize_clip(clip, norm_path, duration=settings.SCENE_DURATION_SEC):
                normalized_clips.append(norm_path)

        if not normalized_clips:
            logger.error("Failed to normalize clips.")
            return None

        # Step 2: Concat normalized clips
        merged_video = settings.TEMP_DIR / "merged_raw.mp4"
        logger.info("Merging normalized clips...")
        if not self.concat_clips(normalized_clips, merged_video):
            return None

        # Step 3: Mix Voice & Music
        video_with_audio = settings.TEMP_DIR / "video_with_audio.mp4"
        logger.info("Mixing audio streams...")
        if not self.add_voice_and_music(merged_video, voice_audio, bg_music, video_with_audio):
            video_with_audio = merged_video

        # Step 4: Burn Subtitles (if available)
        final_output = settings.OUTPUT_DIR / f"short_{int(time.time())}.mp4"
        logger.info("Adding dynamic subtitles...")
        if subtitles_srt and subtitles_srt.exists():
            if not self.burn_subtitles(video_with_audio, subtitles_srt, final_output):
                final_output = video_with_audio
        else:
            import shutil
            shutil.copy(video_with_audio, final_output)

        logger.info(f"🎉 Final Video successfully created: {final_output}")
        return final_output


compositor = Compositor()

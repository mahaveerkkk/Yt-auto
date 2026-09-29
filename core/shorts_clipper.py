#!/usr/bin/env python3
"""
🎬 Void Archive Shorts Clipper Engine
Automatically converts the hook of any 16:9 long-form documentary into a 9:16 vertical YouTube Short.
- High-retention cinematic format: 1080x1920 with ambient blurred background & centered sharp visual
- Audio fade-out & top/bottom retention cards
- Direct YouTube publishing with #Shorts tag to drive massive traffic to the full video
"""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from config.settings import settings
from utils.logger import logger
from core.uploader import uploader
from core.worker_manager import worker_manager


class ShortsClipper:
    """Clips long-form documentaries into high-impact YouTube Shorts."""

    def __init__(self):
        self.output_dir = settings.TEMP_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_short(
        self,
        long_video_path: Path,
        title: str,
        category: str = "Mystery",
        duration_sec: int = 48
    ) -> Optional[Path]:
        """
        Clips the first `duration_sec` of the master documentary and re-formats into 9:16 (1080x1920).
        """
        if not long_video_path.exists():
            logger.error(f"[ShortsClipper] Long video file not found at: {long_video_path}")
            return None

        worker_manager.start_task("producer", f"Clipping viral 9:16 Short from: {title[:40]}...")
        out_short_path = self.output_dir / "short_hook.mp4"
        if out_short_path.exists():
            try:
                out_short_path.unlink()
            except Exception:
                pass

        logger.info(f"[ShortsClipper] Rendering {duration_sec}s YouTube Short from master documentary...")

        # FFmpeg filter:
        # 1. Background: scale to cover 1080x1920, crop, heavy boxblur
        # 2. Foreground: scale to width 1080, centered overlay
        # 3. Top branding: VOID ARCHIVE | CLASSIFIED
        # 4. Bottom CTA: FULL INVESTIGATION ON CHANNEL 👇
        # 5. Audio: fade-out at the end
        fade_start = max(1, duration_sec - 2)

        # Lightweight 720x1280 vertical standard format (prevents Linux OOM SIGKILL -9)
        filter_graph = (
            f"[0:v]scale=360:640:force_original_aspect_ratio=increase,crop=360:640,boxblur=6:1,scale=720:1280[bg];"
            f"[0:v]scale=720:-1[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
            f"[base]drawtext=text='VOID ARCHIVE | CLASSIFIED':fontcolor=white:fontsize=32:x=(w-text_w)/2:y=140:box=1:boxcolor=black@0.65:boxborderw=8,"
            f"drawtext=text='FULL INVESTIGATION ON CHANNEL 👇':fontcolor=yellow:fontsize=26:x=(w-text_w)/2:y=h-180:box=1:boxcolor=black@0.65:boxborderw=8[v];"
            f"[0:a]afade=t=out:st={fade_start}:d=2[a]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-ss", "0",
            "-t", str(duration_sec),
            "-i", str(long_video_path),
            "-filter_complex", filter_graph,
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            str(out_short_path)
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            logger.info(f"[ShortsClipper] ✅ Viral Short successfully rendered: {out_short_path}")
            worker_manager.complete_task("producer", "YouTube Short rendering complete")
            return out_short_path
        except subprocess.CalledProcessError as e:
            logger.error(f"[ShortsClipper] FFmpeg failed with code {e.returncode}: {e.stderr[-400:]}")
            worker_manager.report_error("producer", f"Shorts clipping failed: {e.returncode}")
            return None
        except Exception as ex:
            logger.error(f"[ShortsClipper] Unexpected error clipping short: {ex}")
            return None

    def publish_short(
        self,
        short_video_path: Path,
        title: str,
        long_video_url: str = "",
        category: str = "Mystery"
    ) -> Optional[str]:
        """
        Uploads the 9:16 vertical video as a YouTube Short.
        """
        if not short_video_path or not short_video_path.exists():
            return None

        # Clean title ensuring #Shorts tag is present
        short_title = f"{title[:70]} #Shorts #Mystery"
        description = (
            f"Watch the full classified investigation: {long_video_url}\n\n"
            f"Subscribe to Void Archive for daily deep-dive documentaries into unexplainable anomalies.\n\n"
            f"#Shorts #{category.replace(' ', '')} #Mystery #VoidArchive #Documentary"
        )
        tags = ["Shorts", "Short", "Mystery", "Void Archive", category, "Unexplained", "Documentary"]

        logger.info(f"[ShortsClipper] Uploading Short to YouTube: '{short_title}'...")
        short_manifest = {
            "title": short_title,
            "description": description,
            "hashtags": tags
        }
        try:
            yt_url = uploader.upload_to_youtube(
                video_path=short_video_path,
                manifest=short_manifest,
                privacy_status="public"
            )

            if yt_url:
                import urllib.parse
                parsed_url = urllib.parse.urlparse(yt_url)
                qs = urllib.parse.parse_qs(parsed_url.query)
                video_id = qs.get('v', [parsed_url.path.split('/')[-1]])[0]
                short_url = f"https://youtube.com/shorts/{video_id}"
                logger.info(f"[ShortsClipper] 🚀 YouTube Short published live: {short_url}")
                return short_url
        except Exception as e:
            logger.error(f"[ShortsClipper] Failed to publish YouTube Short: {e}")
        return None


shorts_clipper = ShortsClipper()

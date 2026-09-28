#!/usr/bin/env python3
"""
AutoDirector - Autonomous AI Video Production Engine
Master CLI and Autonomous Cron Entrypoint
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import settings
from core import director, video_engine, voice_engine, compositor, qc_validator, uploader
from notifier import notifier
from utils import logger, clean_temp_storage


def run_pipeline(topic: str = None, mode: str = "fast", dry_run: bool = False, keep_temp: bool = False) -> bool:
    """Runs a single end-to-end video creation & delivery cycle."""
    logger.info("==================================================")
    logger.info("🚀 Starting AutoDirector Autonomous Production Run")
    logger.info("==================================================")

    settings.ensure_directories()

    try:
        # 1. AI Director: Script & Scene Generation
        logger.info("Step 1: Generating Production Manifest...")
        manifest = director.generate_manifest(topic)
        title = manifest.get("title", "Untitled Short")
        hashtags = " ".join(manifest.get("hashtags", []))
        scenes = manifest.get("scenes", [])
        logger.info(f"Target Video Title: {title}")

        # 2. Video Engine: Generate & Download Video Parts
        logger.info(f"Step 2: Generating Scene Video Clips (Mode: {mode})...")
        raw_clips = video_engine.generate_all_scenes(scenes, mode=mode)
        if not raw_clips or len(raw_clips) < 2:
            raise RuntimeError(f"Insufficient video clips generated ({len(raw_clips)} clips). Aborting.")

        # 3. Voice Engine: Conditional Voiceover & Subtitles
        voice_path = None
        subtitles_path = None
        if manifest.get("voice_needed", True):
            logger.info("Step 3: Generating Natural Voiceover & Subtitle Timings...")
            voice_script = manifest.get("voice_script", "")
            voice_path, subtitles_path = voice_engine.generate_voiceover(
                voice_script, language=settings.DEFAULT_LANGUAGE
            )

        # 4. Compositor: Assemble & Post-Production
        logger.info("Step 4: Assembling Normalized 9:16 Video...")
        # Check if background music exists
        bg_music = None
        for music_file in settings.MUSIC_DIR.glob("*.mp3"):
            bg_music = music_file
            break

        final_video = compositor.assemble_full_video(
            raw_clips=raw_clips,
            voice_audio=voice_path,
            subtitles_srt=subtitles_path,
            bg_music=bg_music
        )

        if not final_video or not final_video.exists():
            raise RuntimeError("Compositor failed to produce final video.")

        # 5. Quality Control Validation
        logger.info("Step 5: Running Quality Control Gate...")
        is_valid, qc_msg = qc_validator.validate_video(
            final_video, expect_audio=manifest.get("voice_needed", True)
        )
        if not is_valid:
            raise RuntimeError(f"Quality Control Check Failed: {qc_msg}")

        # 6. Delivery (Telegram / YouTube)
        caption = f"🎬 {title}\n\n{manifest.get('description', '')}\n\n{hashtags}"
        if not dry_run:
            logger.info("Step 6: Delivering Video...")
            uploader.send_to_telegram(final_video, caption)
            uploader.upload_to_youtube(final_video, manifest)
            notifier.notify_success(title, duration=len(raw_clips) * 5.0, scene_count=len(raw_clips))
        else:
            logger.info(f"[Dry Run] Final video ready at: {final_video} (Upload skipped)")

        # 7. Auto Garbage Collection
        if not keep_temp:
            logger.info("Step 7: Cleaning up temporary intermediate files...")
            clean_temp_storage(keep_final=dry_run)

        logger.info("==================================================")
        logger.info("🎉 Autonomous Production Cycle Completed Successfully!")
        logger.info("==================================================")
        return True

    except Exception as e:
        logger.error(f"❌ Pipeline failed with error: {e}", exc_info=True)
        notifier.notify_failure("Pipeline Run", str(e))
        if not keep_temp:
            clean_temp_storage(keep_final=False)
        return False


def main():
    parser = argparse.ArgumentParser(description="AutoDirector - Autonomous AI Video Production Engine")
    parser.add_argument("--topic", type=str, default=None, help="Custom video topic prompt")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    parser.add_argument("--mode", type=str, default="fast", choices=["fast", "ai"], help="Generation mode: 'fast' (Stock HD) or 'ai' (Cloud AI)")
    parser.add_argument("--dry-run", action="store_true", help="Generate video without uploading/sending")
    parser.add_argument("--keep-temp", action="store_true", help="Do not delete temporary files after run")

    args = parser.parse_args()

    for i in range(1, args.count + 1):
        if args.count > 1:
            logger.info(f"\n>>> Running Production Batch {i}/{args.count} <<<")
        success = run_pipeline(topic=args.topic, mode=args.mode, dry_run=args.dry_run, keep_temp=args.keep_temp)
        if not success and i < args.count:
            logger.warning("Retrying next iteration...")


if __name__ == "__main__":
    main()

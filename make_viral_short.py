#!/usr/bin/env python3
"""
AutoDirector - High-Retention Viral Cinematic Production Engine
Uses Clean Official FLUX 4K + 3D Ken Burns Motion + Deep Documentary Voice + Kinetic Subtitles
"""

import os
import sys
import time
import shutil
import asyncio
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import settings
from utils.logger import logger
from core.uploader import uploader

TEMP_DIR = Path("/tmp/autodirector_viral")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

SCENES_DATA = [
    {
        "prompt": "Deep dark stormy Pacific ocean at midnight, mysterious research vessel with powerful yellow spotlights shining into black water, cinematic 8k photorealistic, unreal engine 5, volumetric fog",
        "zoom_type": "in"
    },
    {
        "prompt": "Deep underwater ocean abyss at thirty thousand feet, underwater submersible exploration submarine, bright headlights cutting through murky black abyss, photorealistic 8k, highly detailed",
        "zoom_type": "pan_down"
    },
    {
        "prompt": "Giant mysterious prehistoric creature silhouette lurking in deep underwater ocean trench, bioluminescent glowing cyan eyes, terrifying scale, cinematic lighting, 8k",
        "zoom_type": "in"
    },
    {
        "prompt": "Green glowing sonar radar screen in dark submarine control room showing massive unidentified moving biological anomaly, cinematic 8k",
        "zoom_type": "out"
    }
]

VOICE_SCRIPT = (
    "Deep in the Pacific Ocean, at thirty-six thousand feet, "
    "scientists lowered a specialized microphone into the Mariana Trench. "
    "At first, there was only pitch-black silence. "
    "Then, the sensors captured an unexplained mechanical hum... "
    "followed by a massive metallic sound. "
    "To this day, science cannot explain what made it."
)


def generate_voice_and_srt() -> tuple:
    """Generates deep, commanding documentary voiceover with edge-tts."""
    import edge_tts

    audio_path = TEMP_DIR / "voice.mp3"
    raw_srt_path = TEMP_DIR / "subtitles.srt"

    logger.info("[Voice] Synthesizing deep Christopher documentary voice...")

    async def _synth():
        comm = edge_tts.Communicate(VOICE_SCRIPT, "en-US-ChristopherNeural", rate="+10%")
        sub_maker = edge_tts.SubMaker()
        with open(audio_path, "wb") as f:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    sub_maker.feed(chunk)

        with open(raw_srt_path, "w", encoding="utf-8") as srt_file:
            srt_file.write(sub_maker.get_srt())

    asyncio.run(_synth())
    return audio_path, raw_srt_path


def generate_flux_images() -> list:
    """Generates 4 clean, zero-watermark 4K visuals using official FLUX.1-schnell."""
    from gradio_client import Client

    logger.info("[FLUX.1] Connecting to official Black Forest Labs FLUX.1-schnell...")
    client = Client("black-forest-labs/FLUX.1-schnell", token=settings.HF_TOKEN)

    image_paths = []
    for i, sc in enumerate(SCENES_DATA, start=1):
        target_img = TEMP_DIR / f"scene_{i}.webp"
        logger.info(f"[FLUX.1] Generating Scene {i}/4: '{sc['prompt'][:45]}...'")
        res = client.predict(
            prompt=sc["prompt"],
            seed=i * 111,
            randomize_seed=True,
            width=1280,
            height=720,
            num_inference_steps=4,
            api_name="/infer"
        )
        src_path = res[0]
        if isinstance(src_path, dict):
            src_path = src_path.get("path")
        shutil.copy(src_path, target_img)
        logger.info(f"[FLUX.1] Scene {i} saved successfully.")
        image_paths.append((target_img, sc["zoom_type"]))

    return image_paths


def create_3d_motion_clips(image_data: list, duration_per_clip: float = 4.5) -> list:
    """Applies smooth 60fps Ken Burns 3D motion (Zoom in, Pan, Zoom out) to each visual."""
    clip_paths = []
    frames = int(duration_per_clip * 30)

    for i, (img_path, motion_type) in enumerate(image_data, start=1):
        out_clip = TEMP_DIR / f"motion_{i}.mp4"
        logger.info(f"[Motion] Creating 3D camera movement for Scene {i} ({motion_type})...")

        if motion_type == "in":
            # Smooth slow zoom in
            vf = f"zoompan=z='min(zoom+0.0018,1.25)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps=30"
        elif motion_type == "out":
            # Smooth slow zoom out
            vf = f"zoompan=z='if(lte(zoom,1.0),1.25,max(1.001,zoom-0.0018))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps=30"
        else:
            # Smooth pan down
            vf = f"zoompan=z=1.15:d={frames}:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),(ih-ih/zoom)/4,y+0.6)':s=1280x720:fps=30"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", vf,
            "-t", str(duration_per_clip),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            str(out_clip)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        clip_paths.append(out_clip)

    return clip_paths


def assemble_final_viral_video(clips: list, voice_path: Path, srt_path: Path) -> Path:
    """Fast merges motion clips, mixes voice + dark ambient suspense drone, burns kinetic subtitles."""
    # 1. Concat motion clips
    concat_list = TEMP_DIR / "list.txt"
    with open(concat_list, "w") as f:
        for c in clips:
            f.write(f"file '{c.resolve()}'\n")

    merged_video = TEMP_DIR / "merged.mp4"
    logger.info("[Assembly] Merging 3D camera clips...")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(merged_video)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # 2. Generate atmospheric suspense drone
    logger.info("[Audio] Generating deep suspense sub-bass ambience...")
    drone_path = TEMP_DIR / "drone.mp3"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "anoisesrc=d=30:c=pink:r=48000:a=0.04,lowpass=f=220",
        "-f", "lavfi", "-i", "sine=frequency=48:duration=30",
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first[a];[a]volume=0.22[out]",
        "-map", "[out]",
        str(drone_path)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 3. Mix audio (Voice 100% + Ambient Drone 20%)
    video_with_audio = TEMP_DIR / "video_audio.mp4"
    logger.info("[Assembly] Layering documentary voiceover and cinematic score...")
    filter_complex = "[1:a]volume=1.0[v];[2:a]volume=0.20[m];[v][m]amix=inputs=2:duration=first[a]"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(merged_video),
        "-i", str(voice_path),
        "-i", str(drone_path),
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(video_with_audio)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 4. Burn styled kinetic subtitles (Bold Yellow font, black outline, centered)
    final_output = TEMP_DIR / "The_Mariana_Trench_Mystery.mp4"
    logger.info("[Assembly] Burning kinetic subtitles...")
    sub_style = "force_style='FontSize=26,Bold=1,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=45'"
    vf = f"subtitles={srt_path.resolve()}:{sub_style}"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(video_with_audio),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "copy",
        str(final_output)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return final_output


def main():
    logger.info("==================================================")
    logger.info("🎬 GENERATING PRO VIRAL SHORT: THE MARIANA TRENCH")
    logger.info("==================================================")

    # 1. Voice
    voice_path, srt_path = generate_voice_and_srt()

    # 2. Clean 4K FLUX Visuals
    images = generate_flux_images()

    # 3. 3D Camera Movement
    clips = create_3d_motion_clips(images, duration_per_clip=4.5)

    # 4. Assembly & Sound Design & Subtitles
    final_video = assemble_final_viral_video(clips, voice_path, srt_path)

    # 5. Telegram Delivery
    caption = (
        "🎬 The Mariana Trench Mystery #Shorts\n\n"
        "What did the acoustic sensors detect at 36,000 feet? "
        "A sound that science still cannot explain.\n\n"
        "#Mystery #Ocean #DeepSea #Discovery #Unexplained"
    )
    logger.info("[Telegram] Sending Master Viral Short to your phone...")
    uploader.send_to_telegram(final_video, caption)

    logger.info("==================================================")
    logger.info("🎉 MASTER SHORT DELIVERED! CHECK YOUR TELEGRAM!")
    logger.info("==================================================")


if __name__ == "__main__":
    main()

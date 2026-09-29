#!/usr/bin/env python3
"""
🔊 Void Archive Cinematic SFX Generator
Generates 5 royalty-free, high-impact sound design elements using FFmpeg synthesis:
1. sfx_braam.mp3 - Inception-style cinematic sub-bass brass/horn drop (40Hz fundamental with slow decay)
2. sfx_whoosh.mp3 - Dynamic filtered white-noise transition riser
3. sfx_static.mp3 - Vintage military radio / classified audio telemetry burst
4. sfx_heartbeat.mp3 - Sub-audible lowpass heartbeat thud (35Hz)
5. sfx_riser.mp3 - Eerie suspense riser for act climaxes
"""

import subprocess
from pathlib import Path

SFX_DIR = Path(__file__).resolve().parent / "sfx"
SFX_DIR.mkdir(parents=True, exist_ok=True)


def generate_all_sfx():
    print("🔊 Synthesizing Void Archive Cinematic SFX Library...")

    # 1. Cinematic Braam (Deep Sub-Bass Horn Drop) - 4 seconds
    braam_path = SFX_DIR / "sfx_braam.mp3"
    cmd_braam = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=42:duration=4",
        "-f", "lavfi", "-i", "sine=frequency=84:duration=4",
        "-f", "lavfi", "-i", "anoisesrc=d=4:c=brown:r=48000:a=0.03",
        "-filter_complex",
        "[0:a]volume=1.0[s1];[1:a]volume=0.4[s2];[2:a]lowpass=f=250,volume=0.3[n];"
        "[s1][s2][n]amix=inputs=3:duration=first[mix];"
        "[mix]afade=t=in:st=0:d=0.05,afade=t=out:st=1.2:d=2.8,volume=1.4[out]",
        "-map", "[out]",
        str(braam_path)
    ]
    subprocess.run(cmd_braam, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  ✅ Generated: {braam_path.name}")

    # 2. Transition Whoosh (Filtered Dynamic Sweep) - 1.5 seconds
    whoosh_path = SFX_DIR / "sfx_whoosh.mp3"
    cmd_whoosh = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "anoisesrc=d=1.5:c=pink:r=48000:a=0.08",
        "-filter_complex",
        "[0:a]bandpass=f=800:width_type=h:w=600,"
        "afade=t=in:st=0:d=0.7,"
        "afade=t=out:st=0.7:d=0.8,"
        "volume=1.2[out]",
        "-map", "[out]",
        str(whoosh_path)
    ]
    subprocess.run(cmd_whoosh, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  ✅ Generated: {whoosh_path.name}")

    # 3. Classified Radio Static Burst - 1.2 seconds
    static_path = SFX_DIR / "sfx_static.mp3"
    cmd_static = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "anoisesrc=d=1.2:c=white:r=48000:a=0.05",
        "-filter_complex",
        "[0:a]highpass=f=1200,lowpass=f=3400,"
        "tremolo=f=18:d=0.7,"
        "afade=t=in:st=0:d=0.08,"
        "afade=t=out:st=0.8:d=0.4,"
        "volume=0.9[out]",
        "-map", "[out]",
        str(static_path)
    ]
    subprocess.run(cmd_static, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  ✅ Generated: {static_path.name}")

    # 4. Lowpass Heartbeat Thud - 1.0 second
    heartbeat_path = SFX_DIR / "sfx_heartbeat.mp3"
    cmd_heartbeat = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=38:duration=1.0",
        "-filter_complex",
        "[0:a]lowpass=f=90,"
        "afade=t=in:st=0:d=0.04,"
        "afade=t=out:st=0.2:d=0.7,"
        "volume=2.0[out]",
        "-map", "[out]",
        str(heartbeat_path)
    ]
    subprocess.run(cmd_heartbeat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  ✅ Generated: {heartbeat_path.name}")

    # 5. Suspense Tension Riser - 3.5 seconds
    riser_path = SFX_DIR / "sfx_riser.mp3"
    cmd_riser = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=65:duration=3.5",
        "-f", "lavfi", "-i", "anoisesrc=d=3.5:c=pink:r=48000:a=0.02",
        "-filter_complex",
        "[0:a]asetrate=48000*1.4,aresample=48000[pitched];"
        "[1:a]lowpass=f=800[noise];"
        "[pitched][noise]amix=inputs=2:duration=first[mix];"
        "[mix]afade=t=in:st=0:d=2.0,afade=t=out:st=3.0:d=0.5,volume=1.0[out]",
        "-map", "[out]",
        str(riser_path)
    ]
    subprocess.run(cmd_riser, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  ✅ Generated: {riser_path.name}")

    print("🎉 All 5 Cinematic SFX generated successfully in assets/sfx/!")


if __name__ == "__main__":
    generate_all_sfx()

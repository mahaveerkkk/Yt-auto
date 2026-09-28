import os
import subprocess
from pathlib import Path

MUSIC_DIR = Path("/home/veer/Desktop/experiment/assets/music")
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

TRACKS = [
    # 1. Deep Space Sub-Bass Drone
    {
        "name": "space_drone_01.mp3",
        "cmd": [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "anoisesrc=d=300:c=pink:r=48000:a=0.015",
            "-f", "lavfi", "-i", "sine=frequency=36:duration=300",
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first[a];[a]lowpass=f=180,volume=0.22[out]",
            "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k",
            str(MUSIC_DIR / "space_drone_01.mp3")
        ]
    },
    # 2. Deep Ocean Abyss (Brown Noise & Sub-Bass)
    {
        "name": "ocean_abyss_02.mp3",
        "cmd": [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "anoisesrc=d=300:c=brown:r=48000:a=0.03",
            "-f", "lavfi", "-i", "sine=frequency=42:duration=300",
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first[a];[a]lowpass=f=220,volume=0.20[out]",
            "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k",
            str(MUSIC_DIR / "ocean_abyss_02.mp3")
        ]
    },
    # 3. Ancient Ruins Suspense (Dual Harmonics)
    {
        "name": "ancient_ruins_03.mp3",
        "cmd": [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "anoisesrc=d=300:c=pink:r=48000:a=0.02",
            "-f", "lavfi", "-i", "sine=frequency=48:duration=300",
            "-f", "lavfi", "-i", "sine=frequency=72:duration=300",
            "-filter_complex", "[0:a][1:a][2:a]amix=inputs=3:duration=first[a];[a]lowpass=f=240,volume=0.18[out]",
            "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k",
            str(MUSIC_DIR / "ancient_ruins_03.mp3")
        ]
    },
    # 4. Dark Cosmic Void (Sub Drone + Pulse)
    {
        "name": "cosmic_void_04.mp3",
        "cmd": [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "anoisesrc=d=300:c=pink:r=48000:a=0.02",
            "-f", "lavfi", "-i", "sine=frequency=55:duration=300",
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first[a];[a]tremolo=f=0.2:d=0.4,lowpass=f=200,volume=0.22[out]",
            "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k",
            str(MUSIC_DIR / "cosmic_void_04.mp3")
        ]
    },
    # 5. Paranormal Tension
    {
        "name": "mystery_tension_05.mp3",
        "cmd": [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "anoisesrc=d=300:c=brown:r=48000:a=0.025",
            "-f", "lavfi", "-i", "sine=frequency=50:duration=300",
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first[a];[a]lowpass=f=190,volume=0.20[out]",
            "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k",
            str(MUSIC_DIR / "mystery_tension_05.mp3")
        ]
    }
]

print("Generating cinematic ambient tracks...")
for t in TRACKS:
    target = MUSIC_DIR / t["name"]
    if not target.exists():
        print(f"Rendering {t['name']}...")
        subprocess.run(t["cmd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    else:
        print(f"{t['name']} already exists.")

print("All ambient tracks ready in assets/music!")

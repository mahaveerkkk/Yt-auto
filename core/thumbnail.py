import requests
import subprocess
from pathlib import Path
from typing import Optional
from config.settings import settings
from utils.logger import logger

class ThumbnailDesigner:
    """
    Auto-Thumbnail Designer Agent.
    Generates high-CTR, high-contrast 1280x720 cover visuals using Pollinations FLUX / HF,
    adds cinematic dark vignetting and bold yellow intrigue hook text using FFmpeg.
    """

    def __init__(self):
        self.output_dir = Path("/tmp/autodirector_thumbs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_thumbnail(self, title: str, hook_text: str, visual_prompt: str) -> Optional[Path]:
        """
        Creates an ultra-high CTR 1280x720 thumbnail:
        1. Generates 1280x720 base image via Pollinations/HF FLUX.
        2. Applies contrast boost + dark bottom gradient.
        3. Burns bold yellow/white impact text.
        """
        base_img = self.output_dir / "thumb_raw.jpg"
        final_thumb = self.output_dir / "thumbnail_final.jpg"

        logger.info(f"[Thumbnail] Designing Click-Magnet thumbnail for '{title}'...")

        try:
            # 1. Image generation via Pollinations FLUX (or fallback to existing scene 1 image)
            clean_p = requests.utils.quote(f"{visual_prompt}, extreme closeup dramatic lighting, hyperrealistic 8k, cinematic mystery, vivid contrast")
            url = f"https://image.pollinations.ai/prompt/{clean_p}?width=1280&height=720&model=flux&nologo=true"
            downloaded = False
            try:
                res = requests.get(url, timeout=12)
                if res.status_code == 200 and len(res.content) > 10000:
                    with open(base_img, "wb") as f:
                        f.write(res.content)
                    downloaded = True
            except Exception as e:
                logger.warning(f"[Thumbnail] Pollinations thumb timeout: {e}")

            if not downloaded:
                # Use scene 1 generated image as fallback base
                scene_1 = Path("/tmp/autodirector_production/scene_1.jpg")
                if scene_1.exists():
                    import shutil
                    shutil.copy(scene_1, base_img)
                    downloaded = True
                else:
                    return None

            # 2. Text sanitization (short impact phrase)
            clean_hook = hook_text.upper().replace("'", "").replace(":", "")[:22]

            # 3. FFmpeg overlay with shadow & vignette
            vf = (
                f"eq=contrast=1.18:saturation=1.25,"
                f"drawtext=text='{clean_hook}':fontcolor=yellow:fontsize=68:x=(w-text_w)/2:y=h-130:"
                f"bordercolor=black:borderw=6:shadowcolor=black@0.8:shadowx=4:shadowy=4"
            )

            cmd = [
                "ffmpeg", "-y",
                "-i", str(base_img),
                "-vf", vf,
                str(final_thumb)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            logger.info(f"🎉 Thumbnail successfully created: {final_thumb}")
            return final_thumb

        except Exception as e:
            logger.error(f"[Thumbnail] Failed to generate thumbnail: {e}")
            return None

thumbnail_designer = ThumbnailDesigner()

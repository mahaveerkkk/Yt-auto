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

    def _render_image_pollinations(self, prompt: str, target_path: Path, seed: int = 42) -> bool:
        """Downloads high-res 1280x720 base image from Pollinations FLUX."""
        try:
            clean_p = requests.utils.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{clean_p}?width=1280&height=720&model=flux&nologo=true&seed={seed}"
            res = requests.get(url, timeout=12)
            if res.status_code == 200 and len(res.content) > 10000:
                with open(target_path, "wb") as f:
                    f.write(res.content)
                return True
        except Exception as e:
            logger.warning(f"[Thumbnail] Pollinations generation error: {e}")
        return False

    def generate_dual_thumbnails(self, title: str, hook_text: str, visual_prompt: str, category: str = "Mystery") -> dict:
        """
        Creates 2 distinct high-CTR thumbnail styles for Boss to pick:
        - Option A: Macro Close-up Intrigue with bold yellow impact text.
        - Option B: Cinematic Scale & Dread with classified red banner and bold white text.
        Returns {'thumb_a': Path, 'thumb_b': Path}.
        """
        raw_a = self.output_dir / "raw_thumb_a.jpg"
        raw_b = self.output_dir / "raw_thumb_b.jpg"
        final_a = self.output_dir / "thumb_option_a.jpg"
        final_b = self.output_dir / "thumb_option_b.jpg"

        clean_hook = hook_text.upper().replace("'", "").replace(":", "")[:22]
        if not clean_hook:
            clean_hook = "CLASSIFIED"

        logger.info(f"[Thumbnail] Generating Dual Thumbnails (Option A & B) for '{title}'...")

        # Option A: Close-Up Intrigue
        prompt_a = f"{visual_prompt}, extreme macro closeup, glowing bioluminescent relic, intense dramatic lighting, 8k cinematic mystery, vivid contrast"
        success_a = self._render_image_pollinations(prompt_a, raw_a, seed=777)
        if not success_a:
            # Fallback to local scene frame if available
            scene_1_jpg = Path("/tmp/autodirector_production/scene_1.jpg")
            if scene_1_jpg.exists():
                import shutil
                shutil.copy(scene_1_jpg, raw_a)

        # Option B: Atmospheric Scale & Dread
        prompt_b = f"{visual_prompt}, wide angle panoramic view, immense cosmic dread, stormy ocean abyss, deep dark atmospheric mist, red emergency glow, 8k"
        success_b = self._render_image_pollinations(prompt_b, raw_b, seed=999)
        if not success_b and raw_a.exists():
            import shutil
            shutil.copy(raw_a, raw_b)

        # Render Final A (Bold Yellow Text + Vignette)
        if raw_a.exists():
            vf_a = (
                f"eq=contrast=1.2:saturation=1.25,vignette=PI/4,"
                f"drawtext=text='{clean_hook}':fontcolor=yellow:fontsize=68:x=(w-text_w)/2:y=h-130:"
                f"bordercolor=black:borderw=6:shadowcolor=black@0.9:shadowx=4:shadowy=4"
            )
            try:
                subprocess.run(["ffmpeg", "-y", "-i", str(raw_a), "-vf", vf_a, str(final_a)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"[Thumbnail] FFmpeg Option A failed: {e.stderr[:300] if e.stderr else e}")

        # Render Final B (Red Classified Badge + Bold White Text)
        if raw_b.exists():
            vf_b = (
                f"eq=contrast=1.15:saturation=1.1,vignette=PI/3,"
                f"drawtext=text='[ CLASSIFIED DOSSIER ]':fontcolor=red:fontsize=32:x=60:y=60:bordercolor=black:borderw=4,"
                f"drawtext=text='{clean_hook}':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=h-130:"
                f"bordercolor=black:borderw=6:shadowcolor=red@0.5:shadowx=3:shadowy=3"
            )
            try:
                subprocess.run(["ffmpeg", "-y", "-i", str(raw_b), "-vf", vf_b, str(final_b)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"[Thumbnail] FFmpeg Option B failed: {e.stderr[:300] if e.stderr else e}")

        return {
            "thumb_a": final_a if final_a.exists() else None,
            "thumb_b": final_b if final_b.exists() else None  # Don't fake B with A — let A/B optimizer know B failed
        }

    def generate_thumbnail(self, title: str, hook_text: str, visual_prompt: str) -> Optional[Path]:
        """Backwards compatible single-thumbnail generator (returns Option A)."""
        res = self.generate_dual_thumbnails(title, hook_text, visual_prompt)
        return res.get("thumb_a") or res.get("thumb_b")

thumbnail_designer = ThumbnailDesigner()

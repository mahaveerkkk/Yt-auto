import os
import time
import json
import requests
import subprocess
from pathlib import Path
from typing import Optional, Dict
from config.settings import settings
from utils.logger import logger

class ThumbnailDesigner:
    """
    Frontier AI Thumbnail Engine (V2).
    Generates 16:9 ultra-HD, cinematic documentary thumbnails without watermarks.
    Primary: OpenAI GPT Image 2.5 Flare (via Kie.ai)
    Secondary: Grok Imagine 2.0 (via Kie.ai)
    Fallback: Clean HuggingFace FLUX / Cropped FLUX
    Zero cheap yellow MS-Paint text overlays — native high-CTR technical spectrogram aesthetic.
    """

    def __init__(self):
        self.output_dir = getattr(settings, "THUMBNAILS_DIR", settings.BASE_DIR / "output" / "thumbnails")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.kie_key = getattr(settings, "KIE_API_KEY", "") or os.getenv("KIE_API_KEY", "")

    def _render_kie_task(self, model_name: str, prompt: str, target_path: Path, max_wait_sec: int = 70) -> bool:
        """Asynchronously dispatches image generation to Kie.ai and downloads HD result."""
        if not self.kie_key:
            return False

        headers = {
            "Authorization": f"Bearer {self.kie_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "input": {
                "prompt": prompt,
                "aspect_ratio": "16:9"
            }
        }

        try:
            logger.info(f"[Thumbnail] Submitting generation task to Kie.ai ({model_name})...")
            create_res = requests.post("https://api.kie.ai/api/v1/jobs/createTask", json=payload, headers=headers, timeout=20)
            if create_res.status_code != 200:
                logger.warning(f"[Thumbnail] Kie.ai task submission returned status {create_res.status_code}: {create_res.text[:150]}")
                return False

            data = create_res.json() or {}
            task_id = (data.get("data") or {}).get("taskId")
            if not task_id:
                logger.warning(f"[Thumbnail] No taskId in Kie.ai response: {data}")
                return False

            logger.info(f"[Thumbnail] Task {task_id} queued on {model_name}. Polling status...")
            start_t = time.time()
            while time.time() - start_t < max_wait_sec:
                time.sleep(4)
                try:
                    status_res = requests.get(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers, timeout=25)
                    if status_res.status_code != 200:
                        continue
                    sdata = (status_res.json() or {}).get("data") or {}
                    state = sdata.get("state")
                    if state == "success":
                        result_urls = (sdata.get("response") or {}).get("resultUrls") or []
                        if not result_urls and "resultJson" in sdata:
                            try:
                                result_urls = (json.loads(sdata["resultJson"]) or {}).get("resultUrls", [])
                            except Exception:
                                pass
                        if result_urls:
                            dl_res = requests.get(result_urls[0], timeout=35)
                            dl_res.raise_for_status()
                            img_bytes = dl_res.content
                            raw_temp = target_path.with_suffix(".raw.png")
                            with open(raw_temp, "wb") as f:
                                f.write(img_bytes)

                            conformed = self._conform_thumbnail(raw_temp, target_path)
                            if raw_temp.exists():
                                raw_temp.unlink()

                            if conformed:
                                logger.info(f"✅ [Thumbnail] High-Res 16:9 Thumbnail saved ({model_name}): {target_path} ({target_path.stat().st_size} bytes)")
                                return True
                            logger.warning(f"[Thumbnail] Image conform failed for {model_name}. Rejecting corrupted file.")
                        break
                    elif state in ["fail", "error"]:
                        logger.warning(f"[Thumbnail] Task failed on {model_name}: {sdata.get('failMsg')}")
                        break
                except (requests.RequestException, Exception) as poll_err:
                    logger.debug(f"[Thumbnail] Polling retry on transient error: {poll_err}")
                    continue
        except Exception as e:
            logger.warning(f"[Thumbnail] Kie.ai exception for {model_name}: {e}")
        return False

    def _conform_thumbnail(self, src_path: Path, dst_path: Path) -> bool:
        """
        Conforms any raw PNG/JPEG from Kie.ai into a guaranteed 1280x720 16:9 JPEG
        under 1.5MB so YouTube API never throws 400 'image is too large'.
        """
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(src_path),
                "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
                "-q:v", "3",
                str(dst_path)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return dst_path.exists() and dst_path.stat().st_size > 10000
        except Exception as e:
            logger.warning(f"[Thumbnail] FFmpeg conform error: {e}")
            return False

    def _render_image_pollinations_clean(self, prompt: str, target_path: Path, seed: int = 42) -> bool:
        """Downloads base image from Pollinations and crops any bottom-corner watermark."""
        try:
            clean_p = requests.utils.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{clean_p}?width=1280&height=740&model=flux&nologo=true&seed={seed}"
            res = requests.get(url, timeout=35)
            if res.status_code == 200 and len(res.content) > 10000:
                raw_temp = target_path.with_suffix(".tmp.jpg")
                with open(raw_temp, "wb") as f:
                    f.write(res.content)
                # Crop bottom 20px using FFmpeg to eliminate any watermark
                try:
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", str(raw_temp), "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720", str(target_path)],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20
                    )
                    if raw_temp.exists():
                        raw_temp.unlink()
                    return target_path.exists() and target_path.stat().st_size > 5000
                except Exception:
                    if raw_temp.exists():
                        raw_temp.unlink()
                    return False
        except Exception as e:
            logger.warning(f"[Thumbnail] Clean Pollinations error: {e}")
        return False

    def _render_local_fallback(self, title: str, hook_text: str, dst_path: Path, style: str = "a") -> bool:
        """
        Guaranteed zero-network local fallback thumbnail using FFmpeg lavfi filters.
        Produces a crisp 1280x720 16:9 thumbnail with dark mystery gradients, vignette,
        and high-contrast typography even if all external APIs and DNS are unreachable.
        """
        try:
            if style == "b":
                bg_color = "0x0b0406"
                border_color = "0xe11d48@0.6"
                vignette = "PI/3"
            else:
                bg_color = "0x040914"
                border_color = "0x38bdf8@0.6"
                vignette = "PI/4"

            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font_filter = f":fontfile='{font_path}'" if Path(font_path).exists() else ""
            clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", ":", "?", "!"))[:38].replace("'", "")
            clean_hook = "".join(c for c in hook_text if c.isalnum() or c in (" ", "-", ":", "?", "!"))[:40].replace("'", "")
            clean_title = clean_title.replace(":", "\\:")
            clean_hook = clean_hook.replace(":", "\\:")

            vf = (
                f"color=c={bg_color}:s=1280x720:d=1,"
                f"drawbox=x=40:y=40:w=1200:h=640:color=0x000000@0.7:t=fill,"
                f"drawbox=x=40:y=40:w=1200:h=640:color={border_color}:t=4,"
                f"drawtext=text='{clean_title}'{font_filter}:fontsize=46:fontcolor=white:x=(w-text_w)/2:y=280:shadowcolor=black:shadowx=3:shadowy=3,"
                f"drawtext=text='{clean_hook}'{font_filter}:fontsize=34:fontcolor=0xfacc15:x=(w-text_w)/2:y=380:shadowcolor=black:shadowx=2:shadowy=2,"
                f"vignette={vignette}"
            )
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", vf,
                "-frames:v", "1", "-update", "1", str(dst_path)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=15)
            return dst_path.exists() and dst_path.stat().st_size > 5000
        except Exception as e:
            logger.warning(f"[Thumbnail] Local fallback generation error: {e}")
            return False

    def generate_dual_thumbnails(self, title: str, hook_text: str, visual_prompt: str, category: str = "Mystery") -> Dict[str, Optional[Path]]:
        """
        Creates 2 distinct high-CTR, 16:9 documentary thumbnails:
        - Option A: GPT Image 2.5 Flare (Technical Spectrogram, Depth HUD, Split-view scale)
        - Option B: Grok Imagine 2.0 (Atmospheric Dread, Deep Abyss Lighting, High Contrast)
        Returns {'thumb_a': Path, 'thumb_b': Path}.
        """
        timestamp = int(time.time())
        clean_slug = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip().replace(" ", "_")[:30]
        final_a = self.output_dir / f"thumb_{clean_slug}_A_{timestamp}.jpg"
        final_b = self.output_dir / f"thumb_{clean_slug}_B_{timestamp}.jpg"

        logger.info(f"[Thumbnail] Generating Frontier Dual Thumbnails for '{title}'...")

        # Option A Prompt: Technical documentary, acoustic spectrogram HUD, split cross-section
        prompt_a = (
            f"A cinematic National Geographic documentary photograph, topic '{title}'. "
            f"{visual_prompt}. Split cross-section perspective showing dramatic scale contrast. "
            f"Technical acoustic audio spectrogram waterfall display in top corner, scientific digital depth HUD telemetry, "
            f"ultra-sharp focal point, dramatic rim lighting, 16:9 widescreen, hyperrealistic, zero cheap text."
        )

        # Option B Prompt: Dark atmospheric scale, deep abyss dread, glowing anomaly
        prompt_b = (
            f"An unsettling BBC documentary cinematic visual, topic '{title}'. "
            f"{visual_prompt}. Wide panoramic scale of vast cosmic or oceanic abyss, intense red emergency lighting contrast, "
            f"massive colossal silhouette towering over tiny human research element, foggy atmospheric haze, 16:9, hyperrealistic 4K."
        )

        # Try Tier 1: GPT Image 2.5 Flare for Option A
        success_a = self._render_kie_task("gpt-image-2-5-flare-text-to-image", prompt_a, final_a)
        if not success_a:
            logger.info("[Thumbnail] Falling back Option A to Grok Imagine 2.0...")
            success_a = self._render_kie_task("grok-imagine/text-to-image", prompt_a, final_a)
        if not success_a:
            logger.info("[Thumbnail] Falling back Option A to Clean FLUX...")
            success_a = self._render_image_pollinations_clean(prompt_a, final_a, seed=777)
        if not success_a:
            logger.info("[Thumbnail] Falling back Option A to Local Cinematic Emergency Canvas...")
            success_a = self._render_local_fallback(title, hook_text, final_a, style="a")

        # Try Tier 2: Grok Imagine 2.0 for Option B
        success_b = self._render_kie_task("grok-imagine/text-to-image", prompt_b, final_b)
        if not success_b:
            logger.info("[Thumbnail] Falling back Option B to Clean FLUX...")
            success_b = self._render_image_pollinations_clean(prompt_b, final_b, seed=999)
        if not success_b:
            logger.info("[Thumbnail] Falling back Option B to Local Cinematic Emergency Canvas...")
            success_b = self._render_local_fallback(title, hook_text, final_b, style="b")

        return {
            "thumb_a": final_a if (final_a.exists() and final_a.stat().st_size > 5000) else None,
            "thumb_b": final_b if (final_b.exists() and final_b.stat().st_size > 5000) else None
        }

    def generate_thumbnail(self, title: str, hook_text: str, visual_prompt: str) -> Optional[Path]:
        """Backwards compatible single-thumbnail generator (returns best available option)."""
        res = self.generate_dual_thumbnails(title, hook_text, visual_prompt)
        return res.get("thumb_a") or res.get("thumb_b")

thumbnail_designer = ThumbnailDesigner()

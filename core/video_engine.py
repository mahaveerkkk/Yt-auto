import os
import time
import requests
from pathlib import Path
from typing import List, Optional
from config.settings import settings
from utils.logger import logger

settings.ensure_directories()


class VideoEngine:
    """
    Multi-Model Video Orchestrator.
    Handles scene-by-scene clip generation using Hugging Face ZeroGPU (Wan 2.1 / LTX-Video)
    and Pexels HD Stock Footage as a rock-solid fallback.
    """

    def __init__(self):
        self.parts_dir = settings.PARTS_DIR
        self.hf_token = settings.HF_TOKEN
        self.pexels_key = settings.PEXELS_API_KEY
        self.openrouter_key = settings.OPENROUTER_API_KEY

    # -------------------------------------------------------------
    # Provider 1: Hugging Face ZeroGPU (Wan 2.1 / 2.2)
    # -------------------------------------------------------------
    def _generate_hf_wan(self, prompt: str, output_path: Path) -> bool:
        """Calls Hugging Face Wan 2.1 space via gradio_client async pipeline."""
        try:
            from gradio_client import Client
            logger.info(f"[Wan 2.x HF] Initiating generation for prompt: '{prompt[:40]}...'")

            client = Client(settings.HF_WAN_SPACE, token=self.hf_token or None)
            client.predict(
                prompt=prompt,
                size="1280*720",
                watermark_wan=False,
                seed=-1,
                api_name="/t2v_generation_async"
            )
            # Poll /status_refresh for video completion
            logger.info("[Wan 2.x HF] Render submitted, polling for completion...")
            for _ in range(24):  # Poll up to 2 minutes
                time.sleep(5)
                status = client.predict(api_name="/status_refresh")
                if isinstance(status, (list, tuple)) and status[0] and isinstance(status[0], dict):
                    val = status[0].get("value")
                    if val:
                        vid_info = val.get("video") if isinstance(val, dict) else val
                        vid_path = vid_info.get("path") if isinstance(vid_info, dict) else vid_info
                        if vid_path and os.path.exists(vid_path):
                            import shutil
                            shutil.copy(vid_path, output_path)
                            logger.info(f"[Wan 2.x HF] Successfully saved AI video: {output_path.name}")
                            return True
        except Exception as e:
            logger.warning(f"[Wan 2.x HF] Failed or queue timeout: {e}")
        return False

    # -------------------------------------------------------------
    # Provider 2: Hugging Face ZeroGPU (LTX-Video)
    # -------------------------------------------------------------
    def _generate_hf_ltx(self, prompt: str, output_path: Path) -> bool:
        """Calls Hugging Face LTX-Video space via gradio_client (Fast generator)."""
        try:
            from gradio_client import Client
            logger.info(f"[LTX-Video HF] Initiating generation for prompt: '{prompt[:40]}...'")

            client = Client(settings.HF_LTX_SPACE, token=self.hf_token or None)
            result = client.predict(
                prompt=prompt,
                negative_prompt="low quality, bad anatomy, worst quality",
                api_name="/predict"
            )

            if result and os.path.exists(result):
                import shutil
                shutil.copy(result, output_path)
                logger.info(f"[LTX-Video HF] Successfully saved: {output_path.name}")
                return True
        except Exception as e:
            logger.warning(f"[LTX-Video HF] Failed or queue timeout: {e}")
        return False

    # -------------------------------------------------------------
    # Provider 3: OpenRouter Video API (Wan 3.0 / Seedance)
    # -------------------------------------------------------------
    def _generate_openrouter_video(self, prompt: str, output_path: Path) -> bool:
        """Generates video via OpenRouter video endpoint if key available."""
        if not self.openrouter_key:
            return False

        try:
            logger.info(f"[OpenRouter Video] Requesting video generation: '{prompt[:40]}...'")
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "wan/wan-3.0",
                "prompt": prompt,
                "duration": 5
            }
            # OpenRouter async video API
            resp = requests.post("https://openrouter.ai/api/v1/videos", headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                video_url = data.get("video_url")
                if video_url:
                    self._download_file(video_url, output_path)
                    logger.info(f"[OpenRouter Video] Downloaded: {output_path.name}")
                    return True
        except Exception as e:
            logger.warning(f"[OpenRouter Video] Error: {e}")
        return False

    # -------------------------------------------------------------
    # Provider 4: Pexels API (100% Free Stock Footage Fallback)
    # -------------------------------------------------------------
    def _fetch_pexels_stock(self, query: str, output_path: Path) -> bool:
        """Searches and downloads high-quality vertical stock video from Pexels with multi-term fallback."""
        if not self.pexels_key:
            logger.warning("[Pexels] No PEXELS_API_KEY provided in .env.")
            return False

        headers = {"Authorization": self.pexels_key}

        # Build fallback search candidates from specific to general
        queries = [query.strip(), query.split(",")[0].strip()]
        first_word = query.split()[0].strip() if query.split() else "cinematic"
        queries.append(first_word)
        if any(w in query.lower() for w in ["space", "galaxy", "star", "universe", "planet"]):
            queries.extend(["space", "galaxy", "stars universe"])
        else:
            queries.extend(["cinematic 4k", "nature background", "abstract neon"])

        for q in queries:
            if not q:
                continue
            try:
                logger.info(f"[Pexels Stock] Searching footage for query: '{q}'")
                resp = requests.get(
                    "https://api.pexels.com/videos/search",
                    headers=headers,
                    params={"query": q, "orientation": "landscape", "per_page": 5},
                    timeout=15
                )

                if resp.status_code == 200:
                    data = resp.json()
                    videos = data.get("videos", [])
                    if videos:
                        video_files = videos[0].get("video_files", [])
                        download_url = None
                        # Prefer landscape HD (16:9 for documentaries)
                        for vf in video_files:
                            if vf.get("width") and vf.get("height") and vf.get("width") > vf.get("height"):
                                download_url = vf.get("link")
                                break
                        if not download_url and video_files:
                            download_url = video_files[0].get("link")

                        if download_url and self._download_file(download_url, output_path):
                            logger.info(f"[Pexels Stock] Found and downloaded clip for query '{q}'")
                            return True
            except Exception as e:
                logger.warning(f"[Pexels Stock] Error fetching stock for '{q}': {e}")
        return False

    # -------------------------------------------------------------
    # Helper: Download video from URL
    # -------------------------------------------------------------
    def _download_file(self, url: str, target_path: Path) -> bool:
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(target_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return True
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            return False

    # -------------------------------------------------------------
    # Master Scene Generator with Fallback Chain
    # -------------------------------------------------------------
    def generate_scene(self, scene_prompt: str, scene_index: int, search_fallback_term: str = "", mode: str = "fast") -> Optional[Path]:
        """
        Generates or fetches a single scene clip.
        mode='fast': uses instant Pexels HD stock clips (ultra-fast, reliable)
        mode='ai': attempts cloud AI video models (Wan 2.x, LTX) with fallback
        """
        output_path = self.parts_dir / f"part_{scene_index:02d}.mp4"
        search_query = search_fallback_term or scene_prompt.split(",")[0]

        if mode == "fast":
            logger.info(f"[VideoEngine] Fast mode: fetching stock video for '{search_query}'")
            if self._fetch_pexels_stock(search_query, output_path):
                return output_path

        # AI Mode attempts
        logger.info(f"[VideoEngine] AI mode: trying Wan 2.x / LTX-Video...")
        if self._generate_hf_wan(scene_prompt, output_path):
            return output_path

        if self._generate_hf_ltx(scene_prompt, output_path):
            return output_path

        if self._generate_openrouter_video(scene_prompt, output_path):
            return output_path

        # Final Fallback to Pexels
        if self._fetch_pexels_stock(search_query, output_path):
            return output_path

        logger.error(f"All video providers failed for Scene #{scene_index}")
        return None

    def generate_all_scenes(self, scenes: List[dict], mode: str = "fast") -> List[Path]:
        """
        Takes a list of scene objects [{'prompt': '...', 'keywords': '...'}]
        and returns a list of downloaded clip filepaths.
        """
        successful_clips = []
        for i, sc in enumerate(scenes, start=1):
            prompt = sc.get("prompt", "")
            keywords = sc.get("keywords", prompt[:30])
            logger.info(f"--- Generating Scene {i}/{len(scenes)} ---")
            clip_path = self.generate_scene(prompt, i, keywords, mode=mode)
            if clip_path and clip_path.exists():
                successful_clips.append(clip_path)

        logger.info(f"Video generation complete: {len(successful_clips)}/{len(scenes)} scenes ready.")
        return successful_clips


video_engine = VideoEngine()

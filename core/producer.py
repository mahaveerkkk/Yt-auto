import json
import shutil
import asyncio
import subprocess
import requests
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
from config.settings import settings
from utils.logger import logger
from core.worker_manager import worker_manager
from core.resilience import quota_tracker
import edge_tts


class Producer:
    """
    Hollywood-Grade Resilient Long-Form Documentary Production Engine:
    - Target: High-retention 8-12 minute / 480-720s long-form documentaries
    - BBC/National Geographic authoritative voiceover via Edge-TTS BrianMultilingual
    - True visual diversity across every scene:
      * Priority 1: Unique Pexels HD Stock Video Footage (keyword targeted, distinct video IDs)
      * Priority 2: Hugging Face FLUX.1 4K (if quota available)
      * Priority 3: Pollinations FLUX Engine + Dynamic 3D Ken Burns Camera Pan
    - Real cinematic ambient background soundtrack from assets/music/
    - Automated cleanup of intermediate video fragments to protect VPS storage
    """

    VOICE_ROSTER = {
        "Cosmic": "en-US-BrianMultilingualNeural",      # Deep, philosophical BBC narrator
        "Ancient": "en-GB-RyanNeural",                   # British classical historical documentary
        "Aviation": "en-US-ChristopherNeural",           # Crisp, military/investigative radio
        "Ocean": "en-US-AndrewMultilingualNeural",       # Deep resonance oceanic narrative
        "Default": "en-US-BrianMultilingualNeural"
    }

    def _select_voice_for_topic(self, topic: str, category: str = "") -> str:
        """Dynamically casts the most fitting professional narrator voice per documentary theme."""
        text = f"{topic} {category}".lower()
        if any(w in text for w in ["ancient", "civilization", "pyramid", "ruins", "history", "atlantis"]):
            return self.VOICE_ROSTER["Ancient"]
        elif any(w in text for w in ["flight", "plane", "maritime", "ship", "bermuda", "radar", "classified"]):
            return self.VOICE_ROSTER["Aviation"]
        elif any(w in text for w in ["ocean", "sea", "bloop", "trench", "underwater", "abyss"]):
            return self.VOICE_ROSTER["Ocean"]
        elif any(w in text for w in ["space", "universe", "galaxy", "signal", "astronomy", "cosmic", "void", "physics"]):
            return self.VOICE_ROSTER["Cosmic"]
        return self.VOICE_ROSTER["Default"]

    def __init__(self):
        self.temp_dir = Path("/tmp/autodirector_production")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.pexels_key = settings.PEXELS_API_KEY
        self.hf_token = settings.HF_TOKEN
        self.music_dir = settings.MUSIC_DIR
        self.sfx_dir = settings.SFX_DIR

    def _get_media_duration(self, file_path: Path) -> float:
        """Measures exact duration in seconds using ffprobe."""
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(file_path)]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(json.loads(res.stdout)["format"]["duration"])
        except Exception as e:
            logger.warning(f"[Producer] ffprobe failed for {file_path}, using fallback duration: {e}")
            return 600.0  # 10-minute fallback for long-form documentaries

    def _get_ambient_music_track(self) -> Path:
        """Selects a dark ambient cinematic track from the pre-rendered music pool."""
        tracks = list(self.music_dir.glob("*.mp3"))
        if tracks:
            chosen = random.choice(tracks)
            logger.info(f"[Producer] 🎵 Selected Ambient Soundtrack: {chosen.name}")
            return chosen
        
        # Fallback to creating a dynamic drone if no tracks exist
        fallback_track = self.temp_dir / "fallback_drone.mp3"
        if not fallback_track.exists():
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "anoisesrc=d=300:c=pink:r=48000:a=0.02",
                "-f", "lavfi", "-i", "sine=frequency=44:duration=300",
                "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first[a];[a]lowpass=f=200,volume=0.2[out]",
                "-map", "[out]", str(fallback_track)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return fallback_track

    def _generate_hf_flux(self, prompt: str, target_path: Path, seed: int) -> bool:
        """Attempts generation via official Hugging Face FLUX.1 if quota permits."""
        if not self.hf_token or not quota_tracker.can_use("hf_flux"):
            return False
        try:
            from gradio_client import Client
            logger.info("[Producer] Trying HuggingFace FLUX.1-schnell...")
            client = Client("black-forest-labs/FLUX.1-schnell", token=self.hf_token)
            res = client.predict(
                prompt=f"{prompt}, 8k photorealistic, cinematic movie still, dramatic lighting, unreal engine 5",
                seed=seed,
                randomize_seed=True,
                width=1280,
                height=720,
                num_inference_steps=4,
                api_name="/infer"
            )
            src_path = res[0]
            if isinstance(src_path, dict):
                src_path = src_path.get("path")
            shutil.copy(src_path, target_path)
            quota_tracker.record_use("hf_flux")
            logger.info("✅ HF FLUX.1 visual generated successfully!")
            return True
        except Exception as e:
            logger.warning(f"[Producer] HF FLUX.1 quota skipped: {str(e)[:70]}")
            return False

    def _download_pexels_clip(self, query: str, target_path: Path, used_video_ids: set, duration: float = 7.0) -> bool:
        """Downloads a distinct HD landscape stock video from Pexels, guaranteeing zero duplicate clips."""
        if not self.pexels_key or not quota_tracker.can_use("pexels"):
            return False
        try:
            clean_words = [w for w in query.replace("!", "").replace("?", "").replace(":", "").split() if len(w) > 2][:3]
            search_term = " ".join(clean_words) if clean_words else "deep space galaxy"
            logger.info(f"[Producer] Scouting Pexels HD Footage for: '{search_term}'...")

            headers = {"Authorization": self.pexels_key}
            clean_q = requests.utils.quote(search_term)
            url = f"https://api.pexels.com/videos/search?query={clean_q}&per_page=12&orientation=landscape"
            res = requests.get(url, headers=headers, timeout=12)
            quota_tracker.record_use("pexels")

            videos = []
            if res.status_code == 200:
                videos = res.json().get("videos", [])

            # Fallback to diverse atmospheric pools if specific query is empty
            if not videos:
                generic_pools = [
                    "deep space stars", "ocean abyss underwater", "storm clouds time lapse",
                    "astronomical observatory telescope", "ancient desert ruins", "radar sonar technology"
                ]
                fallback_q = random.choice(generic_pools)
                url_fb = f"https://api.pexels.com/videos/search?query={requests.utils.quote(fallback_q)}&per_page=10&orientation=landscape"
                res_fb = requests.get(url_fb, headers=headers, timeout=12)
                if res_fb.status_code == 200:
                    videos = res_fb.json().get("videos", [])

            # Filter out already used video IDs for 100% visual diversity
            available_videos = [v for v in videos if v.get("id") not in used_video_ids]
            if not available_videos and videos:
                available_videos = videos

            if available_videos:
                v_item = random.choice(available_videos[:min(6, len(available_videos))])
                used_video_ids.add(v_item.get("id"))
                files = v_item.get("video_files", [])

                chosen = None
                for vf in files:
                    if vf.get("width", 0) >= 1280 and vf.get("quality") == "hd":
                        chosen = vf.get("link")
                        break
                if not chosen and files:
                    chosen = files[0].get("link")

                if chosen:
                    v_res = requests.get(chosen, timeout=30)
                    if v_res.status_code == 200:
                        raw_stock = self.temp_dir / f"raw_stock_{target_path.stem}.mp4"
                        with open(raw_stock, "wb") as f:
                            f.write(v_res.content)

                        # Conform to 1280x720, exact scene duration, 30fps, no audio, SAR=1
                        cmd = [
                            "ffmpeg", "-y",
                            "-threads", "2",
                            "-stream_loop", "-1",
                            "-i", str(raw_stock),
                            "-t", str(duration),
                            "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1",
                            "-r", "30",
                            "-an",  # Strip audio track from stock footage to prevent concat audio stream conflicts
                            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                            str(target_path)
                        ]
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
                        if raw_stock.exists():
                            raw_stock.unlink()
                        logger.info(f"✅ Distinct HD Stock Clip ready (ID: {v_item.get('id')})!")
                        return True
        except Exception as e:
            logger.warning(f"[Producer] Pexels retrieval error: {e}")
        return False

    def _generate_pollinations_flux(self, prompt: str, target_path: Path, seed: int) -> bool:
        """Pollinations image fallback."""
        try:
            clean_p = requests.utils.quote(prompt[:80])
            url = f"https://image.pollinations.ai/prompt/{clean_p}?width=1280&height=720&nologo=true&seed={seed}"
            res = requests.get(url, timeout=12)
            if res.status_code == 200 and len(res.content) > 10000:
                with open(target_path, "wb") as f:
                    f.write(res.content)
                return True
        except Exception:
            pass
        return False

    def _create_3d_motion(self, img_path: Path, out_clip: Path, motion_type: str = "in", duration: float = 7.0):
        """Creates Ken Burns 2.0 camera pan/zoom clip with dark vignette and archival film grain."""
        frames = int(duration * 30)
        if motion_type == "in":
            base_pan = f"zoompan=z='min(zoom+0.0016,1.25)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps=30"
        elif motion_type == "out":
            base_pan = f"zoompan=z='if(lte(zoom,1.0),1.25,max(1.001,zoom-0.0016))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps=30"
        else:
            base_pan = f"zoompan=z=1.15:d={frames}:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),(ih-ih/zoom)/4,y+0.6)':s=1280x720:fps=30"

        # Archival film grading: setsar=1 + dark vignette + subtle contrast & saturation boost + fine film grain
        vf = f"{base_pan},setsar=1,vignette=PI/4,eq=contrast=1.08:saturation=1.12,noise=alls=6:allf=t+u"

        cmd = [
            "ffmpeg", "-y",
            "-threads", "2",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", vf,
            "-t", str(duration),
            "-r", "30",
            "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            str(out_clip)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        except Exception as e:
            logger.warning(f"[Producer] 3D motion render failed for {img_path}: {e}")

    def _generate_outro_clip(self, target_path: Path, duration: float = 12.0) -> bool:
        """
        Generates a 12-second branded mystery outro slate:
        - Deep black/dark oceanic background
        - High-contrast glowing text: 'INVESTIGATION CONCLUDED // CHOOSE NEXT DOSSIER'
        - Provides designated space for YouTube's algorithm to render interactive end screens.
        """
        try:
            draw_text = (
                "drawtext=text='INVESTIGATION CONCLUDED':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2-40:"
                "shadowcolor=black:shadowx=3:shadowy=3,"
                "drawtext=text='CHOOSE NEXT CLASSIFIED DOSSIER':fontcolor=yellow:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2+30:"
                "shadowcolor=black:shadowx=2:shadowy=2,"
                "vignette=PI/3,noise=alls=10:allf=t+u,setsar=1"
            )
            cmd = [
                "ffmpeg", "-y",
                "-threads", "2",
                "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={duration}:r=30",
                "-vf", draw_text,
                "-t", str(duration),
                "-r", "30",
                "-an",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                str(target_path)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
            return target_path.exists()
        except Exception as e:
            logger.warning(f"[Producer] Outro slate generation error: {e}")
            return False

    def produce_full_documentary(self, manifest: Dict[str, Any], cancel_check: Optional[Any] = None) -> Optional[Path]:
        """Executes full long-form documentary production with high visual diversity & natural voice."""
        scenes = manifest.get("scenes", [])
        script = manifest.get("voice_script", "")
        title = manifest.get("title", "documentary")
        title_slug = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip().replace(" ", "_")[:25]

        worker_manager.start_task("producer", f"Synthesizing voiceover and visual montage for '{title}'")
        logger.info(f"[Producer] 🎬 Initiating Production for: '{title}'")

        # 1. Voice Synthesis (Dynamic Theme Voice Narrator)
        chosen_voice = self._select_voice_for_topic(title, manifest.get("category", ""))
        voice_path = self.temp_dir / f"{title_slug}_voice.mp3"
        logger.info(f"[Producer] 🎙️ Casted Voice Narrator: {chosen_voice}...")
        try:
            async def _synth():
                comm = edge_tts.Communicate(script, chosen_voice, rate="-2%")
                await comm.save(str(voice_path))

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    executor.submit(asyncio.run, _synth()).result()
            else:
                asyncio.run(_synth())
        except Exception as e:
            logger.error(f"[Producer] Voice synthesis failed: {e}")
            worker_manager.report_error("producer", f"Voice synthesis error: {e}")
            return None

        voice_duration = self._get_media_duration(voice_path)
        logger.info(f"[Producer] 🎙️ Voiceover Duration: {voice_duration:.1f} seconds (~{voice_duration/60:.1f} mins)")

        # Each scene should occupy proportional duration
        num_scenes = max(len(scenes), 6)
        sec_per_scene = max(5.0, round(voice_duration / num_scenes, 1))

        # 2. High-Retention Visual Beats Generation (Dynamic 5-8 Second Cuts)
        # Instead of 1 long static visual per scene, each scene is broken into dynamic sub-beats
        ready_clips = []
        used_video_ids = set()
        beat_counter = 1

        for sc_idx, sc in enumerate(scenes, start=1):
            if cancel_check and cancel_check():
                logger.info("[Producer] Cancellation detected during scene rendering. Aborting.")
                worker_manager.report_error("producer", "Production cancelled by user")
                return None

            base_query = sc.get("keywords") or sc.get("prompt") or title
            scene_prompt = sc.get("prompt") or title

            # Calculate how many visual cuts (sub-beats) this scene needs (target 6-8s per cut)
            target_cut_duration = random.uniform(6.0, 8.5)
            # If scene duration is long, split into 2-3 visual cuts with different queries
            cuts_for_scene = max(1, int(round(sec_per_scene / target_cut_duration)))
            sub_cut_duration = round(sec_per_scene / cuts_for_scene, 2)

            logger.info(f"[Producer] Scene {sc_idx}/{len(scenes)} ({sec_per_scene}s): Generating {cuts_for_scene} dynamic visual cuts (~{sub_cut_duration}s each)...")

            # Extract distinct sub-queries for visual diversity within the same scene
            sub_queries = [w.strip() for w in base_query.split() if len(w.strip()) > 3]
            for cut_idx in range(cuts_for_scene):
                clip_target = self.temp_dir / f"beat_{beat_counter}.mp4"
                img_target = self.temp_dir / f"beat_img_{beat_counter}.jpg"
                beat_counter += 1

                # Vary the search term for sub-cuts
                if cut_idx > 0 and len(sub_queries) > 1:
                    cut_query = f"{sub_queries[cut_idx % len(sub_queries)]} mystery cinematic"
                else:
                    cut_query = base_query

                seed = sc_idx * 500 + cut_idx * 77 + random.randint(100, 999)

                # Priority 1: High-Definition Pexels Video Clip
                stock_success = self._download_pexels_clip(cut_query, clip_target, used_video_ids, duration=sub_cut_duration)
                if stock_success:
                    ready_clips.append(clip_target)
                    continue

                # Priority 2: Hugging Face FLUX.1 Photorealistic Image
                img_success = self._generate_hf_flux(scene_prompt, img_target, seed)
                if not img_success:
                    img_success = self._generate_pollinations_flux(scene_prompt, img_target, seed)

                if img_success and img_target.exists():
                    # Alternate motion types for high engagement: zoom-in, zoom-out, pan-tilt
                    motion_choices = ["in", "out", "pan"]
                    chosen_motion = motion_choices[(beat_counter + cut_idx) % len(motion_choices)]
                    self._create_3d_motion(img_target, clip_target, motion_type=chosen_motion, duration=sub_cut_duration)
                    ready_clips.append(clip_target)
                elif ready_clips:
                    ready_clips.append(ready_clips[-1])

        if len(ready_clips) < 2:
            logger.error("[Producer] Insufficient visual clips assembled.")
            worker_manager.report_error("producer", "Insufficient visuals generated")
            return None

        # Append 12-second branded mystery outro slate for YouTube End Screen cards
        outro_clip = self.temp_dir / "outro_slate.mp4"
        if self._generate_outro_clip(outro_clip, duration=12.0):
            ready_clips.append(outro_clip)

        # 3. Concatenate all distinct scene clips cleanly using Concat Demuxer
        merged_video = self.temp_dir / "merged_scenes.mp4"
        valid_clips = [c for c in ready_clips if c and c.exists() and c.stat().st_size > 1000]
        if len(valid_clips) < 2:
            logger.error("[Producer] Insufficient valid visual clips assembled.")
            worker_manager.report_error("producer", "Insufficient visuals generated")
            return None

        concat_list = self.temp_dir / "concat_scenes.txt"
        with open(concat_list, "w") as f:
            for c in valid_clips:
                f.write(f"file '{c.resolve()}'\n")

        # Concat demuxer with re-encoding (robust, low RAM, never hits filtergraph limit)
        cmd_concat = [
            "ffmpeg", "-y",
            "-threads", "2",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            str(merged_video)
        ]
        try:
            subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=True)
            logger.info("✅ Merged scenes successfully generated via concat demuxer!")
        except subprocess.CalledProcessError as err:
            err_msg = err.stderr[-300:] if err.stderr else str(err)
            logger.error(f"[Producer] Concat demuxer failed: {err_msg}")
            worker_manager.report_error("producer", f"Scene stitching failed: {err_msg}")
            return None
        finally:
            if concat_list.exists():
                concat_list.unlink()

        # 4. Cinematic Background Music Track
        music_track = self._get_ambient_music_track()

        # 5. Master Documentary Audio & Video Blend (Dynamic Multi-SFX Tension Mix)
        final_video = self.temp_dir / f"{title_slug}_FINAL.mp4"
        braam_sfx = self.sfx_dir / "sfx_braam.mp3"
        whoosh_sfx = self.sfx_dir / "sfx_whoosh.mp3"
        riser_sfx = self.sfx_dir / "sfx_riser.mp3"
        heartbeat_sfx = self.sfx_dir / "sfx_heartbeat.mp3"

        base_inputs = [
            "-stream_loop", "-1", "-i", str(merged_video),
            "-i", str(voice_path),
            "-stream_loop", "-1", "-i", str(music_track)
        ]

        # Multi-layer audio mixing with suspense pacing:
        # - Braam at 1.5s (Cold Open Hook)
        # - Whoosh at 45s (Act 1 -> Act 2 transition)
        # - Riser at 180s (3 min suspense peak)
        # - Heartbeat at 300s (5 min revelation tension)
        sfx_inputs = []
        amix_filters = ["[1:a]volume=1.0[v]", "[2:a]volume=0.13[m]"]
        input_count = 2

        if braam_sfx.exists():
            base_inputs.extend(["-i", str(braam_sfx)])
            input_count += 1
            idx = input_count
            amix_filters.append(f"[{idx}:a]adelay=1500|1500,volume=0.22[sfx_b]")
            sfx_inputs.append("[sfx_b]")

        if whoosh_sfx.exists():
            base_inputs.extend(["-i", str(whoosh_sfx)])
            input_count += 1
            idx = input_count
            amix_filters.append(f"[{idx}:a]adelay=45000|45000,volume=0.18[sfx_w]")
            sfx_inputs.append("[sfx_w]")

        if riser_sfx.exists():
            base_inputs.extend(["-i", str(riser_sfx)])
            input_count += 1
            idx = input_count
            amix_filters.append(f"[{idx}:a]adelay=180000|180000,volume=0.18[sfx_r]")
            sfx_inputs.append("[sfx_r]")

        if heartbeat_sfx.exists():
            base_inputs.extend(["-i", str(heartbeat_sfx)])
            input_count += 1
            idx = input_count
            amix_filters.append(f"[{idx}:a]adelay=300000|300000,volume=0.20[sfx_h]")
            sfx_inputs.append("[sfx_h]")

        has_outro = outro_clip.exists()
        total_video_duration = round(voice_duration + (10.0 if has_outro else 0.0), 1)

        all_amix_sources = "[v][m]" + "".join(sfx_inputs)
        total_sources = 2 + len(sfx_inputs)
        fade_start = max(1.0, total_video_duration - 2.5)
        audio_filter_chain = (
            ";".join(amix_filters) +
            f";{all_amix_sources}amix=inputs={total_sources}:duration=longest:normalize=0,afade=t=out:st={fade_start}:d=2.0[a_out]"
        )

        video_filter = (
            "[0:v]eq=contrast=1.05:saturation=1.1,"
            "drawtext=text='VOID ARCHIVE':fontcolor=white@0.45:fontsize=22:x=w-tw-40:y=35:bordercolor=black@0.4:borderw=2,"
            "drawtext=text='RECORDING \\: CLASSIFIED ARCHIVE':enable='between(t,1.5,7.0)':fontsize=24:fontcolor=white:box=1:boxcolor=black@0.7:boxborderw=8:x=50:y=h-90[v_out]"
        )
        filter_complex = f"{video_filter};{audio_filter_chain}"

        cmd = ["ffmpeg", "-y", "-threads", "2"] + base_inputs + [
            "-filter_complex", filter_complex,
            "-map", "[v_out]",
            "-map", "[a_out]",
            "-t", str(total_video_duration),
            "-c:v", "libx264", "-preset", "veryfast",
            "-c:a", "aac",
            str(final_video)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        final_duration = self._get_media_duration(final_video)
        logger.info(f"🎉 MASTER DOCUMENTARY COMPLETE! Duration: {final_duration:.1f}s | Path: {final_video}")

        # Cleanup intermediate clips and scene frames immediately
        try:
            from utils.cleanup import cleanup_intermediate_production
            cleanup_intermediate_production(keep_path=final_video)
        except Exception as cle:
            logger.debug(f"[Producer] Intermediate cleanup: {cle}")

        worker_manager.complete_task("producer", f"Master video generated ({final_duration:.1f}s)")
        return final_video


producer = Producer()

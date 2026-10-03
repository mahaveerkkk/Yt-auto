import json
import random
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from config.settings import settings
from utils.logger import logger
from core.worker_manager import worker_manager
from core.omni_router import omni_router
from core.studio_memory import studio_memory


class Scout:
    """
    Trend & Topic Scout Agent.
    Combines:
    1. Real-time Live Google Trends & News RSS (Instant viral detection)
    2. Curated High-RPM Mystery Pools (Deep Ocean, Space, Ancient Secrets, Quantum, Bermuda)
    3. Anti-Duplication History Cache
    """

    CURATED_HIGH_RPM_POOLS = [
        {
            "category": "Deep Ocean Abyss",
            "topic": "The 1997 Pacific Bloop Anomaly",
            "angle": "An ultra-low-frequency sound detected across 5,000 km in the South Pacific that matched no known creature.",
            "keywords": ["ocean abyss", "hydrophone sonar", "deep sea creature", "submarine radar anomaly"]
        },
        {
            "category": "Dark Space & Astronomy",
            "topic": "The Wow! Signal: Interstellar Transmission",
            "angle": "A 72-second narrow-band radio signal from constellation Sagittarius that was 30 times louder than cosmic background noise.",
            "keywords": ["radio telescope observatory", "deep space galaxy", "mysterious signal screen", "alien cosmos anomaly"]
        },
        {
            "category": "Forbidden Ancient Civilizations",
            "topic": "The Richat Structure: Atlantis in the Sahara",
            "angle": "A mysterious 40-kilometer concentric geological dome in Mauritania perfectly matching Plato's description of Atlantis.",
            "keywords": ["desert eye of sahara", "ancient ruins satellite view", "golden concentric circles", "desert ancient pyramid"]
        },
        {
            "category": "Deep Ocean Abyss",
            "topic": "The Mariana Trench Challenger Deep Metallic Sound",
            "angle": "Scientists lowering hydrophones to 36,000 feet captured recurring metallic hums that physics cannot replicate naturally.",
            "keywords": ["deep submarine abyss", "ocean trench underwater", "bioluminescent anomaly", "sonar audio wave"]
        },
        {
            "category": "Classified Aviation & Maritime",
            "topic": "Flight 19: The Lost Patrol of the Bermuda Triangle",
            "angle": "Five US Navy torpedo bombers vanished simultaneously off Florida while their compasses spun wildly in clear weather.",
            "keywords": ["vintage bomber planes storm", "bermuda triangle compass spinning", "ocean mist vortex", "empty ocean wreckage"]
        },
        {
            "category": "Quantum & Universe Physics",
            "topic": "The Boötes Void: The Great Nothing in the Cosmos",
            "angle": "A massive 330-million-light-year spherical sphere of almost pure empty space where 2,000 galaxies should exist.",
            "keywords": ["empty black cosmic void", "isolated lonely galaxy", "space telescope deep field", "starless cosmic dark"]
        },
        {
            "category": "Forbidden Ancient Civilizations",
            "topic": "Göbekli Tepe: The 12,000-Year-Old Astronomical Observatory",
            "angle": "Massive megalithic T-shaped stone pillars carved before agriculture, metal tools, or wheel inventions.",
            "keywords": ["ancient stone pillars", "archeological excavation ruins", "ancient carved stone animal", "desert night sky"]
        },
        {
            "category": "Dark Space & Astronomy",
            "topic": "Tabby's Star: The Irregular Megastructure",
            "angle": "KIC 8462852 dips in brightness by up to 22% in non-periodic cycles, baffling astrophysicists searching for natural causes.",
            "keywords": ["dyson sphere alien megastructure", "deep space star", "astronomical telescope data", "cosmic darkness"]
        },
        {
            "category": "Classified Aviation & Maritime",
            "topic": "The Ghost Ship SS Ourang Medan Mystery",
            "angle": "A Dutch cargo vessel sent frantic Morse code distress signals before crew members were discovered frozen in terror.",
            "keywords": ["abandoned ghost ship fog", "ocean storm waves", "vintage radio transmitter morse", "eerie dark ocean"]
        }
    ]

    def __init__(self):
        self.history_file = settings.LOGS_DIR / "scout_history.json"

    def _load_history(self) -> List[str]:
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self, topic: str):
        history = self._load_history()
        history.append(topic)
        history = history[-100:]
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "w") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.warning(f"[Scout] Could not save history: {e}")

    def fetch_live_trending_news(self) -> List[Dict[str, Any]]:
        """Scouts real-time trending mystery, ocean discovery, and astronomy news from Google Trends RSS."""
        queries = ["unexplained ocean mystery", "deep space discovery anomaly", "ancient ruins archeology discovery"]
        live_topics = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        for q in queries:
            try:
                url = f"https://news.google.com/rss/search?q={q.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    root = ET.fromstring(res.content)
                    items = root.findall(".//item")
                    for it in items[:3]:
                        title = it.find("title").text
                        clean_title = title.split(" - ")[0].strip()
                        live_topics.append({
                            "category": f"Trending Discovery",
                            "topic": clean_title[:80],
                            "angle": clean_title,
                            "keywords": q.split()
                        })
            except Exception as e:
                logger.debug(f"[Scout] Google RSS query '{q}' error: {e}")

        logger.info(f"[Scout] Scraped {len(live_topics)} live trending topics from Google News.")
        return live_topics

    YOUTUBE_INSPIRATION_CHANNELS = [
        {"name": "Astrum", "id": "UC9RM-iSvTu1uPJb8X5yp3EQ", "category": "Dark Space & Astronomy"},
        {"name": "RealLifeLore", "id": "UCLtREJY21xRfCuEKvdki1Kw", "category": "Classified Aviation & Maritime"},
        {"name": "Kurzgesagt", "id": "UCsXVk37bltHxD1rDPwtNM8Q", "category": "Quantum & Universe Physics"},
        {"name": "SciShow Space", "id": "UC0cd_-e49hZpWLH3UIwoWRA", "category": "Dark Space & Astronomy"}
    ]

    def fetch_youtube_channel_trends(self) -> List[Dict[str, Any]]:
        """Scrapes recent video titles from high-performing science/mystery channels via public RSS."""
        channel_topics = []
        for ch in self.YOUTUBE_INSPIRATION_CHANNELS:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch['id']}"
            try:
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    root = ET.fromstring(res.content)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    entries = root.findall("atom:entry", ns)
                    for e in entries[:2]:
                        t_el = e.find("atom:title", ns)
                        if t_el is not None and t_el.text:
                            raw_t = t_el.text.strip()
                            channel_topics.append({
                                "category": ch["category"],
                                "topic": raw_t[:80],
                                "angle": f"Investigating the phenomenon behind: {raw_t}",
                                "keywords": raw_t.split()[:4]
                            })
            except Exception as e:
                logger.debug(f"[Scout] YouTube RSS channel {ch['name']} error: {e}")

        logger.info(f"[Scout] Scraped {len(channel_topics)} recent inspiration topics from YouTube RSS.")
        return channel_topics

    def _polish_viral_title(self, raw_candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses Gemini OmniRouter to transform raw headlines or viewer requests into
        an elite, psychological click-magnet mystery title and narrative angle.
        """
        raw_topic = raw_candidate.get("topic", "")
        category = raw_candidate.get("category", "Mystery")
        raw_angle = raw_candidate.get("angle", "")

        prompt = (
            f"You are the Lead YouTube Showrunner for 'Void Archive' (mystery, ocean abyss, dark space, ancient forbidden history).\n"
            f"Given this raw discovery or headline:\n"
            f"Raw Topic: '{raw_topic}'\n"
            f"Category: '{category}'\n"
            f"Context: '{raw_angle}'\n\n"
            f"Transform this into an elite, blockbuster YouTube documentary dossier:\n"
            f"1. 'topic': A high-CTR, psychological mystery title (under 65 chars, dramatic, curiosity-inducing, e.g. 'The 7-Mile Abyss That Swallowed 5 Submarines').\n"
            f"2. 'angle': A gripping 3-act narrative hook (under 120 words) with 2 unanswered questions that force viewers to watch till the end.\n"
            f"3. 'keywords': An array of 4 distinct visual keywords for cinematic HD stock video and AI image generation.\n\n"
            f"Return ONLY valid JSON matching this exact structure:\n"
            f'{{"topic": "...", "angle": "...", "keywords": ["...", "..."]}}'
        )

        try:
            res = omni_router.query(prompt=prompt)
            if res:
                clean = res.strip()
                if "{" in clean and "}" in clean:
                    start_idx = clean.find("{")
                    end_idx = clean.rfind("}")
                    if start_idx >= 0 and end_idx > start_idx:
                        clean = clean[start_idx:end_idx+1]
                    data = json.loads(clean)
                    if data.get("topic") and len(data.get("topic")) > 5:
                        logger.info(f"[Scout] ✨ Polished '{raw_topic}' -> '{data.get('topic')}'")
                        return {
                            "category": category,
                            "topic": data.get("topic").strip().replace('"', ''),
                            "angle": data.get("angle", raw_angle).strip(),
                            "keywords": data.get("keywords") or raw_candidate.get("keywords", [])
                        }
        except Exception as e:
            logger.warning(f"[Scout] Viral title polishing skipped: {e}")

        # Local heuristic mystery hook polishing if cloud models unreachable
        clean_raw = raw_topic.strip().rstrip(".")
        if not clean_raw.lower().startswith(("the ", "why ", "what ", "inside ")):
            fallback_title = f"The Classified Mystery of {clean_raw}"
        else:
            fallback_title = f"{clean_raw}: Unexplained Files"
        return {
            "category": category,
            "topic": fallback_title[:65],
            "angle": raw_angle or f"Declassified investigation into {clean_raw}.",
            "keywords": raw_candidate.get("keywords") or [category, "Mystery", "Declassified", "Anomaly"]
        }

    def pick_next_viral_topic(self, user_override: Optional[str] = None) -> Dict[str, Any]:
        """Chooses the next high-retention viral topic with zero repetition and Gemini hook polishing."""
        worker_manager.start_task("scout", "Evaluating web trends, YouTube RSS, and audience suggestions")

        if user_override:
            logger.info(f"[Scout] Using commissioned topic: '{user_override}'")
            candidate = {
                "category": "Special Investigation",
                "topic": user_override,
                "angle": f"In-depth classified investigation of {user_override}",
                "keywords": [user_override]
            }
            polished = self._polish_viral_title(candidate)
            worker_manager.complete_task("scout", f"Topic selected: {polished['topic']}")
            return polished

        # 0. Check for viewer-requested topics mined from comments in content_calendar
        try:
            planned_items = studio_memory.get_calendar(status="planned")
            if planned_items:
                top_viewer = planned_items[0]
                studio_memory.update_calendar_status(top_viewer["id"], "producing")
                raw_cand = {
                    "category": top_viewer.get("category", "Audience Dossier"),
                    "topic": top_viewer.get("topic", ""),
                    "angle": f"Audience-commissioned investigation into {top_viewer.get('topic')}",
                    "keywords": top_viewer.get("topic", "").split()[:4]
                }
                logger.info(f"[Scout] 🎯 Prioritizing viewer-requested topic from comments: '{raw_cand['topic']}'")
                polished = self._polish_viral_title(raw_cand)
                self._save_history(raw_cand["topic"])
                self._save_history(polished["topic"])
                worker_manager.complete_task("scout", f"Audience topic locked: {polished['topic']}")
                return polished
        except Exception as ce:
            logger.debug(f"[Scout] Content calendar check skipped: {ce}")

        history = self._load_history()

        # 1. 35% chance: Pick fresh live discovery from Google Trends RSS
        live_news = self.fetch_live_trending_news()
        fresh_live = [t for t in live_news if t["topic"] not in history]
        if fresh_live and random.random() < 0.35:
            chosen = random.choice(fresh_live)
            polished = self._polish_viral_title(chosen)
            self._save_history(chosen["topic"])
            self._save_history(polished["topic"])
            logger.info(f"[Scout] Selected LIVE web trend: '{polished['topic']}'")
            worker_manager.complete_task("scout", f"Live trend locked: {polished['topic']}")
            return polished

        # 2. 25% chance: Pick viral topic from high-performing YouTube RSS channels
        yt_trends = self.fetch_youtube_channel_trends()
        fresh_yt = [t for t in yt_trends if t["topic"] not in history]
        if fresh_yt and random.random() < 0.25:
            chosen = random.choice(fresh_yt)
            polished = self._polish_viral_title(chosen)
            self._save_history(chosen["topic"])
            self._save_history(polished["topic"])
            logger.info(f"[Scout] Selected YouTube RSS inspiration: '{polished['topic']}'")
            worker_manager.complete_task("scout", f"YT inspiration locked: {polished['topic']}")
            return polished

        # 3. 40% chance (or fallback): Select from High-RPM Curated Documentary Pool
        candidates = [t for t in self.CURATED_HIGH_RPM_POOLS if t["topic"] not in history]
        if not candidates:
            candidates = self.CURATED_HIGH_RPM_POOLS

        chosen = random.choice(candidates)
        # Even curated topics can be enriched or used as-is
        self._save_history(chosen["topic"])
        logger.info(f"[Scout] Selected High-RPM topic: '{chosen['topic']}' (Category: {chosen['category']})")
        worker_manager.complete_task("scout", f"High-RPM topic locked: {chosen['topic']}")
        return chosen


scout = Scout()

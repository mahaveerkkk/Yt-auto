import json
import random
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from config.settings import settings
from utils.logger import logger
from core.worker_manager import worker_manager


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

    def pick_next_viral_topic(self, user_override: Optional[str] = None) -> Dict[str, Any]:
        """Chooses the next high-retention viral topic with zero repetition."""
        worker_manager.start_task("scout", "Evaluating web trends and high-RPM candidate pool")

        if user_override:
            logger.info(f"[Scout] Using commissioned topic: '{user_override}'")
            worker_manager.complete_task("scout", f"Topic selected: {user_override}")
            return {
                "category": "Special Investigation",
                "topic": user_override,
                "angle": f"In-depth classified investigation of {user_override}",
                "keywords": [user_override]
            }

        history = self._load_history()

        # 1. 40% chance: Pick fresh live discovery from Google Trends RSS
        live_news = self.fetch_live_trending_news()
        fresh_live = [t for t in live_news if t["topic"] not in history]
        if fresh_live and random.random() < 0.4:
            chosen = random.choice(fresh_live)
            self._save_history(chosen["topic"])
            logger.info(f"[Scout] Selected LIVE web trend: '{chosen['topic']}'")
            worker_manager.complete_task("scout", f"Selected Live: {chosen['topic']}")
            return chosen

        # 2. 60% chance: Select from High-RPM Curated Documentary Pool
        candidates = [t for t in self.CURATED_HIGH_RPM_POOLS if t["topic"] not in history]
        if not candidates:
            candidates = self.CURATED_HIGH_RPM_POOLS

        chosen = random.choice(candidates)
        self._save_history(chosen["topic"])
        logger.info(f"[Scout] Selected High-RPM topic: '{chosen['topic']}' (Category: {chosen['category']})")
        worker_manager.complete_task("scout", f"Selected Pool: {chosen['topic']}")
        return chosen


scout = Scout()

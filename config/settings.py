import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "config" / ".env"

# Load .env if present
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


class Settings:
    BASE_DIR: Path = BASE_DIR
    # --- Project Info ---
    PROJECT_NAME: str = "AutoDirector"
    VERSION: str = "2.0.0"

    # --- API Keys ---
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # --- LLM Settings ---
    # Primary: qwen/qwen3.8-27b:free (fast & powerful), Fallback: gemini-2.5-flash
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "qwen/qwen3.8-27b:free")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    LLM_PRIORITY: list = ["openrouter", "gemini"]

    # --- Video Engine Settings ---
    # Provider chain priority
    VIDEO_PROVIDERS: list = ["wan3_api", "wan2_hf", "ltx_hf", "pexels"]
    HF_WAN_SPACE: str = os.getenv("HF_WAN_SPACE", "Wan-AI/Wan2.1")
    HF_LTX_SPACE: str = os.getenv("HF_LTX_SPACE", "Lightricks/LTX-Video")
    HF_TIMEOUT_SECONDS: int = 180  # 3 min timeout for Hugging Face queues

    # --- Voice Settings (edge-tts) ---
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "hi")  # 'hi' or 'en'
    VOICE_HI_MALE: str = "hi-IN-MadhurNeural"
    VOICE_HI_FEMALE: str = "hi-IN-SwaraNeural"
    VOICE_EN_MALE: str = "en-US-GuyNeural"
    VOICE_EN_FEMALE: str = "en-US-JennyNeural"

    # --- Video Specs (Widescreen 16:9 / 1280x720) ---
    VIDEO_WIDTH: int = 1280
    VIDEO_HEIGHT: int = 720
    VIDEO_FPS: int = 30
    AUDIO_SAMPLE_RATE: int = 48000
    MAX_SCENES: int = 4
    SCENE_DURATION_SEC: int = 5

    # --- Paths ---
    TEMP_DIR: Path = Path("/tmp/autodirector")
    PARTS_DIR: Path = TEMP_DIR / "parts"
    OUTPUT_DIR: Path = TEMP_DIR / "output"
    ASSETS_DIR: Path = BASE_DIR / "assets"
    MUSIC_DIR: Path = ASSETS_DIR / "music"
    LOGS_DIR: Path = BASE_DIR / "logs"

    def ensure_directories(self):
        """Create necessary temporary and output directories in /tmp."""
        for p in [self.TEMP_DIR, self.PARTS_DIR, self.OUTPUT_DIR, self.LOGS_DIR, self.MUSIC_DIR]:
            p.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()

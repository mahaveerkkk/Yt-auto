import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config.settings import settings

settings.ensure_directories()
LOG_FILE = settings.LOGS_DIR / "autodirector.log"

logger = logging.getLogger("AutoDirector")
log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO)
logger.setLevel(log_level)

# Formatter
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(module)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# File Handler (Max 5MB per file, max 3 backups)
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
file_handler.setFormatter(formatter)
file_handler.setLevel(log_level)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(log_level)

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

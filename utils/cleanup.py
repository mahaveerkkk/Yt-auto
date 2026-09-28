import shutil
from pathlib import Path
from config.settings import settings
from utils.logger import logger


def clean_temp_storage(keep_final: bool = False):
    """
    Cleans up temporary video parts, audio, and intermediate files.
    If keep_final is True, preserves the final output video.
    """
    try:
        if settings.PARTS_DIR.exists():
            shutil.rmtree(settings.PARTS_DIR, ignore_errors=True)
            logger.info("Cleared temporary video parts directory.")

        if not keep_final and settings.OUTPUT_DIR.exists():
            shutil.rmtree(settings.OUTPUT_DIR, ignore_errors=True)
            logger.info("Cleared final output directory.")

        # Re-ensure fresh empty directories
        settings.ensure_directories()
    except Exception as e:
        logger.warning(f"Error during temp cleanup: {e}")


def cleanup_file(file_path: Path):
    """Safely delete a single file if it exists."""
    try:
        p = Path(file_path)
        if p.exists():
            p.unlink()
            logger.info(f"Deleted temp file: {p.name}")
    except Exception as e:
        logger.warning(f"Could not delete {file_path}: {e}")

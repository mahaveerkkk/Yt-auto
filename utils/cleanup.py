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


def cleanup_intermediate_production(keep_path: Path = None):
    """
    Wipes all intermediate scene clips, images, and audio from /tmp/autodirector_production,
    preserving ONLY the master final video file.
    Guarantees that each video leaves zero garbage on disk.
    """
    import tempfile
    prod_dir = Path(tempfile.gettempdir()) / "autodirector_production"
    if not prod_dir.exists():
        return

    purged_bytes = 0
    purged_count = 0
    try:
        for f in prod_dir.iterdir():
            if keep_path and f.resolve() == keep_path.resolve():
                continue
            if f.is_file():
                try:
                    size = f.stat().st_size
                    f.unlink()
                    purged_bytes += size
                    purged_count += 1
                except Exception:
                    pass
        logger.info(f"[Cleanup] Wiped {purged_count} intermediate production files ({purged_bytes / (1024*1024):.1f} MB freed).")
    except Exception as e:
        logger.warning(f"[Cleanup] Error purging intermediate production: {e}")


def prune_disk_hygiene(max_age_hours: int = 48) -> dict:
    """
    1-Year Autopilot Disk Hygiene Engine:
    - Purges thumbnail drafts older than max_age_hours.
    - Purges any stranded production clips or logs older than max_age_hours.
    - Monitors and reports free disk space.
    """
    import time
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    freed_mb = 0

    import tempfile
    tmp = Path(tempfile.gettempdir())
    scan_dirs = [
        tmp / "autodirector_thumbs",
        tmp / "autodirector_production"
    ]

    for d in scan_dirs:
        if not d.exists():
            continue
        try:
            for item in d.glob("*"):
                if item.is_file() and (item.name.startswith("thumb_") or item.name.startswith("clip_") or item.name.startswith("scene_")):
                    try:
                        if item.stat().st_mtime < cutoff:
                            size = item.stat().st_size
                            item.unlink()
                            freed_mb += (size / (1024 * 1024))
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"[Disk Hygiene] Directory scan error: {e}")

    # Check total disk stats
    try:
        usage = shutil.disk_usage("/")
        free_gb = round(usage.free / (1024 ** 3), 2)
    except Exception:
        free_gb = 0.0

    logger.info(f"[Disk Hygiene] Maintenance complete: {freed_mb:.1f} MB purged. Free space: {free_gb} GB.")
    return {"freed_mb": freed_mb, "free_disk_gb": free_gb}

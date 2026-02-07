import logging
import os
from datetime import datetime

from config import LOG_FOLDER, MAX_LOGS  # Import from new config

def cleanup_old_logs():
    """Keeps only the last MAX_LOGS log files, deletes older ones."""
    logs = sorted(
        [f for f in os.listdir(LOG_FOLDER) if f.startswith("raid_tool_") and f.endswith(".log")],
        key=lambda x: os.path.getmtime(os.path.join(LOG_FOLDER, x))
    )
    while len(logs) > MAX_LOGS:
        oldest = logs.pop(0)
        try:
            os.remove(os.path.join(LOG_FOLDER, oldest))
        except OSError as e:
            logging.warning(f"Failed to delete old log {oldest}: {e}")  # Added error handling

def setup_logger():
    """
    Sets up a logger that writes to a timestamped file.
    Keeps only the last MAX_LOGS logs.
    Returns:
        logging.Logger: Configured logger.
    """
    cleanup_old_logs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_FOLDER, f"raid_tool_{timestamp}.log")

    logger = logging.getLogger("raid_tool")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
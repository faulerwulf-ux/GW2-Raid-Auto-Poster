# logger_setup.py
import logging
import os
from datetime import datetime

# Path where logs will be saved
LOG_FOLDER = "logs"
os.makedirs(LOG_FOLDER, exist_ok=True)

# Max number of saved logs
MAX_LOGS = 3  # can later move to config

def cleanup_old_logs():
    """Keeps only the last MAX_LOGS log files, deletes older ones."""
    logs = sorted(
        [f for f in os.listdir(LOG_FOLDER) if f.startswith("raid_tool_") and f.endswith(".log")],
        key=lambda x: os.path.getmtime(os.path.join(LOG_FOLDER, x))
    )

    while len(logs) > MAX_LOGS:
        oldest = logs.pop(0)
        os.remove(os.path.join(LOG_FOLDER, oldest))

def setup_logger(name="raid_tool"):
    """
    Sets up a logger that writes to a timestamped file.
    Keeps only the last MAX_LOGS logs.
    """
    # Cleanup old logs first
    cleanup_old_logs()

    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_FOLDER, f"raid_tool_{timestamp}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

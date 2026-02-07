import time
import psutil

from config import LOG_DIR, INACTIVITY_THRESHOLD_MINUTES, GW2_EXIT_GRACE_SECONDS
from logger import setup_logger
from session import RaidSession
from watcher import start_log_watcher

logger = setup_logger()

def is_gw2_running() -> bool:
    """Check if GW2 process is running."""
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] and proc.info["name"].lower() == "gw2-64.exe":
            return True
    return False

def main():
    session_ref = {"current_session": None}  # Mutable ref to share session state
    observer = start_log_watcher(LOG_DIR, session_ref)  # Pass ref dict

    try:
        while True:
            if not is_gw2_running():
                logger.info("[Main] GW2 closed. Waiting grace period...")
                grace_start = time.time()
                while time.time() - grace_start < GW2_EXIT_GRACE_SECONDS:
                    if is_gw2_running():
                        logger.info("[Main] GW2 reopened within grace period, resuming...")
                        break
                    time.sleep(1)
                else:
                    if session_ref["current_session"] is not None:
                        session_ref["current_session"].end_session()
                        session_ref["current_session"] = None
                    logger.info("[Main] GW2 closed beyond grace; shutting down.")
                    break

            if session_ref["current_session"] and session_ref["current_session"].has_inactivity(INACTIVITY_THRESHOLD_MINUTES):
                logger.info("[Main] Inactivity detected; ending session.")
                session_ref["current_session"].end_session()
                session_ref["current_session"] = None

            time.sleep(5)  # Poll interval

    except KeyboardInterrupt:
        logger.info("[Main] Keyboard interrupt; shutting down gracefully.")
    except Exception:
        logger.exception("[Main] Unhandled exception")

    finally:
        observer.stop()
        observer.join()
        if session_ref["current_session"]:
            session_ref["current_session"].end_session()
        logger.info("[Main] Tool shutting down.")

if __name__ == "__main__":
    main()
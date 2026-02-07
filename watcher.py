from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import is_raid_session
from logger import setup_logger
from session import RaidSession  # Import here for creation
from uploader import is_final_zevtc, upload_log_to_dps_report

logger = setup_logger()

class LogHandler(FileSystemEventHandler):
    def __init__(self, session_ref: dict):
        self.session_ref = session_ref

    def on_moved(self, event):
        if event.is_directory or not is_final_zevtc(event.dest_path):
            return

        logger.info("Final arcdps log detected: %s", event.dest_path)

        upload_result = upload_log_to_dps_report(event.dest_path)
        if not upload_result:
            return

        players = upload_result.get("players")
        if not is_raid_session(players):
            logger.info("[Session] Log skipped (not enough core members)")
            return

        # Get or create session using mutable ref
        current_session = self.session_ref["current_session"]
        if current_session is None:
            current_session = RaidSession("Guild Raid Night")
            logger.info("[Session] Starting new session")
            self.session_ref["current_session"] = current_session  # Update ref

        current_session.add_log(event.dest_path, upload_result)
        current_session.post_or_update_discord()

def start_log_watcher(log_dir: str, session_ref: dict):
    """
    Start filesystem watcher.
    
    Args:
        log_dir (str): Directory to watch.
        session_ref (dict): Mutable ref to current session.
    Returns:
        Observer: The started observer.
    """
    observer = Observer()
    handler = LogHandler(session_ref)
    observer.schedule(handler, log_dir, recursive=True)
    observer.start()
    return observer
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict

import psutil
import requests

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from discord_webhook import DISCORD_WEBHOOK_URL
from content_map import BOSS_CONTENT_MAP
from raid_group_config import is_raid_session, get_core_member_count

from logger_setup import setup_logger
logger = setup_logger()

# ============================================================
# Configuration
# ============================================================

LOG_DIR = r"C:\Users\deven\Documents\GUILD WARS 2\addons\arcdps\arcdps.cbtlogs"
INACTIVITY_THRESHOLD_MINUTES = 180
GW2_EXIT_GRACE_SECONDS = 30

# ============================================================
# Helper: GW2 process detection
# ============================================================

def is_gw2_running() -> bool:
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] and proc.info["name"].lower() == "gw2-64.exe":
            return True
    return False

# ============================================================
# Helper: arcdps log parsing
# ============================================================

def is_final_zevtc(path: str) -> bool:
    return path.endswith(".zevtc") and os.path.isfile(path)

def get_boss_name_from_log(log_path: str) -> str:
    parent = os.path.basename(os.path.dirname(log_path))
    return parent.split("(", 1)[0].strip()

# ============================================================
# Helper: DPS.report upload
# ============================================================

def upload_log_to_dps_report(log_path: str) -> dict | None:
    url = "https://dps.report/uploadContent"
    try:
        with open(log_path, "rb") as f:
            response = requests.post(url, files={"file": f}, data={"json": "1"}, timeout=60)

        if response.status_code == 422:
            logger.info("[Upload] Log already uploaded elsewhere (duplicate).")
            return None

        if response.status_code != 200:
            logger.info("[Upload] Failed (%s) for %s", response.status_code, log_path)
            logger.info("[Upload] Response: %s", response.text)
            return None

        payload = response.json()
        permalink = payload.get("permalink")
        if not permalink:
            logger.info("[Upload] No permalink returned: %s", payload)
            return None

        encounter = payload.get("encounter", {})
        players = payload.get("players", [])
        result = {
            "permalink": permalink,
            "success": encounter.get("success", False),
            "boss_name": encounter.get("boss", ""),
            "player_count": encounter.get("numberOfPlayers", 0),
            "is_cm": encounter.get("isCm", False),
            "players": players
        }

        logger.info(
            "[Upload] Uploaded: %s (Success: %s, Boss: %s, Players: %s, CM: %s)",
            permalink, result["success"], result["boss_name"], result["player_count"], result["is_cm"]
        )
        return result

    except Exception as e:
        logger.error("[Upload] Exception: %s", e)
        return None

# ============================================================
# Helper: Discord webhook
# ============================================================

def post_to_discord(message: str) -> str | None:
    response = requests.post(DISCORD_WEBHOOK_URL + "?wait=true", json={"content": message}, timeout=10)
    if response.status_code not in (200, 204):
        logger.warning("[Discord] Failed to post: %s", response.text)
        return None
    return response.json().get("id")

def edit_discord_message(message_id: str, message: str):
    response = requests.patch(f"{DISCORD_WEBHOOK_URL}/messages/{message_id}", json={"content": message}, timeout=10)
    if response.status_code not in (200, 204):
        logger.warning("[Discord] Failed to edit: %s", response.text)

# ============================================================
# RaidSession class
# ============================================================

class RaidSession:
    def __init__(self, name: str):
        self.name = name
        self.start_time = datetime.now()
        self.last_log_time = datetime.now()
        self.grouped_logs = defaultdict(lambda: defaultdict(list))
        self.display_links = defaultdict(dict)
        self.discord_message_id: str | None = None

    def add_log(self, log_path: str, upload_result: dict):
        self.last_log_time = datetime.now()
        if not upload_result:
            return

        players = upload_result.get("players", {})
        if not is_raid_session(players):
            logger.info("[Session] Skipping log with insufficient core members: %s", log_path)
            return

        boss_name = get_boss_name_from_log(log_path)
        if boss_name not in BOSS_CONTENT_MAP:
            logger.info("[Session] Skipped non-raid boss '%s': %s", boss_name, log_path)
            return

        if not upload_result.get("success", False):
            logger.info("[Session] Skipping failed attempt: %s", boss_name)
            return

        wing, short_name, order = BOSS_CONTENT_MAP[boss_name]
        link = upload_result["permalink"]
        display_name = short_name
        if upload_result.get("is_cm", False):
            display_name = f"{short_name} CM"

        self.grouped_logs[wing][short_name].append(link)
        if short_name not in self.display_links[wing]:
            self.display_links[wing][short_name] = []
        self.display_links[wing][short_name].append({
            'link': link,
            'order': order,
            'display_name': display_name
        })
        logger.info("[Session] Added successful %s (%s) to %s: %s", boss_name, display_name, wing, log_path)

    def has_inactivity(self, threshold_minutes: int) -> bool:
        return datetime.now() - self.last_log_time > timedelta(minutes=threshold_minutes)

    def to_discord_message(self) -> str:
        lines = [self.name, ""]

        def wing_sort_key(wing):
            if wing.startswith("Wing ") and len(wing.split()) > 1:
                try:
                    return int(wing.split()[1]), wing
                except ValueError:
                    pass
            return 999, wing

        for wing in sorted(self.display_links.keys(), key=wing_sort_key):
            lines.append(f"{wing}:")
            for boss_short in sorted(self.display_links[wing].keys(),
                                    key=lambda b: self.display_links[wing][b][0]['order']):
                for boss_data in self.display_links[wing][boss_short]:
                    display_name = boss_data.get('display_name', boss_short)
                    lines.append(f"{display_name}: {boss_data['link']}")
            lines.append("")
        return "\n".join(lines)

    def post_or_update_discord(self):
        message = self.to_discord_message()
        if self.discord_message_id is None:
            self.discord_message_id = post_to_discord(message)
            logger.info("[Discord] Session posted.")
        else:
            edit_discord_message(self.discord_message_id, message)
            logger.info("[Discord] Session updated.")

# ============================================================
# Watchdog: log observer
# ============================================================

class LogHandler(FileSystemEventHandler):
    def __init__(self, session_ref: dict):
        self.session_ref = session_ref

    def on_moved(self, event):
        # Ignore directories
        if event.is_directory:
            return

        # Only handle final .zevtc files
        if not is_final_zevtc(event.dest_path):
            return

        logger.info("Final arcdps log detected: %s", event.dest_path)

        # Upload and check core members
        upload_result = upload_log_to_dps_report(event.dest_path)
        if not upload_result:
            return  # failed upload, skip

        players = upload_result.get("players")
        if not is_raid_session(players):
            logger.info("[Session] Log skipped (not enough core members)")
            return

        # Create session if none exists
        if self.session_ref["current_session"] is None:
            self.session_ref["current_session"] = RaidSession("Guild Raid Night")
            logger.info("[Session] Starting new session")

        # Add log to session and update Discord
        self.session_ref["current_session"].add_log(event.dest_path, upload_result)
        self.session_ref["current_session"].post_or_update_discord()


def start_log_watcher(log_dir: str, session_ref: dict):
    observer = Observer()
    handler = LogHandler(session_ref)
    observer.schedule(handler, log_dir, recursive=True)
    observer.start()
    return observer

# ============================================================
# Main loop
# ============================================================

def main():
    session_ref = {"current_session": None}
    observer = start_log_watcher(LOG_DIR, session_ref)

    try:
        while True:
            current_session = session_ref["current_session"]

            if not is_gw2_running():
                logger.info("GW2 closed. Waiting grace period...")
                grace_start = time.time()
                while time.time() - grace_start < GW2_EXIT_GRACE_SECONDS:
                    if is_gw2_running():
                        logger.info("GW2 reopened within grace period, resuming session...")
                        break
                    time.sleep(1)
                else:
                    if current_session is not None:
                        logger.info("[Session] GW2 closed beyond grace period, ending session.")
                        current_session.post_or_update_discord()
                    break

            if current_session is not None and current_session.has_inactivity(INACTIVITY_THRESHOLD_MINUTES):
                logger.info("[Session] No new logs for threshold, ending session.")
                current_session.post_or_update_discord()
                session_ref["current_session"] = None

            time.sleep(5)

    except Exception:
        logger.exception("Unhandled exception caused program crash")

    finally:
        observer.stop()
        observer.join()
        logger.info("Tool shutting down.")

if __name__ == "__main__":
    main()

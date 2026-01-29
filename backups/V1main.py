import time
import os
import psutil
import requests
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
LOG_DIR = r"C:\Users\deven\Documents\GUILD WARS 2\addons\arcdps\arcdps.cbtlogs"
INACTIVITY_THRESHOLD_MINUTES = 3  # minutes for testing
INACTIVITY_CHECK_INTERVAL = 10    # seconds
GRACE_PERIOD = 30                 # seconds after GW2 closes
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1465551021093818562/tMh8ogzGSr2z1RpEl8xhgNOBRKP0FJboR1Zrf0-gnWw5JlDcB93WAYVLukCx3pjXWiYS"

class RaidSession:
    def __init__(self, session_name=None):
        self.start_time = datetime.now()
        self.logs: list[str] = []
        self.log_links: list[str] = []
        self.last_log_time = None
        self.session_name = session_name or "Unnamed Raid Session"
        self.discord_message_id = None
        self.discord_message_id: str | None = None

    def add_log(self, log_path):
        now = datetime.now()
        self.last_log_time = now

        self.logs.append(log_path)

        link = upload_log_to_dps_report(log_path)
        if link:
            self.log_links.append(link)

        print(f"[Session] Added log: {log_path}")

        # Post or update Discord
        if self.log_links:
            message = self.to_discord_message()

            if self.discord_message_id is None:
                self.discord_message_id = post_to_discord(message)
            else:
                edit_discord_message(self.discord_message_id, message)


    def has_inactivity(self, threshold_minutes=180):
        if not self.last_log_time:
            return False
        return datetime.now() - self.last_log_time > timedelta(minutes=threshold_minutes)

    def summary(self):
        print(f"\n=== Raid Session: {self.session_name} ===")
        print(f"Start time: {self.start_time}")
        print(f"Logs ({len(self.logs)}):")
        for log in self.logs:
            print("  ", log)
        print("====================================\n")
    
    def to_discord_message(self):
        lines = []
        lines.append(f"**{self.session_name}**")
        lines.append(f"Start: {self.start_time.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append(f"Logs ({len(self.log_links)}):")

        for link in self.log_links:
            lines.append(link)

        return "\n".join(lines)


# Log watcher
class ArcLogHandler(FileSystemEventHandler):
    def __init__(self, session_container):
        super().__init__()
        self.session_container = session_container

    # Only react to final log files
    def on_moved(self, event):
        if event.dest_path.endswith(".zevtc"):
            print("Final arcdps log detected:", event.dest_path)
            self.session_container["session"].add_log(event.dest_path)

def start_log_watcher(log_dir, session_container):
    observer = Observer()
    handler = ArcLogHandler(session_container)
    observer.schedule(handler, log_dir, recursive=True)
    observer.start()
    return observer

# GW2 detection
def is_gw2_running():
    for proc in psutil.process_iter(['name']):
        name = proc.info['name']
        if name and name.lower() == "gw2-64.exe":
            return True
    return False

def wait_for_gw2():
    print("Waiting for Guild Wars 2 to start...")
    while not is_gw2_running():
        time.sleep(5)
    print("GW2 detected!")

# Monitor GW2 with grace period
def monitor_with_grace():
    print("Monitoring GW2...")
    while True:
        if not is_gw2_running():
            print(f"GW2 closed. Waiting {GRACE_PERIOD} seconds for final logs...")
            time.sleep(GRACE_PERIOD)
            if not is_gw2_running():
                break
        time.sleep(1)

#Use webhook to post to discord
def post_to_discord(message: str) -> str | None:
    response = requests.post(
        DISCORD_WEBHOOK_URL + "?wait=true",
        json={"content": message},
        timeout=10
    )

    if response.status_code not in (200, 204):
        print("[Discord] Failed to post message:", response.text)
        return None

    data = response.json()
    message_id = data.get("id")

    if not message_id:
        print("[Discord] No message ID returned!")
        return None

    print("[Discord] Posted new session message.")
    return message_id
    
def edit_discord_message(message_id: str, message: str):
    response = requests.patch(
        f"{DISCORD_WEBHOOK_URL}/messages/{message_id}",
        json={"content": message},
        timeout=10
    )

    if response.status_code not in (200, 204):
        print("[Discord] Failed to edit message:", response.text)
    else:
        print("[Discord] Session message updated.")

def upload_log_to_dps_report(log_path: str) -> str | None:
    """
    Attempts to upload a .zevtc log to dps.report.

    Returns:
        permalink (str) if upload succeeded
        None if upload was rejected (duplicate combat data or error)
    """
    url = "https://dps.report/uploadContent"

    try:
        with open(log_path, "rb") as f:
            files = {"file": f}
            data = {"json": "1"}

            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=60,
                headers={"User-Agent": "GW2-Raid-Logger"}
            )

        # Duplicate combat data — acceptable, just no link
        if response.status_code == 422:
            print("[Upload] DPS.report rejected log (duplicate combat data).")
            return None

        if response.status_code != 200:
            print(f"[Upload] Failed ({response.status_code}) for {log_path}")
            print("[Upload] Response:", response.text)
            return None

        payload = response.json()
        permalink = payload.get("permalink")

        if not permalink:
            print("[Upload] No permalink returned:", payload)
            return None

        print(f"[Upload] Uploaded: {permalink}")
        return permalink

    except Exception as e:
        print(f"[Upload] Exception: {e}")
        return None

if __name__ == "__main__":
    wait_for_gw2()

    session_container = {"session": RaidSession("Guild Raid Night")}
    log_observer = start_log_watcher(LOG_DIR, session_container)

    try:
        while True:
            time.sleep(INACTIVITY_CHECK_INTERVAL)

            # Check inactivity
            if session_container["session"].has_inactivity(INACTIVITY_THRESHOLD_MINUTES):
                print("\n[Session] No new logs for threshold, ending session.")
                session_container["session"].summary()
                session_container["session"] = RaidSession("Guild Raid Night")

            # Check GW2 exit
            if not is_gw2_running():
                print(f"GW2 closed. Waiting {GRACE_PERIOD} seconds for final logs...")
                time.sleep(GRACE_PERIOD)
                if not is_gw2_running():
                    print("GW2 not running. Exiting main loop.")
                    break

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected.", flush=True)
    finally:
        print("Stopping log observer...", flush=True)
        log_observer.stop()
        log_observer.join()
        print("Tool shutting down.", flush=True)
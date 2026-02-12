from collections import defaultdict
from datetime import datetime, timedelta

from config import BOSS_CONTENT_MAP, is_raid_session, TRACKED_FAIL_BOSSES, get_core_member_count, CORE_COUNT_MINIMUM
from discord_utils import post_to_discord, edit_discord_message
from logger import setup_logger
from uploader import get_boss_name_from_log  # For folder-based boss name

logger = setup_logger()

class RaidSession:
    def __init__(self, name: str):
        self.name = name
        self.start_time = datetime.now()
        self.last_log_time = datetime.now()
        self.grouped_logs = defaultdict(lambda: defaultdict(list))
        self.display_links = defaultdict(dict)
        self.discord_message_id: str | None = None

    def add_log(self, log_path: str, upload_result: dict):
        # Add successful log to session if it meets criteria.
        self.last_log_time = datetime.now()
        if not upload_result:
            return

        players = upload_result.get("players", {})
        
        if not is_raid_session(players):
            core_count = get_core_member_count(players)   # Get the actual number for logging
            logger.info("[Session] Skipping log — insufficient core members (%d/%d) or not 10 players", core_count, CORE_COUNT_MINIMUM)
            return

        # Use folder-based boss name since we don't know what the API returns
        boss_name = get_boss_name_from_log(log_path)
        if boss_name not in BOSS_CONTENT_MAP:
            logger.info("[Session] Skipped non-raid boss '%s'", boss_name)
            return

        if not upload_result.get("success", False) and boss_name not in TRACKED_FAIL_BOSSES:
            logger.info("[Session] Skipping failed attempt: %s", boss_name)
            return

        wing, short_name, order = BOSS_CONTENT_MAP[boss_name]
        link = upload_result["permalink"]
        display_name = f"{short_name} CM" if upload_result.get("is_cm", False) else short_name

        self.grouped_logs[wing][short_name].append(link)
        if short_name not in self.display_links[wing]:
            self.display_links[wing][short_name] = []
        self.display_links[wing][short_name].append({
            'link': link,
            'order': order,
            'display_name': display_name
        })
        logger.info("[Session] Added successful %s (%s) to %s", boss_name, display_name, wing)

    def has_inactivity(self, threshold_minutes: int) -> bool:
        """Check if session is inactive."""
        return datetime.now() - self.last_log_time > timedelta(minutes=threshold_minutes)

    def to_discord_message(self) -> str:
        """Generate Discord message from session data."""
        lines = []
        
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
        """Post or update session to Discord if there are kills."""
        if not any(self.display_links.values()):
            logger.info("[Discord] Skipping post — session has no successful kills.")
            return
        message = self.to_discord_message()
        if self.discord_message_id is None:
            self.discord_message_id = post_to_discord(message)
            if self.discord_message_id:
                logger.info("[Discord] Session posted.")
        else:
            edit_discord_message(self.discord_message_id, message)
            logger.info("[Discord] Session updated.")

    def end_session(self):
        """End session and ensure final Discord update."""
        self.post_or_update_discord()
        logger.info("[Session] Session ended: %s", self.name)
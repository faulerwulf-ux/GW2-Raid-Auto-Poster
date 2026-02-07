import os
import requests

from config import BOSS_CONTENT_MAP  # For boss name check
from logger import setup_logger

logger = setup_logger()

def is_final_zevtc(path: str) -> bool:
    #Check if path is a final .zevtc log file.
    return path.endswith(".zevtc") and os.path.isfile(path)

def get_boss_name_from_log(log_path: str) -> str:
    #Extract boss name from log path.
    parent = os.path.basename(os.path.dirname(log_path))
    return parent.split("(", 1)[0].strip()

def upload_log_to_dps_report(log_path: str) -> dict | None:
    """
    Upload log to dps.report.
    
    Args:
        log_path (str): Path to .zevtc file.
    Returns:
        dict | None: Upload result or None on failure.
    """
    url = "https://b.dps.report/uploadContent"
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
        players = payload.get("players", {})
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
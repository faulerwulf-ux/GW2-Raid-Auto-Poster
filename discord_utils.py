import requests

from discord_webhook import DISCORD_WEBHOOK_URL
from logger import setup_logger

logger = setup_logger()

def post_to_discord(message: str) -> str | None:
    """
    Post message to Discord webhook.
    
    Args:
        message (str): Message to post.
    Returns:
        str | None: Message ID or None on failure.
    """
    response = requests.post(DISCORD_WEBHOOK_URL + "?wait=true", json={"content": message}, timeout=10)
    if response.status_code not in (200, 204):
        logger.warning("[Discord] Failed to post: %s", response.text)
        return None
    return response.json().get("id")

def edit_discord_message(message_id: str, message: str):
    """
    Edit existing Discord message.
    
    Args:
        message_id (str): ID of message to edit.
        message (str): New content.
    """
    response = requests.patch(f"{DISCORD_WEBHOOK_URL}/messages/{message_id}", json={"content": message}, timeout=10)
    if response.status_code not in (200, 204):
        logger.warning("[Discord] Failed to edit: %s", response.text)
# Central configuration for the raid tool. Edit constants here.

import os
from datetime import timedelta
from logger import setup_logger

# Logging
LOG_FOLDER = "logs"
MAX_LOGS = 3

# Paths and thresholds
LOG_DIR = r"C:\Users\deven\Documents\GUILD WARS 2\addons\arcdps\arcdps.cbtlogs"
INACTIVITY_THRESHOLD_MINUTES = 180
GW2_EXIT_GRACE_SECONDS = 30
CORE_COUNT_MINIMUM = 5

# Core members
CORE_MEMBERS = {
    "Piroko.1209",
    "Viven Alencia.9125",
    "Iota.4967",
    "OGSMOKE.2138",
    "Shirolk.5738",
    "Ketsueki.7190",
    "Raindrip.1653",
    "Aaron.2159",
    "Tzimisce.8347",
    "Mr Splendiferous.9782",
    "Natsukoko.7316",
    "Emi.4152",
    "Druwburt.7596",
    "Tillwad.7439",
    "sykloid.4092",
    "JMDhouse.7162",
    "fugepopers.2165",
    "Rytus.6985",
    "Sylo Johnson.4172"
}

# Boss content map
BOSS_CONTENT_MAP = {
    # Wing 1: Spirit Vale
    "Vale Guardian": ("Wing 1", "VG", 1),
    "Gorseval the Multifarious": ("Wing 1", "Gors", 2),
    "Sabetha the Saboteur": ("Wing 1", "Sabetha", 3),

    # Wing 2: Salvation Pass
    "Slothasor": ("Wing 2", "Sloth", 1),
    "Matthias Gabrel": ("Wing 2", "Matthias", 2),

    # Wing 3: Stronghold of the Faithful
    "Keep Construct": ("Wing 3", "KC", 1), 
    "Xera": ("Wing 3", "Xera", 2),

    # Wing 4: Bastion of the Penitent
    "Cairn the Indomitable": ("Wing 4", "Cairn", 1),  
    "Mursaat Overseer": ("Wing 4", "MO", 2),
    "Samarog": ("Wing 4", "Samarog", 3),
    "Deimos": ("Wing 4", "Deimos", 4),

    # Wing 5: Hall of Chains
    "Soulless Horror": ("Wing 5", "SH", 1),
    "Dhuum": ("Wing 5", "Dhuum", 2),

    # Wing 6: Mythwright Gambit
    "Conjured Amalgamate": ("Wing 6", "CA", 1),
    "Nikare": ("Wing 6", "Largos", 2),
    "Qadim": ("Wing 6", "Qadim", 3),

    # Wing 7: The Key of Ahdashim
    "Cardinal Adina": ("Wing 7", "Adina", 1),
    "Cardinal Sabir": ("Wing 7", "Sabir", 2),
    "Qadim the Peerless": ("Wing 7", "QTP", 3),

    # Wing 8: Mount Balrior
    "Greer, the Blightbringer": ("Wing 8", "Greer", 1),
    "Decima, the Stormsinger": ("Wing 8", "Decima", 2),
    "Ura": ("Wing 8", "Ura", 3),

    # Strikes - Icebrood Saga
    "Boneskinner": ("IBS Strikes", "Boneskinner", 1),
    "Whisper of Jormag": ("IBS Strikes", "Whisper", 2),
    "Fraenir of Jormag": ("IBS Strikes", "Fraenir", 3),
    "Voice of the Fallen": ("IBS Strikes", "Voice and Claw", 4),
    "Icebrood Construct": ("IBS Strikes", "Icebrood Construct", 5),

    # Strikes - End of Dragons
    "Captain Mai Trin": ("EoD Strikes", "Aetherblade", 1),
    "Ankka": ("EoD Strikes", "Junkyard", 2),
    "Minister Li": ("EoD Strikes", "KO", 3),
    "The Dragonvoid": ("EoD Strikes", "HT", 4),
    "Prototype Vermilion": ("EoD Strikes", "OLC", 5),

    # Strikes - Secrets of the Obscure
    "Dagda": ("Wing 8", "CO", 1), 
    "Cerus": ("SotO Strikes", "Febe", 2),

    # New encounter
    "Kela, Seneschal of Waves":("VoE", "Crab", 1),
    #"Standard Kitty Golem":("Golems", "Standard Kitty", 2),
    #"Medium Kitty Golem":("Golems", "Medium Kitty", 3),
    #"Large Kitty Golem":("Golems", "Large Kitty", 4),
}

# Bosses for which to track and include failed attempts.
# Use exact names from BOSS_CONTENT_MAP keys (e.g., "Cerus", "Qadim").
TRACKED_FAIL_BOSSES = {
    "Kela, Seneschal of Waves",
    "Deimos"
}

def is_raid_session(players: dict) -> bool:
    """
    Determine if a session should be included based on core members.
    
    Args:
        players (dict): DPS.report players dict.
    Returns:
        bool: True if >=5 core members and exactly 10 players.
    """
    if not isinstance(players, dict) or len(players) != 10:
        logger.info("[Session] Player count is not 10: %s", len(players))
        return False
    core_count = sum(1 for p in players.values() if p.get("display_name", "") in CORE_MEMBERS)
    logger = setup_logger()
    display_names = [p.get("display_name", "UNKNOWN") for p in players.values()]  # Use "UNKNOWN" for missing/empty
    logger.info("[Session] Player display_names: %s", display_names)
    logger.info("[Session] Core count: %s/%s", core_count, CORE_COUNT_MINIMUM)
    return core_count >= CORE_COUNT_MINIMUM

def get_core_member_count(players: dict) -> int:
    """
    Count core members in players dict.
    
    Args:
        players (dict): DPS.report players dict.
    Returns:
        int: Number of core members.
    """
    if not players:
        return 0
    return sum(1 for p in players.values() if p.get("display_name", "") in CORE_MEMBERS)

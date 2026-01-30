#!/usr/bin/env python3
"""
Raid Group Configuration

This file contains the configuration for raid group filtering.
Edit this file to add, remove, or modify group members.

Usage:
- Add player names to the CORE_MEMBERS list
- All members in this list can be raid commanders
- The scoring system will use this list to filter raid sessions
"""

# Core group members (including raid commanders)
# Add/remove player names here as needed
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

def is_raid_session(players: dict) -> bool:
    """
    Determine if a session should be included based on core members.

    Args:
        players (dict): Dictionary of DPS.report player objects
                        Keys are character names,
                        values are dicts with fields like 'display_name'
    Returns:
        bool: True if session meets raid criteria, False otherwise
    """
    if not isinstance(players, dict) or not players:
        return False

    # Must have exactly 10 players
    if len(players) != 10:
        return False

    # Count core members using display_name (account names only)
    core_count = 0
    for _, player in players.items():
        account_name = player.get("display_name", "")
        if account_name in CORE_MEMBERS:
            core_count += 1

    return core_count >= 5



def get_core_member_count(player_dict):
    """Get count of core members in the session."""
    if not player_dict:
        return 0
    
    core_count = 0
    for character_name, player in player_dict.items():
        if isinstance(player, dict):
            # Try display_name first (account name), then character_name
            account_name = player.get("display_name", "")
            if not account_name:
                account_name = player.get("character_name", "")
            
            if account_name in CORE_MEMBERS:
                core_count += 1
        else:
            # This should not happen if DPS.report always returns dicts
            # But if it does, log it as a bug
            print(f"[Filtering] Unexpected player format: {player}")
    
    return core_count


if __name__ == "__main__":
    # Example usage and testing
    print("Raid Group Configuration")
    print(f"Core members: {len(CORE_MEMBERS)}")
    
    # Example test
    test_players = ["Player1", "Player2", "Player3", "Player4", "Player5", 
                   "Random1", "Random2", "Random3", "Random4", "Random5"]
    
    core_count = get_core_member_count(test_players)
    is_raid = is_raid_session(test_players)
    
    print(f"\nTest session core members: {core_count}/5")
    print(f"Is raid session: {is_raid}")

# test_session_filter.py
from collections import defaultdict

# Import your code
from content_map import BOSS_CONTENT_MAP
from raid_group_config import CORE_MEMBERS, is_raid_session
from main import RaidSession


# --------------------------
# Simulated DPS.report uploads
# --------------------------

def make_fake_upload(boss_name, core_members_included, total_players=10):
    """
    Simulate a DPS.report upload result.

    boss_name: str, must exist in BOSS_CONTENT_MAP
    core_members_included: list of account names from CORE_MEMBERS
    total_players: int, default 10
    """
    # Fill remaining slots with dummy random players
    random_players = [f"Random{i}.0000" for i in range(total_players - len(core_members_included))]

    players = {}

    # Add core members
    for i, acct in enumerate(core_members_included):
        char_name = f"CoreChar{i}"
        players[char_name] = {"display_name": acct, "character_name": char_name}

    # Add random members
    for i, acct in enumerate(random_players):
        char_name = f"RandomChar{i}"
        players[char_name] = {"display_name": acct, "character_name": char_name}

    # Simulate upload result dict
    return {
        "permalink": f"https://dps.report/test/{boss_name.replace(' ', '_')}",
        "success": True,
        "boss_name": boss_name,
        "player_count": total_players,
        "is_cm": False,
        "players": players
    }


# --------------------------
# Test function
# --------------------------

def test_session():
    session = RaidSession("Test Raid Night")

    core_members_list = list(CORE_MEMBERS)  # Convert set to list for slicing

    # Test bosses with different core member counts
    test_cases = [
        ("Vale Guardian", core_members_list[:5]),    # exactly 5 core members -> should pass
        ("Gorseval the Multifarious", core_members_list[:4]),  # 4 core members -> should skip
        ("Sabetha the Saboteur", core_members_list[:7]),  # 7 core members -> should pass
    ]

    for boss_name, core_members in test_cases:
        upload_result = make_fake_upload(boss_name, core_members)
        players = upload_result["players"]

        if is_raid_session(players):
            print(f"[TEST] Log for {boss_name} accepted (core members: {len(core_members)})")

            # Simulate adding log to session (like RaidSession.add_log)
            wing, short_name, order = BOSS_CONTENT_MAP[boss_name]
            link = upload_result["permalink"]
            display_name = short_name  # No CM in this test

            # Initialize wing if needed
            if wing not in session.display_links:
                session.display_links[wing] = {}

            # Initialize boss if needed
            if short_name not in session.display_links[wing]:
                session.display_links[wing][short_name] = []

            # Append log
            session.display_links[wing][short_name].append({
                "link": link,
                "order": order,
                "display_name": display_name
            })
        else:
            print(f"[TEST] Log for {boss_name} skipped (core members: {len(core_members)})")

    # --------------------------
    # Print out grouped logs
    # --------------------------
    print("\n=== Grouped Logs ===")
    for wing, bosses in session.display_links.items():
        print(f"{wing}:")
        for short_name, boss_data_list in bosses.items():
            for data in boss_data_list:
                print(f"  {data['display_name']}: {data['link']}")


if __name__ == "__main__":
    test_session()

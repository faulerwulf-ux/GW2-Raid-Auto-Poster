# test_session_lifecycle_mock.py
import time
from content_map import BOSS_CONTENT_MAP
from raid_group_config import CORE_MEMBERS, is_raid_session
from main import RaidSession

# --------------------------
# Fake log upload simulation
# --------------------------
def make_fake_upload(boss_name, core_members_included, total_players=10):
    """
    Simulate a DPS.report upload result.
    """
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

    return {
        "permalink": f"https://dps.report/test/{boss_name.replace(' ', '_')}",
        "success": True,
        "boss_name": boss_name,
        "player_count": total_players,
        "is_cm": False,
        "players": players
    }

# --------------------------
# Mock Discord posting
# --------------------------
def mock_post_or_update_discord(session):
    print("\n[Discord Message Updated]")
    print(session.to_discord_message())
    print("------------------------")

# --------------------------
# Test simulation
# --------------------------
def test_session_lifecycle():
    session_ref = {"current_session": None}

    # Sequence of fake logs: (boss_name, number of core members, wait_seconds)
    log_sequence = [
        ("Vale Guardian", 5, 0),     # first valid log -> starts session
        ("Gorseval the Multifarious", 4, 1),  # skipped
        ("Sabetha the Saboteur", 7, 2),       # added to session
        ("Slothasor", 6, 1),        # added to session
    ]

    # Use very short inactivity threshold for testing (~3 seconds)
    INACTIVITY_THRESHOLD_MINUTES = 0.05

    print("[TEST] Starting session lifecycle test...\n")

    for boss_name, core_count, wait_seconds in log_sequence:
        time.sleep(wait_seconds)
        upload_result = make_fake_upload(boss_name, list(CORE_MEMBERS)[:core_count])
        players = upload_result["players"]

        if is_raid_session(players):
            # Start session if none exists
            if session_ref["current_session"] is None:
                session_ref["current_session"] = RaidSession("Test Raid Night")
                print(f"[Session] Starting new session due to log: {boss_name}")

            # --------------------------
            # Simulate add_log WITHOUT reading a file
            # --------------------------
            current_session = session_ref["current_session"]
            wing, short_name, order = BOSS_CONTENT_MAP[boss_name]
            link = upload_result["permalink"]
            display_name = short_name

            # Initialize wing/boss if needed
            if wing not in current_session.display_links:
                current_session.display_links[wing] = {}
            if short_name not in current_session.display_links[wing]:
                current_session.display_links[wing][short_name] = []

            # Append log
            current_session.display_links[wing][short_name].append({
                "link": link,
                "order": order,
                "display_name": display_name
            })

            # Update Discord
            mock_post_or_update_discord(current_session)

        else:
            print(f"[Session] Log skipped (not enough core members): {boss_name}")

        # Check inactivity after each log
        current_session = session_ref.get("current_session")
        if current_session and current_session.has_inactivity(INACTIVITY_THRESHOLD_MINUTES):
            print("[Session] Ending session due to inactivity.")
            mock_post_or_update_discord(current_session)
            session_ref["current_session"] = None

    # Final check at end
    current_session = session_ref.get("current_session")
    if current_session:
        print("[Session] Final session ending at test end.")
        mock_post_or_update_discord(current_session)
        session_ref["current_session"] = None

    print("\n[TEST] Session lifecycle test complete.")


if __name__ == "__main__":
    test_session_lifecycle()

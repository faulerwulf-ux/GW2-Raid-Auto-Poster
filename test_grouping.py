#!/usr/bin/env python3
"""
Unit test for URL grouping functionality.
Tests the RaidSession class without running GW2 or uploading real logs.
"""

from main import RaidSession

def test_url_grouping():
    print("Testing URL Grouping Functionality")
    print("=" * 50)

    # Create a test session
    session = RaidSession("Test Raid Session")

    # Simulate adding various boss logs (what add_log() would do)
    print("Adding test logs...")

    # Wing 1 - Normal progression
    session.display_links["Wing 1"]["VG"] = {'link': 'https://dps.report/test-vg-001', 'order': 1}
    session.display_links["Wing 1"]["Gors"] = {'link': 'https://dps.report/test-gors-002', 'order': 2}
    session.display_links["Wing 1"]["Sabetha"] = {'link': 'https://dps.report/test-sab-003', 'order': 3}

    # Wing 2 - Mixed normal and CM
    session.display_links["Wing 2"]["Sloth"] = {'link': 'https://dps.report/test-sloth-004', 'order': 1}
    session.display_links["Wing 2"]["Trio"] = {'link': 'https://dps.report/test-trio-005', 'order': 2}
    session.display_links["Wing 2"]["Matthias"] = {'link': 'https://dps.report/test-matt-006', 'order': 3}

    # Wing 4 - Normal and CM mixed (CM variants should appear right after normal)
    session.display_links["Wing 4"]["Cairn"] = {'link': 'https://dps.report/test-cairn-007', 'order': 1}
    session.display_links["Wing 4"]["Cairn CM"] = {'link': 'https://dps.report/test-cairn-cm-008', 'order': 2}
    session.display_links["Wing 4"]["MO"] = {'link': 'https://dps.report/test-mo-009', 'order': 3}
    session.display_links["Wing 4"]["Samarog"] = {'link': 'https://dps.report/test-sam-010', 'order': 5}
    session.display_links["Wing 4"]["Samarog CM"] = {'link': 'https://dps.report/test-sam-cm-011', 'order': 6}
    session.display_links["Wing 4"]["Deimos"] = {'link': 'https://dps.report/test-dei-012', 'order': 7}

    # Strikes - Should appear after wings
    session.display_links["EoD Strikes"]["Aetherblade"] = {'link': 'https://dps.report/test-aether-013', 'order': 1}
    session.display_links["EoD Strikes"]["Junkyard"] = {'link': 'https://dps.report/test-junk-014', 'order': 3}
    session.display_links["EoD Strikes"]["Aetherblade CM"] = {'link': 'https://dps.report/test-aether-cm-015', 'order': 2}

    print("Added test logs")
    print()

    # Generate the Discord message
    message = session.to_discord_message()

    print("Generated Discord Message:")
    print("-" * 30)
    print(message)
    print("-" * 30)

    # Verify the output structure
    lines = message.split('\n')
    print("Verification:")

    # Check session title
    assert lines[0] == "Test Raid Session", f"Expected 'Test Raid Session', got '{lines[0]}'"
    assert lines[1] == "", f"Expected empty line, got '{lines[1]}'"

    # Check Wing 1 appears first
    wing1_index = next(i for i, line in enumerate(lines) if "Wing 1:" in line)
    assert wing1_index > 1, "Wing 1 should appear after title"

    # Check VG appears before Gors
    vg_line = next(line for line in lines if line.startswith("VG:"))
    gors_line = next(line for line in lines if line.startswith("Gors:"))
    assert lines.index(vg_line) < lines.index(gors_line), "VG should appear before Gors"

    # Check variants are grouped (Cairn CM right after Cairn)
    cairn_line = next(line for line in lines if line.startswith("Cairn:"))
    cairn_cm_line = next(line for line in lines if line.startswith("Cairn CM:"))
    assert abs(lines.index(cairn_line) - lines.index(cairn_cm_line)) == 1, "Cairn variants should be adjacent"

    print("All grouping tests passed!")
    print()

    # Test posting and editing like a real raid session
    print("Testing Discord posting and editing like real raid session...")

    from main import post_to_discord, edit_discord_message

    # Step 1: Post initial message with just Wing 1 (simulating early raid)
    initial_session = RaidSession("Test Raid Session")
    initial_session.display_links["Wing 1"]["VG"] = {'link': 'https://dps.report/test-vg-001', 'order': 1}
    initial_session.display_links["Wing 1"]["Gors"] = {'link': 'https://dps.report/test-gors-002', 'order': 2}

    initial_message = initial_session.to_discord_message()
    print("Initial message to post:")
    print(initial_message)
    print("-" * 40)

    message_id = post_to_discord(initial_message)

    if message_id:
        print(f"Posted initial message to Discord! Message ID: {message_id}")
        print("Check Discord - should show only Wing 1 with VG and Gors")
        print()

        # Step 2: Simulate more bosses being defeated - add wings OUT OF ORDER to test sorting
        print("Simulating more bosses defeated - adding Wing 4 first, then Wing 2 (out of order)...")
        # Add Wing 4 first (should appear later in sorted output)
        session.display_links["Wing 4"]["Cairn"] = {'link': 'https://dps.report/test-cairn-007', 'order': 1}
        session.display_links["Wing 4"]["Cairn CM"] = {'link': 'https://dps.report/test-cairn-cm-008', 'order': 2}

        # Then add Wing 2 (should appear earlier in sorted output despite being added later)
        session.display_links["Wing 2"]["Sloth"] = {'link': 'https://dps.report/test-sloth-004', 'order': 1}
        session.display_links["Wing 2"]["Trio"] = {'link': 'https://dps.report/test-trio-005', 'order': 2}
        session.display_links["Wing 2"]["Matthias"] = {'link': 'https://dps.report/test-matt-006', 'order': 3}

        # Step 3: Edit the message with updated content
        print("Editing Discord message with additional wings...")
        updated_message = session.to_discord_message()

        print("Updated message:")
        print(updated_message)
        print("-" * 40)

        if edit_discord_message(message_id, updated_message) is None:
            print("Successfully edited the Discord message!")
            print("Check Discord - should now show Wing 1, Wing 2, AND Wing 4 in correct order")
            print("Verify that Wing 4 appears AFTER Wing 2, not appended at bottom")
        else:
            print("Failed to edit Discord message")

    else:
        print("Failed to post to Discord - check your webhook URL")

    print()
    print("Real raid session simulation complete!")

if __name__ == "__main__":
    test_url_grouping()

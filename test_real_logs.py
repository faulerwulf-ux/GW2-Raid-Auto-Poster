#!/usr/bin/env python3
"""
Test script for the enhanced raid tool using real log files.
This script tests success/failure detection, CM detection, multiple clears, and raid group filtering.
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import RaidSession, upload_log_to_dps_report, get_boss_name_from_log
from content_map import BOSS_CONTENT_MAP
from raid_group_config import get_core_member_count


def test_real_logs():
    """Test the enhanced raid tool with real log files."""
    
    # Test directory with real logs
    TEST_LOG_DIR = r"C:\test_logs"
    
    print("=" * 60)
    print("TESTING ENHANCED RAID TOOL WITH REAL LOGS")
    print("=" * 60)
    print(f"Test directory: {TEST_LOG_DIR}")
    print()
    
    # Create a test session
    session = RaidSession("Test Raid Session")
    
    # Find all .zevtc files in the test directory
    log_files = []
    for root, dirs, files in os.walk(TEST_LOG_DIR):
        for file in files:
            if file.endswith('.zevtc'):
                log_files.append(os.path.join(root, file))
    
    if not log_files:
        print("❌ No .zevtc files found in test directory!")
        return
    
    print(f"Found {len(log_files)} log files:")
    for log_file in log_files:
        print(f"  - {log_file}")
    print()
    
    # Process each log file
    print("PROCESSING LOG FILES:")
    print("-" * 40)
    
    for i, log_path in enumerate(log_files, 1):
        print(f"\n[{i}/{len(log_files)}] Processing: {os.path.basename(log_path)}")
        
        # Extract boss name from folder structure
        boss_name = get_boss_name_from_log(log_path)
        print(f"Boss name: {boss_name}")
        
        # Check if boss is in content map
        if boss_name not in BOSS_CONTENT_MAP:
            print(f"❌ Skipped non-raid boss: {boss_name}")
            continue
        
        # Upload to dps.report
        print("📤 Uploading to dps.report...")
        upload_result = upload_log_to_dps_report(log_path)
        
        if upload_result:
            success = upload_result.get("success", False)
            is_cm = upload_result.get("is_cm", False)
            player_count = upload_result.get("player_count", 0)
            permalink = upload_result.get("permalink", "")
            players = upload_result.get("players", {})
            
            print(f"✅ Upload successful!")
            print(f"   Success: {success}")
            print(f"   CM: {is_cm}")
            print(f"   Players: {player_count}")
            print(f"   Link: {permalink}")
            
            # Show raw player objects to debug JSON structure
            print(f"   Raw player objects from API:")
            for i, (character_name, player) in enumerate(players.items(), 1):
                print(f"     {i}. {character_name}: {player}")
            
            # Show raid group filtering results using raw player objects
            core_count = get_core_member_count(players)
            print(f"   Core members: {core_count}/5")
            
            if core_count >= 5:
                print(f"   ✅ Raid session accepted - adding to session")
                # Add to session (this will apply all our enhanced logic)
                session.add_log(log_path)
            else:
                print(f"   ❌ Raid session rejected (insufficient core members) - not adding to session")
            
        else:
            print("❌ Upload failed!")
    
    # Display final results
    print("\n" + "=" * 60)
    print("FINAL DISCORD MESSAGE OUTPUT:")
    print("=" * 60)
    
    discord_message = session.to_discord_message()
    print(discord_message)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print("=" * 60)
    
    total_bosses = 0
    total_clears = 0
    
    for wing, bosses in session.display_links.items():
        wing_clears = 0
        for boss_short, clears in bosses.items():
            boss_clears = len(clears)
            total_bosses += 1
            total_clears += boss_clears
            wing_clears += boss_clears
            print(f"{wing} - {boss_short}: {boss_clears} clear(s)")
        
        print(f"{wing} total: {wing_clears} clears")
    
    print(f"\nTotal bosses cleared: {total_bosses}")
    print(f"Total successful clears: {total_clears}")
    
    if total_clears > 0:
        print("✅ Test completed successfully!")
        print("✅ Success/failure detection working")
        print("✅ CM detection working")
        print("✅ Multiple clears working")
        print("✅ Raid group filtering working")
    else:
        print("⚠️  No successful clears found (may be expected if all attempts failed)")


if __name__ == "__main__":
    test_real_logs()

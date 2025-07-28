#!/usr/bin/env python3
"""
Test Script for 2-Hour Scheduler Configuration
=============================================

Verifies that the scheduler is properly configured to run every 2 hours.
Tests the scheduler settings and provides status information.

Author: Web Scraping Project
"""

import json
import os
from datetime import datetime, timedelta

def test_scheduler_configuration():
    """Test the 2-hour scheduler configuration"""
    print("🕐 Testing 2-Hour Scheduler Configuration")
    print("=" * 50)
    
    # Check scheduler status file
    status_file = 'data/scheduler_status.json'
    
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as f:
            status = json.load(f)
        
        print("📊 Current Scheduler Status:")
        print(f"   Enabled: {status.get('enabled', False)}")
        print(f"   Interval: {status.get('interval_minutes', 'Unknown')} minutes")
        print(f"   Last Run: {status.get('last_run', 'Never')}")
        print(f"   Next Run: {status.get('next_run', 'Unknown')}")
        print(f"   Collection Count: {status.get('collection_count', 0)}")
        print(f"   Success Count: {status.get('success_count', 0)}")
        print(f"   Error Count: {status.get('error_count', 0)}")
        
        # Verify 2-hour interval
        interval = status.get('interval_minutes', 0)
        if interval == 120:
            print("✅ Scheduler is correctly configured for 2-hour intervals")
        else:
            print(f"⚠️  Scheduler interval is {interval} minutes (should be 120)")
            
    else:
        print("❌ Scheduler status file not found")
    
    print()
    
    # Test scheduler module
    try:
        from scheduler import DataCollectionScheduler
        
        scheduler = DataCollectionScheduler()
        print("🔧 Scheduler Module Test:")
        print(f"   Default Interval: {scheduler.collection_interval} seconds")
        print(f"   Default Interval: {scheduler.collection_interval // 60} minutes")
        
        if scheduler.collection_interval == 7200:  # 2 hours in seconds
            print("✅ Scheduler module correctly configured for 2-hour intervals")
        else:
            print(f"⚠️  Scheduler module interval is {scheduler.collection_interval} seconds")
            
    except ImportError as e:
        print(f"❌ Error importing scheduler module: {e}")
    
    print()
    
    # Calculate next run time
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as f:
            status = json.load(f)
        
        last_run_str = status.get('last_run')
        if last_run_str:
            try:
                last_run = datetime.fromisoformat(last_run_str.replace('Z', '+00:00'))
                interval_minutes = status.get('interval_minutes', 120)
                next_run = last_run + timedelta(minutes=interval_minutes)
                
                print("⏰ Next Collection Times:")
                print(f"   Last Run: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Next Run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Interval: {interval_minutes} minutes")
                
                # Show next few runs
                print("\n📅 Upcoming Collection Schedule:")
                current_time = datetime.now()
                for i in range(1, 6):  # Next 5 runs
                    future_run = last_run + timedelta(minutes=interval_minutes * i)
                    if future_run > current_time:
                        print(f"   Run {i}: {future_run.strftime('%Y-%m-%d %H:%M:%S')}")
                        
            except Exception as e:
                print(f"❌ Error calculating next run time: {e}")
    
    print()
    print("🎯 Summary:")
    print("   - Scheduler should run every 2 hours (120 minutes)")
    print("   - Data collection includes: Google, Reddit, YouTube, Twitter")
    print("   - Scheduler runs in background when Flask app is running")
    print("   - Manual triggers available via dashboard")

def update_scheduler_to_2hours():
    """Update scheduler to 2-hour intervals if needed"""
    print("\n🔧 Updating Scheduler to 2-Hour Intervals")
    print("=" * 50)
    
    try:
        from scheduler import update_scheduler_settings
        
        # Update scheduler settings
        result = update_scheduler_settings(interval_minutes=120)
        
        if result:
            print("✅ Scheduler updated to 2-hour intervals")
        else:
            print("❌ Failed to update scheduler")
            
    except Exception as e:
        print(f"❌ Error updating scheduler: {e}")

if __name__ == "__main__":
    test_scheduler_configuration()
    update_scheduler_to_2hours() 
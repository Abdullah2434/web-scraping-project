"""
Fix Scheduler Settings
=====================

Fix the scheduler to run every 2 minutes instead of 2 hours
and ensure it starts automatically.
"""

import os
import json
from datetime import datetime
from scheduler import scheduler, start_scheduler, get_scheduler_status

def fix_scheduler_settings():
    """Fix scheduler settings to run every 2 minutes"""
    
    print("🔧 Fixing scheduler settings...")
    
    # Update scheduler settings
    scheduler.update_settings(
        enabled=True,
        interval_minutes=2,  # Change from 120 to 2 minutes
        sources=['upwork']  # Focus on Upwork for now
    )
    
    print("✅ Scheduler settings updated:")
    print("   - Interval: 2 minutes")
    print("   - Enabled: True")
    print("   - Sources: ['upwork']")
    
    # Start the scheduler
    print("\n🚀 Starting scheduler...")
    start_scheduler()
    
    # Get current status
    status = get_scheduler_status()
    print(f"\n📊 Scheduler Status:")
    print(f"   - Running: {status.get('is_running', False)}")
    print(f"   - Enabled: {status.get('enabled', False)}")
    print(f"   - Interval: {status.get('interval_minutes', 120)} minutes")
    print(f"   - Next run in: {status.get('time_until_next_minutes', 0)} minutes")
    
    return True

def test_scheduler_manual():
    """Test the scheduler manually"""
    
    print("\n🧪 Testing scheduler manually...")
    
    # Trigger immediate collection
    from scheduler import trigger_immediate_collection
    success = trigger_immediate_collection()
    
    if success:
        print("✅ Manual collection triggered successfully!")
        print("📊 Check your Google Sheets for new jobs")
    else:
        print("❌ Manual collection failed")
    
    return success

if __name__ == "__main__":
    print("🔧 Scheduler Configuration Fix")
    print("=" * 50)
    
    # Fix settings
    fix_scheduler_settings()
    
    # Test manual collection
    test_scheduler_manual()
    
    print("\n🎉 Scheduler configuration complete!")
    print("📋 What happens now:")
    print("   - Scheduler runs every 2 minutes")
    print("   - Automatic Upwork job collection")
    print("   - Jobs added to Google Sheets")
    print("   - Check status at: http://localhost:8080/settings") 
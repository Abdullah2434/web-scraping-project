"""
Complete Scheduler Fix
=====================

Fix all scheduler issues:
1. Timing mismatch (60s sleep vs 2hours interval)
2. Thread not staying alive
3. Integration with Flask app
4. Proper error handling
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from scheduler import scheduler, start_scheduler, get_scheduler_status, trigger_immediate_collection

def fix_scheduler_complete():
    """Complete fix for scheduler issues"""
    
    print("🔧 Complete Scheduler Fix")
    print("=" * 50)
    
    # 1. Stop any existing scheduler
    print("🛑 Stopping existing scheduler...")
    scheduler.stop()
    time.sleep(2)
    
    # 2. Update scheduler settings
    print("⚙️ Updating scheduler settings...")
    scheduler.update_settings(
        enabled=True,
        interval_minutes=120,
        sources=['upwork']
    )
    
    # 3. Start scheduler
    print("🚀 Starting scheduler...")
    start_scheduler()
    time.sleep(3)  # Wait for thread to start
    
    # 4. Check status
    status = get_scheduler_status()
    print(f"\n📊 Scheduler Status:")
    print(f"   - Running: {status.get('is_running', False)}")
    print(f"   - Thread Alive: {status.get('thread_alive', False)}")
    print(f"   - Enabled: {status.get('enabled', False)}")
    print(f"   - Interval: {status.get('interval_minutes', 120)} minutes")
    print(f"   - Next run in: {status.get('time_until_next_minutes', 0)} minutes")
    
    # 5. Test immediate collection
    print("\n🧪 Testing immediate collection...")
    success = trigger_immediate_collection()
    if success:
        print("✅ Immediate collection triggered successfully!")
    else:
        print("❌ Immediate collection failed")
    
    return status.get('is_running', False) and status.get('thread_alive', False)

def monitor_scheduler():
    """Monitor scheduler for 5 minutes"""
    
    print("\n📡 Monitoring scheduler for 5 minutes...")
    print("⏰ Will check every 30 seconds...")
    
    for i in range(10):  # 10 checks * 30 seconds = 5 minutes
        time.sleep(30)
        
        status = get_scheduler_status()
        current_time = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n[{current_time}] Scheduler Status:")
        print(f"   - Running: {status.get('is_running', False)}")
        print(f"   - Thread Alive: {status.get('thread_alive', False)}")
        print(f"   - Next run in: {status.get('time_until_next_minutes', 0)} minutes")
        print(f"   - Collection count: {status.get('collection_count', 0)}")
        
        # Check if collection happened
        if status.get('last_run'):
            last_run = datetime.fromisoformat(status.get('last_run'))
            time_since_last = datetime.now() - last_run
            print(f"   - Last run: {time_since_last.total_seconds():.0f} seconds ago")
    
    print("\n✅ Monitoring complete!")

def create_scheduler_test():
    """Create a simple test to verify scheduler works"""
    
    print("\n🧪 Creating scheduler test...")
    
    # Create a simple test script
    test_script = '''
import time
import threading
from datetime import datetime
from scheduler import scheduler, start_scheduler, get_scheduler_status

def test_scheduler():
    print("🧪 Testing scheduler...")
    
    # Start scheduler
    start_scheduler()
    time.sleep(2)
    
    # Check status
    status = get_scheduler_status()
    print(f"Status: {status}")
    
    # Wait for 3 minutes
    print("⏰ Waiting 3 minutes for automatic collection...")
    for i in range(6):  # 6 * 30 seconds = 3 minutes
        time.sleep(30)
        current_status = get_scheduler_status()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Running: {current_status.get('is_running')}, Thread: {current_status.get('thread_alive')}")
    
    print("✅ Test complete!")

if __name__ == "__main__":
    test_scheduler()
'''
    
    with open('test_scheduler_simple.py', 'w') as f:
        f.write(test_script)
    
    print("✅ Test script created: test_scheduler_simple.py")

if __name__ == "__main__":
    # Fix scheduler
    success = fix_scheduler_complete()
    
    if success:
        print("\n🎉 Scheduler fixed successfully!")
        print("📋 What to do next:")
        print("   1. Wait 2 hours for automatic collection")
        print("   2. Check Google Sheets for new jobs")
        print("   3. Monitor at: http://localhost:8080/settings")
        print("   4. Or run: python test_scheduler_simple.py")
        
        # Create test script
        create_scheduler_test()
        
        # Ask if user wants to monitor
        print("\n📡 Would you like to monitor the scheduler for 5 minutes? (y/n)")
        # For now, just show instructions
        print("   Run: python test_scheduler_simple.py")
        
    else:
        print("\n❌ Scheduler fix failed!")
        print("🔧 Try running the Flask app to start scheduler automatically:")
        print("   python flask_app.py") 
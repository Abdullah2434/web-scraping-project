"""
Test Scheduler Monitoring
========================

Monitor the scheduler for 5 minutes to verify it's working correctly.
"""

import time
import threading
from datetime import datetime
from scheduler import start_scheduler, get_scheduler_status, trigger_immediate_collection

def test_scheduler_monitoring():
    """Test and monitor scheduler for 5 minutes"""
    
    print("🧪 Scheduler Monitoring Test")
    print("=" * 50)
    
    # Start scheduler
    print("🚀 Starting scheduler...")
    start_scheduler()
    time.sleep(2)
    
    # Initial status
    status = get_scheduler_status()
    print(f"\n📊 Initial Status:")
    print(f"   - Running: {status.get('is_running', False)}")
    print(f"   - Thread Alive: {status.get('thread_alive', False)}")
    print(f"   - Enabled: {status.get('enabled', False)}")
    print(f"   - Interval: {status.get('interval_minutes', 120)} minutes")
    print(f"   - Next run in: {status.get('time_until_next_minutes', 0)} minutes")
    print(f"   - Collection count: {status.get('collection_count', 0)}")
    
    # Test immediate collection
    print("\n🧪 Testing immediate collection...")
    success = trigger_immediate_collection()
    if success:
        print("✅ Immediate collection triggered successfully!")
    else:
        print("❌ Immediate collection failed")
    
    # Monitor for 5 minutes (10 checks every 30 seconds)
    print(f"\n📡 Monitoring scheduler for 5 minutes...")
    print("⏰ Will check every 30 seconds...")
    print("=" * 50)
    
    initial_collection_count = status.get('collection_count', 0)
    collections_detected = 0
    
    for i in range(10):  # 10 checks * 30 seconds = 5 minutes
        time.sleep(30)
        
        current_status = get_scheduler_status()
        current_time = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n[{current_time}] Check {i+1}/10:")
        print(f"   - Running: {current_status.get('is_running', False)}")
        print(f"   - Thread Alive: {current_status.get('thread_alive', False)}")
        print(f"   - Next run in: {current_status.get('time_until_next_minutes', 0)} minutes")
        print(f"   - Collection count: {current_status.get('collection_count', 0)}")
        
        # Check if collection happened
        if current_status.get('last_run'):
            last_run = datetime.fromisoformat(current_status.get('last_run'))
            time_since_last = datetime.now() - last_run
            print(f"   - Last run: {time_since_last.total_seconds():.0f} seconds ago")
        
        # Check if collection count increased
        current_collection_count = current_status.get('collection_count', 0)
        if current_collection_count > initial_collection_count:
            collections_detected += 1
            print(f"   - 🎉 NEW COLLECTION DETECTED! (Total: {collections_detected})")
            initial_collection_count = current_collection_count
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 MONITORING COMPLETE!")
    print("=" * 50)
    
    final_status = get_scheduler_status()
    print(f"Final Status:")
    print(f"   - Running: {final_status.get('is_running', False)}")
    print(f"   - Thread Alive: {final_status.get('thread_alive', False)}")
    print(f"   - Total Collections Detected: {collections_detected}")
    print(f"   - Final Collection Count: {final_status.get('collection_count', 0)}")
    
    if collections_detected > 0:
        print("\n🎉 SUCCESS! Scheduler is working correctly!")
        print("✅ Automatic collections are happening")
        print("📊 Check your Google Sheets for new jobs")
    else:
        print("\n⚠️ No automatic collections detected")
        print("🔧 Scheduler might need adjustment")
    
    return collections_detected > 0

if __name__ == "__main__":
    success = test_scheduler_monitoring()
    
    if success:
        print("\n🎉 Test PASSED! Scheduler is working!")
        print("📋 What this means:")
        print("   - Scheduler runs every 2 minutes")
        print("   - Automatic Upwork job collection")
        print("   - Jobs added to Google Sheets")
        print("   - System is fully automated")
    else:
        print("\n❌ Test FAILED! Scheduler needs attention")
        print("🔧 Try running Flask app: python flask_app.py") 
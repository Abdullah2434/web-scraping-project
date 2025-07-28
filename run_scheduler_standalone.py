"""
Standalone Scheduler Runner
==========================

Run the scheduler independently to ensure it works properly.
"""

import time
import threading
from datetime import datetime
from scheduler import start_scheduler, get_scheduler_status, trigger_immediate_collection

def run_scheduler_standalone():
    """Run scheduler standalone"""
    
    print("🚀 Starting Standalone Scheduler")
    print("=" * 50)
    
    # Start scheduler
    start_scheduler()
    time.sleep(2)
    
    # Check initial status
    status = get_scheduler_status()
    print(f"📊 Initial Status:")
    print(f"   - Running: {status.get('is_running', False)}")
    print(f"   - Thread Alive: {status.get('thread_alive', False)}")
    print(f"   - Enabled: {status.get('enabled', False)}")
    print(f"   - Interval: {status.get('interval_minutes', 120)} minutes")
    print(f"   - Next run in: {status.get('time_until_next_minutes', 0)} minutes")
    
    # Trigger immediate collection
    print("\n🧪 Triggering immediate collection...")
    success = trigger_immediate_collection()
    if success:
        print("✅ Immediate collection triggered!")
    else:
        print("❌ Immediate collection failed")
    
    print("\n⏰ Scheduler is now running...")
    print("📋 Will collect data every 2 hours")
    print("🌐 Flask app available at: http://localhost:8080")
    print("📊 Check Google Sheets for new jobs")
    print("\nPress Ctrl+C to stop...")
    
    # Keep running
    try:
        while True:
            time.sleep(30)  # Check every 30 seconds
            
            current_status = get_scheduler_status()
            current_time = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n[{current_time}] Status Check:")
            print(f"   - Running: {current_status.get('is_running', False)}")
            print(f"   - Thread Alive: {current_status.get('thread_alive', False)}")
            print(f"   - Next run in: {current_status.get('time_until_next_minutes', 0)} minutes")
            print(f"   - Collection count: {current_status.get('collection_count', 0)}")
            
            if current_status.get('last_run'):
                last_run = datetime.fromisoformat(current_status.get('last_run'))
                time_since_last = datetime.now() - last_run
                print(f"   - Last run: {time_since_last.total_seconds():.0f} seconds ago")
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping scheduler...")
        from scheduler import stop_scheduler
        stop_scheduler()
        print("✅ Scheduler stopped")

if __name__ == "__main__":
    run_scheduler_standalone() 
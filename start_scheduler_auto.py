"""
Auto-Start Scheduler Script
==========================

This script ensures the scheduler starts automatically and stays running.
Run this script to start the scheduler independently of Flask.
"""

import time
import threading
from datetime import datetime
from scheduler import start_scheduler, get_scheduler_status, stop_scheduler

def auto_start_scheduler():
    """Automatically start and monitor the scheduler"""
    
    print("🚀 Auto-Starting Scheduler...")
    print("=" * 50)
    
    # Start scheduler
    start_scheduler()
    time.sleep(2)
    
    # Check initial status
    status = get_scheduler_status()
    print(f"📊 Initial Status:")
    print(f"   - Running: {status.get('is_running', False)}")
    print(f"   - Thread Alive: {status.get('thread_alive', False)}")
    print(f"   - Sources: {status.get('sources', [])}")
    print(f"   - Next run in: {status.get('time_until_next_minutes', 0)} minutes")
    
    print("\n⏰ Scheduler is now running automatically!")
    print("📋 Will collect Upwork jobs every 2 hours")
    print("🌐 Flask app available at: http://localhost:5000")
    print("📊 Check Google Sheets for new jobs")
    print("\nPress Ctrl+C to stop...")
    
    # Keep running and monitor
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
        stop_scheduler()
        print("✅ Scheduler stopped")

if __name__ == "__main__":
    auto_start_scheduler() 
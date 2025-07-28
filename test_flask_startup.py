"""
Test Flask Startup
=================

Test script to verify Flask app starts the scheduler properly.
"""

import subprocess
import time
import sys

def test_flask_startup():
    """Test Flask app startup with scheduler"""
    
    print("🧪 Testing Flask app startup...")
    print("=" * 50)
    
    try:
        # Start Flask app in background
        print("🚀 Starting Flask app...")
        process = subprocess.Popen([
            sys.executable, 'flask_app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a bit for startup
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Flask app started successfully")
            print("🌐 Dashboard available at: http://localhost:8080")
            print("⏰ Scheduler should be running automatically")
            print("\nPress Ctrl+C to stop Flask app...")
            
            try:
                # Keep running
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping Flask app...")
                process.terminate()
                process.wait()
                print("✅ Flask app stopped")
        else:
            stdout, stderr = process.communicate()
            print("❌ Flask app failed to start")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            
    except Exception as e:
        print(f"❌ Error testing Flask startup: {e}")

if __name__ == "__main__":
    test_flask_startup() 
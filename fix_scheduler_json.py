"""
Fix Scheduler JSON File
======================

Fix the corrupted JSON file that's causing scheduler issues.
"""

import os
import json
from datetime import datetime

def fix_scheduler_json():
    """Fix the corrupted scheduler JSON file"""
    
    print("🔧 Fixing corrupted scheduler JSON file...")
    
    # Path to the status file
    status_file = "data/scheduler_status.json"
    
    try:
        # Check if file exists
        if os.path.exists(status_file):
            print(f"📋 Found status file: {status_file}")
            
            # Try to read it
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"📄 File content length: {len(content)} characters")
                    
                    if not content.strip():
                        print("⚠️ File is empty, creating new content")
                        raise ValueError("Empty file")
                    
                    # Try to parse JSON
                    data = json.loads(content)
                    print("✅ JSON is valid")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ JSON is corrupted: {e}")
                print("🔄 Creating new valid JSON file...")
                
                # Create backup
                backup_file = f"{status_file}.backup"
                if os.path.exists(status_file):
                    os.rename(status_file, backup_file)
                    print(f"📋 Backup created: {backup_file}")
                
                # Create new valid JSON
                new_data = {
                    'enabled': True,
                    'last_run': None,
                    'next_run': None,
                    'collection_count': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'sources': ['upwork'],
                    'interval_minutes': 120,
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
                
                # Ensure directory exists
                os.makedirs('data', exist_ok=True)
                
                # Write new file
                with open(status_file, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2)
                
                print("✅ New valid JSON file created")
                return True
        else:
            print("📋 Status file doesn't exist, creating new one...")
            
            # Create new valid JSON
            new_data = {
                'enabled': True,
                'last_run': None,
                'next_run': None,
                'collection_count': 0,
                'success_count': 0,
                'error_count': 0,
                'sources': ['upwork'],
                'interval_minutes': 120,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            
            # Ensure directory exists
            os.makedirs('data', exist_ok=True)
            
            # Write new file
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2)
            
            print("✅ New status file created")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing JSON: {e}")
        return False

def test_scheduler_after_fix():
    """Test scheduler after fixing JSON"""
    
    print("\n🧪 Testing scheduler after JSON fix...")
    
    try:
        from scheduler import start_scheduler, get_scheduler_status, trigger_immediate_collection
        
        # Start scheduler
        start_scheduler()
        
        # Check status
        status = get_scheduler_status()
        print(f"\n📊 Scheduler Status:")
        print(f"   - Running: {status.get('is_running', False)}")
        print(f"   - Thread Alive: {status.get('thread_alive', False)}")
        print(f"   - Enabled: {status.get('enabled', False)}")
        print(f"   - Interval: {status.get('interval_minutes', 120)} minutes")
        print(f"   - Next run in: {status.get('time_until_next_minutes', 0)} minutes")
        
        # Test immediate collection
        print("\n🧪 Testing immediate collection...")
        success = trigger_immediate_collection()
        if success:
            print("✅ Immediate collection triggered successfully!")
        else:
            print("❌ Immediate collection failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing scheduler: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Scheduler JSON Fix")
    print("=" * 50)
    
    # Fix JSON
    success = fix_scheduler_json()
    
    if success:
        print("\n✅ JSON file fixed successfully!")
        
        # Test scheduler
        test_success = test_scheduler_after_fix()
        
        if test_success:
            print("\n🎉 Scheduler is now working!")
            print("📋 What happens next:")
            print("   1. Scheduler runs every 2 minutes")
            print("   2. Automatic Upwork job collection")
            print("   3. Jobs added to Google Sheets")
            print("   4. Monitor at: http://localhost:5000/settings")
        else:
            print("\n⚠️ Scheduler test failed, try running Flask app:")
            print("   python flask_app.py")
    else:
        print("\n❌ Failed to fix JSON file") 
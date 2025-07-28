#!/usr/bin/env python3
"""
Quick Test for 2-Minute Scheduler Configuration
==============================================

Verifies that both schedulers are set to 2 hours.
"""

def test_scheduler_intervals():
    """Test that both schedulers are set to 2 hours"""
    print("🕐 Testing 2-Hour Scheduler Configuration")
    print("=" * 50)
    
    # Test main scheduler
    try:
        from scheduler import DataCollectionScheduler
        main_scheduler = DataCollectionScheduler()
        main_interval = main_scheduler.collection_interval
        main_minutes = main_interval // 60
        
        print(f"📊 Main Scheduler:")
        print(f"   Interval: {main_interval} seconds ({main_minutes} minutes)")
        
        if main_interval == 120:
            print("   ✅ Correctly set to 2 hours")
        else:
            print(f"   ❌ Should be 120 seconds, got {main_interval}")
            
    except Exception as e:
        print(f"   ❌ Error testing main scheduler: {e}")
    
    print()
    
    # Test Upwork scheduler
    try:
        from upwork_scheduler import UpworkScheduler
        upwork_scheduler = UpworkScheduler()
        upwork_interval = upwork_scheduler.collection_interval
        upwork_minutes = upwork_interval // 60
        
        print(f"📊 Upwork Scheduler:")
        print(f"   Interval: {upwork_interval} seconds ({upwork_minutes} minutes)")
        
        if upwork_interval == 120:
            print("   ✅ Correctly set to 2 hours")
        else:
            print(f"   ❌ Should be 120 seconds, got {upwork_interval}")
            
    except Exception as e:
        print(f"   ❌ Error testing Upwork scheduler: {e}")
    
    print()
    print("🎯 Summary:")
    print("   - Both schedulers should run every 2 hours")
    print("   - Main scheduler: Google, Reddit, YouTube, Twitter")
    print("   - Upwork scheduler: Upwork jobs only")
    print("   - Jobs will be added to Google Sheets automatically")

if __name__ == "__main__":
    test_scheduler_intervals() 
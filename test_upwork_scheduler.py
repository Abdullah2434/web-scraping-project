#!/usr/bin/env python3
"""
Test Script for Upwork Scheduler
================================

Tests and monitors the Upwork scheduler that runs every 2 hours.
Provides status information and allows manual triggering.

Author: Web Scraping Project
"""

import json
import os
from datetime import datetime, timedelta

def test_upwork_scheduler():
    """Test the Upwork scheduler configuration"""
    print("🚀 Testing Upwork Scheduler Configuration")
    print("=" * 50)
    
    # Check scheduler status file
    status_file = 'data/upwork_scheduler_status.json'
    
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as f:
            status = json.load(f)
        
        print("📊 Current Upwork Scheduler Status:")
        print(f"   Enabled: {status.get('enabled', False)}")
        print(f"   Interval: {status.get('interval_minutes', 'Unknown')} minutes")
        print(f"   Last Run: {status.get('last_run', 'Never')}")
        print(f"   Next Run: {status.get('next_run', 'Unknown')}")
        print(f"   Collection Count: {status.get('collection_count', 0)}")
        print(f"   Success Count: {status.get('success_count', 0)}")
        print(f"   Error Count: {status.get('error_count', 0)}")
        print(f"   Total Jobs Collected: {status.get('total_jobs_collected', 0)}")
        print(f"   Total Jobs Added to Sheets: {status.get('total_jobs_added_to_sheets', 0)}")
        
        # Verify 2-hour interval
        interval = status.get('interval_minutes', 0)
        if interval == 120:
            print("✅ Scheduler is correctly configured for 2-hour intervals")
        else:
            print(f"⚠️  Scheduler interval is {interval} minutes (should be 120)")
            
    else:
        print("❌ Upwork scheduler status file not found")
    
    print()
    
    # Test scheduler module
    try:
        from upwork_scheduler import UpworkScheduler
        
        scheduler = UpworkScheduler()
        print("🔧 Upwork Scheduler Module Test:")
        print(f"   Default Interval: {scheduler.collection_interval} seconds")
        print(f"   Default Interval: {scheduler.collection_interval // 60} minutes")
        print(f"   Max Jobs Per Keyword: {scheduler.max_jobs_per_keyword}")
        print(f"   Skip Private Jobs: {scheduler.skip_private_jobs}")
        
        if scheduler.collection_interval == 7200:  # 2 hours in seconds
            print("✅ Upwork scheduler module correctly configured for 2-hour intervals")
        else:
            print(f"⚠️  Upwork scheduler module interval is {scheduler.collection_interval} seconds")
            
    except ImportError as e:
        print(f"❌ Error importing Upwork scheduler module: {e}")
    
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
    print("   - Upwork scheduler runs every 2 hours (120 minutes)")
    print("   - Collects jobs from Upwork using enhanced scraper")
    print("   - Automatically adds unique jobs to Google Sheets")
    print("   - Creates daily sheets with date/month titles")
    print("   - Prevents duplicate jobs using hash tracking")

def test_google_sheets_integration():
    """Test Google Sheets integration"""
    print("\n📋 Testing Google Sheets Integration")
    print("=" * 50)
    
    try:
        from google_sheets_integration import get_sheets_summary
        
        summary = get_sheets_summary()
        
        if 'error' not in summary:
            print("✅ Google Sheets integration working!")
            print(f"📊 Spreadsheet: {summary.get('spreadsheet_title', 'Unknown')}")
            print(f"📋 Total sheets: {summary.get('total_sheets', 0)}")
            print(f"📅 Today's sheet: {summary.get('today_sheet', 'Not created yet')}")
            print(f"📊 Today's jobs: {summary.get('today_jobs_count', 0)}")
            print(f"🔢 Unique jobs cache: {summary.get('unique_jobs_cache_size', 0)}")
        else:
            print(f"❌ Google Sheets integration error: {summary.get('error')}")
            
    except Exception as e:
        print(f"❌ Error testing Google Sheets integration: {e}")

def test_immediate_collection():
    """Test immediate Upwork collection"""
    print("\n🚀 Testing Immediate Upwork Collection")
    print("=" * 50)
    
    try:
        from upwork_scheduler import trigger_immediate_upwork_collection
        
        print("🔄 Triggering immediate collection...")
        result = trigger_immediate_upwork_collection()
        
        if result:
            print("✅ Immediate collection triggered successfully!")
            print("📊 Check the logs for collection progress...")
        else:
            print("❌ Failed to trigger immediate collection")
            
    except Exception as e:
        print(f"❌ Error testing immediate collection: {e}")

def show_keywords():
    """Show current keywords"""
    print("\n🔍 Current Keywords")
    print("=" * 50)
    
    try:
        from keyword_manager import get_current_keywords
        
        keywords = get_current_keywords()
        print(f"📋 Keywords: {keywords}")
        print(f"📊 Total keywords: {len(keywords)}")
        
    except Exception as e:
        print(f"❌ Error getting keywords: {e}")

def main():
    """Main test function"""
    print("🧪 Upwork Scheduler Test Suite")
    print("=" * 50)
    
    # Test scheduler configuration
    test_upwork_scheduler()
    
    # Test Google Sheets integration
    test_google_sheets_integration()
    
    # Show current keywords
    show_keywords()
    
    # Ask user if they want to test immediate collection
    print("\n" + "=" * 50)
    print("🎯 Test Options:")
    print("1. Test immediate collection (will scrape Upwork now)")
    print("2. Just show status (no action)")
    
    try:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            test_immediate_collection()
        else:
            print("✅ Status check completed!")
            
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")
    except Exception as e:
        print(f"❌ Error in test: {e}")
    
    print("\n📋 Next Steps:")
    print("1. Start the scheduler: python upwork_scheduler.py")
    print("2. Monitor logs for collection progress")
    print("3. Check Google Sheets for new jobs")
    print("4. Jobs will be collected every 2 hours automatically")

if __name__ == "__main__":
    main() 
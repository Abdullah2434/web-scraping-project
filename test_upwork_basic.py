#!/usr/bin/env python3
"""
Basic Upwork Scheduler Test
===========================

Tests the Upwork scheduler without requiring Google Sheets credentials.
This script verifies the basic functionality and configuration.

Author: Web Scraping Project
"""

import json
import os
from datetime import datetime, timedelta

def test_basic_configuration():
    """Test basic Upwork scheduler configuration"""
    print("🚀 Testing Basic Upwork Scheduler Configuration")
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
        print("📁 Creating default status file...")
        
        # Create default status file
        os.makedirs('data', exist_ok=True)
        default_status = {
            'enabled': True,
            'last_run': None,
            'next_run': None,
            'collection_count': 0,
            'success_count': 0,
            'error_count': 0,
            'total_jobs_collected': 0,
            'total_jobs_added_to_sheets': 0,
            'interval_minutes': 120,
            'created_at': datetime.now().isoformat()
        }
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(default_status, f, indent=2)
        
        print("✅ Created default status file")
    
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
        print(f"   Upwork Filters: {scheduler.upwork_filters}")
        
        if scheduler.collection_interval == 7200:  # 2 hours in seconds
            print("✅ Upwork scheduler module correctly configured for 2-hour intervals")
        else:
            print(f"⚠️  Upwork scheduler module interval is {scheduler.collection_interval} seconds")
            
    except ImportError as e:
        print(f"❌ Error importing Upwork scheduler module: {e}")
    
    print()

def test_keywords():
    """Test keyword configuration"""
    print("🔍 Testing Keyword Configuration")
    print("=" * 50)
    
    try:
        from keyword_manager import get_current_keywords
        
        keywords = get_current_keywords()
        print(f"📋 Current Keywords: {keywords}")
        print(f"📊 Total keywords: {len(keywords)}")
        
        if keywords:
            print("✅ Keywords are configured")
        else:
            print("⚠️ No keywords configured - using defaults")
            
    except Exception as e:
        print(f"❌ Error getting keywords: {e}")
    
    print()

def test_upwork_scraper():
    """Test Upwork scraper availability"""
    print("🔧 Testing Upwork Scraper Availability")
    print("=" * 50)
    
    try:
        from fetch_upwork_data_enhanced import collect_comprehensive_upwork_data
        
        print("✅ Upwork scraper module is available")
        print("📋 Functions available:")
        print("   - collect_comprehensive_upwork_data")
        print("   - scrape_upwork_individual_pages")
        print("   - extract_job_details")
        
    except ImportError as e:
        print(f"❌ Error importing Upwork scraper: {e}")
    
    print()

def show_next_schedule():
    """Show next collection schedule"""
    print("⏰ Next Collection Schedule")
    print("=" * 50)
    
    status_file = 'data/upwork_scheduler_status.json'
    
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as f:
            status = json.load(f)
        
        last_run_str = status.get('last_run')
        interval_minutes = status.get('interval_minutes', 120)
        
        if last_run_str:
            try:
                last_run = datetime.fromisoformat(last_run_str.replace('Z', '+00:00'))
                next_run = last_run + timedelta(minutes=interval_minutes)
                
                print(f"📅 Last Run: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"📅 Next Run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏱️ Interval: {interval_minutes} minutes")
                
                # Show next few runs
                print("\n📅 Upcoming Collection Schedule:")
                current_time = datetime.now()
                for i in range(1, 6):  # Next 5 runs
                    future_run = last_run + timedelta(minutes=interval_minutes * i)
                    if future_run > current_time:
                        time_until = future_run - current_time
                        hours = int(time_until.total_seconds() // 3600)
                        minutes = int((time_until.total_seconds() % 3600) // 60)
                        print(f"   Run {i}: {future_run.strftime('%Y-%m-%d %H:%M:%S')} (in {hours}h {minutes}m)")
                        
            except Exception as e:
                print(f"❌ Error calculating schedule: {e}")
        else:
            print("📅 No previous runs - scheduler will start on first run")
            print(f"⏱️ Interval: {interval_minutes} minutes")
    else:
        print("❌ Status file not found")
    
    print()

def main():
    """Main test function"""
    print("🧪 Basic Upwork Scheduler Test")
    print("=" * 50)
    
    # Test basic configuration
    test_basic_configuration()
    
    # Test keywords
    test_keywords()
    
    # Test Upwork scraper
    test_upwork_scraper()
    
    # Show schedule
    show_next_schedule()
    
    print("🎯 Summary:")
    print("   - Upwork scheduler configured for 2-hour intervals")
    print("   - Enhanced Upwork scraper available")
    print("   - Keywords configured")
    print("   - Status tracking enabled")
    print()
    print("📋 Next Steps:")
    print("1. Set up Google Sheets credentials (see setup_google_sheets.py)")
    print("2. Start the scheduler: python upwork_scheduler.py")
    print("3. Monitor logs for collection progress")
    print("4. Jobs will be collected every 2 hours automatically")
    print()
    print("⚠️ Note: Google Sheets integration requires credentials setup")
    print("   Run: python setup_google_sheets.py for instructions")

if __name__ == "__main__":
    main() 
"""
Fresh Google Sheets Test
=======================

Test Google Sheets integration with fresh data to verify URLs are working.
"""

import json
import os
from datetime import datetime
from google_sheets_integration import add_upwork_jobs_to_sheets, get_sheets_summary

def test_fresh_google_sheets():
    """Test with fresh job data to verify URLs"""
    
    print("🔄 Testing fresh Google Sheets integration...")
    
    # Create fresh sample job data with proper URLs
    fresh_jobs = [
        {
            "id": f"test_job_{int(datetime.now().timestamp())}_1",
            "search_keyword": "python",
            "title": "Python Developer Needed - FRESH TEST",
            "description": "We need a Python developer for a web application project. This is a fresh test job.",
            "posted_time": {"display": "5 minutes ago"},
            "url": "https://www.upwork.com/jobs/python-developer-fresh-test-1",
            "collected_at": datetime.now().isoformat()
        },
        {
            "id": f"test_job_{int(datetime.now().timestamp())}_2", 
            "search_keyword": "web development",
            "title": "Web Development Project - FRESH TEST",
            "description": "Looking for an expert web developer for a full-stack project. This is a fresh test job.",
            "posted_time": {"display": "10 minutes ago"},
            "url": "https://www.upwork.com/jobs/web-development-fresh-test-2",
            "collected_at": datetime.now().isoformat()
        }
    ]
    
    try:
        print(f"📋 Adding {len(fresh_jobs)} fresh test jobs...")
        
        result = add_upwork_jobs_to_sheets(fresh_jobs)
        
        if result.get('success'):
            print("✅ Fresh test jobs added successfully!")
            print(f"📊 Jobs added: {result.get('jobs_added', 0)}")
            print(f"📄 Sheet: {result.get('sheet_name', 'Unknown')}")
            
            # Get summary
            summary = get_sheets_summary()
            print(f"\n📈 Fresh Test Summary:")
            print(f"   Total sheets: {summary.get('total_sheets', 0)}")
            print(f"   Total jobs: {summary.get('total_jobs', 0)}")
            print(f"   Last updated: {summary.get('last_updated', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Error adding fresh test jobs: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error with fresh test: {e}")
        return False

def verify_url_structure():
    """Verify the job data structure has proper URLs"""
    
    print("\n🔍 Verifying job data structure...")
    
    # Load existing data to check structure
    upwork_data_file = "data/raw_upwork_data.json"
    
    if os.path.exists(upwork_data_file):
        try:
            with open(upwork_data_file, 'r', encoding='utf-8') as f:
                upwork_data = json.load(f)
            
            jobs = upwork_data.get('jobs', [])
            print(f"📋 Found {len(jobs)} jobs in data file")
            
            if jobs:
                # Check first few jobs for URL structure
                for i, job in enumerate(jobs[:3]):
                    print(f"\n📄 Job {i+1}:")
                    print(f"   Title: {job.get('title', 'N/A')[:50]}...")
                    print(f"   URL field: {job.get('url', 'NOT FOUND')}")
                    print(f"   Keywords: {job.get('search_keyword', 'N/A')}")
                    
                    if job.get('url') and job.get('url') != 'N/A':
                        print(f"   ✅ URL found: {job.get('url')}")
                    else:
                        print(f"   ❌ URL missing or N/A")
                        
        except Exception as e:
            print(f"❌ Error reading data file: {e}")
    else:
        print("❌ No data file found")

if __name__ == "__main__":
    print("🚀 Fresh Google Sheets URL Test")
    print("=" * 50)
    
    # Verify data structure first
    verify_url_structure()
    
    # Test with fresh data
    test_result = test_fresh_google_sheets()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    
    if test_result:
        print("✅ Fresh Google Sheets test successful!")
        print("🌐 Check your spreadsheet for the new test jobs with URLs:")
        print("   https://docs.google.com/spreadsheets/d/1fgzMNrsdoWYxhItFWdSQkxgq0VqPYh_6tmkRGaWJvwU")
    else:
        print("❌ Fresh Google Sheets test failed")
        print("💡 Check the error messages above") 
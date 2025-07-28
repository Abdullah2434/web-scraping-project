"""
Test Google Sheets Integration
============================

Test adding Upwork jobs to Google Sheets automatically.
"""

import json
import os
from datetime import datetime
from google_sheets_integration import add_upwork_jobs_to_sheets, get_sheets_summary

def test_google_sheets_integration():
    """Test adding jobs to Google Sheets"""
    
    print("📊 Testing Google Sheets integration...")
    
    # Load existing Upwork data
    upwork_data_file = "data/raw_upwork_data.json"
    
    if not os.path.exists(upwork_data_file):
        print("❌ No Upwork data found. Run the scraper first!")
        return False
    
    try:
        with open(upwork_data_file, 'r', encoding='utf-8') as f:
            upwork_data = json.load(f)
        
        jobs = upwork_data.get('jobs', [])
        print(f"📋 Found {len(jobs)} jobs in data file")
        
        if not jobs:
            print("❌ No jobs found in data file")
            return False
        
        # Test adding jobs to Google Sheets
        print("🔄 Adding jobs to Google Sheets...")
        
        result = add_upwork_jobs_to_sheets(jobs)
        
        if result.get('success'):
            print("✅ Successfully added jobs to Google Sheets!")
            print(f"📊 Jobs added: {result.get('jobs_added', 0)}")
            print(f"📋 Total jobs in sheet: {result.get('total_jobs', 0)}")
            print(f"📄 Sheet name: {result.get('sheet_name', 'Unknown')}")
            
            # Get summary
            summary = get_sheets_summary()
            print(f"\n📈 Sheets Summary:")
            print(f"   Total sheets: {summary.get('total_sheets', 0)}")
            print(f"   Total jobs: {summary.get('total_jobs', 0)}")
            print(f"   Last updated: {summary.get('last_updated', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Error adding jobs: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Google Sheets integration: {e}")
        return False

def test_with_sample_jobs():
    """Test with sample job data"""
    
    print("\n🧪 Testing with sample job data...")
    
    # Create sample job data
    sample_jobs = [
        {
            "title": "Python Developer Needed",
            "budget": {"raw_text": "$50/hour", "type": "hourly"},
            "job_type": "hourly",
            "experience_level": "intermediate",
            "posted_time": {"display": "2 hours ago"},
            "proposals_count": {"count": 5, "display": "5-10"},
            "client_location": "United States",
            "client_rating": 4.8,
            "payment_verified": {"status": "verified", "display": "Payment verified"},
            "skills": ["Python", "Django", "React"],
            "description": "We need a Python developer for a web application project.",
            "job_url": "https://www.upwork.com/jobs/test-job-1",
            "keyword": "python",
            "collected_at": datetime.now().isoformat()
        },
        {
            "title": "Web Development Project",
            "budget": {"raw_text": "$2000", "type": "fixed"},
            "job_type": "fixed",
            "experience_level": "expert",
            "posted_time": {"display": "1 hour ago"},
            "proposals_count": {"count": 3, "display": "Less than 5"},
            "client_location": "Canada",
            "client_rating": 4.9,
            "payment_verified": {"status": "verified", "display": "Payment verified"},
            "skills": ["JavaScript", "Node.js", "MongoDB"],
            "description": "Looking for an expert web developer for a full-stack project.",
            "job_url": "https://www.upwork.com/jobs/test-job-2",
            "keyword": "web development",
            "collected_at": datetime.now().isoformat()
        }
    ]
    
    try:
        print(f"📋 Adding {len(sample_jobs)} sample jobs...")
        
        result = add_upwork_jobs_to_sheets(sample_jobs)
        
        if result.get('success'):
            print("✅ Sample jobs added successfully!")
            print(f"📊 Jobs added: {result.get('jobs_added', 0)}")
            print(f"📄 Sheet: {result.get('sheet_name', 'Unknown')}")
            return True
        else:
            print(f"❌ Error adding sample jobs: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error with sample jobs: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Google Sheets Integration")
    print("=" * 50)
    
    # Test with existing data
    test1 = test_google_sheets_integration()
    
    # Test with sample data
    test2 = test_with_sample_jobs()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    
    if test1 or test2:
        print("✅ Google Sheets integration is working!")
        print("🌐 Check your spreadsheet: https://docs.google.com/spreadsheets/d/1fgzMNrsdoWYxhItFWdSQkxgq0VqPYh_6tmkRGaWJvwU")
    else:
        print("❌ Google Sheets integration needs attention")
        print("💡 Check the error messages above") 
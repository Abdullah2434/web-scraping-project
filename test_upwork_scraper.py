"""
Test Upwork Scraper
==================

Test the Upwork scraper functionality with sample keywords.
"""

from fetch_upwork_data_enhanced import collect_comprehensive_upwork_data
import json

def test_upwork_scraper():
    """Test Upwork scraper with sample keywords"""
    
    print("💼 Testing Upwork scraper...")
    
    # Test keywords
    test_keywords = ["python", "web development"]
    
    print(f"🔍 Testing with keywords: {test_keywords}")
    
    try:
        # Run scraper with more jobs for better testing
        result = collect_comprehensive_upwork_data(
            keywords=test_keywords,
            max_jobs_per_keyword=2,  # Increased to collect more jobs
            use_persistence=True,
            skip_private_jobs=True
        )
        
        print("✅ Upwork scraper completed successfully!")
        print(f"📊 Total jobs collected: {len(result.get('jobs', []))}")
        print(f"🔍 Keywords processed: {len(result.get('keywords_processed', []))}")
        
        # Show sample job data
        jobs = result.get('jobs', [])
        if jobs:
            print(f"\n📋 Sample job data:")
            sample_job = jobs[0]
            print(f"   Title: {sample_job.get('title', 'N/A')}")
            print(f"   Budget: {sample_job.get('budget', 'N/A')}")
            print(f"   Job Type: {sample_job.get('job_type', 'N/A')}")
            print(f"   Posted: {sample_job.get('posted_time', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Upwork scraper error: {e}")
        return False

if __name__ == "__main__":
    test_upwork_scraper() 
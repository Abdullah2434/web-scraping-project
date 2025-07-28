"""
Clear Cache and Test with More Jobs
==================================

Clear the duplicate job cache and test with more jobs to see more data in Google Sheets.
"""

import os
import json
from test_upwork_scraper import test_upwork_scraper

def clear_duplicate_cache():
    """Clear the duplicate jobs cache to allow more jobs to be added"""
    
    print("🧹 Clearing duplicate jobs cache...")
    
    cache_file = "data/unique_jobs_cache.json"
    
    if os.path.exists(cache_file):
        try:
            # Backup the cache first
            backup_file = f"{cache_file}.backup"
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"📋 Backup created: {backup_file}")
            print(f"📊 Previous cache had {len(cache_data.get('unique_jobs', []))} unique jobs")
            
            # Clear the cache
            os.remove(cache_file)
            print("✅ Duplicate cache cleared successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
            return False
    else:
        print("ℹ️ No cache file found to clear")
        return True

def test_with_more_jobs():
    """Test with more jobs after clearing cache"""
    
    print("\n🚀 Testing with more jobs...")
    print("=" * 50)
    
    # Clear cache first
    if clear_duplicate_cache():
        # Run the scraper test
        success = test_upwork_scraper()
        
        if success:
            print("\n✅ Test completed successfully!")
            print("📊 Check your Google Sheets for more jobs:")
            print("🌐 https://docs.google.com/spreadsheets/d/1fgzMNrsdoWYxhItFWdSQkxgq0VqPYh_6tmkRGaWJvwU")
        else:
            print("\n❌ Test failed")
    else:
        print("❌ Could not clear cache")

if __name__ == "__main__":
    test_with_more_jobs() 
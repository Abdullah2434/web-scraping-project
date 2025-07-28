"""
Complete Setup Test
==================

Test all components of the web scraping dashboard:
1. Google Sheets credentials
2. Data collection modules
3. Flask application
4. Scheduler functionality
5. Upwork scraper
"""

import os
import sys
import json
import time
from datetime import datetime

def test_environment():
    """Test basic environment setup"""
    print("🔧 Testing environment setup...")
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check if virtual environment is active
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is active")
    else:
        print("⚠️  Virtual environment not detected")
    
    # Check required files
    required_files = [
        'requirements.txt',
        'config.py',
        'flask_app.py',
        'google_sheets_credentials.json'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
    
    print()

def test_dependencies():
    """Test if all required packages are installed"""
    print("📦 Testing dependencies...")
    
    required_packages = [
        'flask',
        'pandas',
        'requests',
        'gspread',
        'google-auth',
        'praw',
        'pytrends',
        'google-api-python-client',
        'tweepy',
        'textblob',
        'apscheduler',
        'selenium',
        'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("💡 Run: pip install -r requirements.txt")
    else:
        print("\n✅ All dependencies are installed!")
    
    print()

def test_google_sheets():
    """Test Google Sheets integration"""
    print("📊 Testing Google Sheets integration...")
    
    try:
        from google.oauth2.service_account import Credentials
        import gspread
        
        credentials_file = "google_sheets_credentials.json"
        if not os.path.exists(credentials_file):
            print("❌ google_sheets_credentials.json not found!")
            return False
        
        # Load credentials
        creds = Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Create client
        client = gspread.authorize(creds)
        
        # Test connection
        test_spreadsheet_id = "1fgzMNrsdoWYxhItFWdSQkxgq0VqPYh_6tmkRGaWJvwU"
        spreadsheet = client.open_by_key(test_spreadsheet_id)
        
        print(f"✅ Connected to Google Sheets!")
        print(f"📊 Spreadsheet: {spreadsheet.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Sheets error: {e}")
        return False

def test_data_collection():
    """Test data collection modules"""
    print("📡 Testing data collection modules...")
    
    modules_to_test = [
        'fetch_google_data',
        'fetch_reddit_data', 
        'fetch_youtube_data',
        'fetch_twitter_data',
        'fetch_upwork_data_enhanced'
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module} - {e}")
    
    print()

def test_flask_app():
    """Test Flask application"""
    print("🌐 Testing Flask application...")
    
    try:
        from flask_app import app
        print("✅ Flask app imported successfully")
        
        # Test basic routes
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Dashboard route working")
            else:
                print(f"❌ Dashboard route error: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Flask app error: {e}")
    
    print()

def test_scheduler():
    """Test scheduler functionality"""
    print("⏰ Testing scheduler...")
    
    try:
        from scheduler import DataCollectionScheduler
        
        scheduler = DataCollectionScheduler()
        print("✅ Scheduler initialized")
        
        # Test status loading
        status = scheduler.get_status()
        print(f"✅ Scheduler status loaded: {status.get('enabled', False)}")
        
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
    
    print()

def test_upwork_scraper():
    """Test Upwork scraper"""
    print("💼 Testing Upwork scraper...")
    
    try:
        from fetch_upwork_data_enhanced import UpworkFilters
        
        filters = UpworkFilters()
        print("✅ Upwork filters initialized")
        
        # Test URL building
        test_url = filters.build_search_url("python", "today", "any", "any", "any", "both")
        print(f"✅ URL building working: {len(test_url)} characters")
        
    except Exception as e:
        print(f"❌ Upwork scraper error: {e}")
    
    print()

def test_data_directory():
    """Test data directory and files"""
    print("📁 Testing data directory...")
    
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print("✅ Created data directory")
    else:
        print("✅ Data directory exists")
    
    # Check for existing data files
    data_files = [
        'raw_google_trends.json',
        'raw_reddit_data.json',
        'raw_youtube_data.json',
        'raw_twitter_data.json',
        'raw_upwork_data.json',
        'user_keywords.json'
    ]
    
    for file in data_files:
        filepath = os.path.join(data_dir, file)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"⚠️  {file} - not found (will be created when needed)")
    
    print()

def run_complete_test():
    """Run all tests"""
    print("🚀 Starting complete setup test...")
    print("=" * 50)
    
    test_environment()
    test_dependencies()
    test_data_directory()
    
    # Test Google Sheets
    sheets_ok = test_google_sheets()
    
    # Test other components
    test_data_collection()
    test_flask_app()
    test_scheduler()
    test_upwork_scraper()
    
    print("=" * 50)
    print("📋 Test Summary:")
    
    if sheets_ok:
        print("✅ Google Sheets integration working")
    else:
        print("❌ Google Sheets needs attention")
    
    print("\n🎯 Next Steps:")
    print("1. If all tests pass, you can run the application")
    print("2. If Google Sheets fails, check the spreadsheet sharing")
    print("3. If dependencies are missing, run: pip install -r requirements.txt")
    print("4. Start the app with: python flask_app.py")

if __name__ == "__main__":
    run_complete_test() 
#!/usr/bin/env python3
"""
Google Sheets Setup Script
==========================

Helps you set up Google Sheets integration for Upwork jobs.
This script will guide you through the process of creating
Google Service Account credentials.

Author: Web Scraping Project
"""

import os
import json
import subprocess
import sys

def print_setup_instructions():
    """Print detailed setup instructions"""
    print("🔧 Google Sheets Setup Instructions")
    print("=" * 50)
    print()
    print("📋 Step 1: Create Google Cloud Project")
    print("   1. Go to https://console.cloud.google.com/")
    print("   2. Create a new project or select existing")
    print("   3. Enable Google Sheets API")
    print("   4. Enable Google Drive API")
    print()
    print("📋 Step 2: Create Service Account")
    print("   1. Go to 'APIs & Services' > 'Credentials'")
    print("   2. Click 'Create Credentials' > 'Service Account'")
    print("   3. Fill in service account details")
    print("   4. Click 'Create and Continue'")
    print("   5. Skip role assignment (click 'Continue')")
    print("   6. Click 'Done'")
    print()
    print("📋 Step 3: Create and Download Key")
    print("   1. Click on your service account")
    print("   2. Go to 'Keys' tab")
    print("   3. Click 'Add Key' > 'Create new key'")
    print("   4. Choose 'JSON' format")
    print("   5. Download the JSON file")
    print("   6. Rename it to 'google_sheets_credentials.json'")
    print("   7. Place it in your project root directory")
    print()
    print("📋 Step 4: Share Google Sheet")
    print("   1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1fgzMNrsdoWYxhItFWdSQkxgq0VqPYh_6tmkRGaWJvwU/edit")
    print("   2. Click 'Share' button")
    print("   3. Add your service account email (from the JSON file)")
    print("   4. Give 'Editor' permissions")
    print("   5. Click 'Send'")
    print()
    print("📋 Step 5: Install Dependencies")
    print("   pip install gspread google-auth")
    print()
    print("📋 Step 6: Test Integration")
    print("   python test_google_sheets.py")
    print()

def check_credentials_file():
    """Check if credentials file exists"""
    credentials_file = "google_sheets_credentials.json"
    
    if os.path.exists(credentials_file):
        print("✅ Google Sheets credentials file found!")
        
        try:
            with open(credentials_file, 'r') as f:
                credentials = json.load(f)
            
            # Extract service account email
            client_email = credentials.get('client_email', 'Not found')
            project_id = credentials.get('project_id', 'Not found')
            
            print(f"📧 Service Account Email: {client_email}")
            print(f"🏗️ Project ID: {project_id}")
            print()
            print("⚠️ Remember to share your Google Sheet with this email!")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error reading credentials file: {e}")
            return False
    else:
        print("❌ Google Sheets credentials file not found!")
        print("📁 Expected file: google_sheets_credentials.json")
        print()
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import gspread
        print("✅ gspread is installed")
    except ImportError:
        print("❌ gspread is not installed")
        print("   Install with: pip install gspread")
        return False
    
    try:
        import google.auth
        print("✅ google-auth is installed")
    except ImportError:
        print("❌ google-auth is not installed")
        print("   Install with: pip install google-auth")
        return False
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'gspread', 'google-auth'])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def test_google_sheets_connection():
    """Test Google Sheets connection"""
    print("🧪 Testing Google Sheets connection...")
    
    try:
        from google_sheets_integration import get_sheets_summary
        
        summary = get_sheets_summary()
        
        if 'error' not in summary:
            print("✅ Google Sheets connection successful!")
            print(f"📊 Spreadsheet: {summary.get('spreadsheet_title', 'Unknown')}")
            print(f"📋 Total sheets: {summary.get('total_sheets', 0)}")
            print(f"📅 Today's sheet: {summary.get('today_sheet', 'Not created yet')}")
            return True
        else:
            print(f"❌ Google Sheets connection failed: {summary.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Google Sheets connection: {e}")
        return False

def create_test_sheet():
    """Create a test sheet to verify permissions"""
    print("📋 Creating test sheet...")
    
    try:
        from google_sheets_integration import sheets_manager
        
        # Test creating a sheet
        worksheet = sheets_manager.get_or_create_daily_sheet()
        
        if worksheet:
            print(f"✅ Test sheet created: {worksheet.title}")
            
            # Clean up test sheet
            try:
                worksheet.delete()
                print("🧹 Test sheet cleaned up")
            except:
                print("⚠️ Could not clean up test sheet (this is normal)")
            
            return True
        else:
            print("❌ Could not create test sheet")
            return False
            
    except Exception as e:
        print(f"❌ Error creating test sheet: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Google Sheets Setup for Upwork Jobs")
    print("=" * 50)
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("📦 Installing missing dependencies...")
        if not install_dependencies():
            print("❌ Failed to install dependencies")
            return
    
    print()
    
    # Check credentials
    if not check_credentials_file():
        print()
        print_setup_instructions()
        return
    
    print()
    
    # Test connection
    if test_google_sheets_connection():
        print()
        print("🎉 Setup completed successfully!")
        print()
        print("📋 Next steps:")
        print("   1. Start the Upwork scheduler: python upwork_scheduler.py")
        print("   2. Monitor the scheduler: python test_upwork_scheduler.py")
        print("   3. Check Google Sheets for new jobs every 2 hours")
        print()
    else:
        print()
        print("❌ Setup incomplete. Please follow the instructions above.")
        print()
        print_setup_instructions()

if __name__ == "__main__":
    main() 
"""
Test Google Sheets Integration
============================

Quick test to verify Google Sheets credentials and connection.
"""

import json
import os
from google.oauth2.service_account import Credentials
import gspread

def test_google_sheets_credentials():
    """Test if Google Sheets credentials are working"""
    
    print("🔍 Testing Google Sheets credentials...")
    
    # Check if credentials file exists
    credentials_file = "google_sheets_credentials.json"
    if not os.path.exists(credentials_file):
        print("❌ Error: google_sheets_credentials.json not found!")
        return False
    
    try:
        # Load credentials
        creds = Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Create client
        client = gspread.authorize(creds)
        
        # Test with a sample spreadsheet (you can change this)
        test_spreadsheet_id = "1fgzMNrsdoWYxhItFWdSQkxgq0VqPYh_6tmkRGaWJvwU"
        
        try:
            spreadsheet = client.open_by_key(test_spreadsheet_id)
            print("✅ Successfully connected to Google Sheets!")
            print(f"📊 Spreadsheet title: {spreadsheet.title}")
            
            # List worksheets
            worksheets = spreadsheet.worksheets()
            print(f"📋 Found {len(worksheets)} worksheets:")
            for ws in worksheets:
                print(f"   - {ws.title}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error accessing spreadsheet: {e}")
            print("💡 Make sure to share the spreadsheet with your service account email")
            return False
            
    except Exception as e:
        print(f"❌ Error with credentials: {e}")
        return False

if __name__ == "__main__":
    test_google_sheets_credentials() 
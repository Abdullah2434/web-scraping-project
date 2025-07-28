"""
Fix Google Sheets Headers
========================

Add proper column headers to the existing Google Sheets.
"""

import os
import json
from datetime import datetime
from google_sheets_integration import UpworkGoogleSheetsManager

def fix_google_sheets_headers():
    """Fix missing column headers in Google Sheets"""
    
    print("🔧 Fixing Google Sheets headers...")
    
    try:
        # Initialize Google Sheets manager
        sheets_manager = UpworkGoogleSheetsManager()
        
        if not sheets_manager.spreadsheet:
            print("❌ Could not connect to Google Sheets")
            return False
        
        # Get today's sheet
        today = datetime.now()
        sheet_title = today.strftime("%B_%d_%Y")
        
        try:
            worksheet = sheets_manager.spreadsheet.worksheet(sheet_title)
            print(f"📋 Found sheet: {sheet_title}")
            
            # Get all current values
            all_values = worksheet.get_all_values()
            print(f"📊 Current rows in sheet: {len(all_values)}")
            
            if len(all_values) > 0:
                # Check if first row looks like headers
                first_row = all_values[0]
                print(f"🔍 First row content: {first_row}")
                
                # If first row doesn't look like headers, insert headers at the top
                if not any(header in first_row[0].lower() for header in ['keyword', 'title', 'description', 'date', 'url']):
                    print("📝 Adding column headers...")
                    
                    # Insert headers at the top
                    headers = ['Keywords', 'Job Title', 'Description', 'Posted Date', 'URL']
                    worksheet.insert_row(headers, 1)
                    
                    # Format headers (bold and blue background)
                    worksheet.format('A1:E1', {
                        'textFormat': {'bold': True},
                        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9}
                    })
                    
                    print("✅ Headers added and formatted successfully!")
                    print("📋 Headers: Keywords | Job Title | Description | Posted Date | URL")
                    
                    # Show updated structure
                    updated_values = worksheet.get_all_values()
                    print(f"📊 Updated rows in sheet: {len(updated_values)}")
                    
                    return True
                else:
                    print("✅ Headers already exist")
                    return True
            else:
                print("⚠️ Sheet is empty")
                return False
                
        except Exception as e:
            print(f"❌ Error accessing sheet: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing headers: {e}")
        return False

if __name__ == "__main__":
    success = fix_google_sheets_headers()
    if success:
        print("\n🎉 Headers fixed successfully!")
        print("🌐 Check your Google Sheets now:")
        print("📊 https://docs.google.com/spreadsheets/d/1fgzMNrsdoWYxhItFWdSQkxgq0VqPYh_6tmkRGaWJvwU")
    else:
        print("\n❌ Failed to fix headers") 
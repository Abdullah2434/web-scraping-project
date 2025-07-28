"""
Fix First Row Formatting
=======================

Remove the blue background and bold formatting from the first job row (Row 2)
to make it look normal like the other job rows.
"""

import os
import json
from datetime import datetime
from google_sheets_integration import UpworkGoogleSheetsManager

def fix_first_row_formatting():
    """Fix the formatting of the first job row to make it normal"""
    
    print("🔧 Fixing first job row formatting...")
    
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
            
            if len(all_values) >= 2:
                # Check if row 2 (first job row) has formatting
                print("🎨 Removing formatting from first job row (Row 2)...")
                
                # Remove formatting from row 2 (first job row)
                worksheet.format('A2:E2', {
                    'textFormat': {'bold': False},
                    'backgroundColor': {'red': 1, 'green': 1, 'blue': 1}  # White background
                })
                
                print("✅ First job row formatting fixed!")
                print("📋 Row 1: Headers (blue background, bold)")
                print("📋 Row 2: First job (normal formatting)")
                print("📋 Rows 3+: Other jobs (normal formatting)")
                
                return True
            else:
                print("⚠️ Not enough rows to fix formatting")
                return False
                
        except Exception as e:
            print(f"❌ Error accessing sheet: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing formatting: {e}")
        return False

if __name__ == "__main__":
    success = fix_first_row_formatting()
    if success:
        print("\n🎉 First job row formatting fixed successfully!")
        print("🌐 Check your Google Sheets now:")
        print("📊 https://docs.google.com/spreadsheets/d/1fgzMNrsdoWYxhItFWdSQkxgq0VqPYh_6tmkRGaWJvwU")
        print("\n📋 Expected result:")
        print("   - Row 1: Headers (blue background, bold)")
        print("   - Row 2: First job (normal white background)")
        print("   - Rows 3+: Other jobs (normal white background)")
    else:
        print("\n❌ Failed to fix formatting") 
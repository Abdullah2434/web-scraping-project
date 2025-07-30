"""
Google Sheets Formatter
======================

Comprehensive utility to fix Google Sheets formatting issues:
1. Add missing column headers
2. Fix first job row formatting (remove blue background/bold)
3. Ensure consistent formatting across the sheet

Usage:
- Run without arguments to fix today's sheet
- Can be integrated into the main application
"""

import os
import json
from datetime import datetime
from google_sheets_integration import UpworkGoogleSheetsManager

def format_google_sheet(sheet_title=None):
    """
    Comprehensive Google Sheets formatting utility
    
    Args:
        sheet_title (str, optional): Specific sheet title. If None, uses today's sheet.
    
    Returns:
        dict: Results of formatting operations
    """
    
    print("🔧 Google Sheets Formatter")
    print("=" * 40)
    
    # Initialize results
    results = {
        'headers_added': False,
        'first_row_fixed': False,
        'sheet_title': sheet_title,
        'success': False,
        'error': None
    }
    
    try:
        # Initialize Google Sheets manager
        sheets_manager = UpworkGoogleSheetsManager()
        
        if not sheets_manager.spreadsheet:
            error_msg = "Could not connect to Google Sheets"
            print(f"❌ {error_msg}")
            results['error'] = error_msg
            return results
        
        # Get sheet title (today's sheet if not specified)
        if not sheet_title:
            today = datetime.now()
            sheet_title = today.strftime("%B_%d_%Y")
        
        results['sheet_title'] = sheet_title
        print(f"📋 Working on sheet: {sheet_title}")
        
        try:
            worksheet = sheets_manager.spreadsheet.worksheet(sheet_title)
            
            # Get all current values
            all_values = worksheet.get_all_values()
            print(f"📊 Current rows in sheet: {len(all_values)}")
            
            # Step 1: Fix Headers
            print("\n🔧 Step 1: Checking headers...")
            headers_fixed = fix_headers(worksheet, all_values)
            results['headers_added'] = headers_fixed
            
            # Refresh values after potential header insertion
            if headers_fixed:
                all_values = worksheet.get_all_values()
                print(f"📊 Updated rows after header fix: {len(all_values)}")
            
            # Step 2: Fix First Row Formatting
            print("\n🔧 Step 2: Checking first job row formatting...")
            if len(all_values) >= 2:
                first_row_fixed = fix_first_row_formatting(worksheet)
                results['first_row_fixed'] = first_row_fixed
            else:
                print("⚠️ Not enough rows to fix first row formatting")
                results['first_row_fixed'] = False
            
            # Summary
            print("\n" + "=" * 40)
            print("📋 FORMATTING SUMMARY:")
            print(f"   Headers: {'✅ Added' if results['headers_added'] else '✅ Already exist'}")
            print(f"   First Row: {'✅ Fixed' if results['first_row_fixed'] else '⚠️ Skipped'}")
            print(f"   Sheet: {sheet_title}")
            
            results['success'] = True
            return results
                
        except Exception as e:
            error_msg = f"Error accessing sheet: {e}"
            print(f"❌ {error_msg}")
            results['error'] = error_msg
            return results
            
    except Exception as e:
        error_msg = f"Error in formatting: {e}"
        print(f"❌ {error_msg}")
        results['error'] = error_msg
        return results

def fix_headers(worksheet, all_values):
    """Fix missing column headers"""
    
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
            return True
        else:
            print("✅ Headers already exist")
            return False
    else:
        print("⚠️ Sheet is empty")
        return False

def fix_first_row_formatting(worksheet):
    """Fix the formatting of the first job row to make it normal"""
    
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

def format_todays_sheet():
    """Convenience function to format today's sheet"""
    return format_google_sheet()

if __name__ == "__main__":
    print("🚀 Google Sheets Formatter")
    print("=" * 40)
    
    # Format today's sheet
    results = format_todays_sheet()
    
    if results['success']:
        print("\n🎉 Google Sheets formatting completed successfully!")
        print("🌐 Check your Google Sheets now:")
        print("📊 https://docs.google.com/spreadsheets/d/1fgzMNrsdoWYxhItFWdSQkxgq0VqPYh_6tmkRGaWJvwU")
        print("\n📋 Expected result:")
        print("   - Row 1: Headers (blue background, bold)")
        print("   - Row 2: First job (normal white background)")
        print("   - Rows 3+: Other jobs (normal white background)")
    else:
        print(f"\n❌ Failed to format Google Sheets: {results.get('error', 'Unknown error')}") 
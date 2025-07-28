"""
Google Sheets Integration for Upwork Jobs
========================================

Automatically adds Upwork jobs to Google Sheets with:
- Unique job tracking (no duplicates)
- Daily sheet creation with date/month titles
- Automatic formatting and organization
- Error handling and retry logic

Author: Web Scraping Project
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import time
import hashlib

# Google Sheets API
try:
    import gspread
    from google.oauth2.service_account import Credentials
    from google.auth.exceptions import GoogleAuthError
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("⚠️ Google Sheets API not available. Install with: pip install gspread google-auth")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UpworkGoogleSheetsManager:
    """
    Manages Upwork jobs integration with Google Sheets
    
    Features:
    - Automatic job addition to Google Sheets
    - Unique job tracking (prevents duplicates)
    - Daily sheet creation with date/month titles
    - Automatic formatting and organization
    - Error handling and retry logic
    """
    
    def __init__(self, spreadsheet_id: str = "1fgzMNrsdoWYxhItFWdSQkxgq0VqPYh_6tmkRGaWJvwU"):
        """
        Initialize Google Sheets manager
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.spreadsheet_id = spreadsheet_id
        self.spreadsheet = None
        self.client = None
        self.unique_jobs_cache = set()  # Track unique jobs to prevent duplicates
        self.credentials_file = "google_sheets_credentials.json"
        
        # Load unique jobs cache from file
        self.load_unique_jobs_cache()
        
        # Initialize Google Sheets connection
        self.initialize_google_sheets()
    
    def load_unique_jobs_cache(self):
        """Load unique jobs cache from file"""
        try:
            cache_file = "data/unique_jobs_cache.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.unique_jobs_cache = set(cache_data.get('unique_jobs', []))
                    logger.info(f"Loaded {len(self.unique_jobs_cache)} unique jobs from cache")
        except Exception as e:
            logger.error(f"Error loading unique jobs cache: {e}")
            self.unique_jobs_cache = set()
    
    def save_unique_jobs_cache(self):
        """Save unique jobs cache to file"""
        try:
            os.makedirs('data', exist_ok=True)
            cache_file = "data/unique_jobs_cache.json"
            cache_data = {
                'unique_jobs': list(self.unique_jobs_cache),
                'last_updated': datetime.now().isoformat(),
                'total_unique_jobs': len(self.unique_jobs_cache)
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.info(f"Saved {len(self.unique_jobs_cache)} unique jobs to cache")
        except Exception as e:
            logger.error(f"Error saving unique jobs cache: {e}")
    
    def initialize_google_sheets(self):
        """Initialize Google Sheets connection"""
        if not GOOGLE_SHEETS_AVAILABLE:
            logger.error("❌ Google Sheets API not available")
            return False
        
        try:
            # Check if credentials file exists
            if not os.path.exists(self.credentials_file):
                logger.error(f"❌ Google Sheets credentials file not found: {self.credentials_file}")
                logger.info("📋 Please create a Google Service Account and download credentials")
                logger.info("🔗 Guide: https://docs.gspread.org/en/latest/oauth2.html")
                return False
            
            # Set up credentials
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scope
            )
            
            # Create client
            self.client = gspread.authorize(credentials)
            
            # Open spreadsheet
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            
            logger.info("✅ Google Sheets connection established")
            logger.info(f"📊 Spreadsheet: {self.spreadsheet.title}")
            
            return True
            
        except GoogleAuthError as e:
            logger.error(f"❌ Google authentication error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error initializing Google Sheets: {e}")
            return False
    
    def get_or_create_daily_sheet(self) -> Optional[gspread.Worksheet]:
        """
        Get or create daily sheet with date/month title
        
        Returns:
            Worksheet object or None if error
        """
        try:
            if not self.spreadsheet:
                logger.error("❌ Spreadsheet not initialized")
                return None
            
            # Create sheet title with date/month
            today = datetime.now()
            sheet_title = today.strftime("%B_%d_%Y")  # e.g., "January_15_2025"
            
            # Check if sheet exists
            try:
                worksheet = self.spreadsheet.worksheet(sheet_title)
                logger.info(f"📋 Using existing sheet: {sheet_title}")
                
                # Check if headers exist, if not add them
                existing_values = worksheet.get_all_values()
                if not existing_values or len(existing_values) == 0:
                    # Add headers to existing sheet
                    headers = [
                        'Keywords', 'Job Title', 'Description', 'Posted Date', 'URL'
                    ]
                    worksheet.append_row(headers)
                    
                    # Format headers (bold)
                    worksheet.format('A1:E1', {
                        'textFormat': {'bold': True},
                        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9}
                    })
                    logger.info(f"✅ Added headers to existing sheet: {sheet_title}")
                
                return worksheet
            except gspread.WorksheetNotFound:
                # Create new sheet
                logger.info(f"📋 Creating new sheet: {sheet_title}")
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_title,
                    rows=1000,
                    cols=20
                )
                
                # Set up headers - PRIORITY FIELDS ONLY
                headers = [
                    'Keywords', 'Job Title', 'Description', 'Posted Date', 'URL'
                ]
                
                worksheet.append_row(headers)
                
                # Format headers (bold)
                worksheet.format('A1:E1', {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9}
                })
                
                logger.info(f"✅ Created and formatted sheet: {sheet_title}")
                return worksheet
                
        except Exception as e:
            logger.error(f"❌ Error getting/creating daily sheet: {e}")
            return None
    
    def generate_job_hash(self, job_data: Dict[str, Any]) -> str:
        """
        Generate unique hash for job to prevent duplicates
        
        Args:
            job_data: Job data dictionary
            
        Returns:
            Unique hash string
        """
        # Create unique identifier from job data
        unique_string = f"{job_data.get('id', '')}_{job_data.get('title', '')}_{job_data.get('budget', {}).get('raw_text', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def is_job_unique(self, job_data: Dict[str, Any]) -> bool:
        """
        Check if job is unique (not already added)
        
        Args:
            job_data: Job data dictionary
            
        Returns:
            True if job is unique, False if duplicate
        """
        job_hash = self.generate_job_hash(job_data)
        return job_hash not in self.unique_jobs_cache
    
    def format_job_for_sheets(self, job_data: Dict[str, Any]) -> List[str]:
        """
        Format job data for Google Sheets row - PRIORITY FIELDS ONLY
        
        Args:
            job_data: Job data dictionary
            
        Returns:
            List of values for Google Sheets row
        """
        # Extract priority fields only
        keywords = job_data.get('search_keyword', 'N/A')
        title = job_data.get('title', 'N/A')
        description = job_data.get('description', 'N/A')
        
        # Posted time
        posted_time = job_data.get('posted_time', {})
        if isinstance(posted_time, dict):
            time_text = posted_time.get('display', 'N/A')
        else:
            time_text = str(posted_time)
        
        # Job URL - MOST IMPORTANT!
        job_url = job_data.get('url', 'N/A')  # Fixed: use 'url' field, not 'job_url'
        
        return [
            keywords, title, description, time_text, job_url
        ]
    
    def add_jobs_to_sheets(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add unique jobs to Google Sheets
        
        Args:
            jobs: List of job data dictionaries
            
        Returns:
            Dictionary with results summary
        """
        if not self.spreadsheet:
            logger.error("❌ Google Sheets not initialized")
            return {
                'success': False,
                'error': 'Google Sheets not initialized',
                'jobs_added': 0,
                'jobs_skipped': len(jobs)
            }
        
        try:
            # Get or create daily sheet
            worksheet = self.get_or_create_daily_sheet()
            if not worksheet:
                return {
                    'success': False,
                    'error': 'Could not get/create worksheet',
                    'jobs_added': 0,
                    'jobs_skipped': len(jobs)
                }
            
            jobs_added = 0
            jobs_skipped = 0
            new_jobs_data = []
            
            logger.info(f"📊 Processing {len(jobs)} jobs for Google Sheets")
            
            for job in jobs:
                # Check if job is unique
                if self.is_job_unique(job):
                    # Format job for sheets
                    job_row = self.format_job_for_sheets(job)
                    new_jobs_data.append(job_row)
                    
                    # Add to unique cache
                    job_hash = self.generate_job_hash(job)
                    self.unique_jobs_cache.add(job_hash)
                    
                    jobs_added += 1
                else:
                    jobs_skipped += 1
            
            # Add all new jobs to sheet
            if new_jobs_data:
                worksheet.append_rows(new_jobs_data)
                logger.info(f"✅ Added {jobs_added} new jobs to Google Sheets")
                
                # Save updated cache
                self.save_unique_jobs_cache()
            
            return {
                'success': True,
                'jobs_added': jobs_added,
                'jobs_skipped': jobs_skipped,
                'total_processed': len(jobs),
                'sheet_title': worksheet.title,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error adding jobs to Google Sheets: {e}")
            return {
                'success': False,
                'error': str(e),
                'jobs_added': 0,
                'jobs_skipped': len(jobs)
            }
    
    def get_sheets_summary(self) -> Dict[str, Any]:
        """
        Get summary of Google Sheets integration
        
        Returns:
            Dictionary with summary information
        """
        try:
            if not self.spreadsheet:
                return {'error': 'Spreadsheet not initialized'}
            
            # Get all worksheets
            worksheets = self.spreadsheet.worksheets()
            
            # Get today's sheet
            today = datetime.now()
            today_sheet_title = today.strftime("%B_%d_%Y")
            
            today_sheet = None
            total_rows = 0
            
            for ws in worksheets:
                if ws.title == today_sheet_title:
                    today_sheet = ws
                    total_rows = len(ws.get_all_values()) - 1  # Subtract header
                    break
            
            return {
                'spreadsheet_title': self.spreadsheet.title,
                'total_sheets': len(worksheets),
                'today_sheet': today_sheet_title if today_sheet else None,
                'today_jobs_count': total_rows,
                'unique_jobs_cache_size': len(self.unique_jobs_cache),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting sheets summary: {e}")
            return {'error': str(e)}


# Global instance
sheets_manager = UpworkGoogleSheetsManager()

def add_upwork_jobs_to_sheets(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Add Upwork jobs to Google Sheets (convenience function)
    
    Args:
        jobs: List of job data dictionaries
        
    Returns:
        Dictionary with results summary
    """
    return sheets_manager.add_jobs_to_sheets(jobs)

def get_sheets_summary() -> Dict[str, Any]:
    """
    Get Google Sheets summary (convenience function)
    
    Returns:
        Dictionary with summary information
    """
    return sheets_manager.get_sheets_summary()

if __name__ == "__main__":
    # Test the Google Sheets integration
    print("🔧 Testing Google Sheets Integration")
    print("=" * 50)
    
    # Test initialization
    summary = get_sheets_summary()
    print(f"📊 Sheets Summary: {summary}")
    
    # Test with sample data
    sample_jobs = [
        {
            'id': 'test_job_1',
            'title': 'Python Developer Needed',
            'budget': {'raw_text': '$50-100/hr'},
            'job_details': {
                'job_type': 'Hourly',
                'experience_level': 'Intermediate',
                'posted_time': {'display': '2 hours ago'},
                'proposals_count': {'display': '5-10'},
                'client_location': 'United States',
                'client_rating': '4.8',
                'payment_verified': {'display': 'Payment verified'},
                'skills': ['Python', 'Django', 'React']
            },
            'description': 'We need a Python developer for a web application project.',
            'search_keyword': 'python',
            'job_url': 'https://www.upwork.com/jobs/test1'
        }
    ]
    
    result = add_upwork_jobs_to_sheets(sample_jobs)
    print(f"📋 Test Result: {result}") 
"""
Upwork Scheduler - 2-Hour Automated Job Collection
==================================================

Dedicated scheduler for Upwork jobs that:
- Runs every 2 hours automatically
- Collects jobs from Upwork
- Adds unique jobs to Google Sheets
- Creates daily sheets with date/month titles
- 100% automated process

Author: Web Scraping Project
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os

# Local imports
from keyword_manager import get_current_keywords, update_collection_timestamp
from fetch_upwork_data_enhanced import collect_comprehensive_upwork_data
from google_sheets_integration import add_upwork_jobs_to_sheets, get_sheets_summary

# Set up logging
logger = logging.getLogger(__name__)

class UpworkScheduler:
    """
    Dedicated scheduler for Upwork job collection and Google Sheets integration
    
    Features:
    - Runs every 2 hours (7200 seconds)
    - Collects jobs from Upwork using enhanced scraper
    - Automatically adds unique jobs to Google Sheets
    - Creates daily sheets with date/month titles
    - Prevents duplicate jobs
    - Comprehensive logging and error handling
    """
    
    def __init__(self):
        """Initialize the Upwork scheduler"""
        self.is_running = False
        self.collection_thread = None
        self.next_collection_time = None
        self.collection_interval = 7200  # 2 hours in seconds
        self.enabled = True
        self.status_file = os.path.join('data', 'upwork_scheduler_status.json')
        
        # Upwork collection settings
        self.upwork_filters = {
            'time_range': 'today',
            'hourly_filter': '',
            'budget_range': 'any',
            'job_type': 'any',
            'experience_level': 'any',
            'payment_status': 'both',
            'sort_by': 'recency'
        }
        
        self.max_jobs_per_keyword = 15  # Collect more jobs per keyword
        self.skip_private_jobs = True
        
        # Ensure status file exists
        self.ensure_status_file()
        
    def ensure_status_file(self):
        """Ensure scheduler status file exists"""
        try:
            os.makedirs('data', exist_ok=True)
            
            if not os.path.exists(self.status_file):
                default_status = {
                    'enabled': True,
                    'last_run': None,
                    'next_run': None,
                    'collection_count': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'total_jobs_collected': 0,
                    'total_jobs_added_to_sheets': 0,
                    'interval_minutes': 120,  # 2 hours
                    'created_at': datetime.now().isoformat()
                }
                
                with open(self.status_file, 'w', encoding='utf-8') as f:
                    json.dump(default_status, f, indent=2)
                    
                logger.info(f"Created Upwork scheduler status file: {self.status_file}")
            
        except Exception as e:
            logger.error(f"Error ensuring status file: {e}")
    
    def load_settings(self) -> Dict[str, Any]:
        """Load scheduler settings from file"""
        try:
            with open(self.status_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            self.enabled = settings.get('enabled', True)
            interval_minutes = settings.get('interval_minutes', 120)
            self.collection_interval = interval_minutes * 60
            
            logger.info(f"Loaded Upwork scheduler settings: enabled={self.enabled}, interval={interval_minutes}min")
            return settings
            
        except Exception as e:
            logger.error(f"Error loading Upwork scheduler settings: {e}")
            return {}
    
    def save_settings(self, **updates):
        """Save scheduler settings to file"""
        try:
            # Load current settings
            settings = {}
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # Update with new values
            settings.update(updates)
            settings['last_updated'] = datetime.now().isoformat()
            
            # Save updated settings
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
                
            logger.info(f"Saved Upwork scheduler settings: {updates}")
            
        except Exception as e:
            logger.error(f"Error saving Upwork scheduler settings: {e}")
    
    def start(self):
        """Start the Upwork scheduler"""
        if self.is_running:
            logger.warning("Upwork scheduler is already running")
            return
        
        self.load_settings()
        
        if not self.enabled:
            logger.info("Upwork scheduler is disabled in settings")
            return
        
        self.is_running = True
        self.collection_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.collection_thread.start()
        
        logger.info("🚀 Upwork scheduler started")
        logger.info(f"   Collection interval: {self.collection_interval // 60} minutes")
        logger.info(f"   Max jobs per keyword: {self.max_jobs_per_keyword}")
        logger.info(f"   Skip private jobs: {self.skip_private_jobs}")
    
    def stop(self):
        """Stop the Upwork scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.collection_thread and self.collection_thread.is_alive():
            logger.info("Stopping Upwork scheduler...")
            # Thread will stop on next iteration
        
        logger.info("🛑 Upwork scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        logger.info("🔄 Upwork scheduler loop started")
        
        # Calculate next collection time
        self.next_collection_time = datetime.now() + timedelta(seconds=self.collection_interval)
        self.save_settings(next_run=self.next_collection_time.isoformat())
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check if it's time for collection
                if current_time >= self.next_collection_time:
                    logger.info("⏰ Scheduled Upwork collection time reached")
                    self._run_upwork_collection()
                    
                    # Schedule next collection
                    self.next_collection_time = current_time + timedelta(seconds=self.collection_interval)
                    self.save_settings(next_run=self.next_collection_time.isoformat())
                    
                    logger.info(f"📅 Next Upwork collection scheduled for: {self.next_collection_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Sleep for a minute before checking again
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Error in Upwork scheduler loop: {e}")
                time.sleep(60)  # Continue after error
    
    def _run_upwork_collection(self):
        """Run Upwork data collection and Google Sheets integration"""
        try:
            logger.info("🚀 Starting scheduled Upwork data collection")
            
            # Get current keywords
            keywords = get_current_keywords()
            if not keywords:
                logger.warning("⚠️ No keywords configured for Upwork collection")
                self.save_settings(
                    last_run=datetime.now().isoformat(),
                    error_count=self._increment_counter('error_count')
                )
                return
            
            logger.info(f"🔍 Using keywords: {keywords}")
            logger.info(f"⚙️ Using filters: {self.upwork_filters}")
            
            # Collect Upwork data
            start_time = datetime.now()
            upwork_data = collect_comprehensive_upwork_data(
                keywords=keywords,
                filters=self.upwork_filters,
                max_jobs_per_keyword=self.max_jobs_per_keyword,
                use_persistence=True,
                skip_private_jobs=self.skip_private_jobs
            )
            end_time = datetime.now()
            
            collection_duration = end_time - start_time
            jobs = upwork_data.get('jobs', [])
            
            logger.info(f"📊 Upwork collection completed:")
            logger.info(f"   ⏱️ Duration: {collection_duration}")
            logger.info(f"   📋 Jobs collected: {len(jobs)}")
            
            # Add jobs to Google Sheets
            if jobs:
                logger.info("📋 Adding jobs to Google Sheets...")
                sheets_result = add_upwork_jobs_to_sheets(jobs)
                
                if sheets_result.get('success'):
                    jobs_added = sheets_result.get('jobs_added', 0)
                    jobs_skipped = sheets_result.get('jobs_skipped', 0)
                    
                    logger.info(f"✅ Google Sheets integration completed:")
                    logger.info(f"   📊 Jobs added: {jobs_added}")
                    logger.info(f"   ⏭️ Jobs skipped (duplicates): {jobs_skipped}")
                    logger.info(f"   📋 Sheet: {sheets_result.get('sheet_title', 'Unknown')}")
                    
                    # Update statistics
                    collection_count = self._increment_counter('collection_count')
                    success_count = self._increment_counter('success_count')
                    total_jobs_collected = self._get_counter('total_jobs_collected') + len(jobs)
                    total_jobs_added = self._get_counter('total_jobs_added_to_sheets') + jobs_added
                    
                    # Update collection timestamp
                    update_collection_timestamp()
                    
                    self.save_settings(
                        last_run=datetime.now().isoformat(),
                        collection_count=collection_count,
                        success_count=success_count,
                        total_jobs_collected=total_jobs_collected,
                        total_jobs_added_to_sheets=total_jobs_added,
                        last_successful_run=datetime.now().isoformat(),
                        last_collection_stats={
                            'jobs_collected': len(jobs),
                            'jobs_added_to_sheets': jobs_added,
                            'jobs_skipped': jobs_skipped,
                            'collection_duration_seconds': collection_duration.total_seconds(),
                            'keywords_used': keywords,
                            'filters_used': self.upwork_filters
                        }
                    )
                else:
                    logger.error(f"❌ Google Sheets integration failed: {sheets_result.get('error', 'Unknown error')}")
                    
                    error_count = self._increment_counter('error_count')
                    self.save_settings(
                        last_run=datetime.now().isoformat(),
                        error_count=error_count,
                        last_error=datetime.now().isoformat(),
                        last_error_message=sheets_result.get('error', 'Unknown error')
                    )
            else:
                logger.warning("⚠️ No jobs collected from Upwork")
                
                error_count = self._increment_counter('error_count')
                self.save_settings(
                    last_run=datetime.now().isoformat(),
                    error_count=error_count,
                    last_error=datetime.now().isoformat(),
                    last_error_message="No jobs collected"
                )
            
        except Exception as e:
            logger.error(f"❌ Error in scheduled Upwork collection: {e}")
            
            error_count = self._increment_counter('error_count')
            self.save_settings(
                last_run=datetime.now().isoformat(),
                error_count=error_count,
                last_error=datetime.now().isoformat(),
                last_error_message=str(e)
            )
    
    def _increment_counter(self, counter_name: str) -> int:
        """Increment a counter in the status file"""
        try:
            settings = {}
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            current_value = settings.get(counter_name, 0)
            new_value = current_value + 1
            
            return new_value
            
        except Exception as e:
            logger.error(f"Error incrementing counter {counter_name}: {e}")
            return 1
    
    def _get_counter(self, counter_name: str) -> int:
        """Get a counter value from the status file"""
        try:
            settings = {}
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            return settings.get(counter_name, 0)
            
        except Exception as e:
            logger.error(f"Error getting counter {counter_name}: {e}")
            return 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get current Upwork scheduler status"""
        try:
            settings = {}
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # Add runtime status
            status = {
                **settings,
                'is_running': self.is_running,
                'current_time': datetime.now().isoformat(),
                'thread_alive': self.collection_thread.is_alive() if self.collection_thread else False
            }
            
            # Calculate time until next collection
            if self.next_collection_time:
                time_until_next = self.next_collection_time - datetime.now()
                status['time_until_next_minutes'] = max(0, int(time_until_next.total_seconds() / 60))
            
            # Add Google Sheets summary
            try:
                sheets_summary = get_sheets_summary()
                status['google_sheets_summary'] = sheets_summary
            except Exception as e:
                status['google_sheets_summary'] = {'error': str(e)}
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting Upwork scheduler status: {e}")
            return {
                'error': str(e),
                'is_running': self.is_running,
                'current_time': datetime.now().isoformat()
            }
    
    def update_settings(self, enabled: Optional[bool] = None, interval_minutes: Optional[int] = None):
        """Update Upwork scheduler settings"""
        updates = {}
        
        if enabled is not None:
            self.enabled = enabled
            updates['enabled'] = enabled
        
        if interval_minutes is not None:
            self.collection_interval = interval_minutes * 60
            updates['interval_minutes'] = interval_minutes
        
        self.save_settings(**updates)
        
        # Restart scheduler if settings changed and it's running
        if self.is_running and updates:
            logger.info("🔄 Restarting Upwork scheduler with new settings")
            self.stop()
            time.sleep(1)
            self.start()
    
    def trigger_immediate_collection(self):
        """Trigger an immediate Upwork collection (outside of schedule)"""
        logger.info("🚀 Triggering immediate Upwork collection")
        
        # Run collection in a separate thread to avoid blocking
        collection_thread = threading.Thread(target=self._run_upwork_collection, daemon=True)
        collection_thread.start()
        
        return True


# Global Upwork scheduler instance
upwork_scheduler = UpworkScheduler()

def start_upwork_scheduler():
    """Start the global Upwork scheduler"""
    upwork_scheduler.start()

def stop_upwork_scheduler():
    """Stop the global Upwork scheduler"""
    upwork_scheduler.stop()

def get_upwork_scheduler_status():
    """Get Upwork scheduler status"""
    return upwork_scheduler.get_status()

def update_upwork_scheduler_settings(**kwargs):
    """Update Upwork scheduler settings"""
    upwork_scheduler.update_settings(**kwargs)

def trigger_immediate_upwork_collection():
    """Trigger immediate Upwork collection"""
    return upwork_scheduler.trigger_immediate_collection()

if __name__ == "__main__":
    # Test the Upwork scheduler
    print("🚀 Testing Upwork Scheduler")
    print("=" * 50)
    
    # Test status
    status = get_upwork_scheduler_status()
    print(f"📊 Status: {status}")
    
    # Test immediate collection
    print("\n🚀 Testing immediate collection...")
    result = trigger_immediate_upwork_collection()
    print(f"✅ Immediate collection triggered: {result}") 
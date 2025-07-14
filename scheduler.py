"""
Automated Data Collection Scheduler
==================================

Handles automated hourly data collection using user-defined keywords.
Supports configurable scheduling, error handling, and logging.

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
from config import DATA_PATHS

# Set up logging
logger = logging.getLogger(__name__)

class DataCollectionScheduler:
    """
    Automated scheduler for data collection
    
    Features:
    - Hourly data collection with user keywords
    - Configurable sources and intervals
    - Error handling and retry logic
    - Status tracking and logging
    """
    
    def __init__(self):
        """Initialize the scheduler"""
        self.is_running = False
        self.collection_thread = None
        self.next_collection_time = None
        self.collection_interval = 3600  # 1 hour in seconds
        self.enabled = True
        self.sources = ['google', 'reddit', 'youtube', 'twitter']
        self.status_file = os.path.join('data', 'scheduler_status.json')
        
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
                    'sources': self.sources,
                    'interval_minutes': 60,
                    'created_at': datetime.now().isoformat()
                }
                
                with open(self.status_file, 'w', encoding='utf-8') as f:
                    json.dump(default_status, f, indent=2)
                    
                logger.info(f"Created scheduler status file: {self.status_file}")
            
        except Exception as e:
            logger.error(f"Error ensuring status file: {e}")
    
    def load_settings(self) -> Dict[str, Any]:
        """Load scheduler settings from file"""
        try:
            with open(self.status_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            self.enabled = settings.get('enabled', True)
            self.sources = settings.get('sources', self.sources)
            interval_minutes = settings.get('interval_minutes', 60)
            self.collection_interval = interval_minutes * 60
            
            logger.info(f"Loaded scheduler settings: enabled={self.enabled}, interval={interval_minutes}min")
            return settings
            
        except Exception as e:
            logger.error(f"Error loading scheduler settings: {e}")
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
                
            logger.info(f"Saved scheduler settings: {updates}")
            
        except Exception as e:
            logger.error(f"Error saving scheduler settings: {e}")
    
    def start(self):
        """Start the automated scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.load_settings()
        
        if not self.enabled:
            logger.info("Scheduler is disabled in settings")
            return
        
        self.is_running = True
        self.collection_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.collection_thread.start()
        
        logger.info("🕒 Automated scheduler started")
        logger.info(f"   ⏰ Collection interval: {self.collection_interval // 60} minutes")
        logger.info(f"   📊 Sources: {', '.join(self.sources)}")
    
    def stop(self):
        """Stop the automated scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.collection_thread and self.collection_thread.is_alive():
            logger.info("Stopping scheduler...")
            # Thread will stop on next iteration
        
        logger.info("🛑 Automated scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        logger.info("📅 Scheduler loop started")
        
        # Calculate next collection time
        self.next_collection_time = datetime.now() + timedelta(seconds=self.collection_interval)
        self.save_settings(next_run=self.next_collection_time.isoformat())
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check if it's time for collection
                if current_time >= self.next_collection_time:
                    logger.info("⏰ Scheduled collection time reached")
                    self._run_collection()
                    
                    # Schedule next collection
                    self.next_collection_time = current_time + timedelta(seconds=self.collection_interval)
                    self.save_settings(next_run=self.next_collection_time.isoformat())
                    
                    logger.info(f"📅 Next collection scheduled for: {self.next_collection_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Sleep for a minute before checking again
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Continue after error
    
    def _run_collection(self):
        """Run data collection with current settings"""
        try:
            logger.info("🚀 Starting scheduled data collection")
            
            # Get current keywords
            keywords = get_current_keywords()
            if not keywords:
                logger.warning("⚠️ No keywords configured for collection")
                self.save_settings(
                    last_run=datetime.now().isoformat(),
                    error_count=self._increment_counter('error_count')
                )
                return
            
            logger.info(f"📝 Using keywords: {keywords}")
            logger.info(f"📊 Using sources: {self.sources}")
            
            # Import and run collection function
            from flask_app import run_data_collection_with_logging
            
            # Run collection with current keywords and sources
            results, successful_sources = run_data_collection_with_logging(keywords, self.sources)
            
            # Update statistics
            collection_count = self._increment_counter('collection_count')
            
            if successful_sources:
                success_count = self._increment_counter('success_count')
                logger.info(f"✅ Scheduled collection completed successfully")
                logger.info(f"   📊 Successful sources: {', '.join(successful_sources)}")
                
                # Update collection timestamp
                update_collection_timestamp()
                
                self.save_settings(
                    last_run=datetime.now().isoformat(),
                    collection_count=collection_count,
                    success_count=success_count,
                    last_successful_run=datetime.now().isoformat(),
                    last_results=results
                )
            else:
                error_count = self._increment_counter('error_count')
                logger.error("❌ Scheduled collection failed - no sources successful")
                
                self.save_settings(
                    last_run=datetime.now().isoformat(),
                    collection_count=collection_count,
                    error_count=error_count,
                    last_error=datetime.now().isoformat()
                )
            
        except Exception as e:
            logger.error(f"💥 Error in scheduled collection: {e}")
            
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
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
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
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {
                'error': str(e),
                'is_running': self.is_running,
                'current_time': datetime.now().isoformat()
            }
    
    def update_settings(self, enabled: bool = None, sources: List[str] = None, interval_minutes: int = None):
        """Update scheduler settings"""
        updates = {}
        
        if enabled is not None:
            self.enabled = enabled
            updates['enabled'] = enabled
        
        if sources is not None:
            self.sources = sources
            updates['sources'] = sources
        
        if interval_minutes is not None:
            self.collection_interval = interval_minutes * 60
            updates['interval_minutes'] = interval_minutes
        
        self.save_settings(**updates)
        
        # Restart scheduler if settings changed and it's running
        if self.is_running and updates:
            logger.info("⚙️ Restarting scheduler with new settings")
            self.stop()
            time.sleep(1)
            self.start()
    
    def trigger_immediate_collection(self):
        """Trigger an immediate data collection (outside of schedule)"""
        logger.info("🚀 Triggering immediate data collection")
        
        # Run collection in a separate thread to avoid blocking
        collection_thread = threading.Thread(target=self._run_collection, daemon=True)
        collection_thread.start()
        
        return True


# Global scheduler instance
scheduler = DataCollectionScheduler()

def start_scheduler():
    """Start the global scheduler"""
    scheduler.start()

def stop_scheduler():
    """Stop the global scheduler"""
    scheduler.stop()

def get_scheduler_status():
    """Get scheduler status"""
    return scheduler.get_status()

def update_scheduler_settings(**kwargs):
    """Update scheduler settings"""
    scheduler.update_settings(**kwargs)

def trigger_immediate_collection():
    """Trigger immediate collection"""
    return scheduler.trigger_immediate_collection() 
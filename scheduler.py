"""
Automated Data Collection Scheduler
==================================

Handles automated data collection every 2 hours using user-defined keywords.
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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import date

# Local imports
from keyword_file_manager import get_current_keywords
from config import DATA_PATHS

# Set up logging
logger = logging.getLogger(__name__)

class DataCollectionScheduler:
    """
    Automated scheduler for data collection
    
    Features:
    - Data collection every 2 hours with user keywords
    - Configurable sources and intervals
    - Error handling and retry logic
    - Status tracking and logging
    """
    
    def __init__(self):
        """Initialize the scheduler"""
        self.is_running = False
        self.collection_thread = None
        self.next_collection_time = None
        self.collection_interval = 120  # 2 hours in seconds (120 minutes) 7200
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
                    'interval_minutes': 120,  # 2 hours default 7200
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
            interval_minutes = settings.get('interval_minutes', 120)  # Default to 2 hours
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
        
        logger.info("Automated scheduler started")
        logger.info(f"   Collection interval: {self.collection_interval // 60} minutes")
        logger.info(f"   Sources: {', '.join(self.sources)}")
    
    def stop(self):
        """Stop the automated scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.collection_thread and self.collection_thread.is_alive():
            logger.info("Stopping scheduler...")
            # Thread will stop on next iteration
        
        logger.info("Automated scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        logger.info("Scheduler loop started")
        
        # Calculate next collection time
        self.next_collection_time = datetime.now() + timedelta(seconds=self.collection_interval)
        self.save_settings(next_run=self.next_collection_time.isoformat())
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check if it's time for collection
                if current_time >= self.next_collection_time:
                    logger.info("Scheduled collection time reached")
                    self._run_collection()
                    
                    # Schedule next collection
                    self.next_collection_time = current_time + timedelta(seconds=self.collection_interval)
                    self.save_settings(next_run=self.next_collection_time.isoformat())
                    
                    logger.info(f"Next collection scheduled for: {self.next_collection_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Sleep for a minute before checking again
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Continue after error
    
    def _run_collection(self):
        """Run data collection with current settings"""
        try:
            logger.info("Starting scheduled data collection")
            
            # Get current keywords
            keywords = get_current_keywords()
            if not keywords:
                logger.warning("No keywords configured for collection")
                self.save_settings(
                    last_run=datetime.now().isoformat(),
                    error_count=self._increment_counter('error_count')
                )
                return
            
            logger.info(f"Using keywords: {keywords}")
            logger.info(f"Using sources: {self.sources}")
            
            # Check if only Upwork is configured
            if self.sources == ['upwork']:
                logger.info("🎯 UPWORK-ONLY mode detected - using dedicated Upwork collection")
                from flask_app import run_upwork_only_collection
                results, successful_sources = run_upwork_only_collection(keywords)
            else:
                # Import and run collection function for multiple sources
                from flask_app import run_data_collection_with_logging
                results, successful_sources = run_data_collection_with_logging(keywords, self.sources)
            
            # Update statistics
            collection_count = self._increment_counter('collection_count')
            
            if successful_sources:
                success_count = self._increment_counter('success_count')
                logger.info(f"Scheduled collection completed successfully")
                logger.info(f"   Successful sources: {', '.join(successful_sources)}")
                
                # Update collection timestamp
                # update_collection_timestamp()  # Not needed with file-based keywords
                
                self.save_settings(
                    last_run=datetime.now().isoformat(),
                    collection_count=collection_count,
                    success_count=success_count,
                    last_successful_run=datetime.now().isoformat(),
                    last_results=results
                )
                # Send daily report if this is the last run of the day (e.g., after 23:00)
                now = datetime.now()
                if now.hour >= 23:
                    send_daily_upwork_report()
            else:
                error_count = self._increment_counter('error_count')
                logger.error("Scheduled collection failed - no sources successful")
                
                self.save_settings(
                    last_run=datetime.now().isoformat(),
                    collection_count=collection_count,
                    error_count=error_count,
                    last_error=datetime.now().isoformat()
                )
            
        except Exception as e:
            logger.error(f"Error in scheduled collection: {e}")
            
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
    
    def update_settings(self, enabled: Optional[bool] = None, sources: Optional[List[str]] = None, interval_minutes: Optional[int] = None):
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
            logger.info("Restarting scheduler with new settings")
            self.stop()
            time.sleep(1)
            self.start()
    
    def trigger_immediate_collection(self):
        """Trigger an immediate data collection (outside of schedule)"""
        logger.info("Triggering immediate data collection")
        
        # Run collection in a separate thread to avoid blocking
        collection_thread = threading.Thread(target=self._run_collection, daemon=True)
        collection_thread.start()
        
        return True


def send_daily_upwork_report():
    """Aggregate Upwork jobs per keyword for today and send a professional HTML email report to the manager."""
    from config import EMAIL_REPORT_CONFIG
    from flask_app import load_upwork_data
    import logging
    logger = logging.getLogger(__name__)
    try:
        upwork_data = load_upwork_data()
        jobs = upwork_data.get('jobs', [])
        today_str = date.today().isoformat()
        # Aggregate jobs per keyword for today
        keyword_counts = {}
        for job in jobs:
            job_date = job.get('scraped_at') or job.get('posted_date')
            if job_date and today_str in job_date:
                keyword = job.get('search_keyword') or job.get('keyword') or 'Unknown'
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        # If no jobs for today, still send a report with zeroes for all keywords
        if not keyword_counts:
            from keyword_file_manager import get_current_keywords
            for kw in get_current_keywords() or []:
                keyword_counts[kw] = 0
        total_jobs = sum(keyword_counts.values())
        # Compose HTML email
        subject = f"Upwork Daily Report: {today_str}"
        html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f8fafc; color: #222; }}
            .container {{ background: #fff; border-radius: 10px; max-width: 480px; margin: 30px auto; padding: 32px 24px; box-shadow: 0 4px 24px rgba(0,0,0,0.07); }}
            h2 {{ color: #2563eb; margin-bottom: 8px; }}
            .subtitle {{ color: #64748b; font-size: 15px; margin-bottom: 24px; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 18px; }}
            th, td {{ border: 1px solid #e5e7eb; padding: 10px 12px; text-align: left; }}
            th {{ background: #f1f5f9; color: #1e293b; font-weight: 600; }}
            tr:nth-child(even) {{ background: #f9fafb; }}
            .total-row td {{ font-weight: bold; color: #2563eb; border-top: 2px solid #2563eb; }}
            .footer {{ color: #64748b; font-size: 13px; margin-top: 24px; }}
        </style>
        </head>
        <body>
        <div class="container">
            <h2>Upwork Daily Report</h2>
            <div class="subtitle">Date: {today_str}</div>
            <p>Dear Team,</p>
            <p>Here is the summary of Upwork jobs collected today, grouped by keyword:</p>
            <table>
                <tr><th>Keyword</th><th>Jobs Collected Today</th></tr>
                {''.join(f'<tr><td>{kw}</td><td>{count}</td></tr>' for kw, count in sorted(keyword_counts.items()))}
                <tr class="total-row"><td>Total</td><td>{total_jobs}</td></tr>
            </table>
            <div class="footer">
                This is an automated report generated by the Web Scraping Dashboard.<br>
              
                Best regards,<br>
                Web Scraping Dashboard
            </div>
        </div>
        </body>
        </html>
        """
        # Plain text fallback
        body = f"Upwork Daily Report - {today_str}\n\n"
        body += "Keyword           Jobs Collected Today\n"
        body += "-------------------------------------\n"
        for kw, count in sorted(keyword_counts.items()):
            body += f"{kw:18} {count}\n"
        body += f"\nTotal jobs: {total_jobs}\n\n"
        body += "This is an automated report generated by the Web Scraping Dashboard.\n"
        body += "If you have any questions, please contact the development team.\n"
        body += "\nBest regards,\nWeb Scraping Bot\n"
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("Web Scraping Bot", EMAIL_REPORT_CONFIG['from_email']))
        msg['To'] = ', '.join(EMAIL_REPORT_CONFIG['to_email'])
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        # Send email
        with smtplib.SMTP(EMAIL_REPORT_CONFIG['smtp_server'], EMAIL_REPORT_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_REPORT_CONFIG['smtp_user'], EMAIL_REPORT_CONFIG['smtp_password'])
            server.sendmail(
    EMAIL_REPORT_CONFIG['from_email'],
    EMAIL_REPORT_CONFIG['to_email'],  # This can be a list
    msg.as_string()
)

        logger.info(f"Daily Upwork report sent to {EMAIL_REPORT_CONFIG['to_email']}")
    except Exception as e:
        logger.error(f"Failed to send daily Upwork report: {e}")


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
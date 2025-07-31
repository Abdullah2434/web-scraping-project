"""
Email Reports System
===================

Handles daily, weekly, and monthly email reports with period-specific job counts and budgets.
"""

import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Tuple
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from config import EMAIL_REPORT_CONFIG
from flask_app import load_upwork_data
from keyword_manager import get_current_keywords

logger = logging.getLogger(__name__)

class EmailReportsManager:
    """Manages email reports for different time periods"""
    
    def __init__(self):
        self.stats_file = os.path.join('data', 'email_stats.json')
        self.cumulative_data_file = os.path.join('data', 'daily_email_data.json')
        self.ensure_stats_file()
        self.ensure_cumulative_data_file()
    
    def ensure_stats_file(self):
        """Ensure stats file exists"""
        try:
            os.makedirs('data', exist_ok=True)
            
            if not os.path.exists(self.stats_file):
                default_stats = {
                    'last_daily_report': None,
                    'last_weekly_report': None,
                    'last_monthly_report': None,
                    'created_at': datetime.now().isoformat()
                }
                
                with open(self.stats_file, 'w', encoding='utf-8') as f:
                    json.dump(default_stats, f, indent=2)
                    
                logger.info(f"Created email stats file: {self.stats_file}")
            
        except Exception as e:
            logger.error(f"Error ensuring stats file: {e}")
    
    def ensure_cumulative_data_file(self):
        """Ensure cumulative data file exists"""
        try:
            os.makedirs('data', exist_ok=True)
            
            if not os.path.exists(self.cumulative_data_file):
                default_data = {
                    'created_at': datetime.now().isoformat(),
                    'daily_data': {}
                }
                
                with open(self.cumulative_data_file, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2)
                    
                logger.info(f"Created cumulative data file: {self.cumulative_data_file}")
            
        except Exception as e:
            logger.error(f"Error ensuring cumulative data file: {e}")
    
    def load_stats(self) -> Dict[str, Any]:
        """Load email stats"""
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading email stats: {e}")
            return {}
    
    def save_stats(self, **updates):
        """Save email stats"""
        try:
            stats = self.load_stats()
            stats.update(updates)
            stats['last_updated'] = datetime.now().isoformat()
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
                
            logger.info(f"Saved email stats: {updates}")
            
        except Exception as e:
            logger.error(f"Error saving email stats: {e}")
    
    def load_cumulative_data(self) -> Dict[str, Any]:
        """Load cumulative daily data"""
        try:
            with open(self.cumulative_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cumulative data: {e}")
            return {'daily_data': {}}
    
    def save_cumulative_data(self, daily_data: Dict[str, Any]):
        """Save cumulative daily data"""
        try:
            data = self.load_cumulative_data()
            data['daily_data'].update(daily_data)
            data['last_updated'] = datetime.now().isoformat()
            
            with open(self.cumulative_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved cumulative data for {len(daily_data)} days")
            
        except Exception as e:
            logger.error(f"Error saving cumulative data: {e}")
    
    def extract_budget_from_job(self, job: Dict[str, Any]) -> float:
        """Extract budget amount from job data"""
        try:
            budget = job.get('budget', {})
            
            if isinstance(budget, dict):
                # Try different budget fields
                amount = (budget.get('min_amount') or 
                         budget.get('amount') or 
                         budget.get('max_amount') or 0)
            elif isinstance(budget, (int, float)):
                amount = budget
            else:
                amount = 0
            
            return float(amount) if amount else 0
            
        except Exception as e:
            logger.error(f"Error extracting budget from job: {e}")
            return 0
    
    def get_period_jobs(self, period_start: date, period_end: date) -> Dict[str, Dict[str, Any]]:
        """Get jobs for a specific period with keyword aggregation"""
        try:
            upwork_data = load_upwork_data()
            jobs = upwork_data.get('jobs', [])
            
            keyword_stats = {}
            
            for job in jobs:
                # Get job date
                job_date_str = job.get('scraped_at') or job.get('posted_date')
                if not job_date_str:
                    continue
                
                try:
                    # Parse job date
                    if 'T' in job_date_str:
                        job_date = datetime.fromisoformat(job_date_str.replace('Z', '+00:00')).date()
                    else:
                        job_date = datetime.strptime(job_date_str, '%Y-%m-%d').date()
                    
                    # Check if job is in period
                    if period_start <= job_date <= period_end:
                        keyword = job.get('search_keyword') or job.get('keyword') or 'Unknown'
                        budget = self.extract_budget_from_job(job)
                        
                        if keyword not in keyword_stats:
                            keyword_stats[keyword] = {
                                'jobs_count': 0,
                                'total_budget': 0,
                                'budget_count': 0
                            }
                        
                        keyword_stats[keyword]['jobs_count'] += 1
                        keyword_stats[keyword]['total_budget'] += budget
                        if budget > 0:
                            keyword_stats[keyword]['budget_count'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing job date: {e}")
                    continue
            
            return keyword_stats
            
        except Exception as e:
            logger.error(f"Error getting period jobs: {e}")
            return {}
    
    def get_cumulative_period_data(self, period_start: date, period_end: date) -> Dict[str, Dict[str, Any]]:
        """Get cumulative data for a specific period"""
        try:
            cumulative_data = self.load_cumulative_data()
            daily_data = cumulative_data.get('daily_data', {})
            
            # Aggregate data for the period
            period_stats = {}
            total_jobs = 0
            total_budget = 0
            total_budget_count = 0
            
            current_date = period_start
            while current_date <= period_end:
                date_str = current_date.isoformat()
                day_data = daily_data.get(date_str, {})
                
                if day_data:
                    # Add keyword data
                    for keyword, stats in day_data.items():
                        if keyword not in ['total_jobs', 'total_budget', 'total_budget_count']:
                            if keyword not in period_stats:
                                period_stats[keyword] = {
                                    'jobs_count': 0,
                                    'total_budget': 0,
                                    'budget_count': 0
                                }
                            
                            period_stats[keyword]['jobs_count'] += stats.get('jobs', 0)
                            period_stats[keyword]['total_budget'] += stats.get('total_budget', 0)
                            period_stats[keyword]['budget_count'] += stats.get('budget_count', 0)
                    
                    # Add totals
                    total_jobs += day_data.get('total_jobs', 0)
                    total_budget += day_data.get('total_budget', 0)
                    total_budget_count += day_data.get('total_budget_count', 0)
                
                current_date += timedelta(days=1)
            
            return period_stats
            
        except Exception as e:
            logger.error(f"Error getting cumulative period data: {e}")
            return {}
    
    def save_daily_data(self, date_str: str, keyword_stats: Dict[str, Dict[str, Any]], total_jobs: int, total_budget: float, total_budget_count: int):
        """Save daily data to cumulative file"""
        try:
            daily_data = {}
            
            # Save keyword stats
            for keyword, stats in keyword_stats.items():
                daily_data[keyword] = {
                    'jobs': stats['jobs_count'],
                    'total_budget': stats['total_budget'],
                    'budget_count': stats['budget_count']
                }
            
            # Save totals
            daily_data['total_jobs'] = total_jobs
            daily_data['total_budget'] = total_budget
            daily_data['total_budget_count'] = total_budget_count
            
            # Save to cumulative file
            self.save_cumulative_data({date_str: daily_data})
            
            logger.info(f"Saved daily data for {date_str}: {total_jobs} jobs, ${total_budget:,.0f} total budget")
            
        except Exception as e:
            logger.error(f"Error saving daily data: {e}")
    
    def send_daily_report(self):
        """Send daily email report"""
        try:
            today = date.today()
            stats = self.load_stats()
            
            # Check if already sent today
            last_daily = stats.get('last_daily_report')
            if last_daily and last_daily.startswith(today.isoformat()):
                logger.info("Daily report already sent today")
                return False
            
            # Get today's jobs
            keyword_stats = self.get_period_jobs(today, today)
            
            # Ensure all keywords are included (even with zero counts)
            current_keywords = get_current_keywords() or []
            for keyword in current_keywords:
                if keyword not in keyword_stats:
                    keyword_stats[keyword] = {'jobs_count': 0, 'total_budget': 0, 'budget_count': 0}
            
            # Calculate totals
            total_jobs = sum(stats['jobs_count'] for stats in keyword_stats.values())
            total_budget = sum(stats['total_budget'] for stats in keyword_stats.values())
            total_budget_count = sum(stats['budget_count'] for stats in keyword_stats.values())
            
            # Save daily data to cumulative file
            self.save_daily_data(today.isoformat(), keyword_stats, total_jobs, total_budget, total_budget_count)
            
            if self.send_email_report('daily', today, keyword_stats, today, today):
                self.save_stats(last_daily_report=today.isoformat())
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            return False
    
    def send_weekly_report(self):
        """Send weekly email report"""
        try:
            today = date.today()
            stats = self.load_stats()
            
            # Check if it's Sunday (end of week)
            if today.weekday() != 6:  # 6 = Sunday
                return False
            
            # Check if already sent this week
            week_start = today - timedelta(days=today.weekday())
            week_key = f"{week_start.isoformat()}_week"
            
            last_weekly = stats.get('last_weekly_report')
            if last_weekly == week_key:
                logger.info("Weekly report already sent this week")
                return False
            
            # Get this week's jobs from cumulative data
            week_start_date = today - timedelta(days=today.weekday())
            week_end_date = today
            keyword_stats = self.get_cumulative_period_data(week_start_date, week_end_date)
            
            if self.send_email_report('weekly', today, keyword_stats, week_start_date, week_end_date):
                self.save_stats(last_weekly_report=week_key)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending weekly report: {e}")
            return False
    
    def send_monthly_report(self):
        """Send monthly email report"""
        try:
            today = date.today()
            stats = self.load_stats()
            
            # Check if it's last day of month
            next_month = today.replace(day=1) + timedelta(days=32)
            last_day_of_month = next_month.replace(day=1) - timedelta(days=1)
            
            if today != last_day_of_month:
                return False
            
            # Check if already sent this month
            month_key = f"{today.year}-{today.month:02d}"
            last_monthly = stats.get('last_monthly_report')
            if last_monthly == month_key:
                logger.info("Monthly report already sent this month")
                return False
            
            # Get this month's jobs from cumulative data
            month_start = today.replace(day=1)
            month_end = today
            keyword_stats = self.get_cumulative_period_data(month_start, month_end)
            
            if self.send_email_report('monthly', today, keyword_stats, month_start, month_end):
                self.save_stats(last_monthly_report=month_key)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending monthly report: {e}")
            return False
    
    def send_email_report(self, report_type: str, report_date: date, keyword_stats: Dict[str, Dict[str, Any]], 
                         period_start: date = None, period_end: date = None) -> bool:
        """Send email report with the specified format"""
        try:
            # Calculate totals and averages
            total_jobs = sum(stats['jobs_count'] for stats in keyword_stats.values())
            total_budget = sum(stats['total_budget'] for stats in keyword_stats.values())
            total_budget_count = sum(stats['budget_count'] for stats in keyword_stats.values())
            
            # Calculate the true overall average budget (not average of averages)
            # We need to get all individual job budgets and calculate the average
            from flask_app import load_upwork_data
            from datetime import datetime
            
            # Get all jobs for the period and calculate true average
            upwork_data = load_upwork_data()
            jobs = upwork_data.get('jobs', [])
            
            period_budgets = []
            for job in jobs:
                job_date_str = job.get('scraped_at') or job.get('posted_date')
                if job_date_str:
                    try:
                        job_date = datetime.fromisoformat(job_date_str.split('T')[0]).date()
                        if period_start <= job_date <= period_end:
                            budget = self.extract_budget_from_job(job)
                            if budget > 0:
                                period_budgets.append(budget)
                    except:
                        continue
            
            # Calculate true average budget
            avg_budget = sum(period_budgets) / len(period_budgets) if period_budgets else 0
            
            # Generate subject and title based on report type
            if report_type == 'daily':
                subject = f"Upwork Daily Report: {report_date.isoformat()}"
                title = f"Upwork Daily Report"
                subtitle = f"Date: {report_date.isoformat()}"
                period_text = "today"
            elif report_type == 'weekly':
                subject = f"Upwork Weekly Report: Week {report_date.isocalendar()[1]} ({period_start.isoformat()} - {period_end.isoformat()})"
                title = f"Upwork Weekly Report"
                subtitle = f"Week {report_date.isocalendar()[1]} ({period_start.isoformat()} - {period_end.isoformat()})"
                period_text = "this week"
            else:  # monthly
                subject = f"Upwork Monthly Report: {report_date.strftime('%B %Y')}"
                title = f"Upwork Monthly Report"
                subtitle = f"{report_date.strftime('%B %Y')}"
                period_text = "this month"
            
            # Generate HTML table
            html_rows = []
            for keyword, stats in sorted(keyword_stats.items()):
                jobs_count = stats['jobs_count']
                budget_count = stats['budget_count']
                keyword_avg_budget = stats['total_budget'] / budget_count if budget_count > 0 else 0
                html_rows.append(f'<tr><td>{keyword}</td><td>{jobs_count}</td><td>${keyword_avg_budget:,.0f}</td></tr>')
            
            html_table = '\n'.join(html_rows)
            
            # HTML email
            html = f"""
            <html>
            <head>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f8fafc; color: #222; }}
                .container {{ background: #fff; border-radius: 10px; max-width: 600px; margin: 30px auto; padding: 32px 24px; box-shadow: 0 4px 24px rgba(0,0,0,0.07); }}
                h2 {{ color: #2563eb; margin-bottom: 8px; }}
                .subtitle {{ color: #64748b; font-size: 15px; margin-bottom: 24px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 18px; }}
                th, td {{ border: 1px solid #e5e7eb; padding: 12px 16px; text-align: left; }}
                th {{ background: #f1f5f9; color: #1e293b; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }}
                tr:nth-child(even) {{ background: #f9fafb; }}
                .total-row td {{ font-weight: bold; color: #2563eb; border-top: 2px solid #2563eb; background: #eff6ff; }}
                .footer {{ color: #64748b; font-size: 13px; margin-top: 24px; }}
            </style>
            </head>
            <body>
            <div class="container">
                <h2>{title}</h2>
                <div class="subtitle">{subtitle}</div>
                <p>Dear Team,</p>
                <p>Here is the summary of Upwork jobs collected {period_text}, grouped by keyword:</p>
                <table>
                    <tr><th>Keyword</th><th>Jobs {period_text.title()}</th><th>Average Budget {period_text.title()}</th></tr>
                    {html_table}
                    <tr class="total-row"><td><strong>Total</strong></td><td><strong>{total_jobs}</strong></td><td><strong>${avg_budget:,.0f}</strong></td></tr>
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
            body = f"{title} - {subtitle}\n\n"
            body += f"Keyword    | Jobs {period_text.title()} | Average Budget {period_text.title()}\n"
            body += "-" * 50 + "\n"
            
            for keyword, stats in sorted(keyword_stats.items()):
                jobs_count = stats['jobs_count']
                budget_count = stats['budget_count']
                keyword_avg_budget = stats['total_budget'] / budget_count if budget_count > 0 else 0
                body += f"{keyword:12} | {jobs_count:14} | ${keyword_avg_budget:,.0f}\n"
            
            # Use the same corrected average budget for plain text
            body += f"\nTotal      | {total_jobs:14} | ${avg_budget:,.0f}\n\n"
            body += "This is an automated report generated by the Web Scraping Dashboard.\n"
            body += "Best regards,\nWeb Scraping Bot\n"
            
            # Send email
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr(("Web Scraping Bot", EMAIL_REPORT_CONFIG['from_email']))
            msg['To'] = ', '.join(EMAIL_REPORT_CONFIG['to_email'])
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(EMAIL_REPORT_CONFIG['smtp_server'], EMAIL_REPORT_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(EMAIL_REPORT_CONFIG['smtp_user'], EMAIL_REPORT_CONFIG['smtp_password'])
                server.sendmail(
                    EMAIL_REPORT_CONFIG['from_email'],
                    EMAIL_REPORT_CONFIG['to_email'],
                    msg.as_string()
                )
            
            logger.info(f"{report_type.title()} report sent to {EMAIL_REPORT_CONFIG['to_email']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send {report_type} report: {e}")
            return False

# Global instance
email_manager = EmailReportsManager()

def send_daily_upwork_report():
    """Send daily Upwork report"""
    return email_manager.send_daily_report()

def send_weekly_upwork_report():
    """Send weekly Upwork report"""
    return email_manager.send_weekly_report()

def send_monthly_upwork_report():
    """Send monthly Upwork report"""
    return email_manager.send_monthly_report()

def check_and_send_reports():
    """Check and send all applicable reports"""
    try:
        # Send daily report (after 11 PM)
        now = datetime.now()
        if now.hour >= 23:
            email_manager.send_daily_report()
        
        # Send weekly report (Sunday 11 PM)
        if now.weekday() == 6 and now.hour >= 23:  # Sunday
            email_manager.send_weekly_report()
        
        # Send monthly report (last day of month 11 PM)
        today = date.today()
        next_month = today.replace(day=1) + timedelta(days=32)
        last_day_of_month = next_month.replace(day=1) - timedelta(days=1)
        
        if today == last_day_of_month and now.hour >= 23:
            email_manager.send_monthly_report()
            
    except Exception as e:
        logger.error(f"Error checking and sending reports: {e}") 
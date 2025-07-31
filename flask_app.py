"""
Flask Dashboard for Keyword Trends Analysis
==========================================

Modern web dashboard for analyzing keyword trends across multiple platforms.
Converts the Streamlit app to Flask with professional frontend.

Author: Web Scraping Project
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, Response, send_file
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import queue
import threading
import time

# Import existing business logic
from config import (
    DATA_PATHS,
    DEFAULT_KEYWORDS,
    CHART_COLORS,
    DASHBOARD_CONFIG
)

def add_no_cache_headers(response):
    """Add cache control headers to prevent caching"""
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Import data collection modules
try:
    from fetch_upwork_data_enhanced import collect_comprehensive_upwork_data
    from keyword_manager import keyword_manager, get_current_keywords, update_collection_timestamp
    from scheduler import start_scheduler, stop_scheduler, get_scheduler_status, update_scheduler_settings, trigger_immediate_collection
    
    # Simple function to load Upwork data from file
    def load_upwork_data():
        """Load Upwork data from the JSON file"""
        try:
            from config import DATA_PATHS
            file_path = DATA_PATHS['raw_upwork_data']
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {'jobs': [], 'metadata': {}}
        except Exception as e:
            logger.error(f"Error loading Upwork data: {e}")
            return {'jobs': [], 'metadata': {}}
    
    # Function to get Upwork summary statistics
    def get_upwork_summary_stats():
        """Get summary statistics for Upwork data"""
        try:
            upwork_data = load_upwork_data()
            jobs = upwork_data.get('jobs', [])
            
            if not jobs:
                return {
                    'total_jobs': 0,
                    'total_budget': 0,
                    'avg_budget': 0,
                    'hourly_jobs': 0,
                    'fixed_jobs': 0,
                    'keywords_analyzed': [],
                    'last_updated': 'Never'
                }
            
            # Calculate statistics
            total_jobs = len(jobs)
            total_budget = 0
            hourly_jobs = 0
            fixed_jobs = 0
            keywords_analyzed = set()
            
            for job in jobs:
                # Count job types
                job_type = job.get('job_type', '').lower()
                if 'hourly' in job_type:
                    hourly_jobs += 1
                elif 'fixed' in job_type:
                    fixed_jobs += 1
                
                # Sum budgets
                budget = job.get('budget', 0)
                if isinstance(budget, (int, float)):
                    total_budget += budget
                elif isinstance(budget, str):
                    # Try to extract number from budget string
                    import re
                    numbers = re.findall(r'\d+', budget)
                    if numbers:
                        total_budget += int(numbers[0])
                
                # Collect keywords
                keyword = job.get('search_keyword', '')
                if keyword:
                    keywords_analyzed.add(keyword)
            
            avg_budget = total_budget / total_jobs if total_jobs > 0 else 0
            
            return {
                'total_jobs': total_jobs,
                'total_budget': total_budget,
                'avg_budget': round(avg_budget, 2),
                'hourly_jobs': hourly_jobs,
                'fixed_jobs': fixed_jobs,
                'keywords_analyzed': list(keywords_analyzed),
                'last_updated': upwork_data.get('metadata', {}).get('collection_timestamp', 'Unknown')
            }
        except Exception as e:
            logger.error(f"Error calculating Upwork summary stats: {e}")
            return {
                'total_jobs': 0,
                'total_budget': 0,
                'avg_budget': 0,
                'hourly_jobs': 0,
                'fixed_jobs': 0,
                'keywords_analyzed': [],
                'last_updated': 'Error'
            }
    from scheduler import start_scheduler, stop_scheduler, get_scheduler_status, update_scheduler_settings, trigger_immediate_collection
    import pandas as pd
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORT_SUCCESS = False

# Add this after the imports and before any usage of load_upwork_data

def load_upwork_data():
    """Load Upwork jobs data from the raw_upwork_data.json file."""
    try:
        from config import DATA_PATHS
        upwork_data_file = DATA_PATHS.get('raw_upwork_data', 'data/raw_upwork_data.json')
        import os
        if not os.path.exists(upwork_data_file):
            return {}
        import json
        with open(upwork_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error loading Upwork data: {e}")
        return {}



def create_simple_jobs_csv(upwork_data: Dict[str, Any]) -> Optional[str]:
    """Create a simple CSV file with job data as fallback for Excel"""
    try:
        jobs = upwork_data.get('jobs', [])
        if not jobs:
            return None
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"upwork_jobs_{timestamp}.csv"
        filepath = os.path.join('data', filename)
        
        # Create CSV content
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            import csv
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['Title', 'Budget', 'URL', 'Skills', 'Posted Date', 'Location', 'Keyword'])
            
            # Data rows
            for job in jobs:
                writer.writerow([
                    job.get('title', 'N/A'),
                    job.get('budget', 'N/A'),
                    job.get('url', 'N/A'),
                    ', '.join(job.get('skills', [])),
                    job.get('posted_date', 'N/A'),
                    job.get('location', 'N/A'),
                    job.get('search_keyword', 'N/A')
                ])
        
        logger.info(f"📄 Created CSV file: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"❌ Error creating CSV file: {e}")
        return None




    """Create keyword frequency chart data for frontend"""
    try:
        # Use user's current keywords instead of defaults
        from keyword_manager import KeywordManager
        keyword_manager = KeywordManager()
        keywords = keyword_manager.get_keywords()
        
        # Fallback to data keywords or defaults if no user keywords
        if not keywords:
            keywords = data.get('keywords_analyzed', DEFAULT_KEYWORDS)
        
        reddit_counts = []
        google_counts = []
        youtube_counts = []
        twitter_counts = []
        
        for keyword in keywords:
            # Count Reddit posts
            reddit_posts = data.get('reddit_data', {}).get('posts', [])
            reddit_count = len([p for p in reddit_posts if p.get('search_keyword') == keyword])
            reddit_counts.append(reddit_count)
            
            # Count Google trends data points
            google_data = data.get('google_trends_data', {}).get('interest_data', [])
            google_count = len([g for g in google_data if keyword in str(g.get('values', {}))])
            google_counts.append(google_count)
            
            # Count YouTube videos
            youtube_videos = data.get('youtube_data', {}).get('videos', [])
            youtube_count = len([v for v in youtube_videos if v.get('search_keyword') == keyword])
            youtube_counts.append(youtube_count)
            
            # Count Twitter tweets
            twitter_tweets = data.get('twitter_data', [])
            twitter_count = len([t for t in twitter_tweets if t.get('keyword') == keyword])
            twitter_counts.append(twitter_count)
        
        return {
            'labels': keywords,
            'datasets': [
                {
                    'label': 'Reddit Posts',
                    'data': reddit_counts,
                    'backgroundColor': 'rgba(255, 99, 132, 0.8)',  # Bright red
                    'borderColor': 'rgba(255, 99, 132, 1)'
                },
                {
                    'label': 'Google Trends',
                    'data': google_counts,
                    'backgroundColor': 'rgba(54, 162, 235, 0.8)',  # Bright blue
                    'borderColor': 'rgba(54, 162, 235, 1)'
                },
                {
                    'label': 'YouTube Videos',
                    'data': youtube_counts,
                    'backgroundColor': 'rgba(255, 206, 86, 0.8)',  # Bright yellow
                    'borderColor': 'rgba(255, 206, 86, 1)'
                },
                {
                    'label': 'Twitter Posts',
                    'data': twitter_counts,
                    'backgroundColor': 'rgba(75, 192, 192, 0.8)',  # Teal
                    'borderColor': 'rgba(75, 192, 192, 1)'
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error creating keyword frequency chart data: {e}")
        return {'labels': [], 'datasets': []}

def create_google_trends_chart_data(data: dict) -> dict:
    """Create Google Trends chart data for frontend"""
    try:
        google_data = data.get('google_trends_data', {})
        interest_data = google_data.get('interest_data', [])
        
        if not interest_data:
            return {'labels': [], 'datasets': []}
        
        # Process data for chart
        dates = []
        keywords_data = {}
        
        for entry in interest_data:
            date = entry.get('date', '')
            if date:
                dates.append(date)
                values = entry.get('values', {})
                for keyword, value in values.items():
                    if keyword not in keywords_data:
                        keywords_data[keyword] = []
                    keywords_data[keyword].append(value if value > 0 else 0)
        
        # Create datasets
        datasets = []
        # Light, pleasant colors for Google Trends
        colors = [
            'rgba(134, 168, 231, 1)',   # Light blue
            'rgba(255, 159, 159, 1)',   # Light red/pink
            'rgba(144, 238, 144, 1)',   # Light green
            'rgba(255, 223, 129, 1)',   # Light orange/yellow
            'rgba(186, 159, 255, 1)',   # Light purple
            'rgba(255, 182, 193, 1)',   # Light pink
            'rgba(173, 216, 230, 1)',   # Light sky blue
            'rgba(221, 160, 221, 1)',   # Light orchid
            'rgba(255, 218, 185, 1)',   # Light peach
            'rgba(152, 251, 152, 1)'    # Light mint green
        ]
        
        for i, (keyword, values) in enumerate(keywords_data.items()):
            color_rgba = colors[i % len(colors)]
            # Create background color with transparency
            bg_color = color_rgba.replace('1)', '0.2)')
            
            datasets.append({
                'label': keyword,
                'data': values,
                'borderColor': color_rgba,
                'backgroundColor': bg_color,
                'fill': False,
                'tension': 0.4
            })
        
        return {
            'labels': dates,
            'datasets': datasets
        }
    except Exception as e:
        logger.error(f"Error creating Google Trends chart data: {e}")
        return {'labels': [], 'datasets': []}

def create_reddit_engagement_chart_data(data: dict) -> dict:
    """Create Reddit engagement chart data for frontend"""
    try:
        reddit_data = data.get('reddit_data', {})
        posts = reddit_data.get('posts', [])
        
        if not posts:
            return {'labels': [], 'datasets': []}
        
        # Calculate engagement metrics
        df = pd.DataFrame(posts)
        
        if df.empty:
            return {'labels': [], 'datasets': []}
        
        # Group by keyword
        keyword_metrics = df.groupby('search_keyword').agg({
            'score': ['mean', 'sum', 'count'],
            'num_comments': ['mean', 'sum'],
            'upvote_ratio': 'mean'
        }).round(2)
        
        # Flatten column names
        keyword_metrics.columns = ['_'.join(col).strip() for col in keyword_metrics.columns]
        keyword_metrics = keyword_metrics.reset_index()
        
        return {
            'labels': keyword_metrics['search_keyword'].tolist(),
            'datasets': [
                {
                    'label': 'Average Score',
                    'data': keyword_metrics['score_mean'].tolist(),
                    'backgroundColor': '#ff4500',
                    'borderColor': '#ff4500',
                    'borderWidth': 2
                },
                {
                    'label': 'Total Posts',
                    'data': keyword_metrics['score_count'].tolist(),
                    'backgroundColor': '#ff6b35',
                    'borderColor': '#ff6b35',
                    'borderWidth': 2
                },
                {
                    'label': 'Average Comments',
                    'data': keyword_metrics['num_comments_mean'].tolist(),
                    'backgroundColor': '#ff8500',
                    'borderColor': '#ff8500',
                    'borderWidth': 2
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error creating Reddit engagement chart data: {e}")
        return {'labels': [], 'datasets': []}

def create_youtube_engagement_chart_data(data: dict) -> dict:
    """Create YouTube engagement chart data for frontend"""
    try:
        youtube_data = data.get('youtube_data', {})
        videos = youtube_data.get('videos', [])
        
        if not videos:
            return {'labels': [], 'datasets': []}
        
        # Convert to DataFrame
        df = pd.DataFrame(videos)
        
        if df.empty:
            return {'labels': [], 'datasets': []}
        
        # Parse duration to seconds
        df['duration_seconds'] = df['duration'].apply(parse_youtube_duration)
        
        # Group by keyword
        keyword_metrics = df.groupby('search_keyword').agg({
            'view_count': ['mean', 'sum'],
            'like_count': ['mean', 'sum'],
            'comment_count': ['mean', 'sum'],
            'duration_seconds': 'mean'
        }).round(2)
        
        # Flatten column names
        keyword_metrics.columns = ['_'.join(col).strip() for col in keyword_metrics.columns]
        keyword_metrics = keyword_metrics.reset_index()
        
        return {
            'labels': keyword_metrics['search_keyword'].tolist(),
            'datasets': [
                {
                    'label': 'Average Views',
                    'data': keyword_metrics['view_count_mean'].tolist(),
                    'backgroundColor': '#36A2EB',  # Bright blue
                    'borderColor': '#36A2EB',
                    'borderWidth': 2
                },
                {
                    'label': 'Average Likes',
                    'data': keyword_metrics['like_count_mean'].tolist(),
                    'backgroundColor': '#FF6384',  # Bright red
                    'borderColor': '#FF6384',
                    'borderWidth': 2
                },
                {
                    'label': 'Average Comments',
                    'data': keyword_metrics['comment_count_mean'].tolist(),
                    'backgroundColor': '#4BC0C0',  # Teal
                    'borderColor': '#4BC0C0',
                    'borderWidth': 2
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error creating YouTube engagement chart data: {e}")
        return {'labels': [], 'datasets': []}

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configure logging with UTF-8 encoding to handle Unicode properly on Windows
import sys
import io

if sys.platform.startswith('win'):
    # For Windows, configure logging to handle unicode properly
    # Force UTF-8 encoding for console output
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(stream=sys.stdout),
            logging.FileHandler('scraping.log', encoding='utf-8')
        ]
    )
else:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global log queue for real-time streaming
log_queue = queue.Queue()
collection_active = False

class LogHandler(logging.Handler):
    """Custom log handler that adds logs to queue for streaming"""
    def emit(self, record):
        global log_queue
        try:
            msg = self.format(record)
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = {
                'timestamp': timestamp,
                'level': record.levelname,
                'message': msg,
                'module': record.name
            }
            log_queue.put(log_entry)
        except Exception:
            pass

# Add custom handler to specific loggers for data collection
log_handler = LogHandler()
log_handler.setFormatter(logging.Formatter('%(message)s'))

# Collection status tracking
collection_status = {
    'upwork': {
        'running': False,
        'completed': False,
        'start_time': None,
        'end_time': None,
        'jobs_count': 0,
        'error': None
    }
}

# Global cache for data to avoid reloading large files
_data_cache = {}
_cache_timestamp = 0

def invalidate_data_cache():
    """Invalidate the data cache to force fresh reload"""
    global _data_cache, _cache_timestamp
    _data_cache = {}
    _cache_timestamp = 0
    logger.info("🔄 Data cache invalidated - fresh data will be loaded")

def load_trending_analysis():
    """Load trending analysis data"""
    try:
        from config import DATA_PATHS
        trending_file = DATA_PATHS.get('trending_analysis', 'data/trending_analysis.json')
        if os.path.exists(trending_file):
            with open(trending_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                'trending_keywords': [],
                'analysis_timestamp': datetime.now().isoformat(),
                'total_count': 0
            }
    except Exception as e:
        logger.error(f"Error loading trending analysis: {e}")
        return {
            'trending_keywords': [],
            'analysis_timestamp': datetime.now().isoformat(),
            'total_count': 0
        }

def load_data():
    """Load data from JSON files with caching for performance"""
    global _data_cache, _cache_timestamp
    
    try:
        # Check if we need to refresh cache (cache for 30 seconds)
        current_time = time.time()
        if _data_cache and (current_time - _cache_timestamp) < 30:
            logger.debug("📊 Using cached data for better performance")
            return _data_cache
        
        logger.info("📊 Loading fresh data from files...")
        all_data = {}
        
        # Load Reddit data
        try:
            with open(DATA_PATHS['raw_reddit_data'], 'r', encoding='utf-8') as f:
                reddit_data = json.load(f)
                
                # Handle the nested keyword_posts structure
                if 'keyword_posts' in reddit_data:
                    all_posts = []
                    for keyword, posts in reddit_data['keyword_posts'].items():
                        all_posts.extend(posts)
                    reddit_data['posts'] = all_posts
                    
                all_data['reddit_data'] = reddit_data
        except FileNotFoundError:
            all_data['reddit_data'] = {}
        
        # Load YouTube data
        try:
            with open(DATA_PATHS['raw_youtube_data'], 'r', encoding='utf-8') as f:
                youtube_data = json.load(f)
                all_data['youtube_data'] = youtube_data
        except FileNotFoundError:
            all_data['youtube_data'] = {}
        
        # Load Twitter data
        try:
            with open(DATA_PATHS['raw_twitter_data'], 'r', encoding='utf-8') as f:
                twitter_data = json.load(f)
                if isinstance(twitter_data, list) and twitter_data and isinstance(twitter_data[0], str):
                    all_data['twitter_data'] = []
                elif isinstance(twitter_data, list):
                    all_data['twitter_data'] = twitter_data
                else:
                    all_data['twitter_data'] = []
        except FileNotFoundError:
            all_data['twitter_data'] = []
        
        # Load Google Trends data
        try:
            with open(DATA_PATHS['raw_google_data'], 'r', encoding='utf-8') as f:
                google_data = json.load(f)
                
                if 'interest_over_time' in google_data:
                    transformed_google = {
                        'interest_data': [],
                        'related_queries': []
                    }
                    
                    # Process interest over time data
                    for group_name, group_data in google_data['interest_over_time'].items():
                        data_points = group_data.get('data', [])
                        for point in data_points:
                            date = point.get('date', '')
                            values = {k: v for k, v in point.items() if k != 'date' and isinstance(v, (int, float))}
                            if values:
                                transformed_google['interest_data'].append({
                                    'date': date,
                                    'values': values
                                })
                    
                    all_data['google_trends_data'] = transformed_google
                else:
                    all_data['google_trends_data'] = google_data
                    
        except FileNotFoundError:
            all_data['google_trends_data'] = {}
        
        # Add metadata
        all_data['keywords_analyzed'] = DEFAULT_KEYWORDS
        all_data['creation_timestamp'] = datetime.now().isoformat()
        all_data['data_sources'] = []
        
        # Check which sources have data
        if all_data['reddit_data'].get('posts'):
            all_data['data_sources'].append('reddit')
        if all_data['youtube_data'].get('videos'):
            all_data['data_sources'].append('youtube')
        if all_data['twitter_data']:
            all_data['data_sources'].append('twitter')
        if all_data['google_trends_data'].get('interest_data'):
            all_data['data_sources'].append('google_trends')
        
        # Update cache for performance
        _data_cache = all_data
        _cache_timestamp = current_time
        
        logger.info(f"📊 Data cached for {len(all_data.get('data_sources', []))} sources")
        return all_data if all_data['data_sources'] else None
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None

def get_summary_stats():
    """Get summary statistics for the dashboard"""
    try:
        data = load_data()
        if not data:
            return {
                'total_keywords': 0,
                'reddit_posts': 0,
                'google_trends_count': 0,
                'youtube_videos': 0,
                'twitter_tweets': 0,
                'data_sources': [],
                'keywords_analyzed': []
            }
        
        return {
            'total_keywords': len(data.get('keywords_analyzed', [])),
            'reddit_posts': len(data.get('reddit_data', {}).get('posts', [])),
            'google_trends_count': len(data.get('google_trends_data', {}).get('interest_data', [])),
            'youtube_videos': len(data.get('youtube_data', {}).get('videos', [])),
            'twitter_tweets': len(data.get('twitter_data', [])),
            'data_sources': data.get('data_sources', []),
            'keywords_analyzed': data.get('keywords_analyzed', [])
        }
    except Exception as e:
        logger.error(f"Error getting summary stats: {e}")
        return {}

# Routes
@app.route('/')
def dashboard():
    """Main dashboard page with Upwork data"""
    upwork_data = load_upwork_data()
    
    # Calculate Upwork-specific stats
    jobs = upwork_data.get('jobs', []) if upwork_data else []
    keywords = set()
    total_budget = 0
    budget_count = 0
    for job in jobs:
        kw = job.get('search_keyword') or job.get('keyword')
        if kw:
            keywords.add(kw)
        # Try to get budget as a number
        budget = None
        if isinstance(job.get('budget'), dict):
            # Try min_amount or amount
            budget = job['budget'].get('min_amount') or job['budget'].get('amount')
        elif isinstance(job.get('budget'), (int, float)):
            budget = job['budget']
        if budget:
            try:
                total_budget += float(budget)
                budget_count += 1
            except Exception:
                pass
    avg_budget = round(total_budget / budget_count, 2) if budget_count else 0
    upwork_stats = {
        'total_jobs': len(jobs),
        'total_keywords': len(keywords),
        'avg_budget': avg_budget,
        'recent_jobs': len(jobs)
    }
    
    return render_template('dashboard.html', upwork_stats=upwork_stats, upwork_data=upwork_data)

@app.route('/api/data')
def api_data():
    """API endpoint to get all data"""
    data = load_data()
    if data:
        response = jsonify(data)
        return add_no_cache_headers(response)
    else:
        return jsonify({'error': 'No data available'}), 404

@app.route('/api/stats')
def api_stats():
    """API endpoint to get summary statistics"""
    stats = get_summary_stats()
    response = jsonify(stats)
    return add_no_cache_headers(response)



@app.route('/api/upwork')
def api_upwork():
    """API endpoint for Upwork jobs data"""
    data = load_upwork_data()
    if data:
        response = jsonify(data)
        return add_no_cache_headers(response)
    return jsonify({'error': 'No Upwork data available'}), 404

@app.route('/upwork')
def upwork_jobs():
    """Upwork jobs page"""
    upwork_data = load_upwork_data()

    # Calculate Upwork-specific stats
    jobs = upwork_data.get('jobs', []) if upwork_data else []
    keywords = set()
    total_budget = 0
    budget_count = 0
    for job in jobs:
        kw = job.get('search_keyword') or job.get('keyword')
        if kw:
            keywords.add(kw)
        # Try to get budget as a number
        budget = None
        if isinstance(job.get('budget'), dict):
            # Try min_amount or amount
            budget = job['budget'].get('min_amount') or job['budget'].get('amount')
        elif isinstance(job.get('budget'), (int, float)):
            budget = job['budget']
        if budget:
            try:
                total_budget += float(budget)
                budget_count += 1
            except Exception:
                pass
    avg_budget = round(total_budget / budget_count, 2) if budget_count else 0
    upwork_stats = {
        'total_jobs': len(jobs),
        'total_keywords': len(keywords),
        'avg_budget': avg_budget,
        'recent_jobs': len(jobs)
    }

    return render_template('upwork.html', 
                         upwork_data=upwork_data, 
                         upwork_stats=upwork_stats)

@app.route('/api/collect-upwork', methods=['POST'])
def api_collect_upwork():
    """API endpoint to trigger Upwork data collection with filters"""
    try:
        data = request.get_json()
        # Use dynamic keywords by default, fallback to provided keywords or DEFAULT_KEYWORDS
        dynamic_keywords = get_current_keywords()
        keywords = data.get('keywords', dynamic_keywords if dynamic_keywords else DEFAULT_KEYWORDS)
        method = data.get('method', 'selenium')  # 'selenium' (default)
        
        # Get enhanced filter options with new fields
        filters = data.get('filters', {
            'time_range': 'today',  # Changed default to 'today'
            'hourly_filter': '',  # NEW: Hourly time filter
            'budget_range': 'any',
            'job_type': 'any',
            'experience_level': 'any',
            'payment_status': 'both',  # NEW: Payment verification filter
            'sort_by': 'recency'
        })
        
        # Use persistence by default
        use_persistence = data.get('use_persistence', True)
        
        # Validate keywords
        if not keywords or not isinstance(keywords, list) or len(keywords) == 0:
            return jsonify({'error': 'No keywords provided'}), 400
        
        # Clean and validate keywords
        keywords = [kw.strip() for kw in keywords if kw and kw.strip()]
        if not keywords:
            return jsonify({'error': 'No valid keywords provided'}), 400
        
        logger.info(f"Received Upwork collection request with {len(keywords)} keywords: {keywords}")
        logger.info(f"Collection method: {method}")
        logger.info(f"Filters: {filters}")
        logger.info(f"Use persistence: {use_persistence}")
        
        # Reset status before starting new collection
        collection_status['upwork'] = {
            'running': False,
            'completed': False,
            'start_time': None,
            'end_time': None,
            'jobs_count': 0,
            'error': None,
            'filters_applied': filters
        }
        
        # Run Upwork data collection in a separate thread
        def collect_upwork_data():
            try:
                # Update status - collection starting
                collection_status['upwork'].update({
                    'running': True,
                    'completed': False,
                    'start_time': datetime.now().isoformat(),
                    'end_time': None,
                    'jobs_count': 0,
                    'error': None
                })
                
                logger.info(f"💼 Starting FILTERED Upwork data collection for: {keywords}")
                logger.info(f"🔍 Using filters: {filters}")
                
                # Use comprehensive individual page collection
                try:
                    # Try comprehensive individual page scraper first
                    try:
                        from fetch_upwork_data_enhanced import collect_comprehensive_upwork_data
                        logger.info("🎯 Using COMPREHENSIVE individual page Upwork scraper")
                        
                        # Set max jobs per keyword based on user preference or default to 5
                        max_jobs_per_keyword = data.get('max_jobs_per_keyword', 10)
                        logger.info(f"🔢 Max jobs per keyword: {max_jobs_per_keyword}")
                        
                        # Get skip_private_jobs setting (default: True)
                        skip_private_jobs = data.get('skip_private_jobs', True)
                        logger.info(f"🔒 Skip private jobs: {skip_private_jobs}")
                        
                        upwork_data = collect_comprehensive_upwork_data(
                            keywords=keywords, 
                            filters=filters, 
                            max_jobs_per_keyword=max_jobs_per_keyword,
                            use_persistence=use_persistence,
                            skip_private_jobs=skip_private_jobs
                        )
                        jobs_data = upwork_data.get('jobs', [])
                        logger.info(f"💾 COMPREHENSIVE data collection completed with {len(jobs_data)} jobs (premium quality)")
                        
                    except ImportError:
                        # Fallback to enhanced version
                        try:
                            from fetch_upwork_data_enhanced import collect_upwork_data_with_filters
                            logger.info("🔄 Comprehensive version not available, using enhanced version")
                            upwork_data = collect_upwork_data_with_filters(keywords, filters, use_persistence, max_jobs_per_keyword)
                            jobs_data = upwork_data.get('jobs', [])
                            logger.info(f"💾 Enhanced data collection completed with {len(jobs_data)} jobs")
                        except ImportError:
                            # Final fallback to original version
                            from fetch_upwork_data_enhanced import collect_comprehensive_upwork_data
                            logger.info("🔄 Enhanced version not available, using standard version")
                            upwork_data = collect_comprehensive_upwork_data(keywords, use_persistence=True, skip_private_jobs=True)
                            jobs_data = upwork_data.get('jobs', [])
                            logger.info(f"💾 Standard data collection completed with {len(jobs_data)} jobs")
                    
                    # Update status - collection completed successfully
                    collection_status['upwork'].update({
                        'running': False,
                        'completed': True,
                        'end_time': datetime.now().isoformat(),
                        'jobs_count': len(jobs_data),
                        'error': None
                    })
                    
                    # Invalidate cache so fresh data is shown immediately
                    invalidate_data_cache()
                    
                    logger.info(f"✅ FILTERED Upwork collection completed: {len(jobs_data)} jobs with filters {filters}")
                    
                except Exception as import_error:
                    logger.error(f"❌ Real scraper error: {import_error}")
                    logger.error("❌ CRITICAL: Real scraper failed - no fallback to dummy data!")
                    
                    # Update status - collection failed
                    collection_status['upwork'].update({
                        'running': False,
                        'completed': True,
                        'end_time': datetime.now().isoformat(),
                        'jobs_count': 0,
                        'error': str(import_error)
                    })
                
            except Exception as e:
                logger.error(f"❌ Upwork collection error: {e}")
                # Update status - collection failed
                collection_status['upwork'].update({
                    'running': False,
                    'completed': True,
                    'end_time': datetime.now().isoformat(),
                    'jobs_count': 0,
                    'error': str(e)
                })
                
        # Start collection in background
        collection_thread = threading.Thread(target=collect_upwork_data)
        collection_thread.daemon = True
        collection_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': f'REAL Upwork data collection started for {len(keywords)} keywords (100% genuine data only)',
            'keywords': keywords,
            'method': 'real_browser_guaranteed',
            'note': 'No simulated data - only real scraped jobs'
        })
        
    except Exception as e:
        logger.error(f"Upwork collection API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upwork-status', methods=['GET'])
def api_upwork_status():
    """Check Upwork collection status"""
    try:
        status = collection_status['upwork'].copy()
        
        # Add elapsed time if running
        if status['running'] and status['start_time']:
            start_time = datetime.fromisoformat(status['start_time'])
            elapsed = (datetime.now() - start_time).total_seconds()
            status['elapsed_seconds'] = int(elapsed)
            status['elapsed_formatted'] = f"{int(elapsed//60)}m {int(elapsed%60)}s"
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-upwork-excel')
def api_download_upwork_excel():
    """API endpoint to download the latest Upwork jobs Excel file"""
    try:
        # Try to get the latest Excel file
        try:
            from fetch_upwork_data_enhanced import get_latest_jobs_excel_path
            excel_path = get_latest_jobs_excel_path()
        except ImportError:
            return jsonify({'error': 'Enhanced Upwork module not available'}), 500
        
        if not excel_path or not os.path.exists(excel_path):
            return jsonify({'error': 'No Excel file found. Please collect data first.'}), 404
        
        # Get filename for download
        filename = os.path.basename(excel_path)
        
        logger.info(f"📊 Serving Excel file for download: {filename}")
        
        # Send file for download
        return send_file(
            excel_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Excel download error: {e}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/api/create-upwork-excel')
def api_create_upwork_excel():
    """API endpoint to create Excel file from current Upwork data"""
    try:
        # Load current Upwork data
        upwork_data = load_upwork_data()
        
        if not upwork_data or not upwork_data.get('jobs'):
            return jsonify({'error': 'No Upwork jobs data available. Please collect data first.'}), 404
        
        # Create Excel file with fallback approach
        excel_path = None
        try:
            from fetch_upwork_data_enhanced import create_jobs_excel_file
            excel_path = create_jobs_excel_file(upwork_data)
        except ImportError as e:
            logger.error(f"❌ Enhanced Upwork module not available: {e}")
            return jsonify({'error': 'Enhanced Upwork module not available'}), 500
        except Exception as e:
            logger.error(f"❌ Excel creation error: {e}")
            # Try simple CSV approach as fallback
            try:
                excel_path = create_simple_jobs_csv(upwork_data)
                logger.info("📊 Created CSV file as Excel fallback")
            except Exception as csv_error:
                logger.error(f"❌ CSV fallback also failed: {csv_error}")
                return jsonify({'error': f'Excel creation failed: {str(e)}'}), 500
        
        if not excel_path:
            return jsonify({'error': 'Failed to create Excel file'}), 500
        
        # Return success with download info
        return jsonify({
            'status': 'success',
            'message': 'Excel file created successfully',
            'filename': os.path.basename(excel_path),
            'jobs_count': len(upwork_data.get('jobs', [])),
            'download_url': '/api/download-upwork-excel'
        })
        
    except Exception as e:
        logger.error(f"Excel creation error: {e}")
        return jsonify({'error': f'Excel creation failed: {str(e)}'}), 500

@app.route('/api/trending')
def api_trending():
    """API endpoint for trending analysis"""
    try:
        trending_data = load_trending_analysis()
        if trending_data:
            response = jsonify(trending_data)
            return add_no_cache_headers(response)
        return jsonify({'error': 'No trending analysis available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trending/top')
def api_trending_top():
    """API endpoint for top trending keywords only"""
    try:
        trending_data = load_trending_analysis()
        if trending_data and trending_data.get('trending_keywords'):
            top_keywords = trending_data['trending_keywords'][:15]  # Top 15 for display
            return jsonify({
                'trending_keywords': top_keywords,
                'analysis_timestamp': trending_data.get('analysis_timestamp'),
                'total_count': len(trending_data.get('trending_keywords', []))
            })
        return jsonify({'error': 'No trending keywords available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """Server-Sent Events endpoint for real-time logs"""
    def generate():
        global collection_active
        while collection_active:
            try:
                # Wait for a log entry with timeout
                log_entry = log_queue.get(timeout=1)
                yield f"data: {json.dumps(log_entry)}\n\n"
            except queue.Empty:
                # Send keepalive ping
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            except Exception:
                break
    
    return Response(generate(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache',
                           'Connection': 'keep-alive'})

def run_data_collection_with_logging(keywords, sources):
    """Run data collection with real-time logging"""
    global collection_active, log_queue
    collection_active = True
    
    # Clear existing logs
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except queue.Empty:
            break
    
    # Add our custom handler to capture logs
    try:
        from fetch_google_data import logger as google_logger
        from fetch_reddit_data import logger as reddit_logger  
        from fetch_youtube_data import logger as youtube_logger
        from fetch_twitter_data import logger as twitter_logger
        from trending_analysis import logger as trending_logger
        
        loggers_to_hook = [google_logger, reddit_logger, youtube_logger, twitter_logger, trending_logger, logger]
        for lg in loggers_to_hook:
            lg.addHandler(log_handler)
    except ImportError:
        # Fallback if specific loggers not available
        logger.addHandler(log_handler)
    
    try:
        results = {}
        total_steps = len(sources) + 1  # +1 for trending analysis
        current_step = 0
        
        # Start message
        logger.info("STARTING data collection process...")
        logger.info(f"KEYWORDS: {', '.join(keywords)}")
        logger.info(f"SOURCES: {', '.join(sources)}")
        
        # Focus only on Upwork data collection for now
        if 'upwork' in sources:
            current_step += 1
            logger.info(f"STEP {current_step}/{total_steps}: Collecting Upwork jobs data...")
            try:
                # Use all keywords for Upwork
                logger.info(f"💼 Using all keywords for Upwork: {keywords}")
                
                upwork_data = collect_comprehensive_upwork_data(keywords, use_persistence=True, skip_private_jobs=True)
                if upwork_data and upwork_data.get('jobs'):
                    jobs_count = len(upwork_data.get('jobs', []))
                    logger.info(f"SUCCESS: Upwork data collection completed! Found {jobs_count} jobs")
                    results['upwork'] = {
                        'status': 'success',
                        'jobs_count': jobs_count
                    }
                else:
                    logger.warning("WARNING: Upwork data collection returned no data")
                    results['upwork'] = {'status': 'failed', 'error': 'No jobs returned'}
            except Exception as e:
                logger.error(f"ERROR: Upwork collection failed: {e}")
                results['upwork'] = {'status': 'error', 'error': str(e)}
        
        # Skip other sources for now - focus on Upwork only
        if 'google' in sources:
            logger.info("⚠️ Google Trends collection skipped - not implemented")
            results['google'] = {'status': 'skipped', 'message': 'Not implemented'}
        
        if 'reddit' in sources:
            logger.info("⚠️ Reddit collection skipped - not implemented")
            results['reddit'] = {'status': 'skipped', 'message': 'Not implemented'}
        
        if 'youtube' in sources:
            logger.info("⚠️ YouTube collection skipped - not implemented")
            results['youtube'] = {'status': 'skipped', 'message': 'Not implemented'}
        
        if 'twitter' in sources:
            logger.info("⚠️ Twitter collection skipped - not implemented")
            results['twitter'] = {'status': 'skipped', 'message': 'Not implemented'}
        
        # Skip trending analysis for now
        logger.info("⚠️ Trending analysis skipped - not implemented")
        results['trending_analysis'] = {'status': 'skipped', 'message': 'Not implemented'}
        
        # Calculate overall success
        successful_sources = [k for k, v in results.items() if v.get('status') == 'success']
        
        logger.info(f"COMPLETED: Data collection process completed!")
        logger.info(f"RESULTS: {len(successful_sources)}/{len(sources) + 1} sources successful")
        
        return results, successful_sources
        
    finally:
        # Remove handlers
        try:
            for lg in loggers_to_hook:
                lg.removeHandler(log_handler)
        except:
            logger.removeHandler(log_handler)
        collection_active = False

@app.route('/api/collect', methods=['POST'])
def api_collect():
    """API endpoint to trigger data collection with real-time logging"""
    try:
        data = request.get_json()
        # Use dynamic keywords by default, fallback to provided keywords or DEFAULT_KEYWORDS
        dynamic_keywords = get_current_keywords()
        keywords = data.get('keywords', dynamic_keywords if dynamic_keywords else DEFAULT_KEYWORDS)
        sources = data.get('sources', ['upwork'])
        
        # Validate keywords
        if not keywords or not isinstance(keywords, list) or len(keywords) == 0:
            return jsonify({'error': 'No keywords provided'}), 400
        
        # Clean and validate keywords
        keywords = [kw.strip() for kw in keywords if kw and kw.strip()]
        if not keywords:
            return jsonify({'error': 'No valid keywords provided'}), 400
        
        logger.info(f"Received collection request with {len(keywords)} keywords: {keywords}")
        logger.info(f"Sources requested: {sources}")
        
        # Run data collection in a separate thread to allow real-time logging
        def collect_data():
            try:
                result = run_data_collection_with_logging(keywords, sources)
                # Update collection timestamp after successful collection
                update_collection_timestamp()
                return result
            except Exception as e:
                logger.error(f"Thread error: {e}")
                return {}, []
        
        # Start collection in thread
        thread = threading.Thread(target=collect_data)
        thread.daemon = True
        thread.start()
        
        # Wait a moment to let collection start
        time.sleep(1.0)  # Increased wait time
        
        return jsonify({
            'status': 'started',
            'message': 'Data collection started. Connect to /api/logs for real-time progress.',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Data collection error: {e}")
        return jsonify({'error': str(e)}), 500



# ===== KEYWORD MANAGEMENT API ENDPOINTS =====

@app.route('/api/keywords', methods=['GET'])
def api_get_keywords():
    """Get current keywords and information"""
    try:
        keywords_info = keyword_manager.get_keywords_info()
        response = jsonify(keywords_info)
        return add_no_cache_headers(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords', methods=['POST'])
def api_set_keywords():
    """Set/update keywords"""
    try:
        data = request.get_json()
        if not data or 'keywords' not in data:
            return jsonify({'error': 'Keywords required'}), 400
        
        result = keyword_manager.set_keywords(data['keywords'])
        
        if result['success']:
            response = jsonify(result)
            return add_no_cache_headers(response)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords/add', methods=['POST'])
def api_add_keyword():
    """Add a single keyword"""
    try:
        data = request.get_json()
        if not data or 'keyword' not in data:
            return jsonify({'error': 'Keyword required'}), 400
        
        result = keyword_manager.add_keyword(data['keyword'])
        
        if result['success']:
            response = jsonify(result)
            return add_no_cache_headers(response)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords/remove', methods=['POST'])
def api_remove_keyword():
    """Remove a keyword"""
    try:
        data = request.get_json()
        if not data or 'keyword' not in data:
            return jsonify({'error': 'Keyword required'}), 400
        
        result = keyword_manager.remove_keyword(data['keyword'])
        
        if result['success']:
            response = jsonify(result)
            return add_no_cache_headers(response)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords/reset', methods=['POST'])
def api_reset_keywords():
    """Reset keywords to defaults"""
    try:
        result = keyword_manager.reset_to_defaults()
        response = jsonify(result)
        return add_no_cache_headers(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords/validate', methods=['POST'])
def api_validate_keywords():
    """Validate keywords without saving"""
    try:
        data = request.get_json()
        if not data or 'keywords' not in data:
            return jsonify({'error': 'Keywords required'}), 400
        
        result = keyword_manager.validate_keywords(data['keywords'])
        response = jsonify(result)
        return add_no_cache_headers(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== SCHEDULER API ENDPOINTS =====

@app.route('/api/scheduler/status', methods=['GET'])
def api_scheduler_status():
    """Get scheduler status and statistics"""
    try:
        status = get_scheduler_status()
        response = jsonify(status)
        return add_no_cache_headers(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/settings', methods=['POST'])
def api_scheduler_settings():
    """Update scheduler settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Settings data required'}), 400
        
        # Extract settings
        enabled = data.get('enabled')
        sources = data.get('sources')
        interval_minutes = data.get('interval_minutes')
        
        # Validate interval
        if interval_minutes is not None:
            if not isinstance(interval_minutes, int) or interval_minutes < 5 or interval_minutes > 1440:
                return jsonify({'error': 'Interval must be between 5 and 1440 minutes'}), 400
        
        # Validate sources
        if sources is not None:
            valid_sources = ['google', 'reddit', 'youtube', 'twitter']
            if not isinstance(sources, list) or not all(s in valid_sources for s in sources):
                return jsonify({'error': f'Sources must be a list from: {valid_sources}'}), 400
        
        # Update settings
        update_scheduler_settings(
            enabled=enabled,
            sources=sources,
            interval_minutes=interval_minutes
        )
        
        response = jsonify({
            'success': True,
            'message': 'Scheduler settings updated successfully'
        })
        return add_no_cache_headers(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/trigger', methods=['POST'])
def api_scheduler_trigger():
    """Trigger immediate data collection"""
    try:
        success = trigger_immediate_collection()
        
        if success:
            response = jsonify({
                'success': True,
                'message': 'Immediate data collection triggered'
            })
            return add_no_cache_headers(response)
        else:
            return jsonify({'error': 'Failed to trigger collection'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/settings')
def settings():
    """Settings page for configuration"""
    return render_template('settings.html')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

# Health check endpoints for Render
@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/trigger-collection')
def manual_trigger():
    """Manual trigger endpoint for testing"""
    try:
        from keyword_manager import get_current_keywords
        keywords = get_current_keywords() or DEFAULT_KEYWORDS
        
        # Start collection in background thread
        def trigger_collection():
            try:
                run_data_collection_with_logging(keywords, ['google', 'reddit', 'youtube', 'twitter'])
            except Exception as e:
                logger.error(f"Manual collection error: {e}")
        
        thread = threading.Thread(target=trigger_collection, daemon=True)
        thread.start()
        
        return jsonify({
            'status': 'triggered',
            'message': 'Data collection started',
            'keywords': keywords
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_upwork_only_collection(keywords):
    """Run ONLY Upwork data collection - no other sources"""
    global collection_active, log_queue
    collection_active = True
    
    # Clear existing logs
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except queue.Empty:
            break
    
    try:
        logger.info("🚀 STARTING UPWORK-ONLY data collection...")
        logger.info(f"💼 KEYWORDS: {', '.join(keywords)}")
        logger.info("🎯 SOURCE: Upwork only")
        
        # Import Upwork collection function
        try:
            from fetch_upwork_data_enhanced import collect_comprehensive_upwork_data
            logger.info("🎯 Using COMPREHENSIVE Upwork scraper")
            
            # Use default settings for scheduler
            upwork_data = collect_comprehensive_upwork_data(
                keywords=keywords, 
                filters=None,  # No filters for scheduler
                                        max_jobs_per_keyword=10,  # Default 10 jobs per keyword
                use_persistence=True,
                skip_private_jobs=True
            )
            
            jobs_data = upwork_data.get('jobs', [])
            logger.info(f"✅ UPWORK collection completed: {len(jobs_data)} jobs")
            
            # Invalidate cache so fresh data is shown immediately
            invalidate_data_cache()
            
            return {
                'upwork': {
                    'status': 'success',
                    'jobs_count': len(jobs_data),
                    'saved': True
                }
            }, ['upwork']
            
        except ImportError:
            # Fallback to enhanced version
            try:
                from fetch_upwork_data_enhanced import collect_upwork_data_with_filters
                logger.info("🔄 Using enhanced Upwork scraper")
                upwork_data = collect_upwork_data_with_filters(keywords, None, True, 5)
                jobs_data = upwork_data.get('jobs', [])
                logger.info(f"✅ UPWORK collection completed: {len(jobs_data)} jobs")
                
                invalidate_data_cache()
                
                return {
                    'upwork': {
                        'status': 'success',
                        'jobs_count': len(jobs_data),
                        'saved': True
                    }
                }, ['upwork']
                
            except ImportError:
                # Final fallback to original version
                from fetch_upwork_data_enhanced import collect_comprehensive_upwork_data
                logger.info("🔄 Using standard Upwork scraper")
                upwork_data = collect_comprehensive_upwork_data(keywords, use_persistence=True, skip_private_jobs=True)
                jobs_data = upwork_data.get('jobs', [])
                logger.info(f"✅ UPWORK collection completed: {len(jobs_data)} jobs")
                
                invalidate_data_cache()
                
                return {
                    'upwork': {
                        'status': 'success',
                        'jobs_count': len(jobs_data),
                        'saved': True
                    }
                }, ['upwork']
                
    except Exception as e:
        logger.error(f"❌ UPWORK collection failed: {e}")
        return {
            'upwork': {
                'status': 'error',
                'error': str(e),
                'jobs_count': 0
            }
        }, []

# ===== DELETE ALL UPWORK JOBS ENDPOINT =====
@app.route('/api/delete-upwork-jobs', methods=['POST'])
def api_delete_upwork_jobs():
    """Delete all Upwork jobs data (dangerous action)"""
    try:
        from config import DATA_PATHS
        upwork_data_file = DATA_PATHS.get('raw_upwork_data', 'data/raw_upwork_data.json')
        # Overwrite with empty jobs list and minimal metadata
        empty_data = {
            'jobs': [],
            'metadata': {
                'total_jobs': 0,
                'keywords_analyzed': [],
                'collection_timestamp': datetime.now().isoformat(),
                'data_source': 'manual_delete',
                'deleted': True
            }
        }
        with open(upwork_data_file, 'w', encoding='utf-8') as f:
            json.dump(empty_data, f, indent=2, ensure_ascii=False)
        invalidate_data_cache()
        return jsonify({'status': 'success', 'message': 'All Upwork jobs deleted.'})
    except Exception as e:
        logger.error(f"Failed to delete Upwork jobs: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # This block only runs for local development
    # Production uses app.py as entry point
    
    # Ensure templates and static directories exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/img', exist_ok=True)
    
    # Use port 5000 as requested
    print("Starting Flask Dashboard (Local Development)...")
    print("Access your dashboard at: http://localhost:5000")
    print("All your existing data and business logic preserved!")
    
    # Start the automated scheduler for local development
    try:
        from scheduler import start_scheduler, update_scheduler_settings
        # Configure scheduler for Upwork-only with 2-hour intervals
        update_scheduler_settings(
            enabled=True,
            sources=['upwork'],
            interval_minutes=120
        )
        start_scheduler()
        print("✅ Automated Upwork scheduler started (2-hour intervals)")
        print("📋 Will collect jobs from keywords.txt file")
    except Exception as e:
        print(f"❌ Warning: Could not start scheduler: {e}")
        print("💡 You can start it manually with: python start_scheduler_auto.py")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 
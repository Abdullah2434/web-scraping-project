"""
Flask Dashboard for Keyword Trends Analysis
==========================================

Modern web dashboard for analyzing keyword trends across multiple platforms.
Converts the Streamlit app to Flask with professional frontend.

Author: Web Scraping Project
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, Response
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

# Import data collection modules and chart functions
try:
    from fetch_google_data import collect_all_google_data
    from fetch_reddit_data import collect_all_reddit_data
    from fetch_youtube_data import collect_all_youtube_data
    from fetch_twitter_data import collect_all_twitter_data
    from fetch_upwork_data import collect_all_upwork_data, load_upwork_data, get_upwork_summary_stats
    from trending_analysis import run_automatic_trending_analysis, load_trending_analysis
    from keyword_manager import keyword_manager, get_current_keywords, update_collection_timestamp
    from scheduler import start_scheduler, stop_scheduler, get_scheduler_status, update_scheduler_settings, trigger_immediate_collection
    import pandas as pd
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORT_SUCCESS = False

# Parse YouTube duration function (from Streamlit app)
def parse_youtube_duration(duration_str: str) -> int:
    """Parse YouTube PT duration format to seconds"""
    if not duration_str or not duration_str.startswith('PT'):
        return 0
    
    # Remove PT prefix
    duration = duration_str[2:]
    
    # Parse hours, minutes, seconds
    hours = 0
    minutes = 0
    seconds = 0
    
    if 'H' in duration:
        hours_part = duration.split('H')[0]
        hours = int(hours_part) if hours_part.isdigit() else 0
        duration = duration.split('H')[1]
    
    if 'M' in duration:
        minutes_part = duration.split('M')[0]
        minutes = int(minutes_part) if minutes_part.isdigit() else 0
        duration = duration.split('M')[1]
    
    if 'S' in duration:
        seconds_part = duration.split('S')[0]
        seconds = int(seconds_part) if seconds_part.isdigit() else 0
    
    return hours * 3600 + minutes * 60 + seconds

def collect_youtube_data_with_timeout(keywords, timeout_seconds=60):
    """
    Collect YouTube data with timeout protection for Flask context
    
    Args:
        keywords: List of keywords to search
        timeout_seconds: Maximum time to wait (default 1 minute)
        
    Returns:
        Dict: YouTube data or empty dict if timeout/error
    """
    from queue import Queue, Empty
    import threading
    import signal
    
    logger.info(f"🔄 Starting YouTube collection with {timeout_seconds}s timeout for {len(keywords)} keywords")
    
    def target_function(result_queue, keywords_list):
        """Target function to run in timeout context"""
        try:
            # Check dependencies first
            try:
                import googleapiclient.discovery
                import googleapiclient.errors
            except ImportError as e:
                logger.error(f"❌ YouTube API dependencies missing: {e}")
                result_queue.put(('error', 'YouTube API dependencies not installed'))
                return
            
            logger.info(f"🎥 Thread starting YouTube collection for: {keywords_list}")
            youtube_data = collect_all_youtube_data(keywords_list)
            logger.info(f"🎥 Thread completed YouTube collection")
            result_queue.put(('success', youtube_data))
        except Exception as e:
            logger.error(f"🎥 Thread error in YouTube collection: {e}")
            result_queue.put(('error', str(e)))
    
    # Use threading with timeout for YouTube collection
    result_queue = Queue()
    collection_thread = threading.Thread(
        target=target_function,
        args=(result_queue, keywords),
        daemon=True,
        name="YouTubeCollectionThread"
    )
    
    try:
        logger.info(f"🚀 Starting YouTube collection thread...")
        collection_thread.start()
        
        logger.info(f"⏳ Waiting for YouTube collection (max {timeout_seconds}s)...")
        
        # Wait with periodic checks
        wait_time = 0
        check_interval = 5  # Check every 5 seconds
        
        while wait_time < timeout_seconds:
            collection_thread.join(timeout=check_interval)
            wait_time += check_interval
            
            if not collection_thread.is_alive():
                break
                
            logger.info(f"⏳ YouTube collection still running... ({wait_time}s/{timeout_seconds}s)")
        
        if collection_thread.is_alive():
            logger.error(f"⏰ YouTube collection timed out after {timeout_seconds} seconds")
            logger.error(f"🧵 Forcing thread termination, returning empty data")
            return {}
        
        # Get result from queue
        try:
            logger.info(f"📥 Getting result from YouTube collection queue...")
            status, result = result_queue.get_nowait()
            if status == 'success':
                videos_count = len(result.get('videos', [])) if result else 0
                logger.info(f"✅ YouTube collection completed successfully ({videos_count} videos)")
                return result
            else:
                logger.error(f"❌ YouTube collection failed: {result}")
                return {}
        except Empty:
            logger.error("❌ No result available from YouTube collection queue")
            return {}
            
    except Exception as e:
        logger.error(f"❌ Error in YouTube timeout wrapper: {e}")
        return {}

# Chart creation functions (from Streamlit app)
def create_keyword_frequency_chart_data(data: dict) -> dict:
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

# Configure logging with UTF-8 encoding to handle emojis in Windows
import sys
if sys.platform.startswith('win'):
    # For Windows, configure logging to handle unicode properly
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

def load_data():
    """Load data from JSON files - same logic as Streamlit app"""
    try:
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
    """Main dashboard page with trending keywords"""
    stats = get_summary_stats()
    
    # Load trending analysis for main dashboard
    try:
        trending_data = load_trending_analysis()
        top_trending = []
        if trending_data and trending_data.get('trending_keywords'):
            # Get top 10 trending keywords for dashboard
            top_trending = trending_data['trending_keywords'][:10]
    except Exception as e:
        logger.error(f"Error loading trending data for dashboard: {e}")
        top_trending = []
    
    return render_template('dashboard.html', stats=stats, trending_keywords=top_trending)

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

@app.route('/api/reddit')
def api_reddit():
    """API endpoint for Reddit data"""
    data = load_data()
    if data and 'reddit_data' in data:
        return jsonify(data['reddit_data'])
    return jsonify({'error': 'No Reddit data available'}), 404

@app.route('/api/youtube')
def api_youtube():
    """API endpoint for YouTube data"""
    data = load_data()
    if data and 'youtube_data' in data:
        return jsonify(data['youtube_data'])
    return jsonify({'error': 'No YouTube data available'}), 404

@app.route('/api/twitter')
def api_twitter():
    """API endpoint for Twitter data"""
    data = load_data()
    if data and 'twitter_data' in data:
        return jsonify(data['twitter_data'])
    return jsonify({'error': 'No Twitter data available'}), 404

@app.route('/api/google-trends')
def api_google_trends():
    """API endpoint for Google Trends data"""
    data = load_data()
    if data and 'google_trends_data' in data:
        return jsonify(data['google_trends_data'])
    return jsonify({'error': 'No Google Trends data available'}), 404

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
    upwork_stats = get_upwork_summary_stats()
    
    return render_template('upwork.html', 
                         upwork_data=upwork_data, 
                         upwork_stats=upwork_stats)

@app.route('/api/collect-upwork', methods=['POST'])
def api_collect_upwork():
    """API endpoint to trigger Upwork data collection specifically"""
    try:
        data = request.get_json()
        # Use dynamic keywords by default, fallback to provided keywords or DEFAULT_KEYWORDS
        dynamic_keywords = get_current_keywords()
        keywords = data.get('keywords', dynamic_keywords if dynamic_keywords else DEFAULT_KEYWORDS)
        method = data.get('method', 'simulated')  # 'simulated', 'selenium', or 'manual'
        
        # Validate keywords
        if not keywords or not isinstance(keywords, list) or len(keywords) == 0:
            return jsonify({'error': 'No keywords provided'}), 400
        
        # Clean and validate keywords
        keywords = [kw.strip() for kw in keywords if kw and kw.strip()]
        if not keywords:
            return jsonify({'error': 'No valid keywords provided'}), 400
        
        logger.info(f"Received Upwork collection request with {len(keywords)} keywords: {keywords}")
        logger.info(f"Collection method: {method}")
        
        # Reset status before starting new collection
        collection_status['upwork'] = {
            'running': False,
            'completed': False,
            'start_time': None,
            'end_time': None,
            'jobs_count': 0,
            'error': None
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
                
                logger.info(f"💼 Starting REAL Upwork data collection for: {keywords}")
                
                # ALWAYS use real browser automation - no simulated data
                try:
                    from fetch_upwork_data import collect_all_upwork_data
                    logger.info("🎯 Using 100% real browser automation with file saving")
                    upwork_data = collect_all_upwork_data(keywords, use_real_browser=True)
                    jobs_data = upwork_data.get('jobs', [])
                    
                    logger.info(f"💾 Data automatically saved to file with {len(jobs_data)} jobs")
                    
                    # Update status - collection completed successfully
                    collection_status['upwork'].update({
                        'running': False,
                        'completed': True,
                        'end_time': datetime.now().isoformat(),
                        'jobs_count': len(jobs_data),
                        'error': None
                    })
                    
                    logger.info(f"✅ REAL Upwork collection completed: {len(jobs_data)} genuine jobs")
                    
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
        
        if 'google' in sources:
            current_step += 1
            logger.info(f"STEP {current_step}/{total_steps}: Collecting Google Trends data...")
            try:
                # Use all keywords for Google Trends
                logger.info(f"📊 Using all keywords for Google Trends: {keywords}")
                
                google_data = collect_all_google_data(keywords)
                if google_data:
                    # Save Google data to file
                    from fetch_google_data import save_google_data
                    save_success = save_google_data(google_data)
                    logger.info(f"SUCCESS: Google Trends data collection completed! Saved: {save_success}")
                    results['google'] = {
                        'status': 'success',
                        'data_points': len(google_data.get('interest_over_time', {})),
                        'saved': save_success
                    }
                else:
                    logger.warning("WARNING: Google Trends data collection returned no data")
                    results['google'] = {'status': 'failed', 'error': 'No data returned'}
            except Exception as e:
                logger.error(f"ERROR: Google Trends collection failed: {e}")
                results['google'] = {'status': 'error', 'error': str(e)}
        
        if 'reddit' in sources:
            current_step += 1
            logger.info(f"STEP {current_step}/{total_steps}: Collecting Reddit data...")
            try:
                # Use all keywords for Reddit
                logger.info(f"🤖 Using all keywords for Reddit: {keywords}")
                
                reddit_data = collect_all_reddit_data(keywords)
                if reddit_data and not reddit_data.get('error'):
                    # Save Reddit data to file
                    from fetch_reddit_data import save_reddit_data
                    save_success = save_reddit_data(reddit_data)
                    # Transform posts for counting
                    posts_count = 0
                    if 'keyword_posts' in reddit_data:
                        posts_count = sum(len(posts) if isinstance(posts, list) else 0 
                                        for posts in reddit_data['keyword_posts'].values())
                    logger.info(f"SUCCESS: Reddit data collection completed! Found {posts_count} posts, Saved: {save_success}")
                    results['reddit'] = {
                        'status': 'success',
                        'posts_count': posts_count,
                        'saved': save_success
                    }
                else:
                    error_msg = reddit_data.get('error', 'No data returned') if reddit_data else 'No data returned'
                    logger.warning(f"WARNING: Reddit data collection failed: {error_msg}")
                    results['reddit'] = {'status': 'failed', 'error': error_msg}
            except Exception as e:
                logger.error(f"ERROR: Reddit collection failed: {e}")
                results['reddit'] = {'status': 'error', 'error': str(e)}
        
        if 'youtube' in sources:
            current_step += 1
            logger.info(f"STEP {current_step}/{total_steps}: Collecting YouTube data...")
            try:
                # Check if YouTube dependencies are available
                try:
                    import googleapiclient.discovery
                    import googleapiclient.errors
                    deps_available = True
                except ImportError:
                    deps_available = False
                    logger.warning("WARNING: YouTube API dependencies not installed")
                    logger.warning("RUN: python install_youtube_deps.py to install dependencies")
                
                if deps_available:
                    logger.info("📺 Starting YouTube data collection...")
                    logger.info(f"Using keywords for YouTube: {keywords}")
                    logger.info("⚠️ If this hangs, YouTube API may be unresponsive. Will timeout in 60 seconds.")
                    
                    # Call YouTube collection with timeout protection
                    youtube_data = collect_youtube_data_with_timeout(keywords, timeout_seconds=60)
                    
                    if youtube_data and youtube_data.get('videos'):
                        videos_count = len(youtube_data.get('videos', []))
                        logger.info(f"SUCCESS: YouTube data collection completed! Found {videos_count} videos")
                        # Save YouTube data
                        try:
                            from fetch_youtube_data import save_youtube_data
                            save_success = save_youtube_data(youtube_data)
                            logger.info(f"YouTube data saved: {save_success}")
                        except Exception as save_error:
                            logger.warning(f"Failed to save YouTube data: {save_error}")
                        
                        results['youtube'] = {
                            'status': 'success',
                            'videos_count': videos_count
                        }
                    else:
                        logger.warning("WARNING: YouTube data collection returned no data or timed out")
                        results['youtube'] = {'status': 'failed', 'error': 'No data returned or timeout'}
                else:
                    logger.error("ERROR: YouTube API dependencies missing")
                    results['youtube'] = {
                        'status': 'error', 
                        'error': 'YouTube API dependencies not installed. Run: python install_youtube_deps.py'
                    }
            except Exception as e:
                logger.error(f"ERROR: YouTube collection failed: {e}")
                results['youtube'] = {'status': 'error', 'error': str(e)}
        
        if 'twitter' in sources:
            current_step += 1
            logger.info(f"STEP {current_step}/{total_steps}: Collecting Twitter data...")
            try:
                # Use all keywords for Twitter
                logger.info(f"🐦 Using all keywords for Twitter: {keywords}")
                
                twitter_data = collect_all_twitter_data(keywords)
                if twitter_data and isinstance(twitter_data, list) and len(twitter_data) > 0:
                    # Save Twitter data to file (wrap list in dict format expected by save function)
                    from fetch_twitter_data import save_twitter_data
                    twitter_data_dict = {
                        'tweets': twitter_data,
                        'collection_timestamp': datetime.now().isoformat(),
                        'keywords': keywords
                    }
                    save_success = save_twitter_data(twitter_data_dict)
                    tweets_count = len(twitter_data)
                    logger.info(f"SUCCESS: Twitter data collection completed! Found {tweets_count} tweets, Saved: {save_success}")
                    results['twitter'] = {
                        'status': 'success',
                        'tweets_count': tweets_count,
                        'saved': save_success
                    }
                else:
                    logger.warning("WARNING: Twitter data collection returned no data")
                    results['twitter'] = {'status': 'failed', 'error': 'No valid tweets returned'}
            except Exception as e:
                logger.error(f"ERROR: Twitter collection failed: {e}")
                results['twitter'] = {'status': 'error', 'error': str(e)}
        
        if 'upwork' in sources:
            current_step += 1
            logger.info(f"STEP {current_step}/{total_steps}: Collecting Upwork jobs data...")
            try:
                # Use all keywords for Upwork
                logger.info(f"💼 Using all keywords for Upwork: {keywords}")
                
                upwork_data = collect_all_upwork_data(keywords)
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
        
        # Run data cleaning and trending analysis
        current_step += 1
        logger.info(f"STEP {current_step}/{total_steps}: Running data cleaning and trending analysis...")
        try:
            # Run data cleaning first to update cleaned_data.json
            try:
                from clean_data import main as clean_data_main
                logger.info("📊 Running data cleaning process...")
                clean_data_main()
                logger.info("✅ Data cleaning completed")
            except Exception as clean_error:
                logger.warning(f"⚠️ Data cleaning failed: {clean_error}")
            
            # Run trending analysis
            logger.info("🔥 Running trending analysis...")
            analysis_report = run_automatic_trending_analysis()
            results['trending_analysis'] = {
                'status': 'success' if analysis_report else 'failed',
                'keywords_found': len(analysis_report.get('trending_keywords', [])) if analysis_report else 0
            }
            if analysis_report:
                keywords_found = len(analysis_report.get('trending_keywords', []))
                logger.info(f"SUCCESS: Trending analysis completed! Found {keywords_found} trending keywords")
            else:
                logger.warning("WARNING: Trending analysis returned no results")
        except Exception as e:
            logger.error(f"ERROR: Trending analysis failed: {e}")
            results['trending_analysis'] = {'status': 'error', 'error': str(e)}
        
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
        sources = data.get('sources', ['google', 'reddit', 'youtube', 'twitter', 'upwork'])
        
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

# Chart data endpoints
@app.route('/api/charts/keyword-frequency')
def api_keyword_frequency_chart():
    """API endpoint for keyword frequency chart data"""
    try:
        data = load_data()
        if not data:
            return jsonify({'error': 'No data available'}), 404
        
        chart_data = create_keyword_frequency_chart_data(data)
        return jsonify(chart_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/google-trends')
def api_google_trends_chart():
    """API endpoint for Google Trends chart data"""
    try:
        data = load_data()
        if not data:
            return jsonify({'error': 'No data available'}), 404
        
        chart_data = create_google_trends_chart_data(data)
        return jsonify(chart_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/reddit-engagement')
def api_reddit_engagement_chart():
    """API endpoint for Reddit engagement chart data"""
    try:
        data = load_data()
        if not data:
            return jsonify({'error': 'No data available'}), 404
        
        chart_data = create_reddit_engagement_chart_data(data)
        return jsonify(chart_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/youtube-engagement')
def api_youtube_engagement_chart():
    """API endpoint for YouTube engagement chart data"""
    try:
        data = load_data()
        if not data:
            return jsonify({'error': 'No data available'}), 404
        
        chart_data = create_youtube_engagement_chart_data(data)
        return jsonify(chart_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-activity')
def api_recent_activity():
    """API endpoint for recent activity data"""
    try:
        data = load_data()
        if not data:
            return jsonify({'error': 'No data available'}), 404
        
        # Get recent Reddit posts (top 5 by score)
        reddit_posts = data.get('reddit_data', {}).get('posts', [])
        recent_reddit = sorted(reddit_posts, key=lambda x: x.get('score', 0), reverse=True)[:5]
        
        # Get recent YouTube videos (top 5 by views)
        youtube_videos = data.get('youtube_data', {}).get('videos', [])
        recent_youtube = sorted(youtube_videos, key=lambda x: int(x.get('view_count', 0)), reverse=True)[:5]
        
        # Get recent Twitter posts (top 5 by likes)
        twitter_tweets = data.get('twitter_data', [])
        recent_twitter = sorted(twitter_tweets, key=lambda x: x.get('like_count', 0), reverse=True)[:5]
        
        response = jsonify({
            'reddit': recent_reddit,
            'youtube': recent_youtube,
            'twitter': recent_twitter
        })
        return add_no_cache_headers(response)
    except Exception as e:
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

@app.route('/reddit')
def reddit_page():
    """Reddit data page"""
    return render_template('data_source.html', source='reddit', title='Reddit Posts Analysis')

@app.route('/youtube')
def youtube_page():
    """YouTube data page"""
    return render_template('data_source.html', source='youtube', title='YouTube Videos Analysis')

@app.route('/twitter')
def twitter_page():
    """Twitter data page"""
    return render_template('data_source.html', source='twitter', title='Twitter Posts Analysis')

@app.route('/google-trends')
def google_trends_page():
    """Google Trends data page"""
    return render_template('data_source.html', source='google', title='Google Trends Analysis')

@app.route('/trending-analysis')
def trending_analysis_page():
    """Trending Analysis page"""
    return render_template('trending_analysis.html')

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

if __name__ == '__main__':
    # This block only runs for local development
    # Production uses app.py as entry point
    
    # Ensure templates and static directories exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/img', exist_ok=True)
    
    # Use port 8080 to avoid Windows port 5000 restrictions
    print("🚀 Starting Flask Dashboard (Local Development)...")
    print("📊 Access your dashboard at: http://localhost:8080")
    print("⚙️  All your existing data and business logic preserved!")
    
    # Start the automated scheduler for local development
    try:
        start_scheduler()
        print("⏰ Automated data collection scheduler started")
    except Exception as e:
        print(f"⚠️ Warning: Could not start scheduler: {e}")
    
    app.run(debug=True, host='127.0.0.1', port=8080) 
"""
Configuration file for the Web Scraping Project
Contains all settings, database connections, and API configurations
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===== GENERAL SETTINGS =====
# Default keywords to search (you can modify this list)
DEFAULT_KEYWORDS = [
    "climate change",
    "cryptocurrency", 
    "space exploration",
    "renewable energy",
    "AI"
]

# Data collection settings
MAX_REDDIT_POSTS = 50  # Maximum number of Reddit posts to fetch per keyword
MAX_YOUTUBE_VIDEOS = 50  # Maximum number of YouTube videos to fetch per keyword
MAX_TWITTER_TWEETS = 10  # Reduced to avoid rate limits
GOOGLE_TRENDS_TIMEFRAME = 'today 12-m'  # Last 12 months (will give ~365+ data points)
GOOGLE_TRENDS_REGION = 'US'  # Region for Google Trends (US, PK, UK, etc.)

# ===== REDDIT API SETTINGS =====
# Reddit API credentials (get these from https://www.reddit.com/prefs/apps)
REDDIT_CONFIG = {
    'client_id': os.getenv('REDDIT_CLIENT_ID', 'your_client_id_here'),
    'client_secret': os.getenv('REDDIT_CLIENT_SECRET', 'your_client_secret_here'),
    'user_agent': os.getenv('REDDIT_USER_AGENT', 'keyword_scraper_bot_1.0'),
    'username': os.getenv('REDDIT_USERNAME', ''),  # Optional: for authenticated requests
    'password': os.getenv('REDDIT_PASSWORD', '')   # Optional: for authenticated requests
}

# Reddit search settings
REDDIT_SETTINGS = {
    'subreddits': ['all'],  # Subreddits to search (or ['all'] for all subreddits)
    'time_filter': 'week',  # Options: 'hour', 'day', 'week', 'month', 'year', 'all'
    'sort': 'hot',          # Options: 'hot', 'new', 'top', 'rising'
    'limit': MAX_REDDIT_POSTS
}

# ===== YOUTUBE API SETTINGS =====
# YouTube Data API v3 credentials (get from Google Cloud Console)
YOUTUBE_CONFIG = {
    'api_key': os.getenv('YOUTUBE_API_KEY', 'your_youtube_api_key_here'),
    'application_name': 'Keyword Trend Analyzer'
}

# YouTube search settings
YOUTUBE_SETTINGS = {
    'order': 'relevance',  # Options: 'relevance', 'date', 'rating', 'viewCount', 'title'
    'published_after': 'week',  # Options: 'hour', 'day', 'week', 'month', 'year'
    'type': 'video',  # Options: 'video', 'channel', 'playlist'
    'region_code': 'US',  # Region code for localized results
    'relevance_language': 'en',  # Language for search results
    'max_results': MAX_YOUTUBE_VIDEOS
}

# ===== TWITTER/X API SETTINGS =====
# Twitter API v2 credentials (get from Twitter Developer Portal)
TWITTER_CONFIG = {
    'bearer_token': os.getenv('TWITTER_BEARER_TOKEN', 'your_bearer_token_here'),
    'api_key': os.getenv('TWITTER_API_KEY', 'your_api_key_here'),
    'api_secret': os.getenv('TWITTER_API_SECRET', 'your_api_secret_here'),
    'access_token': os.getenv('TWITTER_ACCESS_TOKEN', 'your_access_token_here'),
    'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET', 'your_access_token_secret_here')
}

# Twitter search settings
TWITTER_SETTINGS = {
    'result_type': 'recent',  # Options: 'recent', 'popular', 'mixed'
    'lang': 'en',  # Language filter
    'tweet_fields': ['created_at', 'author_id', 'public_metrics', 'context_annotations', 'lang'],
    'user_fields': ['username', 'name', 'verified', 'public_metrics'],
    'max_results': MAX_TWITTER_TWEETS
}

# ===== TRENDING ANALYSIS SETTINGS =====
TRENDING_CONFIG = {
    'min_keyword_length': 3,  # Minimum length for trending keywords
    'max_trending_keywords': 20,  # Maximum number of trending keywords to show
    'trending_threshold': 5,  # Minimum mentions across sources to be considered trending
    'sentiment_analysis': True,  # Enable sentiment analysis for trending keywords
    'time_window_hours': 24,  # Time window for trending analysis
    'weight_factors': {  # Weight different sources for trending calculation
        'google_trends': 1.0,
        'reddit': 0.8,
        'youtube': 0.7,
        'twitter': 0.9
    }
}

# ===== FILE PATHS =====
# Paths for saving raw data (JSON files)
DATA_PATHS = {
    'raw_google_data': 'data/raw_google_trends.json',
    'raw_reddit_data': 'data/raw_reddit_data.json',
    'raw_youtube_data': 'data/raw_youtube_data.json',
    'raw_twitter_data': 'data/raw_twitter_data.json',
    'raw_upwork_data': 'data/raw_upwork_data.json',
    'cleaned_data': 'data/cleaned_data.json',
    'trending_analysis': 'data/trending_analysis.json',
    'data_directory': 'data/'
}

# ===== API RATE LIMITING =====
# Sleep time between API requests (in seconds)
API_DELAYS = {
    'google_trends': 15,  # Delay between Google Trends requests (very conservative to avoid rate limiting)
    'reddit': 2,          # Delay between Reddit requests
    'youtube': 1,         # Delay between YouTube API requests
    'twitter': 1,         # Delay between Twitter API requests
}

# ===== GOOGLE TRENDS COLLECTION MODES =====
# Control what data to collect from Google Trends (to avoid rate limiting)
GOOGLE_TRENDS_COLLECT_RELATED_QUERIES = False  # Disable related queries (causes timeouts)
GOOGLE_TRENDS_COLLECT_REGIONAL_DATA = False    # Disable regional data (causes timeouts)
GOOGLE_TRENDS_COLLECT_INTEREST_ONLY = True     # Only collect interest over time data

# ===== STREAMLIT DASHBOARD SETTINGS =====
DASHBOARD_CONFIG = {
    'page_title': 'Keyword Trends Dashboard',
    'page_icon': '📊',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# Chart colors for the dashboard
CHART_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]

# ===== LOGGING SETTINGS =====
LOGGING_CONFIG = {
    'level': 'INFO',  # Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': 'scraping.log',
    'encoding': 'utf-8',  # Fix emoji encoding issues on Windows
    'windows_safe': True,  # Use Windows-safe logging format
    'stream_encoding': 'utf-8'  # Force UTF-8 for stream handlers
}

# ===== VALIDATION FUNCTIONS =====
def validate_reddit_config():
    """
    Validate Reddit API configuration
    Returns True if configuration is valid, False otherwise
    """
    required_fields = ['client_id', 'client_secret', 'user_agent']
    for field in required_fields:
        if not REDDIT_CONFIG[field] or REDDIT_CONFIG[field] == f'your_{field}_here':
            print(f"⚠️  Warning: Reddit {field} not configured properly")
            print(f"Please update your .env file or config.py")
            return False
    return True

def validate_youtube_config():
    """
    Validate YouTube API configuration
    Returns True if configuration is valid, False otherwise
    """
    if not YOUTUBE_CONFIG['api_key'] or YOUTUBE_CONFIG['api_key'] == 'your_youtube_api_key_here':
        print("⚠️  Warning: YouTube API key not configured properly")
        print("Please get an API key from Google Cloud Console and update your .env file")
        return False
    return True

def validate_twitter_config():
    """
    Validate Twitter API configuration
    Returns True if configuration is valid, False otherwise
    """
    required_fields = ['bearer_token']  # Bearer token is minimum required for v2 API
    for field in required_fields:
        if not TWITTER_CONFIG[field] or TWITTER_CONFIG[field] == f'your_{field}_here':
            print(f"⚠️  Warning: Twitter {field} not configured properly")
            print(f"Please update your .env file or config.py")
            return False
    return True

# ===== UTILITY FUNCTIONS =====
def ensure_data_directory():
    """
    Create data directory if it doesn't exist
    """
    import os
    data_dir = DATA_PATHS['data_directory']
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"✅ Created data directory: {data_dir}")

def print_config_summary():
    """
    Print a summary of current configuration
    """
    print("🔧 Configuration Summary:")
    print(f"   Keywords: {DEFAULT_KEYWORDS}")
    print(f"   Max Reddit Posts: {MAX_REDDIT_POSTS}")
    print(f"   Max YouTube Videos: {MAX_YOUTUBE_VIDEOS}")
    print(f"   Max Twitter Tweets: {MAX_TWITTER_TWEETS}")
    print(f"   Google Trends Region: {GOOGLE_TRENDS_REGION}")
    print(f"   Reddit API Configured: {validate_reddit_config()}")
    print(f"   YouTube API Configured: {validate_youtube_config()}")
    print(f"   Twitter API Configured: {validate_twitter_config()}")
    print(f"   Trending Analysis Enabled: {TRENDING_CONFIG['sentiment_analysis']}")
    print()

if __name__ == "__main__":
    # Test configuration when running this file directly
    print_config_summary()
    ensure_data_directory() 
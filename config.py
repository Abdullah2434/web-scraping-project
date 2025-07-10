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
    "AI", 
    "ChatGPT", 
    "Pakistan Elections",
    "Machine Learning",
    "Python Programming"
]

# Data collection settings
MAX_REDDIT_POSTS = 50  # Maximum number of Reddit posts to fetch per keyword
GOOGLE_TRENDS_TIMEFRAME = 'today 3-m'  # Last 3 months (options: 'today 1-m', 'today 12-m', etc.)
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

# ===== DATABASE SETTINGS =====
# Using MongoDB only
DATABASE_TYPE = 'mongodb'

# MongoDB settings
MONGODB_CONFIG = {
    'host': 'localhost',
    'port': 27017,
    'database_name': 'keyword_trends',
    'collection_name': 'scraped_data'
}

# ===== FILE PATHS =====
# Paths for saving raw data (JSON files)
DATA_PATHS = {
    'raw_google_data': 'data/raw_google_trends.json',
    'raw_reddit_data': 'data/raw_reddit_data.json',
    'cleaned_data': 'data/cleaned_data.json',
    'data_directory': 'data/'
}

# ===== API RATE LIMITING =====
# Sleep time between API requests (in seconds)
API_DELAYS = {
    'google_trends': 15,  # Delay between Google Trends requests (very conservative to avoid rate limiting)
    'reddit': 2,          # Delay between Reddit requests
}

# ===== GOOGLE TRENDS COLLECTION MODES =====
# Control what data to collect from Google Trends (to avoid rate limiting)
GOOGLE_TRENDS_COLLECT_RELATED_QUERIES = False  # Disable related queries (causes HTTP 429)
GOOGLE_TRENDS_COLLECT_REGIONAL_DATA = False    # Disable regional data (causes HTTP 429)
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
    'log_file': 'scraping.log'
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

def validate_database_config():
    """
    Validate MongoDB configuration
    Returns True if configuration is valid, False otherwise
    """
    if DATABASE_TYPE != 'mongodb':
        print("⚠️  Error: DATABASE_TYPE must be 'mongodb'")
        return False
    return True

def get_mongodb_uri():
    """
    Get MongoDB connection URI
    """
    config = MONGODB_CONFIG
    return f"mongodb://{config['host']}:{config['port']}/{config['database_name']}"

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
    print(f"   Database: {DATABASE_TYPE}")
    print(f"   Max Reddit Posts: {MAX_REDDIT_POSTS}")
    print(f"   Google Trends Region: {GOOGLE_TRENDS_REGION}")
    print(f"   Reddit API Configured: {validate_reddit_config()}")
    print()

if __name__ == "__main__":
    # Test configuration when running this file directly
    print_config_summary()
    ensure_data_directory() 
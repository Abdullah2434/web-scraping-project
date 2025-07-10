"""
Reddit Data Fetcher
==================

This module fetches data from Reddit using the PRAW (Python Reddit API Wrapper) library.
It collects:
1. Top posts for given keywords
2. Post titles, scores, comments count
3. Post content and metadata
4. Subreddit information

Author: Web Scraping Project
"""

import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Third-party imports
import praw
from praw.exceptions import RedditAPIException, ClientException

# Local imports
from config import (
    DEFAULT_KEYWORDS,
    REDDIT_CONFIG,
    REDDIT_SETTINGS,
    DATA_PATHS,
    API_DELAYS,
    ensure_data_directory,
    LOGGING_CONFIG,
    validate_reddit_config
)

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['log_file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RedditDataCollector:
    """
    A class to collect data from Reddit using PRAW
    
    This class handles:
    - Connecting to Reddit API
    - Searching for posts by keywords
    - Extracting post metadata
    - Handling rate limiting and errors
    """
    
    def __init__(self):
        """
        Initialize the Reddit data collector
        
        Requires Reddit API credentials to be set in config.py or .env file
        """
        # Validate Reddit configuration before proceeding
        if not validate_reddit_config():
            raise ValueError("Reddit API configuration is invalid. Please check your credentials.")
        
        try:
            # Initialize PRAW Reddit instance
            # This creates an authenticated connection to Reddit's API
            self.reddit = praw.Reddit(
                client_id=REDDIT_CONFIG['client_id'],
                client_secret=REDDIT_CONFIG['client_secret'],
                user_agent=REDDIT_CONFIG['user_agent']
            )
            
            # Set to read-only mode for public data access
            self.reddit.read_only = True
            
            # Test the connection
            logger.info(f"Reddit API connection established")
            logger.info(f"   User Agent: {REDDIT_CONFIG['user_agent']}")
            logger.info(f"   Read-only mode: {self.reddit.read_only}")
            
        except Exception as e:
            logger.error(f"Error initializing Reddit API: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test if the Reddit API connection is working
        
        Returns:
            bool: True if connection works, False otherwise
        """
        try:
            # Try to access a simple endpoint
            test_sub = self.reddit.subreddit('python')
            test_sub.display_name  # This will trigger an API call
            logger.info("Reddit API connection test successful")
            return True
        except Exception as e:
            logger.error(f"Reddit API connection test failed: {e}")
            return False
    
    def search_posts_by_keyword(self, keyword: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search Reddit posts by keyword
        
        Args:
            keyword (str): Keyword to search for
            limit (int, optional): Maximum number of posts to fetch
            
        Returns:
            List[Dict[str, Any]]: List of post data dictionaries
        """
        if limit is None:
            limit = REDDIT_SETTINGS['limit']
        
        logger.info(f"Searching Reddit for keyword: '{keyword}' (limit: {limit})")
        
        posts_data = []
        
        try:
            # Search across all subreddits or specific ones
            if 'all' in REDDIT_SETTINGS['subreddits']:
                # Search across all of Reddit
                subreddit = self.reddit.subreddit('all')
            else:
                # Search specific subreddits
                subreddit_names = '+'.join(REDDIT_SETTINGS['subreddits'])
                subreddit = self.reddit.subreddit(subreddit_names)
            
            # Perform the search
            # sort: 'hot', 'new', 'top', 'rising'
            # time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
            search_results = subreddit.search(
                query=keyword,
                sort=REDDIT_SETTINGS['sort'],
                time_filter=REDDIT_SETTINGS['time_filter'],
                limit=limit
            )
            
            # Process each post
            for post in search_results:
                try:
                    # Extract post data
                    post_data = self._extract_post_data(post, keyword)
                    posts_data.append(post_data)
                    
                    # Small delay to be respectful to the API
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"⚠️  Error processing post {post.id}: {e}")
                    continue
            
            logger.info(f"Found {len(posts_data)} posts for keyword '{keyword}'")
            
        except (RedditAPIException, ClientException) as e:
            logger.error(f"Reddit API error for keyword '{keyword}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error searching for '{keyword}': {e}")
        
        return posts_data
    
    def _extract_post_data(self, post, keyword: str) -> Dict[str, Any]:
        """
        Extract relevant data from a Reddit post
        
        Args:
            post: PRAW submission object
            keyword (str): The keyword that was searched
            
        Returns:
            Dict[str, Any]: Post data dictionary
        """
        try:
            # Basic post information
            post_data = {
                'search_keyword': keyword,
                'post_id': post.id,
                'title': post.title,
                'selftext': post.selftext[:500] if post.selftext else '',  # Limit text length
                'score': post.score,
                'upvote_ratio': post.upvote_ratio,
                'num_comments': post.num_comments,
                'created_utc': post.created_utc,
                'created_date': datetime.fromtimestamp(post.created_utc).isoformat(),
                'subreddit': post.subreddit.display_name,
                'author': str(post.author) if post.author else '[deleted]',
                'url': post.url,
                'permalink': f"https://reddit.com{post.permalink}",
                'is_self': post.is_self,
                'over_18': post.over_18,
                'spoiler': post.spoiler,
                'stickied': post.stickied,
                'locked': post.locked,
                'archived': post.archived,
                'gilded': post.gilded,
                'collection_timestamp': datetime.now().isoformat()
            }
            
            # Add flair information if available
            if post.link_flair_text:
                post_data['link_flair'] = post.link_flair_text
            
            # Add domain for external links
            if not post.is_self:
                post_data['domain'] = post.domain
            
            return post_data
            
        except Exception as e:
            logger.error(f"Error extracting data from post: {e}")
            return {
                'search_keyword': keyword,
                'post_id': getattr(post, 'id', 'unknown'),
                'error': str(e),
                'collection_timestamp': datetime.now().isoformat()
            }
    
    def get_top_posts_from_subreddit(self, subreddit_name: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Get top posts from a specific subreddit
        
        Args:
            subreddit_name (str): Name of the subreddit
            limit (int): Number of posts to fetch
            
        Returns:
            List[Dict[str, Any]]: List of post data
        """
        logger.info(f"Fetching top posts from r/{subreddit_name}")
        
        posts_data = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get top posts from the subreddit
            top_posts = subreddit.top(
                time_filter=REDDIT_SETTINGS['time_filter'],
                limit=limit
            )
            
            for post in top_posts:
                try:
                    post_data = self._extract_post_data(post, f"top_from_{subreddit_name}")
                    posts_data.append(post_data)
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"⚠️  Error processing post from r/{subreddit_name}: {e}")
                    continue
            
            logger.info(f"Collected {len(posts_data)} posts from r/{subreddit_name}")
            
        except Exception as e:
            logger.error(f"Error fetching from r/{subreddit_name}: {e}")
        
        return posts_data
    
    def get_trending_subreddits(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get information about trending subreddits
        
        Args:
            limit (int): Number of subreddits to fetch
            
        Returns:
            List[Dict[str, Any]]: List of subreddit data
        """
        logger.info(f"Fetching trending subreddits")
        
        trending_data = []
        
        try:
            # Get popular subreddits
            popular_subreddits = self.reddit.subreddits.popular(limit=limit)
            
            for subreddit in popular_subreddits:
                try:
                    subreddit_data = {
                        'name': subreddit.display_name,
                        'title': subreddit.title,
                        'description': subreddit.public_description[:200] if subreddit.public_description else '',
                        'subscribers': subreddit.subscribers,
                        'created_utc': subreddit.created_utc,
                        'over_18': subreddit.over18,
                        'url': f"https://reddit.com/r/{subreddit.display_name}",
                        'collection_timestamp': datetime.now().isoformat()
                    }
                    trending_data.append(subreddit_data)
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Error processing subreddit: {e}")
                    continue
            
            logger.info(f"Collected data from {len(trending_data)} trending subreddits")
            
        except Exception as e:
            logger.error(f"Error fetching trending subreddits: {e}")
        
        return trending_data


def collect_all_reddit_data(keywords: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Collect all Reddit data for given keywords
    
    Args:
        keywords (List[str], optional): Keywords to search. Uses DEFAULT_KEYWORDS if None.
        
    Returns:
        Dict[str, Any]: Complete Reddit data
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS.copy()
    
    logger.info(f"Starting Reddit data collection for {len(keywords)} keywords")
    
    # Initialize collector
    try:
        collector = RedditDataCollector()
    except Exception as e:
        logger.error(f"Failed to initialize Reddit collector: {e}")
        return {
            'error': str(e),
            'collection_timestamp': datetime.now().isoformat()
        }
    
    # Data structure to store all results
    all_data = {
        'collection_info': {
            'keywords': keywords,
            'total_keywords': len(keywords),
            'subreddits_searched': REDDIT_SETTINGS['subreddits'],
            'sort_method': REDDIT_SETTINGS['sort'],
            'time_filter': REDDIT_SETTINGS['time_filter'],
            'max_posts_per_keyword': REDDIT_SETTINGS['limit'],
            'collection_timestamp': datetime.now().isoformat()
        },
        'keyword_posts': {},
        'trending_subreddits': []
    }
    
    # 1. Search posts for each keyword
    for keyword in keywords:
        try:
            logger.info(f"Processing keyword: {keyword}")
            posts_data = collector.search_posts_by_keyword(keyword)
            all_data['keyword_posts'][keyword] = posts_data
            
            # Delay between keywords to respect rate limits
            time.sleep(API_DELAYS['reddit'])
            
        except Exception as e:
            logger.error(f"Error collecting data for keyword '{keyword}': {e}")
            all_data['keyword_posts'][keyword] = {
                'error': str(e),
                'keyword': keyword,
                'timestamp': datetime.now().isoformat()
            }
            continue
    
    # 2. Get trending subreddits (optional)
    try:
        logger.info("Fetching trending subreddits...")
        trending_data = collector.get_trending_subreddits()
        all_data['trending_subreddits'] = trending_data
        
    except Exception as e:
        logger.error(f"Error fetching trending subreddits: {e}")
        all_data['trending_subreddits'] = {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
    
    # Calculate summary statistics
    total_posts = sum(
        len(posts) if isinstance(posts, list) else 0 
        for posts in all_data['keyword_posts'].values()
    )
    
    all_data['collection_info']['total_posts_collected'] = total_posts
    all_data['collection_info']['trending_subreddits_count'] = len(all_data['trending_subreddits'])
    
    logger.info(f"Reddit data collection completed! Total posts: {total_posts}")
    return all_data


def save_reddit_data(data: Dict[str, Any], filepath: Optional[str] = None) -> bool:
    """
    Save Reddit data to JSON file
    
    Args:
        data (Dict[str, Any]): Data to save
        filepath (str, optional): File path. Uses default if None.
        
    Returns:
        bool: True if successful, False otherwise
    """
    if filepath is None:
        filepath = DATA_PATHS['raw_reddit_data']
    
    try:
        # Ensure data directory exists
        ensure_data_directory()
        
        # Save to JSON file with proper formatting
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Reddit data saved to: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving Reddit data: {e}")
        return False


def main():
    """
    Main function to run Reddit data collection
    """
    print("Reddit Data Collector")
    print("=" * 40)
    
    try:
        # Check Reddit configuration
        if not validate_reddit_config():
            print("Reddit API configuration is invalid.")
            print("   Please check your .env file or config.py")
            print("   Visit: https://www.reddit.com/prefs/apps to get API credentials")
            return
        
        # Use default keywords
        keywords = DEFAULT_KEYWORDS
        print(f"Searching for keywords: {keywords}")
        print(f"Subreddits: {REDDIT_SETTINGS['subreddits']}")
        print(f"Sort method: {REDDIT_SETTINGS['sort']}")
        print(f"Time filter: {REDDIT_SETTINGS['time_filter']}")
        print(f"Max posts per keyword: {REDDIT_SETTINGS['limit']}")
        print()
        
        # Collect all data
        print("Starting data collection...")
        all_data = collect_all_reddit_data(keywords)
        
        # Check if collection was successful
        if 'error' in all_data:
            print(f"Data collection failed: {all_data['error']}")
            return
        
        # Save data
        print("Saving data...")
        success = save_reddit_data(all_data)
        
        if success:
            print(f"Data collection completed successfully!")
            print(f"Data saved to: {DATA_PATHS['raw_reddit_data']}")
            
            # Print summary statistics
            info = all_data['collection_info']
            print("\nCollection Summary:")
            print(f"   Keywords processed: {info['total_keywords']}")
            print(f"   Total posts collected: {info.get('total_posts_collected', 0)}")
            print(f"   Trending subreddits: {info.get('trending_subreddits_count', 0)}")
            
            # Show posts per keyword
            print("\nPosts per keyword:")
            for keyword, posts in all_data['keyword_posts'].items():
                if isinstance(posts, list):
                    print(f"   {keyword}: {len(posts)} posts")
                else:
                    print(f"   {keyword}: Error occurred")
        else:
            print("Data collection failed. Check logs for details.")
            
    except KeyboardInterrupt:
        print("\nCollection stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 
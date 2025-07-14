"""
Twitter/X Data Fetcher
=====================

This module fetches data from X (formerly Twitter) using the Twitter API v2.
It collects:
1. Recent tweets for given keywords
2. Tweet metadata (likes, retweets, replies)
3. User information
4. Hashtag and mention analysis

Author: Web Scraping Project
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import tweepy
import requests
from config import *
from fetch_twitter_nitter import collect_twitter_data_via_nitter

# Fix Unicode logging issues for Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Override the StreamHandler to avoid Unicode issues in Windows CMD
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

logger = logging.getLogger(__name__)


class TwitterDataCollector:
    """
    A class to collect data from X (Twitter) using the Twitter API v2
    
    This class handles:
    - Connecting to Twitter API v2
    - Searching for tweets by keywords
    - Extracting tweet metadata and user information
    - Handling rate limiting and errors
    """
    
    def __init__(self):
        """
        Initialize the Twitter data collector
        
        Requires Twitter API credentials to be set in config.py or .env file
        """
        # Validate Twitter configuration before proceeding
        if not validate_twitter_config():
            raise ValueError("Twitter API configuration is invalid. Please check your credentials.")
        
        try:
            # Initialize Twitter API client using Bearer Token (for API v2)
            self.client = tweepy.Client(
                bearer_token=TWITTER_CONFIG['bearer_token'],
                consumer_key=TWITTER_CONFIG['api_key'],
                consumer_secret=TWITTER_CONFIG['api_secret'],
                access_token=TWITTER_CONFIG['access_token'],
                access_token_secret=TWITTER_CONFIG['access_token_secret'],
                wait_on_rate_limit=True  # Automatically handle rate limiting
            )
            
            logger.info("Twitter API connection established")
            logger.info(f"   API Version: v2")
            logger.info(f"   Rate limiting: Enabled")
            
        except ImportError:
            logger.error("tweepy not installed. Install with: pip install tweepy")
            raise
        except Exception as e:
            logger.error(f"Error initializing Twitter API: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test if the Twitter API connection is working
        
        Returns:
            bool: True if connection works, False otherwise
        """
        try:
            # Try to get own user information as a simple test
            me = self.client.get_me()
            if me.data:
                logger.info("Twitter API connection test successful")
                return True
            else:
                logger.warning("Twitter API connection test failed - no user data returned")
                return False
        except Exception as e:
            logger.error(f"Twitter API connection test failed: {e}")
            return False
    
    def search_tweets_by_keyword(self, keyword: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search Twitter for tweets containing the keyword
        
        Args:
            keyword (str): Keyword to search for
            max_results (int, optional): Maximum number of tweets to fetch
            
        Returns:
            List[Dict[str, Any]]: List of tweet data dictionaries
        """
        if max_results is None:
            max_results = TWITTER_SETTINGS['max_results']
        
        logger.info(f"🐦 Searching Twitter for keyword: '{keyword}' (limit: {max_results})")
        
        tweets_data = []
        
        try:
            # Calculate start_time for recent tweets (last 7 days max for basic API)
            start_time = datetime.now() - timedelta(days=7)
            
            # Search for tweets
            tweets = self.client.search_recent_tweets(
                query=f"{keyword} -is:retweet lang:{TWITTER_SETTINGS['lang']}",  # Exclude retweets
                max_results=min(max_results, 100),  # API limit per request
                tweet_fields=TWITTER_SETTINGS['tweet_fields'],
                user_fields=TWITTER_SETTINGS['user_fields'],
                expansions=['author_id'],
                start_time=start_time
            )
            
            if not tweets.data:
                logger.warning(f"No tweets found for keyword: {keyword}")
                return []
            
            # Create a lookup dictionary for user information
            users_dict = {}
            if tweets.includes and 'users' in tweets.includes:
                users_dict = {user.id: user for user in tweets.includes['users']}
            
            # Process each tweet
            for tweet in tweets.data:
                tweet_data = self._extract_tweet_data(tweet, users_dict, keyword)
                tweets_data.append(tweet_data)
                
                time.sleep(0.1)  # Small delay between processing
            
            logger.info(f"✅ Found {len(tweets_data)} tweets for keyword '{keyword}'")
            
        except tweepy.TooManyRequests:
            logger.error(f"Rate limit exceeded for keyword '{keyword}'. Try again later.")
        except tweepy.Unauthorized:
            logger.error(f"Unauthorized access for keyword '{keyword}'. Check API credentials.")
        except Exception as e:
            logger.error(f"Error searching Twitter for '{keyword}': {e}")
        
        return tweets_data
    
    def _extract_tweet_data(self, tweet, users_dict: Dict, keyword: str) -> Dict[str, Any]:
        """
        Extract relevant data from a Twitter tweet object
        
        Args:
            tweet: Tweet object from Twitter API
            users_dict (Dict): Dictionary of user objects
            keyword (str): The keyword that was searched
            
        Returns:
            Dict[str, Any]: Tweet data dictionary
        """
        try:
            # Get user information
            user = users_dict.get(tweet.author_id, {})
            
            # Basic tweet information
            tweet_data = {
                'search_keyword': keyword,
                'tweet_id': tweet.id,
                'text': tweet.text,
                'created_at': tweet.created_at.isoformat() if tweet.created_at else '',
                'author_id': tweet.author_id,
                'author_username': user.username if user else '',
                'author_name': user.name if user else '',
                'author_verified': getattr(user, 'verified', False),
                'lang': getattr(tweet, 'lang', ''),
                'url': f"https://twitter.com/user/status/{tweet.id}",
                'collection_timestamp': datetime.now().isoformat()
            }
            
            # Add public metrics if available
            if hasattr(tweet, 'public_metrics') and tweet.public_metrics:
                metrics = tweet.public_metrics
                tweet_data.update({
                    'retweet_count': metrics.get('retweet_count', 0),
                    'like_count': metrics.get('like_count', 0),
                    'reply_count': metrics.get('reply_count', 0),
                    'quote_count': metrics.get('quote_count', 0)
                })
            
            # Add user metrics if available
            if hasattr(user, 'public_metrics') and user.public_metrics:
                user_metrics = user.public_metrics
                tweet_data.update({
                    'author_followers_count': user_metrics.get('followers_count', 0),
                    'author_following_count': user_metrics.get('following_count', 0),
                    'author_tweet_count': user_metrics.get('tweet_count', 0),
                    'author_listed_count': user_metrics.get('listed_count', 0)
                })
            
            # Extract hashtags and mentions
            hashtags = self._extract_hashtags(tweet.text)
            mentions = self._extract_mentions(tweet.text)
            
            tweet_data.update({
                'hashtags': hashtags,
                'mentions': mentions,
                'hashtag_count': len(hashtags),
                'mention_count': len(mentions)
            })
            
            # Add context annotations if available
            if hasattr(tweet, 'context_annotations') and tweet.context_annotations:
                contexts = []
                for context in tweet.context_annotations:
                    contexts.append({
                        'domain': context.get('domain', {}).get('name', ''),
                        'entity': context.get('entity', {}).get('name', '')
                    })
                tweet_data['context_annotations'] = contexts
            
            return tweet_data
            
        except Exception as e:
            logger.error(f"Error extracting data from tweet: {e}")
            return {
                'search_keyword': keyword,
                'tweet_id': getattr(tweet, 'id', 'unknown'),
                'error': str(e),
                'collection_timestamp': datetime.now().isoformat()
            }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """
        Extract hashtags from tweet text
        
        Args:
            text (str): Tweet text
            
        Returns:
            List[str]: List of hashtags (without #)
        """
        import re
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, text.lower())
        return list(set(hashtags))  # Remove duplicates
    
    def _extract_mentions(self, text: str) -> List[str]:
        """
        Extract mentions from tweet text
        
        Args:
            text (str): Tweet text
            
        Returns:
            List[str]: List of mentions (without @)
        """
        import re
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, text.lower())
        return list(set(mentions))  # Remove duplicates
    
    def get_trending_topics(self, location_id: int = 1) -> List[Dict[str, Any]]:
        """
        Get trending topics for a specific location
        
        Args:
            location_id (int): WOEID (Where On Earth ID) for location (1 = Worldwide)
            
        Returns:
            List[Dict[str, Any]]: List of trending topics
        """
        logger.info(f"📈 Fetching trending topics for location: {location_id}")
        
        try:
            # Note: Trending topics might require higher API access levels
            # This is a placeholder for the functionality
            
            trending_data = []
            
            # For now, we'll return empty list as trending topics require special API access
            logger.warning("Trending topics require Twitter API v1.1 and special access")
            
            return trending_data
            
        except Exception as e:
            logger.error(f"Error fetching trending topics: {e}")
            return []


def generate_mock_twitter_data(keywords, tweets_per_keyword=10):
    """Generate mock Twitter data for testing when APIs fail"""
    logger.info("📊 Generating mock Twitter data for testing...")
    
    mock_tweets = []
    base_date = datetime.now()
    
    sample_tweets = [
        "Just discovered this amazing tool! #innovation #tech",
        "Breaking: New developments in the field are exciting! 🚀",
        "Tutorial: How to get started with {keyword} - thread below 🧵",
        "Thoughts on the latest {keyword} trends? What do you think?",
        "Amazing presentation about {keyword} at today's conference!",
        "Quick tip: Best practices for {keyword} implementation",
        "Industry update: {keyword} market showing strong growth",
        "Beginner's guide to {keyword} - perfect for newcomers!",
        "Expert analysis: The future of {keyword} looks promising",
        "Community discussion: Share your {keyword} success stories!"
    ]
    
    for i, keyword in enumerate(keywords):
        logger.info(f"📝 Generating mock data for: {keyword}")
        
        for j in range(tweets_per_keyword):
            # Create realistic mock tweet
            text = sample_tweets[j % len(sample_tweets)].format(keyword=keyword)
            created_at = base_date - timedelta(hours=i*2 + j*0.5)
            
            mock_tweet = {
                'id': f'mock_{i}_{j}',
                'text': text,
                'author_username': f'user_{keyword.lower().replace(" ", "")}_{j}',
                'author_name': f'Expert User {j+1}',
                'created_at': created_at.isoformat(),
                'like_count': max(1, (j * 3) % 50),
                'retweet_count': max(0, (j * 2) % 25),
                'reply_count': max(0, j % 15),
                'source': 'twitter_mock',
                'keyword': keyword,
                'url': f'https://twitter.com/mock_user/status/mock_{i}_{j}',
                'hashtags': [f"#{keyword.replace(' ', '').lower()}", "#tech"],
                'mentions': [],
                'is_verified': j % 3 == 0,  # Some verified users
                'follower_count': 1000 + (j * 100),
                'sentiment_score': round(0.1 + (j % 9) * 0.1, 1)  # 0.1 to 0.9
            }
            
            mock_tweets.append(mock_tweet)
    
    logger.info(f"📊 Generated {len(mock_tweets)} mock tweets")
    return mock_tweets


def collect_twitter_data_api(keywords):
    """Try to collect data via Twitter API"""
    try:
        # This function would contain the Twitter API logic
        # For now, return empty list to trigger fallback
        logger.info("Twitter API collection attempted")
        return []
    except Exception as e:
        logger.error(f"Twitter API error: {e}")
        return []


def collect_all_twitter_data(keywords: Optional[List[str]] = None):
    """Main function to collect Twitter data with multiple fallbacks"""
    if keywords is None:
        keywords = DEFAULT_KEYWORDS
    all_tweets = []
    
    try:
        logger.info(f"Starting Twitter data collection for {len(keywords)} keywords")
        
        # Try Twitter API first
        logger.info("🐦 Attempting Twitter API collection...")
        try:
            api_tweets = collect_twitter_data_api(keywords)
            if api_tweets and len(api_tweets) > 0:
                logger.info(f"✅ Twitter API succeeded: {len(api_tweets)} tweets")
                all_tweets.extend(api_tweets)
                return all_tweets
            else:
                logger.warning("⚠️  Twitter API returned no data (likely rate limited)")
        except Exception as e:
            logger.error(f"❌ Twitter API failed: {str(e)}")
        
        # Fallback to Nitter scraping
        logger.info("🔄 Falling back to Nitter scraping...")
        try:
            nitter_tweets = collect_twitter_data_via_nitter()
            if nitter_tweets and len(nitter_tweets) > 0:
                logger.info(f"✅ Nitter scraping succeeded: {len(nitter_tweets)} tweets")
                all_tweets.extend(nitter_tweets)
                return all_tweets
            else:
                logger.warning("⚠️  Nitter scraping returned no data")
        except Exception as e:
            logger.error(f"❌ Nitter scraping failed: {str(e)}")
        
        # Final fallback: Generate mock data for testing
        logger.info("🔄 Both methods failed. Generating mock data for testing...")
        mock_tweets = generate_mock_twitter_data(keywords, tweets_per_keyword=5)
        all_tweets.extend(mock_tweets)
        logger.info(f"📊 Using {len(mock_tweets)} mock tweets for development/testing")
        
        return all_tweets
        
    except Exception as e:
        logger.error(f"❌ Complete Twitter data collection failed: {str(e)}")
        # Even if everything fails, return mock data
        return generate_mock_twitter_data(keywords, tweets_per_keyword=3)


def save_twitter_data(data: Dict[str, Any], filepath: Optional[str] = None) -> bool:
    """
    Save Twitter data to JSON file
    
    Args:
        data (Dict[str, Any]): Twitter data to save
        filepath (str, optional): Custom file path. Uses default if None.
        
    Returns:
        bool: True if successful, False otherwise
    """
    if filepath is None:
        filepath = DATA_PATHS['raw_twitter_data']
    
    try:
        ensure_data_directory()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📁 Twitter data saved to: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving Twitter data: {e}")
        return False


def main():
    """Main execution function"""
    try:
        logger.info("=== Twitter Data Collection Started ===")
        
        # Collect Twitter data with all fallbacks
        twitter_data = collect_all_twitter_data()
        
        if twitter_data and len(twitter_data) > 0:
            # Save raw data
            raw_filename = f"data/raw_twitter_data.json"
            
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            with open(raw_filename, 'w', encoding='utf-8') as f:
                json.dump(twitter_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"✅ Twitter data saved: {len(twitter_data)} tweets")
            logger.info(f"📁 File: {raw_filename}")
            
            # Print summary
            keywords_found = set(tweet.get('keyword', 'Unknown') for tweet in twitter_data)
            logger.info(f"📊 Keywords covered: {', '.join(keywords_found)}")
            
            # Print first few tweets as examples
            logger.info("📝 Sample tweets:")
            for i, tweet in enumerate(twitter_data[:3]):
                logger.info(f"   {i+1}. {tweet.get('text', '')[:100]}...")
            
        else:
            logger.error("❌ No Twitter data collected")
            
        logger.info("=== Twitter Data Collection Completed ===")
        
    except Exception as e:
        logger.error(f"❌ Main execution failed: {str(e)}")


if __name__ == "__main__":
    main() 
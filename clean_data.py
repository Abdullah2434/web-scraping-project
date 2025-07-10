"""
Data Cleaning Module
===================

This module cleans and processes raw data collected from Google Trends and Reddit.
It performs:
1. Data loading from JSON files
2. Text cleaning and normalization
3. Duplicate removal
4. Data validation and filtering
5. Data transformation for analysis

Author: Web Scraping Project
"""

import json
import re
import string
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

# Third-party imports
import pandas as pd

# Local imports
from config import (
    DATA_PATHS,
    ensure_data_directory,
    LOGGING_CONFIG
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


class DataCleaner:
    """
    A class to clean and process scraped data
    
    This class handles:
    - Text normalization and cleaning
    - Duplicate removal
    - Data validation
    - Format standardization
    """
    
    def __init__(self):
        """
        Initialize the data cleaner
        """
        logger.info("🧹 Data cleaner initialized")
        
        # Define stop words for text cleaning (common words to potentially remove)
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Compile regex patterns for cleaning
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.special_chars_pattern = re.compile(r'[^\w\s]')
        self.multiple_spaces_pattern = re.compile(r'\s+')
    
    def clean_text(self, text: str, remove_urls: bool = True, remove_emails: bool = True, 
                   remove_special_chars: bool = False, to_lowercase: bool = True) -> str:
        """
        Clean and normalize text data
        
        Args:
            text (str): Text to clean
            remove_urls (bool): Remove URLs from text
            remove_emails (bool): Remove email addresses
            remove_special_chars (bool): Remove special characters
            to_lowercase (bool): Convert to lowercase
            
        Returns:
            str: Cleaned text
        """
        if not isinstance(text, str) or not text.strip():
            return ""
        
        cleaned_text = text.strip()
        
        # Remove URLs
        if remove_urls:
            cleaned_text = self.url_pattern.sub('', cleaned_text)
        
        # Remove email addresses
        if remove_emails:
            cleaned_text = self.email_pattern.sub('', cleaned_text)
        
        # Remove special characters (keep only alphanumeric and spaces)
        if remove_special_chars:
            cleaned_text = self.special_chars_pattern.sub(' ', cleaned_text)
        
        # Convert to lowercase
        if to_lowercase:
            cleaned_text = cleaned_text.lower()
        
        # Remove multiple spaces and strip
        cleaned_text = self.multiple_spaces_pattern.sub(' ', cleaned_text).strip()
        
        return cleaned_text
    
    def extract_keywords_from_text(self, text: str, min_length: int = 3) -> Set[str]:
        """
        Extract meaningful keywords from text
        
        Args:
            text (str): Text to process
            min_length (int): Minimum word length to consider
            
        Returns:
            Set[str]: Set of extracted keywords
        """
        if not text:
            return set()
        
        # Clean text first
        cleaned_text = self.clean_text(text, remove_special_chars=True)
        
        # Split into words
        words = cleaned_text.split()
        
        # Filter words: remove stop words, short words, and pure numbers
        keywords = set()
        for word in words:
            if (len(word) >= min_length and 
                word not in self.stop_words and 
                not word.isdigit() and
                word.isalpha()):
                keywords.add(word)
        
        return keywords
    
    def remove_duplicates(self, data_list: List[Dict[str, Any]], key_fields: List[str]) -> List[Dict[str, Any]]:
        """
        Remove duplicate entries based on specified key fields
        
        Args:
            data_list (List[Dict]): List of data dictionaries
            key_fields (List[str]): Fields to use for duplicate detection
            
        Returns:
            List[Dict]: Deduplicated data
        """
        if not data_list:
            return []
        
        seen = set()
        unique_data = []
        
        for item in data_list:
            # Create a tuple of values from key fields
            key_values = tuple(str(item.get(field, '')).lower() for field in key_fields)
            
            if key_values not in seen:
                seen.add(key_values)
                unique_data.append(item)
        
        removed_count = len(data_list) - len(unique_data)
        if removed_count > 0:
            logger.info(f"🗑️  Removed {removed_count} duplicate entries")
        
        return unique_data
    
    def clean_google_trends_data(self, google_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean Google Trends data
        
        Args:
            google_data (Dict): Raw Google Trends data
            
        Returns:
            Dict: Cleaned Google Trends data
        """
        logger.info("🔍 Cleaning Google Trends data...")
        
        cleaned_data = {
            'source': 'google_trends',
            'collection_info': google_data.get('collection_info', {}),
            'cleaned_timestamp': datetime.now().isoformat(),
            'interest_data': [],
            'related_queries': [],
            'regional_data': [],
            'keywords_analyzed': []
        }
        
        # Process interest over time data
        interest_data = google_data.get('interest_over_time', {})
        for batch_key, batch_data in interest_data.items():
            if isinstance(batch_data, dict) and 'data' in batch_data:
                for data_point in batch_data['data']:
                    # Clean and standardize each data point
                    cleaned_point = {
                        'date': data_point.get('date'),
                        'batch_keywords': batch_data.get('keywords', []),
                        'region': batch_data.get('region', ''),
                        'timeframe': batch_data.get('timeframe', ''),
                        'values': {}
                    }
                    
                    # Extract interest values for each keyword
                    for keyword in batch_data.get('keywords', []):
                        if keyword in data_point:
                            cleaned_point['values'][keyword] = data_point[keyword]
                    
                    cleaned_data['interest_data'].append(cleaned_point)
        
        # Process related queries
        related_queries = google_data.get('related_queries', {})
        for keyword, query_data in related_queries.items():
            if isinstance(query_data, dict):
                # Clean top queries
                for query in query_data.get('top_queries', []):
                    if isinstance(query, dict):
                        cleaned_query = {
                            'keyword': keyword,
                            'type': 'top',
                            'query': self.clean_text(query.get('query', '')),
                            'value': query.get('value', 0),
                            'region': query_data.get('region', ''),
                            'timeframe': query_data.get('timeframe', '')
                        }
                        cleaned_data['related_queries'].append(cleaned_query)
                
                # Clean rising queries
                for query in query_data.get('rising_queries', []):
                    if isinstance(query, dict):
                        cleaned_query = {
                            'keyword': keyword,
                            'type': 'rising',
                            'query': self.clean_text(query.get('query', '')),
                            'value': query.get('value', 0),
                            'region': query_data.get('region', ''),
                            'timeframe': query_data.get('timeframe', '')
                        }
                        cleaned_data['related_queries'].append(cleaned_query)
        
        # Process regional interest data
        regional_data = google_data.get('regional_interest', {})
        for keyword, region_data in regional_data.items():
            if isinstance(region_data, dict) and 'regional_data' in region_data:
                for region, interest_value in region_data['regional_data'].items():
                    cleaned_region = {
                        'keyword': keyword,
                        'region': region,
                        'interest_value': interest_value if isinstance(interest_value, (int, float)) else 0
                    }
                    cleaned_data['regional_data'].append(cleaned_region)
        
        # Extract unique keywords
        all_keywords = set()
        if 'collection_info' in google_data and 'keywords' in google_data['collection_info']:
            all_keywords.update(google_data['collection_info']['keywords'])
        
        cleaned_data['keywords_analyzed'] = list(all_keywords)
        
        logger.info(f"✅ Google Trends data cleaned: {len(cleaned_data['interest_data'])} interest points, "
                   f"{len(cleaned_data['related_queries'])} related queries, "
                   f"{len(cleaned_data['regional_data'])} regional data points")
        
        return cleaned_data
    
    def clean_reddit_data(self, reddit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean Reddit data
        
        Args:
            reddit_data (Dict): Raw Reddit data
            
        Returns:
            Dict: Cleaned Reddit data
        """
        logger.info("📱 Cleaning Reddit data...")
        
        cleaned_data = {
            'source': 'reddit',
            'collection_info': reddit_data.get('collection_info', {}),
            'cleaned_timestamp': datetime.now().isoformat(),
            'posts': [],
            'subreddits': [],
            'keywords_analyzed': []
        }
        
        # Process posts by keyword
        keyword_posts = reddit_data.get('keyword_posts', {})
        all_posts = []
        
        for keyword, posts in keyword_posts.items():
            if isinstance(posts, list):
                for post in posts:
                    if isinstance(post, dict) and 'post_id' in post:
                        # Clean post data
                        cleaned_post = {
                            'search_keyword': keyword,
                            'post_id': post.get('post_id', ''),
                            'title': self.clean_text(post.get('title', '')),
                            'title_original': post.get('title', ''),
                            'content': self.clean_text(post.get('selftext', '')),
                            'content_original': post.get('selftext', ''),
                            'score': post.get('score', 0),
                            'upvote_ratio': post.get('upvote_ratio', 0.0),
                            'num_comments': post.get('num_comments', 0),
                            'created_date': post.get('created_date', ''),
                            'subreddit': post.get('subreddit', ''),
                            'author': post.get('author', ''),
                            'url': post.get('url', ''),
                            'permalink': post.get('permalink', ''),
                            'is_self': post.get('is_self', False),
                            'over_18': post.get('over_18', False),
                            'domain': post.get('domain', ''),
                            'link_flair': post.get('link_flair', '')
                        }
                        
                        # Extract keywords from title and content
                        title_keywords = self.extract_keywords_from_text(cleaned_post['title'])
                        content_keywords = self.extract_keywords_from_text(cleaned_post['content'])
                        cleaned_post['extracted_keywords'] = list(title_keywords.union(content_keywords))
                        
                        all_posts.append(cleaned_post)
        
        # Remove duplicate posts based on post_id
        cleaned_data['posts'] = self.remove_duplicates(all_posts, ['post_id'])
        
        # Process trending subreddits
        trending_subreddits = reddit_data.get('trending_subreddits', [])
        if isinstance(trending_subreddits, list):
            for subreddit in trending_subreddits:
                if isinstance(subreddit, dict):
                    cleaned_subreddit = {
                        'name': subreddit.get('name', ''),
                        'title': self.clean_text(subreddit.get('title', '')),
                        'description': self.clean_text(subreddit.get('description', '')),
                        'subscribers': subreddit.get('subscribers', 0),
                        'over_18': subreddit.get('over_18', False),
                        'url': subreddit.get('url', '')
                    }
                    cleaned_data['subreddits'].append(cleaned_subreddit)
        
        # Extract unique keywords and subreddits
        all_keywords = set()
        all_subreddits = set()
        
        for post in cleaned_data['posts']:
            all_keywords.add(post['search_keyword'])
            all_subreddits.add(post['subreddit'])
        
        cleaned_data['keywords_analyzed'] = list(all_keywords)
        cleaned_data['unique_subreddits'] = list(all_subreddits)
        
        logger.info(f"✅ Reddit data cleaned: {len(cleaned_data['posts'])} posts, "
                   f"{len(cleaned_data['subreddits'])} trending subreddits, "
                   f"{len(all_subreddits)} unique subreddits")
        
        return cleaned_data
    
    def create_unified_dataset(self, google_data: Dict[str, Any], reddit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a unified dataset combining Google Trends and Reddit data
        
        Args:
            google_data (Dict): Cleaned Google Trends data
            reddit_data (Dict): Cleaned Reddit data
            
        Returns:
            Dict: Unified dataset
        """
        logger.info("🔗 Creating unified dataset...")
        
        # Get all unique keywords from both sources
        google_keywords = set(google_data.get('keywords_analyzed', []))
        reddit_keywords = set(reddit_data.get('keywords_analyzed', []))
        all_keywords = google_keywords.union(reddit_keywords)
        
        unified_data = {
            'creation_timestamp': datetime.now().isoformat(),
            'data_sources': ['google_trends', 'reddit'],
            'keywords_analyzed': list(all_keywords),
            'summary_stats': {
                'total_keywords': len(all_keywords),
                'google_trends_keywords': len(google_keywords),
                'reddit_keywords': len(reddit_keywords),
                'google_interest_points': len(google_data.get('interest_data', [])),
                'google_related_queries': len(google_data.get('related_queries', [])),
                'reddit_posts': len(reddit_data.get('posts', [])),
                'unique_subreddits': len(reddit_data.get('unique_subreddits', []))
            },
            'google_trends_data': google_data,
            'reddit_data': reddit_data,
            'keyword_analysis': {}
        }
        
        # Create keyword-level analysis
        for keyword in all_keywords:
            keyword_stats = {
                'keyword': keyword,
                'in_google_trends': keyword in google_keywords,
                'in_reddit': keyword in reddit_keywords,
                'reddit_posts_count': 0,
                'reddit_avg_score': 0,
                'reddit_subreddits': [],
                'google_related_queries_count': 0
            }
            
            # Calculate Reddit stats for this keyword
            reddit_posts = [p for p in reddit_data.get('posts', []) if p.get('search_keyword') == keyword]
            keyword_stats['reddit_posts_count'] = len(reddit_posts)
            
            if reddit_posts:
                scores = [p.get('score', 0) for p in reddit_posts if isinstance(p.get('score'), (int, float))]
                keyword_stats['reddit_avg_score'] = sum(scores) / len(scores) if scores else 0
                keyword_stats['reddit_subreddits'] = list(set(p.get('subreddit', '') for p in reddit_posts))
            
            # Calculate Google Trends stats
            google_queries = [q for q in google_data.get('related_queries', []) if q.get('keyword') == keyword]
            keyword_stats['google_related_queries_count'] = len(google_queries)
            
            unified_data['keyword_analysis'][keyword] = keyword_stats
        
        logger.info(f"✅ Unified dataset created with {len(all_keywords)} keywords")
        return unified_data


def load_raw_data() -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Load raw data from JSON files
    
    Returns:
        tuple: (google_data, reddit_data) or (None, None) if loading fails
    """
    google_data = None
    reddit_data = None
    
    # Load Google Trends data
    try:
        with open(DATA_PATHS['raw_google_data'], 'r', encoding='utf-8') as f:
            google_data = json.load(f)
        logger.info(f"✅ Loaded Google Trends data from {DATA_PATHS['raw_google_data']}")
    except FileNotFoundError:
        logger.warning(f"⚠️  Google Trends data not found: {DATA_PATHS['raw_google_data']}")
    except Exception as e:
        logger.error(f"❌ Error loading Google Trends data: {e}")
    
    # Load Reddit data
    try:
        with open(DATA_PATHS['raw_reddit_data'], 'r', encoding='utf-8') as f:
            reddit_data = json.load(f)
        logger.info(f"✅ Loaded Reddit data from {DATA_PATHS['raw_reddit_data']}")
    except FileNotFoundError:
        logger.warning(f"⚠️  Reddit data not found: {DATA_PATHS['raw_reddit_data']}")
    except Exception as e:
        logger.error(f"❌ Error loading Reddit data: {e}")
    
    return google_data, reddit_data


def save_cleaned_data(data: Dict[str, Any], filepath: Optional[str] = None) -> bool:
    """
    Save cleaned data to JSON file
    
    Args:
        data (Dict): Cleaned data to save
        filepath (str, optional): File path. Uses default if None.
        
    Returns:
        bool: True if successful, False otherwise
    """
    if filepath is None:
        filepath = DATA_PATHS['cleaned_data']
    
    try:
        ensure_data_directory()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"✅ Cleaned data saved to: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving cleaned data: {e}")
        return False


def main():
    """
    Main function to run data cleaning process
    """
    print("🧹 Data Cleaning Module")
    print("=" * 40)
    
    try:
        # Load raw data
        print("📂 Loading raw data...")
        google_data, reddit_data = load_raw_data()
        
        if google_data is None and reddit_data is None:
            print("❌ No raw data found to clean.")
            print("   Please run fetch_google_data.py and fetch_reddit_data.py first.")
            return
        
        # Initialize cleaner
        cleaner = DataCleaner()
        
        # Clean individual datasets
        cleaned_google = None
        cleaned_reddit = None
        
        if google_data:
            print("🔍 Cleaning Google Trends data...")
            cleaned_google = cleaner.clean_google_trends_data(google_data)
        
        if reddit_data:
            print("📱 Cleaning Reddit data...")
            cleaned_reddit = cleaner.clean_reddit_data(reddit_data)
        
        # Create unified dataset if both sources are available
        if cleaned_google and cleaned_reddit:
            print("🔗 Creating unified dataset...")
            unified_data = cleaner.create_unified_dataset(cleaned_google, cleaned_reddit)
        elif cleaned_google:
            unified_data = {
                'creation_timestamp': datetime.now().isoformat(),
                'data_sources': ['google_trends'],
                'google_trends_data': cleaned_google
            }
        elif cleaned_reddit:
            unified_data = {
                'creation_timestamp': datetime.now().isoformat(),
                'data_sources': ['reddit'],
                'reddit_data': cleaned_reddit
            }
        else:
            print("❌ No valid data to process.")
            return
        
        # Save cleaned data
        print("💾 Saving cleaned data...")
        success = save_cleaned_data(unified_data)
        
        if success:
            print("✅ Data cleaning completed successfully!")
            print(f"📁 Cleaned data saved to: {DATA_PATHS['cleaned_data']}")
            
            # Print summary
            print("\n📊 Cleaning Summary:")
            if 'summary_stats' in unified_data:
                stats = unified_data['summary_stats']
                print(f"   Total keywords: {stats.get('total_keywords', 0)}")
                print(f"   Google Trends data: {stats.get('google_interest_points', 0)} interest points")
                print(f"   Reddit data: {stats.get('reddit_posts', 0)} posts")
                print(f"   Unique subreddits: {stats.get('unique_subreddits', 0)}")
            
            if 'keyword_analysis' in unified_data:
                print(f"   Keyword analysis: {len(unified_data['keyword_analysis'])} keywords processed")
        else:
            print("❌ Data cleaning failed. Check logs for details.")
            
    except KeyboardInterrupt:
        print("\n⏹️  Cleaning stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error in main: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 
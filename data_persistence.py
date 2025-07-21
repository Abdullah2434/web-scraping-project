"""
Data Persistence Module
=====================

Handles data storage with append functionality instead of overwriting.
Maintains historical data while adding new collections.

Author: Web Scraping Project
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import DATA_PATHS, ensure_data_directory

logger = logging.getLogger(__name__)

def append_data_to_file(new_data: Dict[str, Any], file_path: str, data_key: str = 'data') -> bool:
    """
    Append new data to existing file instead of overwriting
    
    Args:
        new_data: New data to append
        file_path: Path to the data file
        data_key: Key under which the main data is stored
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        ensure_data_directory()
        
        # Load existing data
        existing_data = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                logger.info(f"Loaded existing data from {file_path}")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in {file_path}, starting fresh")
                existing_data = {}
        else:
            logger.info(f"Creating new file: {file_path}")
        
        # Merge data based on file type
        merged_data = merge_data_by_type(existing_data, new_data, data_key)
        
        # Save merged data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Successfully appended data to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error appending data to {file_path}: {e}")
        return False

def merge_data_by_type(existing_data: Dict[str, Any], new_data: Dict[str, Any], data_key: str) -> Dict[str, Any]:
    """
    Merge data based on the type and structure
    
    Args:
        existing_data: Existing data from file
        new_data: New data to merge
        data_key: Main data key
        
    Returns:
        Dict: Merged data
    """
    if not existing_data:
        # First time data - add collection history
        merged_data = new_data.copy()
        merged_data['collection_history'] = [{
            'timestamp': datetime.now().isoformat(),
            'items_added': get_data_count(new_data, data_key),
            'total_items': get_data_count(new_data, data_key)
        }]
        return merged_data
    
    # Initialize collection history if not exists
    if 'collection_history' not in existing_data:
        existing_data['collection_history'] = []
    
    # Merge based on data structure
    if data_key == 'jobs':  # Upwork jobs
        merged_data = merge_upwork_data(existing_data, new_data)
    elif data_key == 'posts':  # Reddit posts
        merged_data = merge_reddit_data(existing_data, new_data)
    elif data_key == 'videos':  # YouTube videos
        merged_data = merge_youtube_data(existing_data, new_data)
    elif data_key == 'tweets':  # Twitter data
        merged_data = merge_twitter_data(existing_data, new_data)
    elif data_key == 'interest_over_time':  # Google Trends
        merged_data = merge_google_trends_data(existing_data, new_data)
    else:
        # Generic merge
        merged_data = merge_generic_data(existing_data, new_data, data_key)
    
    # Update collection history
    new_items_count = get_data_count(new_data, data_key)
    total_items_count = get_data_count(merged_data, data_key)
    
    merged_data['collection_history'].append({
        'timestamp': datetime.now().isoformat(),
        'items_added': new_items_count,
        'total_items': total_items_count,
        'keywords': new_data.get('metadata', {}).get('keywords_analyzed', [])
    })
    
    # Keep only last 50 collection history entries
    if len(merged_data['collection_history']) > 50:
        merged_data['collection_history'] = merged_data['collection_history'][-50:]
    
    return merged_data

def merge_upwork_data(existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge Upwork jobs data"""
    existing_jobs = existing_data.get('jobs', [])
    new_jobs = new_data.get('jobs', [])
    
    # Create set of existing job IDs to avoid duplicates
    existing_ids = {job.get('id', '') for job in existing_jobs}
    
    # Add only new jobs
    unique_new_jobs = [job for job in new_jobs if job.get('id', '') not in existing_ids]
    
    merged_data = existing_data.copy()
    merged_data['jobs'] = existing_jobs + unique_new_jobs
    
    # Update metadata
    merged_data['metadata'] = new_data.get('metadata', {})
    merged_data['metadata']['total_jobs'] = len(merged_data['jobs'])
    merged_data['metadata']['last_updated'] = datetime.now().isoformat()
    
    logger.info(f"Merged Upwork data: {len(existing_jobs)} existing + {len(unique_new_jobs)} new = {len(merged_data['jobs'])} total")
    return merged_data

def merge_reddit_data(existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge Reddit posts data"""
    # Handle both 'posts' and 'keyword_posts' structures
    if 'keyword_posts' in new_data:
        # Flatten keyword_posts structure
        new_posts = []
        for keyword, posts in new_data['keyword_posts'].items():
            new_posts.extend(posts)
    else:
        new_posts = new_data.get('posts', [])
    
    if 'keyword_posts' in existing_data:
        existing_posts = []
        for keyword, posts in existing_data['keyword_posts'].items():
            existing_posts.extend(posts)
    else:
        existing_posts = existing_data.get('posts', [])
    
    # Create set of existing post IDs
    existing_ids = {post.get('id', '') for post in existing_posts}
    
    # Add only new posts
    unique_new_posts = [post for post in new_posts if post.get('id', '') not in existing_ids]
    
    merged_data = existing_data.copy()
    all_posts = existing_posts + unique_new_posts
    
    # Update structure to use 'posts' format
    merged_data['posts'] = all_posts
    
    # Update collection info
    merged_data['collection_info'] = new_data.get('collection_info', {})
    merged_data['collection_info']['total_posts'] = len(all_posts)
    merged_data['collection_info']['last_updated'] = datetime.now().isoformat()
    
    logger.info(f"Merged Reddit data: {len(existing_posts)} existing + {len(unique_new_posts)} new = {len(all_posts)} total")
    return merged_data

def merge_youtube_data(existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge YouTube videos data"""
    existing_videos = existing_data.get('videos', [])
    new_videos = new_data.get('videos', [])
    
    # Create set of existing video IDs
    existing_ids = {video.get('video_id', '') for video in existing_videos}
    
    # Add only new videos
    unique_new_videos = [video for video in new_videos if video.get('video_id', '') not in existing_ids]
    
    merged_data = existing_data.copy()
    merged_data['videos'] = existing_videos + unique_new_videos
    
    # Merge comments
    existing_comments = existing_data.get('comments', [])
    new_comments = new_data.get('comments', [])
    merged_data['comments'] = existing_comments + new_comments
    
    # Update collection info
    merged_data['collection_info'] = new_data.get('collection_info', {})
    merged_data['collection_info']['total_videos'] = len(merged_data['videos'])
    merged_data['collection_info']['last_updated'] = datetime.now().isoformat()
    
    # Update summary stats
    merged_data['summary_stats'] = {
        'total_videos': len(merged_data['videos']),
        'total_comments': len(merged_data['comments']),
        'last_updated': datetime.now().isoformat()
    }
    
    logger.info(f"Merged YouTube data: {len(existing_videos)} existing + {len(unique_new_videos)} new = {len(merged_data['videos'])} total")
    return merged_data

def merge_twitter_data(existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge Twitter data"""
    # Handle both list and dict formats
    if isinstance(new_data, list):
        new_tweets = new_data
        new_data = {'tweets': new_tweets, 'collection_timestamp': datetime.now().isoformat()}
    else:
        new_tweets = new_data.get('tweets', [])
    
    if isinstance(existing_data, list):
        existing_tweets = existing_data
        existing_data = {'tweets': existing_tweets}
    else:
        existing_tweets = existing_data.get('tweets', [])
    
    # Create set of existing tweet IDs (handle both dict and string formats)
    existing_ids = set()
    for tweet in existing_tweets:
        if isinstance(tweet, dict):
            existing_ids.add(tweet.get('id', ''))
        elif isinstance(tweet, str):
            existing_ids.add(tweet)  # Use the string itself as ID
    
    # Add only new tweets (handle both dict and string formats)
    unique_new_tweets = []
    for tweet in new_tweets:
        if isinstance(tweet, dict):
            tweet_id = tweet.get('id', '')
            if tweet_id not in existing_ids:
                unique_new_tweets.append(tweet)
        elif isinstance(tweet, str):
            if tweet not in existing_ids:
                unique_new_tweets.append(tweet)
    
    merged_data = existing_data.copy()
    merged_data['tweets'] = existing_tweets + unique_new_tweets
    merged_data['collection_timestamp'] = datetime.now().isoformat()
    merged_data['total_tweets'] = len(merged_data['tweets'])
    
    logger.info(f"Merged Twitter data: {len(existing_tweets)} existing + {len(unique_new_tweets)} new = {len(merged_data['tweets'])} total")
    return merged_data

def merge_google_trends_data(existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge Google Trends data"""
    merged_data = existing_data.copy()
    
    # Merge interest over time data
    existing_interest = existing_data.get('interest_over_time', {})
    new_interest = new_data.get('interest_over_time', {})
    
    merged_interest = existing_interest.copy()
    merged_interest.update(new_interest)
    merged_data['interest_over_time'] = merged_interest
    
    # Merge related queries
    existing_queries = existing_data.get('related_queries', {})
    new_queries = new_data.get('related_queries', {})
    
    merged_queries = existing_queries.copy()
    merged_queries.update(new_queries)
    merged_data['related_queries'] = merged_queries
    
    # Update collection info
    merged_data['collection_info'] = new_data.get('collection_info', {})
    merged_data['collection_info']['last_updated'] = datetime.now().isoformat()
    
    logger.info(f"Merged Google Trends data: {len(merged_interest)} interest batches, {len(merged_queries)} query sets")
    return merged_data

def merge_generic_data(existing_data: Dict[str, Any], new_data: Dict[str, Any], data_key: str) -> Dict[str, Any]:
    """Generic data merge for unknown structures"""
    merged_data = existing_data.copy()
    merged_data.update(new_data)
    merged_data['last_updated'] = datetime.now().isoformat()
    
    logger.info(f"Generic merge completed for {data_key}")
    return merged_data

def get_data_count(data: Dict[str, Any], data_key: str) -> int:
    """Get count of items in data"""
    if data_key == 'jobs':
        return len(data.get('jobs', []))
    elif data_key == 'posts':
        return len(data.get('posts', []))
    elif data_key == 'videos':
        return len(data.get('videos', []))
    elif data_key == 'tweets':
        if isinstance(data, list):
            return len(data)
        return len(data.get('tweets', []))
    elif data_key == 'interest_over_time':
        return len(data.get('interest_over_time', {}))
    else:
        return 1

# Convenience functions for each data type
def append_upwork_data(new_data: Dict[str, Any]) -> bool:
    """Append Upwork data"""
    return append_data_to_file(new_data, DATA_PATHS['raw_upwork_data'], 'jobs')

def append_reddit_data(new_data: Dict[str, Any]) -> bool:
    """Append Reddit data"""
    return append_data_to_file(new_data, DATA_PATHS['raw_reddit_data'], 'posts')

def append_youtube_data(new_data: Dict[str, Any]) -> bool:
    """Append YouTube data"""
    return append_data_to_file(new_data, DATA_PATHS['raw_youtube_data'], 'videos')

def append_twitter_data(new_data: Dict[str, Any]) -> bool:
    """Append Twitter data"""
    return append_data_to_file(new_data, DATA_PATHS['raw_twitter_data'], 'tweets')

def append_google_trends_data(new_data: Dict[str, Any]) -> bool:
    """Append Google Trends data"""
    return append_data_to_file(new_data, DATA_PATHS['raw_google_data'], 'interest_over_time')

def get_collection_history(file_path: str) -> List[Dict[str, Any]]:
    """Get collection history for a data file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('collection_history', [])
    except Exception as e:
        logger.error(f"Error reading collection history from {file_path}: {e}")
    return []

def get_data_summary(file_path: str) -> Dict[str, Any]:
    """Get summary of data in file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            summary = {
                'file_exists': True,
                'last_updated': data.get('collection_info', {}).get('last_updated', 'Unknown'),
                'total_collections': len(data.get('collection_history', [])),
                'file_size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2)
            }
            
            # Add data-specific counts
            if 'jobs' in data:
                summary['total_jobs'] = len(data['jobs'])
            elif 'posts' in data:
                summary['total_posts'] = len(data['posts'])
            elif 'videos' in data:
                summary['total_videos'] = len(data['videos'])
            elif 'tweets' in data:
                summary['total_tweets'] = len(data['tweets'])
            elif 'interest_over_time' in data:
                summary['total_interest_batches'] = len(data['interest_over_time'])
            
            return summary
    except Exception as e:
        logger.error(f"Error getting data summary for {file_path}: {e}")
    
    return {'file_exists': False}

if __name__ == "__main__":
    # Test the data persistence system
    print("🔧 Data Persistence Module - Test Mode")
    print("=" * 50)
    
    # Test with sample data
    sample_data = {
        'jobs': [
            {'id': 'test_1', 'title': 'Test Job 1', 'keyword': 'python'},
            {'id': 'test_2', 'title': 'Test Job 2', 'keyword': 'python'}
        ],
        'metadata': {
            'keywords_analyzed': ['python'],
            'collection_timestamp': datetime.now().isoformat()
        }
    }
    
    test_file = 'data/test_append.json'
    success = append_data_to_file(sample_data, test_file, 'jobs')
    print(f"Test append: {'Success' if success else 'Failed'}")
    
    # Test summary
    summary = get_data_summary(test_file)
    print(f"Data summary: {summary}") 
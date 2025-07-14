"""
YouTube Data Fetcher
===================

This module fetches data from YouTube using the YouTube Data API v3.
It collects:
1. Video search results for given keywords
2. Video metadata (views, likes, comments, duration)
3. Channel information
4. Video comments and engagement metrics

Author: Web Scraping Project
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Local imports
from config import (
    DEFAULT_KEYWORDS,
    YOUTUBE_CONFIG,
    YOUTUBE_SETTINGS,
    DATA_PATHS,
    API_DELAYS,
    ensure_data_directory,
    LOGGING_CONFIG,
    validate_youtube_config
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


class YouTubeDataCollector:
    """
    A class to collect data from YouTube using the YouTube Data API v3
    
    This class handles:
    - Connecting to YouTube API
    - Searching for videos by keywords
    - Extracting video metadata and statistics
    - Handling rate limiting and errors
    """
    
    def __init__(self):
        """
        Initialize the YouTube data collector
        
        Requires YouTube API key to be set in config.py or .env file
        """
        # Check if google-api-python-client is available
        try:
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            self.HttpError = HttpError
        except ImportError:
            logger.error("⚠️ google-api-python-client not installed")
            logger.error("📦 Install with: pip install google-api-python-client")
            raise ImportError("YouTube API client library not available. Install google-api-python-client.")
        
        # Validate YouTube configuration before proceeding
        if not validate_youtube_config():
            raise ValueError("YouTube API configuration is invalid. Please check your API key.")
        
        try:
            # Initialize YouTube API client
            self.youtube = build(
                'youtube', 
                'v3', 
                developerKey=YOUTUBE_CONFIG['api_key']
            )
            
            logger.info("✅ YouTube API connection established")
            logger.info(f"   📱 Application: {YOUTUBE_CONFIG['application_name']}")
            
        except Exception as e:
            logger.error(f"💥 Error initializing YouTube API: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test if the YouTube API connection is working
        
        Returns:
            bool: True if connection works, False otherwise
        """
        try:
            # Try a simple search to test the API
            request = self.youtube.search().list(
                part='snippet',
                q='test',
                maxResults=1,
                type='video'
            )
            request.execute()
            logger.info("YouTube API connection test successful")
            return True
        except Exception as e:
            logger.error(f"YouTube API connection test failed: {e}")
            return False
    
    def search_videos_by_keyword(self, keyword: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search YouTube videos by keyword
        
        Args:
            keyword (str): Keyword to search for
            max_results (int, optional): Maximum number of videos to fetch
            
        Returns:
            List[Dict[str, Any]]: List of video data dictionaries
        """
        if max_results is None:
            max_results = YOUTUBE_SETTINGS['max_results']
        
        logger.info(f"🔍 Searching YouTube for keyword: '{keyword}' (limit: {max_results})")
        
        videos_data = []
        
        try:
            # Calculate published_after date
            published_after = self._get_published_after_date(YOUTUBE_SETTINGS['published_after'])
            
            # Ensure max_results is a valid integer
            if max_results is None:
                max_results = YOUTUBE_SETTINGS['max_results']
            max_results = int(max_results) if max_results is not None else YOUTUBE_SETTINGS['max_results']
            
            # Search for videos
            search_request = self.youtube.search().list(
                part='snippet',
                q=keyword,
                type=YOUTUBE_SETTINGS['type'],
                order=YOUTUBE_SETTINGS['order'],
                publishedAfter=published_after,
                regionCode=YOUTUBE_SETTINGS['region_code'],
                relevanceLanguage=YOUTUBE_SETTINGS['relevance_language'],
                maxResults=min(max_results, 50)  # YouTube API limit is 50 per request
            )
            
            search_response = search_request.execute()
            
            # Extract video IDs for detailed statistics
            video_ids = []
            for item in search_response.get('items', []):
                if item['id']['kind'] == 'youtube#video':
                    video_ids.append(item['id']['videoId'])
            
            if not video_ids:
                logger.warning(f"No videos found for keyword: {keyword}")
                return []
            
            # Get detailed video statistics
            stats_request = self.youtube.videos().list(
                part='statistics,contentDetails,snippet',
                id=','.join(video_ids)
            )
            
            time.sleep(API_DELAYS['youtube'])  # Rate limiting
            stats_response = stats_request.execute()
            
            # Combine search results with statistics
            stats_dict = {item['id']: item for item in stats_response.get('items', [])}
            
            for item in search_response.get('items', []):
                if item['id']['kind'] == 'youtube#video':
                    video_id = item['id']['videoId']
                    video_data = self._extract_video_data(item, stats_dict.get(video_id), keyword)
                    videos_data.append(video_data)
            
            logger.info(f"✅ Found {len(videos_data)} videos for keyword '{keyword}'")
            
        except self.HttpError as e:
            logger.error(f"YouTube API error for keyword '{keyword}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error searching YouTube for '{keyword}': {e}")
        
        return videos_data
    
    def _extract_video_data(self, search_item: Dict, stats_item: Optional[Dict], keyword: str) -> Dict[str, Any]:
        """
        Extract relevant data from YouTube video items
        
        Args:
            search_item (Dict): Search result item from YouTube API
            stats_item (Dict): Statistics item from YouTube API
            keyword (str): The keyword that was searched
            
        Returns:
            Dict[str, Any]: Video data dictionary
        """
        try:
            video_id = search_item['id']['videoId']
            snippet = search_item['snippet']
            
            # Basic video information
            video_data = {
                'search_keyword': keyword,
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', '')[:500],  # Limit description length
                'channel_id': snippet.get('channelId', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'thumbnails': snippet.get('thumbnails', {}),
                'tags': snippet.get('tags', []),
                'category_id': snippet.get('categoryId', ''),
                'default_language': snippet.get('defaultLanguage', ''),
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'collection_timestamp': datetime.now().isoformat()
            }
            
            # Add statistics if available
            if stats_item:
                statistics = stats_item.get('statistics', {})
                content_details = stats_item.get('contentDetails', {})
                
                video_data.update({
                    'view_count': int(statistics.get('viewCount', 0)),
                    'like_count': int(statistics.get('likeCount', 0)),
                    'comment_count': int(statistics.get('commentCount', 0)),
                    'duration': content_details.get('duration', ''),
                    'definition': content_details.get('definition', ''),
                    'caption': content_details.get('caption', ''),
                    'licensed_content': content_details.get('licensedContent', False)
                })
            
            return video_data
            
        except Exception as e:
            logger.error(f"Error extracting data from video: {e}")
            return {
                'search_keyword': keyword,
                'video_id': search_item.get('id', {}).get('videoId', 'unknown'),
                'error': str(e),
                'collection_timestamp': datetime.now().isoformat()
            }
    
    def get_video_comments(self, video_id: str, max_comments: int = 20) -> List[Dict[str, Any]]:
        """
        Get comments for a specific video
        
        Args:
            video_id (str): YouTube video ID
            max_comments (int): Maximum number of comments to fetch
            
        Returns:
            List[Dict[str, Any]]: List of comment data
        """
        logger.info(f"💬 Fetching comments for video: {video_id}")
        
        comments_data = []
        
        try:
            # Get video comments
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(max_comments, 100),  # API limit
                order='relevance'
            )
            
            time.sleep(API_DELAYS['youtube'])
            response = request.execute()
            
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                comment_data = {
                    'video_id': video_id,
                    'comment_id': item['snippet']['topLevelComment']['id'],
                    'text': comment.get('textDisplay', ''),
                    'author': comment.get('authorDisplayName', ''),
                    'like_count': comment.get('likeCount', 0),
                    'published_at': comment.get('publishedAt', ''),
                    'updated_at': comment.get('updatedAt', ''),
                    'collection_timestamp': datetime.now().isoformat()
                }
                comments_data.append(comment_data)
            
            logger.info(f"✅ Found {len(comments_data)} comments for video {video_id}")
            
        except self.HttpError as e:
            logger.warning(f"Could not fetch comments for video {video_id}: {e}")
        except Exception as e:
            logger.error(f"Error fetching comments for video {video_id}: {e}")
        
        return comments_data
    
    def _get_published_after_date(self, time_period: str) -> str:
        """
        Calculate the published_after date based on time period
        
        Args:
            time_period (str): Time period ('hour', 'day', 'week', 'month', 'year')
            
        Returns:
            str: ISO format date string
        """
        now = datetime.now()
        
        if time_period == 'hour':
            published_after = now - timedelta(hours=1)
        elif time_period == 'day':
            published_after = now - timedelta(days=1)
        elif time_period == 'week':
            published_after = now - timedelta(weeks=1)
        elif time_period == 'month':
            published_after = now - timedelta(days=30)
        elif time_period == 'year':
            published_after = now - timedelta(days=365)
        else:
            published_after = now - timedelta(weeks=1)  # Default to week
        
        return published_after.isoformat() + 'Z'


def collect_all_youtube_data(keywords: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Collect YouTube data for all specified keywords
    
    Args:
        keywords (List[str], optional): List of keywords to search. Uses DEFAULT_KEYWORDS if None.
        
    Returns:
        Dict[str, Any]: Complete YouTube data collection
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS
    
    logger.info(f"🎥 Starting YouTube data collection for {len(keywords)} keywords")
    
    try:
        collector = YouTubeDataCollector()
        
        if not collector.test_connection():
            logger.error("YouTube API connection failed")
            return {}
        
        all_videos = []
        all_comments = []
        keyword_stats = {}
        failed_keywords = []
        
        for i, keyword in enumerate(keywords):
            logger.info(f"📍 Processing keyword {i+1}/{len(keywords)}: {keyword}")
            
            try:
                # Search for videos with timeout protection
                videos = collector.search_videos_by_keyword(keyword)
                
                if videos:
                    all_videos.extend(videos)
                    
                    # Track statistics per keyword
                    keyword_stats[keyword] = {
                        'videos_found': len(videos),
                        'total_views': sum(video.get('view_count', 0) for video in videos),
                        'total_likes': sum(video.get('like_count', 0) for video in videos),
                        'total_comments': sum(video.get('comment_count', 0) for video in videos)
                    }
                    
                    # Optional: Get comments from top video only (reduced from 3 to prevent hanging)
                    top_videos = sorted(videos, key=lambda x: x.get('view_count', 0), reverse=True)[:1]
                    for video in top_videos:
                        if 'video_id' in video:
                            try:
                                logger.info(f"🔄 Fetching comments for top video: {video.get('title', 'Unknown')[:50]}...")
                                comments = collector.get_video_comments(video['video_id'], max_comments=5)  # Reduced from 10
                                all_comments.extend(comments)
                                logger.info(f"✅ Retrieved {len(comments)} comments")
                            except Exception as comment_error:
                                logger.warning(f"⚠️ Failed to get comments for video {video['video_id']}: {comment_error}")
                                # Continue without comments rather than failing
                    
                    logger.info(f"✅ Keyword '{keyword}' completed: {len(videos)} videos found")
                else:
                    keyword_stats[keyword] = {
                        'videos_found': 0,
                        'total_views': 0,
                        'total_likes': 0,
                        'total_comments': 0
                    }
                    logger.warning(f"⚠️ No videos found for keyword: {keyword}")
                
            except Exception as keyword_error:
                logger.error(f"❌ Failed to process keyword '{keyword}': {keyword_error}")
                failed_keywords.append(keyword)
                keyword_stats[keyword] = {
                    'videos_found': 0,
                    'total_views': 0,
                    'total_likes': 0,
                    'total_comments': 0,
                    'error': str(keyword_error)
                }
            
            # Rate limiting between keywords
            if i < len(keywords) - 1:  # Don't wait after the last keyword
                logger.info("⏳ Waiting to respect API rate limits...")
                time.sleep(API_DELAYS['youtube'])
        
        # Compile final data structure
        youtube_data = {
            'collection_info': {
                'keywords': keywords,
                'successful_keywords': [k for k in keywords if k not in failed_keywords],
                'failed_keywords': failed_keywords,
                'total_keywords': len(keywords),
                'collection_timestamp': datetime.now().isoformat(),
                'settings': YOUTUBE_SETTINGS
            },
            'videos': all_videos,
            'comments': all_comments,
            'keyword_statistics': keyword_stats,
            'summary_stats': {
                'total_videos': len(all_videos),
                'total_comments': len(all_comments),
                'total_views': sum(stats.get('total_views', 0) for stats in keyword_stats.values()),
                'total_likes': sum(stats.get('total_likes', 0) for stats in keyword_stats.values()),
                'success_rate': f"{len(keywords) - len(failed_keywords)}/{len(keywords)}"
            }
        }
        
        logger.info(f"🎉 YouTube data collection completed!")
        logger.info(f"   📊 Total videos: {len(all_videos)}")
        logger.info(f"   💬 Total comments: {len(all_comments)}")
        logger.info(f"   ✅ Success rate: {youtube_data['summary_stats']['success_rate']}")
        
        # Save data automatically
        save_youtube_data(youtube_data)
        
        return youtube_data
        
    except Exception as e:
        logger.error(f"💥 Critical error in YouTube data collection: {e}")
        # Return partial data if any was collected
        return {
            'collection_info': {
                'keywords': keywords or [],
                'total_keywords': len(keywords) if keywords else 0,
                'collection_timestamp': datetime.now().isoformat(),
                'error': str(e)
            },
            'videos': [],
            'comments': [],
            'keyword_statistics': {},
            'summary_stats': {
                'total_videos': 0,
                'total_comments': 0,
                'total_views': 0,
                'total_likes': 0,
                'success_rate': "0/0"
            }
        }


def save_youtube_data(data: Dict[str, Any], filepath: Optional[str] = None) -> bool:
    """
    Save YouTube data to JSON file
    
    Args:
        data (Dict[str, Any]): YouTube data to save
        filepath (str, optional): Custom file path. Uses default if None.
        
    Returns:
        bool: True if successful, False otherwise
    """
    if filepath is None:
        filepath = DATA_PATHS['raw_youtube_data']
    
    try:
        ensure_data_directory()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📁 YouTube data saved to: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving YouTube data: {e}")
        return False


def main():
    """
    Main function to run YouTube data collection
    """
    try:
        # Collect data
        youtube_data = collect_all_youtube_data()
        
        if youtube_data:
            # Save to file
            save_youtube_data(youtube_data)
            print(f"✅ YouTube data collection completed successfully!")
            print(f"   Videos collected: {youtube_data.get('summary_stats', {}).get('total_videos', 0)}")
            print(f"   Comments collected: {youtube_data.get('summary_stats', {}).get('total_comments', 0)}")
        else:
            print("❌ YouTube data collection failed!")
            
    except KeyboardInterrupt:
        print("\n⚠️  YouTube data collection interrupted by user")
    except Exception as e:
        print(f"❌ Error in YouTube data collection: {e}")


if __name__ == "__main__":
    main() 
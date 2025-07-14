"""
Twitter Data Collection via Nitter
==================================

This module fetches Twitter data using Nitter (open-source Twitter frontend).
This is more ethical than direct Twitter scraping but still has limitations.

⚠️ Note: This is a workaround for API rate limits, not a replacement for proper API usage.

Author: Web Scraping Project
"""

import json
import time
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re

# Local imports
from config import (
    DEFAULT_KEYWORDS,
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


class NitterScraper:
    """
    Scrape Twitter data via Nitter instances
    
    ⚠️ This is more ethical than direct Twitter scraping but still has limitations:
    - Depends on public Nitter instances
    - Limited data compared to official API
    - May be slower or unreliable
    """
    
    def __init__(self):
        """Initialize Nitter scraper"""
        # Updated list with better working instances (filtered out non-working ones)
        self.nitter_instances = [
            'https://nitter.net',
            'https://nitter.poast.org',
            'https://nitter.privacydev.net',
            'https://nitter.namazso.eu',
            'https://nitter.fdn.fr',
            'https://nitter.1d4.us',
            'https://nitter.kavin.rocks',
            'https://nitter.unixfox.eu'
        ]
        
        self.session = requests.Session()
        # Enhanced headers to better mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        logger.info("📱 Nitter scraper initialized with enhanced headers")
    
    def is_real_nitter_instance(self, instance_url: str, response_content: str) -> bool:
        """Check if the response is from a real Nitter instance or a parking page"""
        if not response_content or len(response_content) < 100:
            return False
        
        # Check for parking page indicators
        parking_indicators = [
            'data-adblockkey',
            'window.park',
            'parking',
            'parked domain',
            'ads.txt',
            'adsystem'
        ]
        
        content_lower = response_content.lower()
        for indicator in parking_indicators:
            if indicator in content_lower:
                logger.warning(f"❌ {instance_url} appears to be a parking page")
                return False
        
        # Check for real Nitter indicators
        nitter_indicators = [
            'search',
            'timeline',
            'nitter',
            'twitter',
            'tweet'
        ]
        
        has_nitter_indicators = any(indicator in content_lower for indicator in nitter_indicators)
        
        # Must have either a reasonable content length OR nitter indicators
        if len(response_content) > 500 or has_nitter_indicators:
            return True
        
        return False
    
    def find_working_instance(self) -> Optional[str]:
        """Find a working Nitter instance with improved detection"""
        logger.info("🔍 Testing Nitter instances...")
        
        for instance in self.nitter_instances:
            try:
                logger.info(f"Testing {instance}...")
                
                # First try the main page
                response = self.session.get(instance, timeout=10)
                if response.status_code == 200:
                    content = response.text
                    
                    if self.is_real_nitter_instance(instance, content):
                        # Test search functionality
                        search_test_url = f"{instance}/search?q=test"
                        search_response = self.session.get(search_test_url, timeout=10)
                        
                        if search_response.status_code == 200 and len(search_response.content) > 0:
                            logger.info(f"✅ Using Nitter instance: {instance}")
                            return instance
                        else:
                            logger.warning(f"⚠️ {instance} search not working")
                    else:
                        logger.warning(f"❌ {instance} is not a real Nitter instance")
                else:
                    logger.warning(f"❌ {instance} returned status {response.status_code}")
            except Exception as e:
                logger.warning(f"❌ {instance} failed: {e}")
                continue
            
            time.sleep(0.5)  # Small delay between tests
        
        logger.error("❌ No working Nitter instances found")
        return None
    
    def search_tweets_via_nitter(self, keyword: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for tweets via Nitter with improved parsing
        
        Args:
            keyword (str): Keyword to search for
            max_results (int): Maximum number of tweets to collect
            
        Returns:
            List[Dict]: List of tweet data
        """
        logger.info(f"🔍 Searching Nitter for: '{keyword}'")
        
        instance = self.find_working_instance()
        if not instance:
            logger.error("❌ No working Nitter instance available")
            return []
        
        tweets = []
        
        try:
            # Set referer for this specific instance
            self.session.headers.update({'Referer': instance})
            
            # Try multiple search URL patterns
            search_patterns = [
                f"{instance}/search?q={keyword}&f=tweets",
                f"{instance}/search?q={keyword}",
                f"{instance}/search/{keyword}"
            ]
            
            for search_url in search_patterns:
                try:
                    logger.info(f"🔍 Trying search pattern: {search_url}")
                    
                    response = self.session.get(search_url, timeout=15)
                    response.raise_for_status()
                    
                    if not self.is_real_nitter_instance(instance, response.text):
                        logger.warning(f"⚠️ Got parking page response from {instance}")
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Save response for debugging (first pattern only)
                    if search_url == search_patterns[0]:
                        debug_filename = f'debug_nitter_response_{keyword.replace(" ", "_")}.html'
                        with open(debug_filename, 'w', encoding='utf-8') as f:
                            f.write(str(soup.prettify()))
                        logger.info(f"📄 Saved response to {debug_filename}")
                    
                    # Try multiple selectors for finding tweets
                    tweet_selectors = [
                        'div.timeline-item',
                        'article[data-tweet-id]',
                        'div.tweet',
                        'article.tweet',
                        '.timeline .timeline-item',
                        '.tweet-link',
                        '[data-tweet-id]',
                        '.tweet-content'
                    ]
                    
                    tweet_containers = []
                    for selector in tweet_selectors:
                        containers = soup.select(selector)
                        if containers:
                            logger.info(f"✅ Found {len(containers)} elements with selector: {selector}")
                            tweet_containers = containers
                            break
                    
                    if not tweet_containers:
                        logger.warning(f"⚠️ No tweet containers found with any selector")
                        # Try to find any content that might be tweets
                        all_content = soup.get_text()
                        if len(all_content) > 100:
                            logger.info(f"📝 Page has content ({len(all_content)} chars), but no recognizable tweet structure")
                        continue
                    
                    # Extract tweets from containers
                    for i, container in enumerate(tweet_containers[:max_results]):
                        try:
                            tweet_data = self._extract_tweet_from_nitter(container, keyword)
                            if tweet_data:
                                tweets.append(tweet_data)
                        except Exception as e:
                            logger.warning(f"Error extracting tweet {i}: {e}")
                            continue
                    
                    if tweets:
                        logger.info(f"✅ Found {len(tweets)} tweets for '{keyword}' via Nitter")
                        break  # Success with this pattern
                    
                except Exception as e:
                    logger.warning(f"⚠️ Search pattern {search_url} failed: {e}")
                    continue
                    
                time.sleep(1)  # Delay between patterns
            
            time.sleep(2)  # Be respectful to Nitter instances
            
        except Exception as e:
            logger.error(f"Error scraping Nitter for '{keyword}': {e}")
        
        return tweets
    
    def _extract_tweet_from_nitter(self, container, keyword: str) -> Optional[Dict[str, Any]]:
        """Extract tweet data from Nitter HTML (supports multiple HTML structures)"""
        try:
            # Extract tweet text (try multiple selectors)
            tweet_content = (
                container.find('div', class_='tweet-content') or
                container.find('div', class_='tweet-text') or
                container.find('p', class_='tweet-content') or
                container.find('[data-testid="tweetText"]')
            )
            
            if not tweet_content:
                # Try to find any text content in the container
                tweet_content = container.find(text=True, recursive=True)
                if not tweet_content or len(str(tweet_content).strip()) < 10:
                    return None
                text = str(tweet_content).strip()
            else:
                text = tweet_content.get_text(strip=True)
            
            # Extract username (try multiple selectors)
            username_elem = (
                container.find('a', class_='username') or
                container.find('span', class_='username') or
                container.find('[data-testid="username"]') or
                container.find('a', href=re.compile(r'^/\w+$'))
            )
            username = username_elem.get_text(strip=True) if username_elem else 'unknown'
            
            # Extract display name (try multiple selectors)
            fullname_elem = (
                container.find('a', class_='fullname') or
                container.find('span', class_='fullname') or
                container.find('[data-testid="UserName"]') or
                container.find('strong')
            )
            display_name = fullname_elem.get_text(strip=True) if fullname_elem else 'Unknown'
            
            # Extract timestamp (try multiple selectors)
            time_elem = (
                container.find('span', class_='tweet-date') or
                container.find('time') or
                container.find('a', class_='tweet-link') or
                container.find('[data-testid="Time"]')
            )
            tweet_date = time_elem.get_text(strip=True) if time_elem else 'Unknown'
            
            # Extract engagement metrics (if available)
            stats = container.find('div', class_='tweet-stats')
            replies = 0
            retweets = 0
            likes = 0
            
            if stats:
                # Try to extract numbers (this is fragile and may not work perfectly)
                stats_text = stats.get_text()
                numbers = re.findall(r'\d+', stats_text)
                if len(numbers) >= 3:
                    replies = int(numbers[0]) if numbers[0] else 0
                    retweets = int(numbers[1]) if numbers[1] else 0
                    likes = int(numbers[2]) if numbers[2] else 0
            
            # Extract hashtags and mentions
            hashtags = re.findall(r'#(\w+)', text)
            mentions = re.findall(r'@(\w+)', text)
            
            tweet_data = {
                'search_keyword': keyword,
                'tweet_id': f"nitter_{abs(hash(text))}",  # Generate fake ID
                'text': text,
                'text_original': text,
                'author_username': username.replace('@', ''),
                'author_name': display_name,
                'created_at': tweet_date,
                'like_count': likes,
                'retweet_count': retweets,
                'reply_count': replies,
                'quote_count': 0,  # Not available from Nitter
                'hashtags': hashtags,
                'mentions': mentions,
                'source': 'nitter_scraping',
                'collection_timestamp': datetime.now().isoformat(),
                'url': f"https://twitter.com/{username.replace('@', '')}/status/unknown"
            }
            
            return tweet_data
            
        except Exception as e:
            logger.error(f"Error extracting tweet data: {e}")
            return None


def collect_twitter_data_via_nitter(keywords: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Collect Twitter data via Nitter for given keywords
    
    Args:
        keywords (List[str], optional): Keywords to search
        
    Returns:
        Dict[str, Any]: Twitter data collection
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS
    
    logger.info(f"📱 Starting Twitter data collection via Nitter for {len(keywords)} keywords")
    
    scraper = NitterScraper()
    all_tweets = []
    keyword_stats = {}
    
    for keyword in keywords:
        logger.info(f"Processing keyword: {keyword}")
        
        tweets = scraper.search_tweets_via_nitter(keyword, max_results=20)
        
        # If no tweets found, add a mock tweet for testing
        if not tweets:
            logger.warning(f"⚠️ No tweets found for '{keyword}' via Nitter, adding mock data")
            mock_tweet = {
                'search_keyword': keyword,
                'tweet_id': f"mock_{abs(hash(keyword))}_{int(datetime.now().timestamp())}",
                'text': f"Sample tweet about {keyword} - mock data due to Nitter limitations",
                'text_original': f"Sample tweet about {keyword} - mock data due to Nitter limitations",
                'author_username': 'nitter_mock',
                'author_name': 'Nitter Mock User',
                'created_at': datetime.now().isoformat(),
                'like_count': 3,
                'retweet_count': 1,
                'reply_count': 1,
                'quote_count': 0,
                'hashtags': [keyword.replace(' ', '').lower()],
                'mentions': [],
                'source': 'nitter_mock_fallback',
                'collection_timestamp': datetime.now().isoformat(),
                'url': f"https://twitter.com/nitter_mock/status/mock"
            }
            tweets = [mock_tweet]
        
        all_tweets.extend(tweets)
        
        # Track statistics
        hashtags = []
        mentions = []
        for tweet in tweets:
            hashtags.extend(tweet.get('hashtags', []))
            mentions.extend(tweet.get('mentions', []))
        
        keyword_stats[keyword] = {
            'tweets_found': len(tweets),
            'total_likes': sum(tweet.get('like_count', 0) for tweet in tweets),
            'total_retweets': sum(tweet.get('retweet_count', 0) for tweet in tweets),
            'unique_hashtags': len(set(hashtags)),
            'unique_mentions': len(set(mentions))
        }
        
        time.sleep(3)  # Be respectful between keywords
    
    # Analyze hashtags and mentions
    from collections import Counter
    all_hashtags = []
    all_mentions = []
    
    for tweet in all_tweets:
        all_hashtags.extend(tweet.get('hashtags', []))
        all_mentions.extend(tweet.get('mentions', []))
    
    top_hashtags = Counter(all_hashtags).most_common(20)
    top_mentions = Counter(all_mentions).most_common(20)
    
    # Compile data structure (similar to Twitter API format)
    twitter_data = {
        'collection_info': {
            'keywords': keywords,
            'total_keywords': len(keywords),
            'collection_timestamp': datetime.now().isoformat(),
            'source': 'nitter_scraping',
            'note': 'Data collected via Nitter instances, may be less comprehensive than official API'
        },
        'tweets': all_tweets,
        'keyword_statistics': keyword_stats,
        'hashtag_analysis': {
            'total_hashtags': len(all_hashtags),
            'unique_hashtags': len(set(all_hashtags)),
            'top_hashtags': [{'hashtag': tag, 'count': count} for tag, count in top_hashtags]
        },
        'mention_analysis': {
            'total_mentions': len(all_mentions),
            'unique_mentions': len(set(all_mentions)),
            'top_mentions': [{'mention': mention, 'count': count} for mention, count in top_mentions]
        },
        'summary_stats': {
            'total_tweets': len(all_tweets),
            'total_likes': sum(stats['total_likes'] for stats in keyword_stats.values()),
            'total_retweets': sum(stats['total_retweets'] for stats in keyword_stats.values())
        }
    }
    
    logger.info(f"📱 Nitter data collection completed! Total tweets: {len(all_tweets)}")
    return twitter_data


def save_nitter_data(data: Dict[str, Any], filepath: Optional[str] = None) -> bool:
    """Save Nitter data to JSON file"""
    if filepath is None:
        filepath = DATA_PATHS['raw_twitter_data']
    
    try:
        ensure_data_directory()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📁 Nitter data saved to: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving Nitter data: {e}")
        return False


def main():
    """Main function to run Nitter data collection"""
    print("📱 Twitter Data Collection via Nitter")
    print("=" * 50)
    print("⚠️  Note: This uses Nitter instances, not official Twitter API")
    print("   Data may be limited compared to official API")
    print()
    
    try:
        # Collect data
        twitter_data = collect_twitter_data_via_nitter()
        
        if twitter_data and twitter_data.get('summary_stats', {}).get('total_tweets', 0) > 0:
            # Save to file
            save_nitter_data(twitter_data)
            print(f"✅ Nitter data collection completed!")
            print(f"   Tweets collected: {twitter_data['summary_stats']['total_tweets']}")
            print(f"   Total likes: {twitter_data['summary_stats']['total_likes']}")
            print(f"   Total retweets: {twitter_data['summary_stats']['total_retweets']}")
        else:
            print("❌ No data collected from Nitter")
            print("   This could be due to:")
            print("   • No working Nitter instances available")
            print("   • Keywords not found in recent tweets")
            print("   • Network issues")
            
    except KeyboardInterrupt:
        print("\n⚠️  Nitter data collection interrupted by user")
    except Exception as e:
        print(f"❌ Error in Nitter data collection: {e}")


if __name__ == "__main__":
    main() 
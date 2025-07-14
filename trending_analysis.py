"""
Trending Analysis Module
=======================

This module performs advanced trending keyword analysis across all data sources.
It discovers trending keywords automatically from actual content rather than 
just analyzing predefined keywords.

Features:
- Automatic keyword extraction from titles, descriptions, comments
- Cross-platform trending score calculation
- Real-time trending detection
- Sentiment analysis for trending keywords
- Content-based keyword discovery

Author: Web Scraping Project
"""

import json
import os
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Any, Set, Tuple, Optional
import logging

# External libraries with graceful fallbacks
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
    
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        print("Downloading required NLTK data...")
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        
    ENGLISH_STOPWORDS = set(stopwords.words('english'))
    
except ImportError:
    NLTK_AVAILABLE = False
    # Basic English stopwords list
    ENGLISH_STOPWORDS = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
        'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
        'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
        'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
        'while', 'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after',
        'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
        'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
        'just', 'don', 'should', 'now', 'to', 'from', 'like', 'get', 'one', 'would', 'could',
        'also', 'see', 'make', 'way', 'much', 'many', 'good', 'well', 'come', 'know', 'time',
        'people', 'really', 'think', 'want', 'work', 'use', 'need', 'go', 'year', 'new',
        'even', 'back', 'take', 'day', 'still', 'say', 'life', 'look', 'first', 'two',
        'right', 'find', 'help', 'video', 'channel', 'subscribe', 'comment', 'share',
        'please', 'thanks', 'thank', 'amazing', 'awesome', 'great', 'love', 'nice',
        'best', 'cool', 'wow', 'yes', 'yeah', 'ok', 'okay', 'sure', 'definitely'
    }

from config import TRENDING_CONFIG, DATA_PATHS, ensure_data_directory

# Set up logging with UTF-8 encoding to handle emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraping.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class AutomaticTrendingAnalyzer:
    """
    Advanced trending analysis that automatically discovers keywords 
    from content across all platforms
    """
    
    def __init__(self):
        self.config = TRENDING_CONFIG
        self.min_keyword_length = self.config.get('min_keyword_length', 3)
        self.max_trending_keywords = self.config.get('max_trending_keywords', 50)
        self.trending_threshold = self.config.get('trending_threshold', 3)
        self.weight_factors = self.config.get('weight_factors', {})
        
        # Additional filters for better keyword extraction
        self.excluded_patterns = {
            r'\b(https?://[^\s]+)',  # URLs
            r'\b\d{1,2}:\d{2}\b',    # Time stamps
            r'\b\d+[kmbt]?\b',       # Numbers with suffixes
            r'\b[a-z0-9_-]{20,}\b',  # Long random strings
            r'\b(rt|dm|pm|am)\b',    # Common abbreviations
        }
        
        # Trending keywords cache
        self.discovered_keywords = defaultdict(lambda: defaultdict(int))
        self.keyword_contexts = defaultdict(list)
        self.keyword_sentiments = defaultdict(list)
    
    def extract_keywords_from_text(self, text: str, min_length: int = None) -> List[str]:
        """
        Extract meaningful keywords from text using multiple techniques
        """
        if not text or not isinstance(text, str):
            return []
        
        if min_length is None:
            min_length = self.min_keyword_length
        
        # Clean and normalize text
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove URLs and other unwanted patterns
        for pattern in self.excluded_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Extract words
        if NLTK_AVAILABLE:
            words = word_tokenize(text)
        else:
            words = text.split()
        
        # Filter words
        keywords = []
        for word in words:
            if (len(word) >= min_length and 
                word not in ENGLISH_STOPWORDS and
                word.isalpha() and  # Only alphabetic words
                not word.isdigit()):
                keywords.append(word)
        
        # Extract meaningful phrases (2-3 words)
        phrases = []
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if (all(w not in ENGLISH_STOPWORDS for w in phrase.split()) and
                all(w.isalpha() for w in phrase.split()) and
                len(phrase) >= min_length):
                phrases.append(phrase)
        
        # Extract 3-word phrases for trending topics
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            if (all(w not in ENGLISH_STOPWORDS for w in phrase.split()) and
                all(w.isalpha() for w in phrase.split()) and
                len(phrase.replace(' ', '')) >= min_length * 2):
                phrases.append(phrase)
        
        return keywords + phrases
    
    def extract_hashtags_and_mentions(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Extract hashtags and mentions from social media text
        """
        if not text:
            return [], []
        
        hashtags = re.findall(r'#(\w+)', text)
        mentions = re.findall(r'@(\w+)', text)
        
        return hashtags, mentions
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text
        """
        if not TEXTBLOB_AVAILABLE or not text:
            return {'polarity': 0.0, 'subjectivity': 0.0}
        
        try:
            blob = TextBlob(text)
            return {
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity
            }
        except Exception:
            return {'polarity': 0.0, 'subjectivity': 0.0}
    
    def process_reddit_data(self, reddit_data: Dict[str, Any]) -> None:
        """
        Extract trending keywords from Reddit posts and comments
        """
        posts = reddit_data.get('posts', [])
        logger.info(f"Processing {len(posts)} Reddit posts for keyword discovery...")
        
        for post in posts:
            # Extract from title
            title = post.get('title', '')
            if title:
                keywords = self.extract_keywords_from_text(title)
                for keyword in keywords:
                    self.discovered_keywords['reddit'][keyword] += 2  # Title words get higher weight
                    self.keyword_contexts[keyword].append({
                        'source': 'reddit',
                        'type': 'title',
                        'content': title[:100],
                        'score': post.get('score', 0),
                        'url': post.get('permalink', '')
                    })
            
            # Extract from content
            content = post.get('content', '')
            if content:
                keywords = self.extract_keywords_from_text(content)
                sentiment = self.analyze_sentiment(content)
                
                for keyword in keywords:
                    self.discovered_keywords['reddit'][keyword] += 1
                    self.keyword_sentiments[keyword].append(sentiment)
                    self.keyword_contexts[keyword].append({
                        'source': 'reddit',
                        'type': 'post',
                        'content': content[:100],
                        'score': post.get('score', 0)
                    })
    
    def process_youtube_data(self, youtube_data: Dict[str, Any]) -> None:
        """
        Extract trending keywords from YouTube videos and comments
        """
        videos = youtube_data.get('videos', [])
        logger.info(f"Processing {len(videos)} YouTube videos for keyword discovery...")
        
        for video in videos:
            # Extract from title
            title = video.get('title', '')
            if title:
                keywords = self.extract_keywords_from_text(title)
                for keyword in keywords:
                    self.discovered_keywords['youtube'][keyword] += 2  # Title words get higher weight
                    self.keyword_contexts[keyword].append({
                        'source': 'youtube',
                        'type': 'title',
                        'content': title,
                        'views': video.get('view_count', 0),
                        'video_id': video.get('video_id', '')
                    })
            
            # Extract from description
            description = video.get('description', '')
            if description:
                keywords = self.extract_keywords_from_text(description)
                sentiment = self.analyze_sentiment(description)
                
                for keyword in keywords:
                    self.discovered_keywords['youtube'][keyword] += 1
                    self.keyword_sentiments[keyword].append(sentiment)
            
            # Extract from tags
            tags = video.get('tags', [])
            for tag in tags:
                if isinstance(tag, str) and len(tag) >= self.min_keyword_length:
                    clean_tag = re.sub(r'[^\w\s]', '', tag.lower())
                    if clean_tag not in ENGLISH_STOPWORDS:
                        self.discovered_keywords['youtube'][clean_tag] += 1
            
            # Extract from comments
            comments = video.get('comments', [])
            for comment in comments[:5]:  # Limit to top comments to avoid spam
                comment_text = comment.get('text', '')
                if comment_text:
                    keywords = self.extract_keywords_from_text(comment_text)
                    sentiment = self.analyze_sentiment(comment_text)
                    
                    for keyword in keywords:
                        self.discovered_keywords['youtube'][keyword] += 0.5  # Comments get lower weight
                        self.keyword_sentiments[keyword].append(sentiment)
    
    def process_twitter_data(self, twitter_data: List[Dict[str, Any]]) -> None:
        """
        Extract trending keywords from Twitter/X data
        """
        logger.info(f"Processing {len(twitter_data)} tweets for keyword discovery...")
        
        # Handle malformed data gracefully
        valid_tweets = 0
        for tweet in twitter_data:
            # Skip if tweet is not a dictionary (malformed data)
            if not isinstance(tweet, dict):
                logger.debug(f"Skipping non-dict tweet data: {type(tweet)}")
                continue
                
            # Extract from tweet text
            text = tweet.get('text', '')
            if text and isinstance(text, str):
                valid_tweets += 1
                # Extract hashtags and mentions first
                hashtags, mentions = self.extract_hashtags_and_mentions(text)
                
                # Add hashtags as trending keywords
                for hashtag in hashtags:
                    if len(hashtag) >= self.min_keyword_length:
                        self.discovered_keywords['twitter'][hashtag.lower()] += 3  # Hashtags get high weight
                        self.keyword_contexts[hashtag.lower()].append({
                            'source': 'twitter',
                            'type': 'hashtag',
                            'content': text[:100],
                            'likes': tweet.get('like_count', 0)
                        })
                
                # Extract regular keywords
                keywords = self.extract_keywords_from_text(text)
                sentiment = self.analyze_sentiment(text)
                
                for keyword in keywords:
                    self.discovered_keywords['twitter'][keyword] += 1
                    self.keyword_sentiments[keyword].append(sentiment)
                    self.keyword_contexts[keyword].append({
                        'source': 'twitter',
                        'type': 'tweet',
                        'content': text[:100],
                        'likes': tweet.get('like_count', 0)
                    })
        
        if valid_tweets == 0:
            logger.warning("⚠️ No valid tweet data found - Twitter data may be malformed")
    
    def process_google_trends_data(self, google_data: Dict[str, Any]) -> None:
        """
        Extract trending keywords from Google Trends related queries
        """
        related_queries = google_data.get('related_queries', [])
        logger.info(f"Processing Google Trends related queries for keyword discovery...")
        
        for query_group in related_queries:
            queries = query_group.get('queries', [])
            for query_data in queries:
                query_text = query_data.get('query', '')
                value = query_data.get('value', 0)
                
                if query_text:
                    keywords = self.extract_keywords_from_text(query_text)
                    for keyword in keywords:
                        # Weight by Google Trends value
                        weight = max(1, int(value) // 10) if isinstance(value, (int, float)) else 1
                        self.discovered_keywords['google_trends'][keyword] += weight
                        self.keyword_contexts[keyword].append({
                            'source': 'google_trends',
                            'type': 'related_query',
                            'content': query_text,
                            'value': value
                        })
    
    def calculate_trending_scores(self) -> List[Dict[str, Any]]:
        """
        Calculate final trending scores for all discovered keywords
        """
        logger.info("Calculating trending scores for discovered keywords...")
        
        all_keywords = set()
        for source_keywords in self.discovered_keywords.values():
            all_keywords.update(source_keywords.keys())
        
        trending_keywords = []
        
        for keyword in all_keywords:
            # Skip very short or common words
            if len(keyword) < self.min_keyword_length:
                continue
            
            # Calculate weighted score across all sources
            total_score = 0
            sources = {}
            
            for source, weight in self.weight_factors.items():
                count = self.discovered_keywords[source].get(keyword, 0)
                if count > 0:
                    sources[source] = count
                    total_score += count * weight
            
            # Only include keywords that appear in multiple sources or have high frequency
            total_mentions = sum(sources.values())
            if total_mentions < self.trending_threshold:
                continue
            
            # Calculate average sentiment
            sentiments = self.keyword_sentiments.get(keyword, [])
            avg_sentiment = {
                'polarity': sum(s.get('polarity', 0) for s in sentiments) / len(sentiments) if sentiments else 0,
                'subjectivity': sum(s.get('subjectivity', 0) for s in sentiments) / len(sentiments) if sentiments else 0,
                'sample_count': len(sentiments)
            }
            
            # Determine sentiment label
            polarity = avg_sentiment['polarity']
            if polarity > 0.1:
                sentiment_label = 'Positive'
            elif polarity < -0.1:
                sentiment_label = 'Negative'
            else:
                sentiment_label = 'Neutral'
            
            avg_sentiment['sentiment_label'] = sentiment_label
            
            trending_keywords.append({
                'keyword': keyword,
                'trending_score': round(total_score, 2),
                'total_mentions': total_mentions,
                'sources': sources,
                'sentiment': avg_sentiment,
                'contexts': self.keyword_contexts.get(keyword, [])[:5]  # Top 5 contexts
            })
        
        # Sort by trending score
        trending_keywords.sort(key=lambda x: x['trending_score'], reverse=True)
        
        return trending_keywords[:self.max_trending_keywords]


def save_trending_analysis(analysis: Dict[str, Any], filepath: Optional[str] = None) -> bool:
    """
    Save trending analysis to JSON file
    
    Args:
        analysis (Dict[str, Any]): Trending analysis data
        filepath (str, optional): Custom file path. Uses default if None.
        
    Returns:
        bool: True if successful, False otherwise
    """
    if filepath is None:
        filepath = DATA_PATHS['trending_analysis']
    
    try:
        ensure_data_directory()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📁 Trending analysis saved to: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving trending analysis: {e}")
        return False


def load_trending_analysis(filepath: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load trending analysis from JSON file
    
    Args:
        filepath (str, optional): Custom file path. Uses default if None.
        
    Returns:
        Dict[str, Any]: Trending analysis data or None if failed
    """
    if filepath is None:
        filepath = DATA_PATHS['trending_analysis']
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        logger.info(f"📁 Trending analysis loaded from: {filepath}")
        return analysis
        
    except FileNotFoundError:
        logger.info("No existing trending analysis found")
        return None
    except Exception as e:
        logger.error(f"Error loading trending analysis: {e}")
        return None


def load_all_data_sources() -> Dict[str, Any]:
    """
    Load all available data sources for trending analysis
    """
    all_data = {}
    
    # Load Reddit data
    try:
        with open(DATA_PATHS['raw_reddit_data'], 'r', encoding='utf-8') as f:
            reddit_data = json.load(f)
            all_data['reddit_data'] = reddit_data
            logger.info(f"✅ Loaded Reddit data: {len(reddit_data.get('posts', []))} posts")
    except FileNotFoundError:
        logger.warning("❌ Reddit data not found")
        all_data['reddit_data'] = {}
    except Exception as e:
        logger.error(f"❌ Error loading Reddit data: {e}")
        all_data['reddit_data'] = {}
    
    # Load YouTube data
    try:
        with open(DATA_PATHS['raw_youtube_data'], 'r', encoding='utf-8') as f:
            youtube_data = json.load(f)
            all_data['youtube_data'] = youtube_data
            logger.info(f"✅ Loaded YouTube data: {len(youtube_data.get('videos', []))} videos")
    except FileNotFoundError:
        logger.warning("❌ YouTube data not found")
        all_data['youtube_data'] = {}
    except Exception as e:
        logger.error(f"❌ Error loading YouTube data: {e}")
        all_data['youtube_data'] = {}
    
    # Load Twitter data
    try:
        with open(DATA_PATHS['raw_twitter_data'], 'r', encoding='utf-8') as f:
            twitter_data = json.load(f)
            # Handle both old and new Twitter data formats
            if isinstance(twitter_data, dict) and 'tweets' in twitter_data:
                tweets_list = twitter_data['tweets']
                # Validate that tweets are actual dictionaries, not strings
                if isinstance(tweets_list, list):
                    valid_tweets = []
                    for tweet in tweets_list:
                        if isinstance(tweet, dict) and 'text' in tweet:
                            valid_tweets.append(tweet)
                    twitter_data = valid_tweets
                    if len(valid_tweets) == 0 and len(tweets_list) > 0:
                        logger.warning("⚠️ Twitter data contains malformed tweets (no valid tweet dictionaries found)")
                else:
                    twitter_data = []
            elif isinstance(twitter_data, list):
                # Check if it's a valid list of tweet dictionaries
                valid_tweets = []
                for tweet in twitter_data:
                    if isinstance(tweet, dict) and 'text' in tweet:
                        valid_tweets.append(tweet)
                twitter_data = valid_tweets
                if len(valid_tweets) == 0 and len(twitter_data) > 0:
                    logger.warning("⚠️ Twitter data appears malformed - no valid tweet dictionaries found")
            else:
                twitter_data = []
            
            all_data['twitter_data'] = twitter_data
            logger.info(f"✅ Loaded Twitter data: {len(twitter_data)} valid tweets")
    except FileNotFoundError:
        logger.warning("❌ Twitter data not found")
        all_data['twitter_data'] = []
    except Exception as e:
        logger.error(f"❌ Error loading Twitter data: {e}")
        all_data['twitter_data'] = []
    
    # Load Google Trends data
    try:
        with open(DATA_PATHS['raw_google_data'], 'r', encoding='utf-8') as f:
            google_data = json.load(f)
            all_data['google_trends_data'] = google_data
            queries_count = len(google_data.get('related_queries', []))
            logger.info(f"✅ Loaded Google Trends data: {queries_count} query groups")
    except FileNotFoundError:
        logger.warning("❌ Google Trends data not found")
        all_data['google_trends_data'] = {}
    except Exception as e:
        logger.error(f"❌ Error loading Google Trends data: {e}")
        all_data['google_trends_data'] = {}
    
    return all_data


def run_automatic_trending_analysis() -> Dict[str, Any]:
    """
    Run complete automatic trending analysis across all data sources
    """
    logger.info("🔥 Starting automatic trending keyword discovery...")
    
    # Initialize analyzer
    analyzer = AutomaticTrendingAnalyzer()
    
    # Load all data sources
    all_data = load_all_data_sources()
    
    data_sources_used = []
    
    # Process each data source
    if all_data.get('reddit_data', {}).get('posts'):
        analyzer.process_reddit_data(all_data['reddit_data'])
        data_sources_used.append('reddit')
    
    if all_data.get('youtube_data', {}).get('videos'):
        analyzer.process_youtube_data(all_data['youtube_data'])
        data_sources_used.append('youtube')
    
    if all_data.get('twitter_data'):
        analyzer.process_twitter_data(all_data['twitter_data'])
        data_sources_used.append('twitter')
    
    if all_data.get('google_trends_data', {}).get('related_queries'):
        analyzer.process_google_trends_data(all_data['google_trends_data'])
        data_sources_used.append('google_trends')
    
    if not data_sources_used:
        logger.error("❌ No data sources available for trending analysis")
        return {}
    
    # Calculate trending scores
    trending_keywords = analyzer.calculate_trending_scores()
    
    # Create comprehensive analysis report
    analysis_report = {
        'trending_keywords': trending_keywords,
        'analysis_timestamp': datetime.now().isoformat(),
        'data_sources_used': data_sources_used,
        'analysis_config': {
            'min_keyword_length': analyzer.min_keyword_length,
            'trending_threshold': analyzer.trending_threshold,
            'max_keywords': analyzer.max_trending_keywords,
            'weight_factors': analyzer.weight_factors
        },
        'summary_stats': {
            'total_trending_keywords': len(trending_keywords),
            'sources_analyzed': len(data_sources_used),
            'keywords_by_source': {
                source: len([kw for kw in trending_keywords if source in kw.get('sources', {})])
                for source in data_sources_used
            }
        }
    }
    
    logger.info(f"🎉 Analysis complete! Found {len(trending_keywords)} trending keywords")
    
    return analysis_report


def main():
    """
    Main function to run automatic trending analysis
    """
    try:
        logger.info("🔥 Starting automatic trending keyword discovery...")
        
        # Run automatic analysis
        analysis_report = run_automatic_trending_analysis()
        
        if analysis_report and analysis_report.get('trending_keywords'):
            # Save analysis
            save_trending_analysis(analysis_report)
            
            trending_keywords = analysis_report['trending_keywords']
            
            # Print summary
            print("🔥 Automatic Trending Keywords Analysis Complete!")
            print(f"   Total trending keywords discovered: {len(trending_keywords)}")
            print(f"   Data sources analyzed: {', '.join(analysis_report.get('data_sources_used', []))}")
            
            if trending_keywords:
                print("\n📊 Top 10 Automatically Discovered Trending Keywords:")
                for i, keyword_data in enumerate(trending_keywords[:10], 1):
                    keyword = keyword_data['keyword']
                    score = keyword_data['trending_score']
                    sources = list(keyword_data['sources'].keys())
                    mentions = keyword_data['total_mentions']
                    sentiment = keyword_data['sentiment']['sentiment_label']
                    
                    print(f"   {i:2d}. {keyword:20} (Score: {score:6.1f}) - {mentions} mentions")
                    print(f"       Sources: {', '.join(sources):30} Sentiment: {sentiment}")
                
                print(f"\n💾 Analysis saved to: {DATA_PATHS['trending_analysis']}")
                print("🚀 Use 'streamlit run app.py' to view in dashboard!")
        else:
            print("❌ No trending keywords discovered!")
            print("💡 Try collecting more data first:")
            print("   - python fetch_reddit_data.py")
            print("   - python fetch_youtube_data.py") 
            print("   - python fetch_twitter_data.py")
            print("   - python fetch_google_data.py")
            
    except KeyboardInterrupt:
        print("\n⚠️  Trending analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error in trending analysis: {e}")
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 
"""
Google Trends Data Fetcher
==========================

This module fetches trending data from Google Trends using the pytrends library.
It collects:
1. Interest over time for given keywords
2. Related queries for each keyword
3. Rising search terms
4. Regional interest data

Author: Web Scraping Project
"""

import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Third-party imports
import pandas as pd
from pytrends.request import TrendReq

# Local imports
from config import (
    DEFAULT_KEYWORDS, 
    GOOGLE_TRENDS_TIMEFRAME, 
    GOOGLE_TRENDS_REGION,
    DATA_PATHS, 
    API_DELAYS,
    ensure_data_directory,
    LOGGING_CONFIG,
    GOOGLE_TRENDS_COLLECT_RELATED_QUERIES,
    GOOGLE_TRENDS_COLLECT_REGIONAL_DATA,
    GOOGLE_TRENDS_COLLECT_INTEREST_ONLY
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


class GoogleTrendsCollector:
    """
    A class to collect data from Google Trends
    
    This class handles:
    - Connecting to Google Trends API
    - Fetching interest over time data
    - Getting related queries
    - Handling rate limiting and errors
    """
    
    def __init__(self, region: str = GOOGLE_TRENDS_REGION, language: str = 'en-US'):
        """
        Initialize the Google Trends collector
        
        Args:
            region (str): Country/region code (e.g., 'US', 'PK', 'UK')
            language (str): Language code (e.g., 'en-US', 'ur-PK')
        """
        self.region = region
        self.language = language
        self.timeframe = GOOGLE_TRENDS_TIMEFRAME
        
        # Initialize pytrends object
        # This creates a connection to Google Trends
        try:
            self.pytrends = TrendReq(
                hl=language,  # Language
                tz=360,       # Timezone offset
                timeout=(10, 25)  # Connection timeout
            )
            logger.info(f"✅ Google Trends collector initialized for region: {region}")
        except Exception as e:
            logger.error(f"❌ Error initializing Google Trends: {e}")
            raise
    
    def fetch_interest_over_time(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Fetch interest over time for given keywords
        
        Args:
            keywords (List[str]): List of keywords to search
            
        Returns:
            Dict[str, Any]: Dictionary containing interest data
        """
        logger.info(f"🔍 Fetching interest over time for: {keywords}")
        
        try:
            # Build the payload for pytrends
            # This tells Google Trends what we want to search for
            self.pytrends.build_payload(
                kw_list=keywords,          # Keywords to search
                cat=0,                     # Category (0 = all categories)
                timeframe=self.timeframe,  # Time period
                geo=self.region,           # Geographic region
                gprop=''                   # Google property ('' = web search)
            )
            
            # Add a small delay to be respectful to the API
            time.sleep(API_DELAYS['google_trends'])
            
            # Get the interest over time data
            interest_df = self.pytrends.interest_over_time()
            
            if interest_df.empty:
                logger.warning(f"⚠️  No interest data found for keywords: {keywords}")
                return {'keywords': keywords, 'data': [], 'timestamp': datetime.now().isoformat()}
            
            # Convert DataFrame to dictionary for JSON storage
            # Remove the 'isPartial' column if it exists
            if 'isPartial' in interest_df.columns:
                interest_df = interest_df.drop(columns=['isPartial'])
            
            # Convert to dictionary with proper formatting
            data_dict = {
                'keywords': keywords,
                'timeframe': self.timeframe,
                'region': self.region,
                'data': interest_df.reset_index().to_dict('records'),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Successfully fetched interest data for {len(keywords)} keywords")
            return data_dict
            
        except Exception as e:
            logger.error(f"❌ Error fetching interest over time: {e}")
            return {'keywords': keywords, 'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def fetch_related_queries(self, keyword: str) -> Dict[str, Any]:
        """
        Fetch related queries for a single keyword
        
        Args:
            keyword (str): Single keyword to search
            
        Returns:
            Dict[str, Any]: Dictionary containing related queries
        """
        logger.info(f"🔗 Fetching related queries for: {keyword}")
        
        try:
            # Build payload for single keyword
            self.pytrends.build_payload(
                kw_list=[keyword],
                timeframe=self.timeframe,
                geo=self.region
            )
            
            # Add delay for rate limiting
            time.sleep(API_DELAYS['google_trends'])
            
            # Get related queries
            related_queries = self.pytrends.related_queries()
            
            # Process the related queries data
            keyword_data = related_queries.get(keyword, {})
            
            result = {
                'keyword': keyword,
                'timeframe': self.timeframe,
                'region': self.region,
                'timestamp': datetime.now().isoformat(),
                'top_queries': [],
                'rising_queries': []
            }
            
            # Process top related queries with better error handling
            try:
                if 'top' in keyword_data and keyword_data['top'] is not None:
                    top_df = keyword_data['top']
                    if hasattr(top_df, 'empty') and not top_df.empty and len(top_df.columns) > 0:
                        result['top_queries'] = top_df.to_dict('records')
                    else:
                        logger.info(f"No top queries available for '{keyword}'")
            except Exception as e:
                logger.warning(f"Error processing top queries for '{keyword}': {e}")
            
            # Process rising related queries with better error handling
            try:
                if 'rising' in keyword_data and keyword_data['rising'] is not None:
                    rising_df = keyword_data['rising']
                    if hasattr(rising_df, 'empty') and not rising_df.empty and len(rising_df.columns) > 0:
                        result['rising_queries'] = rising_df.to_dict('records')
                    else:
                        logger.info(f"No rising queries available for '{keyword}'")
            except Exception as e:
                logger.warning(f"Error processing rising queries for '{keyword}': {e}")
            
            logger.info(f"✅ Found {len(result['top_queries'])} top and {len(result['rising_queries'])} rising queries")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error fetching related queries for '{keyword}': {e}")
            return {
                'keyword': keyword,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'top_queries': [],
                'rising_queries': []
            }
    
    def fetch_regional_interest(self, keyword: str) -> Dict[str, Any]:
        """
        Fetch regional interest data for a keyword
        
        Args:
            keyword (str): Keyword to search
            
        Returns:
            Dict[str, Any]: Regional interest data
        """
        logger.info(f"🌍 Fetching regional interest for: {keyword}")
        
        try:
            # Build payload
            self.pytrends.build_payload(
                kw_list=[keyword],
                timeframe=self.timeframe,
                geo=self.region
            )
            
            time.sleep(API_DELAYS['google_trends'])
            
            # Get regional interest
            regional_df = self.pytrends.interest_by_region(resolution='COUNTRY')
            
            result = {
                'keyword': keyword,
                'regional_data': regional_df.to_dict() if not regional_df.empty else {},
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Fetched regional data for {len(result['regional_data'])} regions")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error fetching regional interest for '{keyword}': {e}")
            return {
                'keyword': keyword,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def collect_all_google_data(keywords: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Collect all Google Trends data for given keywords
    
    Args:
        keywords (List[str], optional): Keywords to search. Uses DEFAULT_KEYWORDS if None.
        
    Returns:
        Dict[str, Any]: Complete Google Trends data
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS.copy()
    
    logger.info(f"🚀 Starting Google Trends data collection for {len(keywords)} keywords")
    
    # Initialize collector
    collector = GoogleTrendsCollector()
    
    # Data structure to store all results
    all_data = {
        'collection_info': {
            'keywords': keywords,
            'total_keywords': len(keywords),
            'region': GOOGLE_TRENDS_REGION,
            'timeframe': GOOGLE_TRENDS_TIMEFRAME,
            'collection_timestamp': datetime.now().isoformat()
        },
        'interest_over_time': {},
        'related_queries': {},
        'regional_interest': {}
    }
    
    # 1. Fetch interest over time (can handle multiple keywords at once)
    try:
        # Google Trends allows up to 5 keywords at once
        keyword_batches = [keywords[i:i+5] for i in range(0, len(keywords), 5)]
        
        for batch in keyword_batches:
            logger.info(f"📊 Processing keyword batch: {batch}")
            interest_data = collector.fetch_interest_over_time(batch)
            
            # Store data for each keyword in the batch
            batch_key = "_".join(batch)
            all_data['interest_over_time'][batch_key] = interest_data
            
            # Small delay between batches
            time.sleep(API_DELAYS['google_trends'] * 2)
            
    except Exception as e:
        logger.error(f"❌ Error in interest over time collection: {e}")
    
    # 2. Fetch related queries for each keyword individually (if enabled)
    if GOOGLE_TRENDS_COLLECT_RELATED_QUERIES:
        logger.info("🔗 Related queries collection is enabled")
        for keyword in keywords:
            try:
                logger.info(f"🔗 Processing related queries for: {keyword}")
                related_data = collector.fetch_related_queries(keyword)
                all_data['related_queries'][keyword] = related_data
                
                # Delay between keywords
                time.sleep(API_DELAYS['google_trends'])
                
            except Exception as e:
                logger.error(f"❌ Error fetching related queries for '{keyword}': {e}")
                continue
    else:
        logger.info("⏭️  Skipping related queries collection (disabled in config)")
    
    # 3. Fetch regional interest for each keyword (if enabled)
    if GOOGLE_TRENDS_COLLECT_REGIONAL_DATA:
        logger.info("🌍 Regional data collection is enabled")
        for keyword in keywords:
            try:
                logger.info(f"🌍 Processing regional interest for: {keyword}")
                regional_data = collector.fetch_regional_interest(keyword)
                all_data['regional_interest'][keyword] = regional_data
                
                # Delay between keywords
                time.sleep(API_DELAYS['google_trends'])
                
            except Exception as e:
                logger.error(f"❌ Error fetching regional interest for '{keyword}': {e}")
                continue
    else:
        logger.info("⏭️  Skipping regional data collection (disabled in config)")
    
    logger.info(f"✅ Google Trends data collection completed!")
    return all_data


def save_google_data(data: Dict[str, Any], filepath: Optional[str] = None, use_persistence: bool = True) -> bool:
    """
    Save Google Trends data to JSON file with persistence option
    
    Args:
        data (Dict[str, Any]): Data to save
        filepath (str, optional): File path. Uses default if None.
        use_persistence (bool): Whether to append to existing data
        
    Returns:
        bool: True if successful, False otherwise
    """
    if filepath is None:
        filepath = DATA_PATHS['raw_google_data']
    
    try:
        if use_persistence:
            # Use new persistence system to append data
            from data_persistence import append_google_trends_data
            success = append_google_trends_data(data)
            if success:
                logger.info(f"✅ Google Trends data appended to: {filepath}")
                return True
            else:
                logger.warning("⚠️ Failed to append, falling back to overwrite")
        
        # Fallback to overwrite or if persistence is disabled
        ensure_data_directory()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"✅ Google Trends data saved to: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving Google Trends data: {e}")
        return False


def main():
    """
    Main function to run Google Trends data collection
    """
    print("🔥 Google Trends Data Collector")
    print("=" * 40)
    
    try:
        # Use default keywords or get from user input
        keywords = DEFAULT_KEYWORDS
        print(f"📝 Searching for keywords: {keywords}")
        print(f"🌍 Region: {GOOGLE_TRENDS_REGION}")
        print(f"📅 Timeframe: {GOOGLE_TRENDS_TIMEFRAME}")
        print()
        
        # Collect all data
        print("🚀 Starting data collection...")
        all_data = collect_all_google_data(keywords)
        
        # Save data
        print("💾 Saving data...")
        success = save_google_data(all_data)
        
        if success:
            print(f"✅ Data collection completed successfully!")
            print(f"📁 Data saved to: {DATA_PATHS['raw_google_data']}")
            
            # Print summary statistics
            print("\n📊 Collection Summary:")
            print(f"   Keywords processed: {len(keywords)}")
            print(f"   Interest data batches: {len(all_data['interest_over_time'])}")
            print(f"   Related queries collected: {len(all_data['related_queries'])}")
            print(f"   Regional data collected: {len(all_data['regional_interest'])}")
        else:
            print("❌ Data collection failed. Check logs for details.")
            
    except KeyboardInterrupt:
        print("\n⏹️  Collection stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error in main: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 
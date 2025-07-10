"""
MongoDB Storage Module
=====================

This module handles saving cleaned data to MongoDB.
Features:
1. MongoDB storage (document-based)
2. Automatic index creation
3. Data validation before insertion
4. Collection management

Author: Web Scraping Project
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Local imports
from config import (
    MONGODB_CONFIG,
    DATA_PATHS,
    get_mongodb_uri,
    validate_database_config,
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


class MongoDBManager:
    """
    MongoDB manager for handling database operations
    """
    
    def __init__(self):
        """
        Initialize MongoDB manager
        """
        self.client = None
        self.database = None
        self.collection = None
        self.is_connected = False
        
        # Validate configuration
        if not validate_database_config():
            raise ValueError("Invalid MongoDB configuration")
        
        logger.info("MongoDB manager initialized")
    
    def connect(self) -> bool:
        """
        Connect to MongoDB
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import pymongo
            from pymongo import MongoClient
            
            uri = get_mongodb_uri()
            self.client = MongoClient(uri)
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database and collection
            self.database = self.client[MONGODB_CONFIG['database_name']]
            self.collection = self.database[MONGODB_CONFIG['collection_name']]
            
            self.is_connected = True
            logger.info(f"Connected to MongoDB: {MONGODB_CONFIG['database_name']}")
            return True
            
        except ImportError:
            logger.error("pymongo not installed. Install with: pip install pymongo")
            return False
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            return False
    
    def create_indexes(self) -> bool:
        """
        Create indexes for better query performance
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected or self.collection is None:
            logger.error("Not connected to MongoDB")
            return False
        
        try:
            # Create indexes for better query performance
            indexes_to_create = [
                'creation_timestamp',
                'data_sources',
                'keywords_analyzed',
                'reddit_data.posts.search_keyword',
                'reddit_data.posts.subreddit',
                'reddit_data.posts.score',
                'google_trends_data.keywords_analyzed'
            ]
            
            for index_field in indexes_to_create:
                try:
                    self.collection.create_index(index_field)
                    logger.debug(f"Created index: {index_field}")
                except Exception as e:
                    logger.warning(f"Could not create index {index_field}: {e}")
            
            logger.info("MongoDB indexes created")
            return True
            
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            return False
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """
        Save cleaned data to MongoDB
        
        Args:
            data (Dict): Cleaned data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected or self.collection is None:
            logger.error("Not connected to MongoDB")
            return False
        
        try:
            # Add metadata
            document = {
                **data,
                'inserted_at': datetime.now(),
                'database_version': '1.0'
            }
            
            # Insert the document
            result = self.collection.insert_one(document)
            
            logger.info(f"Data saved to MongoDB with ID: {result.inserted_id}")
            
            # Log summary statistics
            if 'summary_stats' in data:
                stats = data['summary_stats']
                logger.info(f"   Keywords: {stats.get('total_keywords', 0)}")
                logger.info(f"   Reddit posts: {stats.get('reddit_posts', 0)}")
                logger.info(f"   Google data points: {stats.get('google_interest_points', 0)}")
            
            return True
            
        except Exception as e:
            logger.error(f"MongoDB save failed: {e}")
            return False
    
    def get_data_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get a summary of stored data
        
        Returns:
            Dict: Data summary or None if failed
        """
        if not self.is_connected or self.collection is None:
            logger.error("Not connected to MongoDB")
            return None
        
        try:
            total_records = self.collection.count_documents({})
            
            # Get latest record
            latest_record = self.collection.find_one(
                {},
                sort=[('creation_timestamp', -1)]
            )
            
            summary = {
                'database_type': 'mongodb',
                'total_records': total_records,
                'latest_record_date': latest_record.get('creation_timestamp') if latest_record else None,
                'collection_name': MONGODB_CONFIG['collection_name'],
                'database_name': MONGODB_CONFIG['database_name']
            }
            
            if latest_record and 'summary_stats' in latest_record:
                summary['latest_stats'] = latest_record['summary_stats']
            
            if latest_record and 'keywords_analyzed' in latest_record:
                summary['latest_keywords'] = latest_record['keywords_analyzed']
            
            if latest_record and 'data_sources' in latest_record:
                summary['latest_sources'] = latest_record['data_sources']
            
            return summary
            
        except Exception as e:
            logger.error(f"MongoDB summary failed: {e}")
            return {}
    
    def get_all_data(self) -> List[Dict[str, Any]]:
        """
        Get all stored data documents
        
        Returns:
            List: All documents or empty list if failed
        """
        if not self.is_connected or self.collection is None:
            logger.error("Not connected to MongoDB")
            return []
        
        try:
            documents = list(self.collection.find({}).sort('creation_timestamp', -1))
            logger.info(f"Retrieved {len(documents)} documents from MongoDB")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving data: {e}")
            return []
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent data document
        
        Returns:
            Dict: Latest document or None if not found
        """
        if not self.is_connected or self.collection is None:
            logger.error("Not connected to MongoDB")
            return None
        
        try:
            latest = self.collection.find_one(sort=[('creation_timestamp', -1)])
            if latest:
                logger.info(f"Retrieved latest document from {latest.get('creation_timestamp', 'unknown time')}")
            return latest
            
        except Exception as e:
            logger.error(f"Error retrieving latest data: {e}")
            return None
    
    def delete_old_data(self, days: int = 30) -> int:
        """
        Delete data older than specified days
        
        Args:
            days (int): Number of days to keep data
            
        Returns:
            int: Number of documents deleted
        """
        if not self.is_connected or self.collection is None:
            logger.error("Not connected to MongoDB")
            return 0
        
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            result = self.collection.delete_many({
                'creation_timestamp': {'$lt': cutoff_date.isoformat()}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"Deleted {deleted_count} old documents (older than {days} days)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting old data: {e}")
            return 0
    
    def close_connection(self):
        """Close MongoDB connection"""
        try:
            if self.client:
                self.client.close()
                self.is_connected = False
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")


def load_cleaned_data(filepath: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load cleaned data from JSON file
    
    Args:
        filepath (str, optional): File path. Uses default if None.
        
    Returns:
        Dict or None: Loaded data or None if failed
    """
    if filepath is None:
        filepath = DATA_PATHS['cleaned_data']
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded cleaned data from: {filepath}")
        return data
        
    except FileNotFoundError:
        logger.error(f"Cleaned data file not found: {filepath}")
        return None
    except Exception as e:
        logger.error(f"Error loading cleaned data: {e}")
        return None


def main():
    """
    Main function to save cleaned data to MongoDB
    """
    print("MongoDB Storage Module")
    print("=" * 40)
    
    db_manager = None
    
    try:
        # Load cleaned data
        print("Loading cleaned data...")
        cleaned_data = load_cleaned_data()
        
        if cleaned_data is None:
            print("No cleaned data found to save.")
            print("   Please run clean_data.py first.")
            return
        
        # Initialize MongoDB manager
        print("Connecting to MongoDB database...")
        db_manager = MongoDBManager()
        
        # Connect to database
        if not db_manager.connect():
            print("Failed to connect to MongoDB.")
            print("   Please check your MongoDB installation and ensure the service is running.")
            print("   Start MongoDB with: net start MongoDB")
            return
        
        # Create indexes
        print("Creating database indexes...")
        if not db_manager.create_indexes():
            print("Some indexes could not be created, but continuing...")
        
        # Save data
        print("Saving data to MongoDB...")
        if db_manager.save_data(cleaned_data):
            print("Data saved successfully!")
            
            # Get and display summary
            print("\nDatabase Summary:")
            summary = db_manager.get_data_summary()
            if summary:
                print(f"   Database: {summary.get('database_name', 'N/A')}")
                print(f"   Collection: {summary.get('collection_name', 'N/A')}")
                print(f"   Total records: {summary.get('total_records', 0)}")
                print(f"   Latest record: {summary.get('latest_record_date', 'N/A')}")
                
                if 'latest_stats' in summary:
                    stats = summary['latest_stats']
                    print(f"   Keywords: {stats.get('total_keywords', 0)}")
                    print(f"   Reddit posts: {stats.get('reddit_posts', 0)}")
                    print(f"   Google data: {stats.get('google_interest_points', 0)} points")
                
                if 'latest_keywords' in summary:
                    keywords = summary['latest_keywords']
                    print(f"   Latest keywords: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
        else:
            print("Failed to save data to MongoDB.")
            
    except KeyboardInterrupt:
        print("\nOperation stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        print(f"Error: {e}")
    finally:
        # Always close the database connection
        if db_manager:
            db_manager.close_connection()


if __name__ == "__main__":
    main() 
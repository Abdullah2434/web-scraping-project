"""
Keyword Management System
========================

Handles dynamic keyword storage, validation, and retrieval for the web scraping project.
Supports user-defined keywords with limits and persistence.

Author: Web Scraping Project
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import DATA_PATHS

# Set up logging
logger = logging.getLogger(__name__)

# Keywords storage file
KEYWORDS_FILE = os.path.join('data', 'user_keywords.json')

# Default keywords if none are set
DEFAULT_USER_KEYWORDS = [
    "artificial intelligence",
    "climate change", 
    "cryptocurrency",
    "space exploration",
    "renewable energy"
]

# Limits
MAX_KEYWORDS = 5
MIN_KEYWORD_LENGTH = 2
MAX_KEYWORD_LENGTH = 50

class KeywordManager:
    """
    Manages user-defined keywords for data collection
    
    Features:
    - Dynamic keyword storage in JSON
    - Validation and limits enforcement
    - Default keywords fallback
    - Last collection tracking
    """
    
    def __init__(self):
        """Initialize keyword manager"""
        self.keywords_file = KEYWORDS_FILE
        self.ensure_keywords_file()
    
    def ensure_keywords_file(self):
        """Ensure keywords file exists with default data"""
        try:
            os.makedirs('data', exist_ok=True)
            
            if not os.path.exists(self.keywords_file):
                default_data = {
                    'keywords': DEFAULT_USER_KEYWORDS,
                    'max_keywords': MAX_KEYWORDS,
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'last_collection': None,
                    'collection_count': 0
                }
                
                with open(self.keywords_file, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2)
                    
                logger.info(f"Created keywords file with defaults: {self.keywords_file}")
            
        except Exception as e:
            logger.error(f"Error ensuring keywords file: {e}")
    
    def get_keywords(self) -> List[str]:
        """
        Get current user keywords
        
        Returns:
            List[str]: List of active keywords
        """
        try:
            with open(self.keywords_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('keywords', DEFAULT_USER_KEYWORDS)
        except Exception as e:
            logger.error(f"Error reading keywords: {e}")
            return DEFAULT_USER_KEYWORDS
    
    def set_keywords(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Set user keywords with validation
        
        Args:
            keywords (List[str]): List of keywords to set
            
        Returns:
            Dict[str, Any]: Result with success status and message
        """
        try:
            # Validate keywords
            validation_result = self.validate_keywords(keywords)
            if not validation_result['valid']:
                return validation_result
            
            # Clean keywords
            cleaned_keywords = self.clean_keywords(keywords)
            
            # Load current data
            with open(self.keywords_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update keywords
            old_keywords = data.get('keywords', [])
            data['keywords'] = cleaned_keywords
            data['last_updated'] = datetime.now().isoformat()
            
            # Save updated data
            with open(self.keywords_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Keywords updated: {old_keywords} -> {cleaned_keywords}")
            
            return {
                'success': True,
                'message': 'Keywords updated successfully',
                'keywords': cleaned_keywords,
                'old_keywords': old_keywords
            }
            
        except Exception as e:
            logger.error(f"Error setting keywords: {e}")
            return {
                'success': False,
                'message': f'Error updating keywords: {str(e)}'
            }
    
    def add_keyword(self, keyword: str) -> Dict[str, Any]:
        """
        Add a single keyword
        
        Args:
            keyword (str): Keyword to add
            
        Returns:
            Dict[str, Any]: Result with success status
        """
        current_keywords = self.get_keywords()
        
        # Check if already exists
        cleaned_keyword = keyword.strip().lower()
        if any(k.lower() == cleaned_keyword for k in current_keywords):
            return {
                'success': False,
                'message': 'Keyword already exists'
            }
        
        # Check limit
        if len(current_keywords) >= MAX_KEYWORDS:
            return {
                'success': False,
                'message': f'Maximum {MAX_KEYWORDS} keywords allowed'
            }
        
        # Add keyword
        new_keywords = current_keywords + [keyword.strip()]
        return self.set_keywords(new_keywords)
    
    def remove_keyword(self, keyword: str) -> Dict[str, Any]:
        """
        Remove a keyword
        
        Args:
            keyword (str): Keyword to remove
            
        Returns:
            Dict[str, Any]: Result with success status
        """
        current_keywords = self.get_keywords()
        cleaned_keyword = keyword.strip().lower()
        
        # Find and remove keyword (case insensitive)
        new_keywords = [k for k in current_keywords if k.lower() != cleaned_keyword]
        
        if len(new_keywords) == len(current_keywords):
            return {
                'success': False,
                'message': 'Keyword not found'
            }
        
        return self.set_keywords(new_keywords)
    
    def validate_keywords(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Validate keyword list
        
        Args:
            keywords (List[str]): Keywords to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        if not isinstance(keywords, list):
            return {
                'valid': False,
                'message': 'Keywords must be a list'
            }
        
        if len(keywords) == 0:
            return {
                'valid': False,
                'message': 'At least one keyword is required'
            }
        
        if len(keywords) > MAX_KEYWORDS:
            return {
                'valid': False,
                'message': f'Maximum {MAX_KEYWORDS} keywords allowed'
            }
        
        # Validate individual keywords
        for keyword in keywords:
            if not isinstance(keyword, str):
                return {
                    'valid': False,
                    'message': 'All keywords must be strings'
                }
            
            cleaned = keyword.strip()
            if len(cleaned) < MIN_KEYWORD_LENGTH:
                return {
                    'valid': False,
                    'message': f'Keywords must be at least {MIN_KEYWORD_LENGTH} characters'
                }
            
            if len(cleaned) > MAX_KEYWORD_LENGTH:
                return {
                    'valid': False,
                    'message': f'Keywords cannot exceed {MAX_KEYWORD_LENGTH} characters'
                }
        
        # Check for duplicates
        cleaned_keywords = [k.strip().lower() for k in keywords]
        if len(set(cleaned_keywords)) != len(cleaned_keywords):
            return {
                'valid': False,
                'message': 'Duplicate keywords are not allowed'
            }
        
        return {
            'valid': True,
            'message': 'Keywords are valid'
        }
    
    def clean_keywords(self, keywords: List[str]) -> List[str]:
        """
        Clean and normalize keywords
        
        Args:
            keywords (List[str]): Raw keywords
            
        Returns:
            List[str]: Cleaned keywords
        """
        cleaned = []
        for keyword in keywords:
            # Strip whitespace and normalize
            clean_keyword = ' '.join(keyword.strip().split())
            if clean_keyword:
                cleaned.append(clean_keyword)
        
        return cleaned
    
    def get_keywords_info(self) -> Dict[str, Any]:
        """
        Get complete keywords information
        
        Returns:
            Dict[str, Any]: Complete keywords data
        """
        try:
            with open(self.keywords_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return {
                'keywords': data.get('keywords', DEFAULT_USER_KEYWORDS),
                'max_keywords': MAX_KEYWORDS,
                'count': len(data.get('keywords', [])),
                'last_updated': data.get('last_updated'),
                'last_collection': data.get('last_collection'),
                'collection_count': data.get('collection_count', 0),
                'limits': {
                    'max_keywords': MAX_KEYWORDS,
                    'min_length': MIN_KEYWORD_LENGTH,
                    'max_length': MAX_KEYWORD_LENGTH
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting keywords info: {e}")
            return {
                'keywords': DEFAULT_USER_KEYWORDS,
                'max_keywords': MAX_KEYWORDS,
                'count': len(DEFAULT_USER_KEYWORDS),
                'last_updated': None,
                'last_collection': None,
                'collection_count': 0,
                'error': str(e)
            }
    
    def update_collection_info(self):
        """Update last collection timestamp"""
        try:
            with open(self.keywords_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data['last_collection'] = datetime.now().isoformat()
            data['collection_count'] = data.get('collection_count', 0) + 1
            
            with open(self.keywords_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating collection info: {e}")
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """
        Reset keywords to defaults
        
        Returns:
            Dict[str, Any]: Reset result
        """
        return self.set_keywords(DEFAULT_USER_KEYWORDS)


# Global keyword manager instance
keyword_manager = KeywordManager()

# Convenience functions
def get_current_keywords() -> List[str]:
    """Get current keywords for data collection"""
    return keyword_manager.get_keywords()

def update_collection_timestamp():
    """Update last collection timestamp"""
    keyword_manager.update_collection_info() 
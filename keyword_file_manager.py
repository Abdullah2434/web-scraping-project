"""
Keyword File Manager
===================

Manages keywords from a simple text file.
Reads keywords from keywords.txt file.
"""

import os
import logging
from typing import List

logger = logging.getLogger(__name__)

def load_keywords_from_file(file_path: str = "keywords.txt") -> List[str]:
    """Load keywords from a text file"""
    keywords = []
    
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Keywords file {file_path} not found. Creating default file.")
            create_default_keywords_file(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            # Remove whitespace and newlines
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Add keyword
            keywords.append(line)
        
        logger.info(f"Loaded {len(keywords)} keywords from {file_path}")
        return keywords
        
    except Exception as e:
        logger.error(f"Error loading keywords from {file_path}: {e}")
        return []

def create_default_keywords_file(file_path: str = "keywords.txt"):
    """Create a default keywords file"""
    default_content = """# Upwork Keywords File
# Add your keywords here, one per line
# Lines starting with # are comments and will be ignored
# 
# Example keywords:
# web development
# python developer
# data analysis
# graphic design
# content writing

# Add your keywords below:
Go-high level
n8n
zapier
React.js
Node.js
Next.js
Android Application
IOS Application
Flutter Application
React Native Application
LLM
RAG
Lang chain
"""
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(default_content)
        logger.info(f"Created default keywords file: {file_path}")
    except Exception as e:
        logger.error(f"Error creating keywords file: {e}")

def add_keyword_to_file(keyword: str, file_path: str = "keywords.txt"):
    """Add a new keyword to the file"""
    try:
        # Load existing keywords
        existing_keywords = load_keywords_from_file(file_path)
        
        # Check if keyword already exists
        if keyword.lower() in [k.lower() for k in existing_keywords]:
            logger.warning(f"Keyword '{keyword}' already exists")
            return False
        
        # Add new keyword to file
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{keyword}")
        
        logger.info(f"Added keyword: {keyword}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding keyword '{keyword}': {e}")
        return False

def remove_keyword_from_file(keyword: str, file_path: str = "keywords.txt"):
    """Remove a keyword from the file"""
    try:
        # Load existing keywords
        existing_keywords = load_keywords_from_file(file_path)
        
        # Remove keyword (case-insensitive)
        filtered_keywords = [k for k in existing_keywords if k.lower() != keyword.lower()]
        
        if len(filtered_keywords) == len(existing_keywords):
            logger.warning(f"Keyword '{keyword}' not found")
            return False
        
        # Rewrite file without the keyword
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove the specific line
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if line.strip().lower() != keyword.lower():
                new_lines.append(line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        logger.info(f"Removed keyword: {keyword}")
        return True
        
    except Exception as e:
        logger.error(f"Error removing keyword '{keyword}': {e}")
        return False

def get_current_keywords() -> List[str]:
    """Get current keywords from file (compatible with existing system)"""
    return load_keywords_from_file()

if __name__ == "__main__":
    # Test the keyword manager
    print("🔍 Testing Keyword File Manager...")
    
    keywords = get_current_keywords()
    print(f"📋 Current keywords: {keywords}")
    
    # Test adding a keyword
    test_keyword = "machine learning"
    success = add_keyword_to_file(test_keyword)
    print(f"➕ Added '{test_keyword}': {success}")
    
    # Test removing a keyword
    success = remove_keyword_from_file(test_keyword)
    print(f"➖ Removed '{test_keyword}': {success}")
    
    print("✅ Keyword file manager test completed!") 
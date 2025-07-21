"""
Enhanced Upwork Job Data Collection Module
=========================================

Advanced scraper with time range and budget filters.
Uses data persistence to append new data instead of overwriting.

Author: Web Scraping Project
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time
import random
from urllib.parse import urlencode, quote_plus
import re
import subprocess
import sys
import os
import pandas as pd

# Import the new data persistence module
from data_persistence import append_upwork_data
from config import DATA_PATHS, ensure_data_directory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Auto-install openpyxl if missing for Excel export
try:
    import openpyxl
    logger.debug("✅ openpyxl is available for Excel export")
except ImportError:
    logger.info("📦 openpyxl not found, installing automatically...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openpyxl'])
        import openpyxl
        logger.info("✅ openpyxl installed successfully!")
    except Exception as install_error:
        logger.error(f"❌ Failed to auto-install openpyxl: {install_error}")

# Data file path
UPWORK_DATA_FILE = DATA_PATHS.get('raw_upwork_data', "data/raw_upwork_data.json")

class UpworkFilters:
    """
    Upwork search filters for advanced filtering
    """
    
    def __init__(self):
        # Simplified time ranges - only today and previous day
        self.time_ranges = {
            'today': '',  # Posted today
            'previous_day': '86400',  # Posted within last 24 hours
        }
        
        # Hourly time filters for more precise timing
        self.hourly_filters = {
            '2_hours': '7200',     # 2 hours ago
            '5_hours': '18000',    # 5 hours ago  
            '10_hours': '36000',   # 10 hours ago
            '24_hours': '86400',   # 24 hours ago (1 day)
        }
        
        self.budget_ranges = {
            'any': '',  # No budget filter
            'under_500': 'amount-500',  # Under $500
            '500_1000': 'amount-500,1000',  # $500-$1000
            '1000_3000': 'amount-1000,3000',  # $1000-$3000
            '3000_5000': 'amount-3000,5000',  # $3000-$5000
            'over_5000': 'amount-5000'  # Over $5000
        }
        
        self.job_types = {
            'any': '',
            'hourly': 'hourly',
            'fixed': 'fixed-price'
        }
        
        self.experience_levels = {
            'any': '',
            'entry': 'entry-level',
            'intermediate': 'intermediate',
            'expert': 'expert'
        }
        
        # Payment verification filters
        self.payment_filters = {
            'both': '',  # No filter, show all
            'verified': 'payment-verified',  # Only verified clients
            'not_verified': 'payment-unverified',  # Only unverified clients
        }
        
        # Countries to exclude from results
        self.excluded_countries = ['Israel', 'India', 'IL', 'IN']
    
    def build_search_url(self, keyword: str, time_range: str = 'today', 
                        budget_range: str = 'any', job_type: str = 'any',
                        experience_level: str = 'any', payment_status: str = 'both',
                        hourly_filter: str = '', sort_by: str = 'recency') -> str:
        """
        Build Upwork search URL with enhanced filters
        
        Args:
            keyword: Search keyword
            time_range: Time range filter (today/previous_day)
            budget_range: Budget range filter
            job_type: Job type filter (hourly/fixed)
            experience_level: Experience level filter
            payment_status: Payment verification filter (verified/not_verified/both)
            hourly_filter: Hourly time filter (2_hours, 5_hours, etc.)
            sort_by: Sort order (recency, client_rating, etc.)
            
        Returns:
            str: Complete search URL with filters
        """
        base_url = "https://www.upwork.com/nx/search/jobs/"
        params = {'q': keyword}
        
        # Add time filter - prioritize hourly filter over general time range
        if hourly_filter and hourly_filter in self.hourly_filters:
            params['t'] = self.hourly_filters[hourly_filter]
        elif time_range != 'today' and time_range in self.time_ranges:
            params['t'] = self.time_ranges[time_range]
        
        # Add budget filter
        if budget_range != 'any' and budget_range in self.budget_ranges:
            params['budget'] = self.budget_ranges[budget_range]
        
        # Add job type filter
        if job_type != 'any' and job_type in self.job_types:
            params['job_type'] = self.job_types[job_type]
        
        # Add experience level filter
        if experience_level != 'any' and experience_level in self.experience_levels:
            params['experience'] = self.experience_levels[experience_level]
        
        # Add payment verification filter
        if payment_status != 'both' and payment_status in self.payment_filters:
            params['payment'] = self.payment_filters[payment_status]
        
        # Add sort parameter
        if sort_by == 'recency':
            params['sort'] = 'recency'
        elif sort_by == 'client_rating':
            params['sort'] = 'client_rating'
        
        # Build final URL
        query_string = urlencode(params)
        return f"{base_url}?{query_string}"
    
    def should_exclude_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Check if job should be excluded based on location filters
        
        Args:
            job_data: Job data dictionary
            
        Returns:
            bool: True if job should be excluded, False otherwise
        """
        try:
            # Check client location
            client_location = job_data.get('client_info', {}).get('location', '').upper()
            
            # Check if location contains excluded countries
            for excluded_country in self.excluded_countries:
                if excluded_country.upper() in client_location:
                    logger.info(f"Excluding job from {client_location}")
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking location filter: {e}")
            return False

def human_delay(min_seconds: float = 3.0, max_seconds: float = 8.0):
    """Human-like delay with random variation"""
    delay = random.uniform(min_seconds, max_seconds)
    logger.info(f"⏳ Waiting {delay:.1f} seconds (human-like behavior)...")
    time.sleep(delay)

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove special characters that might cause issues
    text = re.sub(r'[^\w\s\-\.\,\$\(\)\[\]\/\+\&\%\#\@\!\?]', '', text)
    return text

def is_private_job(job_data: Dict[str, Any]) -> bool:
    """
    Detect if a job is private/confidential and should be skipped
    
    Args:
        job_data: Job data dictionary
        
    Returns:
        bool: True if job appears to be private, False otherwise
    """
    try:
        title = job_data.get('title', '').lower()
        description = job_data.get('description', '').lower()
        
        # Debug logging
        logger.debug(f"🔍 Checking if job is private: Title='{job_data.get('title', '')}', Description length={len(description)}")
        
        # Private job indicators in title
        private_title_indicators = [
            'private job',
            'confidential',
            'title not found',
            'private project',
            'undisclosed',
            'confidential project',
            'stealth',
            'nda required'
        ]
        
        # Check if title indicates private job
        for indicator in private_title_indicators:
            if indicator in title:
                logger.info(f"🔒 Private job detected (title): '{title}' - SKIPPING")
                return True
        
        # Private job indicators in description
        private_desc_indicators = [
            'this is a private job',
            'confidential project',
            'nda required',
            'private listing',
            'details will be shared',
            'more details in private',
            'confidential information',
            'stealth mode'
        ]
        
        # Check if description indicates private job
        for indicator in private_desc_indicators:
            if indicator in description:
                logger.info(f"🔒 Private job detected (description): '{indicator}' - SKIPPING")
                return True
        
        # Check for very generic/minimal titles that often indicate private jobs
        generic_titles = [
            'project',
            'work needed',
            'help needed',
            'assistance required',
            'developer needed',
            'freelancer needed'
        ]
        
        # If title is very short and generic, might be private
        if len(title) < 20 and any(generic in title for generic in generic_titles):
            logger.info(f"🔒 Potentially private job (generic title): '{title}' - SKIPPING")
            return True
        
        # Check for very short descriptions (often private jobs have minimal info)
        if len(description) < 50 and 'private' not in description:
            # This might be too aggressive, so let's be more specific
            short_private_indicators = [
                'details provided',
                'more info',
                'contact for details',
                'will discuss',
                'details in chat'
            ]
            if any(indicator in description for indicator in short_private_indicators):
                logger.info(f"🔒 Private job detected (minimal description): '{description[:50]}...' - SKIPPING")
                return True
        
        # Check if job has "Title not found" which often indicates access issues
        if ('title not found' in title.lower() or 
            title.strip() == '' or 
            title.lower() == 'title not found' or
            'private job' in title.lower()):
            logger.info(f"🔒 Job with no accessible title or private job - SKIPPING: '{title}'")
            return True
        
        return False
        
    except Exception as e:
        logger.debug(f"Error checking if job is private: {e}")
        return False  # If we can't determine, don't skip

def extract_budget_advanced(budget_text: str) -> Dict[str, Any]:
    """
    Enhanced budget extraction with better parsing
    
    Args:
        budget_text: Raw budget text from Upwork
        
    Returns:
        Dict: Structured budget information
    """
    budget_info = {
        'raw_text': budget_text or 'Budget not specified',
        'type': 'unknown',
        'min_amount': 0,
        'max_amount': 0,
        'currency': 'USD',
        'hourly_rate': 0
    }
    
    if not budget_text or budget_text.strip() == '':
        budget_info['raw_text'] = 'Budget not specified'
        return budget_info
    
    # Clean the budget text
    budget_text_clean = budget_text.strip()
    budget_lower = budget_text_clean.lower()
    
    # Store the original text
    budget_info['raw_text'] = budget_text_clean
    
    # Extract numbers from text (improved regex)
    amounts = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', budget_text_clean)
    amounts = [float(amount.replace(',', '')) for amount in amounts if float(amount.replace(',', '')) > 0]
    
    # Determine budget type with more patterns
    if any(word in budget_lower for word in ['hour', '/hr', 'hourly', 'per hour']):
        budget_info['type'] = 'hourly'
        if amounts:
            budget_info['hourly_rate'] = amounts[0]
            budget_info['min_amount'] = amounts[0]
            if len(amounts) > 1:
                budget_info['max_amount'] = amounts[1]
            else:
                budget_info['max_amount'] = amounts[0]
    elif any(word in budget_lower for word in ['fixed', 'project', 'flat', 'one-time', 'fixed-price']):
        budget_info['type'] = 'fixed'
        if amounts:
            budget_info['min_amount'] = amounts[0]
            if len(amounts) > 1:
                budget_info['max_amount'] = amounts[1]
            else:
                budget_info['max_amount'] = amounts[0]
    elif amounts:
        # If we have amounts but no clear type, try to guess
        if len(amounts) == 1:
            budget_info['type'] = 'fixed'
            budget_info['min_amount'] = amounts[0]
            budget_info['max_amount'] = amounts[0]
        else:
            budget_info['type'] = 'hourly'
            budget_info['min_amount'] = amounts[0]
            budget_info['max_amount'] = amounts[1]
            budget_info['hourly_rate'] = amounts[0]
    
    # Ensure we have some usable data
    if budget_info['type'] == 'unknown' and budget_text_clean:
        # If we couldn't parse it but have text, keep the original
        budget_info['raw_text'] = budget_text_clean
    
    return budget_info

def scrape_upwork_with_filters(keywords: List[str], filters: Optional[Dict[str, str]] = None, max_jobs: int = 10) -> List[Dict[str, Any]]:
    """
    Enhanced Upwork scraping with filters
    
    Args:
        keywords: List of search keywords
        filters: Dictionary of filter options
        max_jobs: Maximum number of jobs to extract per keyword
        
    Returns:
        List of job data with filter information
    """
    if filters is None:
        filters = {
            'time_range': 'any',
            'budget_range': 'any', 
            'job_type': 'any',
            'experience_level': 'any',
            'sort_by': 'recency'
        }
    
    logger.info(f"Starting filtered Upwork scraping...")
    logger.info(f"Keywords: {keywords}")
    logger.info(f"Filters: {filters}")
    
    # Import selenium modules (now in requirements.txt)
    try:
        import undetected_chromedriver as uc
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError as e:
        logger.error(f"❌ Missing selenium dependencies: {e}")
        logger.error("💡 Please install: pip install selenium undetected-chromedriver setuptools")
        return []  # Return empty list to match function signature
    
    # Ensure By is available in the calling scope
    def find_elements_safe(driver_or_element, selector):
        """Safe wrapper for find_elements that handles By import"""
        return driver_or_element.find_elements(By.CSS_SELECTOR, selector)
    
    def find_element_safe(driver_or_element, selector):
        """Safe wrapper for find_element that handles By import"""
        return driver_or_element.find_element(By.CSS_SELECTOR, selector)
    
    # Setup browser
    logger.info("Setting up browser...")
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    all_jobs = []
    upwork_filters = UpworkFilters()
    
    try:
        logger.info("Launching browser...")
        driver = uc.Chrome(options=options)
        wait = WebDriverWait(driver, 20)
        
        logger.info("Browser launched successfully!")
        
        # Start with Google to avoid direct detection
        logger.info("Navigating through Google...")
        driver.get("https://www.google.com")
        human_delay(3, 5)
        
        # Process each keyword with filters
        for keyword_index, keyword in enumerate(keywords):
            logger.info(f"Processing keyword {keyword_index + 1}/{len(keywords)}: '{keyword}'")
            
            try:
                # Build filtered search URL
                search_url = upwork_filters.build_search_url(
                    keyword=keyword,
                    time_range=filters.get('time_range', 'any'),
                    budget_range=filters.get('budget_range', 'any'),
                    job_type=filters.get('job_type', 'any'),
                    experience_level=filters.get('experience_level', 'any'),
                    payment_status=filters.get('payment_status', 'both'),
                    hourly_filter=filters.get('hourly_filter', ''),
                    sort_by=filters.get('sort_by', 'recency')
                )
                
                logger.info(f"Navigating to filtered search: {search_url}")
                driver.get(search_url)
                
                # Wait for page load
                human_delay(8, 12)
                
                # Check for Cloudflare or similar protection
                current_title = driver.title.lower()
                if "just a moment" in current_title or "checking" in current_title:
                    logger.info("Detected protection system, waiting...")
                    for i in range(20):
                        time.sleep(5)
                        new_title = driver.title.lower()
                        if "just a moment" not in new_title and "checking" not in new_title:
                            logger.info("Protection bypass successful!")
                            break
                        logger.info(f"   Still waiting... ({(i+1)*5}s)")
                
                # Extract jobs with filter metadata
                page_jobs = extract_jobs_with_metadata(driver, keyword, filters, max_jobs)
                all_jobs.extend(page_jobs)
                
                logger.info(f"Extracted {len(page_jobs)} jobs for '{keyword}' with filters")
                
                # Human delay between keywords
                if keyword_index < len(keywords) - 1:
                    human_delay(5, 10)
                
            except Exception as e:
                logger.error(f"Error processing keyword '{keyword}': {e}")
                continue
        
        logger.info(f"Scraping completed! Total jobs collected: {len(all_jobs)}")
        
    except Exception as e:
        logger.error(f"Browser error: {e}")
    
    finally:
        try:
            driver.quit()
            logger.info("Browser closed")
        except:
            pass
    
    return all_jobs

def extract_jobs_with_metadata(driver, keyword: str, filters: Dict[str, str], max_jobs: int = 10) -> List[Dict[str, Any]]:
    """
    Extract job listings with filter metadata
    
    Args:
        driver: Selenium WebDriver instance
        keyword: Search keyword
        filters: Applied filters
        max_jobs: Maximum number of jobs to extract per keyword
        
    Returns:
        List of job dictionaries with metadata
    """
    # Import selenium By for element selection
    try:
        from selenium.webdriver.common.by import By
    except ImportError:
        # If selenium not available, return empty list
        logger.error("Selenium not available for job extraction")
        return []
    
    jobs = []
    current_time = datetime.now()
    
    try:
        # Wait for job listings to load
        job_selectors = [
            'article[data-test="job-tile"]',
            'section[data-cy="job-tile"]',
            'div[data-test="JobTile"]',
            '.job-tile',
            'article'
        ]
        
        job_elements = []
        for selector in job_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 0:
                    job_elements = elements
                    logger.info(f"Found {len(job_elements)} jobs using selector: {selector}")
                    break
            except:
                continue
        
        if not job_elements:
            logger.warning("⚠️ No job elements found")
            return jobs
        
        # Process each job element
        for i, element in enumerate(job_elements[:max_jobs]):  # Limit to max_jobs parameter
            try:
                job_data = {
                    'id': f"upwork_filtered_{keyword}_{i}_{int(time.time())}",
                    'search_keyword': keyword,
                    'scraped_at': current_time.isoformat(),
                    'filters_applied': filters.copy(),
                    'extraction_method': 'selenium_filtered'
                }
                
                # Extract job title with updated selectors
                title_selectors = [
                    '[data-test="job-title"] a',
                    'h2 a', 
                    'h3 a', 
                    'h4 a',
                    '[data-test*="title"] a',
                    '.job-title a',
                    'a[data-test*="job"]',
                    'h2',  # Fallback without anchor
                    'h3',  # Fallback without anchor
                    'a'    # Any anchor as last resort
                ]
                title = "Title not found"
                job_url = "https://www.upwork.com"
                
                for sel in title_selectors:
                    try:
                        title_elem = element.find_element(By.CSS_SELECTOR, sel)
                        title = clean_text(title_elem.text)
                        href = title_elem.get_attribute('href')
                        if href:
                            job_url = href
                        break
                    except:
                        continue
                
                job_data['title'] = title
                job_data['url'] = job_url
                
                # Early private job detection - check before extracting more data
                if is_private_job(job_data):
                    logger.info(f"🔒 Early detection: Skipping private job from listings: {job_data['title']}")
                    continue
                
                # Extract description with updated selectors
                desc_selectors = [
                    '[data-test="job-description"]',
                    '[data-test*="description"]',
                    'div[data-test="description"]',
                    '.job-description',
                    '[data-cy*="description"]',
                    'p[data-test*="description"]',
                    'div[data-cy*="description"]',
                    'p',  # Generic paragraph fallback
                    'div'  # Generic div fallback
                ]
                description = "Description not available"
                
                for sel in desc_selectors:
                    try:
                        desc_elem = element.find_element(By.CSS_SELECTOR, sel)
                        desc_text = clean_text(desc_elem.text)
                        if len(desc_text) > 50:  # Substantial description
                            description = desc_text[:500]  # Limit length
                            break
                    except:
                        continue
                
                job_data['description'] = description
                
                # Extract budget with advanced parsing - avoid client spending info
                budget_selectors = [
                    '[data-test="budget"]',
                    '[data-test*="budget"]',
                    'span[data-test="budget"]',
                    'span[data-test*="budget"]',
                    '[data-cy*="budget"]',
                    '.budget',
                    # Remove generic selectors that pick up client info
                    # 'strong:contains("$")',  # Too generic
                    # 'span:contains("$")',    # Too generic
                    # 'strong',               # Too generic - picks up client spending
                    # 'span'                  # Too generic - picks up client spending
                ]
                budget_text = "Budget not specified"
                
                for sel in budget_selectors:
                    try:
                        budget_elem = element.find_element(By.CSS_SELECTOR, sel)
                        budget_candidate = clean_text(budget_elem.text)
                        
                        # Enhanced filtering to exclude client spending information
                        if ('$' in budget_candidate and len(budget_candidate) > 3 and
                            # Exclude client spending patterns
                            not any(exclude_pattern in budget_candidate.lower() for exclude_pattern in [
                                'total spent', 'spent', 'hires', 'active', 'hours', 'member since',
                                'rating', 'reviews', 'company', 'client', 'profile', 'k total'
                            ])):
                            budget_text = budget_candidate
                            break
                    except:
                        continue
                
                job_data['budget'] = extract_budget_advanced(budget_text)
                logger.debug(f"  Budget: raw='{budget_text}' -> {job_data['budget']}")
                
                # Extract skills with updated selectors
                skill_selectors = [
                    '[data-test="token"]',
                    '[data-test*="skill"]',
                    '[data-test*="token"]',
                    'span[data-test="skill"]',
                    'span[data-test*="skill"]',
                    '.skill-token',
                    '.token',
                    '[data-cy="skill-token"]',
                    '[data-cy*="skill"]',
                    'span.token',
                    'div.token'
                ]
                skills = []
                
                for sel in skill_selectors:
                    try:
                        skill_elements = element.find_elements(By.CSS_SELECTOR, sel)
                        for skill_elem in skill_elements:
                            skill_text = clean_text(skill_elem.text)
                            if skill_text and len(skill_text) > 2:
                                skills.append(skill_text)
                        if skills:
                            break
                    except:
                        continue
                
                if not skills:
                    skills = [keyword]  # Fallback to search keyword
                
                job_data['skills_required'] = skills[:10]  # Limit skills
                
                # Extract additional details
                job_details = extract_job_details(element)
                job_data['job_details'] = job_details
                
                # Debug logging
                logger.info(f"🔍 Job {i}: Title='{title[:50]}...', Time='{job_details.get('posted_time', {}).get('display', 'Unknown')}', Location='{job_details.get('client_location', 'Unknown')}', Proposals={job_details.get('proposals_count', {}).get('count', 0)}, Payment={job_details.get('payment_verified', {}).get('status', 'unknown')}")
                
                # Create client_info structure that template expects
                job_data['client_info'] = {
                    'location': job_details.get('client_location', 'Not specified'),
                    'rating': job_details.get('client_rating', 0.0),
                    'verified': job_details.get('verified_payment', False)
                }
                
                # Add filter compliance check
                job_data['filter_compliance'] = check_filter_compliance(job_data, filters)
                
                # Check location filter
                filters_instance = UpworkFilters()
                if filters_instance.should_exclude_job(job_data):
                    logger.info(f"Excluding job {job_data['id']} from {job_data['client_info']['location']}")
                    continue
                
                jobs.append(job_data)
                
            except Exception as e:
                logger.warning(f"⚠️ Error extracting job {i}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"❌ Error in job extraction: {e}")
    
    return jobs

def extract_job_details(element) -> Dict[str, Any]:
    """Extract enhanced job details with all new features"""
    # Import selenium By for element selection
    try:
        from selenium.webdriver.common.by import By
    except ImportError:
        # If selenium not available, return default details
        return {
            'posted_time': 'Recently',
            'proposals_count': {'count': 0, 'display': 'No proposals', 'range': 'exact'},
            'job_type': 'Unknown',
            'experience_level': 'All levels',
            'duration': 'Not specified',
            'client_rating': 0.0,
            'client_location': 'Not specified',
            'client_country': 'Unknown',
            'payment_verified': {'status': 'unknown', 'display': 'Payment status unknown', 'verified': False}
        }
    
    # Use the new enhanced extraction functions
    try:
        # Extract enhanced posting time with hourly precision
        posting_time_info = extract_enhanced_posting_time(element)
        
        # Extract proposals count
        proposals_info = extract_proposals_count(element)
        
        # Extract payment verification status
        payment_info = extract_payment_verification(element)
        
        # Extract enhanced client information
        client_info = extract_enhanced_client_info(element)
        
        # Build comprehensive details object
        details = {
            'posted_time': posting_time_info,
            'proposals_count': proposals_info,
            'payment_verified': payment_info,
            'client_location': client_info.get('location', 'Not specified'),
            'client_country': client_info.get('country', 'Unknown'),
            'client_rating': client_info.get('rating', 0.0),
            'client_name': client_info.get('name', 'Unknown Client'),
            'job_type': 'Unknown',
            'experience_level': 'All levels',
            'duration': 'Not specified'
        }
        
        # Filter out "Posted" from location if that's what was extracted
        if details['client_location'] in ['Posted', 'posted', 'POSTED']:
            details['client_location'] = 'Worldwide'
            details['client_country'] = 'Worldwide'
        
        # Extract traditional job details
        try:
            # Extract job type (hourly vs fixed)
            type_selectors = ['[data-test="job-type"]', '.job-type', 'strong', 'span']
            for sel in type_selectors:
                try:
                    type_elem = element.find_element(By.CSS_SELECTOR, sel)
                    type_text = clean_text(type_elem.text).lower()
                    if 'hourly' in type_text:
                        details['job_type'] = 'Hourly'
                        break
                    elif 'fixed' in type_text or 'project' in type_text:
                        details['job_type'] = 'Fixed Price'
                        break
                except:
                    continue
            
            # Extract experience level
            exp_selectors = ['[data-test="experience-level"]', '.experience-level', 'span']
            for sel in exp_selectors:
                try:
                    exp_elem = element.find_element(By.CSS_SELECTOR, sel)
                    exp_text = clean_text(exp_elem.text)
                    if any(level in exp_text.lower() for level in ['entry', 'intermediate', 'expert', 'beginner', 'advanced']):
                        details['experience_level'] = exp_text
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error extracting traditional job details: {e}")
        
        return details
        
    except Exception as e:
        logger.error(f"Error in extract_job_details: {e}")
        return {
            'posted_time': {'original': 'Unknown', 'hours_ago': 0, 'display': 'Recently posted', 'category': 'recent'},
            'proposals_count': {'count': 0, 'display': 'No proposals', 'range': 'exact'},
            'payment_verified': {'status': 'unknown', 'display': 'Payment status unknown', 'verified': False},
            'client_location': 'Not specified',
            'client_country': 'Unknown',
            'client_rating': 0.0,
            'client_name': 'Unknown Client',
            'job_type': 'Unknown',
            'experience_level': 'All levels',
            'duration': 'Not specified'
        }

def check_filter_compliance(job_data: Dict[str, Any], filters: Dict[str, str]) -> Dict[str, bool]:
    """
    Check if job data complies with applied filters
    
    Args:
        job_data: Job data dictionary
        filters: Applied filters
        
    Returns:
        Dict: Compliance status for each filter
    """
    compliance = {
        'budget_compliant': True,
        'time_compliant': True,
        'type_compliant': True,
        'experience_compliant': True,
        'overall_compliant': True
    }
    
    try:
        # Check budget compliance
        budget_filter = filters.get('budget_range', 'any')
        if budget_filter != 'any':
            job_budget = job_data.get('budget', {}).get('min_amount', 0)
            
            if budget_filter == 'under_500' and job_budget >= 500:
                compliance['budget_compliant'] = False
            elif budget_filter == '500_1000' and not (500 <= job_budget <= 1000):
                compliance['budget_compliant'] = False
            elif budget_filter == '1000_3000' and not (1000 <= job_budget <= 3000):
                compliance['budget_compliant'] = False
            elif budget_filter == '3000_5000' and not (3000 <= job_budget <= 5000):
                compliance['budget_compliant'] = False
            elif budget_filter == 'over_5000' and job_budget <= 5000:
                compliance['budget_compliant'] = False
        
        # Check job type compliance
        type_filter = filters.get('job_type', 'any')
        if type_filter != 'any':
            job_type = job_data.get('budget', {}).get('type', 'unknown')
            if type_filter == 'hourly' and job_type != 'hourly':
                compliance['type_compliant'] = False
            elif type_filter == 'fixed' and job_type != 'fixed':
                compliance['type_compliant'] = False
        
        # Overall compliance
        compliance['overall_compliant'] = all([
            compliance['budget_compliant'],
            compliance['time_compliant'],
            compliance['type_compliant'],
            compliance['experience_compliant']
        ])
        
    except Exception as e:
        logger.debug(f"Error checking filter compliance: {e}")
    
    return compliance

def collect_upwork_data_with_filters(keywords: List[str], filters: Optional[Dict[str, str]] = None, 
                                   use_persistence: bool = True, max_jobs: int = 10) -> Dict[str, Any]:
    """
    Main function to collect Upwork data with filters and persistence
    
    Args:
        keywords: List of search keywords
        filters: Dictionary of filter options
        use_persistence: Whether to append to existing data
        max_jobs: Maximum number of jobs to extract per keyword
        
    Returns:
        Dictionary containing collected job data
    """
    logger.info(f"Starting filtered Upwork data collection for {len(keywords)} keywords")
    
    if filters is None:
        filters = {
            'time_range': 'today',  # Default to today
            'hourly_filter': '',  # Default to no hourly filter
            'budget_range': 'any',
            'job_type': 'any',
            'experience_level': 'any',
            'payment_status': 'both',  # Default to show all payment statuses
            'sort_by': 'recency'
        }
    
    logger.info(f"Keywords: {keywords}")
    logger.info(f"Applied filters: {filters}")
    logger.info(f"Using persistence: {use_persistence}")
    
    # Collect jobs with filters
    all_jobs = scrape_upwork_with_filters(keywords, filters, max_jobs)
    
    # Prepare data structure
    collection_stats = {
        'total_jobs': len(all_jobs),
        'keywords_processed': len(keywords),
        'filters_applied': filters,
        'collection_time': datetime.now().isoformat(),
        'method': 'selenium_with_filters',
        'compliance_stats': calculate_compliance_stats(all_jobs)
    }
    
    upwork_data = {
        'jobs': all_jobs,
        'stats': collection_stats,
        'metadata': {
            'total_jobs': len(all_jobs),
            'keywords_analyzed': keywords,
            'collection_timestamp': datetime.now().isoformat(),
            'data_source': 'upwork_filtered_collection',
            'filters_used': filters
        }
    }
    
    # Save data with persistence
    try:
        if use_persistence:
            logger.info("Appending data to existing file...")
            success = append_upwork_data(upwork_data)
            if success:
                logger.info("Data successfully appended to existing collection")
            else:
                logger.warning("Failed to append data, saving as new file")
                with open(UPWORK_DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(upwork_data, f, indent=2, ensure_ascii=False)
        else:
            logger.info("Saving as new file (overwriting existing)...")
            with open(UPWORK_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(upwork_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {UPWORK_DATA_FILE}")
        
    except Exception as e:
        logger.error(f"Failed to save data: {e}")
    
    logger.info(f"Upwork collection completed: {len(all_jobs)} jobs with filters")
    return upwork_data

def calculate_compliance_stats(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics about filter compliance"""
    if not jobs:
        return {'total_jobs': 0, 'compliant_jobs': 0, 'compliance_rate': 0.0}
    
    compliant_jobs = sum(1 for job in jobs 
                        if job.get('filter_compliance', {}).get('overall_compliant', True))
    
    return {
        'total_jobs': len(jobs),
        'compliant_jobs': compliant_jobs,
        'compliance_rate': round((compliant_jobs / len(jobs)) * 100, 2)
    }

# Convenience functions for common filter combinations
def collect_recent_upwork_jobs(keywords: List[str], days: int = 7) -> Dict[str, Any]:
    """Collect recent Upwork jobs within specified days"""
    time_map = {7: 'last_week', 30: 'last_month', 90: 'last_3_months', 180: 'last_6_months'}
    time_range = time_map.get(days, 'last_month')
    
    filters = {
        'time_range': time_range,
        'budget_range': 'any',
        'job_type': 'any',
        'experience_level': 'any',
        'sort_by': 'recency'
    }
    
    return collect_upwork_data_with_filters(keywords, filters)

def collect_high_budget_jobs(keywords: List[str], min_budget: int = 1000) -> Dict[str, Any]:
    """Collect high-budget Upwork jobs"""
    budget_map = {500: 'under_500', 1000: '500_1000', 3000: '1000_3000', 5000: '3000_5000'}
    budget_range = 'over_5000' if min_budget >= 5000 else budget_map.get(min_budget, '1000_3000')
    
    filters = {
        'time_range': 'last_month',
        'budget_range': budget_range,
        'job_type': 'any',
        'experience_level': 'any',
        'sort_by': 'budget'
    }
    
    return collect_upwork_data_with_filters(keywords, filters)

def collect_hourly_jobs(keywords: List[str]) -> Dict[str, Any]:
    """Collect only hourly Upwork jobs"""
    filters = {
        'time_range': 'last_month',
        'budget_range': 'any',
        'job_type': 'hourly',
        'experience_level': 'any',
        'sort_by': 'recency'
    }
    
    return collect_upwork_data_with_filters(keywords, filters)

def collect_fixed_price_jobs(keywords: List[str]) -> Dict[str, Any]:
    """Collect only fixed-price Upwork jobs"""
    filters = {
        'time_range': 'last_month',
        'budget_range': 'any',
        'job_type': 'fixed',
        'experience_level': 'any',
        'sort_by': 'budget'
    }
    
    return collect_upwork_data_with_filters(keywords, filters)

def extract_proposals_count(job_card) -> Dict[str, Any]:
    """
    Extract proposals count from job card
    
    Args:
        job_card: BeautifulSoup or Selenium element
        
    Returns:
        Dict with proposals count information
    """
    try:
        from selenium.webdriver.common.by import By
    except ImportError:
        By = None
    
    proposals_info = {
        'count': 0,
        'display': 'No proposals',
        'range': 'exact'  # exact, 5-10, 10-15, etc.
    }
    
    try:
        # Updated selectors based on actual Upwork HTML structure
        proposal_selectors = [
            # Specific selectors for the new Upwork structure
            'span.value[data-v-1efc9607]',  # From actual HTML
            '.value',
            'span.value',
            # Original selectors as fallback
            '[data-test="proposals"]',
            '[data-test="ProposalsTile"]',
            '[data-test*="proposal"]',
            'span[data-test*="proposal"]',
            '.proposals-count',
            '[data-cy="proposals"]',
            '[data-cy*="proposal"]',
            # Activity section selectors
            '.ca-item .value',
            'li.ca-item span.value',
            # Generic selectors for proposal text
            'span:contains("proposal")',
            'div:contains("proposal")',
            'small:contains("proposal")',
            '*[contains(text(), "proposal")]'
        ]
        
        proposals_text = ""
        
        # If it's a selenium element
        if hasattr(job_card, 'find_element') and By:
            # Try specific selectors first
            for selector in proposal_selectors[:12]:  # First 12 are specific
                try:
                    if 'contains' in selector:
                        # XPath for text content
                        xpath_selector = f"//*[contains(text(), 'proposal')]"
                        element = job_card.find_element(By.XPATH, xpath_selector)
                    else:
                        element = job_card.find_element(By.CSS_SELECTOR, selector)
                    proposals_text = element.text.strip()
                    if proposals_text and ('proposal' in proposals_text.lower() or any(char.isdigit() for char in proposals_text)):
                        break
                except:
                    continue
            
            # Special handling for the activity section structure
            if not proposals_text:
                try:
                    # Look for the proposals section specifically
                    activity_items = job_card.find_elements(By.CSS_SELECTOR, '.ca-item, .client-activity-items li')
                    for item in activity_items:
                        try:
                            item_text = item.text.strip().lower()
                            if 'proposals' in item_text or 'proposal' in item_text:
                                # Find the value within this item
                                value_elem = item.find_element(By.CSS_SELECTOR, '.value, span.value')
                                proposals_text = value_elem.text.strip()
                                break
                        except:
                            continue
                except:
                    pass
            
            # Try to find proposal count in general text elements
            if not proposals_text:
                try:
                    # Look for any text containing proposal numbers
                    all_text_elements = job_card.find_elements(By.CSS_SELECTOR, 'span, div, small, p')
                    for elem in all_text_elements:
                        try:
                            elem_text = elem.text.strip()
                            if (elem_text and 
                                len(elem_text) < 100 and  # Not too long
                                ('proposal' in elem_text.lower() or 'bid' in elem_text.lower()) and
                                any(char.isdigit() for char in elem_text)):
                                proposals_text = elem_text
                                break
                            # Also check for standalone numbers that might be proposal counts
                            elif (elem_text and 
                                  elem_text.isdigit() and 
                                  int(elem_text) < 100 and int(elem_text) > 0):  # Reasonable proposal count range
                                # Check if this number is near proposal-related text
                                parent = elem.find_element(By.XPATH, '..')
                                parent_text = parent.text.strip().lower()
                                if 'proposal' in parent_text or 'bid' in parent_text:
                                    proposals_text = f"{elem_text} proposals"
                                    break
                        except:
                            continue
                except:
                    pass
        
        # Parse proposals count from text
        if proposals_text:
            # Extract number from text like "5 proposals", "10+ proposals", "5-10 proposals", "Less than 5"
            import re
            
            # Look for patterns like "5 proposals", "10+ proposals", "5-10 proposals", "Less than 5"
            patterns = [
                r'less than\s*(\d+)',  # "Less than 5" - priority pattern
                r'(\d+)\+?\s*proposals?',
                r'(\d+)-(\d+)\s*proposals?',
                r'(\d+)\s*to\s*(\d+)\s*proposals?',
                r'more than\s*(\d+)\s*proposals?',
                r'(\d+)'  # Any number as fallback
            ]
            
            for pattern in patterns:
                match = re.search(pattern, proposals_text.lower())
                if match:
                    if 'less than' in proposals_text.lower():
                        count = int(match.group(1))
                        proposals_info['count'] = max(0, count - 1)
                        proposals_info['display'] = f"Less than {count} proposals"
                        proposals_info['range'] = f"<{count}"
                        break
                    elif len(match.groups()) == 1:
                        count = int(match.group(1))
                        if '+' in proposals_text:
                            proposals_info['count'] = count
                            proposals_info['display'] = f"{count}+ proposals"
                            proposals_info['range'] = f"{count}+"
                        elif 'more than' in proposals_text.lower():
                            proposals_info['count'] = count + 1
                            proposals_info['display'] = f"More than {count} proposals"
                            proposals_info['range'] = f">{count}"
                        else:
                            proposals_info['count'] = count
                            proposals_info['display'] = f"{count} proposals"
                            proposals_info['range'] = 'exact'
                        break
                    elif len(match.groups()) == 2:
                        # Range like "5-10"
                        min_count = int(match.group(1))
                        max_count = int(match.group(2))
                        proposals_info['count'] = (min_count + max_count) // 2  # Average
                        proposals_info['display'] = f"{min_count}-{max_count} proposals"
                        proposals_info['range'] = f"{min_count}-{max_count}"
                        break
    
    except Exception as e:
        logger.debug(f"Error extracting proposals count: {e}")
    
    return proposals_info

def extract_payment_verification(job_card) -> Dict[str, Any]:
    """
    Extract payment verification status from job card
    
    Args:
        job_card: BeautifulSoup or Selenium element
        
    Returns:
        Dict with payment verification information
    """
    try:
        from selenium.webdriver.common.by import By
    except ImportError:
        By = None
    
    payment_info = {
        'status': 'unknown',
        'display': 'Payment status unknown',
        'verified': False
    }
    
    try:
        # Updated verification selectors based on actual Upwork HTML structure
        verification_selectors = [
            # About client section selectors
            '.cfe-about-client-v2 .ac-items li',
            '.about-client .ac-items li',
            # Specific verification indicators
            '[data-test="payment-verified"]',
            '[data-test*="verified"]',
            '[data-test*="payment"]',
            'span[data-test*="verified"]',
            '.payment-verified',
            '.verified-badge',
            '.verified',
            '[data-cy="payment-verified"]',
            '[data-cy*="verified"]',
            '[data-cy*="payment"]',
            # Generic selectors for verification text
            'span:contains("verified")',
            'div:contains("verified")',
            'small:contains("verified")',
            '*[contains(text(), "verified")]',
            '*[contains(text(), "Payment verified")]'
        ]
        
        verification_text = ""
        verification_found = False
        
        # If it's a selenium element
        if hasattr(job_card, 'find_element') and By:
            # Try specific selectors first  
            for selector in verification_selectors[:12]:  # First 12 are specific
                try:
                    if 'contains' in selector:
                        xpath_selector = f"//*[contains(text(), 'verified') or contains(text(), 'Verified') or contains(text(), 'payment') or contains(text(), 'Payment')]"
                        element = job_card.find_element(By.XPATH, xpath_selector)
                    else:
                        element = job_card.find_element(By.CSS_SELECTOR, selector)
                    verification_text = element.text.strip().lower()
                    if verification_text and ('verified' in verification_text or 'payment' in verification_text):
                        verification_found = True
                        break
                except:
                    continue
            
            # Check for visual indicators (checkmarks, badges, etc.) in about client section
            if not verification_found:
                try:
                    about_client_section = job_card.find_element(By.CSS_SELECTOR, '.cfe-about-client-v2, .about-client')
                    
                    # Look for verification indicators in client info
                    verification_indicators = [
                        '.fa-check',
                        '.checkmark',
                        '.verified-icon',
                        'svg[data-test="icon-verified"]',
                        '.fa-shield',
                        '.fa-shield-alt',
                        'i[class*="check"]',
                        'i[class*="verified"]'
                    ]
                    
                    for indicator in verification_indicators:
                        try:
                            about_client_section.find_element(By.CSS_SELECTOR, indicator)
                            payment_info['status'] = 'verified'
                            payment_info['verified'] = True
                            payment_info['display'] = 'Payment verified'
                            verification_found = True
                        except:
                            continue
                            
                    # Also check for "Member since" date - newer accounts may be less verified
                    if not verification_found:
                        try:
                            member_since_elem = about_client_section.find_element(By.CSS_SELECTOR, 'small')
                            member_text = member_since_elem.text.strip()
                            if 'member since' in member_text.lower():
                                # Extract year and make assumption based on account age
                                import re
                                year_match = re.search(r'(\d{4})', member_text)
                                if year_match:
                                    year = int(year_match.group(1))
                                    from datetime import datetime
                                    current_year = datetime.now().year
                                    if current_year - year >= 1:  # Account 1+ years old
                                        payment_info['status'] = 'likely_verified'
                                        payment_info['verified'] = True
                                        payment_info['display'] = 'Likely verified (established account)'
                                        verification_found = True
                        except:
                            pass
                except:
                    pass
            
            # If no specific selector worked, search through all elements for verification text
            if not verification_found:
                try:
                    all_elements = job_card.find_elements(By.CSS_SELECTOR, 'small, span, div, i')  # Include icons
                    for elem in all_elements:
                        try:
                            elem_text = elem.text.strip().lower()
                            elem_class = elem.get_attribute('class') or ''
                            elem_title = elem.get_attribute('title') or ''
                            
                            # Check text content
                            if elem_text and ('verified' in elem_text or 'payment' in elem_text):
                                verification_text = elem_text
                                verification_found = True
                                break
                            # Check class names for verification indicators
                            elif 'verified' in elem_class.lower() or 'check' in elem_class.lower():
                                verification_text = 'verified'
                                verification_found = True
                                break
                            # Check title attributes
                            elif 'verified' in elem_title.lower() or 'payment' in elem_title.lower():
                                verification_text = elem_title.lower()
                                verification_found = True
                                break
                        except:
                            continue
                except:
                    pass
        
        # Also check for class names or data attributes indicating verification
        if not verification_found and hasattr(job_card, 'get_attribute'):
            try:
                class_names = job_card.get_attribute('class') or ''
                if 'verified' in class_names.lower():
                    verification_text = 'verified'
                    verification_found = True
            except:
                pass
        
        # Parse verification status
        if verification_found and verification_text:
            if any(word in verification_text for word in ['verified', 'payment verified', 'badge', 'check']):
                payment_info['status'] = 'verified'
                payment_info['verified'] = True
                payment_info['display'] = 'Payment verified'
            elif any(word in verification_text for word in ['unverified', 'not verified', 'no payment']):
                payment_info['status'] = 'not_verified'
                payment_info['verified'] = False
                payment_info['display'] = 'Payment not verified'
            elif 'likely' in verification_text:
                # Keep the likely_verified status set earlier
                pass
        
        # If still unknown, make educated guess based on other factors
        if payment_info['status'] == 'unknown':
            # Default to unknown but with helpful message
            payment_info['display'] = 'Payment status not verified'
    
    except Exception as e:
        logger.debug(f"Error extracting payment verification: {e}")
    
    return payment_info

def extract_enhanced_client_info(job_card) -> Dict[str, Any]:
    """
    Extract enhanced client information including country parsing
    
    Args:
        job_card: BeautifulSoup or Selenium element
        
    Returns:
        Dict with enhanced client information
    """
    try:
        from selenium.webdriver.common.by import By
    except ImportError:
        By = None
    
    client_info = {
        'name': 'Unknown Client',
        'location': 'Unknown',
        'country': 'Unknown',
        'rating': 0.0,
        'reviews_count': 0,
        'verified': False
    }
    
    try:
        # Updated location selectors based on actual Upwork HTML structure
        location_selectors = [
            # Specific selectors from actual Upwork HTML
            'strong[data-v-ea8e3ca4]',  # From actual HTML: <strong data-v-ea8e3ca4="">Bangladesh</strong>
            'li[data-qa="client-location"] strong',  # Client location section
            '.ac-items li strong',  # About client items
            # Original selectors as fallback
            '[data-test="client-location"]',
            '[data-test*="location"]',
            '[data-test*="client"]',
            'span[data-test*="location"]',
            '.client-location',
            '[data-cy="location"]',
            '[data-cy*="location"]',
            '[data-cy*="client"]',
            '.location',
            # Generic selectors
            'strong',  # Many locations are in strong tags
            'small'  # Fallback - many location details are in small tags
        ]
        
        location_text = ""
        
        if hasattr(job_card, 'find_element') and By:
            # Try specific selectors first
            for selector in location_selectors:
                try:
                    if 'contains' in selector:
                        xpath_selector = "//*[contains(@class, 'location') or contains(text(), 'location')]"
                        element = job_card.find_element(By.XPATH, xpath_selector)
                    else:
                        element = job_card.find_element(By.CSS_SELECTOR, selector)
                    candidate_text = element.text.strip()
                    
                    # Filter out non-location text
                    if (candidate_text and 
                        candidate_text.lower() not in ['location', 'client location', 'unknown', '', 'member since', 'about the client', 'posted'] and
                        len(candidate_text) > 2 and len(candidate_text) < 50 and
                        not candidate_text.startswith(('$', '€', '£', '+', '-', '(', ')')) and
                        not candidate_text.lower().startswith(('posted', 'fixed', 'hourly', 'entry', 'intermediate', 'expert')) and
                        not any(word in candidate_text.lower() for word in ['rating', 'star', 'review', 'job', 'project', 'hour', 'ago', 'posted', 'minute', 'day'])):
                        location_text = candidate_text
                        break
                except:
                    continue
            
            # Special handling for about client section
            if not location_text or location_text.lower() in ['location', 'client location', 'unknown', '']:
                try:
                    # Look for the about client section specifically
                    about_client_section = job_card.find_element(By.CSS_SELECTOR, '.cfe-about-client-v2, .about-client')
                    location_items = about_client_section.find_elements(By.CSS_SELECTOR, 'li, .ac-items li')
                    
                    for item in location_items:
                        try:
                            item_text = item.text.strip()
                            # Look for location-like patterns in the item
                            if any(attr in item.get_attribute('data-qa') or '' for attr in ['location', 'client-location']):
                                strong_elem = item.find_element(By.CSS_SELECTOR, 'strong')
                                location_text = strong_elem.text.strip()
                                break
                            # Or check if the strong text looks like a location
                            elif item.find_elements(By.CSS_SELECTOR, 'strong'):
                                strong_elem = item.find_element(By.CSS_SELECTOR, 'strong')
                                strong_text = strong_elem.text.strip()
                                if (strong_text and len(strong_text) > 2 and len(strong_text) < 50 and
                                    strong_text[0].isupper() and 
                                    not any(word in strong_text.lower() for word in ['rating', 'star', 'review', 'hour', 'ago', 'since'])):
                                    location_text = strong_text
                                    break
                        except:
                            continue
                except:
                    pass
            
            # If still no location found, search through all elements for location-like text
            if not location_text or location_text.lower() in ['location', 'client location', 'unknown', '']:
                try:
                    all_elements = job_card.find_elements(By.CSS_SELECTOR, 'small, span, div, strong')
                    
                    # Common country/location patterns
                    country_patterns = [
                        'united states', 'usa', 'us', 'canada', 'uk', 'united kingdom', 'australia', 'germany', 
                        'france', 'india', 'pakistan', 'bangladesh', 'israel', 'netherlands', 'spain', 'italy',
                        'brazil', 'mexico', 'argentina', 'poland', 'ukraine', 'russia', 'china', 'japan',
                        'south korea', 'singapore', 'malaysia', 'thailand', 'philippines', 'indonesia',
                        'south africa', 'egypt', 'nigeria', 'kenya', 'morocco', 'tunisia', 'algeria', 'worldwide'
                    ]
                    
                    for elem in all_elements:
                        try:
                            elem_text = elem.text.strip()
                            if elem_text and len(elem_text) > 2 and len(elem_text) < 50:
                                elem_lower = elem_text.lower()
                                # Check if it matches country patterns
                                if any(country in elem_lower for country in country_patterns):
                                    location_text = elem_text
                                    break
                                # Or if it's a capitalized word that could be a location
                                elif (elem_text[0].isupper() and ' ' not in elem_text and 
                                      elem_text.isalpha() and len(elem_text) > 3 and len(elem_text) < 20):
                                    location_text = elem_text
                                    break
                        except:
                            continue
                except:
                    pass
        
        if location_text and location_text != 'Unknown':
            client_info['location'] = location_text
            
            # Parse country from location
            # Common patterns: "Country", "City, Country", "State, Country"
            country_mapping = {
                'united states': 'United States',
                'usa': 'United States', 
                'us': 'United States',
                'uk': 'United Kingdom',
                'united kingdom': 'United Kingdom',
                'canada': 'Canada',
                'australia': 'Australia',
                'germany': 'Germany',
                'france': 'France',
                'india': 'India',
                'israel': 'Israel',
                'pakistan': 'Pakistan',
                'bangladesh': 'Bangladesh',
                'philippines': 'Philippines',
                'ukraine': 'Ukraine',
                'poland': 'Poland',
                'brazil': 'Brazil',
                'mexico': 'Mexico',
                'argentina': 'Argentina',
                'colombia': 'Colombia',
                'spain': 'Spain',
                'italy': 'Italy',
                'netherlands': 'Netherlands',
                'sweden': 'Sweden',
                'norway': 'Norway',
                'denmark': 'Denmark',
                'worldwide': 'Worldwide'
            }
            
            # Try to extract country
            location_lower = location_text.lower()
            for key, country in country_mapping.items():
                if key in location_lower:
                    client_info['country'] = country
                    break
            
            # If no mapping found, try to extract last part after comma
            if client_info['country'] == 'Unknown' and ',' in location_text:
                potential_country = location_text.split(',')[-1].strip()
                if len(potential_country) > 2:
                    client_info['country'] = potential_country.title()
            elif client_info['country'] == 'Unknown':
                # Use the location as country if it's a single word/country
                client_info['country'] = location_text
        
        # Extract client rating - updated selectors
        rating_selectors = [
            '[data-test="client-rating"]',
            '.client-rating',
            '.rating',
            '.client-stats .rating',
            '*[contains(text(), "★")]/..',
            '.stars'
        ]
        
        if hasattr(job_card, 'find_element') and By:
            for selector in rating_selectors:
                try:
                    element = job_card.find_element(By.CSS_SELECTOR, selector)
                    rating_text = element.text.strip()
                    # Extract rating number (like "4.5" from "4.5 ★" or "4.5/5")
                    import re
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                        if 0 <= rating <= 5:
                            client_info['rating'] = rating
                        break
                except:
                    continue
    
    except Exception as e:
        logger.debug(f"Error extracting enhanced client info: {e}")
    
    return client_info

def extract_enhanced_posting_time(job_card) -> Dict[str, Any]:
    """
    Extract enhanced posting time with hourly precision
    
    Args:
        job_card: BeautifulSoup or Selenium element
        
    Returns:
        Dict with detailed posting time information
    """
    try:
        from selenium.webdriver.common.by import By
    except ImportError:
        By = None
    
    time_info = {
        'original': 'Unknown',
        'hours_ago': 0,
        'display': 'Recently posted',
        'category': 'recent'  # recent, hours, days, weeks, months
    }
    
    try:
        # Updated time selectors based on actual Upwork HTML structure
        time_selectors = [
            # Specific selectors from actual Upwork HTML
            'span[data-v-44870f71]',  # From actual HTML: <span>44 minutes ago</span>
            '.posted-on-line span',  # Posted on line section
            '[data-test="PostedOn"] span',  # Posted on element
            # Original selectors as fallback
            '[data-test="posted-on"]',
            '[data-test="JobPostedOn"]', 
            'small[data-test*="posted"]',
            'span[data-test*="posted"]',
            '.posted-on',
            '.job-date',
            '.timestamp',
            'small:contains("ago")',
            'span:contains("ago")',
            'time',
            '[data-cy*="posted"]',
            'small',  # Fallback to all small tags
            'span'    # Fallback to all spans
        ]
        
        time_text = ""
        
        if hasattr(job_card, 'find_element') and By:
            # Try specific selectors first
            for selector in time_selectors[:10]:  # First 10 are specific
                try:
                    if 'contains' in selector:
                        xpath_selector = "//*[contains(text(), 'ago') or contains(text(), 'posted') or contains(text(), 'hour') or contains(text(), 'minute')]"
                        element = job_card.find_element(By.XPATH, xpath_selector)
                    else:
                        element = job_card.find_element(By.CSS_SELECTOR, selector)
                    candidate_text = element.text.strip()
                    
                    # Check if this looks like a time indication
                    if (candidate_text and 
                        ('ago' in candidate_text.lower() or 
                         'posted' in candidate_text.lower() or 
                         'hour' in candidate_text.lower() or 
                         'minute' in candidate_text.lower()) and
                        len(candidate_text) < 50):  # Reasonable length for time text
                        time_text = candidate_text
                        break
                except:
                    continue
            
            # Special handling for the posted-on section
            if not time_text:
                try:
                    # Look for the posted on section specifically
                    posted_section = job_card.find_element(By.CSS_SELECTOR, '.posted-on-line, [data-test="PostedOn"]')
                    time_spans = posted_section.find_elements(By.CSS_SELECTOR, 'span')
                    
                    for span in time_spans:
                        try:
                            span_text = span.text.strip()
                            if (span_text and 
                                ('ago' in span_text.lower() or 
                                 'hour' in span_text.lower() or 
                                 'minute' in span_text.lower() or
                                 'day' in span_text.lower()) and
                                any(char.isdigit() for char in span_text)):
                                time_text = span_text
                                break
                        except:
                            continue
                except:
                    pass
            
            # If no specific selector worked, search through all small and span elements
            if not time_text:
                try:
                    all_elements = job_card.find_elements(By.CSS_SELECTOR, 'small, span, div')
                    for elem in all_elements:
                        try:
                            elem_text = elem.text.strip()
                            elem_lower = elem_text.lower()
                            
                            # Look for time patterns
                            if (elem_text and len(elem_text) < 50 and
                                (('ago' in elem_lower) or 
                                 ('hour' in elem_lower and any(word in elem_lower for word in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'])) or 
                                 ('minute' in elem_lower and any(char.isdigit() for char in elem_text)) or 
                                 ('day' in elem_lower and 'ago' in elem_lower))):
                                time_text = elem_text
                                break
                        except:
                            continue
                except:
                    pass
        
        if time_text:
            time_info['original'] = time_text
            
            # Parse time with improved regex patterns
            import re
            
            # Extract numbers and time units
            time_lower = time_text.lower()
            
            # Handle specific patterns like "44 minutes ago"
            minutes_match = re.search(r'(\d+)\s*minutes?\s*ago', time_lower)
            hours_match = re.search(r'(\d+)\s*hours?\s*ago', time_lower)
            days_match = re.search(r'(\d+)\s*days?\s*ago', time_lower)
            weeks_match = re.search(r'(\d+)\s*weeks?\s*ago', time_lower)
            months_match = re.search(r'(\d+)\s*months?\s*ago', time_lower)
            
            if minutes_match:
                minutes = int(minutes_match.group(1))
                time_info['hours_ago'] = minutes / 60.0
                time_info['display'] = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                time_info['category'] = 'recent' if minutes < 60 else 'hours'
            elif hours_match:
                hours = int(hours_match.group(1))
                time_info['hours_ago'] = hours
                time_info['display'] = f"{hours} hour{'s' if hours != 1 else ''} ago"
                time_info['category'] = 'hours'
            elif days_match:
                days = int(days_match.group(1))
                time_info['hours_ago'] = days * 24
                time_info['display'] = f"{days} day{'s' if days != 1 else ''} ago"
                time_info['category'] = 'days'
            elif weeks_match:
                weeks = int(weeks_match.group(1))
                time_info['hours_ago'] = weeks * 7 * 24
                time_info['display'] = f"{weeks} week{'s' if weeks != 1 else ''} ago"
                time_info['category'] = 'weeks'
            elif months_match:
                months = int(months_match.group(1))
                time_info['hours_ago'] = months * 30 * 24  # Approximate
                time_info['display'] = f"{months} month{'s' if months != 1 else ''} ago"
                time_info['category'] = 'months'
            else:
                # Fallback: just use the original text
                time_info['display'] = time_text
                time_info['category'] = 'recent'
                
                # Try to extract any number as a fallback estimate
                number_match = re.search(r'(\d+)', time_text)
                if number_match:
                    number = int(number_match.group(1))
                    if 'hour' in time_lower:
                        time_info['hours_ago'] = number
                        time_info['category'] = 'hours'
                    elif 'day' in time_lower:
                        time_info['hours_ago'] = number * 24
                        time_info['category'] = 'days'
                    elif 'minute' in time_lower:
                        time_info['hours_ago'] = number / 60.0
                        time_info['category'] = 'recent' if number < 60 else 'hours'
        else:
            # No time found, use defaults
            time_info['display'] = 'Recently posted'
            time_info['category'] = 'recent'
    
    except Exception as e:
        logger.debug(f"Error extracting posting time: {e}")
    
    return time_info

def scrape_individual_job_page(driver, job_url: str, keyword: str, skip_private_jobs: bool = True) -> Dict[str, Any]:
    """
    Scrape detailed information from an individual Upwork job page
    
    Args:
        driver: Selenium WebDriver instance
        job_url: URL of the individual job page
        keyword: Search keyword that found this job
        skip_private_jobs: Whether to skip private/confidential jobs (default: True)
        
    Returns:
        Dictionary with comprehensive job details
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    current_time = datetime.now()
    job_data: Dict[str, Any] = {
        'id': f"upwork_detailed_{int(time.time())}_{random.randint(1000, 9999)}",
        'search_keyword': keyword,
        'scraped_at': current_time.isoformat(),
        'url': job_url,
        'extraction_method': 'individual_job_page',
        'data_quality': 'comprehensive'
    }
    
    try:
        logger.info(f"🔍 Visiting individual job page: {job_url}")
        driver.get(job_url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 15)
        human_delay(3, 6)  # Let page fully load
        
        # Extract job title - using the exact selectors from the individual job page HTML
        title_selectors = [
            'h1.m-0.h4[data-v-44870f71]',  # Exact match from HTML
            'h1[data-v-44870f71]',         # Broader match
            'h1.h4',                       # Class-based fallback
            'h1',                          # Generic fallback
            'header h1'                    # Header fallback
        ]
        title = "Title not found"
        for selector in title_selectors:
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, selector)
                title = clean_text(title_elem.text)
                if title and len(title) > 5:
                    logger.info(f"✅ Found title with selector '{selector}': {title[:50]}...")
                    break
            except Exception as e:
                logger.debug(f"❌ Title selector '{selector}' failed: {e}")
                continue
        
        job_data['title'] = title
        logger.info(f"📝 Title: {title}")
        
        # Check if this is a private job - if so, skip it (only if skip_private_jobs is enabled)
        if skip_private_jobs and is_private_job(job_data):
            logger.warning(f"🔒 SKIPPING private job: {title}")
            return {
                'id': job_data['id'],
                'search_keyword': keyword,
                'scraped_at': current_time.isoformat(),
                'url': job_url,
                'title': title,
                'description': 'Private job - skipped',
                'skipped': True,
                'skip_reason': 'private_job',
                'extraction_method': 'skipped_private',
                'budget': {'raw_text': 'Private job', 'type': 'unknown'},
                'job_details': {
                    'posted_time': {'display': 'Private job'},
                    'proposals_count': {'display': 'Private'},
                    'experience_level': 'Private',
                    'duration': 'Private',
                    'client_location': 'Private',
                    'payment_verified': {'status': 'unknown', 'verified': False}
                },
                'client_info': {
                    'location': 'Private',
                    'rating': 0.0,
                    'verified': False
                },
                'skills_required': []
            }
        
        # Extract posting time (much more precise)
        posted_time = extract_detailed_posting_time(driver)
        job_data['posted_time'] = posted_time
        logger.info(f"⏰ Posted: {posted_time.get('display', 'Unknown')}")
        
        # Extract comprehensive budget information
        budget_info = extract_detailed_budget(driver)
        job_data['budget'] = budget_info
        logger.info(f"💰 Budget: {budget_info.get('raw_text', 'Unknown')}")
        
        # Extract detailed job description
        description = extract_detailed_description(driver)
        job_data['description'] = description
        logger.info(f"📄 Description length: {len(description)} characters")
        
        # Extract job features from the specific features section (NOT client info)
        features_info = extract_job_features_section(driver)
        job_data['features'] = features_info
        logger.info(f"⚙️ Features: Work Hours: {features_info.get('work_hours', 'Unknown')}, Experience: {features_info.get('experience_level', 'Unknown')}")
        
        # Extract project details (duration, experience level, etc.) - fallback method
        project_details = extract_project_details(driver)
        job_data['project_details'] = project_details
        logger.info(f"🎯 Experience Level: {project_details.get('experience_level', 'Unknown')}")
        
        # Extract activity information (proposals, interviews, invites)
        activity_info = extract_activity_information(driver)
        job_data['activity'] = activity_info
        logger.info(f"👥 Proposals: {activity_info.get('proposals', {}).get('display', 'Unknown')}")
        
        # Extract client information
        client_info = extract_detailed_client_info(driver)
        job_data['client_info'] = client_info
        logger.info(f"🌍 Client Location: {client_info.get('location', 'Unknown')}")
        
        # Extract payment verification status
        payment_info = extract_detailed_payment_verification(driver)
        job_data['payment_verification'] = payment_info
        logger.info(f"💳 Payment Status: {payment_info.get('status', 'Unknown')}")
        
        # Extract skills and requirements
        skills_info = extract_skills_and_requirements(driver)
        job_data['skills_required'] = skills_info.get('skills', [])
        job_data['mandatory_skills'] = skills_info.get('mandatory_skills', [])
        logger.info(f"🛠️ Skills: {len(job_data['skills_required'])} total")
        
        # Extract location information
        location_info = extract_location_details(driver)
        job_data['location'] = location_info
        logger.info(f"📍 Job Location: {location_info.get('type', 'Unknown')}")
        
        # Create legacy-compatible structure for existing template - prioritize features section
        job_data['job_details'] = {
            'posted_time': posted_time,
            'proposals_count': activity_info.get('proposals', {}),
            # Prioritize features section data over fallback methods
            'experience_level': (features_info.get('experience_level') if features_info.get('experience_level') != 'Not specified' 
                               else project_details.get('experience_level', 'All levels')),
            'duration': (features_info.get('duration') if features_info.get('duration') != 'Not specified'
                        else project_details.get('duration', 'Duration flexible')),
            'job_type': (features_info.get('job_type') if features_info.get('job_type') != 'Not specified'
                        else project_details.get('job_type', 'Not specified')),
            'work_hours': features_info.get('work_hours', 'Not specified'),
            'location_type': features_info.get('location_type', 'Not specified'),
            'project_type': features_info.get('project_type', 'Not specified'),
            'client_location': client_info.get('location', 'Worldwide'),
            'client_rating': client_info.get('rating', 0.0),
            'payment_verified': payment_info,
            'verified_payment': payment_info.get('verified', False)
        }
        
        logger.info(f"✅ Successfully extracted comprehensive data from individual job page")
        return job_data
        
    except Exception as e:
        logger.error(f"❌ Error scraping individual job page {job_url}: {e}")
        # Return basic job data with error info
        job_data.update({
            'title': 'Error extracting title',
            'description': 'Error occurred while extracting job details',
            'error': str(e),
            'budget': {'raw_text': 'Error extracting budget', 'type': 'unknown'},
            'job_details': {
                'posted_time': {'display': 'Error extracting time'},
                'proposals_count': {'display': 'Error'},
                'experience_level': 'Unknown',
                'duration': 'Unknown',
                'client_location': 'Unknown',
                'payment_verified': {'status': 'unknown', 'verified': False}
            },
            'client_info': {
                'location': 'Unknown',
                'rating': 0.0,
                'verified': False
            },
            'skills_required': []
        })
        return job_data

def extract_detailed_posting_time(driver) -> Dict[str, Any]:
    """Extract precise posting time from individual job page"""
    from selenium.webdriver.common.by import By
    
    # Based on actual individual job page HTML structure
    time_selectors = [
        # Exact selectors from the individual job page HTML
        '[data-test="PostedOn"] span',                    # "44 minutes ago" from exact HTML
        '.posted-on-line span',                           # Posted on line span
        '.text-light-on-muted span',                      # Light muted text spans
        'div[data-v-44870f71] span',                     # Div with data attribute spans
        '.mt-5.d-flex span',                             # Margin top flex spans
        'small span',                                     # Small tag spans (fallback)
        'span',                                          # Last resort - any span
    ]
    
    for selector_index, selector in enumerate(time_selectors):
        try:
            time_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            logger.debug(f"🔍 Time selector {selector_index + 1}: '{selector}' found {len(time_elements)} elements")
            
            for elem in time_elements:
                time_text = clean_text(elem.text)
                logger.debug(f"   Checking time text: '{time_text}'")
                
                # Check if this looks like a time indication
                if (time_text and len(time_text) < 50 and  # Reasonable length
                    any(word in time_text.lower() for word in ['ago', 'minute', 'hour', 'day', 'week', 'second']) and
                    not time_text.lower().startswith(('posted', 'member', 'last', 'duration'))):  # Avoid false matches
                    
                    logger.info(f"✅ Found posting time with selector '{selector}': {time_text}")
                    return {
                        'display': time_text,
                        'original': time_text,
                        'extracted_at': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.debug(f"❌ Time selector '{selector}' failed: {e}")
            continue
    
    logger.warning("❌ No posting time found")
    return {'display': 'Recently posted', 'original': 'Unknown', 'extracted_at': datetime.now().isoformat()}

def extract_job_features_section(driver) -> Dict[str, Any]:
    """Extract data specifically from the job features section - NOT client info"""
    from selenium.webdriver.common.by import By
    
    features_info = {
        'work_hours': 'Not specified',
        'job_type': 'Not specified', 
        'duration': 'Not specified',
        'experience_level': 'Not specified',
        'location_type': 'Not specified',
        'project_type': 'Not specified'
    }
    
    try:
        # Look specifically for the features section the user wants
        features_selectors = [
            'section[data-test="Features"] .features li',
            'section.air3-card-section[data-test="Features"] li',
            '[data-test="Features"] ul.features li',
            'ul.features.list-unstyled li'
        ]
        
        for selector in features_selectors:
            try:
                feature_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.debug(f"Found {len(feature_elements)} feature elements with selector: {selector}")
                
                for feature_elem in feature_elements:
                    try:
                        strong_elem = feature_elem.find_element(By.CSS_SELECTOR, 'strong')
                        desc_elem = feature_elem.find_element(By.CSS_SELECTOR, '.description')
                        
                        strong_text = clean_text(strong_elem.text)
                        desc_text = clean_text(desc_elem.text)
                        
                        logger.debug(f"Feature: '{strong_text}' - '{desc_text}'")
                        
                        # Map based on description type
                        if 'hourly' in desc_text.lower():
                            features_info['work_hours'] = strong_text
                            features_info['job_type'] = desc_text
                        elif 'duration' in desc_text.lower():
                            features_info['duration'] = strong_text
                        elif 'experience' in desc_text.lower():
                            features_info['experience_level'] = strong_text
                        elif 'remote' in strong_text.lower():
                            features_info['location_type'] = strong_text
                        elif 'project' in desc_text.lower():
                            features_info['project_type'] = strong_text
                            
                    except Exception as e:
                        logger.debug(f"Error parsing feature element: {e}")
                        continue
                        
                if any(v != 'Not specified' for v in features_info.values()):
                    break  # Found features, stop trying other selectors
                    
            except Exception as e:
                logger.debug(f"Features selector '{selector}' failed: {e}")
                continue
                
    except Exception as e:
        logger.debug(f"Error extracting job features: {e}")
    
    return features_info

def extract_detailed_budget(driver) -> Dict[str, Any]:
    """Extract comprehensive budget information from individual job page"""
    from selenium.webdriver.common.by import By
    
    budget_info = {
        'raw_text': 'Budget not available',
        'type': 'unknown',
        'min_amount': 0,
        'max_amount': 0,
        'hourly_rate': 0,
        'is_fixed': False,
        'is_hourly': False
    }
    
    try:
        # Look for budget ONLY in the job features section - avoid client spending info
        budget_selectors = [
            # Based on actual individual job page HTML structure - specific to job details
            '[data-test="BudgetAmount"] strong[data-v-2638f5cd]',  # Exact match from HTML
            '[data-test="BudgetAmount"] strong',                  # "$500.00"  
            '[data-test="BudgetAmount"] p strong',                # Paragraph with strong
            # Only look in features section - NOT in client info
            '[data-test="Features"] .features li strong',         # Features list strong tags
            '[data-test="Features"] li strong',                   # Features section only
            'section[data-test="Features"] .features li strong',  # Specific features section
            'section.air3-card-section[data-test="Features"] li strong',  # User's HTML structure
            'li[data-v-ca6db23e] strong',                        # List item strong (from HTML)
            '[data-cy="fixed-price"] + div strong',              # Fixed price context
            '[data-cy="hourly"] + div strong',                   # Hourly context
        ]
        
        budget_text = ""
        for selector_index, selector in enumerate(budget_selectors):
            try:
                budget_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.debug(f"🔍 Budget selector {selector_index + 1}: '{selector}' found {len(budget_elements)} elements")
                
                for budget_elem in budget_elements:
                    candidate_text = clean_text(budget_elem.text)
                    logger.debug(f"   Checking budget text: '{candidate_text}'")
                    
                    # Enhanced filtering to exclude client spending information
                    if (candidate_text and '$' in candidate_text and len(candidate_text) < 50 and
                        # Exclude client spending patterns
                        not any(exclude_pattern in candidate_text.lower() for exclude_pattern in [
                            'total spent', 'spent', 'hires', 'active', 'hours', 'member since',
                            'rating', 'reviews', 'company', 'client', 'profile'
                        ]) and
                        # Only include budget-like patterns
                        any(budget_pattern in candidate_text.lower() for budget_pattern in [
                            '$', 'fixed', 'hourly', '/hr', 'budget', 'price', 'rate'
                        ])):
                        
                        budget_text = candidate_text
                        logger.info(f"✅ Found budget with selector '{selector}': {budget_text}")
                        break
                        
                if budget_text:
                    break  # Found budget, stop trying other selectors
                    
            except Exception as e:
                logger.debug(f"❌ Budget selector '{selector}' failed: {e}")
                continue
        
        if budget_text:
            budget_info['raw_text'] = budget_text
            
            # Parse budget amount
            amounts = re.findall(r'\$?([\d,]+\.?\d*)', budget_text)
            if amounts:
                try:
                    amount = float(amounts[0].replace(',', ''))
                    budget_info['min_amount'] = amount
                    budget_info['max_amount'] = amount
                except:
                    pass
            
            # Determine budget type
            budget_text_lower = budget_text.lower()
            if 'fixed' in budget_text_lower or 'project' in budget_text_lower:
                budget_info['type'] = 'fixed'
                budget_info['is_fixed'] = True
            elif 'hour' in budget_text_lower or '/hr' in budget_text_lower:
                budget_info['type'] = 'hourly'
                budget_info['is_hourly'] = True
                budget_info['hourly_rate'] = budget_info['min_amount']
        
        # Look for additional budget context
        context_selectors = [
            '.description',  # "Fixed-price" or "Hourly"
            '[data-v-ca6db23e] .description',
            '.text-light-on-muted'
        ]
        
        for selector in context_selectors:
            try:
                context_elems = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in context_elems:
                    context_text = clean_text(elem.text).lower()
                    if 'fixed' in context_text:
                        budget_info['type'] = 'fixed'
                        budget_info['is_fixed'] = True
                        break
                    elif 'hourly' in context_text:
                        budget_info['type'] = 'hourly'
                        budget_info['is_hourly'] = True
                        break
            except:
                continue
        
    except Exception as e:
        logger.warning(f"Error extracting budget: {e}")
    
    return budget_info

def extract_detailed_description(driver) -> str:
    """Extract comprehensive job description from individual job page"""
    from selenium.webdriver.common.by import By
    
    description_selectors = [
        # Based on actual individual job page HTML structure
        '[data-test="Description"] p.text-body-sm',  # Exact match from HTML
        '[data-test="Description"] p',               # Main description paragraphs
        '.break.mt-2 p',                            # Description in break section
        '.air3-card-section p.text-body-sm',       # Card section paragraphs
        '.air3-card-section p',                     # Generic card paragraphs
        'section p.text-body-sm',                   # Any section paragraphs
        'section p',                                # Generic section paragraphs
        '.job-description p',                       # Fallback job description
        'p'                                         # Last resort - any paragraph
    ]
    
    description_parts = []
    
    for selector_index, selector in enumerate(description_selectors):
        try:
            desc_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            logger.debug(f"🔍 Description selector {selector_index + 1}: '{selector}' found {len(desc_elements)} elements")
            
            for elem in desc_elements:
                text = clean_text(elem.text)
                if (text and len(text) > 30 and  # Substantial content
                    not text.lower().startswith(('summary', 'posted', 'hourly', 'fixed', 'expert', 'intermediate', 'entry')) and
                    text not in description_parts):  # Avoid duplicates
                    description_parts.append(text)
                    logger.debug(f"   ✅ Added description part: {text[:100]}...")
                    
            if description_parts:
                break  # Found description, stop trying other selectors
                
        except Exception as e:
            logger.debug(f"❌ Description selector '{selector}' failed: {e}")
            continue
    
    if description_parts:
        full_description = '\n\n'.join(description_parts[:3])  # Limit to first 3 substantial paragraphs
        logger.info(f"✅ Found description ({len(full_description)} chars): {full_description[:100]}...")
        return full_description
    
    logger.warning("❌ No description found")
    return "No description available"

def extract_project_details(driver) -> Dict[str, Any]:
    """Extract project details like experience level, duration, job type"""
    from selenium.webdriver.common.by import By
    
    details = {
        'experience_level': 'All levels',
        'duration': 'Duration flexible',
        'job_type': 'Not specified',
        'project_type': 'Not specified',
        'is_remote': False,
        'is_contract_to_hire': False
    }
    
    try:
        # Extract experience level
        exp_selectors = [
            '[data-cy="expertise"] + strong',  # "Entry level"
            '.features strong',
            'li strong'
        ]
        
        for selector in exp_selectors:
            try:
                exp_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in exp_elements:
                    text = clean_text(elem.text)
                    if any(level in text.lower() for level in ['entry', 'intermediate', 'expert', 'level']):
                        details['experience_level'] = text
                        break
            except:
                continue
        
        # Extract project type and duration
        type_selectors = [
            '[data-cy="briefcase-outlined"] + strong',  # "Ongoing project"
            '.features li strong'
        ]
        
        for selector in type_selectors:
            try:
                type_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in type_elements:
                    text = clean_text(elem.text)
                    if 'project' in text.lower():
                        details['project_type'] = text
                        details['duration'] = text
                        break
            except:
                continue
        
        # Check for remote work
        remote_selectors = [
            '[data-cy="local"] + strong',  # "Remote Job"
            '.features strong'
        ]
        
        for selector in remote_selectors:
            try:
                remote_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in remote_elements:
                    text = clean_text(elem.text).lower()
                    if 'remote' in text:
                        details['is_remote'] = True
                        break
            except:
                continue
        
        # Check for contract-to-hire
        try:
            contract_elem = driver.find_element(By.CSS_SELECTOR, '[data-test="ContractToHireBanner"]')
            if contract_elem:
                details['is_contract_to_hire'] = True
        except:
            pass
        
    except Exception as e:
        logger.warning(f"Error extracting project details: {e}")
    
    return details

def extract_activity_information(driver) -> Dict[str, Any]:
    """Extract activity information: proposals, interviews, invites"""
    from selenium.webdriver.common.by import By
    
    activity = {
        'proposals': {'display': 'Unknown', 'count': 0},
        'last_viewed': 'Unknown',
        'interviewing': 0,
        'invites_sent': 0,
        'unanswered_invites': 0
    }
    
    try:
        # Find activity section - using exact selectors from individual job page HTML
        activity_selectors = [
            # Based on actual individual job page HTML structure
            '[data-test="ClientActivity"] .ca-item',         # Exact match from HTML
            '.client-activity-items .ca-item',               # Client activity items
            'section[data-v-1efc9607] .ca-item',            # Section with data attribute
            '.air3-card-section .ca-item',                  # Card section activity items
            'ul.client-activity-items li',                   # List items in activity
            '.activity-section li',                          # Generic activity section
            'li.ca-item',                                    # Generic activity items
        ]
        
        for selector_index, selector in enumerate(activity_selectors):
            try:
                activity_items = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.debug(f"🔍 Activity selector {selector_index + 1}: '{selector}' found {len(activity_items)} elements")
                
                for item in activity_items:
                    item_text = clean_text(item.text).lower()
                    logger.debug(f"   Checking activity item: '{item_text}'")
                    
                    if 'proposals:' in item_text or 'proposal' in item_text:
                        # Extract proposals count
                        try:
                            value_elem = item.find_element(By.CSS_SELECTOR, '.value, span.value')
                            proposals_text = clean_text(value_elem.text)
                            activity['proposals']['display'] = proposals_text
                            logger.info(f"✅ Found proposals: {proposals_text}")
                            
                            # Extract number
                            if 'less than' in proposals_text.lower():
                                numbers = re.findall(r'(\d+)', proposals_text)
                                if numbers:
                                    activity['proposals']['count'] = int(numbers[0]) - 1  # "Less than 5" = 4
                            else:
                                numbers = re.findall(r'(\d+)', proposals_text)
                                if numbers:
                                    activity['proposals']['count'] = int(numbers[0])
                        except:
                            pass
                    
                    elif 'last viewed' in item_text:
                        try:
                            value_elem = item.find_element(By.CSS_SELECTOR, '.value, span.value')
                            activity['last_viewed'] = clean_text(value_elem.text)
                            logger.info(f"✅ Found last viewed: {activity['last_viewed']}")
                        except:
                            pass
                    
                    elif 'interviewing' in item_text:
                        try:
                            value_elem = item.find_element(By.CSS_SELECTOR, '.value, span.value')
                            numbers = re.findall(r'(\d+)', value_elem.text)
                            if numbers:
                                activity['interviewing'] = int(numbers[0])
                                logger.info(f"✅ Found interviewing: {activity['interviewing']}")
                        except:
                            pass
                    
                    elif 'invites sent' in item_text:
                        try:
                            value_elem = item.find_element(By.CSS_SELECTOR, '.value, span.value')
                            numbers = re.findall(r'(\d+)', value_elem.text)
                            if numbers:
                                activity['invites_sent'] = int(numbers[0])
                                logger.info(f"✅ Found invites sent: {activity['invites_sent']}")
                        except:
                            pass
                    
                    elif 'unanswered' in item_text:
                        try:
                            value_elem = item.find_element(By.CSS_SELECTOR, '.value, span.value')
                            numbers = re.findall(r'(\d+)', value_elem.text)
                            if numbers:
                                activity['unanswered_invites'] = int(numbers[0])
                                logger.info(f"✅ Found unanswered invites: {activity['unanswered_invites']}")
                        except:
                            pass
                            
                if activity['proposals']['display'] != 'Unknown':  # Found activity data
                    break  # Found activity section, stop trying other selectors
                    
            except Exception as e:
                logger.debug(f"❌ Activity selector '{selector}' failed: {e}")
                continue
        
    except Exception as e:
        logger.warning(f"Error extracting activity information: {e}")
    
    return activity

def extract_detailed_client_info(driver) -> Dict[str, Any]:
    """Extract comprehensive client information"""
    from selenium.webdriver.common.by import By
    
    client_info = {
        'location': 'Worldwide',
        'country': 'Unknown',
        'city': 'Unknown',
        'timezone': 'Unknown',
        'member_since': 'Unknown',
        'rating': 0.0,
        'verified': False,
        'company_profile': False
    }
    
    try:
        # Extract client location from job details
        location_selectors = [
            '[data-test="LocationLabel"] p',  # "Worldwide"
            '.text-light-on-muted',
            '.location-info'
        ]
        
        for selector in location_selectors:
            try:
                location_elem = driver.find_element(By.CSS_SELECTOR, selector)
                location_text = clean_text(location_elem.text)
                if location_text and location_text not in ['', 'Unknown']:
                    client_info['location'] = location_text
                    break
            except:
                continue
        
        # Extract client details from About section
        about_selectors = [
            '[data-test="AboutClientVisitor"] .ac-items li',
            '.cfe-about-client-v2 .ac-items li',
            '.about-client li'
        ]
        
        for selector in about_selectors:
            try:
                about_items = driver.find_elements(By.CSS_SELECTOR, selector)
                for item in about_items:
                    item_text = clean_text(item.text)
                    
                    # Member since
                    if 'member since' in item_text.lower():
                        date_match = re.search(r'member since (.+)', item_text.lower())
                        if date_match:
                            client_info['member_since'] = date_match.group(1).strip()
                    
                    # Location details
                    elif any(indicator in item_text.lower() for indicator in ['country', 'city', 'time', ':']):
                        if ':' in item_text:
                            location_parts = item_text.split('\n')
                            if len(location_parts) >= 2:
                                client_info['country'] = location_parts[0].strip()
                                time_info = location_parts[1].strip()
                                if 'am' in time_info.lower() or 'pm' in time_info.lower():
                                    client_info['timezone'] = time_info
                break
            except:
                continue
        
        # Extract member since from top section
        try:
            member_elem = driver.find_element(By.CSS_SELECTOR, '[data-qa="client-contract-date"] small')
            member_text = clean_text(member_elem.text)
            if 'member since' in member_text.lower():
                client_info['member_since'] = member_text.replace('Member since', '').strip()
        except:
            pass
        
        # Extract country and city from detailed location
        try:
            location_elem = driver.find_element(By.CSS_SELECTOR, '[data-qa="client-location"] strong')
            country = clean_text(location_elem.text)
            if country:
                client_info['country'] = country
                
                # Try to get city/state
                city_elem = location_elem.find_element(By.XPATH, '../div/span[@class="nowrap"]')
                city = clean_text(city_elem.text)
                if city:
                    client_info['city'] = city
        except:
            pass
    
    except Exception as e:
        logger.warning(f"Error extracting client info: {e}")
    
    return client_info

def extract_detailed_payment_verification(driver) -> Dict[str, Any]:
    """Extract detailed payment verification status from individual job page"""
    from selenium.webdriver.common.by import By
    
    payment_info = {
        'status': 'unknown',
        'verified': False,
        'display': 'Payment status not verified'
    }
    
    try:
        # Look for payment verification indicators
        payment_selectors = [
            '.payment-verified',
            '.verified-payment',
            '[data-test="payment-status"]',
            '.client-verified'
        ]
        
        for selector in payment_selectors:
            try:
                payment_elem = driver.find_element(By.CSS_SELECTOR, selector)
                payment_text = clean_text(payment_elem.text).lower()
                
                if 'verified' in payment_text:
                    payment_info['status'] = 'verified'
                    payment_info['verified'] = True
                    payment_info['display'] = 'Payment verified'
                elif 'not verified' in payment_text:
                    payment_info['status'] = 'not_verified'
                    payment_info['verified'] = False
                    payment_info['display'] = 'Payment not verified'
                break
            except:
                continue
    
    except Exception as e:
        logger.warning(f"Error extracting payment verification: {e}")
    
    return payment_info

def extract_skills_and_requirements(driver) -> Dict[str, Any]:
    """Extract skills and requirements from individual job page"""
    from selenium.webdriver.common.by import By
    
    skills_info = {
        'skills': [],
        'mandatory_skills': [],
        'total_skills': 0
    }
    
    try:
        # Extract from Skills and Expertise section
        skills_selectors = [
            '[data-test="Skill"] .air3-line-clamp',  # Individual skills
            '.skills-list .air3-badge',
            '.skill-tag',
            '.badge'
        ]
        
        all_skills = set()  # Use set to avoid duplicates
        
        for selector in skills_selectors:
            try:
                skill_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in skill_elements:
                    skill_text = clean_text(elem.text)
                    if skill_text and len(skill_text) > 1 and skill_text not in ['+ 8 more', '+ more']:
                        all_skills.add(skill_text)
            except:
                continue
        
        skills_info['skills'] = list(all_skills)
        skills_info['total_skills'] = len(all_skills)
        
        # Try to identify mandatory vs optional skills
        try:
            mandatory_section = driver.find_element(By.CSS_SELECTOR, '.mandatory-skills, [data-v-34a90980] strong')
            if 'mandatory' in mandatory_section.text.lower():
                # Get skills from mandatory section
                mandatory_skills = []
                parent = mandatory_section.find_element(By.XPATH, '..')
                skill_elems = parent.find_elements(By.CSS_SELECTOR, '[data-test="Skill"] .air3-line-clamp')
                for elem in skill_elems:
                    skill = clean_text(elem.text)
                    if skill:
                        mandatory_skills.append(skill)
                skills_info['mandatory_skills'] = mandatory_skills
        except:
            # If no mandatory section found, treat first few skills as mandatory
            skills_info['mandatory_skills'] = skills_info['skills'][:3]
        
    except Exception as e:
        logger.warning(f"Error extracting skills: {e}")
    
    return skills_info

def extract_location_details(driver) -> Dict[str, Any]:
    """Extract job location details"""
    from selenium.webdriver.common.by import By
    
    location_info = {
        'type': 'Remote',
        'is_remote': False,
        'is_worldwide': False,
        'specific_location': None,
        'timezone_required': False
    }
    
    try:
        # Look for location information
        location_selectors = [
            '[data-test="LocationLabel"] p',
            '[data-cy="local"] + strong',
            '.location-type',
            '.remote-job'
        ]
        
        for selector in location_selectors:
            try:
                location_elem = driver.find_element(By.CSS_SELECTOR, selector)
                location_text = clean_text(location_elem.text)
                
                if 'worldwide' in location_text.lower():
                    location_info['type'] = 'Worldwide'
                    location_info['is_worldwide'] = True
                    location_info['is_remote'] = True
                elif 'remote' in location_text.lower():
                    location_info['type'] = 'Remote'
                    location_info['is_remote'] = True
                else:
                    location_info['type'] = location_text
                    location_info['specific_location'] = location_text
                break
            except:
                continue
    
    except Exception as e:
        logger.warning(f"Error extracting location details: {e}")
    
    return location_info

def scrape_upwork_individual_pages(keywords: List[str], filters: Optional[Dict[str, str]] = None, max_jobs_per_keyword: int = 10, skip_private_jobs: bool = True) -> List[Dict[str, Any]]:
    """
    Enhanced Upwork scraping that visits individual job pages for comprehensive data collection
    
    Args:
        keywords: List of search keywords
        filters: Dictionary of filter options
        max_jobs_per_keyword: Maximum number of jobs to scrape per keyword (default: 10)
        skip_private_jobs: Whether to skip private/confidential jobs (default: True)
        
    Returns:
        List of comprehensive job data from individual pages
    """
    if filters is None:
        filters = {
            'time_range': 'any',
            'budget_range': 'any', 
            'job_type': 'any',
            'experience_level': 'any',
            'sort_by': 'recency'
        }
    
    logger.info(f"🚀 Starting COMPREHENSIVE individual page scraping...")
    logger.info(f"📋 Keywords: {keywords}")
    logger.info(f"🔧 Filters: {filters}")
    logger.info(f"🎯 Max jobs per keyword: {max_jobs_per_keyword}")
    logger.info(f"⏰ This process will take time to collect detailed data from each job page...")
    
    # Import selenium modules
    try:
        import undetected_chromedriver as uc
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError as e:
        logger.error(f"❌ Missing selenium dependencies: {e}")
        return []
    
    # Setup browser with longer timeouts for individual page visits
    logger.info("🌐 Setting up browser for individual page scraping...")
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Longer timeouts for comprehensive scraping
    options.add_argument("--page-load-strategy=normal")
    
    all_comprehensive_jobs = []
    upwork_filters = UpworkFilters()
    
    try:
        logger.info("🔧 Launching browser...")
        driver = uc.Chrome(options=options)
        wait = WebDriverWait(driver, 30)  # Longer wait for individual pages
        
        logger.info("✅ Browser launched successfully!")
        logger.info("🎯 Starting comprehensive data collection process...")
        
        # Start with Google to avoid direct detection
        logger.info("🔍 Initial navigation through Google...")
        driver.get("https://www.google.com")
        human_delay(3, 5)
        
        # Process each keyword
        for keyword_index, keyword in enumerate(keywords):
            logger.info(f"\n{'='*80}")
            logger.info(f"🔍 PROCESSING KEYWORD {keyword_index + 1}/{len(keywords)}: '{keyword}'")
            logger.info(f"{'='*80}")
            
            try:
                # STEP 1: Get job URLs from listing page
                logger.info(f"📋 STEP 1: Getting job URLs from listing page...")
                
                search_url = upwork_filters.build_search_url(
                    keyword=keyword,
                    time_range=filters.get('time_range', 'any'),
                    budget_range=filters.get('budget_range', 'any'),
                    job_type=filters.get('job_type', 'any'),
                    experience_level=filters.get('experience_level', 'any'),
                    sort_by=filters.get('sort_by', 'recency')
                )
                
                logger.info(f"🎯 Navigating to: {search_url}")
                driver.get(search_url)
                human_delay(8, 12)
                
                # Handle protection systems
                current_title = driver.title.lower()
                if "just a moment" in current_title or "checking" in current_title:
                    logger.info("🛡️ Detected protection system, waiting patiently...")
                    for i in range(20):
                        time.sleep(5)
                        new_title = driver.title.lower()
                        if "just a moment" not in new_title and "checking" not in new_title:
                            logger.info("✅ Protection bypass successful!")
                            break
                        logger.info(f"   ⏳ Still waiting... ({(i+1)*5}s)")
                
                # Extract job URLs from listing page
                job_urls = extract_job_urls_from_listing(driver, max_jobs_per_keyword)
                logger.info(f"📊 Found {len(job_urls)} job URLs to scrape individually")
                
                if not job_urls:
                    logger.error(f"❌ NO JOB URLs FOUND for keyword '{keyword}'!")
                    logger.info(f"🔍 Debugging info for keyword '{keyword}':")
                    logger.info(f"   📄 Current page title: {driver.title}")
                    logger.info(f"   🌐 Current URL: {driver.current_url}")
                    logger.info(f"   📝 Page source length: {len(driver.page_source)} characters")
                    
                    # Take a screenshot for debugging (if possible)
                    try:
                        screenshot_path = f"debug_screenshot_{keyword.replace(' ', '_')}.png"
                        driver.save_screenshot(screenshot_path)
                        logger.info(f"   📸 Screenshot saved: {screenshot_path}")
                    except:
                        logger.info("   📸 Could not save screenshot")
                    
                    logger.warning(f"⚠️ Skipping keyword '{keyword}' and continuing with next keyword...")
                    continue
                
                # STEP 2: Visit each individual job page
                logger.info(f"🔍 STEP 2: Visiting individual job pages for comprehensive data...")
                
                for job_index, job_url in enumerate(job_urls):
                    logger.info(f"\n📄 Processing job {job_index + 1}/{len(job_urls)} for keyword '{keyword}'")
                    
                    try:
                        # Visit individual job page and extract comprehensive data
                        comprehensive_job_data = scrape_individual_job_page(driver, job_url, keyword, skip_private_jobs)
                        
                        # Check if job was skipped due to being private
                        if comprehensive_job_data.get('skipped', False):
                            logger.info(f"🔒 Job skipped: {comprehensive_job_data.get('skip_reason', 'unknown reason')}")
                            # Don't add private jobs to main results - only track for statistics
                            # all_comprehensive_jobs.append(comprehensive_job_data)  # REMOVED - don't add private jobs
                        else:
                            all_comprehensive_jobs.append(comprehensive_job_data)
                            logger.info(f"✅ Successfully extracted comprehensive data for job: {comprehensive_job_data['title'][:50]}...")
                        
                        # Human delay between individual job page visits
                        if job_index < len(job_urls) - 1:
                            delay_time = random.uniform(4, 8)
                            logger.info(f"⏳ Waiting {delay_time:.1f}s before next job page...")
                            time.sleep(delay_time)
                            
                    except Exception as e:
                        logger.error(f"❌ Error processing individual job {job_index + 1}: {e}")
                        continue
                
                logger.info(f"✅ Completed processing {len(job_urls)} jobs for keyword '{keyword}'")
                
                # Longer delay between keywords
                if keyword_index < len(keywords) - 1:
                    delay_time = random.uniform(10, 15)
                    logger.info(f"⏳ Waiting {delay_time:.1f}s before processing next keyword...")
                    time.sleep(delay_time)
                
            except Exception as e:
                logger.error(f"❌ Error processing keyword '{keyword}': {e}")
                continue
        
        logger.info(f"\n🎉 COMPREHENSIVE SCRAPING COMPLETED!")
        logger.info(f"📊 Total jobs with comprehensive data: {len(all_comprehensive_jobs)}")
        
    except Exception as e:
        logger.error(f"❌ Critical error in comprehensive scraping: {e}")
    finally:
        try:
            driver.quit()
            logger.info("🔧 Browser closed successfully")
        except:
            pass
    
    return all_comprehensive_jobs

def extract_job_urls_from_listing(driver, max_jobs: int = 10) -> List[str]:
    """Extract job URLs from the listing page with enhanced debugging and updated selectors"""
    from selenium.webdriver.common.by import By
    
    job_urls = []
    
    try:
        logger.info(f"🔍 Starting job URL extraction (target: {max_jobs} URLs)")
        
        # Wait a bit for dynamic content to load
        human_delay(3, 5)
        
        # Check what's actually on the page for debugging
        page_title = driver.title
        current_url = driver.current_url
        logger.info(f"📄 Current page: {page_title}")
        logger.info(f"🌐 Current URL: {current_url}")
        
        # Check if there are any job-related elements
        page_source = driver.page_source
        if 'freelance-jobs' in page_source or 'job' in page_source.lower():
            logger.info("✅ Page contains job-related content")
        else:
            logger.warning("⚠️ Page may not contain job listings")
        
        # Updated selectors based on the ACTUAL job listings page HTML structure provided
        link_selectors = [
            # Most specific - based on the real HTML structure from job listings page
            'article[data-test="JobTile"] a[data-test="job-tile-title-link UpLink"]',  # Perfect match
            'a[data-test="job-tile-title-link UpLink"]',  # Direct job title links
            'a[data-test*="job-tile-title-link"]',  # Job title links variations
            
            # Broader but still specific selectors from the actual HTML
            'article[data-test="JobTile"] h2 a',  # Job title in h2 tag
            'section[data-test="JobsList"] article a',  # Any link in job tiles within job list
            'h2.job-tile-title a',  # Job tile title links
            '.job-tile-title a',  # Job tile title class
            
            # Generic selectors for job tiles
            'article[data-test="JobTile"] a',  # Any link in job tile
            'section[data-test="JobsList"] a',  # Any link in jobs list
            
            # Last resort - any link containing job paths (relative URLs from the HTML)
            'a[href*="/jobs/"]',  # Links to /jobs/ paths like in the HTML
            'a[href^="/jobs/"]'   # Links starting with /jobs/
        ]
        
        for selector_index, selector in enumerate(link_selectors):
            try:
                logger.info(f"🔎 Trying selector {selector_index + 1}/{len(link_selectors)}: {selector}")
                link_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"🔗 Found {len(link_elements)} elements with this selector")
                
                urls_found_with_this_selector = 0
                
                for elem_index, elem in enumerate(link_elements):
                    try:
                        href = elem.get_attribute('href')
                        if href:
                            logger.debug(f"   Link {elem_index + 1}: {href}")
                            
                            # Check if this is a valid job link (based on actual HTML structure)
                            if (href.startswith('/jobs/') or '/jobs/' in href) and not href.startswith('javascript:'):
                                # Convert relative URL to absolute URL
                                if href.startswith('/'):
                                    full_url = 'https://www.upwork.com' + href
                                else:
                                    full_url = href
                                
                                if full_url not in job_urls:  # Avoid duplicates
                                    job_urls.append(full_url)
                                    urls_found_with_this_selector += 1
                                    logger.info(f"   ✅ Added job URL {len(job_urls)}: {full_url}")
                                else:
                                    logger.debug(f"   🔄 Duplicate URL skipped: {full_url}")
                                
                                if len(job_urls) >= max_jobs:
                                    logger.info(f"🎯 Reached target of {max_jobs} URLs")
                                    break
                    except Exception as e:
                        logger.debug(f"   ⚠️ Error with element {elem_index + 1}: {e}")
                        continue
                
                logger.info(f"📊 Selector '{selector}' found {urls_found_with_this_selector} valid job URLs")
                
                if job_urls:
                    logger.info(f"✅ Successfully found {len(job_urls)} job URLs, stopping selector search")
                    break  # Found job URLs, no need to try other selectors
                    
            except Exception as e:
                logger.warning(f"⚠️ Error with selector '{selector}': {e}")
                continue
        
        # Final validation
        if not job_urls:
            logger.error("❌ NO JOB URLs FOUND!")
            logger.info("🔍 Debugging - checking page content...")
            
            # Debug: Try to find ANY links
            all_links = driver.find_elements(By.TAG_NAME, 'a')
            logger.info(f"📋 Total links on page: {len(all_links)}")
            
            job_related_links = []
            for link in all_links[:20]:  # Check first 20 links
                href = link.get_attribute('href')
                if href and ('/jobs/' in href or 'job' in href.lower() or 'freelance' in href.lower()):
                    job_related_links.append(href)
            
            if job_related_links:
                logger.info(f"🔍 Found {len(job_related_links)} job-related links:")
                for link in job_related_links[:5]:
                    logger.info(f"   📎 {link}")
            else:
                logger.warning("⚠️ No job-related links found on page")
                
                # Check if we're on the right page
                if 'search' not in current_url or 'upwork.com' not in current_url:
                    logger.error(f"❌ Not on Upwork search page! Current URL: {current_url}")
        else:
            logger.info(f"🎉 Successfully extracted {len(job_urls)} job URLs!")
            for i, url in enumerate(job_urls, 1):
                logger.info(f"   {i}. {url}")
        
        return job_urls[:max_jobs]  # Ensure we don't exceed max_jobs
        
    except Exception as e:
        logger.error(f"❌ Critical error extracting job URLs: {e}")
        return []

def collect_comprehensive_upwork_data(keywords: List[str], filters: Optional[Dict[str, str]] = None, 
                                    max_jobs_per_keyword: int = 10, use_persistence: bool = True, 
                                    skip_private_jobs: bool = True) -> Dict[str, Any]:
    """
    Main function to collect comprehensive Upwork data from individual job pages
    
    Args:
        keywords: List of search keywords
        filters: Dictionary of filter options
        max_jobs_per_keyword: Maximum number of jobs to scrape per keyword
        use_persistence: Whether to append to existing data
        skip_private_jobs: Whether to skip private/confidential jobs (default: True)
        
    Returns:
        Dictionary containing comprehensive job data
    """
    logger.info(f"🚀 STARTING COMPREHENSIVE UPWORK DATA COLLECTION")
    logger.info(f"📋 Keywords: {keywords}")
    logger.info(f"🎯 Max jobs per keyword: {max_jobs_per_keyword}")
    logger.info(f"⏰ Expected time: {len(keywords) * max_jobs_per_keyword * 0.5:.1f} minutes (approximate)")
    logger.info(f"💾 Using persistence: {use_persistence}")
    logger.info(f"🔒 Skip private jobs: {skip_private_jobs}")
    
    if filters is None:
        filters = {
            'time_range': 'today',
            'hourly_filter': '',
            'budget_range': 'any',
            'job_type': 'any',
            'experience_level': 'any',
            'payment_status': 'both',
            'sort_by': 'recency'
        }
    
    logger.info(f"🔧 Applied filters: {filters}")
    
    # Collect comprehensive job data
    start_time = datetime.now()
    all_jobs = scrape_upwork_individual_pages(keywords, filters, max_jobs_per_keyword, skip_private_jobs)
    end_time = datetime.now()
    
    duration = end_time - start_time
    logger.info(f"⏱️ Total collection time: {duration}")
    
    # Calculate private job statistics - private jobs are no longer in all_jobs
    # We need to track this separately since private jobs are now completely excluded
    private_jobs_count = 0  # Will be updated if we implement separate tracking
    valid_jobs_count = len(all_jobs)  # All jobs in all_jobs are now valid
    
    logger.info(f"📊 Collection Summary:")
    logger.info(f"   🎯 Total jobs processed: {len(all_jobs)}")
    logger.info(f"   ✅ Valid jobs collected: {valid_jobs_count}")
    logger.info(f"   🔒 Private jobs skipped: {private_jobs_count} (not included in results)")
    
    # Prepare comprehensive data structure
    collection_stats = {
        'total_jobs': len(all_jobs),
        'valid_jobs': valid_jobs_count,
        'private_jobs_skipped': private_jobs_count,
        'private_job_skip_rate': 0,  # Private jobs are completely excluded now
        'keywords_processed': len(keywords),
        'max_jobs_per_keyword': max_jobs_per_keyword,
        'actual_avg_jobs_per_keyword': len(all_jobs) / len(keywords) if keywords else 0,
        'filters_applied': filters,
        'collection_time': end_time.isoformat(),
        'collection_duration_seconds': duration.total_seconds(),
        'method': 'individual_job_pages_comprehensive',
        'data_quality': 'premium_comprehensive',
        'private_jobs_excluded': True  # Flag indicating private jobs are completely excluded
    }
    
    upwork_data = {
        'jobs': all_jobs,
        'stats': collection_stats,
        'metadata': {
            'total_jobs': len(all_jobs),
            'keywords_analyzed': keywords,
            'collection_timestamp': end_time.isoformat(),
            'data_source': 'upwork_individual_pages_comprehensive',
            'filters_used': filters,
            'scraping_method': 'selenium_individual_pages',
            'data_completeness': 'comprehensive',
            'avg_time_per_job': duration.total_seconds() / len(all_jobs) if all_jobs else 0
        }
    }
    
    # Use persistence if requested
    if use_persistence and all_jobs:
        try:
            result = append_upwork_data(upwork_data)
            logger.info(f"💾 Data persistence result: {'Success' if result else 'Failed'}")
            upwork_data['persistence_result'] = result
        except Exception as e:
            logger.error(f"❌ Error with data persistence: {e}")
            upwork_data['persistence_error'] = str(e)
    
    # Create Excel file with all job URLs and details
    if all_jobs:
        try:
            excel_path = create_jobs_excel_file(upwork_data)
            if excel_path:
                upwork_data['excel_file_path'] = excel_path
                logger.info(f"📊 Excel file created: {excel_path}")
            else:
                logger.warning("⚠️ Failed to create Excel file")
        except Exception as e:
            logger.error(f"❌ Error creating Excel file: {e}")
    
    logger.info(f"🎉 COMPREHENSIVE DATA COLLECTION COMPLETED!")
    logger.info(f"📊 Final stats: {len(all_jobs)} jobs collected with premium detail level")
    
    return upwork_data

def create_jobs_excel_file(upwork_data: Dict[str, Any], filename: Optional[str] = None) -> Optional[str]:
    """
    Create a simplified Excel file with job titles and URLs only
    
    Args:
        upwork_data: Dictionary containing job data
        filename: Optional custom filename (will auto-generate if not provided)
        
    Returns:
        Optional[str]: Path to the created Excel file, or None if failed
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"upwork_jobs_{timestamp}.xlsx"
    
    try:
        jobs = upwork_data.get('jobs', [])
        if not jobs:
            logger.warning("No jobs data found to export")
            return "No jobs data found to export"
        
        logger.info(f"📊 Creating Excel file with {len(jobs)} jobs...")
        
        # Prepare data for Excel
        excel_data = []
        
        for job in jobs:
            row_data = {
                'Keyword': job.get('search_keyword', job.get('keyword', 'Unknown')),
                'Job Title': job.get('title', 'No title'),
                'Description': job.get('description', 'No description'),
                'Job URL': job.get('url', 'No URL')
            }
            excel_data.append(row_data)
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        # Sort by keyword and job title alphabetically
        df = df.sort_values(['Keyword', 'Job Title'], ascending=[True, True])
        # Create Excel file with single sheet
        excel_path = os.path.join('data', filename)
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Jobs', index=False)
        logger.info(f"✅ Excel file created successfully: {excel_path}")
        logger.info(f"📋 File contains {len(jobs)} jobs with keyword, title, description, and URL only")
        return excel_path
        
    except Exception as e:
        logger.error(f"❌ Error creating Excel file: {e}")
        return None

def get_latest_jobs_excel_path() -> Optional[str]:
    """
    Get the path to the most recently created jobs Excel file
    
    Returns:
        Optional[str]: Path to the latest Excel file or None if not found
    """
    try:
        data_dir = 'data'
        if not os.path.exists(data_dir):
            return "No data directory found"
        
        # Find all Excel files matching the pattern
        excel_files = [f for f in os.listdir(data_dir) if f.startswith('upwork_jobs_') and f.endswith('.xlsx')]
        
        if not excel_files:
            return "No Excel files found"
        
        # Sort by creation time and get the latest
        excel_files.sort(reverse=True)
        latest_file = excel_files[0]
        
        return os.path.join(data_dir, latest_file)
        
    except Exception as e:
        logger.error(f"Error finding latest Excel file: {e}")
        return "Error finding latest Excel file"

if __name__ == "__main__":
    print("🔧 Enhanced Upwork Scraper with Filters")
    print("=" * 60)
    print("✅ Features:")
    print("   - Time range filtering (last week to 6 months)")
    print("   - Budget range filtering ($500 to $5000+)")
    print("   - Job type filtering (hourly/fixed)")
    print("   - Experience level filtering")
    print("   - Data persistence (append mode)")
    print("   - Filter compliance checking")
    print()
    print("📋 Available functions:")
    print("   - collect_upwork_data_with_filters()")
    print("   - collect_recent_upwork_jobs()")
    print("   - collect_high_budget_jobs()")
    print("   - collect_hourly_jobs()")
    print("   - collect_fixed_price_jobs()")
    print("=" * 60)
    
    # Demo collection
    demo_keywords = ["python", "data science"]
    demo_filters = {
        'time_range': 'last_month',
        'budget_range': '1000_3000',
        'job_type': 'any',
        'experience_level': 'any',
        'sort_by': 'recency'
    }
    
    print(f"🎯 Demo: Collecting jobs for {demo_keywords} with filters")
    print(f"🔍 Filters: {demo_filters}")
    
    # Uncomment to run demo
    # result = collect_upwork_data_with_filters(demo_keywords, demo_filters)
    # print(f"✅ Demo completed: {result.get('stats', {}).get('total_jobs', 0)} jobs collected") 
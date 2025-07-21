#!/usr/bin/env python3
"""
Test script to verify extraction functions work with actual Upwork HTML
"""

from bs4 import BeautifulSoup
import re

def test_html_extraction():
    """Test extraction using the actual Upwork HTML structure"""
    
    # Sample HTML structure based on user's provided HTML
    sample_html = '''
    <div class="job-card">
        <!-- Proposals Section -->
        <section class="air3-card-section py-4x" data-test="ClientActivity">
            <ul class="client-activity-items list-unstyled visitor">
                <li class="ca-item">
                    <span class="title">Proposals:</span>
                    <span class="value" data-v-1efc9607="">Less than 5</span>
                </li>
                <li class="ca-item">
                    <span class="title">Last viewed by client:</span>
                    <span class="value" data-v-1efc9607="">41 minutes ago</span>
                </li>
                <li class="ca-item">
                    <span class="title">Interviewing:</span>
                    <div class="value">0</div>
                </li>
            </ul>
        </section>
        
        <!-- About Client Section -->
        <div class="cfe-about-client-v2 air3-card-section py-4x" data-test="AboutClientVisitor">
            <h5 class="mb-4 d-flex">About the client</h5>
            <div class="text-light-on-muted mb-3">
                <small>Member since Jul 3, 2025</small>
            </div>
            <ul class="ac-items list-unstyled">
                <li data-qa="client-location">
                    <strong data-v-ea8e3ca4="">Bangladesh</strong>
                    <div class="text-body-sm text-light-on-muted">
                        <span class="nowrap">Nilphamari</span>
                        <span class="nowrap" data-test="LocalTime">11:32 AM</span>
                    </div>
                </li>
            </ul>
        </div>
        
        <!-- Posted Time Section -->
        <div class="posted-on-line">
            <div data-test="PostedOn">
                Posted
                <span>44 minutes ago</span>
            </div>
        </div>
    </div>
    '''
    
    soup = BeautifulSoup(sample_html, 'html.parser')
    
    print("🧪 Testing HTML Extraction Functions")
    print("=" * 50)
    
    # Test proposal count extraction
    print("\n📊 Testing Proposal Count Extraction:")
    proposal_elements = soup.select('.ca-item')
    for item in proposal_elements:
        title = item.select_one('.title')
        value = item.select_one('.value')
        if title and value and 'proposal' in title.get_text().lower():
            proposals_text = value.get_text().strip()
            print(f"   Found: '{proposals_text}'")
            
            # Parse proposal count
            if 'less than' in proposals_text.lower():
                match = re.search(r'less than\s*(\d+)', proposals_text.lower())
                if match:
                    count = int(match.group(1))
                    result_count = max(0, count - 1)
                    print(f"   Parsed: {result_count} proposals (Less than {count})")
    
    # Test location extraction
    print("\n🌍 Testing Location Extraction:")
    about_client = soup.select_one('.cfe-about-client-v2, .about-client')
    if about_client:
        location_items = about_client.select('li')
        for item in location_items:
            qa_attr = item.get('data-qa', '')
            if 'location' in qa_attr:
                strong_elem = item.select_one('strong')
                if strong_elem:
                    location = strong_elem.get_text().strip()
                    print(f"   Found location: '{location}'")
                    
                    # Test country mapping
                    country_mapping = {
                        'bangladesh': 'Bangladesh',
                        'united states': 'United States',
                        'usa': 'United States'
                    }
                    
                    location_lower = location.lower()
                    country = location  # Default to location as country
                    for key, mapped_country in country_mapping.items():
                        if key in location_lower:
                            country = mapped_country
                            break
                    
                    print(f"   Mapped country: '{country}'")
    
    # Test time extraction
    print("\n⏰ Testing Time Extraction:")
    posted_sections = soup.select('.posted-on-line, [data-test="PostedOn"]')
    for section in posted_sections:
        time_spans = section.select('span')
        for span in time_spans:
            span_text = span.get_text().strip()
            if ('ago' in span_text.lower() or 
                'hour' in span_text.lower() or 
                'minute' in span_text.lower()) and any(char.isdigit() for char in span_text):
                print(f"   Found time: '{span_text}'")
                
                # Parse time
                minutes_match = re.search(r'(\d+)\s*minutes?\s*ago', span_text.lower())
                if minutes_match:
                    minutes = int(minutes_match.group(1))
                    hours_ago = minutes / 60.0
                    print(f"   Parsed: {minutes} minutes ago ({hours_ago:.2f} hours)")
    
    # Test member since for payment verification inference
    print("\n💳 Testing Payment Verification Inference:")
    member_since_elem = soup.select_one('small')
    if member_since_elem and 'member since' in member_since_elem.get_text().lower():
        member_text = member_since_elem.get_text().strip()
        print(f"   Found member info: '{member_text}'")
        
        # Extract year
        year_match = re.search(r'(\d{4})', member_text)
        if year_match:
            year = int(year_match.group(1))
            from datetime import datetime
            current_year = datetime.now().year
            account_age = current_year - year
            print(f"   Account age: {account_age} years")
            
            if account_age >= 1:
                print(f"   Payment status: Likely verified (established account)")
            else:
                print(f"   Payment status: Unknown (new account)")

if __name__ == "__main__":
    test_html_extraction() 
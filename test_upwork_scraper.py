#!/usr/bin/env python3
"""
Test script for enhanced Upwork data extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_upwork_data_enhanced import collect_upwork_data_with_filters
import json
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_upwork_extraction():
    """Test the enhanced Upwork data extraction"""
    print("🧪 Testing Enhanced Upwork Data Extraction")
    print("=" * 50)
    
    # Test with a simple keyword
    test_keywords = ["python"]
    
    # Simple filters
    test_filters = {
        'time_range': 'today',
        'hourly_filter': '',
        'budget_range': 'any',
        'job_type': 'any',
        'experience_level': 'any',
        'payment_status': 'both',
        'sort_by': 'recency'
    }
    
    print(f"🔍 Testing with keywords: {test_keywords}")
    print(f"📋 Using filters: {test_filters}")
    print()
    
    try:
        # Collect data
        result = collect_upwork_data_with_filters(
            keywords=test_keywords,
            filters=test_filters,
            use_persistence=False  # Don't save to file for testing
        )
        
        print("📊 Extraction Results:")
        print("-" * 30)
        
        jobs = result.get('jobs', [])
        print(f"✅ Total jobs collected: {len(jobs)}")
        
        if jobs:
            # Analyze first few jobs for data quality
            for i, job in enumerate(jobs[:3]):
                print(f"\n🔍 Job {i+1} Analysis:")
                print(f"  Title: {job.get('title', 'N/A')[:60]}...")
                
                # Check time data
                time_info = job.get('job_details', {}).get('posted_time', {})
                if isinstance(time_info, dict):
                    time_display = time_info.get('display', 'Unknown')
                    time_original = time_info.get('original', 'Unknown')
                    print(f"  Time: {time_display} (original: {time_original})")
                else:
                    print(f"  Time: {time_info}")
                
                # Check location data
                location = job.get('job_details', {}).get('client_location', 'Unknown')
                country = job.get('job_details', {}).get('client_country', 'Unknown')
                print(f"  Location: {location} / {country}")
                
                # Check proposals
                proposals_info = job.get('job_details', {}).get('proposals_count', {})
                if isinstance(proposals_info, dict):
                    count = proposals_info.get('count', 0)
                    display = proposals_info.get('display', 'Unknown')
                    print(f"  Proposals: {count} ({display})")
                else:
                    print(f"  Proposals: {proposals_info}")
                
                # Check payment status
                payment_info = job.get('job_details', {}).get('payment_verified', {})
                if isinstance(payment_info, dict):
                    status = payment_info.get('status', 'unknown')
                    display = payment_info.get('display', 'Unknown')
                    print(f"  Payment: {status} ({display})")
                else:
                    print(f"  Payment: {payment_info}")
                
                # Check budget
                budget = job.get('budget', {})
                if budget and budget.get('raw_text') != 'Budget not specified':
                    print(f"  Budget: {budget.get('raw_text', 'N/A')} ({budget.get('type', 'unknown')})")
                else:
                    print(f"  Budget: Not specified")
        
        # Summary analysis
        print(f"\n📈 Data Quality Analysis:")
        print("-" * 30)
        
        real_times = sum(1 for job in jobs if 
                        job.get('job_details', {}).get('posted_time', {}).get('original', 'Unknown') != 'Unknown')
        real_locations = sum(1 for job in jobs if 
                           job.get('job_details', {}).get('client_location', 'Unknown') not in ['Unknown', 'Not specified'])
        real_proposals = sum(1 for job in jobs if 
                           job.get('job_details', {}).get('proposals_count', {}).get('count', 0) > 0)
        real_payment = sum(1 for job in jobs if 
                         job.get('job_details', {}).get('payment_verified', {}).get('status', 'unknown') != 'unknown')
        real_budgets = sum(1 for job in jobs if 
                         job.get('budget', {}).get('raw_text', 'Budget not specified') != 'Budget not specified')
        
        total = len(jobs)
        if total > 0:
            print(f"⏰ Real posting times: {real_times}/{total} ({real_times/total*100:.1f}%)")
            print(f"🌍 Real locations: {real_locations}/{total} ({real_locations/total*100:.1f}%)")
            print(f"👥 Real proposal counts: {real_proposals}/{total} ({real_proposals/total*100:.1f}%)")
            print(f"💳 Real payment status: {real_payment}/{total} ({real_payment/total*100:.1f}%)")
            print(f"💰 Real budgets: {real_budgets}/{total} ({real_budgets/total*100:.1f}%)")
            
            # Overall data quality score
            quality_score = (real_times + real_locations + real_proposals + real_payment + real_budgets) / (total * 5) * 100
            print(f"\n🎯 Overall Data Quality Score: {quality_score:.1f}%")
            
            if quality_score > 80:
                print("🟢 Excellent data quality!")
            elif quality_score > 60:
                print("🟡 Good data quality, some improvements possible")
            elif quality_score > 40:
                print("🟠 Moderate data quality, needs improvement")
            else:
                print("🔴 Poor data quality, scraper needs fixing")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_upwork_extraction() 
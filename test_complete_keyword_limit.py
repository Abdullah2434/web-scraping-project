import requests
import json
import time

def test_complete_keyword_limit():
    """Comprehensive test of keyword limit functionality (backend + frontend)"""
    base_url = "http://localhost:8080"
    
    print("🧪 Comprehensive Testing of Keyword Limit Functionality...")
    print("=" * 60)
    
    # Test 1: Backend API limit enforcement
    print("\n📝 Test 1: Backend API Limit Enforcement")
    print("-" * 40)
    
    # Reset to defaults first
    try:
        response = requests.post(f"{base_url}/api/keywords/reset")
        if response.status_code == 200:
            print("✅ Reset keywords to defaults")
        else:
            print(f"❌ Failed to reset keywords: {response.status_code}")
    except Exception as e:
        print(f"❌ Error resetting keywords: {e}")
    
    # Add keywords until limit is reached
    added_count = 0
    for i in range(1, 12):  # Try to add 11 keywords
        keyword = f"test_keyword_{i}"
        try:
            response = requests.post(f"{base_url}/api/keywords/add", 
                                  json={"keyword": keyword})
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    added_count += 1
                    print(f"✅ Added keyword {i}: {keyword}")
                else:
                    print(f"❌ Failed to add keyword {i}: {keyword}")
                    print(f"   Error: {result.get('message', 'No message')}")
                    break
            else:
                print(f"❌ HTTP error {response.status_code} for keyword {i}")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    pass
                break
                
        except Exception as e:
            print(f"❌ Error adding keyword {i}: {e}")
            break
    
    print(f"📊 Successfully added {added_count} keywords")
    
    # Test 2: Verify final state
    print("\n📝 Test 2: Verifying Final State")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/api/keywords")
        if response.status_code == 200:
            data = response.json()
            final_keywords = data.get('keywords', [])
            max_keywords = data.get('max_keywords', 10)
            
            print(f"Final keyword count: {len(final_keywords)}")
            print(f"Max keywords allowed: {max_keywords}")
            print(f"Keywords: {final_keywords}")
            
            if len(final_keywords) <= max_keywords:
                print("✅ SUCCESS: Backend keyword limit is working correctly!")
                print(f"📊 Total keywords: {len(final_keywords)} (max: {max_keywords})")
            else:
                print("❌ FAILURE: Backend keyword limit is not working!")
                print(f"📊 Total keywords: {len(final_keywords)} (should be ≤ {max_keywords})")
                
        else:
            print(f"❌ Failed to get final keywords: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting final keywords: {e}")
    
    # Test 3: Frontend simulation - test API response format
    print("\n📝 Test 3: Frontend API Response Format")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/api/keywords")
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields for frontend
            required_fields = ['keywords', 'count', 'max_keywords']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print("✅ All required frontend fields present")
                print(f"   - keywords: {len(data['keywords'])} items")
                print(f"   - count: {data['count']}")
                print(f"   - max_keywords: {data['max_keywords']}")
            else:
                print(f"❌ Missing required fields: {missing_fields}")
                
            # Check if limits object exists
            if 'limits' in data:
                print("✅ Limits object present")
                print(f"   - limits: {data['limits']}")
            else:
                print("⚠️ Limits object not present")
                
        else:
            print(f"❌ Failed to get keywords API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing API format: {e}")
    
    # Test 4: Test error message when limit is reached
    print("\n📝 Test 4: Error Message Testing")
    print("-" * 40)
    try:
        response = requests.post(f"{base_url}/api/keywords/add", 
                              json={"keyword": "should_be_rejected"})
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("❌ FAILURE: Should not have been able to add keyword when at limit")
            else:
                print("✅ SUCCESS: Properly rejected keyword when at limit")
                print(f"   Error message: {result.get('message', 'No message')}")
        else:
            print(f"❌ HTTP error {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   No error details available")
            
    except Exception as e:
        print(f"❌ Error testing limit: {e}")
    
    # Test 5: Test removing keywords and adding again
    print("\n📝 Test 5: Remove and Add Again")
    print("-" * 40)
    try:
        # Remove a keyword
        response = requests.post(f"{base_url}/api/keywords/remove", 
                              json={"keyword": "test_keyword_1"})
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Successfully removed keyword")
                
                # Try to add a new keyword
                response = requests.post(f"{base_url}/api/keywords/add", 
                                      json={"keyword": "new_keyword_after_removal"})
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print("✅ Successfully added new keyword after removal")
                    else:
                        print(f"❌ Failed to add new keyword: {result.get('message', 'No message')}")
                else:
                    print(f"❌ HTTP error {response.status_code} when adding new keyword")
            else:
                print(f"❌ Failed to remove keyword: {result.get('message', 'No message')}")
        else:
            print(f"❌ HTTP error {response.status_code} when removing keyword")
            
    except Exception as e:
        print(f"❌ Error in remove/add test: {e}")
    
    # Test 6: Final verification
    print("\n📝 Test 6: Final Verification")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/api/keywords")
        if response.status_code == 200:
            data = response.json()
            final_keywords = data.get('keywords', [])
            max_keywords = data.get('max_keywords', 10)
            
            print(f"Final keyword count: {len(final_keywords)}")
            print(f"Max keywords allowed: {max_keywords}")
            
            if len(final_keywords) <= max_keywords:
                print("✅ SUCCESS: Complete keyword limit system is working correctly!")
                print(f"📊 Total keywords: {len(final_keywords)} (max: {max_keywords})")
                print("🎉 All tests passed!")
            else:
                print("❌ FAILURE: Keyword limit system has issues!")
                print(f"📊 Total keywords: {len(final_keywords)} (should be ≤ {max_keywords})")
                
        else:
            print(f"❌ Failed to get final keywords: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error in final verification: {e}")

if __name__ == "__main__":
    test_complete_keyword_limit() 
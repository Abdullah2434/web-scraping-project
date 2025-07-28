import requests
import json

def test_keyword_limit_detailed():
    """Detailed test of keyword limit functionality"""
    base_url = "http://localhost:8080"
    
    print("🧪 Detailed Testing of Keyword Limit Functionality...")
    
    # Test 1: Check current state
    print("\n📝 Test 1: Checking current keyword state")
    try:
        response = requests.get(f"{base_url}/api/keywords")
        if response.status_code == 200:
            data = response.json()
            current_keywords = data.get('keywords', [])
            print(f"Current keywords ({len(current_keywords)}): {current_keywords}")
            print(f"Max keywords allowed: {data.get('max_keywords', 'Unknown')}")
        else:
            print(f"❌ Failed to get keywords: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting keywords: {e}")
        return
    
    # Test 2: Try to add keywords one by one and see when limit is reached
    print("\n📝 Test 2: Adding keywords one by one to test limit")
    
    # Reset to defaults first
    try:
        response = requests.post(f"{base_url}/api/keywords/reset")
        if response.status_code == 200:
            print("✅ Reset keywords to defaults")
        else:
            print(f"❌ Failed to reset keywords: {response.status_code}")
    except Exception as e:
        print(f"❌ Error resetting keywords: {e}")
    
    # Add keywords one by one
    for i in range(1, 16):  # Try to add 15 keywords
        keyword = f"test_keyword_{i}"
        try:
            response = requests.post(f"{base_url}/api/keywords/add", 
                                  json={"keyword": keyword})
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Successfully added keyword {i}: {keyword}")
                else:
                    print(f"❌ Failed to add keyword {i}: {keyword}")
                    print(f"   Error message: {result.get('message', 'No message')}")
                    break
            else:
                print(f"❌ HTTP error {response.status_code} for keyword {i}: {keyword}")
                # Try to get error details
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   No error details available")
                break
                
        except Exception as e:
            print(f"❌ Error adding keyword {i}: {e}")
            break
    
    # Test 3: Check final state
    print("\n📝 Test 3: Checking final keyword state")
    try:
        response = requests.get(f"{base_url}/api/keywords")
        if response.status_code == 200:
            data = response.json()
            final_keywords = data.get('keywords', [])
            print(f"Final keyword count: {len(final_keywords)}")
            print(f"Final keywords: {final_keywords}")
            
            if len(final_keywords) <= 10:
                print("✅ SUCCESS: Keyword limit is properly enforced!")
                print(f"📊 Total keywords: {len(final_keywords)} (max: 10)")
            else:
                print("❌ FAILURE: Keyword limit is not enforced!")
                print(f"📊 Total keywords: {len(final_keywords)} (should be ≤ 10)")
                
        else:
            print(f"❌ Failed to get final keywords: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting final keywords: {e}")
    
    # Test 4: Try to add one more keyword and check error message
    print("\n📝 Test 4: Testing error message when limit is reached")
    try:
        response = requests.post(f"{base_url}/api/keywords/add", 
                              json={"keyword": "should_be_rejected"})
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("❌ FAILURE: Should not have been able to add keyword when at limit")
            else:
                print(f"✅ SUCCESS: Properly rejected keyword when at limit")
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

if __name__ == "__main__":
    test_keyword_limit_detailed() 
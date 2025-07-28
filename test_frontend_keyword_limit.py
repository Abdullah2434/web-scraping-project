import requests
import json
import time

def test_frontend_keyword_limit():
    """Test frontend keyword limit functionality"""
    base_url = "http://localhost:8080"
    
    print("🧪 Testing Frontend Keyword Limit Functionality...")
    
    # Test 1: Check if the frontend shows the correct limit
    print("\n📝 Test 1: Checking frontend keyword limit display")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            content = response.text
            if "Maximum 10 keywords allowed" in content or "max 10" in content.lower():
                print("✅ Frontend shows keyword limit information")
            else:
                print("⚠️ Frontend may not show keyword limit information")
            print("📄 Frontend is accessible")
        else:
            print(f"❌ Failed to access frontend: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing frontend: {e}")
    
    # Test 2: Test API response format for frontend
    print("\n📝 Test 2: Testing API response format")
    try:
        response = requests.get(f"{base_url}/api/keywords")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API response format: {json.dumps(data, indent=2)}")
            
            # Check if response includes limit information
            if 'max_keywords' in data:
                print(f"✅ API includes max_keywords: {data['max_keywords']}")
            else:
                print("⚠️ API doesn't include max_keywords field")
                
        else:
            print(f"❌ Failed to get keywords API: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing API format: {e}")
    
    # Test 3: Test adding keyword when at limit (simulate frontend behavior)
    print("\n📝 Test 3: Testing frontend-like keyword addition")
    
    # First, ensure we're at the limit
    try:
        # Reset to defaults
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
        keyword = f"frontend_test_{i}"
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
                break
                
        except Exception as e:
            print(f"❌ Error adding keyword {i}: {e}")
            break
    
    print(f"📊 Successfully added {added_count} keywords")
    
    # Test 4: Verify final state
    print("\n📝 Test 4: Verifying final keyword state")
    try:
        response = requests.get(f"{base_url}/api/keywords")
        if response.status_code == 200:
            data = response.json()
            final_keywords = data.get('keywords', [])
            print(f"Final keyword count: {len(final_keywords)}")
            
            if len(final_keywords) <= 10:
                print("✅ SUCCESS: Frontend keyword limit is working correctly!")
                print(f"📊 Total keywords: {len(final_keywords)} (max: 10)")
            else:
                print("❌ FAILURE: Frontend keyword limit is not working!")
                print(f"📊 Total keywords: {len(final_keywords)} (should be ≤ 10)")
                
        else:
            print(f"❌ Failed to get final keywords: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting final keywords: {e}")

if __name__ == "__main__":
    test_frontend_keyword_limit() 
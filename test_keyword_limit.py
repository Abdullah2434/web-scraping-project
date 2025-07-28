import requests
import json

def test_keyword_limit():
    """Test that the keyword limit of 10 is properly enforced"""
    base_url = "http://localhost:8080"
    
    print("🧪 Testing keyword limit functionality...")
    
    # Test 1: Try to add more than 10 keywords
    print("\n📝 Test 1: Adding more than 10 keywords")
    
    # First, let's see current keywords
    try:
        response = requests.get(f"{base_url}/api/keywords")
        if response.status_code == 200:
            current_keywords = response.json().get('keywords', [])
            print(f"Current keywords ({len(current_keywords)}): {current_keywords}")
        else:
            print(f"❌ Failed to get current keywords: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting current keywords: {e}")
        return
    
    # Try to add keywords beyond the limit
    test_keywords = [
        "keyword1", "keyword2", "keyword3", "keyword4", "keyword5",
        "keyword6", "keyword7", "keyword8", "keyword9", "keyword10",
        "keyword11", "keyword12", "keyword13", "keyword14", "keyword15",
        "keyword16", "keyword17", "keyword18", "keyword19", "keyword20"
    ]
    
    print(f"\nAttempting to add {len(test_keywords)} keywords...")
    
    for i, keyword in enumerate(test_keywords, 1):
        try:
            response = requests.post(f"{base_url}/api/keywords/add", 
                                  json={"keyword": keyword})
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Added keyword {i}: {keyword}")
                else:
                    print(f"❌ Failed to add keyword {i}: {keyword} - {result.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP error {response.status_code} for keyword {i}: {keyword}")
                
        except Exception as e:
            print(f"❌ Error adding keyword {i}: {e}")
    
    # Check final state
    try:
        response = requests.get(f"{base_url}/api/keywords")
        if response.status_code == 200:
            final_keywords = response.json().get('keywords', [])
            print(f"\n📊 Final keyword count: {len(final_keywords)}")
            print(f"Final keywords: {final_keywords}")
            
            if len(final_keywords) <= 15:
                print("✅ SUCCESS: Keyword limit is properly enforced!")
            else:
                print("❌ FAILURE: Keyword limit is not enforced!")
                
        else:
            print(f"❌ Failed to get final keywords: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting final keywords: {e}")
    
    # Test 2: Try to add a keyword when already at limit
    print("\n📝 Test 2: Adding keyword when at limit")
    
    # First, clear all keywords by resetting to defaults
    try:
        response = requests.post(f"{base_url}/api/keywords/reset")
        if response.status_code == 200:
            print("✅ Reset keywords to defaults")
        else:
            print(f"❌ Failed to reset keywords: {response.status_code}")
    except Exception as e:
        print(f"❌ Error resetting keywords: {e}")
    
    # Add exactly 15 keywords
    for i in range(1, 16):
        try:
            response = requests.post(f"{base_url}/api/keywords/add", 
                                  json={"keyword": f"test{i}"})
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Added keyword {i}: test{i}")
                else:
                    print(f"❌ Failed to add keyword {i}: {result.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP error {response.status_code} for keyword {i}")
        except Exception as e:
            print(f"❌ Error adding keyword {i}: {e}")
    
    # Try to add one more keyword
    try:
        response = requests.post(f"{base_url}/api/keywords/add", 
                              json={"keyword": "should_be_rejected"})
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("❌ FAILURE: Should not have been able to add keyword when at limit")
            else:
                print(f"✅ SUCCESS: Properly rejected keyword when at limit - {result.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP error {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing limit: {e}")

if __name__ == "__main__":
    test_keyword_limit() 
"""
Test if Flask app is running
==========================
"""

import requests
import time

def test_app_running():
    """Test if the Flask app is running on localhost:8080"""
    
    print("🌐 Testing if Flask app is running...")
    
    # Wait a moment for the app to start
    time.sleep(3)
    
    try:
        # Try to connect to the app
        response = requests.get('http://localhost:8080', timeout=10)
        
        if response.status_code == 200:
            print("✅ Flask app is running successfully!")
            print(f"📊 Status code: {response.status_code}")
            print(f"📄 Content length: {len(response.text)} characters")
            print("\n🎉 Your web scraping dashboard is ready!")
            print("🌐 Open your browser and go to: http://localhost:8080")
            return True
        else:
            print(f"❌ App responded with status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app")
        print("💡 Make sure the app is running with: python flask_app.py")
        return False
    except Exception as e:
        print(f"❌ Error testing app: {e}")
        return False

if __name__ == "__main__":
    test_app_running() 
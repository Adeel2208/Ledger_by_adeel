"""Test the channels endpoint."""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_channels():
    """Test channels analytics endpoint."""
    print("\n=== Testing Channels Analytics ===")
    url = f"{BASE_URL}/api/v1/analytics/channels"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"\nFull response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_channels()

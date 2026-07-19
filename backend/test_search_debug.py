"""Debug search endpoint issues."""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_simple_search():
    """Test simple search endpoint."""
    print("\n=== Testing Simple Search ===")
    url = f"{BASE_URL}/api/v1/search/simple"
    payload = {
        "query": "AI startup",
        "k": 5
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def test_advanced_search():
    """Test advanced NL search endpoint."""
    print("\n=== Testing Advanced Search ===")
    url = f"{BASE_URL}/api/v1/search"
    payload = {
        "query": "technical founder in AI",
        "k": 5,
        "filters": {}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_simple_search()
    test_advanced_search()

#!/usr/bin/env python
"""Test all new enhanced endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(name, method, url, data=None):
    """Test a single endpoint."""
    try:
        if method == "GET":
            r = requests.get(url, timeout=10)
        elif method == "POST":
            r = requests.post(url, json=data, timeout=10)
        
        print(f"OK {name}: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            # Show a sample of the response
            if isinstance(result, dict):
                print(f"  Keys: {list(result.keys())[:5]}")
            elif isinstance(result, list):
                print(f"  Count: {len(result)}")
            return True
        else:
            print(f"  Error: {r.text[:100]}")
            return False
    except Exception as e:
        print(f"FAIL {name}: {str(e)[:100]}")
        return False

print("="*60)
print("Testing Enhanced Endpoints")
print("="*60 + "\n")

# Test search endpoints
print("Search & Reasoning:")
test_endpoint(
    "Advanced NL Search",
    "POST",
    f"{BASE_URL}/search",
    {"query": "technical founder with GitHub", "k": 5}
)
test_endpoint(
    "Simple Search",
    "POST",
    f"{BASE_URL}/search/simple",
    {"query": "AI founder", "k": 5}
)

# Test intelligence endpoints
print("\nIntelligence & Analysis:")
test_endpoint(
    "Signal Analysis",
    "POST",
    f"{BASE_URL}/intelligence/analyze",
    {"founder_id": 1}
)
test_endpoint(
    "Trajectory Forecast",
    "POST",
    f"{BASE_URL}/intelligence/forecast",
    {"founder_id": 1, "horizon_months": 6}
)
test_endpoint(
    "Success Probability",
    "POST",
    f"{BASE_URL}/intelligence/success-probability",
    {"founder_id": 1}
)
test_endpoint(
    "Risk Assessment",
    "POST",
    f"{BASE_URL}/intelligence/risk-assessment",
    {"founder_id": 1}
)
test_endpoint(
    "Optimal Timing",
    "POST",
    f"{BASE_URL}/intelligence/optimal-timing",
    {"founder_id": 1}
)
test_endpoint(
    "Anomaly Detection",
    "POST",
    f"{BASE_URL}/intelligence/anomaly-detection",
    {"founder_id": 1}
)
test_endpoint(
    "Pattern Mining",
    "POST",
    f"{BASE_URL}/intelligence/mine-patterns",
    {"lookback_months": 12}
)
test_endpoint(
    "Complete Intelligence",
    "POST",
    f"{BASE_URL}/intelligence/complete-intelligence",
    {"founder_id": 1}
)

# Test analytics
print("\nAnalytics:")
test_endpoint(
    "Dashboard Analytics",
    "GET",
    f"{BASE_URL}/analytics/dashboard?lookback_days=30",
)

# Test sourcing
print("\nSourcing:")
test_endpoint(
    "Discovered Founders",
    "GET",
    f"{BASE_URL}/sourcing/discovered?include_intelligence=true",
)
test_endpoint(
    "Channel Analytics",
    "GET",
    f"{BASE_URL}/sourcing/channel-analytics?lookback_days=90",
)

print("\n" + "="*60)
print("Testing Complete!")
print("="*60)

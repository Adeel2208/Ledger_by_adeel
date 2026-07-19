#!/usr/bin/env python
"""Smoke-check the enhanced endpoints against a RUNNING server.

Not a pytest suite — run it directly:  python test_new_endpoints.py
(The helper is deliberately named `check_*`, not `test_*`, and the calls live
under `__main__`: a `test_`-prefixed function here would be collected by pytest
and its arguments misread as fixtures, and module-level requests would fire
during collection.)
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def check_endpoint(name, method, url, data=None):
    """Call a single endpoint and report its status."""
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

if __name__ == "__main__":
    print("="*60)
    print("Testing Enhanced Endpoints")
    print("="*60 + "\n")

    # Test search endpoints
    print("Search & Reasoning:")
    check_endpoint(
        "Advanced NL Search",
        "POST",
        f"{BASE_URL}/search",
        {"query": "technical founder with GitHub", "k": 5}
    )
    check_endpoint(
        "Simple Search",
        "POST",
        f"{BASE_URL}/search/simple",
        {"query": "AI founder", "k": 5}
    )

    # Test intelligence endpoints
    print("\nIntelligence & Analysis:")
    check_endpoint(
        "Signal Analysis",
        "POST",
        f"{BASE_URL}/intelligence/analyze",
        {"founder_id": 1}
    )
    check_endpoint(
        "Trajectory Forecast",
        "POST",
        f"{BASE_URL}/intelligence/forecast",
        {"founder_id": 1, "horizon_months": 6}
    )
    check_endpoint(
        "Success Probability",
        "POST",
        f"{BASE_URL}/intelligence/success-probability",
        {"founder_id": 1}
    )
    check_endpoint(
        "Risk Assessment",
        "POST",
        f"{BASE_URL}/intelligence/risk-assessment",
        {"founder_id": 1}
    )
    check_endpoint(
        "Optimal Timing",
        "POST",
        f"{BASE_URL}/intelligence/optimal-timing",
        {"founder_id": 1}
    )
    check_endpoint(
        "Anomaly Detection",
        "POST",
        f"{BASE_URL}/intelligence/anomaly-detection",
        {"founder_id": 1}
    )
    check_endpoint(
        "Pattern Mining",
        "POST",
        f"{BASE_URL}/intelligence/mine-patterns",
        {"lookback_months": 12}
    )
    check_endpoint(
        "Complete Intelligence",
        "POST",
        f"{BASE_URL}/intelligence/complete-intelligence",
        {"founder_id": 1}
    )

    # Test analytics
    print("\nAnalytics:")
    check_endpoint(
        "Dashboard Analytics",
        "GET",
        f"{BASE_URL}/analytics/dashboard?lookback_days=30",
    )

    # Test sourcing
    print("\nSourcing:")
    check_endpoint(
        "Discovered Founders",
        "GET",
        f"{BASE_URL}/sourcing/discovered?include_intelligence=true",
    )
    check_endpoint(
        "Channel Analytics",
        "GET",
        f"{BASE_URL}/sourcing/channel-analytics?lookback_days=90",
    )

    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)

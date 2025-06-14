#!/usr/bin/env python3
"""
Quick test script to test the transit calculation directly
"""

import requests
import json
from datetime import datetime

# Test data
test_payload = {
    "name": "Test Transit",
    "birth_date": "1990-01-01", 
    "birth_time": "12:00",
    "birth_city": "New York, NY",
    "birth_state": "NY",
    "birth_country": "United States",
    "timezone": "America/New_York",
    "use_extended_planets": True
}

print("Testing transit calculation with payload:")
print(json.dumps(test_payload, indent=2))

try:
    response = requests.post("http://localhost:5000/api/calculate", json=test_payload)
    print(f"\nResponse status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Transit ephemeris calculation successful!")
        data = response.json()
        print(f"Got {len(data.get('planets', []))} planets")
    else:
        print("❌ Transit ephemeris calculation failed!")
        print(f"Error: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")

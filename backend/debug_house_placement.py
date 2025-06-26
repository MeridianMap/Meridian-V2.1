#!/usr/bin/env python3
"""
Debug test for house placement
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from house_placement import add_house_placements_to_chart_data, get_zodiac_sign_name, calculate_house_placement

# Mock chart data
test_chart = {
    'houses': {
        'ascendant': {'longitude': 150.0},  # Virgo ascendant
        'house_system': 'whole_sign'
    },
    'fixed_stars': [
        {'name': 'Test Star', 'longitude': 180.0},  # Libra
    ],
    'lots': [
        {'name': 'Lot of Fortune', 'longitude': 210.0},  # Scorpio
    ],
    'planets': [
        {'name': 'Sun', 'longitude': 120.0},  # Leo
    ]
}

print("Before adding house placements:")
print("Fixed Star:", test_chart['fixed_stars'][0])
print("Lot:", test_chart['lots'][0])
print("Planet:", test_chart['planets'][0])

# Add house placements
result = add_house_placements_to_chart_data(test_chart)

print("\nAfter adding house placements:")
print("Fixed Star:", result['fixed_stars'][0])
print("Lot:", result['lots'][0])
print("Planet:", result['planets'][0])

# Test individual functions
print(f"\nDirect test - Sign for 180 degrees: {get_zodiac_sign_name(180.0)}")
print(f"Direct test - House for 180 degrees with 150 asc: {calculate_house_placement(180.0, 150.0, 'whole_sign')}")

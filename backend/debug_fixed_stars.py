#!/usr/bin/env python3
"""
Debug fixed stars matching
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fixed_star import get_fixed_star_positions
from ephemeris import calculate_chart

# Test chart
test_data = {
    'birth_date': '1990-01-01',
    'birth_time': '12:00',
    'latitude': 40.7128,
    'longitude': -74.0060,
    'timezone': 'America/New_York',
    'house_system': 'whole_sign'
}

try:
    # Get fixed stars from Swiss Ephemeris (what astrocartography uses)
    from ephemeris_utils import initialize_ephemeris
    initialize_ephemeris()
    
    from ephemeris_utils import julian_day_from_date_time
    jd = julian_day_from_date_time("1990", "01", "01", "12", "00", "00")
    
    ephemeris_stars = get_fixed_star_positions(jd)
    print("=== EPHEMERIS STARS (astrocartography source) ===")
    for i, star in enumerate(ephemeris_stars[:3]):
        print(f"Star {i+1}: '{star.get('name')}'")
        print(f"  Has house: {'house' in star}")
        print(f"  Has sign: {'sign' in star}")
        print()
    
    # Get fixed stars from chart data (what should have house/sign info)
    chart = calculate_chart(test_data)
    chart_stars = chart.get('fixed_stars', [])
    print("=== CHART STARS (should have house/sign) ===")
    for i, star in enumerate(chart_stars[:3]):
        print(f"Star {i+1}: '{star.get('name')}'")
        print(f"  House: {star.get('house')}")
        print(f"  Sign: {star.get('sign')}")
        print()
    
    # Test matching
    print("=== MATCHING TEST ===")
    for eph_star in ephemeris_stars[:3]:
        eph_name = eph_star.get("name")
        matching_chart_star = next((s for s in chart_stars if s.get("name") == eph_name), None)
        print(f"Ephemeris star '{eph_name}' -> Chart match: {matching_chart_star is not None}")
        if matching_chart_star:
            print(f"  Matched house: {matching_chart_star.get('house')}")
            print(f"  Matched sign: {matching_chart_star.get('sign')}")
        print()

except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()

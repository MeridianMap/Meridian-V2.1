#!/usr/bin/env python3
"""
Simple test to check fixed stars and lots data
"""

from ephemeris import calculate_chart

test_data = {
    'birth_date': '1990-01-01',
    'birth_time': '12:00',
    'latitude': 40.7128,
    'longitude': -74.0060,
    'timezone': 'America/New_York',
    'house_system': 'whole_sign'
}

try:
    result = calculate_chart(test_data)
    
    print("=== FIXED STARS ===")
    fixed_stars = result.get('fixed_stars', [])
    print(f"Found {len(fixed_stars)} fixed stars")
    if fixed_stars:
        for i, star in enumerate(fixed_stars[:3]):  # Show first 3
            print(f"Star {i+1}: {star.get('name')}")
            print(f"  House: {star.get('house')}")
            print(f"  Sign: {star.get('sign')}")
            print(f"  Longitude: {star.get('longitude')}")
            print()
    
    print("=== HERMETIC LOTS ===")
    lots = result.get('lots', [])
    print(f"Found {len(lots)} lots")
    if lots:
        for i, lot in enumerate(lots[:3]):  # Show first 3
            print(f"Lot {i+1}: {lot.get('name')}")
            print(f"  House: {lot.get('house')}")
            print(f"  Sign: {lot.get('sign')}")
            print(f"  Longitude: {lot.get('longitude')}")
            print()
            
    print("=== PLANETS (for comparison) ===")
    planets = result.get('planets', [])
    if planets:
        first_planet = planets[0]
        print(f"Planet: {first_planet.get('name')}")
        print(f"  House: {first_planet.get('house')}")
        print(f"  Sign: {first_planet.get('sign')}")

except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()

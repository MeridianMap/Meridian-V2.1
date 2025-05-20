#!/usr/bin/env python3
"""
Debug script for Swiss Ephemeris calculations
This script tests the Swiss Ephemeris calculations directly
"""

import swisseph as swe
import sys
import os
import json

# Add the parent directory to the path so we can import the ephemeris module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.ephemeris import calculate_chart, calculate_planets

def debug_swiss_ephemeris():
    """Debug Swiss Ephemeris calculations"""
    print("Debugging Swiss Ephemeris calculations...")
    
    # Set ephemeris path
    print("Setting ephemeris path...")
    swe.set_ephe_path()
    
    # Print Swiss Ephemeris version
    print(f"Swiss Ephemeris version: {swe.version}")
    
    # Test Julian day calculation
    print("\nTesting Julian day calculation...")
    jd = swe.julday(2000, 1, 1, 12)
    print(f"Julian day for 2000-01-01 12:00: {jd}")
    
    # Test direct planet calculation
    print("\nTesting direct planet calculation...")
    try:
        # Calculate Sun position
        sun_result = swe.calc_ut(jd, swe.SUN)
        print(f"Sun position: {sun_result}")
        
        # Calculate Moon position
        moon_result = swe.calc_ut(jd, swe.MOON)
        print(f"Moon position: {moon_result}")
        
        # Test our calculate_planets function
        print("\nTesting calculate_planets function...")
        planets = calculate_planets(jd)
        print(f"Number of planets calculated: {len(planets)}")
        if len(planets) > 0:
            print(f"First planet: {planets[0]['name']} in {planets[0]['sign']}")
        else:
            print("No planets returned!")
            
        # Test full chart calculation
        print("\nTesting full chart calculation...")
        chart = calculate_chart(
            birth_date="1990-01-01",
            birth_time="12:00",
            birth_location="New York, USA",
            timezone="America/New_York",
            house_system="whole_sign"
        )
        
        # Check if planets were calculated
        if "planets" in chart and len(chart["planets"]) > 0:
            print(f"Chart calculation successful. {len(chart['planets'])} planets calculated.")
            # Save chart to file for inspection
            with open("/home/ubuntu/astro-app/backend/debug_chart.json", "w") as f:
                json.dump(chart, f, indent=2)
            print("Chart saved to debug_chart.json")
        else:
            print("Chart calculation failed. No planets returned.")
            print(f"Chart data: {chart}")
            
    except Exception as e:
        print(f"Error in Swiss Ephemeris calculations: {e}")

if __name__ == "__main__":
    debug_swiss_ephemeris()

    # Print out the standard planet IDs for Swiss Ephemeris
    print("Swiss Ephemeris planet IDs:")
    print(f"SUN: {swe.SUN}")
    print(f"MOON: {swe.MOON}")
    print(f"MERCURY: {swe.MERCURY}")
    print(f"VENUS: {swe.VENUS}")
    print(f"MARS: {swe.MARS}")
    print(f"JUPITER: {swe.JUPITER}")
    print(f"SATURN: {swe.SATURN}")
    print(f"URANUS: {swe.URANUS}")
    print(f"NEPTUNE: {swe.NEPTUNE}")
    print(f"PLUTO: {swe.PLUTO}")
    # Chiron is a minor planet/asteroid, its ID is usually 15 in Swiss Ephemeris
    print(f"CHIRON: {getattr(swe, 'CHIRON', 15)}")

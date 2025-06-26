#!/usr/bin/env python3
"""
Debug fixed stars and lots house/sign propagation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ephemeris import calculate_chart
from backend.astrocartography import generate_all_astrocartography_features
import json

def test_fixed_stars_houses():
    """Test that fixed stars have house and sign information"""
    print("Testing fixed stars house/sign propagation...")
    
    # Calculate a basic chart
    chart = calculate_chart(
        birth_date="1990-07-15",
        birth_time="12:00",
        birth_city="New York",
        birth_state="NY", 
        birth_country="USA",
        timezone="America/New_York",
        house_system="whole_sign"
    )
    
    if "error" in chart:
        print(f"Chart error: {chart['error']}")
        return
    
    print(f"\nChart calculated successfully")
    print(f"Number of fixed stars: {len(chart.get('fixed_stars', []))}")
    
    # Print first few fixed stars with house/sign info
    for i, star in enumerate(chart.get('fixed_stars', [])[:5]):
        print(f"Star {i+1}: {star.get('name', 'Unknown')}")
        print(f"  House: {star.get('house', 'Missing')}")
        print(f"  Sign: {star.get('sign', 'Missing')}")
        print(f"  Longitude: {star.get('longitude', 'Missing')}")
        print()
      # Test astrocartography generation
    print("Testing astrocartography data generation...")
    astro_features = generate_all_astrocartography_features(chart, {
        'include_fixed_stars': True,
        'include_lots': True
    })
    
    # Find fixed star features
    star_features = [f for f in astro_features if f['properties'].get('type') == 'fixed_star']
    print(f"Number of fixed star features: {len(star_features)}")
    
    # Print first few fixed star features with house/sign info
    for i, feature in enumerate(star_features[:3]):
        props = feature['properties']
        print(f"Feature {i+1}: {props.get('star', 'Unknown')}")
        print(f"  House: {props.get('house', 'Missing')}")
        print(f"  Sign: {props.get('sign', 'Missing')}")
        print()

if __name__ == "__main__":
    test_fixed_stars_houses()

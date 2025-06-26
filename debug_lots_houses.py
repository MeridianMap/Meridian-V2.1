#!/usr/bin/env python3
"""
Debug Hermetic Lots house/sign propagation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ephemeris import calculate_chart
from backend.astrocartography import generate_all_astrocartography_features
import json

def test_lots_houses():
    """Test that Hermetic Lots have house and sign information"""
    print("Testing Hermetic Lots house/sign propagation...")
    
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
    print(f"Number of Hermetic Lots: {len(chart.get('lots', []))}")
    
    # Print first few lots with house/sign info
    for i, lot in enumerate(chart.get('lots', [])[:5]):
        print(f"Lot {i+1}: {lot.get('name', 'Unknown')}")
        print(f"  House: {lot.get('house', 'Missing')}")
        print(f"  Sign: {lot.get('sign', 'Missing')}")
        print(f"  Longitude: {lot.get('longitude', 'Missing')}")
        print()
      # Test astrocartography generation
    print("Testing astrocartography features generation...")
    astro_features = generate_all_astrocartography_features(chart, {
        'include_fixed_stars': True,
        'include_lots': True,
        'include_hermetic_lots': True
    })
      # Find lot features
    lot_features = [f for f in astro_features if f['properties'].get('category') == 'hermetic_lot']
    print(f"Number of lot features: {len(lot_features)}")
      # Print first few lot features with house/sign info
    for i, feature in enumerate(lot_features[:3]):
        props = feature['properties']
        print(f"Feature {i+1}: {props.get('planet', 'Unknown')} {props.get('line_type', '')}")
        print(f"  House: {props.get('house', 'Missing')}")
        print(f"  Sign: {props.get('sign', 'Missing')}")
        print()

if __name__ == "__main__":
    test_lots_houses()

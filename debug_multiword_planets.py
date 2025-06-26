#!/usr/bin/env python3
"""
Debug multi-word planet names in house/sign propagation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ephemeris import calculate_chart
from backend.astrocartography import generate_all_astrocartography_features
import json

def test_multiword_planets():
    """Test that multi-word planets have house and sign information"""
    print("Testing multi-word planets house/sign propagation...")
    
    # Calculate a chart with extended planets to get multi-word names
    chart = calculate_chart(
        birth_date="1990-07-15",
        birth_time="12:00",
        birth_city="New York",
        birth_state="NY", 
        birth_country="USA",
        timezone="America/New_York",
        house_system="whole_sign",
        use_extended_planets=True  # This should include Pallas Athena, Black Moon Lilith, etc.
    )
    
    if "error" in chart:
        print(f"Chart error: {chart['error']}")
        return
    
    print(f"\nChart calculated successfully")
    
    # Find multi-word planets
    multiword_planets = [p for p in chart.get('planets', []) if ' ' in p.get('name', '')]
    print(f"Multi-word planets found: {len(multiword_planets)}")
    
    for planet in multiword_planets:
        print(f"  {planet.get('name', 'Unknown')}: house={planet.get('house', 'Missing')}, sign={planet.get('sign', 'Missing')}")
    
    # Test astrocartography generation
    print("\nTesting astrocartography features generation...")
    astro_features = generate_all_astrocartography_features(chart, {
        'include_fixed_stars': True,
        'include_hermetic_lots': True,
        'include_ic_mc': True,
        'include_ac_dc': True
    })
    
    # Find IC/MC features for multi-word planets
    multiword_ic_mc_features = []
    multiword_acdc_features = []
    
    for feature in astro_features:
        props = feature.get('properties', {})
        planet_name = props.get('planet', '')
        body_name = props.get('body', '')
        
        # Check if this is a multi-word planet feature
        if (' ' in planet_name) or (' ' in body_name):
            line_type = props.get('line_type', '')
            if line_type in ['MC', 'IC']:
                multiword_ic_mc_features.append(feature)
            elif line_type in ['AC', 'DC', 'HORIZON']:
                multiword_acdc_features.append(feature)
    
    print(f"\nMulti-word IC/MC features: {len(multiword_ic_mc_features)}")
    for i, feature in enumerate(multiword_ic_mc_features[:3]):
        props = feature['properties']
        print(f"  {i+1}: {props.get('body', props.get('planet', 'Unknown'))} {props.get('line_type', '')}")
        print(f"      House: {props.get('house', 'Missing')}")
        print(f"      Sign: {props.get('sign', 'Missing')}")
    
    print(f"\nMulti-word AC/DC features: {len(multiword_acdc_features)}")
    for i, feature in enumerate(multiword_acdc_features[:3]):
        props = feature['properties']
        print(f"  {i+1}: {props.get('planet', 'Unknown')} {props.get('line_type', '')}")
        print(f"      House: {props.get('house', 'Missing')}")
        print(f"      Sign: {props.get('sign', 'Missing')}")

if __name__ == "__main__":
    test_multiword_planets()

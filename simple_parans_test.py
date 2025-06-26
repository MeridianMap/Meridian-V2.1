#!/usr/bin/env python3
"""
Simple debug test for parans Human Design gate integration.
"""

import json
from backend.astrocartography import generate_all_astrocartography_features

def simple_parans_test():
    """Simple test to debug parans gate integration."""
    
    test_chart_data = {
        "utc_time": {"julian_day": 2459396.5},
        "planets": [
            {
                "name": "Sun",
                "id": 0,
                "longitude": 15.5,
                "ra": 10.2,
                "dec": 8.1,
                "house": 1,
                "sign": "Aries"
            },
            {
                "name": "Jupiter",
                "id": 5,
                "longitude": 240.8,
                "ra": 250.2,
                "dec": -20.3,
                "house": 9,
                "sign": "Sagittarius"
            }
        ]
    }
    
    print("Simple parans test with debug output...")
    
    filter_options = {
        "include_ac_dc": True,
        "include_ic_mc": True,
        "include_fixed_stars": False,
        "include_hermetic_lots": False,
        "include_aspects": False,
        "include_parans": True,
        "layer_type": "natal"
    }
    
    features = generate_all_astrocartography_features(test_chart_data, filter_options)
    
    parans = [f for f in features if f.get("properties", {}).get("category") == "parans"]
    print(f"\nGenerated {len(parans)} parans features")
    
    if parans:
        print("\nFirst parans feature properties:")
        for key, value in parans[0]["properties"].items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    simple_parans_test()

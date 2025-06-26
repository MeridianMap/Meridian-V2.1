#!/usr/bin/env python3
"""
Debug script to trace Human Design gate information through parans generation.
"""

import json
from backend.astrocartography import generate_all_astrocartography_features

def debug_parans_gate_flow():
    """Debug the flow of Human Design gate information in parans."""
    
    # Create test chart data
    test_chart_data = {
        "utc_time": {"julian_day": 2459396.5},
        "planets": [
            {
                "name": "Sun",
                "id": 0,
                "longitude": 15.5,  # Gate 51
                "ra": 10.2,
                "dec": 8.1,
                "house": 1,
                "sign": "Aries"
            },
            {
                "name": "Jupiter",
                "id": 5,
                "longitude": 240.8,  # Gate 60
                "ra": 250.2,
                "dec": -20.3,
                "house": 9,
                "sign": "Sagittarius"
            }
        ]
    }
    
    print("🔍 DEBUGGING PARANS HUMAN DESIGN GATE FLOW")
    print("=" * 50)
    
    # Generate all features
    filter_options = {
        "include_ac_dc": True,
        "include_ic_mc": True,
        "include_fixed_stars": False,
        "include_hermetic_lots": False,
        "include_aspects": False,
        "include_parans": True,
        "layer_type": "natal"
    }
    
    all_features = generate_all_astrocartography_features(test_chart_data, filter_options)
    
    # Check planet lines first (these should have gate info)
    planet_features = [f for f in all_features if f.get("properties", {}).get("category") == "planet"]
    parans_features = [f for f in all_features if f.get("properties", {}).get("category") == "parans"]
    
    print(f"Generated {len(planet_features)} planet line features")
    print(f"Generated {len(parans_features)} parans features")
    
    print("\n🔍 STEP 1: Check Planet Lines Have Gate Info")
    print("-" * 50)
    
    planet_gate_info = {}
    for feature in planet_features:
        props = feature.get("properties", {})
        planet_name = props.get("planet", "Unknown")
        line_type = props.get("line_type", "")
        
        # Clean planet name
        clean_name = planet_name.replace(" CCG", "").replace(" Transit", "").replace(" HD", "")
        
        print(f"{planet_name} {line_type}:")
        if "hd_gate" in props:
            gate = props["hd_gate"]
            gate_name = props.get("hd_gate_name", "")
            line = props.get("hd_line", "")
            print(f"  ✓ HD Gate: {gate} - {gate_name}")
            if line:
                print(f"  ✓ HD Line: {line}")
            
            # Store for comparison
            if clean_name not in planet_gate_info:
                planet_gate_info[clean_name] = {
                    "gate": gate,
                    "gate_name": gate_name,
                    "line": line,
                    "house": props.get("house"),
                    "sign": props.get("sign")
                }
        else:
            print(f"  ✗ No HD Gate info")
        
        if "house" in props:
            print(f"  House: {props['house']}")
        if "sign" in props:
            print(f"  Sign: {props['sign']}")
        print()
    
    print(f"\n🔍 STEP 2: Planet Info Available for Parans")
    print("-" * 50)
    for planet, info in planet_gate_info.items():
        print(f"{planet}: Gate {info['gate']} - {info['gate_name']}, Line {info['line']}")
    
    print(f"\n🔍 STEP 3: Check Parans Features")
    print("-" * 50)
    
    if not parans_features:
        print("❌ No parans features generated!")
        return
    
    for i, feature in enumerate(parans_features):
        props = feature.get("properties", {})
        label = props.get("label", "Unknown")
        source_lines = props.get("source_lines", [])
        
        print(f"Parans {i+1}: {label}")
        print(f"  Source lines: {source_lines}")
        
        # Check all properties for debugging
        print(f"  All properties keys: {list(props.keys())}")
        
        if len(source_lines) >= 2:
            planet1 = source_lines[0].split("_")[0] if "_" in source_lines[0] else ""
            planet2 = source_lines[1].split("_")[0] if "_" in source_lines[1] else ""
            
            print(f"  Extracted planets: {planet1}, {planet2}")
            
            # Check for planet-specific properties
            for planet in [planet1, planet2]:
                clean_planet = planet.replace(" CCG", "").replace(" Transit", "").replace(" HD", "")
                
                # Check gate info
                gate_key = f"{clean_planet}_hd_gate"
                gate_name_key = f"{clean_planet}_hd_gate_name"
                line_key = f"{clean_planet}_hd_line"
                house_key = f"{clean_planet}_house"
                sign_key = f"{clean_planet}_sign"
                
                print(f"    {planet}:")
                print(f"      Looking for keys: {gate_key}, {gate_name_key}, {line_key}")
                
                if gate_key in props:
                    print(f"      ✓ Found {gate_key}: {props[gate_key]}")
                else:
                    print(f"      ✗ Missing {gate_key}")
                
                if gate_name_key in props:
                    print(f"      ✓ Found {gate_name_key}: {props[gate_name_key]}")
                else:
                    print(f"      ✗ Missing {gate_name_key}")
                
                if line_key in props:
                    print(f"      ✓ Found {line_key}: {props[line_key]}")
                else:
                    print(f"      ✗ Missing {line_key}")
                
                if house_key in props:
                    print(f"      ✓ Found {house_key}: {props[house_key]}")
                else:
                    print(f"      ✗ Missing {house_key}")
                
                if sign_key in props:
                    print(f"      ✓ Found {sign_key}: {props[sign_key]}")
                else:
                    print(f"      ✗ Missing {sign_key}")
        
        print()
    
    print(f"\n🔍 STEP 4: Summary")
    print("-" * 50)
    total_planet_positions = 0
    planets_with_gates = 0
    
    for feature in parans_features:
        props = feature.get("properties", {})
        source_lines = props.get("source_lines", [])
        
        if len(source_lines) >= 2:
            planet1 = source_lines[0].split("_")[0] if "_" in source_lines[0] else ""
            planet2 = source_lines[1].split("_")[0] if "_" in source_lines[1] else ""
            
            total_planet_positions += 2
            
            planet1_clean = planet1.replace(" CCG", "").replace(" Transit", "").replace(" HD", "")
            planet2_clean = planet2.replace(" CCG", "").replace(" Transit", "").replace(" HD", "")
            
            if f"{planet1_clean}_hd_gate" in props:
                planets_with_gates += 1
            if f"{planet2_clean}_hd_gate" in props:
                planets_with_gates += 1
    
    print(f"Total planet positions in parans: {total_planet_positions}")
    print(f"Planet positions with gate info: {planets_with_gates}")
    
    if planets_with_gates == 0:
        print("❌ PROBLEM: No gate information is making it to parans features!")
        print("   This suggests an issue in the astrocartography.py parans processing.")
    elif planets_with_gates < total_planet_positions:
        print("⚠️  PARTIAL: Some gate information is missing.")
    else:
        print("✅ SUCCESS: All planet positions have gate information.")

if __name__ == "__main__":
    debug_parans_gate_flow()

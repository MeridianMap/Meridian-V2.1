#!/usr/bin/env python3
"""Test script to check transit AC/DC lines generation"""

import requests
import json
import datetime

def test_transit_lines():
    # First get the natal chart data
    natal_url = "http://localhost:5000/api/calculate"
    astro_url = "http://localhost:5000/api/astrocartography"
    
    payload = {
        "name": "Test Transit",
        "birth_date": "1990-01-01",
        "birth_time": "12:00",
        "birth_city": "New York, NY", 
        "birth_state": "NY",
        "birth_country": "United States",
        "timezone": "America/New_York",
        "use_extended_planets": True
    }
    
    print("Step 1: Getting natal chart data...")
    natal_response = requests.post(natal_url, json=payload, timeout=30)
    
    if natal_response.status_code != 200:
        print(f"❌ Natal chart failed: {natal_response.status_code}")
        return
        
    natal_data = natal_response.json()
    print(f"✅ Got natal chart with {len(natal_data.get('planets', []))} planets")
    
    print("Step 2: Calculating transit astrocartography...")
    
    # Use current time for transits
    now = datetime.datetime.now()
    
    transit_payload = {
        "birth_date": now.strftime("%Y-%m-%d"),
        "birth_time": now.strftime("%H:%M"),
        "birth_city": "New York, NY",
        "birth_state": "NY", 
        "birth_country": "United States",
        "timezone": "America/New_York",
        "coordinates": natal_data.get("coordinates", {}),
        "planets": natal_data.get("planets", []),
        "utc_time": natal_data.get("utc_time", {}),
        "lots": natal_data.get("lots", []),
        # Transit-specific filtering
        "include_aspects": False,
        "include_fixed_stars": False,
        "include_hermetic_lots": False,
        "include_parans": True,
        "include_ac_dc": True,
        "include_ic_mc": True
    }
    
    print(f"Transit payload keys: {list(transit_payload.keys())}")
    
    try:
        response = requests.post(astro_url, json=transit_payload, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "features" in data:
                features = data["features"]
                print(f"✅ Got {len(features)} features")
                
                # Count different types of lines
                horizon_lines = []
                ac_dc_lines = []
                ic_mc_lines = []
                parans_lines = []
                
                for f in features:
                    props = f.get("properties", {})
                    line_type = props.get("line_type")
                    category = props.get("category")
                    
                    if line_type == "HORIZON":
                        horizon_lines.append(f)
                    elif line_type in ("AC", "DC"):
                        ac_dc_lines.append(f)
                    elif line_type in ("MC", "IC"):
                        ic_mc_lines.append(f)
                    elif category == "parans":
                        parans_lines.append(f)
                
                print(f"📊 Line breakdown:")
                print(f"  - Horizon lines: {len(horizon_lines)}")
                print(f"  - AC/DC lines: {len(ac_dc_lines)}")
                print(f"  - MC/IC lines: {len(ic_mc_lines)}")
                print(f"  - Parans: {len(parans_lines)}")
                
                # Check if horizon lines have ac_dc_indices
                for f in horizon_lines:
                    props = f.get("properties", {})
                    planet = props.get("planet")
                    ac_dc_indices = props.get("ac_dc_indices")
                    if ac_dc_indices:
                        print(f"✅ {planet} horizon line has ac_dc_indices: {ac_dc_indices}")
                    else:
                        print(f"❌ {planet} horizon line missing ac_dc_indices")
                
            else:
                print("❌ No features in response")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_transit_lines()

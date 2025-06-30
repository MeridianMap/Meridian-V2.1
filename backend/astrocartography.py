from typing import Dict, List
import swisseph as swe
import traceback

from hermetic_lots import calculate_hermetic_lots
from fixed_star import get_fixed_star_positions, FIXED_STARS
from line_parans import find_line_crossings_and_latitude_lines
from line_ac_dc import generate_horizon_lines
from line_ic_mc import calculate_mc_line, calculate_ic_line
from line_aspects import calculate_aspect_lines
from point_influence import calculate_point_influences
from ephemeris_utils import initialize_ephemeris, ensure_ephemeris_path
from humandesign_gates import get_gate_from_longitude, get_gate_line_from_longitude

import numpy as np

# Initialize Swiss Ephemeris
initialize_ephemeris()

# --- Hermetic Lot lines (MC/IC only) ---
def calculate_lot_lines(jd, lots):
    # Import here to avoid circular import
    from humandesign_gates import get_gate_from_longitude, get_gate_line_from_longitude
    
    features = []
    for lot in lots:
        pname = lot["name"]
        ra_lot = lot["longitude"]
        
        # MC
        mc_feature = calculate_mc_line(jd, ra_lot, pname)
        if mc_feature:
            mc_feature["properties"]["category"] = "hermetic_lot"
            mc_feature["properties"]["line_type"] = "MC"
            # Add house and sign information
            if lot.get("house"):
                mc_feature["properties"]["house"] = lot.get("house")
            if lot.get("sign"):
                mc_feature["properties"]["sign"] = lot.get("sign")
            # Add Human Design gate information
            if lot.get("longitude"):
                gate_info = get_gate_from_longitude(lot.get("longitude"))
                gate_line_info = get_gate_line_from_longitude(lot.get("longitude"))
                if gate_info:
                    mc_feature["properties"]["hd_gate"] = gate_info["gate"]
                    mc_feature["properties"]["hd_gate_name"] = gate_info["name"]
                if gate_line_info:
                    mc_feature["properties"]["hd_gate_line"] = gate_line_info["gate_line"]
                    mc_feature["properties"]["hd_line"] = gate_line_info["line"]
            features.append(mc_feature)
            
        # IC
        ic_feature = calculate_ic_line(jd, ra_lot, pname)
        if ic_feature:
            ic_feature["properties"]["category"] = "hermetic_lot"
            ic_feature["properties"]["line_type"] = "IC"
            # Add house and sign information
            if lot.get("house"):
                ic_feature["properties"]["house"] = lot.get("house")
            if lot.get("sign"):
                ic_feature["properties"]["sign"] = lot.get("sign")
            # Add Human Design gate information
            if lot.get("longitude"):
                gate_info = get_gate_from_longitude(lot.get("longitude"))
                gate_line_info = get_gate_line_from_longitude(lot.get("longitude"))
                if gate_info:
                    ic_feature["properties"]["hd_gate"] = gate_info["gate"]
                    ic_feature["properties"]["hd_gate_name"] = gate_info["name"]
                if gate_line_info:
                    ic_feature["properties"]["hd_gate_line"] = gate_line_info["gate_line"]
                    ic_feature["properties"]["hd_line"] = gate_line_info["line"]
            features.append(ic_feature)
    return features


def generate_all_astrocartography_features(chart_data: Dict, filter_options: Dict = None) -> List[Dict]:
    """
    Generate astrocartography features with optional filtering.
    
    Args:
        chart_data: Chart data containing planets, time, etc.
        filter_options: Dictionary with filtering options for transit mode
    """
    if filter_options is None:
        filter_options = {
            'include_aspects': True,
            'include_fixed_stars': True,
            'include_hermetic_lots': True,
            'include_parans': True,
            'include_ac_dc': True,
            'include_ic_mc': True
        }
    
    try:
        planets = chart_data.get("planets", [])
        utc = chart_data.get("utc_time", {})
        jd = utc.get("julian_day")
        houses = chart_data.get("houses", {})
        ascendant_long = houses.get("ascendant", {}).get("longitude")
        features = []        # Calculate Hermetic Lots if possible
        lots = []
        if "lots" in chart_data and chart_data["lots"]:
            lots = chart_data["lots"]  # Use lots with house/sign info from chart data
        elif ascendant_long is not None:
            # Fallback: calculate fresh lots (but won't have house/sign info)
            lots = calculate_hermetic_lots(chart_data)# --- Planet/asteroid/lot lines (Swiss Ephemeris powered) ---
        for planet in planets:
            pname = planet.get("name")
            pid = planet.get("id")
            body_type = planet.get("body_type", "planet")            # Skip nodes for CCG layers
            layer_type = filter_options.get("layer_type")
            if layer_type == "CCG" and pname in ["Lunar Node"]:
                continue
                
            # Check if this is a CCG, transit, or HD planet and append suffix to the name ONLY for overlay layers
            display_name = pname
            if layer_type == "CCG":
                display_name = f"{pname} CCG"
            elif layer_type == "transit":
                display_name = f"{pname} Transit"
            elif layer_type == "HD_DESIGN":
                display_name = f"{pname} HD"
                  # For CCG layers or planets/lots with pre-calculated RA, use those coordinates
            if (layer_type == "CCG" and "ra" in planet) or (planet.get("data_type") in ["progressed", "transit", "hd_design"] and "ra" in planet):
                ra_planet = planet.get("ra")
                print(f"[DEBUG] Using pre-calculated RA for {pname} ({planet.get('data_type', 'unknown')}): {ra_planet}")
            elif body_type == "lot":
                # Hermetic Lots: use ecliptic longitude as RA for angular lines
                ra_planet = planet.get("longitude")
            elif pname == "Lunar Node":
                # Lunar Node: use ecliptic longitude directly for RA (never call Swiss Ephemeris)
                ra_planet = planet.get("longitude")
                print(f"[DEBUG] Using ecliptic longitude as RA for Lunar Node: {ra_planet}")
            else:
                # Use Swiss Ephemeris for natal planets or fallback
                try:
                    ensure_ephemeris_path()
                    ppos, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
                    ra_planet = ppos[0]
                    print(f"[DEBUG] Calculated RA for {pname}: {ra_planet}")
                except Exception as e:
                    print(f"Swiss Ephemeris error for planet {pname}: {e}")
                    continue            # MC line (only if IC/MC lines are enabled)
            if filter_options.get('include_ic_mc', True):
                mc_feature = calculate_mc_line(jd, ra_planet, display_name)
                if mc_feature:
                    mc_feature["properties"]["category"] = body_type
                    mc_feature["properties"]["line_type"] = "MC"
                    mc_feature["properties"]["body"] = pname
                    mc_feature["properties"]["body_key"] = planet.get("id")
                    mc_feature["properties"]["data_type"] = planet.get("data_type")
                    mc_feature["properties"]["layer"] = layer_type or "natal"
                    # Add house and sign information
                    if planet.get("house"):
                        mc_feature["properties"]["house"] = planet.get("house")
                    if planet.get("sign"):
                        mc_feature["properties"]["sign"] = planet.get("sign")
                    # Add Human Design gate information
                    if planet.get("longitude"):
                        gate_info = get_gate_from_longitude(planet.get("longitude"))
                        gate_line_info = get_gate_line_from_longitude(planet.get("longitude"))
                        if gate_info:
                            mc_feature["properties"]["hd_gate"] = gate_info["gate"]
                            mc_feature["properties"]["hd_gate_name"] = gate_info["name"]
                        if gate_line_info:
                            mc_feature["properties"]["hd_gate_line"] = gate_line_info["gate_line"]
                            mc_feature["properties"]["hd_line"] = gate_line_info["line"]
                    features.append(mc_feature)            # IC line (only if IC/MC lines are enabled)
            if filter_options.get('include_ic_mc', True):
                ic_feature = calculate_ic_line(jd, ra_planet, display_name)
                if ic_feature:
                    ic_feature["properties"]["category"] = body_type
                    ic_feature["properties"]["line_type"] = "IC"
                    ic_feature["properties"]["body"] = pname
                    ic_feature["properties"]["body_key"] = planet.get("id")
                    ic_feature["properties"]["data_type"] = planet.get("data_type")
                    ic_feature["properties"]["layer"] = layer_type or "natal"
                    # Add house and sign information
                    if planet.get("house"):
                        ic_feature["properties"]["house"] = planet.get("house")
                    if planet.get("sign"):
                        ic_feature["properties"]["sign"] = planet.get("sign")
                    # Add Human Design gate information
                    if planet.get("longitude"):
                        gate_info = get_gate_from_longitude(planet.get("longitude"))
                        gate_line_info = get_gate_line_from_longitude(planet.get("longitude"))
                        if gate_info:
                            ic_feature["properties"]["hd_gate"] = gate_info["gate"]
                            ic_feature["properties"]["hd_gate_name"] = gate_info["name"]
                        if gate_line_info:
                            ic_feature["properties"]["hd_gate_line"] = gate_line_info["gate_line"]
                            ic_feature["properties"]["hd_line"] = gate_line_info["line"]
                    features.append(ic_feature)

        # --- AC/DC lines (spline-based, all planets, once per chart) ---
        if filter_options.get('include_ac_dc', True):
            # Use dense sampling for horizon lines
            acdc_settings = {"density": 300, "lat_steps": np.arange(-85, 85.01, 0.5)}
            acdc_segments_for_parans = []
            try:                # Filter chart data for CCG to exclude nodes
                filtered_chart_data = chart_data.copy() if chart_data else {}
                if layer_type in ["CCG", "HD_DESIGN"] and "planets" in filtered_chart_data:
                    filtered_planets = [p for p in filtered_chart_data["planets"] 
                                      if p.get("name") not in ["Lunar Node"]]
                    filtered_chart_data["planets"] = filtered_planets
                
                acdc_features = generate_horizon_lines(filtered_chart_data, settings=acdc_settings)
                for f in acdc_features:
                    f["properties"]["category"] = "planet"
                    # Always propagate id from the source planet/lot
                    # Try to get id from 'planet_id', 'body_key', or fallback to name
                    feature_id = (
                        f["properties"].get("planet_id")
                        or f["properties"].get("body_key")
                        or f["properties"].get("body")
                        or f["properties"].get("planet")
                        or ""
                    )
                    # Attach id to feature if not present
                    if not f["properties"].get("planet_id") and not f["properties"].get("body_key"):
                        # Try to find the matching object by name
                        match_obj = next((p for p in planets + lots if p.get("name") == f["properties"].get("planet") or p.get("name") == f["properties"].get("body")), None)
                        if match_obj and match_obj.get("id"):
                            f["properties"]["planet_id"] = match_obj["id"]
                            feature_id = match_obj["id"]
                    # Now match by id first, fallback to name
                    matching_obj = next((p for p in planets + lots if str(p.get("id")) == str(feature_id)), None)
                    if not matching_obj:
                        # Fallback to name if id not found
                        planet_name = (
                            f["properties"].get("planet")
                            or f["properties"].get("body")
                            or ""
                        ).replace(" CCG", "").replace(" Transit", "").replace(" HD", "")
                        matching_obj = next((p for p in planets + lots if p.get("name") == planet_name), None)
                    if matching_obj:
                        if matching_obj.get("house"):
                            f["properties"]["house"] = matching_obj.get("house")
                        if matching_obj.get("sign"):
                            f["properties"]["sign"] = matching_obj.get("sign")
                    
                    # Apply overlay naming if this is an overlay layer
                    if layer_type == "CCG":
                        planet_name = f["properties"].get("planet")
                        if planet_name and not planet_name.endswith(" CCG"):
                            f["properties"]["planet"] = f"{planet_name} CCG"
                    elif layer_type == "transit":
                        planet_name = f["properties"].get("planet")
                        if planet_name and not planet_name.endswith(" Transit"):
                            f["properties"]["planet"] = f"{planet_name} Transit"
                    elif layer_type == "HD_DESIGN":
                        planet_name = f["properties"].get("planet")
                        if planet_name and not planet_name.endswith(" HD"):
                            f["properties"]["planet"] = f"{planet_name} HD"
                    # Keep HORIZON features for display
                    features.append(f)
                    # Split HORIZON feature into AC and DC features for parans only
                    if f["properties"].get("line_type") == "HORIZON":
                        coords = f["geometry"]["coordinates"]
                        segs = f["properties"].get("segments", [])
                        planet = f["properties"].get("planet")                        # Handle both LineString and MultiLineString
                        if f["geometry"]["type"] == "LineString":
                            segments = [coords]
                        else:
                            segments = coords
                        for seg, seg_info in zip(segments, segs):
                            label = seg_info["label"]
                            start = seg_info["start"]
                            end = seg_info["end"]
                            seg_coords = seg[start:end+1]
                            acdc_feat = {
                                "type": "Feature",
                                "geometry": {"type": "LineString", "coordinates": seg_coords},
                                "properties": {
                                    "planet": planet,
                                    "category": "planet",
                                    "line_type": label,
                                    # Pass through house/sign info from parent feature
                                    "house": f["properties"].get("house"),
                                    "sign": f["properties"].get("sign"),
                                    # Pass through Human Design gate info from parent feature
                                    "hd_gate": f["properties"].get("hd_gate"),
                                    "hd_gate_name": f["properties"].get("hd_gate_name"),
                                    "hd_line": f["properties"].get("hd_line"),
                                    "hd_line_name": f["properties"].get("hd_line_name")
                                }
                            }
                            acdc_segments_for_parans.append(acdc_feat)
            except Exception as err:
                print(f"[ERROR] Horizon line generation error: {err}")
                import traceback
                traceback.print_exc()
        else:
            acdc_segments_for_parans = []        # --- Hermetic Lot lines (MC/IC only) ---
        if filter_options.get('include_hermetic_lots', True):
            for lot_feature in calculate_lot_lines(jd, lots):
                lot_feature["properties"]["category"] = "hermetic_lot"
                features.append(lot_feature)

        # --- Fixed Star points (Swiss Ephemeris powered) ---
        if filter_options.get('include_fixed_stars', True):
            fixed_stars_positions = get_fixed_star_positions(jd)
            chart_houses = chart_data.get("houses", {})
            # Get house cusps as a list of 12 longitudes (1-based keys)
            house_cusps = [chart_houses.get(f"house_{i+1}", {}).get("longitude") for i in range(12)]
            def get_sign_from_longitude(longitude):
                signs = [
                    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
                ]
                index = int(longitude // 30) % 12
                return signs[index]
            def get_house_from_longitude(longitude, house_cusps):
                for i in range(12):
                    start = house_cusps[i]
                    end = house_cusps[(i + 1) % 12]
                    if start is None or end is None:
                        continue
                    if start < end:
                        if start <= longitude < end:
                            return i + 1
                    else:
                        if longitude >= start or longitude < end:
                            return i + 1
                return None
            
            for star_pos in fixed_stars_positions:
                star_name = star_pos["name"]
                longitude = star_pos["longitude"]
                sign = get_sign_from_longitude(longitude)
                house = get_house_from_longitude(longitude, house_cusps) if all(h is not None for h in house_cusps) else None
                
                # Calculate Human Design gate information
                gate_info = get_gate_from_longitude(longitude)
                gate_line_info = get_gate_line_from_longitude(longitude)
                
                star_properties = {
                    "star": star_name,
                    "star_key": star_name,
                    "type": "fixed_star",
                    "category": "fixed_star",
                    "radius_miles": 50,
                    "magnitude": star_pos.get("magnitude"),
                    "sign": sign,
                }
                if house:
                    star_properties["house"] = house
                
                # Add Human Design gate information
                if gate_info:
                    star_properties["hd_gate"] = gate_info["gate"]
                    star_properties["hd_gate_name"] = gate_info["name"]
                if gate_line_info:
                    star_properties["hd_gate_line"] = gate_line_info["gate_line"]
                    star_properties["hd_line"] = gate_line_info["line"]
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [star_pos["longitude"], star_pos["latitude"]]
                    },
                    "properties": star_properties
                })

        # --- Aspect lines ---
        if filter_options.get('include_aspects', True):
            try:
                aspect_features = calculate_aspect_lines(chart_data)
                for af in aspect_features:
                    af["properties"]["category"] = "aspect"
                features.extend(aspect_features)
            except Exception as err:
                print(f"[ERROR] Aspect line generation error: {err}")
                import traceback
                traceback.print_exc()
        # --- Point influences (stub) ---
        point_influence_features = calculate_point_influences(chart_data)
        for pf in point_influence_features:
            pf["properties"]["category"] = "point_influence"
        features.extend(point_influence_features)        # --- Planetary line crossings (Parans) ---
        if filter_options.get('include_parans', True):
            try:
                # Only include major planets and Chiron for crossings
                allowed_crossing_bodies = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron"}
                aspect_lines_dict = {}
                planet_info_dict = {}  # Store house/sign info for parans
                
                # Use MC/IC from features, AC/DC from acdc_segments_for_parans
                for f in features + acdc_segments_for_parans:
                    if (
                        f["geometry"]["type"] == "LineString"
                        and f["properties"].get("category") == "planet"
                        and f["properties"].get("line_type") in ("AC", "DC", "MC", "IC")
                    ):
                        name = f["properties"].get("planet")
                        if name and any(body in name for body in allowed_crossing_bodies):
                            line_key = name + "_" + f["properties"].get("line_type", "")
                            aspect_lines_dict.setdefault(line_key, []).append(f["geometry"]["coordinates"])                            # Store planet house/sign info for parans
                            planet_base_name = name.replace(" CCG", "").replace(" Transit", "").replace(" HD", "")
                            if f["properties"].get("house") or f["properties"].get("sign") or f["properties"].get("hd_gate"):
                                planet_info_dict[planet_base_name] = {
                                    "house": f["properties"].get("house"),
                                    "sign": f["properties"].get("sign"),
                                    "hd_gate": f["properties"].get("hd_gate"),
                                    "hd_gate_name": f["properties"].get("hd_gate_name"),
                                    "hd_line": f["properties"].get("hd_line"),
                                    "hd_line_name": f["properties"].get("hd_line_name")
                                }                # Flatten coordinate lists for each line
                aspect_lines_dict = {k: [pt for seg in v for pt in seg] for k, v in aspect_lines_dict.items()}
                crossing_features = find_line_crossings_and_latitude_lines(aspect_lines_dict)
                
                for cf in crossing_features:
                    cf["properties"]["category"] = "parans"
                    
                    # Add house and sign info for the planets involved in the crossing
                    source_lines = cf["properties"].get("source_lines", [])
                    if len(source_lines) >= 2:
                        # Extract planet names from source lines (e.g., "Sun_AC" -> "Sun")
                        planet1 = source_lines[0].split("_")[0] if "_" in source_lines[0] else ""
                        planet2 = source_lines[1].split("_")[0] if "_" in source_lines[1] else ""
                        
                        # Clean planet names (remove suffixes)
                        planet1 = planet1.replace(" CCG", "").replace(" Transit", "").replace(" HD", "")
                        planet2 = planet2.replace(" CCG", "").replace(" Transit", "").replace(" HD", "")                        # Add house and sign info for both planets
                        if planet1 in planet_info_dict:
                            info = planet_info_dict[planet1]
                            if info.get("house"):
                                cf["properties"][f"{planet1}_house"] = info.get("house")
                            if info.get("sign"):
                                cf["properties"][f"{planet1}_sign"] = info.get("sign")
                            if info.get("hd_gate"):
                                cf["properties"][f"{planet1}_hd_gate"] = info.get("hd_gate")
                            if info.get("hd_gate_name"):
                                cf["properties"][f"{planet1}_hd_gate_name"] = info.get("hd_gate_name")
                            if info.get("hd_line"):
                                cf["properties"][f"{planet1}_hd_line"] = info.get("hd_line")
                            if info.get("hd_line_name"):
                                cf["properties"][f"{planet1}_hd_line_name"] = info.get("hd_line_name")
                        
                        if planet2 in planet_info_dict:
                            info = planet_info_dict[planet2]
                            if info.get("house"):
                                cf["properties"][f"{planet2}_house"] = info.get("house")
                            if info.get("sign"):
                                cf["properties"][f"{planet2}_sign"] = info.get("sign")
                            if info.get("hd_gate"):
                                cf["properties"][f"{planet2}_hd_gate"] = info.get("hd_gate")
                            if info.get("hd_gate_name"):
                                cf["properties"][f"{planet2}_hd_gate_name"] = info.get("hd_gate_name")
                            if info.get("hd_line"):
                                cf["properties"][f"{planet2}_hd_line"] = info.get("hd_line")
                            if info.get("hd_line_name"):
                                cf["properties"][f"{planet2}_hd_line_name"] = info.get("hd_line_name")
                
                features.extend(crossing_features)
            except Exception as err:
                print(f"[ERROR] Parans generation error: {err}")
                import traceback
                traceback.print_exc()          # --- Ensure all overlay features are labeled with their layer type ---
        layer_type = filter_options.get('layer_type')
        if layer_type in ['CCG', 'transit', 'HD_DESIGN']:
            for f in features:
                if 'properties' in f:
                    f['properties']['layer'] = layer_type
        
        # --- END: Force layer tag on all overlay features ---
        return features
    except Exception as e:
        print("Astrocartography backend error:", e)
        import traceback
        traceback.print_exc()
        return []

def calculate_astrocartography_lines_geojson(chart_data: Dict, filter_options: Dict = None) -> Dict:
    """
    Calculate astrocartography lines with optional filtering for transit mode.
    
    Args:
        chart_data: Chart data containing planets, time, etc.
        filter_options: Optional filtering for transit calculations
    """
    if filter_options is None:
        filter_options = {
            'include_aspects': True,
            'include_fixed_stars': True,
            'include_hermetic_lots': True,            'include_parans': True,
            'include_ac_dc': True,
            'include_ic_mc': True
        }
        
    features = generate_all_astrocartography_features(chart_data, filter_options)
    
    # Ensure all features have layer_type property set
    layer_type = filter_options.get('layer_type', 'natal')
    for feature in features:
        if 'layer_type' not in feature.get('properties', {}):
            feature['properties']['layer_type'] = layer_type
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

# PATCH: Allow running as script by fixing imports if needed
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    # Now relative imports will work

    import json, pathlib
    test_chart_path = pathlib.Path("debug_chart.json")
    if test_chart_path.exists():
        chart_data = json.loads(test_chart_path.read_text())
        geojson = calculate_astrocartography_lines_geojson(chart_data)
        ac_count = sum(1 for f in geojson["features"] if f["properties"].get("line_type") in ("ASC", "DSC"))
        print(f"✦ AC/DC features generated: {ac_count}")
        test_chart_path.with_suffix(".out.geojson").write_text(json.dumps(geojson, indent=2))
        print("Saved output GeoJSON → *.out.geojson")
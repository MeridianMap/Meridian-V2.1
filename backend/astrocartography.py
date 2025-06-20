from typing import Dict, List
import swisseph as swe
import traceback

# Import with proper backend paths
try:
    from backend.hermetic_lots import calculate_hermetic_lots
    from backend.fixed_star import get_fixed_star_positions, FIXED_STARS
    from backend.line_parans import find_line_crossings_and_latitude_lines
    from backend.line_ac_dc import generate_horizon_lines
    from backend.line_ic_mc import calculate_mc_line, calculate_ic_line
    from backend.line_aspects import calculate_aspect_lines
    from backend.point_influence import calculate_point_influences
    from backend.ephemeris_utils import initialize_ephemeris
except ImportError:
    # Fallback for when running from backend directory
    from hermetic_lots import calculate_hermetic_lots
    from fixed_star import get_fixed_star_positions, FIXED_STARS
    from line_parans import find_line_crossings_and_latitude_lines
    from line_ac_dc import generate_horizon_lines
    from line_ic_mc import calculate_mc_line, calculate_ic_line
    from line_aspects import calculate_aspect_lines
    from point_influence import calculate_point_influences
    from ephemeris_utils import initialize_ephemeris

import numpy as np

# Initialize Swiss Ephemeris
initialize_ephemeris()

# --- Hermetic Lot lines (MC/IC only) ---
def calculate_lot_lines(jd, lots):
    features = []
    for lot in lots:
        pname = lot["name"]
        ra_lot = lot["longitude"]
        # MC
        mc_feature = calculate_mc_line(jd, ra_lot, pname)
        if mc_feature:
            mc_feature["properties"]["category"] = "hermetic_lot"
            mc_feature["properties"]["line_type"] = "MC"
            features.append(mc_feature)
        # IC
        ic_feature = calculate_ic_line(jd, ra_lot, pname)
        if ic_feature:
            ic_feature["properties"]["category"] = "hermetic_lot"
            ic_feature["properties"]["line_type"] = "IC"
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
        features = []
        # Calculate Hermetic Lots if possible
        lots = []
        if "lots" in chart_data and chart_data["lots"]:
            lots = chart_data["lots"]
        elif ascendant_long is not None:
            lots = calculate_hermetic_lots(chart_data)        # --- Planet/asteroid/lot lines (Swiss Ephemeris powered) ---
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
                    ppos, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
                    ra_planet = ppos[0]
                    print(f"[DEBUG] Calculated RA for {pname}: {ra_planet}")
                except Exception as e:
                    print(f"Swiss Ephemeris error for planet {pname}: {e}")
                    continue
            # MC line (only if IC/MC lines are enabled)
            if filter_options.get('include_ic_mc', True):
                mc_feature = calculate_mc_line(jd, ra_planet, display_name)
                if mc_feature:
                    mc_feature["properties"]["category"] = body_type
                    mc_feature["properties"]["line_type"] = "MC"
                    mc_feature["properties"]["body"] = pname
                    mc_feature["properties"]["body_key"] = planet.get("id")
                    mc_feature["properties"]["data_type"] = planet.get("data_type")
                    mc_feature["properties"]["layer"] = layer_type or "natal"
                    features.append(mc_feature)
            # IC line (only if IC/MC lines are enabled)
            if filter_options.get('include_ic_mc', True):
                ic_feature = calculate_ic_line(jd, ra_planet, display_name)
                if ic_feature:
                    ic_feature["properties"]["category"] = body_type
                    ic_feature["properties"]["line_type"] = "IC"
                    ic_feature["properties"]["body"] = pname
                    ic_feature["properties"]["body_key"] = planet.get("id")
                    ic_feature["properties"]["data_type"] = planet.get("data_type")
                    ic_feature["properties"]["layer"] = layer_type or "natal"
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
                    print(f"[DEBUG] Filtered planets for {layer_type} AC/DC: {[p.get('name') for p in filtered_planets]}")
                
                acdc_features = generate_horizon_lines(filtered_chart_data, settings=acdc_settings)
                for f in acdc_features:
                    f["properties"]["category"] = "planet"                    # Apply overlay naming if this is an overlay layer
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
                        planet = f["properties"].get("planet")
                        # Handle both LineString and MultiLineString
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
                                    "line_type": label
                                }
                            }
                            acdc_segments_for_parans.append(acdc_feat)
            except Exception as err:
                print(f"[ERROR] Horizon line generation error: {err}")
                import traceback
                traceback.print_exc()
        else:
            acdc_segments_for_parans = []# --- Hermetic Lot lines (MC/IC only) ---
        if filter_options.get('include_hermetic_lots', True):
            for lot_feature in calculate_lot_lines(jd, lots):
                lot_feature["properties"]["category"] = "hermetic_lot"
                features.append(lot_feature)        # --- Fixed Star points (Swiss Ephemeris powered) ---
        if filter_options.get('include_fixed_stars', True):
            fixed_stars = get_fixed_star_positions(jd)
            for star in fixed_stars:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [star["longitude"], star["latitude"]]
                    },
                    "properties": {
                        "star": star["name"],
                        "type": "fixed_star",
                        "category": "fixed_star",
                        "radius_miles": 50,
                        "magnitude": star.get("magnitude")
                    }
                })        # --- Aspect lines ---
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
                # Use MC/IC from features, AC/DC from acdc_segments_for_parans
                for f in features + acdc_segments_for_parans:
                    if (
                        f["geometry"]["type"] == "LineString"
                        and f["properties"].get("category") == "planet"
                        and f["properties"].get("line_type") in ("AC", "DC", "MC", "IC")
                    ):
                        name = f["properties"].get("planet")
                        if name and any(body in name for body in allowed_crossing_bodies):
                            aspect_lines_dict.setdefault(name + "_" + f["properties"].get("line_type", ""), []).append(f["geometry"]["coordinates"])
                # Flatten coordinate lists for each line
                aspect_lines_dict = {k: [pt for seg in v for pt in seg] for k, v in aspect_lines_dict.items()}
                crossing_features = find_line_crossings_and_latitude_lines(aspect_lines_dict)
                for cf in crossing_features:
                    cf["properties"]["category"] = "parans"
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
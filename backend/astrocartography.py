from typing import Dict, List
import swisseph as swe
import traceback
from hermetic_lots import calculate_hermetic_lots
from fixed_star import get_fixed_star_positions
from parans import calculate_parans
from fixed_star import FIXED_STARS
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


def generate_all_astrocartography_features(chart_data: Dict) -> List[Dict]:
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
            lots = calculate_hermetic_lots(chart_data)
        # --- Planet/asteroid lines (Swiss Ephemeris powered) ---
        for planet in planets:
            pname = planet.get("name")
            pid = planet.get("id")
            try:
                ppos, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
                ra_planet = ppos[0]
            except Exception as e:
                print(f"Swiss Ephemeris error for planet {pname}: {e}")
                continue
            # MC
            mc_feature = calculate_mc_line(jd, ra_planet, pname)
            if mc_feature:
                mc_feature["properties"]["category"] = "planet"
                mc_feature["properties"]["line_type"] = "MC"
                features.append(mc_feature)
            # IC
            ic_feature = calculate_ic_line(jd, ra_planet, pname)
            if ic_feature:
                ic_feature["properties"]["category"] = "planet"
                ic_feature["properties"]["line_type"] = "IC"
                features.append(ic_feature)
        # --- South Node MC/IC lines (calculated from North Node) ---
        for planet in planets:
            if planet.get("name") == "North Node":
                ra_north = None
                try:
                    ppos, _ = swe.calc_ut(jd, planet.get("id"), swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
                    ra_north = ppos[0]
                except Exception:
                    continue
                if ra_north is not None:
                    # Calculate MC longitude for North Node
                    gmst = swe.sidtime(jd) * 15.0
                    mc_long_north = (ra_north - gmst) % 360.0
                    if mc_long_north > 180:
                        mc_long_north -= 360
                    # Calculate MC longitude for South Node (opposite)
                    mc_long_south = (mc_long_north + 180.0)
                    if mc_long_south > 180:
                        mc_long_south -= 360
                    # MC line for South Node
                    mc_feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[mc_long_south, -85], [mc_long_south, 85]]
                        },
                        "properties": {
                            "planet": "South Node",
                            "planet_id": 100,  # Assign unique ID for South Node
                            "category": "planet",
                            "line_type": "MC"
                        }
                    }
                    features.append(mc_feature)
                    # IC line for South Node (opposite MC)
                    ic_long_south = (mc_long_south + 180.0)
                    if ic_long_south > 180:
                        ic_long_south -= 360
                    ic_feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[ic_long_south, -85], [ic_long_south, 85]]
                        },
                        "properties": {
                            "planet": "South Node",
                            "planet_id": 100,  # Assign unique ID for South Node
                            "category": "planet",
                            "line_type": "IC"
                        }
                    }
                    features.append(ic_feature)
        # --- AC/DC lines (spline-based, all planets, once per chart) ---
        # Use dense sampling for horizon lines
        acdc_settings = {"density": 300, "lat_steps": np.arange(-85, 85.01, 0.5)}
        try:
            acdc_features = generate_horizon_lines(chart_data, settings=acdc_settings)
            for f in acdc_features:
                f["properties"]["category"] = "planet"
            features.extend(acdc_features)
        except Exception as err:
            print(f"Horizon line generation error: {err}")
        # --- Hermetic Lot lines (MC/IC only) ---
        for lot_feature in calculate_lot_lines(jd, lots):
            lot_feature["properties"]["category"] = "hermetic_lot"
            features.append(lot_feature)
        # --- Fixed Star points (Swiss Ephemeris powered) ---
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
            })
        # --- Parans calculation (planet + fixed star) ---
        VALID_PLANET_IDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 15]  # Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Chiron
        parans_features = []
        if planets and fixed_stars:
            lat = chart_data.get("coordinates", {}).get("latitude")
            lon = chart_data.get("coordinates", {}).get("longitude")
            for planet in planets:
                pid = planet.get("id")
                if pid not in VALID_PLANET_IDS:
                    continue
                parans = calculate_parans(jd, lat, lon, pid)
                for paran in parans:
                    paran["properties"]["planet"] = planet["name"]
                    paran["properties"]["category"] = "aspect"
                    parans_features.append(paran)
        features.extend(parans_features)
        # --- Aspect lines (stub) ---
        aspect_features = calculate_aspect_lines(chart_data)
        for af in aspect_features:
            af["properties"]["category"] = "aspect"
        features.extend(aspect_features)
        # --- Point influences (stub) ---
        point_influence_features = calculate_point_influences(chart_data)
        for pf in point_influence_features:
            pf["properties"]["category"] = "point_influence"
        features.extend(point_influence_features)
        return features
    except Exception as e:
        print("Astrocartography backend error:", e)
        traceback.print_exc()
        return []

def calculate_astrocartography_lines_geojson(chart_data: Dict) -> Dict:
    return {
        "type": "FeatureCollection",
        "features": generate_all_astrocartography_features(chart_data)
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
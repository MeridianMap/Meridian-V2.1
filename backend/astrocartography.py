import swisseph as swe
from typing import Dict
import math
import traceback
from backend.hermetic_lots import calculate_hermetic_lots
from backend.fixed_star import get_fixed_star_positions
from backend.parans import calculate_parans
from backend.fixed_star import FIXED_STARS

def bisect_longitude(func, lon_min, lon_max, tol=1e-3, max_iter=40):
    a, b = lon_min, lon_max
    fa, fb = func(a), func(b)
    if fa * fb > 0:
        return None  # No root in interval
    for _ in range(max_iter):
        c = (a + b) / 2.0
        fc = func(c)
        if abs(fc) < tol:
            return c
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
    return (a + b) / 2.0

def calculate_mc_line(jd, ra_planet, pname):
    # MC: longitude where the planet is on the local meridian
    gmst = swe.sidtime(jd) * 15.0  # in degrees
    mc_long = (ra_planet - gmst) % 360.0
    if mc_long > 180:
        mc_long -= 360
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[mc_long, -85], [mc_long, 85]]
        },
        "properties": {
            "planet": pname,
            "line_type": "MC"
        }
    }

def calculate_ic_line(jd, ra_planet, pname):
    # IC: longitude opposite the MC (MC ± 180°)
    gmst = swe.sidtime(jd) * 15.0  # in degrees
    mc_long = (ra_planet - gmst) % 360.0
    ic_long = (mc_long + 180.0) % 360.0
    if ic_long > 180:
        ic_long -= 360
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[ic_long, -85], [ic_long, 85]]
        },
        "properties": {
            "planet": pname,
            "line_type": "IC"
        }
    }

def calculate_ac_line(jd, pid, pname, lat_steps=None):
    """
    Calculate the AC (Ascendant) line for a planet as a curve (altitude=0, rising) across latitudes.
    Returns a GeoJSON Feature or None.
    """
    if lat_steps is None:
        lat_steps = list(range(-85, 86, 2))
    jd_int = int(jd)
    ut = (jd - jd_int) * 24.0  # UT in hours for this JD
    features = []
    roots_by_lat = []
    for lat in lat_steps:
        try:
            roots = []
            def alt_func(lon):
                geopos = [float(lon), float(lat), 0.0]
                xx, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH)
                planet_pos = [float(xx[0]), float(xx[1]), float(xx[2])]
                print(f"DEBUG: geopos={geopos}, planet_pos={planet_pos}, types: {[type(x) for x in geopos]}, {[type(x) for x in planet_pos]}")
                azalt = swe.azalt(ut, swe.FLG_SWIEPH, geopos, planet_pos)
                alt = azalt[1][1]
                return alt  # For AC, we want where altitude crosses 0 (rising)
            for base in range(-180, 180, 1):
                root = bisect_longitude(alt_func, base, base + 1)
                if root is not None:
                    if not roots or abs(root - roots[-1]) > 0.5:
                        roots.append(root)
            roots_by_lat.append(roots)
        except Exception as e:
            print(f"Error for {pname} AC at lat {lat}: {e}")
            roots_by_lat.append([])
            continue
    max_roots = max((len(r) for r in roots_by_lat), default=0)
    for root_idx in range(max_roots):
        line_coords = []
        for lat_idx, lat in enumerate(lat_steps):
            roots = roots_by_lat[lat_idx]
            if len(roots) > root_idx:
                root = roots[root_idx]
                if root > 180: root -= 360
                if root < -180: root += 360
                line_coords.append([root, lat])
        if len(line_coords) > 3:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": line_coords
                },
                "properties": {
                    "planet": pname,
                    "line_type": "ASC"
                }
            })
    return features

def calculate_lot_lines(jd, lots):
    """
    For each Hermetic Lot, generate MC and IC lines using the lot's longitude as RA.
    Returns a list of GeoJSON features.
    """
    features = []
    for lot in lots:
        pname = lot["name"]
        ra_lot = lot["longitude"]
        # MC
        mc_feature = calculate_mc_line(jd, ra_lot, pname)
        if mc_feature:
            features.append(mc_feature)
        # IC
        ic_feature = calculate_ic_line(jd, ra_lot, pname)
        if ic_feature:
            features.append(ic_feature)
    return features

def calculate_astrocartography_lines_geojson(chart_data: Dict) -> Dict:
    try:
        planets = chart_data.get("planets", [])
        utc = chart_data.get("utc_time", {})
        jd = utc.get("julian_day")
        houses = chart_data.get("houses", {})
        ascendant_long = houses.get("ascendant", {}).get("longitude")
        features = []
        lat_steps = list(range(-85, 86, 2))
        # Calculate Hermetic Lots if possible
        lots = []
        # Try to get lots from chart_data if already present, else calculate
        if "lots" in chart_data and chart_data["lots"]:
            lots = chart_data["lots"]
        elif ascendant_long is not None:
            lots = calculate_hermetic_lots(planets, ascendant_long)
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
                features.append(mc_feature)
            # IC
            ic_feature = calculate_ic_line(jd, ra_planet, pname)
            if ic_feature:
                features.append(ic_feature)
            # AC
            ac_features = calculate_ac_line(jd, pid, pname, lat_steps)
            if ac_features:
                features.extend(ac_features)
            # South Node lines logic remains unchanged
            if pname == "North Node":
                south_node_ra = (ra_planet + 180) % 360
                south_node_name = "South Node"
                mc_feature = calculate_mc_line(jd, south_node_ra, south_node_name)
                if mc_feature:
                    features.append(mc_feature)
                ic_feature = calculate_ic_line(jd, south_node_ra, south_node_name)
                if ic_feature:
                    features.append(ic_feature)
                ac_features = calculate_ac_line(jd, pid, south_node_name, lat_steps)
                if ac_features:
                    features.extend(ac_features)
        # --- Hermetic Lot lines (MC/IC only) ---
        features.extend(calculate_lot_lines(jd, lots))
        # --- Fixed Star points (Swiss Ephemeris powered) ---
        fixed_stars = get_fixed_star_positions(jd)
        for star in fixed_stars:
            # For map display: use both longitude and latitude from Swiss Ephemeris
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [star["longitude"], star["latitude"]]  # Use both lon, lat
                },
                "properties": {
                    "star": star["name"],
                    "type": "fixed_star",
                    "radius_miles": 50,
                    "magnitude": star.get("magnitude")
                }
            })
        # --- Parans calculation (planet + fixed star) ---
        # Only use valid Swiss Ephemeris planet IDs for parans
        VALID_PLANET_IDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 15]  # Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Chiron
        parans_features = []
        if planets and fixed_stars:
            lat = chart_data.get("coordinates", {}).get("latitude")
            lon = chart_data.get("coordinates", {}).get("longitude")
            for planet in planets:
                pid = planet.get("id")
                if pid not in VALID_PLANET_IDS:
                    continue  # Skip invalid IDs
                parans = calculate_parans(jd, lat, lon, pid)
                for paran in parans:
                    paran["properties"]["planet"] = planet["name"]  # Optionally add planet name
                    parans_features.append(paran)
        features.extend(parans_features)
        return {
            "type": "FeatureCollection",
            "features": features
        }
    except Exception as e:
        print("Astrocartography backend error:", e)
        traceback.print_exc()
        return {"error": f"Astrocartography calculation failed: {e}"}
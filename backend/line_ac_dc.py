"""
Spline-based horizon line generator for astrocartography.

API:
- generate_horizon_lines(chart_data, settings=None) -> List[Dict]:
    Returns GeoJSON features for horizon lines for every planet in chart_data["planets"].
    Spline interpolation is used for smooth animation-ready curves.

Note:
- Output longitudes are geographic and already wrapped to [–180°, 180°].
- Each horizon line is a single continuous LineString, with 'ac_dc_indices' property marking the join.
"""
import sys
import os
if __name__ != "__main__":
    # For test context: allow import from parent directory
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from backend.ephemeris_utils import initialize_ephemeris
    from backend.spline_utils import parametric_spline
except ImportError:
    from ephemeris_utils import initialize_ephemeris
    from spline_utils import parametric_spline

initialize_ephemeris()

import swisseph as swe
from typing import List, Dict
import numpy as np

def split_dateline(seq, max_jump=45):
    """Split a lon/lat sequence wherever |Δlon| > 180°. Filter out segments with any |Δlon| > max_jump (default 45°)."""
    segments, seg = [], [seq[0]]
    for (lon, lat) in seq[1:]:
        if abs(lon - seg[-1][0]) > 180:
            # Before appending, filter out zigzag segments
            if all(abs(a[0] - b[0]) <= max_jump for a, b in zip(seg, seg[1:])):
                segments.append(seg)
            seg = []
        seg.append((lon, lat))
    if all(abs(a[0] - b[0]) <= max_jump for a, b in zip(seg, seg[1:])):
        segments.append(seg)
    return segments

def generate_horizon_line(chart, planet, lat_steps, density=400):
    """
    Returns a GeoJSON Feature for the planet’s horizon curve.
    properties:
        'planet'   – planet name
        'ac_dc_indices' – dict with 'ac_end' and 'dc_start' indices for AC/DC join
    """
    delta = chart['dec'][planet]         # planet declination deg
    if abs(delta) > 90:
        import warnings
        warnings.warn(f"[WARN] Skipping {planet}: |dec| > 90 (got {delta})")
        print(f"[WARN] Skipping {planet}: |dec| > 90 (got {delta})")
        return None
    alpha = chart['ra_deg'][planet]      # RA deg
    gst   = chart['gst_deg']             # Greenwich sidereal time deg

    # Latitude grid for visible horizon
    phi = np.radians(lat_steps)
    cosH = -np.tan(phi) * np.tan(np.radians(delta))
    vis = np.abs(cosH) <= 1
    if not np.any(vis):
        print(f"[WARN] Skipping {planet}: horizon not visible at any latitude")
        return None
    lat_vis = lat_steps[vis]
    lat_vis_sorted = np.sort(lat_vis)
    phi_vis = np.radians(lat_vis_sorted)
    H0 = np.arccos(np.clip(-np.tan(phi_vis) * np.tan(np.radians(delta)), -1, 1))  # rad
    # Compute longitudes for rise and set on the same sorted lat array
    lon_rise = ((alpha - np.degrees(H0)) - gst + 540) % 360 - 180
    lon_set  = ((alpha + np.degrees(H0)) - gst + 540) % 360 - 180
    # Build a single ordered path: AC (south→north), DC (north→south)
    pts_ac = list(zip(lon_rise, lat_vis_sorted))
    pts_dc = list(zip(lon_set[::-1], lat_vis_sorted[::-1]))
    # Drop the duplicate pole point
    pts = pts_ac + pts_dc[1:]
    lons, lats = map(np.array, zip(*pts))
    # Spline both halves together
    lon_smooth, lat_smooth = parametric_spline(lons, lats, density)
    # Already wrapped to [-180,180] by parametric_spline
    coords = list(zip(lon_smooth, lat_smooth))
    # Dateline-safe segmentation
    segments = split_dateline(coords)
    # Safety check
    assert all(abs(a[0]-b[0]) <= 180 for seg in segments for a,b in zip(seg, seg[1:])), "Dateline split failed"
    # AC/DC indices for segment labeling
    ac_end = len(pts_ac) - 1
    dc_start = ac_end + 1
    # Segment labeling (compact)
    segs = [
        {"label": "AC", "start": 0, "end": ac_end},
        {"label": "DC", "start": dc_start, "end": len(coords)-1}
    ]    # GeoJSON output
    if len(segments) == 1:
        geometry = {"type": "LineString", "coordinates": segments[0]}
    else:
        geometry = {"type": "MultiLineString", "coordinates": segments}
    
    feat = {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "planet": planet,
            "line_type": "HORIZON",
            "segments": segs,
            "ac_dc_indices": {
                "ac_end": ac_end,
                "dc_start": dc_start
            }
        },
    }
    return feat

def generate_horizon_lines(chart_data, settings=None) -> list:
    """
    Generate smooth horizon lines for all planets in chart_data.
    Returns a list of GeoJSON features (one per planet).
    """
    features = []
    if not chart_data or "planets" not in chart_data or "utc_time" not in chart_data:
        return features
    jd = chart_data["utc_time"].get("julian_day")
    if jd is None:
        return features
    density = settings.get("density", 400) if settings else 400
    lat_steps = settings.get("lat_steps", np.linspace(-89, 89, 356)) if settings else np.linspace(-89, 89, 356)
    lat_steps = np.asarray(lat_steps)
    swe_id_map = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Uranus": swe.URANUS,
        "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO,
        "North Node": swe.MEAN_NODE,
        "South Node": swe.MEAN_NODE,
        "Ceres": swe.AST_OFFSET + 1,
        "Pallas Athena": swe.AST_OFFSET + 2,
        "Juno": swe.AST_OFFSET + 3,
        "Vesta": swe.AST_OFFSET + 4,
        "Chiron": swe.CHIRON,
        "Pholus": swe.PHOLUS,
        "Black Moon Lilith": swe.MEAN_APOG,
    }
    # Precompute sidereal time and planet RA/Dec
    gst = swe.sidtime(jd) * 15.0  # GST in degrees
    ra_deg = {}
    dec = {}
    for planet in chart_data["planets"]:
        pname = planet.get("name")
        if pname is not None:
            pname = pname.strip()
        pid = swe_id_map.get(pname)
        print(f"[DEBUG] Processing planet: '{pname}' (ID: {pid})")
        if pid is None:
            print(f"[WARN] Skipping planet '{pname}': not in swe_id_map")
            continue
        ppos, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
        ra_deg[pname] = ppos[0]
        dec[pname] = ppos[1]
    chart = {"ra_deg": ra_deg, "dec": dec, "gst_deg": gst}
    for pname in ra_deg:
        feat = generate_horizon_line(chart, pname, lat_steps, density)
        if feat is not None:
            features.append(feat)
    print(f"Generated {len(features)} horizon features: {[f['properties']['planet'] for f in features]}")
    return features

if __name__ == "__main__":
    import os, json
    debug_path = os.path.join(os.path.dirname(__file__), "debug_chart.json")
    if os.path.exists(debug_path):
        with open(debug_path, "r") as f:
            chart_data = json.load(f)
        feats = generate_horizon_lines(chart_data)
        print(f"[DEBUG] Horizon features generated: {len(feats)}")
        for feat in feats:
            pname = feat["properties"].get("planet")
            ltype = feat["properties"].get("line_type")
            if ltype == "HORIZON":
                coords = feat["geometry"]["coordinates"]
                ac_dc = feat["properties"].get("ac_dc_indices", {})
                ac_end = ac_dc.get("ac_end")
                dc_start = ac_dc.get("dc_start")
                print(f"{pname} horizon: {len(coords)} points, AC ends at {ac_end}, DC starts at {dc_start}")
                lat_s = np.array([c[1] for c in coords])
                if not np.all(np.diff(lat_s[:ac_end]) > 0):
                    print(f"[WARN] AC segment not strictly increasing in latitude for {pname}")
                if not np.all(np.diff(lat_s[dc_start:]) < 0):
                    print(f"[WARN] DC segment not strictly decreasing in latitude for {pname}")
                if len(coords) <= 200:
                    print(f"[WARN] Too few points for {pname} horizon!")
    else:
        print("[DEBUG] debug_chart.json not found!")

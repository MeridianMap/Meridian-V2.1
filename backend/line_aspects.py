"""
Aspect lines (sextile, square, trine) to MC and ASC for all planets.
Follows code style and error handling of line_ac_dc.py.
"""
import sys
import os
if __name__ != "__main__":
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from backend.ephemeris_utils import initialize_ephemeris
    from backend.spline_utils import parametric_spline
    from backend.line_ac_dc import split_dateline
except ImportError:
    from ephemeris_utils import initialize_ephemeris
    from spline_utils import parametric_spline
    from line_ac_dc import split_dateline

initialize_ephemeris()

import swisseph as swe
import numpy as np

# --- Midheaven helpers --------------------------------------------
def get_true_obliquity(jd_tt):
    """
    Get the true obliquity of the ecliptic for the given Julian day (TT).
    Uses Swiss Ephemeris if available, otherwise falls back to mean obliquity.
    Returns obliquity in radians.
    """
    try:
        # Try to use Swiss Ephemeris nutation function if available
        # swe.nutation returns nutation in longitude and obliquity (arcseconds)
        dpsi, deps = swe.nutation(jd_tt)
        # Mean obliquity (arcsec)
        T = (jd_tt - 2451545.0) / 36525.0
        mean_seconds = 84381.406 \
            - 46.836769 * T \
            - 0.0001831 * T**2 \
            + 0.00200340 * T**3 \
            - 0.000000576 * T**4 \
            - 0.0000000434 * T**5
        # True obliquity = mean + nutation in obliquity
        true_seconds = mean_seconds + deps
        return np.deg2rad(true_seconds / 3600.0)
    except Exception as e:
        # Fallback to mean obliquity
        T = (jd_tt - 2451545.0) / 36525.0
        seconds = 84381.406 \
            - 46.836769 * T \
            - 0.0001831 * T**2 \
            + 0.00200340 * T**3 \
            - 0.000000576 * T**4 \
            - 0.0000000434 * T**5
        return np.deg2rad(seconds / 3600.0)

_OBLIQ = np.deg2rad(23.4392911)          # mean obliquity J2000

def ecl_lon_of_mc(gst_deg, geo_lon_deg, obliq):
    """
    Ecliptic longitude (λ_MC) of the local meridian, given
    Greenwich sidereal time gst_deg (°), site longitude geo_lon_deg (° E),
    and true obliquity (radians).
    Formula:  tan λ = tan θ ⋅ cos ε , where θ = LST = gst + λ_geo.
    """
    lst = np.deg2rad((gst_deg + geo_lon_deg) % 360)
    return np.rad2deg(np.arctan2(np.sin(lst) * np.cos(obliq),
                                 np.cos(lst))) % 360

def geo_lon_for_mc(target_ecl_lon, gst_deg, obliq):
    """
    Geographic longitude (° E, range –180…180) whose Midheaven’s
    ecliptic longitude equals target_ecl_lon (°), given GST and obliquity.
    Inverse of the above relation:  tan θ = cos ε ⋅ tan λ .
    """
    lam = np.deg2rad(target_ecl_lon)
    lst_deg = np.rad2deg(np.arctan2(np.cos(obliq) * np.sin(lam),
                                    np.cos(lam))) % 360
    return ((lst_deg - gst_deg + 540) % 360) - 180
# ------------------------------------------------------------------

ASPECT_ANGLES = [60, 90, 120]  # sextile, square, trine
ASPECT_LABELS = {60: 'sextile', 90: 'square', 120: 'trine'}

# Helper: get planet RA (deg, equatorial) and ecliptic longitude (deg)
def _get_planet_positions(chart_data, jd):
    swe_id_map = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
        "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO,
        "Lunar Node": swe.MEAN_NODE, "Ceres": swe.AST_OFFSET + 1, "Pallas Athena": swe.AST_OFFSET + 2,
        "Juno": swe.AST_OFFSET + 3, "Vesta": swe.AST_OFFSET + 4, "Chiron": swe.CHIRON, "Pholus": swe.PHOLUS, "Black Moon Lilith": swe.MEAN_APOG,
    }
    positions = {}
    for planet in chart_data["planets"]:
        pname = planet.get("name", "").strip()
        pid = swe_id_map.get(pname)
        if pid is None:
            continue
        # RA (equatorial)
        flags = swe.FLG_SWIEPH | swe.FLG_EQUATORIAL
        ppos_eq, _ = swe.calc_ut(jd, pid, flags)
        ra_deg = ppos_eq[0]        # Ecliptic longitude
        ppos_ecl, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH)
        ecl_lon = ppos_ecl[0]
        # Note: Lunar Node uses direct ecliptic longitude (no modification needed)
        positions[pname] = {"ra": ra_deg, "ecl_lon": ecl_lon}
    return positions

def _normalize_lon(lon):
    lon = (lon + 540) % 360 - 180
    return lon

def _aspect_label(planet, angle, to):
    return f"{planet} {ASPECT_LABELS[abs(angle)]} {to}"

def calculate_aspect_lines(chart_data, debug=False):
    """
    Returns GeoJSON features for sextile, square, trine aspect lines to MC and ASC for all planets.
    properties: { 'planet', 'line_type': 'ASPECT', 'angle': Δ, 'to': 'MC'|'ASC', 'label': ... }
    """
    features = []
    if not chart_data or "planets" not in chart_data or "utc_time" not in chart_data:
        if debug:
            print("[DEBUG] Missing chart_data, planets, or utc_time.")
        return features
    jd = chart_data["utc_time"].get("julian_day")
    if jd is None:
        if debug:
            print("[DEBUG] Missing julian_day in chart_data['utc_time'].")
        return features
    try:
        planet_pos = _get_planet_positions(chart_data, jd)
        # Use TT for sidereal time to match astro.com and avoid small offset
        jd_ut = jd
        delta_t = swe.deltat(jd_ut)
        jd_tt = jd_ut + delta_t / 86400.0
        
        # Get true obliquity for this date
        obliq = get_true_obliquity(jd_tt)
        # MC aspect lines (planet ± 60°, 90°, 120° to the Midheaven)
        # Use sidereal time based on UT, not TT, per Swiss Ephemeris docs and astro.com
        gst_deg = swe.sidtime(jd_ut) * 15.0      # GST in UT hours → degrees

        mc_count = 0
        for name, pos in planet_pos.items():
            plon = pos["ecl_lon"]                   # ecliptic longitude
            for delta in ASPECT_ANGLES + [-a for a in ASPECT_ANGLES]:
                target = (plon - delta) % 360
                lon_geo = geo_lon_for_mc(target, gst_deg, obliq)

                # draw full meridian
                coords = [[lon_geo, -89.9], [lon_geo, 89.9]]
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": {
                        "planet": name,
                        "line_type": "ASPECT",
                        "angle": abs(delta),
                        "to": "MC",
                        "label": _aspect_label(name, delta, "MC")
                    },
                })
                mc_count += 1
        if debug:
            print(f"[DEBUG] MC aspect lines generated: {mc_count}")
        # ------------------------------------------------------------------        # --- ASC aspect lines ---
        # Use coarser latitude steps for better performance and stability
        lat_steps = np.arange(-85, 85.1, 0.5)  # 0.5° steps for better performance
        asc_count = 0
        for pname, pos in planet_pos.items():
            planet_ecl_lon = pos["ecl_lon"]
            for delta in ASPECT_ANGLES + [-a for a in ASPECT_ANGLES]:
                target_asc = (planet_ecl_lon - delta) % 360
                
                # Generate aspect line using simplified approach
                feat = _generate_asc_aspect_line(pname, target_asc, delta, jd_tt, lat_steps, debug)
                if feat is not None:
                    features.append(feat)
                    asc_count += 1
                    if debug:
                        coords_count = (len(feat["geometry"]["coordinates"]) 
                                      if feat["geometry"]["type"] == "LineString" 
                                      else sum(len(seg) for seg in feat["geometry"]["coordinates"]))
                        print(f"[DEBUG] ASC {pname} {ASPECT_LABELS[abs(delta)]} generated with {coords_count} points")
                elif debug:
                    print(f"[WARN] ASC aspect: {pname} {ASPECT_LABELS[abs(delta)]} failed to generate")
        if debug:
            print(f"[DEBUG] ASC aspect lines generated: {asc_count}")
            print(f"[DEBUG] Total features generated: {len(features)}")
    except Exception as e:
        print(f"[ERR] Aspect line generation failed: {e}")
    return features

def _wrap_longitude(lon):
    """
    Wrap longitude to [-180, 180] range using the same formula as horizon lines.
    This ensures consistent wrapping behavior across all line types.
    """
    return ((lon + 180) % 360) - 180

def _generate_asc_aspect_line(planet_name, target_asc_ecl_lon, delta_angle, jd_tt, lat_steps, debug=False):
    """
    Generate a single ASC aspect line using the proven approach from line_ac_dc.py.
    Returns a GeoJSON Feature or None if generation fails.
    
    Args:
        planet_name: Name of the planet
        target_asc_ecl_lon: Target ecliptic longitude for the ASC aspect (degrees)
        delta_angle: Aspect angle (+/-60, +/-90, +/-120)
        jd_tt: Julian day in TT
        lat_steps: Array of latitude values to compute
        debug: Whether to print debug info
    """
    try:
        lons = []
        lats = []
        prev_lon = None
          # Use efficient bisection method for each latitude
        for lat in lat_steps:
            try:
                def asc_residual(lon):
                    """Calculate residual for ASC ecliptic longitude at given lat/lon"""
                    try:
                        # Use Placidus houses for accurate ASC calculation
                        cusps, ascmc = swe.houses_ex(jd_tt, lat, lon, b'P')
                        asc_ecl_lon = ascmc[0]  # ASC ecliptic longitude
                        
                        # Apply the same longitude wrapping as horizon lines for consistency
                        asc_ecl_lon = _wrap_longitude(asc_ecl_lon)
                        target_wrapped = _wrap_longitude(target_asc_ecl_lon)
                          # Calculate difference with proper wrapping
                        diff = asc_ecl_lon - target_wrapped
                        # Wrap difference to [-180, 180] range
                        diff = _wrap_longitude(diff)
                        
                        return diff
                    except Exception:
                        return np.inf
                
                # Smart bracketing based on previous solution
                if prev_lon is not None:
                    # Use narrow bracket around previous solution
                    bracket_width = 10  # degrees
                    lon_start = prev_lon - bracket_width
                    lon_end = prev_lon + bracket_width
                else:
                    # Full range for first point
                    lon_start = -180
                    lon_end = 180
                
                # Ensure bracket is in valid range
                lon_start = max(-180, lon_start)
                lon_end = min(180, lon_end)
                
                # Try bisection method
                found_solution = False
                tolerance = 0.01  # 0.01 degree tolerance
                
                try:
                    f_start = asc_residual(lon_start)
                    f_end = asc_residual(lon_end)
                    
                    # Check if we have a sign change (bracket contains root)
                    if f_start * f_end <= 0 and abs(f_start) < 1000 and abs(f_end) < 1000:
                        # Bisection method
                        for _ in range(20):  # Max 20 iterations
                            lon_mid = 0.5 * (lon_start + lon_end)
                            f_mid = asc_residual(lon_mid)
                            
                            if abs(f_mid) < tolerance:
                                solution_lon = lon_mid
                                found_solution = True
                                break
                            
                            if f_start * f_mid < 0:
                                lon_end = lon_mid
                                f_end = f_mid
                            else:
                                lon_start = lon_mid
                                f_start = f_mid
                        
                        if not found_solution:
                            solution_lon = 0.5 * (lon_start + lon_end)
                            found_solution = True
                
                except Exception:
                    pass
                  # If bisection failed, try grid search
                if not found_solution:
                    grid_lons = np.linspace(-180, 180, 73)  # 5-degree steps
                    residuals = []
                    
                    for test_lon in grid_lons:
                        res = asc_residual(test_lon)
                        residuals.append(abs(res) if abs(res) < 1000 else 1000)
                    
                    min_idx = np.argmin(residuals)
                    if residuals[min_idx] < 1.0:  # Accept if within 1 degree
                        solution_lon = grid_lons[min_idx]
                        found_solution = True
                
                if found_solution:
                    # Apply the same longitude normalization as horizon lines
                    solution_lon = _wrap_longitude(solution_lon)
                    lons.append(solution_lon)
                    lats.append(lat)
                    prev_lon = solution_lon
                else:
                    prev_lon = None
                    
            except Exception as e:
                if debug:
                    print(f"[ERR] ASC aspect calculation failed at lat={lat:.1f}: {e}")
                prev_lon = None
                continue
        
        # Check if we have enough points for a meaningful line
        if len(lons) < 3:
            if debug:
                print(f"[WARN] Insufficient points for {planet_name} {ASPECT_LABELS[abs(delta_angle)]}: {len(lons)}")
            return None        # Convert to arrays and sort by latitude
        lons = np.array(lons)
        lats = np.array(lats)
        idx = np.argsort(lats)
        lons = lons[idx]
        lats = lats[idx]
        
        # Use the same proven spline approach as horizon lines
        # Let parametric_spline handle longitude unwrapping internally
        lons_smooth, lats_smooth = parametric_spline(lons, lats, density=400)
        
        # parametric_spline already wraps to [-180, 180], so coords are ready
        coords = list(zip(lons_smooth, lats_smooth))        # Split at dateline using the EXACT same approach as horizon lines
        segments = split_dateline(coords)  # Use default max_jump=45 like horizon lines
        
        # Use the same validation as horizon lines: just check that dateline split worked
        try:
            assert all(abs(a[0]-b[0]) <= 180 for seg in segments for a,b in zip(seg, seg[1:])), "Dateline split failed"
        except AssertionError:
            if debug:
                print(f"[WARN] Dateline split validation failed for {planet_name} {ASPECT_LABELS[abs(delta_angle)]}")
            return None
        
        # Use segments directly like horizon lines (no additional filtering)
        filtered_segments = [seg for seg in segments if len(seg) >= 2]
          # Create GeoJSON feature(s)
        if len(filtered_segments) == 0:
            if debug:
                print(f"[WARN] No valid segments after filtering for {planet_name} {ASPECT_LABELS[abs(delta_angle)]}")
            return None
        elif len(filtered_segments) == 1:
            geometry = {"type": "LineString", "coordinates": filtered_segments[0]}
        else:
            geometry = {"type": "MultiLineString", "coordinates": filtered_segments}
        
        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "planet": planet_name,
                "line_type": "ASPECT",
                "angle": abs(delta_angle),
                "to": "ASC",
                "label": _aspect_label(planet_name, delta_angle, "ASC")
            }
        }
        
        return feature        
    except Exception as e:
        if debug:
            print(f"[ERR] Failed to generate ASC aspect line for {planet_name} {ASPECT_LABELS[abs(delta_angle)]}: {e}")
        return None

# Set sidereal mode globally (Lahiri ayanamsha as example, can be changed)
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

if __name__ == "__main__":
    import json
    # Try to load a sample chart from debug_chart.json
    try:
        with open(os.path.join(os.path.dirname(__file__), "debug_chart.json"), "r", encoding="utf-8") as f:
            chart_data = json.load(f)
        print("[DEBUG] Loaded debug_chart.json")
    except Exception as e:
        print(f"[ERR] Could not load debug_chart.json: {e}")
        chart_data = None
    if chart_data:
        # Print raw MC, ASC, and planet longitudes for comparison
        jd = chart_data["utc_time"].get("julian_day")
        if jd is not None:
            jd_ut = jd
            delta_t = swe.deltat(jd_ut)
            jd_tt = jd_ut + delta_t / 86400.0
            obliq = get_true_obliquity(jd_tt)
            gst_tt_deg = swe.sidtime(jd_tt) * 15.0
            geo_lon = chart_data.get("longitude", 0.0)
            geo_lat = chart_data.get("latitude", 0.0)
            # MC
            mc_ecl = ecl_lon_of_mc(gst_tt_deg, geo_lon, obliq)
            print(f"[RAW] MC ecliptic longitude: {mc_ecl:.6f}")
            # ASC
            try:
                cusps, ascmc = swe.houses_ex(jd_tt, geo_lat, geo_lon, b'W')
                asc_ecl = ascmc[0]
                print(f"[RAW] ASC ecliptic longitude: {asc_ecl:.6f}")
            except Exception as e:
                print(f"[ERR] swe.houses_ex failed for ASC: {e}")
            # Planets
            planet_pos = _get_planet_positions(chart_data, jd)
            for pname, pos in planet_pos.items():
                print(f"[RAW] {pname} ecliptic longitude: {pos['ecl_lon']:.6f}")
        features = calculate_aspect_lines(chart_data, debug=True)
        print(f"[DEBUG] Features generated: {len(features)}")
        for feat in features[:3]:
            print(json.dumps(feat, indent=2))
    else:
        print("[ERR] No chart data available for aspect line calculation.")

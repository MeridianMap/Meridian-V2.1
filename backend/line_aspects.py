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
        "North Node": swe.MEAN_NODE, "South Node": swe.MEAN_NODE, "Ceres": swe.AST_OFFSET + 1, "Pallas Athena": swe.AST_OFFSET + 2,
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
        ra_deg = ppos_eq[0]
        # Ecliptic longitude
        ppos_ecl, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH)
        ecl_lon = ppos_ecl[0]
        # South Node: shift ecliptic longitude by 180°
        if pname == "South Node":
            ecl_lon = (ecl_lon + 180) % 360
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
        # ------------------------------------------------------------------
        # --- ASC aspect lines ---
        lat_steps = np.arange(-85, 85.1, 0.1)  # 0.1° steps for finer resolution
        asc_count = 0
        for pname, pos in planet_pos.items():
            planet_ecl_lon = pos["ecl_lon"]
            for delta in ASPECT_ANGLES + [-a for a in ASPECT_ANGLES]:
                lons, lats = [], []
                prev_lon = None
                for lat in lat_steps:
                    try:
                        target_asc = (planet_ecl_lon - delta) % 360
                        def asc_resid(lon):
                            try:
                                # Use whole sign houses ('W') instead of Placidus ('P')
                                cusps, ascmc = swe.houses_ex(jd_tt, lat, lon, b'W')
                                asc = ascmc[0]
                                diff = (asc - target_asc + 540) % 360 - 180
                                return diff
                            except Exception as err:
                                if debug:
                                    print(f"[ERR] swe.houses_ex failed: lat={lat}, lon={lon}, err={err}")
                                raise
                        # Use previous longitude as bracket if available
                        if prev_lon is not None:
                            lon_left = prev_lon - 5
                            lon_right = prev_lon + 5
                            lon_left = max(-180, lon_left)
                            lon_right = min(180, lon_right)
                        else:
                            lon_left, lon_right = -180, 180
                        found = False
                        try:
                            f_left = asc_resid(lon_left)
                            f_right = asc_resid(lon_right)
                        except Exception:
                            prev_lon = None
                            continue
                        if f_left * f_right > 0:
                            # Try full bracket if local bracket fails
                            lon_left, lon_right = -180, 180
                            try:
                                f_left = asc_resid(lon_left)
                                f_right = asc_resid(lon_right)
                            except Exception:
                                prev_lon = None
                                continue
                        if f_left * f_right > 0:
                            # Fallback: grid search for minimum
                            grid = np.linspace(-180, 180, 73)
                            vals = []
                            for test_lon in grid:
                                try:
                                    v = abs(asc_resid(test_lon))
                                except Exception:
                                    v = np.inf
                                vals.append(v)
                            min_idx = np.argmin(vals)
                            if vals[min_idx] < 1.0:
                                root = grid[min_idx]
                                found = True
                            else:
                                prev_lon = None
                                continue
                        if not found:
                            for _ in range(20):
                                mid = 0.5 * (lon_left + lon_right)
                                try:
                                    f_mid = asc_resid(mid)
                                except Exception:
                                    prev_lon = None
                                    break
                                if abs(f_mid) < 1e-3:
                                    root = mid
                                    found = True
                                    break
                                if f_left * f_mid < 0:
                                    lon_right = mid
                                    f_right = f_mid
                                else:
                                    lon_left = mid
                                    f_left = f_mid
                            else:
                                root = 0.5 * (lon_left + lon_right)
                                found = True
                        if found:
                            root = _normalize_lon(root)
                            lons.append(root)
                            lats.append(lat)
                            prev_lon = root
                    except Exception as e:
                        prev_lon = None
                        if debug:
                            print(f"[ERR] ASC aspect solve failed: {pname} {ASPECT_LABELS[abs(delta)]} lat={lat:.2f}: {e}")
                        continue
                if len(lons) < 2:
                    if debug:
                        print(f"[WARN] ASC aspect: {pname} {ASPECT_LABELS[abs(delta)]} insufficient points.")
                    continue
                lons, lats = (np.array(lons), np.array(lats))
                # Sort by latitude for AC aspect lines
                idx = np.argsort(lats)
                lons, lats = lons[idx], lats[idx]
                # Unwrap longitude sequence for continuity
                lons_unwrapped = np.degrees(np.unwrap(np.radians(lons)))
                lons_s, lats_s = parametric_spline(lons_unwrapped, lats, density=300)
                # Already wrapped to [-180, 180] by parametric_spline
                coords = list(zip(lons_s, lats_s))
                # Split at dateline
                segments = split_dateline(coords)
                # Discard segments with large longitude jumps (to avoid horizontal artifacts)
                cleaned_segments = []
                for seg in segments:
                    if all(abs(a[0] - b[0]) <= 90 for a, b in zip(seg, seg[1:])):
                        cleaned_segments.append(seg)
                for seg in cleaned_segments:
                    feat = {
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": seg},
                        "properties": {
                            "planet": pname,
                            "line_type": "ASPECT",
                            "angle": abs(delta),
                            "to": "ASC",
                            "label": _aspect_label(pname, delta, "ASC")
                        }
                    }
                    features.append(feat)
                    asc_count += 1
                if debug and lons.size and lats.size:
                    print(f"[DEBUG] ASC {pname} {ASPECT_LABELS[abs(delta)]} points: {len(lons)}")
        if debug:
            print(f"[DEBUG] ASC aspect lines generated: {asc_count}")
            print(f"[DEBUG] Total features generated: {len(features)}")
    except Exception as e:
        print(f"[ERR] Aspect line generation failed: {e}")
    return features

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

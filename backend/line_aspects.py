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
_OBLIQ = np.deg2rad(23.4392911)          # mean obliquity J2000

def ecl_lon_of_mc(gst_deg, geo_lon_deg):
    """
    Ecliptic longitude (λ_M C) of the local meridian, given
    Greenwich sidereal time gst_deg (°) and site longitude geo_lon_deg (° E).
    Formula:  tan λ = tan θ ⋅ cos ε , where θ = LST = gst + λ_geo.
    """
    lst = np.deg2rad((gst_deg + geo_lon_deg) % 360)
    return np.rad2deg(np.arctan2(np.sin(lst) * np.cos(_OBLIQ),
                                 np.cos(lst))) % 360

def geo_lon_for_mc(target_ecl_lon, gst_deg):
    """
    Geographic longitude (° E, range –180…180) whose Midheaven’s
    ecliptic longitude equals target_ecl_lon (°).
    Inverse of the above relation:  tan θ = cos ε ⋅ tan λ .
    """
    lam = np.deg2rad(target_ecl_lon)
    lst_deg = np.rad2deg(np.arctan2(np.cos(_OBLIQ) * np.sin(lam),
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
        return features
    jd = chart_data["utc_time"].get("julian_day")
    if jd is None:
        return features
    try:
        planet_pos = _get_planet_positions(chart_data, jd)
        # Use TT for sidereal time to match astro.com and avoid small offset
        jd_ut = jd
        delta_t = swe.deltat(jd_ut)
        jd_tt = jd_ut + delta_t / 86400.0
        
        # ------------------------------------------------------------------
        # MC aspect lines (planet ± 60°, 90°, 120° to the Midheaven)
        gst_ut_deg = swe.sidtime(jd_ut) * 15.0      # GST in UT hours → degrees

        for name, pos in planet_pos.items():
            plon = pos["ecl_lon"]                   # ecliptic longitude
            for delta in ASPECT_ANGLES + [-a for a in ASPECT_ANGLES]:
                target = (plon - delta) % 360
                lon_geo = geo_lon_for_mc(target, gst_ut_deg)

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
        # ------------------------------------------------------------------
        # --- ASC aspect lines ---
        lat_steps = np.linspace(-85, 85, 340)
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
                                cusps, ascmc = swe.houses_ex(jd_tt, lat, lon, b'P')
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
                idx = np.argsort(lats)
                lons, lats = lons[idx], lats[idx]
                lons_s, lats_s = parametric_spline(lons, lats, density=300)
                coords = list(zip(lons_s, lats_s))
                segments = split_dateline(coords)
                for seg in segments:
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
                if debug and lons.size and lats.size:
                    print(f"[DEBUG] ASC {pname} {ASPECT_LABELS[abs(delta)]} points: {len(lons)}")
    except Exception as e:
        print(f"[ERR] Aspect line generation failed: {e}")
    return features

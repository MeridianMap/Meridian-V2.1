"""
Parans (Paranatellonta) calculation module for Swiss Ephemeris
Calculates when a planet and a fixed star simultaneously cross key points (rising, setting, culminating, anti-culminating) for a given date and location.
"""
import swisseph as swe
import datetime
from typing import List, Dict
from scipy.optimize import bisect

# Event types for parans
PARAN_EVENTS = [
    (swe.CALC_RISE, swe.CALC_RISE, "Both Rising"),
    (swe.CALC_SET, swe.CALC_SET, "Both Setting"),
    (swe.CALC_MTRANSIT, swe.CALC_MTRANSIT, "Both Culminating (MC)"),
    (swe.CALC_ITRANSIT, swe.CALC_ITRANSIT, "Both Anti-culminating (IC)"),
    (swe.CALC_RISE, swe.CALC_MTRANSIT, "Star Rising, Planet Culminating"),
    (swe.CALC_MTRANSIT, swe.CALC_RISE, "Star Culminating, Planet Rising"),
    # Add more combinations as needed
]

def find_paran_latitude(jd_ut, lon, planet1_id, event1, planet2_id, event2, lat_min=-85, lat_max=85, alt=0.0, tol_minutes=4):
    """
    Find the latitude at a given longitude where two planetary events (e.g., rising) are simultaneous.
    Returns (latitude, event_time) or None if not found.
    """
    def time_diff(lat):
        geopos = [lon, lat, alt]
        res1, tret1 = swe.rise_trans(jd_ut, planet1_id, event1, geopos, swe.FLG_SWIEPH)
        res2, tret2 = swe.rise_trans(jd_ut, planet2_id, event2, geopos, swe.FLG_SWIEPH)
        if res1 != 0 or res2 != 0:
            return 1e6  # Large value if event not found
        # Return time difference in minutes
        return (tret1[0] - tret2[0]) * 24 * 60

    # Check if root exists in the interval
    try:
        if time_diff(lat_min) * time_diff(lat_max) > 0:
            return None  # No root in interval
        lat_paran = bisect(time_diff, lat_min, lat_max, xtol=0.01)
        # Get event time at this latitude
        geopos = [lon, lat_paran, alt]
        res, tret = swe.rise_trans(jd_ut, planet1_id, event1, geopos, swe.FLG_SWIEPH)
        if res == 0:
            dt = swe.revjul(tret[0])
            return lat_paran, dt
        else:
            return None
    except Exception as e:
        print(f"Error finding paran latitude: {e}")
        return None

def calculate_parans(jd_ut: float, lat: float, lon: float, planet_id: int, sweph_path: str = None, timezone: float = 0.0, alt: float = 0.0):
    """
    Calculate parans for a given planet at a location and date.
    Returns a list of dicts with event type and event time.
    """
    import swisseph as swe
    print(f"swisseph version: {getattr(swe, '__version__', 'unknown')}")
    # print(f"swe.rise_trans signature: {getattr(swe.rise_trans, '__doc__', 'no docstring available')}")
    if sweph_path:
        swe.set_ephe_path(sweph_path)
    results = []
    # For each event, use find_paran_latitude to get the actual latitude where the event is simultaneous for this planet and the Sun (as an example)
    sun_id = 0  # Swiss Ephemeris ID for Sun
    for i, (event1, _, label) in enumerate(PARAN_EVENTS):
        if planet_id == sun_id:
            continue  # Skip if the planet is the Sun itself
        result = find_paran_latitude(jd_ut, lon, planet_id, event1, sun_id, event1)
        if result:
            lat_paran, dt = result
            results.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-180, lat_paran], [180, lat_paran]]
                },
                "properties": {
                    "event": label,
                    "planet_event_time": dt,
                    "planet_id": planet_id,
                    "type": "paran"
                }
            })
    return results

# Example usage (to be removed or moved to tests):
# parans = calculate_parans(jd_ut, lat, lon, swe.SUN, "Regulus")
# for p in parans:
#     print(p)

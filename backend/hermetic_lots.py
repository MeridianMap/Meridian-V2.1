"""
Hermetic Lots (Arabic Parts) calculation module.
Calculates the most common Hermetic Lots for a given chart.
"""
from math import fmod

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def normalize_deg(deg):
    """Normalize degree to 0-360."""
    return deg % 360

def lot_sign_and_position(lon):
    sign_num = int(lon / 30) % 12
    sign_name = ZODIAC_SIGNS[sign_num]
    position = lon % 30
    return sign_name, position

def is_day_chart(sun_lon, asc_lon):
    """Returns True if Sun is above the horizon (diurnal chart)."""
    diff = (sun_lon - asc_lon) % 360
    return 0 <= diff < 180

# Expanded Hermetic Lot formulas (day/night)
LOT_FORMULAS = {
    "Fortune": lambda asc, sun, moon, is_day: normalize_deg(asc + (moon - sun) if is_day else asc + (sun - moon)),
    "Spirit": lambda asc, sun, moon, is_day: normalize_deg(asc + (sun - moon) if is_day else asc + (moon - sun)),
    "Eros": lambda asc, sun, moon, is_day: normalize_deg(asc + (venus - sun) if is_day else asc + (sun - venus)),
    "Necessity": lambda asc, sun, moon, is_day: normalize_deg(asc + (saturn - sun) if is_day else asc + (sun - saturn)),
    "Victory": lambda asc, sun, moon, is_day: normalize_deg(asc + (jupiter - sun) if is_day else asc + (sun - jupiter)),
    "Courage": lambda asc, sun, moon, is_day: normalize_deg(asc + (mars - sun) if is_day else asc + (sun - mars)),
    "Nemesis": lambda asc, sun, moon, is_day: normalize_deg(asc + (mercury - sun) if is_day else asc + (sun - mercury)),
}

def calculate_hermetic_lots(chart_planets, ascendant):
    """
    Calculate Hermetic Lots for a chart.
    Args:
        chart_planets (list): List of planet dicts (must include Sun and Moon)
        ascendant (float): Ascendant longitude in degrees
    Returns:
        list: List of lots with name, longitude, sign, position
    """
    # Get all needed planet longitudes
    sun = next((p for p in chart_planets if p["name"] == "Sun"), None)
    moon = next((p for p in chart_planets if p["name"] == "Moon"), None)
    mercury = next((p for p in chart_planets if p["name"] == "Mercury"), None)
    venus = next((p for p in chart_planets if p["name"] == "Venus"), None)
    mars = next((p for p in chart_planets if p["name"] == "Mars"), None)
    jupiter = next((p for p in chart_planets if p["name"] == "Jupiter"), None)
    saturn = next((p for p in chart_planets if p["name"] == "Saturn"), None)
    if not sun or not moon or not mercury or not venus or not mars or not jupiter or not saturn:
        return []
    sun_lon = sun["longitude"]
    moon_lon = moon["longitude"]
    mercury_lon = mercury["longitude"]
    venus_lon = venus["longitude"]
    mars_lon = mars["longitude"]
    jupiter_lon = jupiter["longitude"]
    saturn_lon = saturn["longitude"]
    asc_lon = ascendant
    is_day = is_day_chart(sun_lon, asc_lon)
    lots = []
    for lot_name, formula in LOT_FORMULAS.items():
        # Pass all needed arguments to the formula
        if lot_name == "Fortune":
            lot_lon = formula(asc_lon, sun_lon, moon_lon, is_day)
        elif lot_name == "Spirit":
            lot_lon = formula(asc_lon, sun_lon, moon_lon, is_day)
        elif lot_name == "Eros":
            lot_lon = normalize_deg(asc_lon + (venus_lon - sun_lon) if is_day else asc_lon + (sun_lon - venus_lon))
        elif lot_name == "Necessity":
            lot_lon = normalize_deg(asc_lon + (saturn_lon - sun_lon) if is_day else asc_lon + (sun_lon - saturn_lon))
        elif lot_name == "Victory":
            lot_lon = normalize_deg(asc_lon + (jupiter_lon - sun_lon) if is_day else asc_lon + (sun_lon - jupiter_lon))
        elif lot_name == "Courage":
            lot_lon = normalize_deg(asc_lon + (mars_lon - sun_lon) if is_day else asc_lon + (sun_lon - mars_lon))
        elif lot_name == "Nemesis":
            lot_lon = normalize_deg(asc_lon + (mercury_lon - sun_lon) if is_day else asc_lon + (sun_lon - mercury_lon))
        else:
            continue
        sign, pos = lot_sign_and_position(lot_lon)
        lots.append({
            "name": f"Lot of {lot_name}",
            "longitude": lot_lon,
            "sign": sign,
            "position": pos
        })
    return lots

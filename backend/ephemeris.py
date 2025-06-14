#!/usr/bin/env python3
"""
Swiss Ephemeris Interface for Astrological Calculations
Coordinator module: delegates core logic to specialized modules and assembles chart data.
"""

from backend.location_utils import get_coordinates
from backend.ephemeris_utils import calculate_extended_planets, initialize_ephemeris
from backend.hermetic_lots import calculate_hermetic_lots
from backend.fixed_star import get_fixed_star_positions
from backend.aspects import calculate_aspects
from backend.constants import HOUSE_SYSTEMS, ZODIAC_SIGNS
import swisseph as swe
import pytz
import datetime

# Only initialize ephemeris once globally
initialize_ephemeris()

def convert_to_utc(date_str, time_str, timezone_str):
    """
    Convert local time to UTC.
    Args:
        date_str (str): Date in format "YYYY-MM-DD" or "MM/DD/YYYY"
        time_str (str): Time in format "HH:MM"
        timezone_str (str): Timezone string (e.g., "America/New_York")
    Returns:
        tuple: (julian_day_ut, year, month, day, hour, minute, second) in UTC
    """
    try:
        # Handle both date formats: "YYYY-MM-DD" and "MM/DD/YYYY"
        if '-' in date_str:
            # Format: "YYYY-MM-DD"
            year, month, day = map(int, date_str.split('-'))
        elif '/' in date_str:
            # Format: "MM/DD/YYYY"
            month, day, year = map(int, date_str.split('/'))
        else:
            raise ValueError(f"Unsupported date format: {date_str}")
        
        hour, minute = map(int, time_str.split(':'))
        second = 0
        local_tz = pytz.timezone(timezone_str)
        local_dt = local_tz.localize(datetime.datetime(year, month, day, hour, minute, second))
        utc_dt = local_dt.astimezone(pytz.UTC)
        jd_ut = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)
        return (jd_ut, utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second)
    except Exception as e:
        print(f"Error converting time: {e}")
        return None

def calculate_houses(jd_ut, lat, lon, house_system='whole_sign'):
    """
    Calculate house cusps and related points.
    Args:
        jd_ut (float): Julian day in UT
        lat (float): Latitude
        lon (float): Longitude
        house_system (str): House system to use
    Returns:
        dict: House cusps and related points
    """
    hsys = HOUSE_SYSTEMS.get(house_system.lower(), b'W')  # Default to Whole Sign
    houses, ascmc = swe.houses(jd_ut, lat, lon, hsys)
    asc = ascmc[0]  # Ascendant
    mc = ascmc[1]   # Midheaven
    dsc = (asc + 180) % 360  # Descendant
    ic = (mc + 180) % 360    # Imum Coeli
    result = {
        'house_system': house_system,
        'ascendant': {
            'longitude': asc,
            'sign': ZODIAC_SIGNS[int(asc / 30)],
            'position': asc % 30
        },
        'midheaven': {
            'longitude': mc,
            'sign': ZODIAC_SIGNS[int(mc / 30)],
            'position': mc % 30
        },
        'descendant': {
            'longitude': dsc,
            'sign': ZODIAC_SIGNS[int(dsc / 30)],
            'position': dsc % 30
        },
        'imum_coeli': {
            'longitude': ic,
            'sign': ZODIAC_SIGNS[int(ic / 30)],
            'position': ic % 30
        },
        'houses': []
    }
    for i, cusp in enumerate(houses, 1):
        result['houses'].append({
            'house': i,
            'longitude': cusp,
            'sign': ZODIAC_SIGNS[int(cusp / 30)],
            'position': cusp % 30
        })
    return result

def calculate_chart(birth_date, birth_time, birth_city, birth_state="", birth_country="", timezone="", house_system='whole_sign', use_extended_planets=False):
    """
    Calculate complete astrological chart by delegating to specialized modules.
    Args:
        birth_date (str): Birth date in format "YYYY-MM-DD" or "MM/DD/YYYY"
        birth_time (str): Birth time in format "HH:MM"
        birth_city (str): City of birth
        birth_state (str, optional): State/province/region of birth
        birth_country (str, optional): Country of birth
        timezone (str): Timezone string (e.g., "America/New_York")
        house_system (str): House system to use
        use_extended_planets (bool): Whether to use extended planet set including asteroids
    Returns:
        dict: Complete astrological chart data
    """
    try:
        coordinates = get_coordinates(birth_city, birth_state, birth_country)
        if not coordinates:
            return {"error": "Could not geocode location. Please check city, state, and country information."}
        lat, lon = coordinates
        time_data = convert_to_utc(birth_date, birth_time, timezone)
        if not time_data:
            return {"error": "Could not convert time to UTC"}
        jd_ut, year, month, day, hour, minute, second = time_data
        houses_data = calculate_houses(jd_ut, lat, lon, house_system)
        planets_data = calculate_extended_planets(jd_ut, use_extended=use_extended_planets)
        aspects_data = calculate_aspects(planets_data)
        ascendant_long = houses_data["ascendant"]["longitude"] if "ascendant" in houses_data else None
        lots_data = calculate_hermetic_lots(planets_data, ascendant_long) if ascendant_long is not None else []
        fixed_stars_data = get_fixed_star_positions(jd_ut)
        result = {
            "input": {
                "date": birth_date,
                "time": birth_time,
                "city": birth_city,
                "state": birth_state,
                "country": birth_country,
                "timezone": timezone,
                "house_system": house_system
            },
            "coordinates": {
                "latitude": lat,
                "longitude": lon
            },
            "utc_time": {
                "year": year,
                "month": month,
                "day": day,
                "hour": hour,
                "minute": minute,
                "second": second,
                "julian_day": jd_ut
            },
            "houses": houses_data,
            "planets": planets_data,
            "aspects": aspects_data,
            "lots": lots_data,
            "fixed_stars": fixed_stars_data
        }
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    chart = calculate_chart(
        birth_date="1990-01-01",
        birth_time="12:00",
        birth_city="New York",
        birth_state="NY",
        birth_country="USA",
        timezone="America/New_York",
        house_system="whole_sign"
    )
    import json
    print(json.dumps(chart, indent=2))

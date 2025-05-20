#!/usr/bin/env python3
"""
Swiss Ephemeris Interface for Astrological Calculations
This module provides functions to calculate astrological data using the Swiss Ephemeris library.
"""

import swisseph as swe
import os
EPHE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "ephe") ) + os.sep
print(f"[ephemeris.py] Swiss Ephemeris path set to: {EPHE_PATH}")
swe.set_ephe_path(EPHE_PATH)
import datetime
import pytz
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from backend.ephemeris_utils import initialize_ephemeris, calculate_extended_planets
from backend.hermetic_lots import calculate_hermetic_lots
from backend.fixed_star import get_fixed_star_positions

# Initialize Swiss Ephemeris
initialize_ephemeris()  # Use enhanced initialization

# House systems mapping
HOUSE_SYSTEMS = {
    'whole_sign': b'W',      # Whole sign (default)
    'placidus': b'P',        # Placidus
    'koch': b'K',            # Koch
    'regiomontanus': b'R',   # Regiomontanus
    'campanus': b'C',        # Campanus
    'equal': b'E',           # Equal
    'porphyrius': b'O',      # Porphyrius
    'morinus': b'M',         # Morinus
    'polich_page': b'T',     # Polich-Page (Topocentric)
    'alcabitius': b'B',      # Alcabitius
    'krusinski': b'U',       # Krusinski-Pisa-Goelzer
    'equal_mc': b'X',        # Equal (MC)
}

# Planet and point names for reference
PLANET_NAMES = {
    swe.SUN: "Sun",
    swe.MOON: "Moon",
    swe.MERCURY: "Mercury",
    swe.VENUS: "Venus",
    swe.MARS: "Mars",
    swe.JUPITER: "Jupiter",
    swe.SATURN: "Saturn",
    swe.URANUS: "Uranus",
    swe.NEPTUNE: "Neptune",
    swe.PLUTO: "Pluto",
    swe.MEAN_NODE: "North Node",
    swe.TRUE_NODE: "True North Node",
    swe.MEAN_APOG: "Lilith (Mean)",
    swe.OSCU_APOG: "Lilith (Osculating)",
    swe.CHIRON: "Chiron",
    swe.PHOLUS: "Pholus",
    swe.CERES: "Ceres",
    swe.PALLAS: "Pallas",
    swe.JUNO: "Juno",
    swe.VESTA: "Vesta"
}

# Zodiac sign names
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", 
    "Leo", "Virgo", "Libra", "Scorpio", 
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def get_coordinates(city, state="", country=""):
    """
    Convert structured location information to latitude and longitude coordinates.
    
    Args:
        city (str): City name
        state (str, optional): State/province/region name
        country (str, optional): Country name
        
    Returns:
        tuple: (latitude, longitude) or None if geocoding fails
    """
    try:
        geolocator = Nominatim(user_agent="astro-app")
        
        # Build a structured query with available information
        query_parts = []
        if city:
            query_parts.append(city)
        if state:
            query_parts.append(state)
        if country:
            query_parts.append(country)
        
        # If we only have a city, try to geocode it directly
        if len(query_parts) == 1:
            location_data = geolocator.geocode(query_parts[0], exactly_one=False)
            if location_data and len(location_data) > 0:
                # Return the first result if there are multiple matches
                return (location_data[0].latitude, location_data[0].longitude)
        else:
            # Build a structured query string
            query = ", ".join(query_parts)
            location_data = geolocator.geocode(query)
            if location_data:
                return (location_data.latitude, location_data.longitude)
        
        return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding error: {e}")
        return None

def convert_to_utc(date_str, time_str, timezone_str):
    """
    Convert local time to UTC.
    
    Args:
        date_str (str): Date in format "YYYY-MM-DD"
        time_str (str): Time in format "HH:MM"
        timezone_str (str): Timezone string (e.g., "America/New_York")
        
    Returns:
        tuple: (julian_day_ut, year, month, day, hour, minute, second) in UTC
    """
    try:
        # Parse date and time
        year, month, day = map(int, date_str.split('-'))
        hour, minute = map(int, time_str.split(':'))
        second = 0
        
        # Create datetime object in the specified timezone
        local_tz = pytz.timezone(timezone_str)
        local_dt = local_tz.localize(datetime.datetime(year, month, day, hour, minute, second))
        
        # Convert to UTC
        utc_dt = local_dt.astimezone(pytz.UTC)
        
        # Calculate Julian day
        jd_ut = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, 
                          utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)
        
        return (jd_ut, utc_dt.year, utc_dt.month, utc_dt.day, 
                utc_dt.hour, utc_dt.minute, utc_dt.second)
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
    # Get house system code
    hsys = HOUSE_SYSTEMS.get(house_system.lower(), b'W')  # Default to Whole Sign
    
    # Calculate houses
    houses, ascmc = swe.houses(jd_ut, lat, lon, hsys)
    
    # Extract important points
    asc = ascmc[0]  # Ascendant
    mc = ascmc[1]   # Midheaven
    dsc = (asc + 180) % 360  # Descendant
    ic = (mc + 180) % 360    # Imum Coeli
    
    # Prepare result
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
    
    # Add house cusps
    for i, cusp in enumerate(houses, 1):
        result['houses'].append({
            'house': i,
            'longitude': cusp,
            'sign': ZODIAC_SIGNS[int(cusp / 30)],
            'position': cusp % 30
        })
    
    return result

def calculate_planets(jd_ut):
    """
    Calculate planetary positions.
    
    Args:
        jd_ut (float): Julian day in UT
        
    Returns:
        list: Planetary positions and data
    """
    planets = []
    
    # Set ephemeris flags to use built-in data if files are missing
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    
    # Main planets to calculate (limit to major planets to avoid missing file errors)
    main_planets = {
        swe.SUN: "Sun",
        swe.MOON: "Moon",
        swe.MERCURY: "Mercury",
        swe.VENUS: "Venus",
        swe.MARS: "Mars",
        swe.JUPITER: "Jupiter",
        swe.SATURN: "Saturn",
        swe.URANUS: "Uranus",
        swe.NEPTUNE: "Neptune",
        swe.PLUTO: "Pluto",
        swe.MEAN_NODE: "North Node"
    }
    
    # Calculate positions for main planets
    for planet_id, planet_name in main_planets.items():
        try:
            # Calculate planet position with flags
            result, flag = swe.calc_ut(jd_ut, planet_id, flags)
            
            # Extract data
            longitude = result[0]
            latitude = result[1]
            distance = result[2]
            speed = result[3]  # Daily motion in longitude
            
            # Determine zodiac sign and position within sign
            sign_num = int(longitude / 30)
            sign_name = ZODIAC_SIGNS[sign_num]
            position_in_sign = longitude % 30
            
            # Determine if retrograde
            is_retrograde = speed < 0
            
            # Add to results
            planets.append({
                'id': planet_id,
                'name': planet_name,
                'longitude': longitude,
                'latitude': latitude,
                'distance': distance,
                'speed': speed,
                'sign': sign_name,
                'position': position_in_sign,
                'retrograde': is_retrograde
            })
        except Exception as e:
            print(f"Error calculating {planet_name}: {e}")
            # Add placeholder data for failed calculations to avoid breaking the UI
            planets.append({
                'id': planet_id,
                'name': planet_name,
                'longitude': 0.0,
                'latitude': 0.0,
                'distance': 0.0,
                'speed': 0.0,
                'sign': 'Unknown',
                'position': 0.0,
                'retrograde': False,
                'error': str(e)
            })
    
    return planets

def calculate_aspects(planets, orb=6):
    """
    Calculate aspects between planets.
    
    Args:
        planets (list): List of planet data
        orb (float): Maximum orb in degrees
        
    Returns:
        list: Aspects between planets
    """
    aspects = []
    
    # Define aspect types and their ideal angles
    aspect_types = {
        'Conjunction': 0,
        'Opposition': 180,
        'Trine': 120,
        'Square': 90,
        'Sextile': 60,
        'Quincunx': 150,
        'Semi-sextile': 30,
        'Semi-square': 45,
        'Sesquiquadrate': 135
    }
    
    # Check each planet pair
    for i, planet1 in enumerate(planets):
        for j, planet2 in enumerate(planets):
            if i >= j:  # Skip self-aspects and duplicates
                continue
            
            # Calculate angular difference
            diff = abs(planet1['longitude'] - planet2['longitude'])
            if diff > 180:
                diff = 360 - diff
            
            # Check for aspects
            for aspect_name, aspect_angle in aspect_types.items():
                if abs(diff - aspect_angle) <= orb:
                    # Calculate exact orb
                    exact_orb = abs(diff - aspect_angle)
                    
                    # Determine if applying or separating
                    applying = False
                    if planet1['speed'] > planet2['speed']:
                        applying = (diff < aspect_angle)
                    else:
                        applying = (diff > aspect_angle)
                    
                    aspects.append({
                        'planet1': planet1['name'],
                        'planet2': planet2['name'],
                        'aspect': aspect_name,
                        'orb': exact_orb,
                        'applying': applying
                    })
    
    return aspects

def calculate_chart(birth_date, birth_time, birth_city, birth_state="", birth_country="", timezone="", house_system='whole_sign', use_extended_planets=False):
    """
    Calculate complete astrological chart.
    
    Args:
        birth_date (str): Birth date in format "YYYY-MM-DD"
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
    # Get coordinates from location
    coordinates = get_coordinates(birth_city, birth_state, birth_country)
    if not coordinates:
        return {"error": "Could not geocode location. Please check city, state, and country information."}
    
    lat, lon = coordinates
    
    # Convert time to UTC and get Julian day
    time_data = convert_to_utc(birth_date, birth_time, timezone)
    if not time_data:
        return {"error": "Could not convert time to UTC"}
    
    jd_ut, year, month, day, hour, minute, second = time_data
    
    # Calculate houses
    houses_data = calculate_houses(jd_ut, lat, lon, house_system)
    
    # Calculate planets using enhanced function
    planets_data = calculate_extended_planets(jd_ut, use_extended=use_extended_planets)
    
    # Calculate aspects
    aspects_data = calculate_aspects(planets_data)
    
    # Calculate Hermetic Lots
    ascendant_long = houses_data["ascendant"]["longitude"] if "ascendant" in houses_data else None
    lots_data = calculate_hermetic_lots(planets_data, ascendant_long) if ascendant_long is not None else []
    
    # Calculate Fixed Stars
    fixed_stars_data = get_fixed_star_positions(jd_ut)
    
    # Prepare result
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

if __name__ == "__main__":
    # Example usage
    chart = calculate_chart(
        birth_date="1990-01-01",
        birth_time="12:00",
        birth_location="New York, USA",
        timezone="America/New_York",
        house_system="whole_sign"
    )
    
    import json
    print(json.dumps(chart, indent=2))

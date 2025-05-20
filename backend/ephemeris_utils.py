import os
import requests
import zipfile
import io
import swisseph as swe
import time
from functools import lru_cache

swe.set_ephe_path(os.path.join(os.path.dirname(__file__), "ephe"))

# Define ephemeris file paths
EPHEMERIS_DIR = os.path.expanduser("~/.swisseph")
EPHEMERIS_URL = "https://www.astro.com/ftp/swisseph/ephe/"

def ensure_ephemeris_dir():
    """Ensure the ephemeris directory exists"""
    if not os.path.exists(EPHEMERIS_DIR):
        os.makedirs(EPHEMERIS_DIR)
        return True
    return False


def initialize_ephemeris():
    try:
        # ✅ Set to the correct local ephemeris directory
        local_ephe_path = os.path.join(os.path.dirname(__file__), "ephe")
        ephe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ephe"))
        print(f"Swiss Ephemeris path set to: {ephe_path}")
        swe.set_ephe_path(ephe_path)

        # ✅ Just check for a key file
        if not os.path.exists(os.path.join(local_ephe_path, "sepl_18.se1")):
            print("Warning: sepl_18.se1 not found in /ephe folder.")
            print("Please ensure ephemeris files are correctly placed.")

        return True
    except Exception as e:
        print(f"Error initializing ephemeris: {e}")
        return False


# Add caching to expensive calculations
@lru_cache(maxsize=128)
def cached_calc_ut(jd_ut, planet_id, flags):
    """
    Cached version of swe.calc_ut to improve performance
    
    Args:
        jd_ut (float): Julian day in UT
        planet_id (int): Planet ID
        flags (int): Calculation flags
        
    Returns:
        tuple: Result from swe.calc_ut
    """
    return swe.calc_ut(jd_ut, planet_id, flags)

# Extended planet list including more asteroids when available
EXTENDED_PLANETS = {
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

def calculate_extended_planets(jd_ut, use_extended=False):
    """
    Calculate planetary positions with option for extended set
    
    Args:
        jd_ut (float): Julian day in UT
        use_extended (bool): Whether to use extended planet set
        
    Returns:
        list: Planetary positions and data
    """
    planets = []
    
    # Set ephemeris flags to use built-in data if files are missing
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    
    # Main planets, asteroids, nodes, and Lilith for astrocartography (using correct Swiss Ephemeris IDs, no collisions)
    planet_set = {
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
        swe.AST_OFFSET + 1: "Ceres",
        swe.AST_OFFSET + 2: "Pallas Athena",
        swe.AST_OFFSET + 3: "Juno",
        swe.AST_OFFSET + 4: "Vesta",
        swe.CHIRON: "Chiron",
        swe.PHOLUS: "Pholus",
        swe.MEAN_NODE: "North Node",
        swe.MEAN_APOG: "Black Moon Lilith"
    }
    
    # Calculate positions for planets
    for planet_id, planet_name in planet_set.items():
        try:
            # Use cached calculation for better performance
            result, flag = cached_calc_ut(jd_ut, planet_id, flags)
            
            # Extract data
            longitude = result[0]
            latitude = result[1]
            distance = result[2]
            speed = result[3]  # Daily motion in longitude
            
            # Determine zodiac sign and position within sign
            sign_num = int(longitude / 30)
            sign_name = ZODIAC_SIGNS[int(longitude / 30) % 12]  # Ensure we don't go out of bounds
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
            
            # If this is an asteroid and the error is about missing files, try to download
            if planet_id in [swe.CHIRON, swe.PHOLUS, swe.CERES, swe.PALLAS, swe.JUNO, swe.VESTA]:
                if "SwissEph file" in str(e) and "not found" in str(e):
                    print(f"Attempting to download missing asteroid files...")
                    download_asteroid_files()
    
    # Add South Node as 180° opposite the North Node
    north_node = next((p for p in planets if p['name'] == "North Node"), None)
    if north_node:
        south_node_long = (north_node['longitude'] + 180) % 360
        planets.append({
            'id': 100000,  # Arbitrary unique ID for South Node
            'name': 'South Node',
            'longitude': south_node_long,
            'latitude': -north_node['latitude'],  # Opposite latitude
            'distance': north_node['distance'],
            'speed': -north_node['speed'],
            'sign': ZODIAC_SIGNS[int(south_node_long / 30) % 12],
            'position': south_node_long % 30,
            'retrograde': north_node['retrograde']
        })
    
    return planets

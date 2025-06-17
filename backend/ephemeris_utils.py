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
    import swisseph as swe
    import os
    ephe_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "ephe"))
    swe.set_ephe_path(ephe_dir)
    # ---- sanity check --------------------------------------------------
    EPHE_REQUIRED = [
        "sepl_18.se1",             # planets 1800-2399
        "seas_18.se1",             # main asteroids
        "sefstars.txt"             # fixed-star catalogue
    ]
    missing = [f for f in EPHE_REQUIRED if not os.path.exists(os.path.join(ephe_dir, f))]
    print("[EPHE] Using:", ephe_dir, "   missing:", missing)
    if missing:
        raise FileNotFoundError(
            "Swiss-Ephemeris cannot find: " + ", ".join(missing) +
            ".  Put them in backend/ephe or adjust swe.set_ephe_path."
        )
    # --------------------------------------------------------------------

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
    swe.MEAN_NODE: "Lunar Node",
    swe.TRUE_NODE: "True North Node",
    swe.MEAN_APOG: "Black Moon Lilith",
    swe.OSCU_APOG: "Lilith (Osculating)",
    swe.CHIRON: "Chiron",
    swe.PHOLUS: "Pholus",
    swe.AST_OFFSET + 1: "Ceres",
    swe.AST_OFFSET + 2: "Pallas Athena",
    swe.AST_OFFSET + 3: "Juno",
    swe.AST_OFFSET + 4: "Vesta"
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
        swe.MEAN_NODE: "Lunar Node",
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
                    print(f"Missing asteroid file for {planet_name}. Please add the required .se1 file to the backend/ephe/ folder.")
    
    return planets

def get_positions(jd_ut, ids):
    """
    Get planetary positions for the given Julian date and planet IDs.
    
    Args:
        jd_ut (float): Julian day in UT
        ids (list): List of planet names (e.g., ["Sun", "Moon"])
        
    Returns:
        list: List of dicts with planetary positions including both ecliptic and equatorial coordinates
    """
    name_to_id = {v: k for k, v in EXTENDED_PLANETS.items()}
    positions = []
    for name in ids:
        planet_id = name_to_id.get(name)
        if planet_id is not None:
            # Get ecliptic coordinates
            pos, _ = swe.calc_ut(jd_ut, planet_id)
            # Get equatorial coordinates  
            pos_eq, _ = swe.calc_ut(jd_ut, planet_id, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
            positions.append({
                "name": name,
                "id": planet_id,
                "longitude": pos[0],
                "latitude": pos[1],
                "distance": pos[2],
                "ra": pos_eq[0],  # Right Ascension for astrocartography
                "dec": pos_eq[1], # Declination for astrocartography
                "sign": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"][int(pos[0] / 30)],
                "position": pos[0] % 30
            })
    return positions

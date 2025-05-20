# Fixed star calculation module using Swiss Ephemeris
import swisseph as swe

# List of fixed stars and their Swiss Ephemeris names
FIXED_STARS = [
    {"name": "Regulus", "swe_name": "Regulus"},
    {"name": "Spica", "swe_name": "Spica"},
    {"name": "Antares", "swe_name": "Antares"},
    {"name": "Aldebaran", "swe_name": "Aldebaran"},
    {"name": "Algol", "swe_name": "Algol"},
    {"name": "Fomalhaut", "swe_name": "Fomalhaut"},
    {"name": "Sirius", "swe_name": "Sirius"},
    {"name": "Procyon", "swe_name": "Procyon"},
    {"name": "Vega", "swe_name": "Vega"},
    {"name": "Altair", "swe_name": "Altair"},
    {"name": "Betelgeuse", "swe_name": "Betelgeuz"},
    {"name": "Pollux", "swe_name": "Pollux"},
    {"name": "Galactic Center", "swe_name": "Gal. Center"},
]

def get_fixed_star_positions(jd):
    """
    Returns a list of dicts with name, longitude, latitude for each fixed star at given Julian day.
    """
    results = []
    for star in FIXED_STARS:
        try:
            # Use Swiss Ephemeris to get star position (longitude, latitude)
            # swe.fixstar returns (pos, starname, starret)
            ret = swe.fixstar(star["swe_name"], jd, flags=swe.FLG_SWIEPH)
            pos = ret[0]
            results.append({
                "name": star["name"],
                "longitude": pos[0],
                "latitude": pos[1],
                "magnitude": pos[3] if len(pos) > 3 else None
            })
        except Exception as e:
            print(f"Error calculating {star['name']}: {e}")
    return results

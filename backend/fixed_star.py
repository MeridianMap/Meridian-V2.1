# Fixed star calculation module using Swiss Ephemeris
import swisseph as swe
from ephemeris_utils import ensure_ephemeris_path

# List of fixed stars and their Swiss Ephemeris names
FIXED_STARS = [
    {"name": "Regulus", "swe_name": "Regulus"},
    {"name": "Aldebaran", "swe_name": "Aldebaran"},
    {"name": "Antares", "swe_name": "Antares"},
    {"name": "Fomalhaut", "swe_name": "Fomalhaut"},
    {"name": "Alphard", "swe_name": "Alphard"},
    {"name": "Alnilam", "swe_name": "Alnilam"},
    {"name": "Alnitak", "swe_name": "Alnitak"},
    {"name": "Bellatrix", "swe_name": "Bellatrix"},
    {"name": "Betelgeuse", "swe_name": "Betelgeuse"},  # Use the name from sefstars.txt
    {"name": "Mintaka", "swe_name": "Mintaka"},
    {"name": "Rigel", "swe_name": "Rigel"},
    {"name": "Unukalhai", "swe_name": "Unukalhai"},
    {"name": "Acrab (Graffias)", "swe_name": "Acrab"},  # SE uses 'Acrab'
    {"name": "Shaula", "swe_name": "Shaula"},
    {"name": "Lesath", "swe_name": "Lesath"},
    {"name": "Zubenelgenubi", "swe_name": "Zuben Elgenubi"},  # SE uses 'Zuben Elgenubi'
    {"name": "Zubeneschamali", "swe_name": "Zuben Eschamali"},  # SE uses 'Zuben Eschamali'
    {"name": "Deneb Algedi", "swe_name": "Deneb Algedi"},
    {"name": "Sadalmelek", "swe_name": "Sadalmelik"},  # SE uses 'Sadalmelik'
    {"name": "Sadalsuud", "swe_name": "Sadalsuud"},
    {"name": "Capella", "swe_name": "Capella"},
    {"name": "Castor", "swe_name": "Castor"},
    {"name": "Pollux", "swe_name": "Pollux"},
    {"name": "Procyon", "swe_name": "Procyon"},
    {"name": "Sirius", "swe_name": "Sirius"},
    {"name": "Canopus", "swe_name": "Canopus"},
    {"name": "Algol", "swe_name": "Algol"},
    {"name": "Alpherg (Eta Piscium)", "swe_name": "Alpherg"},  # SE uses 'Alpherg'
    {"name": "Alcyone", "swe_name": "Alcyone"},
    {"name": "Mirach", "swe_name": "Mirach"},
    {"name": "Scheat", "swe_name": "Scheat"},
    {"name": "Markab", "swe_name": "Markab"},
    {"name": "Thuban", "swe_name": "Thuban"},
    {"name": "Eltanin", "swe_name": "Eltanin"},
    {"name": "Alphecca", "swe_name": "Alphecca"},
    {"name": "Altair", "swe_name": "Altair"},
    {"name": "Deneb", "swe_name": "Deneb"},
    {"name": "Albireo", "swe_name": "Albireo"},
    {"name": "Achernar", "swe_name": "Achernar"},
    {"name": "Ankaa", "swe_name": "Ankaa"},
    {"name": "Menkar", "swe_name": "Menkar"},
    {"name": "Mirzam", "swe_name": "Mirzam"},
    {"name": "Spica", "swe_name": "Spica"},
    {"name": "Vindemiatrix", "swe_name": "Vindemiatrix"},
    {"name": "Algorab", "swe_name": "Algorab"},
    {"name": "Facies", "swe_name": "Facies"},
    {"name": "Rasalhague", "swe_name": "Rasalhague"},
    {"name": "Rastaban", "swe_name": "Rastaban"},
    {"name": "Galactic Center", "swe_name": "Gal. Center"}  # Not a star, but included for reference
]

def get_fixed_star_positions(jd):
    """
    Returns a list of dicts with name, longitude, latitude for each fixed star at given Julian day.
    """
    results = []
    for star in FIXED_STARS:
        try:
            ensure_ephemeris_path()
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

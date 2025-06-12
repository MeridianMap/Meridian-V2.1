# constants.py

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

PLANET_NAMES = {
    0: "Sun",
    1: "Moon",
    2: "Mercury",
    3: "Venus",
    4: "Mars",
    5: "Jupiter",
    6: "Saturn",
    7: "Uranus",
    8: "Neptune",
    9: "Pluto",
    10: "Mean Node",
    11: "True Node",
    12: "Mean Apogee",
    13: "Osculating Apogee",
    14: "Chiron",
    15: "Pholus",
    16: "Ceres",
    17: "Pallas",
    18: "Juno",
    19: "Vesta"
}

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", 
    "Leo", "Virgo", "Libra", "Scorpio", 
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

from typing import List, Dict

def calculate_aspects(planets: List[dict], orb=6) -> List[dict]:
    """
    Calculate aspects between planets.
    Args:
        planets (list): List of planet data
        orb (float): Maximum orb in degrees
    Returns:
        list: Aspects between planets
    """
    aspects = []
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
    for i, planet1 in enumerate(planets):
        for j, planet2 in enumerate(planets):
            if i >= j:
                continue
            diff = abs(planet1['longitude'] - planet2['longitude'])
            if diff > 180:
                diff = 360 - diff
            for aspect_name, aspect_angle in aspect_types.items():
                if abs(diff - aspect_angle) <= orb:
                    exact_orb = abs(diff - aspect_angle)
                    applying = False
                    if planet1.get('speed', 0) > planet2.get('speed', 0):
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

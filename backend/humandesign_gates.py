# Human Design Gate calculation module
# Each gate covers approximately 5.625 degrees (360 degrees / 64 gates)

# Human Design Gate ranges (in degrees of ecliptic longitude)
# Based on exact Human Design gate boundaries from barneyandflow.com
GATE_RANGES = [
    # Note: Starting from 28° 15' Pisces which is 358.25° (wrapping around)
    {"gate": 25, "start": 358.25, "end": 360.0, "sign": "Pisces", "name": "Innocence"},
    {"gate": 25, "start": 0.0, "end": 3.875, "sign": "Aries", "name": "Innocence"},  # 03° 52' 30" = 3.875°
    {"gate": 17, "start": 3.875, "end": 9.5, "sign": "Aries", "name": "Following"},  # 09° 30' 00" = 9.5°
    {"gate": 21, "start": 9.5, "end": 15.125, "sign": "Aries", "name": "The Hunter/Huntress"},  # 15° 07' 30" = 15.125°
    {"gate": 51, "start": 15.125, "end": 20.75, "sign": "Aries", "name": "The Arousing"},  # 20° 45' 00" = 20.75°
    {"gate": 42, "start": 20.75, "end": 26.375, "sign": "Aries", "name": "Increase"},  # 26° 22' 30" = 26.375°
    {"gate": 3, "start": 26.375, "end": 32.0, "sign": "Taurus", "name": "Ordering"},  # 02° 00' 00" Taurus = 32.0°
    
    {"gate": 27, "start": 32.0, "end": 37.625, "sign": "Taurus", "name": "Nourishment"},  # 07° 37' 30" = 37.625°
    {"gate": 24, "start": 37.625, "end": 43.25, "sign": "Taurus", "name": "Return"},  # 13° 15' 00" = 43.25°
    {"gate": 2, "start": 43.25, "end": 48.875, "sign": "Taurus", "name": "The Receptive"},  # 18° 52' 30" = 48.875°
    {"gate": 23, "start": 48.875, "end": 54.5, "sign": "Taurus", "name": "Splitting Apart"},  # 24° 30' 00" = 54.5°
    {"gate": 8, "start": 54.5, "end": 60.125, "sign": "Gemini", "name": "Contribution"},  # 00° 07' 30" Gemini = 60.125°
    
    {"gate": 20, "start": 60.125, "end": 65.75, "sign": "Gemini", "name": "Contemplation"},  # 05° 45' 00" = 65.75°
    {"gate": 16, "start": 65.75, "end": 71.375, "sign": "Gemini", "name": "Skills"},  # 11° 22' 30" = 71.375°
    {"gate": 35, "start": 71.375, "end": 77.0, "sign": "Gemini", "name": "Progress"},  # 17° 00' 00" = 77.0°
    {"gate": 45, "start": 77.0, "end": 82.625, "sign": "Gemini", "name": "Gathering Together"},  # 22° 27' 30" = 82.625°
    {"gate": 12, "start": 82.625, "end": 88.25, "sign": "Gemini", "name": "Standstill"},  # 28° 15' 00" = 88.25°
    {"gate": 15, "start": 88.25, "end": 93.875, "sign": "Cancer", "name": "Modesty"},  # 03° 52' 30" Cancer = 93.875°
    
    {"gate": 52, "start": 93.875, "end": 99.5, "sign": "Cancer", "name": "Inaction"},  # 09° 30' 00" = 99.5°
    {"gate": 39, "start": 99.5, "end": 105.125, "sign": "Cancer", "name": "Obstruction"},  # 15° 07' 30" = 105.125°
    {"gate": 53, "start": 105.125, "end": 110.75, "sign": "Cancer", "name": "Development"},  # 20° 45' 00" = 110.75°
    {"gate": 62, "start": 110.75, "end": 116.375, "sign": "Cancer", "name": "Preponderance of the Small"},  # 26° 22' 30" = 116.375°
    {"gate": 56, "start": 116.375, "end": 122.0, "sign": "Leo", "name": "The Wanderer"},  # 02° 00' 00" Leo = 122.0°
    
    {"gate": 31, "start": 122.0, "end": 127.625, "sign": "Leo", "name": "Influence"},  # 07° 37' 30" = 127.625°
    {"gate": 33, "start": 127.625, "end": 133.25, "sign": "Leo", "name": "Retreat"},  # 13° 15' 00" = 133.25°
    {"gate": 7, "start": 133.25, "end": 138.875, "sign": "Leo", "name": "The Army"},  # 18° 52' 30" = 138.875°
    {"gate": 4, "start": 138.875, "end": 144.5, "sign": "Leo", "name": "Youthful Folly"},  # 24° 30' 00" = 144.5°
    {"gate": 29, "start": 144.5, "end": 150.125, "sign": "Virgo", "name": "The Abysmal"},  # 00° 07' 30" Virgo = 150.125°
    
    {"gate": 59, "start": 150.125, "end": 155.75, "sign": "Virgo", "name": "Dispersion"},  # 05° 45' 00" = 155.75°
    {"gate": 40, "start": 155.75, "end": 161.375, "sign": "Virgo", "name": "Deliverance"},  # 11° 22' 30" = 161.375°
    {"gate": 64, "start": 161.375, "end": 167.0, "sign": "Virgo", "name": "Before Completion"},  # 17° 00' 00" = 167.0°
    {"gate": 47, "start": 167.0, "end": 172.625, "sign": "Virgo", "name": "Oppression"},  # 22° 37' 30" = 172.625°
    {"gate": 6, "start": 172.625, "end": 178.25, "sign": "Virgo", "name": "Conflict"},  # 28° 15' 00" = 178.25°
    {"gate": 46, "start": 178.25, "end": 183.875, "sign": "Libra", "name": "Pushing Upward"},  # 03° 52' 30" Libra = 183.875°
    
    {"gate": 18, "start": 183.875, "end": 189.5, "sign": "Libra", "name": "Work on What Has Been Spoiled"},  # 09° 30' 00" = 189.5°
    {"gate": 48, "start": 189.5, "end": 195.125, "sign": "Libra", "name": "The Well"},  # 15° 07' 30" = 195.125°
    {"gate": 57, "start": 195.125, "end": 200.75, "sign": "Libra", "name": "The Gentle"},  # 20° 45' 00" = 200.75°
    {"gate": 32, "start": 200.75, "end": 206.375, "sign": "Libra", "name": "Duration"},  # 26° 22' 30" = 206.375°
    {"gate": 50, "start": 206.375, "end": 212.0, "sign": "Scorpio", "name": "The Caldron"},  # 02° 00' 00" Scorpio = 212.0°
    
    {"gate": 28, "start": 212.0, "end": 217.625, "sign": "Scorpio", "name": "The Game Player"},  # 07° 37' 30" = 217.625°
    {"gate": 44, "start": 217.625, "end": 223.25, "sign": "Scorpio", "name": "Coming to Meet"},  # 13° 15' 00" = 223.25°
    {"gate": 1, "start": 223.25, "end": 228.875, "sign": "Scorpio", "name": "The Creative"},  # 18° 52' 30" = 228.875°
    {"gate": 43, "start": 228.875, "end": 234.5, "sign": "Scorpio", "name": "Breakthrough"},  # 24° 30' 00" = 234.5°
    {"gate": 14, "start": 234.5, "end": 240.125, "sign": "Sagittarius", "name": "Power Skills"},  # 00° 07' 30" Sagittarius = 240.125°
    
    {"gate": 34, "start": 240.125, "end": 245.75, "sign": "Sagittarius", "name": "The Power of the Great"},  # 05° 45' 00" = 245.75°
    {"gate": 9, "start": 245.75, "end": 251.375, "sign": "Sagittarius", "name": "The Taming Power of the Small"},  # 11° 22' 30" = 251.375°
    {"gate": 5, "start": 251.375, "end": 257.0, "sign": "Sagittarius", "name": "Waiting"},  # 17° 00' 00" = 257.0°
    {"gate": 26, "start": 257.0, "end": 262.625, "sign": "Sagittarius", "name": "The Taming Power of the Great"},  # 22° 37' 30" = 262.625°
    {"gate": 11, "start": 262.625, "end": 268.25, "sign": "Sagittarius", "name": "Peace"},  # 28° 15' 00" = 268.25°
    {"gate": 10, "start": 268.25, "end": 273.875, "sign": "Capricorn", "name": "Treading"},  # 03° 52' 30" Capricorn = 273.875°
    
    {"gate": 58, "start": 273.875, "end": 279.5, "sign": "Capricorn", "name": "The Joyous"},  # 09° 30' 00" = 279.5°
    {"gate": 38, "start": 279.5, "end": 285.125, "sign": "Capricorn", "name": "Opposition"},  # 15° 07' 30" = 285.125°
    {"gate": 54, "start": 285.125, "end": 290.75, "sign": "Capricorn", "name": "The Marrying Maiden"},  # 20° 45' 00" = 290.75°
    {"gate": 61, "start": 290.75, "end": 296.375, "sign": "Capricorn", "name": "Inner Truth"},  # 26° 22' 30" = 296.375°
    {"gate": 60, "start": 296.375, "end": 302.0, "sign": "Aquarius", "name": "Limitation"},  # 02° 00' 00" Aquarius = 302.0°
    
    {"gate": 41, "start": 302.0, "end": 307.625, "sign": "Aquarius", "name": "Decrease"},  # 07° 37' 30" = 307.625°
    {"gate": 19, "start": 307.625, "end": 313.25, "sign": "Aquarius", "name": "Wanting"},  # 13° 15' 00" = 313.25°
    {"gate": 13, "start": 313.25, "end": 318.875, "sign": "Aquarius", "name": "The Listener"},  # 18° 52' 30" = 318.875°
    {"gate": 49, "start": 318.875, "end": 324.5, "sign": "Aquarius", "name": "Revolution"},  # 24° 30' 00" = 324.5°
    {"gate": 30, "start": 324.5, "end": 330.125, "sign": "Pisces", "name": "Recognition"},  # 00° 07' 30" Pisces = 330.125°
    
    {"gate": 55, "start": 330.125, "end": 335.75, "sign": "Pisces", "name": "Spirit"},  # 05° 45' 00" = 335.75°
    {"gate": 37, "start": 335.75, "end": 341.375, "sign": "Pisces", "name": "The Family"},  # 11° 22' 30" = 341.375°
    {"gate": 63, "start": 341.375, "end": 347.0, "sign": "Pisces", "name": "After Completion"},  # 17° 00' 00" = 347.0°
    {"gate": 22, "start": 347.0, "end": 352.625, "sign": "Pisces", "name": "Grace"},  # 22° 37' 30" = 352.625°
    {"gate": 36, "start": 352.625, "end": 358.25, "sign": "Pisces", "name": "Darkening of the Light"},  # 28° 15' 00" = 358.25°
]

def get_gate_from_longitude(longitude):
    """
    Returns the Human Design gate for a given ecliptic longitude.
    
    Args:
        longitude (float): Ecliptic longitude in degrees (0-360)
        
    Returns:
        dict: Gate information with gate number, name, and sign
    """
    # Normalize longitude to 0-360 range
    longitude = longitude % 360
    
    for gate_info in GATE_RANGES:
        start = gate_info["start"]
        end = gate_info["end"]
        
        # Handle wrap-around case for Gate 25 at beginning/end of zodiac
        if start > end:  # This happens for the first entry that wraps around
            if longitude >= start or longitude < end:
                return {
                    "gate": gate_info["gate"],
                    "name": gate_info["name"],
                    "sign": gate_info["sign"],
                    "longitude_start": start,
                    "longitude_end": end
                }
        else:
            if start <= longitude < end:
                return {
                    "gate": gate_info["gate"],
                    "name": gate_info["name"],
                    "sign": gate_info["sign"],
                    "longitude_start": start,                    "longitude_end": end
                }
    
    # Should not reach here, but return None if no gate found
    return None

def get_gate_line_from_longitude(longitude):
    """
    Returns the Human Design gate and line for a given ecliptic longitude.
    Each gate has 6 lines, so each line covers approximately 0.9375 degrees.
    
    Args:
        longitude (float): Ecliptic longitude in degrees (0-360)
        
    Returns:
        dict: Gate and line information
    """
    gate_info = get_gate_from_longitude(longitude)
    if not gate_info:
        return None
    
    # Calculate line within the gate (1-6)
    gate_start = gate_info["longitude_start"]
    gate_end = gate_info["longitude_end"]
    gate_span = gate_end - gate_start
    line_span = gate_span / 6  # Each gate has 6 lines
    
    # Handle wrap-around at 360 degrees
    if gate_start > longitude:
        position_in_gate = (longitude + 360) - gate_start
    else:
        position_in_gate = longitude - gate_start
    
    line = int(position_in_gate / line_span) + 1
    line = max(1, min(6, line))  # Ensure line is between 1 and 6
    
    return {
        "gate": gate_info["gate"],
        "line": line,
        "name": gate_info["name"],
        "sign": gate_info["sign"],
        "gate_line": f"{gate_info['gate']}.{line}"
    }

def add_gate_info_to_object(obj, longitude_key="longitude"):
    """
    Adds Human Design gate information to an object based on its longitude.
    
    Args:
        obj (dict): Object to add gate info to
        longitude_key (str): Key name for longitude in the object
        
    Returns:
        dict: Object with added gate information
    """
    if longitude_key not in obj:
        return obj
    
    longitude = obj[longitude_key]
    gate_info = get_gate_from_longitude(longitude)
    gate_line_info = get_gate_line_from_longitude(longitude)
    
    if gate_info:
        obj["hd_gate"] = gate_info["gate"]
        obj["hd_gate_name"] = gate_info["name"]
        
    if gate_line_info:
        obj["hd_gate_line"] = gate_line_info["gate_line"]
        obj["hd_line"] = gate_line_info["line"]
    
    return obj

def calculate_gates_for_chart_objects(chart_data):
    """
    Adds Human Design gate information to all objects in chart data.
    
    Args:
        chart_data (dict): Chart data containing planets, lots, fixed_stars, etc.
        
    Returns:
        dict: Chart data with added gate information
    """
    # Add gates to planets
    if "planets" in chart_data:
        for planet in chart_data["planets"]:
            add_gate_info_to_object(planet)
    
    # Add gates to lots
    if "lots" in chart_data:
        for lot in chart_data["lots"]:
            add_gate_info_to_object(lot)
    
    # Add gates to fixed stars
    if "fixed_stars" in chart_data:
        for star in chart_data["fixed_stars"]:
            add_gate_info_to_object(star)
    
    # Add gates to asteroids if present
    if "asteroids" in chart_data:
        for asteroid in chart_data["asteroids"]:
            add_gate_info_to_object(asteroid)
    
    return chart_data

# Test function
def test_gate_calculation():
    """Test function to verify gate calculations"""
    test_longitudes = [
        0.0,    # Should be Gate 41
        15.0,   # Should be Gate 13
        30.0,   # Should be Gate 55
        90.0,   # Should be Gate 3
        180.0,  # Should be Gate 62
        270.0,  # Should be Gate 57
        359.0   # Should be Gate 38
    ]
    
    print("Testing Human Design Gate Calculations:")
    for longitude in test_longitudes:
        gate_info = get_gate_from_longitude(longitude)
        gate_line_info = get_gate_line_from_longitude(longitude)
        print(f"Longitude {longitude}°: Gate {gate_info['gate']} ({gate_info['name']}) - Line {gate_line_info['line']}")

if __name__ == "__main__":
    test_gate_calculation()

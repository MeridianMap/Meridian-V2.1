#!/usr/bin/env python3
"""
House placement calculations for planets, lots, and fixed stars.
Works with existing ephemeris data without modifying core calculations.
"""

def calculate_house_placement(planet_longitude, ascendant_longitude, house_system='whole_sign'):
    """
    Calculate which house a planet falls into.
    
    Args:
        planet_longitude (float): Planet's ecliptic longitude in degrees
        ascendant_longitude (float): Ascendant longitude in degrees  
        house_system (str): House system ('whole_sign', 'placidus', etc.)
    
    Returns:
        int: House number (1-12)
    """
    if house_system.lower() == 'whole_sign':
        # In whole sign houses, each sign = one house
        # House 1 starts at Ascendant's sign
        asc_sign = int(ascendant_longitude / 30)  # 0=Aries, 1=Taurus, etc.
        planet_sign = int(planet_longitude / 30)
        
        # Calculate house number (1-12)
        house_num = ((planet_sign - asc_sign) % 12) + 1
        return house_num
    
    # For other house systems, could add more complex calculations here
    # For now, default to whole sign
    return calculate_house_placement(planet_longitude, ascendant_longitude, 'whole_sign')

def get_zodiac_sign_name(longitude):
    """
    Get zodiac sign name for a given longitude.
    
    Args:
        longitude (float): Longitude in degrees (0-360)
    
    Returns:
        str: Sign name
    """
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    sign_index = int(longitude / 30)
    return signs[sign_index]

def add_house_placements_to_chart_data(chart_data):
    """
    Add house and sign information to all planetary bodies in chart data.
    Modifies the chart_data in place.
    
    Args:
        chart_data (dict): Complete chart data from calculate_chart()
    
    Returns:
        dict: Modified chart data with house placements added
    """
    if 'houses' not in chart_data or 'ascendant' not in chart_data['houses']:
        return chart_data
    
    ascendant_longitude = chart_data['houses']['ascendant']['longitude']
    house_system = chart_data['houses'].get('house_system', 'whole_sign')
    
    # Add house placements to planets
    if 'planets' in chart_data:
        for planet in chart_data['planets']:
            if 'longitude' in planet:
                planet['house'] = calculate_house_placement(
                    planet['longitude'], ascendant_longitude, house_system
                )                # Always calculate sign to ensure consistency
                planet['sign'] = get_zodiac_sign_name(planet['longitude'])
    
    # Add house placements to hermetic lots
    if 'lots' in chart_data:
        for lot in chart_data['lots']:
            if 'longitude' in lot:
                lot['house'] = calculate_house_placement(
                    lot['longitude'], ascendant_longitude, house_system
                )
                if 'sign' not in lot:
                    lot['sign'] = get_zodiac_sign_name(lot['longitude'])
    
    # Add house placements to fixed stars
    if 'fixed_stars' in chart_data:
        for star in chart_data['fixed_stars']:
            if 'longitude' in star:
                star['house'] = calculate_house_placement(
                    star['longitude'], ascendant_longitude, house_system
                )
                star['sign'] = get_zodiac_sign_name(star['longitude'])
    
    return chart_data

if __name__ == "__main__":
    # Test the module
    print("Testing house placement calculation...")
    
    # Test with sample data (Leo Ascendant at 143.11506415832278 degrees)
    asc_long = 143.11506415832278  # Leo ascendant
    
    # Test planets
    planets = [
        ("Sun", 112.56092327893447),  # Cancer
        ("Venus", 101.94327960377213),  # Cancer
        ("Mars", 125.66818196770282),  # Leo
    ]
    
    for name, longitude in planets:
        house = calculate_house_placement(longitude, asc_long, 'whole_sign')
        sign = get_zodiac_sign_name(longitude)
        print(f"{name}: {sign} in {house}{'st' if house == 1 else 'nd' if house == 2 else 'rd' if house == 3 else 'th'} house")

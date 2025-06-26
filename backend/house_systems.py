#!/usr/bin/env python3
"""
House System Management Module
Provides house system definitions, validation, and metadata for astrological calculations.
"""

try:
    from backend.constants import HOUSE_SYSTEMS
except ImportError:
    from constants import HOUSE_SYSTEMS

# Human-readable house system names and descriptions
HOUSE_SYSTEM_INFO = {
    'whole_sign': {
        'name': 'Whole Sign',
        'description': 'Each zodiac sign equals one house, starting with Ascendant sign as 1st house',
        'category': 'ancient'
    },
    'placidus': {
        'name': 'Placidus',
        'description': 'Most popular modern system, divides houses by time rather than space',
        'category': 'modern'
    },
    'koch': {
        'name': 'Koch',
        'description': 'Similar to Placidus but uses birthplace as reference point',
        'category': 'modern'
    },
    'regiomontanus': {
        'name': 'Regiomontanus',
        'description': 'Medieval system using celestial equator divisions',
        'category': 'medieval'
    },
    'campanus': {
        'name': 'Campanus',
        'description': 'Divides prime vertical into equal arcs',
        'category': 'medieval'
    },
    'equal': {
        'name': 'Equal House',
        'description': 'Divides ecliptic into 12 equal 30° segments from Ascendant',
        'category': 'modern'
    },
    'porphyrius': {
        'name': 'Porphyrius',
        'description': 'Ancient system dividing quadrants into equal parts',
        'category': 'ancient'
    },
    'morinus': {
        'name': 'Morinus',
        'description': 'Equatorial system based on right ascension',
        'category': 'modern'
    },
    'polich_page': {
        'name': 'Polich-Page (Topocentric)',
        'description': 'Modern topocentric system accounting for Earth\'s rotation',
        'category': 'modern'
    },
    'alcabitius': {
        'name': 'Alcabitius',
        'description': 'Medieval Arabic system using declination circles',
        'category': 'medieval'
    },
    'krusinski': {
        'name': 'Krusinski-Pisa-Goelzer',
        'description': 'Modern experimental house system',
        'category': 'experimental'
    },
    'equal_mc': {
        'name': 'Equal House (MC)',
        'description': 'Equal houses starting from Midheaven instead of Ascendant',
        'category': 'modern'
    }
}

def get_available_house_systems():
    """
    Get all available house systems with their metadata.
    
    Returns:
        dict: House system key -> metadata dictionary
    """
    return HOUSE_SYSTEM_INFO

def get_house_system_choices():
    """
    Get house system choices formatted for dropdown menus.
    
    Returns:
        list: List of (value, label) tuples for dropdown options
    """
    choices = []
    for key, info in HOUSE_SYSTEM_INFO.items():
        choices.append((key, info['name']))
    
    # Sort by category and name for better UX
    category_order = {'ancient': 1, 'medieval': 2, 'modern': 3, 'experimental': 4}
    choices.sort(key=lambda x: (category_order.get(HOUSE_SYSTEM_INFO[x[0]]['category'], 5), x[1]))
    
    return choices

def get_house_systems_by_category():
    """
    Get house systems grouped by category.
    
    Returns:
        dict: Category -> list of house systems
    """
    categories = {}
    for key, info in HOUSE_SYSTEM_INFO.items():
        category = info['category']
        if category not in categories:
            categories[category] = []
        categories[category].append({
            'key': key,
            'name': info['name'],
            'description': info['description']
        })
    
    # Sort each category
    for category in categories:
        categories[category].sort(key=lambda x: x['name'])
    
    return categories

def validate_house_system(house_system):
    """
    Validate that a house system is supported.
    
    Args:
        house_system (str): House system key to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return house_system in HOUSE_SYSTEMS

def get_house_system_code(house_system):
    """
    Get Swiss Ephemeris code for a house system.
    
    Args:
        house_system (str): House system key
        
    Returns:
        bytes: Swiss Ephemeris house system code
        
    Raises:
        ValueError: If house system is not supported
    """
    if not validate_house_system(house_system):
        raise ValueError(f"Unsupported house system: {house_system}")
    
    return HOUSE_SYSTEMS[house_system]

def get_house_system_name(house_system):
    """
    Get human-readable name for a house system.
    
    Args:
        house_system (str): House system key
        
    Returns:
        str: Human-readable name
    """
    return HOUSE_SYSTEM_INFO.get(house_system, {}).get('name', house_system.title())

def get_house_system_description(house_system):
    """
    Get description for a house system.
    
    Args:
        house_system (str): House system key
        
    Returns:
        str: Description of the house system
    """
    return HOUSE_SYSTEM_INFO.get(house_system, {}).get('description', 'No description available')

def get_default_house_system():
    """
    Get the default house system.
    
    Returns:
        str: Default house system key
    """
    return 'whole_sign'

def get_recommended_house_systems():
    """
    Get list of recommended house systems for beginners.
    
    Returns:
        list: List of recommended house system keys
    """
    return ['whole_sign', 'placidus', 'equal', 'koch']

if __name__ == "__main__":
    # Test the module
    print("Available House Systems:")
    for key, info in get_available_house_systems().items():
        print(f"  {key}: {info['name']} - {info['description']}")
    
    print("\nDropdown Choices:")
    for value, label in get_house_system_choices():
        print(f"  {value} -> {label}")
    
    print("\nBy Category:")
    for category, systems in get_house_systems_by_category().items():
        print(f"  {category.title()}:")
        for system in systems:
            print(f"    {system['key']}: {system['name']}")

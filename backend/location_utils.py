import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

def detect_timezone_from_coordinates(latitude, longitude):
    """
    Detect timezone from latitude and longitude coordinates
    
    Args:
        latitude (float): Latitude
        longitude (float): Longitude
        
    Returns:
        str: Timezone string or None if not found
    """
    try:
        # Initialize TimezoneFinder
        tf = TimezoneFinder()
        
        # Get timezone at coordinates
        timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
        
        # Validate timezone
        if timezone_str and timezone_str in pytz.all_timezones:
            return timezone_str
        
        return None
    except Exception as e:
        print(f"Error detecting timezone: {e}")
        return None

def get_location_suggestions(query, limit=5):
    """
    Get location suggestions based on a query string
    
    Args:
        query (str): Location query string
        limit (int): Maximum number of suggestions to return
        
    Returns:
        list: List of location suggestions
    """
    try:
        geolocator = Nominatim(user_agent="astro-app")
        
        # Get location suggestions
        locations = geolocator.geocode(query, exactly_one=False, limit=limit)
        
        if not locations:
            return []
        
        # Format suggestions
        suggestions = []
        for location in locations:
            # Extract city, state, country from address
            address_parts = location.address.split(', ')
            
            # Try to extract city, state, country
            city = address_parts[0] if len(address_parts) > 0 else ""
            
            # For state and country, try to extract from the end of the address
            country = address_parts[-1] if len(address_parts) > 1 else ""
            state = address_parts[-2] if len(address_parts) > 2 else ""
            
            # Get timezone
            timezone = detect_timezone_from_coordinates(location.latitude, location.longitude)
            
            suggestions.append({
                'address': location.address,
                'city': city,
                'state': state,
                'country': country,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'timezone': timezone
            })
        
        return suggestions
    except Exception as e:
        print(f"Error getting location suggestions: {e}")
        return []

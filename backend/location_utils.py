import pytz
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
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

def get_coordinates(city, state="", country=""):
    """
    Convert structured location information to latitude and longitude coordinates.
    
    Args:
        city (str): City name
        state (str, optional): State/province/region name
        country (str, optional): Country name
        
    Returns:
        tuple: (latitude, longitude) or None if geocoding fails
    """
    try:
        geolocator = Nominatim(user_agent="astro-app", timeout=10)
        query_parts = []
        if city:
            query_parts.append(city)
        if state:
            query_parts.append(state)
        if country:
            query_parts.append(country)
        
        if not query_parts:
            print("Error: No location information provided")
            return None
            
        if len(query_parts) == 1:
            query = query_parts[0]
            print(f"Geocoding single location: '{query}'")
            location_data = geolocator.geocode(query, exactly_one=False, timeout=10)
            if location_data and len(location_data) > 0:
                lat, lon = location_data[0].latitude, location_data[0].longitude
                print(f"Geocoding successful: {lat}, {lon}")
                return (lat, lon)
        else:
            query = ", ".join(query_parts)
            print(f"Geocoding full location: '{query}'")
            location_data = geolocator.geocode(query, timeout=10)
            if location_data:
                lat, lon = location_data.latitude, location_data.longitude
                print(f"Geocoding successful: {lat}, {lon}")
                return (lat, lon)
        
        print(f"Geocoding failed: No results found for '{query if 'query' in locals() else query_parts}'")
        return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding error (timeout/service): {e}")
        return None
    except Exception as e:
        print(f"General geocoding error: {e}")
        return None

@app.route('/api/location-suggestions', methods=['GET'])
def api_get_location_suggestions():
    """
    API endpoint to get location suggestions based on a query string.
    
    Query parameters:
    - query: Location query string
    - limit: Maximum number of suggestions to return (optional, default=5)
    
    Returns:
        JSON: List of location suggestions with city, state, country, coordinates, and timezone
    """
    try:
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 5))
        
        if not query:
            return jsonify({"error": "Missing query parameter"}), 400
        
        suggestions = get_location_suggestions(query, limit)
        return jsonify(suggestions)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/detect-timezone', methods=['GET'])
def api_detect_timezone():
    """
    API endpoint to detect timezone from latitude and longitude.
    
    Query parameters:
    - latitude: Latitude coordinate
    - longitude: Longitude coordinate
    
    Returns:
        JSON: Detected timezone string
    """
    try:
        latitude = float(request.args.get('latitude', 0))
        longitude = float(request.args.get('longitude', 0))
        
        if latitude == 0 and longitude == 0:
            return jsonify({"error": "Missing latitude and longitude parameters"}), 400
        
        timezone = detect_timezone_from_coordinates(latitude, longitude)
        
        if not timezone:
            return jsonify({"error": "Could not detect timezone for the given coordinates"}), 404
        
        return jsonify({"timezone": timezone})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

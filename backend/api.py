#!/usr/bin/env python3
"""
Flask API for Swiss Ephemeris Calculations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os
import swisseph as swe
import logging

# Set ephemeris path to always use backend/ephe, ignoring environment variable
EPHE_PATH = os.path.join(os.path.dirname(__file__), "ephe")
swe.set_ephe_path(EPHE_PATH)
logging.basicConfig(level=logging.INFO)
logging.info(f"Swiss Ephemeris path set to: '{EPHE_PATH}' (exists: {os.path.exists(EPHE_PATH)})")
if not os.path.exists(os.path.join(EPHE_PATH, "sefstars.txt")):
    logging.error(f"sefstars.txt not found in {EPHE_PATH}. Check ephemeris data files.")

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Docker/container imports (when running from /app directory)
from ephemeris import calculate_chart
from location_utils import get_location_suggestions, detect_timezone_from_coordinates
from astrocartography import calculate_astrocartography_lines_geojson
from utils import filter_lines_near_location
from layers.humandesign import calculate_human_design_layer
from house_systems import get_house_system_choices, get_house_systems_by_category, get_default_house_system, get_recommended_house_systems, HOUSE_SYSTEM_INFO

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route("/")
def index():
    return {"status": "Meridian API running"}, 200

@app.route("/api/health")
def health():
    return {"ok": True}, 200

@app.route('/api/calculate', methods=['POST'])
def api_calculate_chart():
    app.logger.info("▶️  /api/calculate")
    try:
        data = request.get_json(force=True)
        app.logger.info(f"Calculate endpoint received data: {data}")
        
        # Extract data with defaults
        birth_date = data.get('birth_date')
        birth_time = data.get('birth_time')
        birth_city = data.get('birth_city')
        birth_state = data.get('birth_state', '')
        birth_country = data.get('birth_country', '')
        coordinates = data.get('coordinates')  # Support coordinate-based requests
        timezone = data.get('timezone')
        house_system = data.get('house_system', 'whole_sign')
        use_extended_planets = data.get('use_extended_planets', False)
        progressed_for = data.get('progressed_for')
        progression_method = data.get('progression_method', 'secondary')
        progressed_date = data.get('progressed_date')

        # Validate required fields
        if not birth_date:
            app.logger.error("Missing required field: birth_date")
            return jsonify({"error": "birth_date is required"}), 400
        if not birth_time:
            app.logger.error("Missing required field: birth_time")
            return jsonify({"error": "birth_time is required"}), 400
        
        # Check if we have either city info OR coordinates
        if not birth_city and not coordinates:
            app.logger.error("Missing location: need either birth_city or coordinates")
            return jsonify({"error": "Either birth_city or coordinates is required"}), 400

        if coordinates:
            app.logger.info(f"Using coordinates: lat={coordinates.get('latitude')}, lon={coordinates.get('longitude')}")
        else:
            app.logger.info(f"Location info: city='{birth_city}', state='{birth_state}', country='{birth_country}'")

        chart_data = calculate_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_city=birth_city,
            birth_state=birth_state,
            birth_country=birth_country,
            timezone=timezone,
            house_system=house_system,
            use_extended_planets=use_extended_planets,
            progressed_for=progressed_for,
            progression_method=progression_method,
            progressed_date=progressed_date,
            coordinates=coordinates  # Pass coordinates if available
        )

        if "error" in chart_data:
            app.logger.error(f"Chart calculation error: {chart_data['error']}")
            return jsonify(chart_data), 400

        # Add all astrocartography features with logging
        try:
            app.logger.info("Calling calculate_astrocartography_lines_geojson...")
            astro_features = calculate_astrocartography_lines_geojson(chart_data, {
                'include_aspects': True,
                'include_fixed_stars': True,
                'include_hermetic_lots': True,
                'include_parans': True,
                'include_ac_dc': True,
                'include_ic_mc': True
            })
            feature_types = [f['properties'].get('category') for f in astro_features.get('features', [])]
            app.logger.info(f"Astrocartography feature types: {set(feature_types)}")
            app.logger.info(f"Astrocartography features generated: {len(astro_features.get('features', []))}")
            chart_data['astrocartography'] = astro_features
        except Exception as e:
            app.logger.exception("Astrocartography calculation failed")
            chart_data['astrocartography'] = {"error": str(e), "features": []}

        return jsonify(chart_data)
    except Exception as e:
        app.logger.exception("Calculation failed")
        return jsonify({"error": str(e)}), 500


@app.route('/api/interpret', methods=['POST'])
def api_interpret():
    """
    Generate interpretation based on chart data and relevant astrocartography lines
    near the birth location (within 600 miles).
    """
    try:
        chart_data = request.get_json()
        if not chart_data:
            return jsonify({"error": "Missing chart data"}), 400

        # Extract birth coordinates
        lat = chart_data.get("coordinates", {}).get("latitude")
        lon = chart_data.get("coordinates", {}).get("longitude")
        if lat is None or lon is None:
            return jsonify({"error": "Missing coordinates in chart data"}), 400

        # Generate full astrocartography lines
        astro_lines_result = calculate_astrocartography_lines_geojson(chart_data)
        all_lines = astro_lines_result.get("features", [])

        # Filter for lines near the birth location
        filtered_lines = filter_lines_near_location(all_lines, lat, lon, radius_miles=600)

        # Add filtered lines to chart_data for interpretation
        chart_data["filtered_lines"] = filtered_lines

        # Generate interpretation with GPT
        # interpretation = generate_interpretation(chart_data)  # REMOVED: No longer exists
        # return jsonify({"interpretation": interpretation})
        return jsonify({"filtered_lines": filtered_lines})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/api/astrocartography', methods=['POST'])
def api_astrocartography():
    try:
        data = request.get_json()
        print(f"[DEBUG] Astrocartography API received data keys: {list(data.keys()) if data else 'None'}")
        
        # Validate essential inputs (optional but safe)
        if not data.get("birth_date") or not data.get("birth_time") or not data.get("coordinates"):
            return jsonify({"error": "Missing birth_date, birth_time, or coordinates."}), 400
        
        # Extract filtering options from nested filter_options or top-level
        nested_filter_options = data.get('filter_options', {})
        filter_options = {
            'include_aspects': nested_filter_options.get('include_aspects', data.get('include_aspects', True)),
            'include_fixed_stars': nested_filter_options.get('include_fixed_stars', data.get('include_fixed_stars', True)),
            'include_hermetic_lots': nested_filter_options.get('include_hermetic_lots', data.get('include_hermetic_lots', True)),
            'include_parans': nested_filter_options.get('include_parans', data.get('include_parans', True)),
            'include_ac_dc': nested_filter_options.get('include_ac_dc', data.get('include_ac_dc', True)),
            'include_ic_mc': nested_filter_options.get('include_ic_mc', data.get('include_ic_mc', True)),
            'layer_type': nested_filter_options.get('layer_type', data.get('layer_type'))  # Check both nested and top-level
        }
        
        print(f"[DEBUG] Filter options: {filter_options}")
        
        # Handle different layer types
        layer_type = filter_options.get('layer_type')
        if layer_type == 'HD_DESIGN':
            # Human Design layer calculation
            try:
                
                # Extract birth data for HD calculation
                birth_date = data.get('birth_date')
                birth_time = data.get('birth_time')
                timezone = data.get('timezone')
                coordinates = data.get('coordinates', {})
                
                # Handle coordinates in multiple formats
                if isinstance(coordinates, list) and len(coordinates) > 0:
                    # Could be list of coordinate objects or list of numbers
                    if isinstance(coordinates[0], dict):
                        # List of coordinate objects: [{"lat": ..., "lng": ...}]
                        coord_obj = coordinates[0]
                        lat = coord_obj.get('lat') or coord_obj.get('latitude')
                        lon = coord_obj.get('lng') or coord_obj.get('longitude')
                    elif len(coordinates) >= 2 and isinstance(coordinates[0], (int, float)):
                        # List of numbers: [lon, lat]
                        lon, lat = coordinates[0], coordinates[1]
                    else:
                        lat, lon = None, None
                elif isinstance(coordinates, dict):
                    # Single coordinate dict: {"latitude": ..., "longitude": ...}
                    lat = coordinates.get('latitude') or coordinates.get('lat')
                    lon = coordinates.get('longitude') or coordinates.get('lng')
                else:
                    lat, lon = None, None
                
                print(f"[HD] Coordinates parsed: lat={lat}, lon={lon}")
                
                if not all([birth_date, birth_time, timezone, lat is not None, lon is not None]):
                    missing = []
                    if not birth_date: missing.append("birth_date")
                    if not birth_time: missing.append("birth_time") 
                    if not timezone: missing.append("timezone")
                    if lat is None: missing.append("latitude")
                    if lon is None: missing.append("longitude")
                    return jsonify({"error": f"Missing required data for Human Design calculation: {missing}"}), 400
                
                # Convert birth date/time to datetime
                import datetime as dt
                import pytz
                
                # Parse date and time
                if '-' in birth_date:
                    year, month, day = map(int, birth_date.split('-'))
                elif '/' in birth_date:
                    month, day, year = map(int, birth_date.split('/'))
                else:
                    return jsonify({"error": "Invalid birth date format"}), 400
                
                hour, minute = map(int, birth_time.split(':'))
                
                # Create timezone-aware datetime
                local_tz = pytz.timezone(timezone)
                birth_dt = local_tz.localize(dt.datetime(year, month, day, hour, minute))
                
                # Extract additional options
                opts = {
                    'house_system': data.get('house_system', 'whole_sign'),
                    'use_extended_planets': data.get('use_extended_planets', True)
                }
                
                # Calculate Human Design layer
                results = calculate_human_design_layer(birth_dt, lat, lon, timezone, filter_options, **opts)
                
                print(f"[HD] Generated {len(results.get('features', []))} Human Design features")
                return jsonify(results)
                
            except Exception as e:
                print(f"[ERROR] Human Design calculation error: {e}")
                return jsonify({"error": f"Human Design calculation failed: {str(e)}"}), 500
        else:
            # Standard astrocartography calculation
            results = calculate_astrocartography_lines_geojson(chart_data=data, filter_options=filter_options)
        
        print(f"Generated {len(results.get('features', []))} astrocartography features")
        
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/house-systems', methods=['GET'])
def api_get_house_systems():
    """
    Get available house systems with their metadata.
    """
    try:
        # Get detailed house system information
        house_systems = []
        for key, label in get_house_system_choices():
            house_systems.append({
                "id": key,
                "name": label,
                "description": HOUSE_SYSTEM_INFO.get(key, {}).get('description', ''),
                "category": HOUSE_SYSTEM_INFO.get(key, {}).get('category', 'modern')
            })
        
        return jsonify({
            "house_systems": house_systems,
            "default": get_default_house_system(),
            "recommended": get_recommended_house_systems(),
            "by_category": get_house_systems_by_category()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/timezones', methods=['GET'])
def api_get_timezones():
    import pytz
    timezones = [{"id": tz, "name": tz.replace('_', ' ')} for tz in pytz.all_timezones]
    return jsonify(timezones)

@app.route('/api/location-suggestions', methods=['GET'])
def api_get_location_suggestions():
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

@app.route('/api/parans', methods=['POST'])
def api_parans():
    data = request.get_json()
    jd_ut = data.get('jd_ut')
    lat = data.get('lat')
    lon = data.get('lon')
    planet_id = data.get('planet_id')
    # Optionally allow alt, sweph_path, etc.
    alt = data.get('alt', 0.0)
    if None in (jd_ut, lat, lon, planet_id):
        return {"error": "Missing required parameters (jd_ut, lat, lon, planet_id)"}, 400
    try:
        # parans = calculate_parans(jd_ut, lat, lon, planet_id, alt=alt)
        return {"type": "FeatureCollection", "features": []}  # Placeholder for now
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/house-systems')
def api_house_systems():
    systems = [
        {"id": "whole_sign", "name": "Whole Sign", "description": "Each zodiac sign equals one house"},
        {"id": "placidus", "name": "Placidus", "description": "Most popular modern system"},
        {"id": "koch", "name": "Koch", "description": "Similar to Placidus"},
        {"id": "equal", "name": "Equal House", "description": "Equal 30° segments from Ascendant"}
    ]
    return jsonify({"house_systems": systems})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

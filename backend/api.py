#!/usr/bin/env python3
"""
Flask API for Swiss Ephemeris Calculations + GPT Interpretation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.ephemeris import calculate_chart
from backend.location_utils import get_location_suggestions, detect_timezone_from_coordinates
from backend.interpretation import generate_interpretation  # <-- NEW IMPORT
from backend.astrocartography import calculate_astrocartography_lines_geojson
from backend.utils import filter_lines_near_location
from backend.parans import calculate_parans

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/calculate', methods=['POST'])
def api_calculate_chart():
    try:
        data = request.get_json()

        birth_date = data.get('birth_date')
        birth_time = data.get('birth_time')
        birth_city = data.get('birth_city')
        birth_state = data.get('birth_state', '')
        birth_country = data.get('birth_country', '')
        timezone = data.get('timezone')
        house_system = data.get('house_system', 'whole_sign')
        use_extended_planets = data.get('use_extended_planets', False)

        if not birth_city and 'birth_location' in data:
            birth_city = data.get('birth_location')

        if not all([birth_date, birth_time, birth_city, timezone]):
            return jsonify({"error": "Missing required parameters. Please provide birth_date, birth_time, birth_city, and timezone."}), 400

        chart_data = calculate_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_city=birth_city,
            birth_state=birth_state,
            birth_country=birth_country,
            timezone=timezone,
            house_system=house_system,
            use_extended_planets=use_extended_planets
        )

        if "error" in chart_data:
            return jsonify(chart_data), 400

        return jsonify(chart_data)

    except Exception as e:
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
        astro_lines_result = calculate_astrocartography_lines(chart_data)
        all_lines = astro_lines_result.get("lines", [])

        # Filter for lines near the birth location
        filtered_lines = filter_lines_near_location(all_lines, lat, lon, radius_miles=600)

        # Add filtered lines to chart_data for interpretation
        chart_data["filtered_lines"] = filtered_lines

        # Generate interpretation with GPT
        interpretation = generate_interpretation(chart_data)
        return jsonify({"interpretation": interpretation})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/api/astrocartography', methods=['POST'])
def api_astrocartography():
    try:
        data = request.get_json()

        # Validate essential inputs (optional but safe)
        if not data.get("birth_date") or not data.get("birth_time") or not data.get("coordinates"):
            return jsonify({"error": "Missing birth_date, birth_time, or coordinates."}), 400

        results = calculate_astrocartography_lines_geojson(chart_data=data)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/house-systems', methods=['GET'])
def api_get_house_systems():
    from backend.ephemeris import HOUSE_SYSTEMS
    house_systems = [{"id": key, "name": key.replace('_', ' ').title()} for key in HOUSE_SYSTEMS.keys()]
    return jsonify(house_systems)

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
        parans = calculate_parans(jd_ut, lat, lon, planet_id, alt=alt)
        return {"type": "FeatureCollection", "features": parans}
    except Exception as e:
        return {"error": str(e)}, 500

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

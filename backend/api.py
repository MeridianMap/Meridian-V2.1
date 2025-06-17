#!/usr/bin/env python3
"""
Flask API for Swiss Ephemeris Calculations + GPT Interpretation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os
import swisseph as swe

# Unset SE_EPHE_PATH to avoid conflicts
if "SE_EPHE_PATH" in os.environ:
    del os.environ["SE_EPHE_PATH"]

# Force ephemeris path to backend/ephe
swe.set_ephe_path(os.path.join(os.path.dirname(__file__), "ephe"))

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.ephemeris import calculate_chart
from backend.location_utils import get_location_suggestions, detect_timezone_from_coordinates
from backend.interpretation import generate_interpretation  # <-- NEW IMPORT
from backend.astrocartography import calculate_astrocartography_lines_geojson
from backend.utils import filter_lines_near_location
# from backend.parans import calculate_parans

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/calculate', methods=['POST'])
def api_calculate_chart():
    try:
        data = request.get_json()
        print(f"[DEBUG] Calculate endpoint received data: {data}")
        # Log progressed_date and its type
        progressed_date = data.get('progressed_date')
        print(f"[DEBUG] progressed_date: {progressed_date} (type: {type(progressed_date)})")
        birth_date = data.get('birth_date')
        birth_time = data.get('birth_time')
        birth_city = data.get('birth_city')
        birth_state = data.get('birth_state', '')
        birth_country = data.get('birth_country', '')
        timezone = data.get('timezone')
        house_system = data.get('house_system', 'whole_sign')
        use_extended_planets = data.get('use_extended_planets', False)
        progressed_for = data.get('progressed_for')
        progression_method = data.get('progression_method', 'secondary')
        # Defensive: print all incoming params
        print(f"[DEBUG] Params: birth_date={birth_date}, birth_time={birth_time}, city={birth_city}, tz={timezone}, progressed_for={progressed_for}, progression_method={progression_method}")
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
            progressed_date=progressed_date
        )
        if "error" in chart_data:
            print(f"[ERROR] Chart calculation error: {chart_data['error']}")
            return jsonify(chart_data), 400
        return jsonify(chart_data)
    except Exception as e:
        import traceback
        print(f"[EXCEPTION] /api/calculate: {e}")
        traceback.print_exc()
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
        interpretation = generate_interpretation(chart_data)
        return jsonify({"interpretation": interpretation})

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
        
        results = calculate_astrocartography_lines_geojson(chart_data=data, filter_options=filter_options)
        
        print(f"[DEBUG] Generated {len(results.get('features', []))} astrocartography features")
        
        # Debug: Check layer tagging
        layer_counts = {}
        for f in results.get('features', []):
            layer = f.get('properties', {}).get('layer', 'untagged')
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
        print(f"[DEBUG] Layer distribution: {layer_counts}")
        
        feature_summary = {}
        for f in results.get('features', []):
            cat = f.get('properties', {}).get('category', 'unknown')
            line_type = f.get('properties', {}).get('line_type', 'unknown')
            key = f"{cat}_{line_type}"
            feature_summary[key] = feature_summary.get(key, 0) + 1
        print(f"[DEBUG] Feature breakdown: {feature_summary}")
        
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
        # parans = calculate_parans(jd_ut, lat, lon, planet_id, alt=alt)
        return {"type": "FeatureCollection", "features": []}  # Placeholder for now
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

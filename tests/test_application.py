#!/usr/bin/env python3
"""
Test script for the enhanced astrological web application
This script tests various aspects of the application to ensure it works correctly
"""

import requests
import json
import time
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.ephemeris import calculate_chart
from backend.location_utils import get_location_suggestions, detect_timezone_from_coordinates

def test_location_suggestions():
    """Test location suggestions functionality with various inputs"""
    print("\n=== Testing Location Suggestions ===")
    
    # Test with common city names
    test_cities = [
        "New York",
        "London",
        "Paris",
        "Tokyo",
        "Springfield"  # Ambiguous - many cities with this name
    ]
    
    for city in test_cities:
        print(f"\nTesting suggestions for: {city}")
        suggestions = get_location_suggestions(city, limit=3)
        
        if suggestions:
            print(f"Found {len(suggestions)} suggestions:")
            for i, suggestion in enumerate(suggestions):
                print(f"  {i+1}. {suggestion['city']}, {suggestion['state']}, {suggestion['country']} "
                      f"(Coords: {suggestion['latitude']:.4f}, {suggestion['longitude']:.4f}, "
                      f"Timezone: {suggestion['timezone']})")
        else:
            print(f"No suggestions found for {city}")
    
    # Test with ambiguous city names
    print("\nTesting disambiguation for cities with the same name:")
    ambiguous_cities = [
        "Springfield",
        "Paris",
        "Cambridge"
    ]
    
    for city in ambiguous_cities:
        print(f"\nTesting disambiguation for: {city}")
        suggestions = get_location_suggestions(city, limit=5)
        
        if len(suggestions) > 1:
            print(f"Successfully found multiple locations for {city}:")
            for i, suggestion in enumerate(suggestions):
                print(f"  {i+1}. {suggestion['city']}, {suggestion['state']}, {suggestion['country']}")
        else:
            print(f"Could not find multiple locations for {city}")

def test_timezone_detection():
    """Test timezone detection from coordinates"""
    print("\n=== Testing Timezone Detection ===")
    
    test_locations = [
        {"name": "New York", "lat": 40.7128, "lon": -74.0060},
        {"name": "London", "lat": 51.5074, "lon": -0.1278},
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
        {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
        {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437}
    ]
    
    for location in test_locations:
        print(f"\nTesting timezone detection for: {location['name']}")
        timezone = detect_timezone_from_coordinates(location['lat'], location['lon'])
        
        if timezone:
            print(f"Detected timezone: {timezone}")
        else:
            print(f"Failed to detect timezone for {location['name']}")

def test_chart_calculation():
    """Test chart calculation with various inputs"""
    print("\n=== Testing Chart Calculation ===")
    
    test_cases = [
        {
            "name": "New York Birth",
            "birth_date": "1990-01-01",
            "birth_time": "12:00",
            "birth_city": "New York",
            "birth_state": "New York",
            "birth_country": "USA",
            "timezone": "America/New_York",
            "house_system": "whole_sign"
        },
        {
            "name": "London Birth with Extended Planets",
            "birth_date": "1985-06-15",
            "birth_time": "15:30",
            "birth_city": "London",
            "birth_state": "",
            "birth_country": "United Kingdom",
            "timezone": "Europe/London",
            "house_system": "placidus",
            "use_extended_planets": True
        },
        {
            "name": "Tokyo Birth with Different House System",
            "birth_date": "2000-12-25",
            "birth_time": "08:45",
            "birth_city": "Tokyo",
            "birth_state": "",
            "birth_country": "Japan",
            "timezone": "Asia/Tokyo",
            "house_system": "koch"
        }
    ]
    
    for case in test_cases:
        print(f"\nTesting chart calculation for: {case['name']}")
        
        try:
            start_time = time.time()
            
            chart = calculate_chart(
                birth_date=case["birth_date"],
                birth_time=case["birth_time"],
                birth_city=case["birth_city"],
                birth_state=case.get("birth_state", ""),
                birth_country=case.get("birth_country", ""),
                timezone=case["timezone"],
                house_system=case["house_system"],
                use_extended_planets=case.get("use_extended_planets", False)
            )
            
            end_time = time.time()
            
            if "error" in chart:
                print(f"Error calculating chart: {chart['error']}")
            else:
                print(f"Chart calculated successfully in {end_time - start_time:.2f} seconds")
                print(f"Ascendant: {chart['houses']['ascendant']['sign']} {chart['houses']['ascendant']['position']:.2f}°")
                print(f"Sun: {next((p for p in chart['planets'] if p['name'] == 'Sun'), {}).get('sign', 'Unknown')}")
                print(f"Moon: {next((p for p in chart['planets'] if p['name'] == 'Moon'), {}).get('sign', 'Unknown')}")
                print(f"Number of planets: {len(chart['planets'])}")
                print(f"Number of aspects: {len(chart['aspects'])}")
        
        except Exception as e:
            print(f"Exception during calculation: {e}")

def test_api_endpoints():
    """Test API endpoints"""
    print("\n=== Testing API Endpoints ===")
    
    # Start the Flask server in a separate process
    print("Note: This test assumes the Flask API is running on http://localhost:5000")
    print("If it's not running, please start it before running this test")
    
    base_url = "http://localhost:5000"
    
    # Test endpoints
    endpoints = [
        {"name": "Health Check", "url": f"{base_url}/health", "method": "GET"},
        {"name": "House Systems", "url": f"{base_url}/api/house-systems", "method": "GET"},
        {"name": "Timezones", "url": f"{base_url}/api/timezones", "method": "GET"},
        {"name": "Location Suggestions", "url": f"{base_url}/api/location-suggestions?query=New%20York", "method": "GET"},
        {"name": "Detect Timezone", "url": f"{base_url}/api/detect-timezone?latitude=40.7128&longitude=-74.0060", "method": "GET"}
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting endpoint: {endpoint['name']}")
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], timeout=5)
            else:
                print(f"Method {endpoint['method']} not implemented in test")
                continue
                
            print(f"Status code: {response.status_code}")
            if response.status_code == 200:
                print("Response: Success")
                # Print a sample of the response for verification
                response_json = response.json()
                if isinstance(response_json, list):
                    print(f"Received a list with {len(response_json)} items")
                    if len(response_json) > 0:
                        print(f"First item sample: {response_json[0]}")
                else:
                    print(f"Response sample: {str(response_json)[:100]}...")
            else:
                print(f"Failed with status code {response.status_code}")
                print(f"Response: {response.text}")
        
        except requests.exceptions.ConnectionError:
            print("Connection error. Is the API server running?")
        except Exception as e:
            print(f"Error testing endpoint: {e}")

def run_all_tests():
    """Run all tests"""
    print("=== Running All Tests for Enhanced Astrological Web Application ===")
    
    test_location_suggestions()
    test_timezone_detection()
    test_chart_calculation()
    
    # Uncomment to test API endpoints if the server is running
    # test_api_endpoints()
    
    print("\n=== All Tests Completed ===")

if __name__ == "__main__":
    run_all_tests()

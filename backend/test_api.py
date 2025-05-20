#!/usr/bin/env python3
"""
Test script for the Swiss Ephemeris backend API
This script tests the backend API with sample birth information
"""

import requests
import json
import sys
import os

# Test data
test_data = {
    "birth_date": "1990-01-01",
    "birth_time": "12:00",
    "birth_location": "New York, USA",
    "timezone": "America/New_York",
    "house_system": "whole_sign"
}

def test_backend_api():
    """Test the backend API with sample birth information"""
    print("Testing Swiss Ephemeris backend API...")
    
    # Start the Flask API
    print("Starting Flask API...")
    os.system("cd /home/ubuntu/astro-app && python3 backend/api.py > /dev/null 2>&1 &")
    
    # Wait for the API to start
    print("Waiting for API to start...")
    import time
    time.sleep(3)
    
    # Test the API
    try:
        # Test health check endpoint
        print("\nTesting health check endpoint...")
        health_response = requests.get("http://localhost:5000/health")
        print(f"Health check status code: {health_response.status_code}")
        print(f"Health check response: {health_response.json()}")
        
        # Test house systems endpoint
        print("\nTesting house systems endpoint...")
        house_systems_response = requests.get("http://localhost:5000/api/house-systems")
        print(f"House systems status code: {house_systems_response.status_code}")
        print(f"Available house systems: {len(house_systems_response.json())}")
        
        # Test timezones endpoint
        print("\nTesting timezones endpoint...")
        timezones_response = requests.get("http://localhost:5000/api/timezones")
        print(f"Timezones status code: {timezones_response.status_code}")
        print(f"Available timezones: {len(timezones_response.json())}")
        
        # Test calculate endpoint
        print("\nTesting calculate endpoint with sample data...")
        calculate_response = requests.post(
            "http://localhost:5000/api/calculate",
            json=test_data
        )
        print(f"Calculate status code: {calculate_response.status_code}")
        
        # Check if the response is valid
        if calculate_response.status_code == 200:
            result = calculate_response.json()
            
            # Verify the response contains the expected data
            print("\nVerifying response data...")
            
            # Check input data
            assert result["input"]["date"] == test_data["birth_date"], "Birth date mismatch"
            assert result["input"]["time"] == test_data["birth_time"], "Birth time mismatch"
            assert result["input"]["location"] == test_data["birth_location"], "Birth location mismatch"
            assert result["input"]["timezone"] == test_data["timezone"], "Timezone mismatch"
            assert result["input"]["house_system"] == test_data["house_system"], "House system mismatch"
            
            # Check coordinates
            assert "latitude" in result["coordinates"], "Latitude missing"
            assert "longitude" in result["coordinates"], "Longitude missing"
            
            # Check UTC time
            assert "year" in result["utc_time"], "UTC year missing"
            assert "month" in result["utc_time"], "UTC month missing"
            assert "day" in result["utc_time"], "UTC day missing"
            assert "hour" in result["utc_time"], "UTC hour missing"
            assert "minute" in result["utc_time"], "UTC minute missing"
            
            # Check houses
            assert "houses" in result, "Houses missing"
            assert "ascendant" in result["houses"], "Ascendant missing"
            assert "midheaven" in result["houses"], "Midheaven missing"
            
            # Check planets
            assert "planets" in result, "Planets missing"
            assert len(result["planets"]) > 0, "No planets returned"
            
            # Check aspects
            assert "aspects" in result, "Aspects missing"
            
            print("\nAll checks passed! Backend API is working correctly.")
            
            # Save a sample of the response to a file
            with open("/home/ubuntu/astro-app/backend/sample_response.json", "w") as f:
                json.dump(result, f, indent=2)
            print("\nSample response saved to /home/ubuntu/astro-app/backend/sample_response.json")
            
        else:
            print(f"Error: {calculate_response.json()}")
            
    except Exception as e:
        print(f"Error testing API: {e}")
    
    finally:
        # Kill the Flask API
        print("\nStopping Flask API...")
        os.system("kill $(lsof -t -i:5000) 2>/dev/null")

if __name__ == "__main__":
    test_backend_api()

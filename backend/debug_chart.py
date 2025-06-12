from backend.ephemeris import calculate_chart
from backend.astrocartography import calculate_astrocartography_lines_geojson
import json

if __name__ == "__main__":
    # Step 1: Generate a chart using ephemeris.py
    chart = calculate_chart(
        birth_date="1990-01-01",
        birth_time="12:00",
        birth_city="New York",
        birth_state="NY",
        birth_country="USA",
        timezone="America/New_York",
        house_system="whole_sign"
    )
    print("--- Chart Data ---")
    print(json.dumps(chart, indent=2))

    # Step 2: Pass chart to astrocartography.py
    features = calculate_astrocartography_lines_geojson(chart)
    print("\n--- Astrocartography FeatureCollection ---")
    print(json.dumps(features, indent=2))

import json

with open("debug_chart.json") as f:
    chart_data = json.load(f)

from astrocartography import calculate_astrocartography_lines_geojson

data = calculate_astrocartography_lines_geojson(chart_data)

# Print all MC/IC lines for North Node and South Node
for feat in data["features"]:
    props = feat["properties"]
    if props.get("planet") in ("North Node", "South Node") and props.get("line_type") in ("MC", "IC"):
        print(json.dumps({
            "planet": props.get("planet"),
            "planet_id": props.get("planet_id"),
            "line_type": props.get("line_type"),
            "coordinates": feat["geometry"]["coordinates"]
        }, indent=2))

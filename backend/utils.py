import swisseph as swe

def get_julian_day(date_str, time_str):
    """Convert date and time to Julian Day using Swiss Ephemeris"""
    year, month, day = map(int, date_str.split("-"))
    hour, minute = map(int, time_str.split(":"))
    return swe.julday(year, month, day, hour + minute / 60.0)

from geopy.distance import geodesic

def filter_lines_near_location(lines, latitude, longitude, max_distance_miles=600):
    """Return only the lines that fall within `max_distance_miles` of a given location."""
    nearby_lines = []
    for line in lines:
        line_lat = line.get("latitude")
        line_lon = line.get("longitude")
        if line_lat is None or line_lon is None:
            continue

        distance = geodesic((latitude, longitude), (line_lat, line_lon)).miles
        if distance <= max_distance_miles:
            line["distance"] = round(distance, 2)
            nearby_lines.append(line)

    return nearby_lines

"""
Geographic planetary line intersection module for Swiss Ephemeris
Calculates visual intersections between planetary lines (e.g., Saturn AC and Jupiter MC) and draws horizontal lines at crossing points.
"""
import swisseph as swe
from typing import List, Dict
from shapely.geometry import LineString, Point
from geojson import Feature

def draw_lat_line(lat: float, spacing: float = 1.0) -> List[List[float]]:
    """
    Utility function to create a horizontal (constant-latitude) line across the globe.
    Returns a list of [lon, lat] pairs from -180 to +180 longitude.
    """
    return [[lon, lat] for lon in range(-180, 181, int(spacing))]


def find_line_crossings_and_latitude_lines(aspect_lines: Dict[str, List[List[float]]]) -> List[Dict]:
    """
    Efficiently finds intersections between AC/DC and MC/IC lines for major planets and Chiron.
    Only checks AC vs MC, AC vs IC, DC vs MC, DC vs IC for each unique planet pair.
    Skips pairs with non-overlapping latitude ranges. Uses 1° step for best accuracy.
    Only uses primary AC/DC/IC/MC lines (not aspect lines).
    """
    print(f"[PARANS] Starting with {len(aspect_lines)} lines.")
    features = []
    # Group lines by planet and type, only primary lines
    line_map = {}
    for name, coords in aspect_lines.items():
        if '_' in name:
            planet, ltype = name.split('_', 1)
            if ltype in ("AC", "DC", "MC", "IC"):
                # Downsample to 1° step
                coords = coords[::max(1, len(coords)//180)]
                line_map.setdefault(planet, {})[ltype] = coords
    planets = list(line_map.keys())
    n = len(planets)
    print(f"[PARANS] {n} planets with primary lines.")
    # Diagnostic: print available line types for each planet
    for planet in planets:
        print(f"[PARANS] {planet}: lines present: {list(line_map[planet].keys())}")
    pair_count = 0
    seg_pair_count = 0
    intersection_count = 0
    # Only check AC/DC vs MC/IC for unique planet pairs
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            p1, p2 = planets[i], planets[j]
            for l1 in ("AC", "DC"):
                for l2 in ("MC", "IC"):
                    coords1 = line_map[p1].get(l1)
                    coords2 = line_map[p2].get(l2)
                    if not coords1 or not coords2:
                        continue
                    # Skip if latitude ranges do not overlap
                    minlat1, maxlat1 = min(pt[1] for pt in coords1), max(pt[1] for pt in coords1)
                    minlat2, maxlat2 = min(pt[1] for pt in coords2), max(pt[1] for pt in coords2)
                    # Only consider crossings within latitude band (e.g., -68 to +68)
                    LAT_BAND_MIN, LAT_BAND_MAX = -68, 68
                    if maxlat1 < minlat2 or maxlat2 < minlat1:
                        continue
                    if maxlat1 < LAT_BAND_MIN or minlat1 > LAT_BAND_MAX:
                        continue
                    if maxlat2 < LAT_BAND_MIN or minlat2 > LAT_BAND_MAX:
                        continue
                    pair_count += 1
                    for k in range(len(coords1) - 1):
                        seg1 = LineString([coords1[k], coords1[k + 1]])
                        for l in range(len(coords2) - 1):
                            seg2 = LineString([coords2[l], coords2[l + 1]])
                            seg_pair_count += 1
                            intersection = seg1.intersection(seg2)
                            if isinstance(intersection, Point):
                                lon, lat = intersection.x, intersection.y
                                # Only keep intersections within latitude band
                                if abs(lat) > 68:
                                    continue
                                intersection_count += 1
                                lat_line_coords = draw_lat_line(lat)
                                label = f"{p1} {l1} crossing {p2} {l2}"
                                feature = Feature(
                                    geometry={
                                        "type": "LineString",
                                        "coordinates": lat_line_coords
                                    },
                                    properties={
                                        "intersection_lat": lat,
                                        "intersection_lon": lon,
                                        "source_lines": [f"{p1}_{l1}", f"{p2}_{l2}"],
                                        "label": label,
                                        "type": "crossing_latitude"
                                    }
                                )
                                features.append(feature)
    print(f"[PARANS] Checked {pair_count} planet line pairs, {seg_pair_count} segment pairs.")
    print(f"[PARANS] Found {intersection_count} intersections.")
    return features

# --- End of planetary line intersection module ---

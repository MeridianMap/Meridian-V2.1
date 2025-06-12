import swisseph as swe

def calculate_mc_line(jd, ra_planet, pname):
    # MC: longitude where the planet is on the local meridian
    gmst = swe.sidtime(jd) * 15.0  # in degrees
    mc_long = (ra_planet - gmst) % 360.0
    if mc_long > 180:
        mc_long -= 360
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[mc_long, -85], [mc_long, 85]]
        },
        "properties": {
            "planet": pname,
            "line_type": "MC"
        }
    }

def calculate_ic_line(jd, ra_planet, pname):
    # IC: longitude opposite the MC (MC ± 180°)
    gmst = swe.sidtime(jd) * 15.0  # in degrees
    mc_long = (ra_planet - gmst) % 360.0
    ic_long = (mc_long + 180.0) % 360.0
    if ic_long > 180:
        ic_long -= 360
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[ic_long, -85], [ic_long, 85]]
        },
        "properties": {
            "planet": pname,
            "line_type": "IC"
        }
    }

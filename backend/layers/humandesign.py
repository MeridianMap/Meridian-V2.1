#!/usr/bin/env python3
"""
Human Design Layer Implementation

This module implements the Human Design layer which calculates all the same map features 
as the Natal layer (planet + asteroid lines, aspect lines, hermetic lots, planet-planet parans)
EXCEPT no fixed-stars. It uses the 88° solar-arc rule to determine the Design date/time
which is approximately 88 days before birth when the Sun was 88° earlier in its ecliptic position.

The layer has its own color palette and style tokens for easy UI toggling.
"""

import datetime as _dt
from typing import Dict, List, Optional
import swisseph as swe
import hashlib
import json

# Optional Redis support for caching
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    REDIS_AVAILABLE = True
except ImportError:
    redis_client = None
    REDIS_AVAILABLE = False
except Exception:
    redis_client = None
    REDIS_AVAILABLE = False

try:
    from backend.astrocartography import generate_all_astrocartography_features
    from backend.ephemeris_utils import get_positions, initialize_ephemeris
    from backend.hermetic_lots import calculate_hermetic_lots
    from backend.constants import ZODIAC_SIGNS
except ImportError:
    # Fallback for when running from backend directory
    from astrocartography import generate_all_astrocartography_features
    from ephemeris_utils import get_positions, initialize_ephemeris
    from hermetic_lots import calculate_hermetic_lots
    from constants import ZODIAC_SIGNS

# Initialize Swiss Ephemeris
initialize_ephemeris()

# Redis cache for design datetime calculations (optional)
# Removed the global Redis setup since we handle it in the class


class HumanDesignLayer:
    """
    Human Design Layer Calculator
    
    Implements the Human Design system's "Design" calculation which uses a solar-arc 
    of 88° to find the point approximately 88 days before birth. This layer includes
    all natal features except fixed stars and uses distinct styling.
    """
    
    def __init__(self, birth_dt: _dt.datetime, lat: float, lon: float, tzinfo: str, **opts):
        """
        Initialize Human Design layer calculator.
        
        Args:
            birth_dt: Birth datetime in local timezone
            lat: Birth latitude
            lon: Birth longitude  
            tzinfo: Timezone info string
            **opts: Additional options (house_system, use_extended_planets, etc.)
        """
        self.birth_dt = birth_dt
        self.lat = lat
        self.lon = lon
        self.tzinfo = tzinfo
        self.opts = opts
        
        # Calculate the design datetime using 88° solar-arc rule
        self.design_dt = self._calc_design_datetime(birth_dt)
        
        # Cache key for Redis storage
        self.cache_key = self._generate_cache_key()
    
    def _generate_cache_key(self) -> str:
        """Generate Redis cache key for this configuration."""
        key_data = {
            'birth_dt': self.birth_dt.isoformat(),
            'lat': round(self.lat, 6),
            'lon': round(self.lon, 6),
            'tzinfo': self.tzinfo
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"hd_design:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def _calc_design_datetime(self, birth_dt: _dt.datetime) -> _dt.datetime:
        """
        Calculate Human Design "Design" datetime using 88° solar-arc rule.
        
        The Design date is when the Sun was 88° earlier in its ecliptic position,
        which is approximately 88 days before birth. We use iterative refinement
        to achieve high precision.
        
        Args:
            birth_dt: Birth datetime
            
        Returns:
            Design datetime (approximately 88 days before birth)
        """        # Check Redis cache first
        if REDIS_AVAILABLE:
            try:
                import redis
                redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                cached_result = redis_client.get(self.cache_key)
                if cached_result:
                    cached_dt = _dt.datetime.fromisoformat(cached_result)
                    print(f"[HD] Using cached design datetime: {cached_dt}")
                    return cached_dt
            except Exception as e:
                print(f"[HD] Redis cache read error: {e}")
        
        # Calculate Julian Day for birth
        jd_birth = swe.julday(
            birth_dt.year, birth_dt.month, birth_dt.day,
            birth_dt.hour + birth_dt.minute/60 + birth_dt.second/3600
        )
        
        # Get Sun's longitude at birth
        try:
            sun_pos_birth, _ = swe.calc_ut(jd_birth, swe.SUN, swe.FLG_SWIEPH)
            sun_lon_birth = sun_pos_birth[0] % 360
        except Exception as e:
            print(f"[HD] Error calculating Sun position at birth: {e}")
            # Fallback to 88 days before birth
            return birth_dt - _dt.timedelta(days=88)
        
        # Target longitude: 88° earlier (counterclockwise)
        target_lon = (sun_lon_birth - 88) % 360
        
        # Initial guess: 88 days before birth
        guess_dt = birth_dt - _dt.timedelta(days=88)
        
        # Newton-Raphson iteration for precise solution
        for iteration in range(15):  # Allow up to 15 iterations
            jd_guess = swe.julday(
                guess_dt.year, guess_dt.month, guess_dt.day,
                guess_dt.hour + guess_dt.minute/60 + guess_dt.second/3600
            )
            
            try:
                sun_pos_guess, _ = swe.calc_ut(jd_guess, swe.SUN, swe.FLG_SWIEPH)
                lon_guess = sun_pos_guess[0] % 360
            except Exception as e:
                print(f"[HD] Error in iteration {iteration}: {e}")
                break
            
            # Calculate signed angular difference
            diff = ((lon_guess - target_lon + 540) % 360) - 180
            
            # Check convergence (0.0001° precision ≈ 0.4 arcseconds)
            if abs(diff) < 1e-4:
                print(f"[HD] Converged in {iteration + 1} iterations, precision: {abs(diff):.6f}°")
                break
            
            # Adjust guess based on angular error
            # Sun moves ~1°/day, so days_adjustment = diff / degrees_per_day
            # Use 360°/365.2422 days ≈ 0.9856°/day for mean solar motion
            days_adjustment = diff / 0.9856
            guess_dt -= _dt.timedelta(days=days_adjustment)
        
        else:
            print(f"[HD] Warning: Did not converge after 15 iterations, final error: {abs(diff):.6f}°")
        
        # Cache result in Redis if available
        if REDIS_AVAILABLE and redis_client:
            try:
                redis_client.setex(self.cache_key, 86400, guess_dt.isoformat())  # 24h TTL
                print(f"[HD] Cached design datetime: {guess_dt}")
            except Exception as e:
                print(f"[HD] Redis cache write error: {e}")
        
        print(f"[HD] Design datetime calculated: {guess_dt} (88° solar-arc from {birth_dt})")
        return guess_dt
    
    def compute_planet_lines(self, filter_options: Optional[Dict] = None) -> List[Dict]:
        """
        Compute planet and asteroid lines for Human Design using design datetime.
        
        Args:
            filter_options: Optional filtering options
            
        Returns:
            List of GeoJSON features for planet lines
        """
        if filter_options is None:
            filter_options = {}
          # Override datetime for design calculation and exclude aspects 
        # (they'll be handled separately by compute_aspect_lines)
        design_filter_options = {
            **filter_options,
            'layer_type': 'HD_DESIGN',
            'include_fixed_stars': False,  # HD excludes fixed stars
            'include_aspects': False,      # Exclude aspects here to avoid duplication
            'design_datetime': self.design_dt
        }
        
        # Create chart data using design datetime
        chart_data = self._create_design_chart_data()
        
        # Generate astrocartography features using design data
        features = generate_all_astrocartography_features(chart_data, design_filter_options)
          # Apply Human Design layer tagging and label updates
        for feature in features:
            if 'properties' in feature:
                feature['properties']['layer'] = 'HD_DESIGN'
                feature['properties']['hd_design'] = True
                
                # Update planet names with HD suffix for distinction
                if 'planet' in feature['properties']:
                    planet_name = feature['properties']['planet']
                    if not planet_name.endswith(' HD'):
                        feature['properties']['planet'] = f"{planet_name} HD"
                
                # Update labels to include HD for planet lines
                if 'label' in feature['properties']:
                    original_label = feature['properties']['label']
                    if 'HD' not in original_label:
                        # Add 'HD' after the planet name in the label
                        parts = original_label.split(' ', 1)
                        if len(parts) >= 2:
                            planet_name = parts[0]
                            rest_of_label = parts[1]
                            feature['properties']['label'] = f"{planet_name} HD {rest_of_label}"
                        else:
                            feature['properties']['label'] = f"{original_label} HD"
        
        return features
    
    def compute_aspect_lines(self) -> List[Dict]:
        """
        Compute aspect lines using design datetime.
        
        Returns:
            List of GeoJSON features for aspect lines
        """
        chart_data = self._create_design_chart_data()
        
        try:
            from backend.line_aspects import calculate_aspect_lines
            aspect_features = calculate_aspect_lines(chart_data)            # Apply HD tagging and modify labels
            for feature in aspect_features:
                if 'properties' in feature:
                    feature['properties']['layer'] = 'HD_DESIGN'
                    feature['properties']['category'] = 'aspect'
                    feature['properties']['hd_design'] = True
                    
                    # Modify the label to include 'HD'
                    original_label = feature['properties'].get('label', '')
                    if original_label and 'HD' not in original_label:
                        # Add 'HD' after the planet name
                        parts = original_label.split(' ', 1)
                        if len(parts) >= 2:
                            planet_name = parts[0]
                            rest_of_label = parts[1]
                            new_label = f"{planet_name} HD {rest_of_label}"
                            feature['properties']['label'] = new_label
                        else:
                            new_label = f"{original_label} HD"
                            feature['properties']['label'] = new_label
                    
                    # Also update the planet property to include HD
                    original_planet = feature['properties'].get('planet', '')
                    if original_planet and 'HD' not in original_planet:
                        feature['properties']['planet'] = f"{original_planet} HD"
            
            return aspect_features
        except Exception as e:
            print(f"[HD] Error calculating aspect lines: {e}")
            return []
    
    def compute_hermetic_lots(self) -> List[Dict]:
        """
        Compute hermetic lots using design datetime.
        
        Returns:
            List of GeoJSON features for hermetic lots
        """
        chart_data = self._create_design_chart_data()
        
        try:
            planets = chart_data.get('planets', [])
            houses = chart_data.get('houses', {})
            ascendant_long = houses.get('ascendant', {}).get('longitude')
            
            if ascendant_long is not None:
                lots = calculate_hermetic_lots(planets, ascendant_long)
                
                lot_features = []
                for lot in lots:
                    # Create MC/IC line features for each lot
                    from backend.line_ic_mc import calculate_mc_line, calculate_ic_line
                    
                    jd = chart_data.get('utc_time', {}).get('julian_day')
                    if jd:
                        # MC line
                        mc_feature = calculate_mc_line(jd, lot['longitude'], f"{lot['name']} HD")
                        if mc_feature:
                            mc_feature['properties']['category'] = 'hermetic_lot'
                            mc_feature['properties']['line_type'] = 'MC'
                            mc_feature['properties']['layer'] = 'HD_DESIGN'
                            mc_feature['properties']['hd_design'] = True
                            lot_features.append(mc_feature)
                        
                        # IC line
                        ic_feature = calculate_ic_line(jd, lot['longitude'], f"{lot['name']} HD")
                        if ic_feature:
                            ic_feature['properties']['category'] = 'hermetic_lot'
                            ic_feature['properties']['line_type'] = 'IC'
                            ic_feature['properties']['layer'] = 'HD_DESIGN'
                            ic_feature['properties']['hd_design'] = True
                            lot_features.append(ic_feature)
                
                return lot_features
        except Exception as e:
            print(f"[HD] Error calculating hermetic lots: {e}")
        
        return []
    
    def compute_parans(self) -> List[Dict]:
        """
        Compute planet-planet parans using design datetime.
          Returns:
            List of GeoJSON features for parans
        """
        # chart_data = self._create_design_chart_data()  # Not currently used
        
        try:
            from backend.line_parans import find_line_crossings_and_latitude_lines
            
            # Get planet lines for paran calculation
            features = self.compute_planet_lines({'include_parans': False})
            
            # Extract line coordinates for major planets
            allowed_crossing_bodies = {
                "Sun", "Moon", "Mercury", "Venus", "Mars", 
                "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron"
            }
            
            aspect_lines_dict = {}
            for f in features:
                if (
                    f["geometry"]["type"] == "LineString" and
                    f["properties"].get("category") == "planet" and
                    f["properties"].get("line_type") in ("AC", "DC", "MC", "IC")
                ):
                    planet_name = f["properties"].get("planet", "").replace(" HD", "")
                    if any(body in planet_name for body in allowed_crossing_bodies):
                        line_key = f"{planet_name}_{f['properties'].get('line_type', '')}"
                        if line_key not in aspect_lines_dict:
                            aspect_lines_dict[line_key] = []
                        aspect_lines_dict[line_key].append(f["geometry"]["coordinates"])
            
            # Flatten coordinate lists
            aspect_lines_dict = {
                k: [pt for seg in v for pt in seg] 
                for k, v in aspect_lines_dict.items()
            }
            
            # Calculate crossings
            crossing_features = find_line_crossings_and_latitude_lines(aspect_lines_dict)
            
            # Apply HD tagging
            for feature in crossing_features:
                if 'properties' in feature:
                    feature['properties']['layer'] = 'HD_DESIGN'
                    feature['properties']['category'] = 'parans'
                    feature['properties']['hd_design'] = True
            
            return crossing_features
        except Exception as e:
            print(f"[HD] Error calculating parans: {e}")
            return []
    
    def _create_design_chart_data(self) -> Dict:
        """
        Create chart data using design datetime for calculations.
        
        Returns:
            Chart data dictionary with design datetime
        """
        # Convert design datetime to Julian Day
        jd_design = swe.julday(
            self.design_dt.year, self.design_dt.month, self.design_dt.day,
            self.design_dt.hour + self.design_dt.minute/60 + self.design_dt.second/3600
        )
        
        # Calculate planets at design time
        use_extended = self.opts.get('use_extended_planets', True)
        
        if use_extended:
            planet_names = [
                "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
                "Uranus", "Neptune", "Pluto", "Lunar Node", "Chiron", "Ceres",
                "Pallas Athena", "Juno", "Vesta", "Black Moon Lilith", "Pholus"
            ]
        else:
            planet_names = [
                "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
                "Uranus", "Neptune", "Pluto", "Lunar Node"
            ]
        
        planets = get_positions(jd_design, planet_names)
        
        # Mark all planets as design data
        for planet in planets:
            planet['data_type'] = 'hd_design'
            planet['hd_design'] = True
        
        # Calculate houses at design time
        house_system = self.opts.get('house_system', 'whole_sign')
        houses_data = self._calculate_houses_at_design(jd_design, house_system)
        
        # Calculate hermetic lots
        ascendant_long = houses_data.get('ascendant', {}).get('longitude')
        lots = []
        if ascendant_long is not None:
            try:
                lots = calculate_hermetic_lots(planets, ascendant_long)
                for lot in lots:
                    lot['hd_design'] = True
                    lot['data_type'] = 'hd_design'
            except Exception as e:
                print(f"[HD] Error calculating lots: {e}")
        
        return {
            'planets': planets,
            'houses': houses_data,
            'lots': lots,
            'coordinates': {'latitude': self.lat, 'longitude': self.lon},
            'utc_time': {
                'julian_day': jd_design,
                'year': self.design_dt.year,
                'month': self.design_dt.month,
                'day': self.design_dt.day,
                'hour': self.design_dt.hour,
                'minute': self.design_dt.minute,
                'second': self.design_dt.second
            },
            'hd_design': True,
            'layer_type': 'HD_DESIGN'
        }
    
    def _calculate_houses_at_design(self, jd_design: float, house_system: str) -> Dict:
        """
        Calculate house cusps and angles at design time.
        
        Args:
            jd_design: Julian day for design time
            house_system: House system to use
            
        Returns:
            Houses data dictionary
        """
        try:
            from backend.constants import HOUSE_SYSTEMS
            
            hsys = HOUSE_SYSTEMS.get(house_system.lower(), b'W')
            houses, ascmc = swe.houses(jd_design, self.lat, self.lon, hsys)
            
            asc = ascmc[0]  # Ascendant
            mc = ascmc[1]   # Midheaven
            dsc = (asc + 180) % 360  # Descendant
            ic = (mc + 180) % 360    # Imum Coeli
            
            result = {
                'house_system': house_system,
                'ascendant': {
                    'longitude': asc,
                    'sign': ZODIAC_SIGNS[int(asc / 30)],
                    'position': asc % 30
                },
                'midheaven': {
                    'longitude': mc,
                    'sign': ZODIAC_SIGNS[int(mc / 30)],
                    'position': mc % 30
                },
                'descendant': {
                    'longitude': dsc,
                    'sign': ZODIAC_SIGNS[int(dsc / 30)],
                    'position': dsc % 30
                },
                'imum_coeli': {
                    'longitude': ic,
                    'sign': ZODIAC_SIGNS[int(ic / 30)],
                    'position': ic % 30
                },
                'houses': []
            }
            
            for i, cusp in enumerate(houses, 1):
                result['houses'].append({
                    'house': i,
                    'longitude': cusp,
                    'sign': ZODIAC_SIGNS[int(cusp / 30)],
                    'position': cusp % 30
                })
            
            return result
        except Exception as e:
            print(f"[HD] Error calculating houses: {e}")
            return {}
    
    def generate_all_features(self, filter_options: Optional[Dict] = None) -> List[Dict]:
        """
        Generate all Human Design features (everything except fixed stars).
        
        Args:
            filter_options: Optional filtering options
            
        Returns:
            List of all GeoJSON features for Human Design layer
        """
        if filter_options is None:
            filter_options = {
                'include_aspects': True,
                'include_fixed_stars': False,  # HD never includes fixed stars
                'include_hermetic_lots': True,
                'include_parans': True,
                'include_ac_dc': True,
                'include_ic_mc': True
            }
        
        # Ensure fixed stars are always excluded for HD
        filter_options['include_fixed_stars'] = False
        
        all_features = []
        
        # Planet lines (includes AC/DC, IC/MC)
        if filter_options.get('include_ac_dc', True) or filter_options.get('include_ic_mc', True):
            planet_features = self.compute_planet_lines(filter_options)
            all_features.extend(planet_features)
        
        # Aspect lines
        if filter_options.get('include_aspects', True):
            aspect_features = self.compute_aspect_lines()
            all_features.extend(aspect_features)
        
        # Hermetic lots
        if filter_options.get('include_hermetic_lots', True):
            lot_features = self.compute_hermetic_lots()
            all_features.extend(lot_features)
        
        # Parans
        if filter_options.get('include_parans', True):
            paran_features = self.compute_parans()
            all_features.extend(paran_features)
        
        print(f"[HD] Generated {len(all_features)} Human Design features")
        return all_features


def calculate_human_design_layer(
    birth_dt: _dt.datetime,
    lat: float,
    lon: float,
    tzinfo: str,
    filter_options: Optional[Dict] = None,
    **opts
) -> Dict:
    """
    Main entry point for Human Design layer calculation.
    
    Args:
        birth_dt: Birth datetime
        lat: Birth latitude
        lon: Birth longitude
        tzinfo: Timezone info
        filter_options: Optional filtering options
        **opts: Additional options
        
    Returns:
        GeoJSON FeatureCollection with Human Design features
    """
    try:
        hd_layer = HumanDesignLayer(birth_dt, lat, lon, tzinfo, **opts)
        features = hd_layer.generate_all_features(filter_options)
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "layer_type": "HD_DESIGN",
                "birth_datetime": birth_dt.isoformat(),
                "design_datetime": hd_layer.design_dt.isoformat(),
                "total_features": len(features)
            }
        }
    except Exception as e:
        print(f"[HD] Error in Human Design calculation: {e}")
        import traceback
        traceback.print_exc()
        return {
            "type": "FeatureCollection",
            "features": [],
            "error": str(e)
        }


# Main entry point for testing
if __name__ == "__main__":
    # Test with known birth date
    test_birth = _dt.datetime(1977, 6, 17, 3, 30, 0)  # June 17, 1977 03:30 UTC
    test_lat, test_lon = 40.7128, -74.0060  # New York
    
    print("Testing Human Design Layer...")
    print(f"Birth: {test_birth}")
    
    hd_layer = HumanDesignLayer(test_birth, test_lat, test_lon, "UTC")
    print(f"Design: {hd_layer.design_dt}")
    print(f"Design is {(test_birth - hd_layer.design_dt).days} days before birth")
    
    # Test feature generation
    result = calculate_human_design_layer(test_birth, test_lat, test_lon, "UTC")
    print(f"Generated {len(result['features'])} features")

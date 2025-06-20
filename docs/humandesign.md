# Human Design Layer Documentation

## Overview

The Human Design layer implements the Human Design system's approach to astrocartography, which uses a "Design" chart calculated based on a specific solar arc measurement from the birth time.

## Algorithm

### The 88° Solar Arc Rule

Human Design calculates the Design chart by finding the moment when the Sun was exactly 88° of longitude before its position at birth. This creates a secondary chart that represents the unconscious or "Design" aspect of a person's chart.

**Implementation Details:**
- Uses iterative calculation to find the precise moment when the Sun was 88° before birth
- Typically occurs approximately 88 days before birth, but varies based on solar motion
- Precision target: within 0.0001° of the exact 88° arc
- Maximum iterations: 20 (typically converges in 3-5 iterations)

### Mathematical Approach

1. **Initial Estimate**: Start with birth time minus 88 days
2. **Solar Position Calculation**: Calculate Sun's position at estimated Design time
3. **Arc Measurement**: Measure the arc between Design Sun and Birth Sun positions
4. **Convergence Check**: If arc differs from 88° by more than tolerance, adjust estimate
5. **Iteration**: Repeat until convergence or maximum iterations reached

## Features Generated

The Human Design layer generates the same astrocartography features as the Natal layer, with these exceptions:

### Included Features
- **Planet Lines**: AC/DC and IC/MC lines for all planets and asteroids
- **Aspect Lines**: Planet-to-angle aspects (unlike CCG and Transit layers)
- **Parans**: Planetary parans based on Design chart positions
- **Hermetic Lots**: Arabic parts calculated from Design chart

### Excluded Features
- **Fixed Stars**: Human Design traditionally doesn't use fixed stars

## API Usage

### Request Format
```json
{
  "birth_date": "1990-01-15",
  "birth_time": "12:00",
  "timezone": "UTC",
  "coordinates": [0.0, 51.5],
  "house_system": "whole_sign",
  "use_extended_planets": true,
  "filter_options": {
    "layer_type": "HD_DESIGN",
    "include_parans": true,
    "include_ac_dc": true,
    "include_ic_mc": true,
    "include_aspects": true,
    "include_fixed_stars": false,
    "include_hermetic_lots": true
  }
}
```

### Response Format
```json
{
  "type": "FeatureCollection",
  "features": [...],
  "metadata": {
    "layer_type": "HD_DESIGN",
    "birth_datetime": "1990-01-15T12:00:00+00:00",
    "design_datetime": "1989-10-19T06:23:42.123456+00:00",
    "algorithm": "88_degree_solar_arc",
    "iterations": 4,
    "precision_achieved": 0.000023,
    "days_difference": 87.234567
  }
}
```

## Caching

The Human Design calculation supports Redis caching to improve performance:

### Cache Key Format
```
hd_design:{birth_datetime_utc}:{lat}:{lon}
```

### Cache Duration
- **Default**: 24 hours (86400 seconds)
- **Configurable**: Via `REDIS_CACHE_TTL` environment variable

### Cache Content
- Complete Design datetime calculation result
- Used to avoid expensive iterative calculations for repeated requests

## Frontend Integration

### Layer Registration
```javascript
layerManager.addLayer('HD_DESIGN', {
  visible: false,
  order: 2,
  type: 'overlay',
  style: { color: '#D47AFF', width: 3, opacity: 0.85 },
  subLayers: { 
    ac_dc: true, 
    ic_mc: true, 
    parans: true, 
    lots: true,
    aspects: true 
  }
});
```

### Color Scheme
- **Primary Color**: `#D47AFF` (Purple)
- **Secondary Colors**: Various purple shades for different feature types
- **CSS Variables**: `--hd-color-*` for consistent theming

### Controls
- **Layer Toggle**: Show/hide entire HD layer
- **Feature Toggles**: Individual controls for IC/MC, AC/DC, parans, aspects, lots
- **Body Toggles**: Individual planet/asteroid enable/disable
- **Generate Button**: Trigger HD calculation

## Error Handling

### Common Errors
1. **Ephemeris File Missing**: Graceful fallback with clear error message
2. **Invalid Birth Data**: Validation before calculation
3. **Convergence Failure**: Fallback to best estimate with warning
4. **Redis Connection**: Optional caching with fallback to direct calculation

### Error Response Format
```json
{
  "error": "Calculation failed",
  "details": "SwissEph file 'seas_18.se1' not found",
  "layer_type": "HD_DESIGN"
}
```

## Testing

### Test Coverage
- Design datetime calculation accuracy
- Feature generation completeness
- Layer tagging and naming
- Integration with existing systems

### Test Files
- `tests/test_humandesign.py`: Core algorithm tests
- Backend integration tests within existing test suite

## Performance Considerations

### Calculation Time
- **First Run**: ~2-5 seconds (iterative solar arc calculation)
- **Cached**: ~50-100ms (Redis lookup)
- **Feature Generation**: Similar to Natal layer

### Memory Usage
- Minimal additional memory overhead
- Feature data comparable to other layers
- Optional Redis caching reduces repeated calculations

## Future Enhancements

### Potential Improvements
1. **Advanced Caching**: Pre-calculate common birth date ranges
2. **Parallel Processing**: Concurrent feature generation
3. **Additional Algorithms**: Alternative HD calculation methods
4. **Export Features**: HD-specific chart export formats
5. **Educational Content**: In-app explanations of HD principles

## References

- Human Design System documentation
- Swiss Ephemeris documentation
- Astrocartography calculation methods
- Solar arc progression techniques

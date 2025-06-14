/**
 * Map utilities for astrocartography line wrapping and display
 */

/**
 * Wraps astrocartography lines around the dateline for continuous display
 * @param {Object} geojsonData - The GeoJSON feature collection
 * @returns {Object} - Modified GeoJSON with wrapped lines
 */
export function wrapAstroLines(geojsonData) {
  if (!geojsonData || !geojsonData.features) {
    return geojsonData;
  }

  const wrappedFeatures = [];

  geojsonData.features.forEach(feature => {
    const lineType = feature.properties?.line_type;
    const category = feature.properties?.category;

    // MC/IC lines are already vertical meridians - no need to wrap
    if (lineType === 'MC' || lineType === 'IC') {
      wrappedFeatures.push(feature);
      return;
    }

    // For AC/DC horizon lines and aspect lines, create wrapped versions
    if (lineType === 'HORIZON' || category === 'aspect') {
      // Add original line
      wrappedFeatures.push(feature);

      // Create wrapped versions at ±360°
      const wrappedEast = createWrappedLine(feature, 360);
      const wrappedWest = createWrappedLine(feature, -360);
      
      if (wrappedEast) wrappedFeatures.push(wrappedEast);
      if (wrappedWest) wrappedFeatures.push(wrappedWest);
    } else {
      // For other features (fixed stars, etc.), just add as-is
      wrappedFeatures.push(feature);
    }
  });

  return {
    ...geojsonData,
    features: wrappedFeatures
  };
}

/**
 * Creates a wrapped version of a line feature at a longitude offset
 * @param {Object} feature - Original GeoJSON feature
 * @param {number} lonOffset - Longitude offset (±360)
 * @returns {Object} - Wrapped feature or null if not applicable
 */
function createWrappedLine(feature, lonOffset) {
  if (!feature.geometry) return null;

  let wrappedGeometry;

  if (feature.geometry.type === 'LineString') {
    wrappedGeometry = {
      type: 'LineString',
      coordinates: feature.geometry.coordinates.map(coord => [
        coord[0] + lonOffset,
        coord[1]
      ])
    };
  } else if (feature.geometry.type === 'MultiLineString') {
    wrappedGeometry = {
      type: 'MultiLineString',
      coordinates: feature.geometry.coordinates.map(lineString =>
        lineString.map(coord => [
          coord[0] + lonOffset,
          coord[1]
        ])
      )
    };
  } else {
    return null; // Don't wrap non-line geometries
  }

  return {
    ...feature,
    geometry: wrappedGeometry,
    properties: {
      ...feature.properties,
      wrapped: true,
      wrapOffset: lonOffset
    }
  };
}

/**
 * Ensures AC/DC horizon lines wrap smoothly across the dateline
 * @param {Object} feature - Horizon line feature
 * @returns {Array} - Array of line segments that wrap properly
 */
export function processHorizonLine(feature) {
  if (feature.properties?.line_type !== 'HORIZON') {
    return [feature];
  }

  const segments = [];
  const coords = feature.geometry.coordinates;
  
  // Split line at dateline crossings
  let currentSegment = [];
  
  for (let i = 0; i < coords.length; i++) {
    const [lon, lat] = coords[i];
    
    if (i > 0) {
      const [prevLon] = coords[i - 1];
      const lonDiff = Math.abs(lon - prevLon);
      
      // If longitude jumps more than 180°, we've crossed the dateline
      if (lonDiff > 180) {
        // Finish current segment
        if (currentSegment.length > 1) {
          segments.push(createSegmentFeature(feature, currentSegment));
        }
        // Start new segment
        currentSegment = [];
      }
    }
    
    currentSegment.push([lon, lat]);
  }
  
  // Add final segment
  if (currentSegment.length > 1) {
    segments.push(createSegmentFeature(feature, currentSegment));
  }
  
  return segments;
}

/**
 * Creates a feature from a coordinate segment
 */
function createSegmentFeature(originalFeature, coordinates) {
  return {
    ...originalFeature,
    geometry: {
      type: 'LineString',
      coordinates: coordinates
    }
  };
}

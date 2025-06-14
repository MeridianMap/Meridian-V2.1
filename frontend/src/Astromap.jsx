import React from "react";
import { MapContainer, TileLayer, Polyline, Tooltip, Circle } from "react-leaflet";
import "./astromap.css";

// Map of planet colors (fallback)
const planetColors = {
  "Sun": "gold", "Moon": "silver", "Mercury": "purple", "Venus": "green",
  "Mars": "red", "Jupiter": "orange", "Saturn": "gray", "Uranus": "teal",
  "Neptune": "blue", "Pluto": "black", "North Node": "brown", "South Node": "darkred"
};

// Helper function to get line styling based on layer
const getLineStyle = (feature) => {
  const planet = feature.properties.planet;
  const baseColor = planetColors[planet] || "magenta";
  const layerName = feature.layerName || 'natal';
  const layerStyle = feature.layerStyle || {};
  
  if (layerName === 'transit') {
    // All transit lines use the same color, 3px width, 60% opacity
    return {
      color: "#4A90E2", // Consistent blue color for all transit lines
      weight: 3,
      opacity: 0.6
    };
  } else {
    // Natal layer (default) - use planet-specific colors
    return {
      color: baseColor,
      weight: layerStyle.width || 2,
      opacity: layerStyle.opacity || 1.0
    };
  }
};

const AstroMap = ({ data, paransData }) => {
  // Debug logging
  console.log('AstroMap render - data features:', data?.features?.length || 0);
  console.log('AstroMap render - transit features:', data?.features?.filter(f => f.layerName === 'transit')?.length || 0);
  
  // Merge features from astrocartography and parans (if present)
  const mergedFeatures = React.useMemo(() => {
    if (!data?.features?.length && !paransData?.features?.length) return [];
    const astroFeatures = data?.features || [];
    const paranFeatures = paransData?.features || [];
    const merged = [...astroFeatures, ...paranFeatures];
    console.log('AstroMap useMemo - merged features:', merged.length);
    return merged;  }, [data, paransData]);
  
  console.log('AstroMap render - data:', data);
  console.log('AstroMap render - mergedFeatures:', mergedFeatures.length);
  
  // Show map even if no features - just empty map
  if (!data) return <div>Loading astrocartography data…</div>;

  return (
    <div className="astromap-wrapper">
      {/* Accordion button for JSON output - removed, now handled in App.jsx */}
      {/*
      <div style={{ margin: '12px 0' }}>
        <button
          onClick={() => setShowJson((v) => !v)}
          style={{
            padding: '6px 14px',
            borderRadius: 4,
            border: '1px solid #aaa',
            background: '#222', // Changed to dark background
            color: '#fff', // Ensure text is white
            fontWeight: 600,
            cursor: 'pointer',
            marginBottom: 6,
          }}
        >
          {showJson ? 'Hide' : 'Show'} Astrocartography JSON Output
        </button>
        {showJson && (
          <pre
            style={{
              maxHeight: 400,
              overflow: 'auto',
              background: '#222',
              color: '#fff',
              padding: 12,
              borderRadius: 4,
              fontSize: 13,
              marginTop: 0,
            }}
          >
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </div>
      */}
      <MapContainer
        className="leaflet-container"
        center={[0, 0]}
        zoom={2}
        minZoom={2}
        scrollWheelZoom={true}
        worldCopyJump={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
          subdomains={["a", "b", "c", "d"]}
          attribution="© OpenStreetMap contributors © CARTO"
        />        {mergedFeatures.map((feat, idx) => {
          // Debug: print all feature properties to understand structure
          if (idx < 5) { // Only log first 5 features to avoid spam
            console.log(`Feature ${idx}:`, {
              geometry_type: feat.geometry.type,
              line_type: feat.properties?.line_type,
              category: feat.properties?.category,
              type: feat.properties?.type,
              planet: feat.properties?.planet,
              all_properties: feat.properties
            });
          }
          
          // Debug: print MC/IC line longitudes for North/South Node
          if ((feat.properties.planet === "North Node" || feat.properties.planet === "South Node") && (feat.properties.line_type === "MC" || feat.properties.line_type === "IC")) {
            const coords = feat.geometry.coordinates;
            const lon = coords[0][0];
            // Enhanced debug: print all coordinates and properties
            console.log(`DEBUG: ${feat.properties.planet} ${feat.properties.line_type} properties:`, feat.properties);
            console.log(`DEBUG: ${feat.properties.planet} ${feat.properties.line_type} coordinates:`, coords);
            console.log(`DEBUG: ${feat.properties.planet} ${feat.properties.line_type} first longitude:`, lon);
          }          if (feat.geometry.type === "LineString" && (feat.properties.line_type === "MC" || feat.properties.line_type === "IC")) {
            // Render MC/IC vertical lines
            const coords = feat.geometry.coordinates;
            const planet = feat.properties.planet;
            const label = `${planet} ${feat.properties.line_type}`;
            return [0, 360, -360].flatMap(offset => [
              // Invisible hover capture line (wider)
              <Polyline
                key={`mcic-hover-${idx}-${offset}`}
                positions={coords.map(([lon, lat]) => [lat, lon + offset])}
                pathOptions={{ 
                  color: "transparent", 
                  weight: 12, // Much wider for easier hover
                  opacity: 0,
                  fillOpacity: 0
                }}
                smoothFactor={1}
              >
                <Tooltip sticky>{label}</Tooltip>
              </Polyline>,              // Visible line (normal thickness)
              <Polyline
                key={`mcic-${idx}-${offset}`}
                positions={coords.map(([lon, lat]) => [lat, lon + offset])}
                pathOptions={{ 
                  ...getLineStyle(feat),
                  interactive: false // Prevent this line from capturing events
                }}
                smoothFactor={1}
              />
            ]);
          }
          // Removed duplicate rendering for parans lines by type
          // else if (feat.geometry.type === "LineString" && feat.properties.type === "paran") {
          //   const rawCoords = feat.geometry.coordinates;
          //   let planet = feat.properties.planet;
          //   if (typeof planet === 'string') planet = planet.trim();
          //   const color = "purple"; // or any color you want for parans
          //   const weight = 4;
          //   const dashArray = "6 6";
          //   const label = `${planet} Paran (${feat.properties.event})`;
          //   return [0, 360, -360].map((offset) => (
          //     <Polyline
          //       key={`paran-${idx}-${offset}`}
          //       positions={rawCoords.map(([lon, lat]) => [lat, lon + offset])}
          //       color={color}
          //       weight={weight}
          //       dashArray={dashArray}
          //       smoothFactor={1}
          //     >
          //       <Tooltip sticky>{label}</Tooltip>
          //     </Polyline>
          //   ));
          // }
          else if (
            (feat.geometry.type === "LineString" || feat.geometry.type === "MultiLineString") &&
            feat.properties.line_type === "HORIZON"
          ) {
            // Handle both LineString and MultiLineString for horizon lines
            const segments = feat.geometry.type === "LineString"
              ? [feat.geometry.coordinates]
              : feat.geometry.coordinates;
            const planet = feat.properties.planet;
            const segLabels = feat.properties.segments || [];
              // Render each segment with wrapping at ±360° longitude
            return segments.flatMap((coords, segIdx) => {
              if (!coords || coords.length < 2) return [];
              let label = planet;
              if (segLabels.length === 2) {
                const segLabel = segLabels[segIdx]?.label;
                if (segLabel) label = `${planet} ${segLabel}`;
              }
              
              // Create wrapped versions for continuous display
              return [-360, 0, 360].flatMap(offset => [
                // Invisible hover capture line (wider)
                <Polyline
                  key={`horizon-hover-${idx}-${segIdx}-${offset}`}
                  positions={coords.map(([lon, lat]) => [lat, lon + offset])}
                  pathOptions={{ 
                    color: "transparent", 
                    weight: 12, // Much wider for easier hover
                    opacity: 0,
                    fillOpacity: 0
                  }}
                  smoothFactor={1}
                >
                  <Tooltip sticky>{label}</Tooltip>
                </Polyline>,                // Visible line (normal thickness)
                <Polyline
                  key={`horizon-${idx}-${segIdx}-${offset}`}
                  positions={coords.map(([lon, lat]) => [lat, lon + offset])}
                  pathOptions={{ 
                    ...getLineStyle(feat),
                    interactive: false // Prevent this line from capturing events
                  }}
                  smoothFactor={1}
                />
              ]);
            });
          } else if (
            (feat.geometry.type === "LineString" || feat.geometry.type === "MultiLineString") &&
            feat.properties.line_type === "ASPECT"
          ) {
            // Handle both LineString and MultiLineString for aspect lines
            const segments = feat.geometry.type === "LineString"
              ? [feat.geometry.coordinates]
              : feat.geometry.coordinates;            const lineStyle = getLineStyle(feat);
            const label = feat.properties.label;
              // Render each segment with wrapping at ±360° longitude
            return segments.flatMap((coords, segIdx) => {
              if (!coords || coords.length < 2) return [];
              
              // Create wrapped versions for continuous display
              return [-360, 0, 360].flatMap(offset => [
                // Invisible hover capture line (wider)
                <Polyline
                  key={`aspect-hover-${idx}-${segIdx}-${offset}`}
                  positions={coords.map(([lon, lat]) => [lat, lon + offset])}
                  pathOptions={{ 
                    color: "transparent", 
                    weight: 12, // Much wider for easier hover
                    opacity: 0,
                    fillOpacity: 0
                  }}
                  smoothFactor={1}
                >
                  <Tooltip sticky>{label}</Tooltip>
                </Polyline>,                // Visible line (normal thickness)
                <Polyline
                  key={`aspect-${idx}-${segIdx}-${offset}`}
                  positions={coords.map(([lon, lat]) => [lat, lon + offset])}
                  pathOptions={{ 
                    ...lineStyle,
                    dashArray: "4 4",
                    interactive: false // Prevent this line from capturing events
                  }}
                  smoothFactor={1}
                />
              ]);
            });
          } else if (feat.geometry.type === "LineString" && feat.properties.type === "crossing_latitude") {
            // Render horizontal parans lines with backend label
            const rawCoords = feat.geometry.coordinates;            // Use consistent styling for transit parans
            const lineStyle = getLineStyle(feat);
            const color = lineStyle.color;
            const weight = lineStyle.weight;
            const opacity = lineStyle.opacity;
            // Use dotted pattern for parans to distinguish from solid lines
            const dashArray = feat.layerName === 'transit' ? "8 4" : "1 6";const label = feat.properties.label || "Paran crossing";
            return [0, 360, -360].flatMap((offset) => [
              // Invisible hover capture line (wider)
              <Polyline
                key={`paran-hover-${idx}-${offset}`}
                positions={rawCoords.map(([lon, lat]) => [lat, lon + offset])}
                pathOptions={{
                  color: "transparent",
                  weight: 12, // Much wider for easier hover
                  opacity: 0,
                  fillOpacity: 0
                }}
                smoothFactor={1}
              >
                <Tooltip sticky>{label}</Tooltip>
              </Polyline>,
              // Visible line (normal thickness)
              <Polyline
                key={`paran-${idx}-${offset}`}
                positions={rawCoords.map(([lon, lat]) => [lat, lon + offset])}                pathOptions={{
                  color,
                  weight,
                  opacity,
                  dashArray,
                  interactive: false // Prevent this line from capturing events
                }}
                smoothFactor={1}
              />
            ]);
          } else if (feat.geometry.type === "LineString") {
            const rawCoords = feat.geometry.coordinates;
            let planet = feat.properties.planet;
            // Remove color/weight from this block to avoid undefined errors
            const dashArray = null;
            // --- PATCH: Split AC/DC segments visually ---
            const acdc = feat.properties.ac_dc_indices;
            let ac_end = acdc ? acdc.ac_end : null;
            let dc_start = acdc ? acdc.dc_start : null;
            let ac_coords = rawCoords;
            let dc_coords = [];
            if (ac_end !== null && dc_start !== null) {
              ac_coords = rawCoords.slice(0, ac_end + 1);
              dc_coords = rawCoords.slice(dc_start);
            }            const acLabel = `${planet} AC`;
            const dcLabel = `${planet} DC`;
            // Draw each segment with wraps at ±360° longitude
            return [0, 360, -360].flatMap((offset) => [
              // AC segment - invisible hover capture line
              ac_coords.length > 1 && (
                <Polyline
                  key={`ac-hover-${idx}-${offset}`}
                  positions={ac_coords.map(([lon, lat]) => [lat, lon + offset])}
                  pathOptions={{ 
                    color: "transparent", 
                    weight: 12, // Much wider for easier hover
                    opacity: 0,
                    fillOpacity: 0
                  }}
                  smoothFactor={1}
                >
                  <Tooltip sticky>{acLabel}</Tooltip>
                </Polyline>
              ),              // AC segment - visible line
              ac_coords.length > 1 && (
                <Polyline
                  key={`ac-${idx}-${offset}`}
                  positions={ac_coords.map(([lon, lat]) => [lat, lon + offset])}
                  pathOptions={{ 
                    ...getLineStyle(feat),
                    interactive: false // Prevent this line from capturing events
                  }}
                  dashArray={dashArray}
                  smoothFactor={1}
                />
              ),
              // DC segment - invisible hover capture line
              dc_coords.length > 1 && (
                <Polyline
                  key={`dc-hover-${idx}-${offset}`}
                  positions={dc_coords.map(([lon, lat]) => [lat, lon + offset])}
                  pathOptions={{ 
                    color: "transparent", 
                    weight: 12, // Much wider for easier hover
                    opacity: 0,
                    fillOpacity: 0
                  }}
                  smoothFactor={1}
                >
                  <Tooltip sticky>{dcLabel}</Tooltip>
                </Polyline>
              ),              // DC segment - visible line
              dc_coords.length > 1 && (
                <Polyline
                  key={`dc-${idx}-${offset}`}
                  positions={dc_coords.map(([lon, lat]) => [lat, lon + offset])}
                  pathOptions={{ 
                    ...getLineStyle(feat),
                    interactive: false // Prevent this line from capturing events
                  }}
                  dashArray={dashArray}
                  smoothFactor={1}
                />
              )
            ].filter(Boolean));
          } else if (feat.geometry.type === "Point" && feat.properties.type === "fixed_star") {
            // Render fixed star as a circle with 50 mile radius (approx 80.47 km)
            const [lon, lat] = feat.geometry.coordinates;
            return [-360, 0, 360].map(offset => (
              <Circle
                key={`star-${idx}-${offset}`}
                center={[lat, lon + offset]}
                radius={80467} // 50 miles in meters
                pathOptions={{ color: "#e6b800", fillColor: "#fffbe6", fillOpacity: 0.5 }}
              >
                <Tooltip sticky>
                  <b>{feat.properties.star}</b>
                  {feat.properties.magnitude !== undefined && (
                    <span> (mag {feat.properties.magnitude.toFixed(2)})</span>
                  )}
                </Tooltip>
              </Circle>
            ));
          }
          return null;
        })}
      </MapContainer>
    </div>
  );
};

export default AstroMap;

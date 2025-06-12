import React from "react";
import { MapContainer, TileLayer, Polyline, Tooltip, Circle } from "react-leaflet";
import "./astromap.css";

// Map of planet colors (fallback)
const planetColors = {
  "Sun": "gold", "Moon": "silver", "Mercury": "purple", "Venus": "green",
  "Mars": "red", "Jupiter": "orange", "Saturn": "gray", "Uranus": "teal",
  "Neptune": "blue", "Pluto": "black", "North Node": "brown", "South Node": "darkred"
};

// Axis abbreviations
const axisLabels = {
  ASC: "AC",
  DSC: "DC",
  MC: "MC",
  IC: "IC",
};

const AstroMap = ({ data, paransData }) => {
  // Merge features from astrocartography and parans (if present)
  const mergedFeatures = React.useMemo(() => {
    if (!data?.features?.length && !paransData?.features?.length) return [];
    const astroFeatures = data?.features || [];
    const paranFeatures = paransData?.features || [];
    return [...astroFeatures, ...paranFeatures];
  }, [data, paransData]);
  if (!mergedFeatures.length) return <div>Loading astrocartography data…</div>;

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
        />

        {mergedFeatures.map((feat, idx) => {
          // Debug: print MC/IC line longitudes for North/South Node
          if ((feat.properties.planet === "North Node" || feat.properties.planet === "South Node") && (feat.properties.line_type === "MC" || feat.properties.line_type === "IC")) {
            const coords = feat.geometry.coordinates;
            const lon = coords[0][0];
            // Enhanced debug: print all coordinates and properties
            console.log(`DEBUG: ${feat.properties.planet} ${feat.properties.line_type} properties:`, feat.properties);
            console.log(`DEBUG: ${feat.properties.planet} ${feat.properties.line_type} coordinates:`, coords);
            console.log(`DEBUG: ${feat.properties.planet} ${feat.properties.line_type} first longitude:`, lon);
          }
          if (feat.geometry.type === "LineString" && (feat.properties.line_type === "MC" || feat.properties.line_type === "IC")) {
            // Render MC/IC vertical lines
            const coords = feat.geometry.coordinates;
            const planet = feat.properties.planet;
            const label = `${planet} ${feat.properties.line_type}`;
            return [0, 360, -360].map(offset => (
              <Polyline
                key={`mcic-${idx}-${offset}`}
                positions={coords.map(([lon, lat]) => [lat, lon + offset])}
                pathOptions={{ color: planetColors[planet] || "magenta", weight: 3 }}
                smoothFactor={1}
              >
                <Tooltip sticky>{label}</Tooltip>
              </Polyline>
            ));
          } else if (feat.geometry.type === "LineString" && feat.properties.type === "paran") {
            // Render horizontal paran lines
            const rawCoords = feat.geometry.coordinates;
            let planet = feat.properties.planet;
            if (typeof planet === 'string') planet = planet.trim();
            const color = "purple"; // or any color you want for parans
            const weight = 4;
            const dashArray = "6 6";
            const label = `${planet} Paran (${feat.properties.event})`;
            return [0, 360, -360].map((offset) => (
              <Polyline
                key={`paran-${idx}-${offset}`}
                positions={rawCoords.map(([lon, lat]) => [lat, lon + offset])}
                color={color}
                weight={weight}
                dashArray={dashArray}
                smoothFactor={1}
              >
                <Tooltip sticky>{label}</Tooltip>
              </Polyline>
            ));
          } else if (
            (feat.geometry.type === "LineString" || feat.geometry.type === "MultiLineString") &&
            feat.properties.line_type === "HORIZON"
          ) {
            // Handle both LineString and MultiLineString for horizon lines
            const segments = feat.geometry.type === "LineString"
              ? [feat.geometry.coordinates]
              : feat.geometry.coordinates;
            const planet = feat.properties.planet;
            // Move color/weight inside map to avoid scope issues
            const segLabels = feat.properties.segments || [];
            // Render each segment, coloring and labeling by AC/DC
            return segments.map((coords, segIdx) => {
              if (!coords || coords.length < 2) return null;
              let label = planet;
              if (segLabels.length === 2) {
                const segLabel = segLabels[segIdx]?.label;
                if (segLabel) label = `${planet} ${segLabel}`;
              }
              // Use pathOptions for Polyline styling (react-leaflet v3+)
              return (
                <Polyline
                  key={`horizon-${idx}-${segIdx}`}
                  positions={coords.map(([lon, lat]) => [lat, lon])}
                  pathOptions={{ color: planetColors[planet] || "magenta", weight: 3 }}
                  smoothFactor={1}
                >
                  <Tooltip sticky>{label}</Tooltip>
                </Polyline>
              );
            });
          } else if (
            (feat.geometry.type === "LineString" || feat.geometry.type === "MultiLineString") &&
            feat.properties.line_type === "ASPECT"
          ) {
            // Handle both LineString and MultiLineString for aspect lines
            const segments = feat.geometry.type === "LineString"
              ? [feat.geometry.coordinates]
              : feat.geometry.coordinates;
            const planet = feat.properties.planet;
            const color = planetColors[planet] || "magenta";
            const label = feat.properties.label;
            return segments.map((coords, segIdx) => (
              <Polyline
                key={`aspect-${idx}-${segIdx}`}
                positions={coords.map(([lon, lat]) => [lat, lon])}
                pathOptions={{ color, weight: 2, dashArray: "4 4" }}
                smoothFactor={1}
              >
                <Tooltip sticky>{label}</Tooltip>
              </Polyline>
            ));
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
            }
            const acLabel = `${planet} AC`;
            const dcLabel = `${planet} DC`;
            // Draw each segment with wraps at ±360° longitude
            return [0, 360, -360].flatMap((offset) => [
              ac_coords.length > 1 && (
                <Polyline
                  key={`ac-${idx}-${offset}`}
                  positions={ac_coords.map(([lon, lat]) => [lat, lon + offset])}
                  pathOptions={{ color: planetColors[planet] || "magenta", weight: 3 }}
                  dashArray={dashArray}
                  smoothFactor={1}
                >
                  <Tooltip sticky>{acLabel}</Tooltip>
                </Polyline>
              ),
              dc_coords.length > 1 && (
                <Polyline
                  key={`dc-${idx}-${offset}`}
                  positions={dc_coords.map(([lon, lat]) => [lat, lon + offset])}
                  pathOptions={{ color: planetColors[planet] || "magenta", weight: 3 }}
                  dashArray={dashArray}
                  smoothFactor={1}
                >
                  <Tooltip sticky>{dcLabel}</Tooltip>
                </Polyline>
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

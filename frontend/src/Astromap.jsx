import React from "react";
import { MapContainer, TileLayer, Polyline, Tooltip, Circle } from "react-leaflet";
import "./astromap.css";

// Map of planet colors (fallback)
const planetColors = {
  "Sun": "gold", "Moon": "silver", "Mercury": "purple", "Venus": "green",
  "Mars": "red", "Jupiter": "orange", "Saturn": "gray", "Uranus": "teal",
  "Neptune": "blue", "Pluto": "black", "North Node": "brown"
};

// Axis abbreviations
const axisLabels = {
  ASC: "AC",
  DSC: "DC",
  MC: "MC",
  IC: "IC",
};

const AstroMap = ({ data, paransData }) => {
  const [showJson, setShowJson] = React.useState(false);
  // Merge features from astrocartography and parans (if present)
  const mergedFeatures = React.useMemo(() => {
    if (!data?.features?.length && !paransData?.features?.length) return [];
    const astroFeatures = data?.features || [];
    const paranFeatures = paransData?.features || [];
    return [...astroFeatures, ...paranFeatures];
  }, [data, paransData]);
  if (!mergedFeatures.length) return <div>Loading astrocartography data…</div>;

  // Wrap raw [lon, lat] coords into Leaflet [lat, lon+offset], clamp lon to [-180, 180]
  const wrapCoords = (coords, offset) =>
    coords.map(([lon, lat]) => {
      let wrappedLon = lon + offset;
      // Clamp longitude to [-180, 180]
      if (wrappedLon > 180) wrappedLon -= 360;
      if (wrappedLon < -180) wrappedLon += 360;
      return [lat, wrappedLon];
    });

  return (
    <div className="astromap-wrapper">
      {/* Accordion button for JSON output */}
      <div style={{ margin: '12px 0' }}>
        <button
          onClick={() => setShowJson((v) => !v)}
          style={{
            padding: '6px 14px',
            borderRadius: 4,
            border: '1px solid #aaa',
            background: '#f7f7f7',
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
      <MapContainer
        className="leaflet-container"
        center={[0, 0]}
        zoom={2}
        scrollWheelZoom={true}
        worldCopyJump={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
          subdomains={["a", "b", "c", "d"]}
          attribution="© OpenStreetMap contributors © CARTO"
        />

        {mergedFeatures.map((feat, idx) => {
          if (feat.geometry.type === "LineString" && feat.properties.type === "paran") {
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
          } else if (feat.geometry.type === "LineString") {
            const rawCoords = feat.geometry.coordinates;
            let planet = feat.properties.planet;
            const axis = feat.properties.line_type;
            if (typeof planet === 'string') planet = planet.trim();
            const color = planetColors[planet] || "magenta";
            const weight = 3;
            const dashArray = null;
            const label = `${planet} ${axisLabels[axis] || axis}`;
            // Draw each line with wraps at ±360° longitude
            return [0, 360, -360].map((offset) => (
              <Polyline
                key={`${idx}-${offset}`}
                positions={rawCoords.map(([lon, lat]) => [lat, lon + offset])}
                color={color}
                weight={weight}
                dashArray={dashArray}
                smoothFactor={1}
              >
                <Tooltip sticky>{label}</Tooltip>
              </Polyline>
            ));
          } else if (feat.geometry.type === "Point" && feat.properties.type === "fixed_star") {
            // Render fixed star as a circle with 50 mile radius (approx 80.47 km)
            const [lon, lat] = feat.geometry.coordinates;
            return (
              <Circle
                key={`star-${idx}`}
                center={[lat, lon]}
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
            );
          }
          return null;
        })}
      </MapContainer>
    </div>
  );
};

export default AstroMap;

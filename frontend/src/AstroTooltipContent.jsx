import React from "react";
import definitions from "./astro_definitions.json";

function normalizeLabelPart(part) {
  if (!part) return part;
  // Always coerce to string before trim
  const str = String(part);
  if (str === "ASC") return "AC";
  if (str === "DSC") return "DC";
  if (str === "IC") return "IC";
  if (str === "MC") return "MC";
  return str.trim();
}

function getFullDef(part) {
  if (!part) return null;
  const key = normalizeLabelPart(part);
  return (
    getDef("planets", key) ||
    getDef("asteroids", key) ||
    getDef("lunarPoints", key) ||
    getDef("hermeticLots", key) ||
    getDef("angles", key) ||
    getDef("aspects", key) ||
    getDef("aspectLines", key) ||
    getDef("fixedStars", key) ||
    null
  );
}

function getDef(type, key) {
  if (!key) return null;
  return definitions[type] && definitions[type][key] ? definitions[type][key] : null;
}

const renderDefLine = (label, def) => (
  <div style={{ marginBottom: 2 }}>
    <b>{label}</b>
    {def && <span style={{ fontStyle: "italic", color: "#888", marginLeft: 4 }}>– {def}</span>}
  </div>
);

function parseLabel(label) {
  if (!label) return [];
  let clean = label.replace(/\s*\(.*\)$/, "").trim();
  const aspects = ["conjunct", "opposite", "square", "trine", "sextile", "quincunx"];
  let parts = clean.split(" ");
  if (parts.length === 3 && aspects.includes(parts[1])) {
    return [parts[0], parts[1], parts[2]];
  }
  return parts;
}

// --- Helper to extract the best id for house/sign lookup ---
function getFeatureId(feat) {
  if (!feat || !feat.properties) return null;
  const p = feat.properties;
  return (
    p.planet_id ||
    p.body_key ||
    p.star_id ||
    p.star_key ||
    p.body ||
    p.planet ||
    p.star ||
    p.name ||
    null
  );
}

function capitalize(str) {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

function getOrdinalSuffix(num) {
  const j = num % 10;
  const k = num % 100;
  if (j === 1 && k !== 11) return `${num}st`;
  if (j === 2 && k !== 12) return `${num}nd`;
  if (j === 3 && k !== 13) return `${num}rd`;
  return `${num}th`;
}

const AstroTooltipContent = ({ feat, label }) => {
  if (!feat || !feat.properties) return <b>{label}</b>;
  const { planet, type, star, planets, angles } = feat.properties;
  const lines = [];

  // Main label
  lines.push(<div key="main" style={{ marginBottom: 4 }}><b>{label}</b></div>);
  const labelParts = parseLabel(label);
  const alreadyRendered = new Set();

  // --- Always try to render the definition for the feature id (for multi-word features, lots, etc.) ---
  const featureId = getFeatureId(feat);
  let idDefRendered = false;
  if (featureId && getFullDef(featureId) && !alreadyRendered.has(featureId)) {
    lines.push(renderDefLine(featureId, getFullDef(featureId)));
    alreadyRendered.add(featureId);
    idDefRendered = true;
  }
  // If id is not a string key in definitions, also try display name (planet/body/star)
  const displayName = feat.properties.planet || feat.properties.body || feat.properties.star || feat.properties.name;
  if (
    displayName &&
    (!idDefRendered || featureId !== displayName) &&
    getFullDef(displayName) &&
    !alreadyRendered.has(displayName)
  ) {
    lines.push(renderDefLine(displayName, getFullDef(displayName)));
    alreadyRendered.add(displayName);
  }

  // --- Aspect and multi-word logic ---
  if (labelParts.length >= 3) {
    const aspect = labelParts[labelParts.length - 2];
    const angle = labelParts[labelParts.length - 1];
    const bodyParts = labelParts.slice(0, labelParts.length - 2);
    const fullBody = bodyParts.join(" ");
    // Only render body definition if not already rendered
    if (bodyParts.length > 0 && getFullDef(fullBody) && !alreadyRendered.has(fullBody)) {
      lines.push(renderDefLine(fullBody, getFullDef(fullBody)));
      alreadyRendered.add(fullBody);
      bodyParts.forEach(part => alreadyRendered.add(part));
    } else if (bodyParts.length === 1 && getFullDef(bodyParts[0]) && !alreadyRendered.has(bodyParts[0])) {
      lines.push(renderDefLine(bodyParts[0], getFullDef(bodyParts[0])));
      alreadyRendered.add(bodyParts[0]);
    }
    // Aspect line
    const aspectLineKey = `${capitalize(aspect)} ${normalizeLabelPart(angle)}`;
    if (getDef("aspectLines", aspectLineKey) && !alreadyRendered.has(aspectLineKey)) {
      lines.push(renderDefLine(aspectLineKey, getDef("aspectLines", aspectLineKey)));
      alreadyRendered.add(aspectLineKey);
      alreadyRendered.add(aspect);
      alreadyRendered.add(angle);
    } else {
      if (!alreadyRendered.has(aspect) && getFullDef(aspect)) {
        lines.push(renderDefLine(aspect, getFullDef(aspect)));
        alreadyRendered.add(aspect);
      }
      if (!alreadyRendered.has(angle) && getFullDef(angle)) {
        lines.push(renderDefLine(angle, getFullDef(angle)));
        alreadyRendered.add(angle);
      }
    }
  } else {
    // Multi-word fallback
    for (let len = labelParts.length; len >= 2; len--) {
      for (let start = 0; start <= labelParts.length - len; start++) {
        const joined = labelParts.slice(start, start + len).join(" ");
        if (getFullDef(joined) && !alreadyRendered.has(joined)) {
          lines.push(renderDefLine(joined, getFullDef(joined)));
          alreadyRendered.add(joined);
          for (let k = start; k < start + len; k++) {
            alreadyRendered.add(labelParts[k]);
          }
        }
      }
    }
    labelParts.forEach((part) => {
      if (!alreadyRendered.has(part) && getFullDef(part)) {
        lines.push(renderDefLine(part, getFullDef(part)));
        alreadyRendered.add(part);
      }
    });
  }

  // --- Parans: show both planets and both angles, no duplicates ---
  if ((type === "paran" || feat.properties.category === "parans") && Array.isArray(feat.properties.source_lines)) {
    const sourceLines = feat.properties.source_lines;
    sourceLines.forEach(sourceLine => {
      if (sourceLine && sourceLine.includes("_")) {
        const planetName = sourceLine.split("_")[0].replace(/ (CCG|Transit|HD)$/g, "");
        if (planetName && getFullDef(planetName) && !alreadyRendered.has(planetName)) {
          lines.push(renderDefLine(planetName, getFullDef(planetName)));
          alreadyRendered.add(planetName);
        }
        const angleName = sourceLine.split("_")[1];
        if (angleName && getFullDef(angleName) && !alreadyRendered.has(angleName)) {
          lines.push(renderDefLine(angleName, getFullDef(angleName)));
          alreadyRendered.add(angleName);
        }
      }
    });
  } else if (type === "paran" && Array.isArray(planets)) {
    // fallback for old-style parans
    planets.forEach((p) => {
      if (p && getFullDef(p) && !alreadyRendered.has(p)) {
        lines.push(renderDefLine(p, getFullDef(p)));
        alreadyRendered.add(p);
      }
    });
    if (Array.isArray(angles)) {
      angles.forEach((a) => {
        if (a && getFullDef(a) && !alreadyRendered.has(a)) {
          lines.push(renderDefLine(a, getFullDef(a)));
          alreadyRendered.add(a);
        }      });
    }
  }
  
  // --- PARANS HUMAN DESIGN GATE BLOCK ---
  // Show Human Design gate info for planets involved in parans crossings
  if ((type === "paran" || feat.properties.category === "parans") && Array.isArray(feat.properties.source_lines)) {
    const sourceLines = feat.properties.source_lines;
    sourceLines.forEach(sourceLine => {
      if (sourceLine && sourceLine.includes("_")) {
        const planetName = sourceLine.split("_")[0].replace(/ (CCG|Transit|HD)$/g, "");
          // Look for Human Design gate info for this planet in the properties
        const gateKey = `${planetName}_hd_gate`;
        const gateNameKey = `${planetName}_hd_gate_name`;
        const lineKey = `${planetName}_hd_line`;
        
        if (feat.properties[gateKey]) {          const gateNumber = feat.properties[gateKey];
          const gateName = feat.properties[gateNameKey] || "";
          const lineNumber = feat.properties[lineKey] || "";
          
          const gateId = `${planetName}_gate_${gateNumber}`;
          if (!alreadyRendered.has(gateId)) {
            // Display gate info for this planet
            lines.push(
              renderDefLine(
                `${planetName} Gate ${gateNumber}${gateName ? ` (${gateName})` : ""}`,
                getDef("humanDesignGates", gateNumber.toString()) || ""
              )
            );
            alreadyRendered.add(gateId);
            
            // Display line info if available
            if (lineNumber) {
              const lineId = `${planetName}_line_${gateNumber}_${lineNumber}`;
              if (!alreadyRendered.has(lineId)) {
                lines.push(
                  renderDefLine(
                    `${planetName} Line ${lineNumber}`,
                    getDef("humanDesignLines", `${gateNumber}.${lineNumber}`) || ""
                  )
                );
                alreadyRendered.add(lineId);
              }
            }
          }
        }
      }
    });
  }
  
  // Fixed stars: always show definition
  if ((type === "fixed_star" || type === "star" || star)) {
    const starName = star || planet;
    if (starName && getFullDef(starName) && !alreadyRendered.has(starName)) {
      lines.push(renderDefLine(starName, getFullDef(starName)));
      alreadyRendered.add(starName);
    }
  }
  // --- UNIVERSAL HOUSE AND SIGN BLOCK ---
  // Always display house and sign if the feature has them, regardless of type
  if (feat.properties.house && feat.properties.sign) {
    const houseDef = getDef("houses", feat.properties.house.toString());
    const signDef = getDef("zodiacSigns", feat.properties.sign);

    if (houseDef) {
      lines.push(
        renderDefLine(
          `${getOrdinalSuffix(feat.properties.house)} house`,
          houseDef
        )
      );
    }
    if (signDef) {
      lines.push(renderDefLine(feat.properties.sign, signDef));
    }
  }
  // --- UNIVERSAL HUMAN DESIGN GATE BLOCK ---
  // Always display HD gate if the feature has it, regardless of type
  if (feat.properties.hd_gate) {
    const gateName = feat.properties.hd_gate_name || "";
    const gateNumber = feat.properties.hd_gate;
    const lineNumber = feat.properties.hd_line || "";
    
    // Display gate number and name
    lines.push(
      renderDefLine(
        `Gate ${gateNumber}${gateName ? ` (${gateName})` : ""}`,
        getDef("humanDesignGates", gateNumber.toString()) || ""
      )
    );
    
    // Display gate line if available
    if (lineNumber) {
      lines.push(
        renderDefLine(
          `Line ${lineNumber}`,
          getDef("humanDesignLines", `${gateNumber}.${lineNumber}`) || ""
        )
      );
    }
  }

  return <div>{lines}</div>;
};

export default AstroTooltipContent;

import React from 'react';

function CCGDisplayControls({
  lineToggles,
  setLineToggles,
  lineLabels,
  allBodies,
  bodyToggles,
  setBodyToggles,
  showBodyAccordion,
  setShowBodyAccordion
}) {
  return (
    <div className="filter-control-panel">
      <h3 style={{ color: '#fff', textAlign: 'center', margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>
        CCG Display Controls
      </h3>
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '0.4rem',
        justifyContent: 'center',
        marginBottom: '0.75rem'
      }}>
        {Object.entries(lineToggles)
          .filter(([key]) => lineLabels[key])
          .map(([key, value]) => (
            <label
              key={key}
              className={`category-toggle ${value ? 'active' : 'inactive'}`}
              style={{ minWidth: '110px', fontSize: '12px', padding: '0.3rem 0.5rem' }}
            >
              <input
                type="checkbox"
                checked={value}
                onChange={() => setLineToggles(toggles => ({ ...toggles, [key]: !toggles[key] }))}
                style={{
                  marginRight: 5,
                  transform: 'scale(0.9)',
                  accentColor: '#4A90E2'
                }}
              />
              {lineLabels[key]}
            </label>
        ))}
      </div>
      <div style={{ borderTop: '1px solid #555', paddingTop: '0.5rem' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.5rem'
        }}>
          <h4 style={{ color: '#fff', margin: 0, fontSize: '0.8rem' }}>
            Planets & Asteroids
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            <div style={{ display: 'flex', gap: '0.3rem' }}>
              <button
                onClick={() => setBodyToggles(Object.fromEntries(allBodies.map(name => [name, true])))}
                className="control-button success"
                style={{ fontSize: '10px', padding: '0.2rem 0.4rem' }}
              >
                All
              </button>
              <button
                onClick={() => setBodyToggles(Object.fromEntries(allBodies.map(name => [name, false])))}
                className="control-button danger"
                style={{ fontSize: '10px', padding: '0.2rem 0.4rem' }}
              >
                None
              </button>
              <button
                onClick={() => setShowBodyAccordion(v => !v)}
                className={`control-button primary ${showBodyAccordion ? 'active' : ''}`}
                style={{ fontSize: '10px', padding: '0.2rem 0.4rem' }}
              >
                {showBodyAccordion ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>
        </div>
        <div
          className="planet-grid planet-grid-container"
          style={{
            maxHeight: showBodyAccordion ? '150px' : '0',
            opacity: showBodyAccordion ? 1 : 0,
            transition: 'max-height 0.3s ease-in-out, opacity 0.3s ease-in-out',
            overflowY: showBodyAccordion ? 'auto' : 'hidden'
          }}
        >
          {allBodies.map(name => (
            <label
              key={name}
              className={`planet-toggle ${bodyToggles[name] ? 'active' : ''}`}
            >
              <input
                type="checkbox"
                checked={bodyToggles[name]}
                onChange={() => setBodyToggles(toggles => ({ ...toggles, [name]: !toggles[name] }))}
                style={{
                  marginRight: 4,
                  transform: 'scale(0.8)',
                  accentColor: '#4A90E2'
                }}
              />
              {name}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}

export default CCGDisplayControls;

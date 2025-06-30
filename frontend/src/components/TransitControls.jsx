import React from 'react';

function TransitControls({
  layerManager,
  forceMapUpdate,
  handleGenerateTransits,
  loadingStep,
  currentTransitDateTime,
  setCurrentTransitDateTime,
  // New props for unified control
  lineToggles,
  setLineToggles,
  allBodies,
  bodyToggles,
  setBodyToggles,
  showBodyAccordion,
  setShowBodyAccordion
}) {
  return (
    <div className="filter-control-panel">
      <h3 style={{ color: '#fff', textAlign: 'center', margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>
        Transit Overlay Controls
      </h3>
      
      {/* Main Transit Layer Toggle */}
      <div style={{ marginBottom: '0.75rem', textAlign: 'center' }}>
        <label
          className={`category-toggle ${layerManager.isLayerVisible('transit') ? 'active' : 'inactive'}`}
          style={{ fontSize: '13px', padding: '0.4rem 0.6rem', cursor: 'pointer' }}
        >
          <input
            type="checkbox"
            checked={layerManager.isLayerVisible('transit')}
            onChange={() => {
              layerManager.toggleLayer('transit');
              forceMapUpdate();
            }}
            style={{
              marginRight: 6,
              transform: 'scale(0.9)',
              accentColor: '#ff6b35'
            }}
          />
          Show Transit Overlay
        </label>
      </div>

      {/* Date/Time Picker */}
      <div style={{ margin: '0.5rem 0', textAlign: 'center' }}>
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '0.5rem'
        }}>
          <input
            type="datetime-local"
            value={currentTransitDateTime.toISOString().slice(0, 16)}
            onChange={(e) => {
              const newDate = new Date(e.target.value);
              if (!isNaN(newDate.getTime())) {
                setCurrentTransitDateTime(newDate);
              }
            }}
            style={{
              flex: 1,
              maxWidth: '180px',
              padding: '0.3rem',
              fontSize: '11px',
              borderRadius: '3px',
              border: '1px solid #555',
              background: '#1a1a1a',
              color: '#fff'
            }}
          />          <button
            onClick={async () => {
              try {
                console.log('Transit button clicked');
                await handleGenerateTransits(currentTransitDateTime);
                console.log('Transit button click completed');
              } catch (error) {
                console.error('Error in transit button click:', error);
              }
            }}
            disabled={loadingStep !== null && loadingStep !== 'done'}
            style={{
              padding: '0.3rem 0.6rem',
              fontSize: '11px',
              background: '#ff6b35',
              color: '#fff',
              border: 'none',
              borderRadius: '3px',
              cursor: 'pointer',
              opacity: loadingStep !== null && loadingStep !== 'done' ? 0.6 : 1
            }}
          >
            Update
          </button>
        </div>
      </div>

      {/* Transit Controls (only show when transit layer is visible) */}
      {layerManager.isLayerVisible('transit') && (
        <>
          {/* Line Type Controls */}
          <div style={{ marginBottom: '0.75rem' }}>
            <h4 style={{
              color: '#fff',
              margin: '0 0 0.5rem 0',
              fontSize: '0.8rem',
              textAlign: 'center'
            }}>
              Line Types
            </h4>
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.4rem',
              justifyContent: 'center',
              marginBottom: '0.75rem'
            }}>
              <label
                className={`category-toggle ${lineToggles.ic_mc ? 'active' : 'inactive'}`}
                style={{ minWidth: '90px', fontSize: '12px', padding: '0.3rem 0.5rem', cursor: 'pointer' }}
              >
                <input
                  type="checkbox"
                  checked={lineToggles.ic_mc}
                  onChange={() => {
                    setLineToggles(prev => ({ ...prev, ic_mc: !prev.ic_mc }));
                    forceMapUpdate();
                  }}
                  style={{
                    marginRight: 5,
                    transform: 'scale(0.9)',
                    accentColor: '#ff6b35'
                  }}
                />
                IC/MC Lines
              </label>
              <label
                className={`category-toggle ${lineToggles.ac_dc ? 'active' : 'inactive'}`}
                style={{ minWidth: '90px', fontSize: '12px', padding: '0.3rem 0.5rem', cursor: 'pointer' }}
              >
                <input
                  type="checkbox"
                  checked={lineToggles.ac_dc}
                  onChange={() => {
                    setLineToggles(prev => ({ ...prev, ac_dc: !prev.ac_dc }));
                    forceMapUpdate();
                  }}
                  style={{
                    marginRight: 5,
                    transform: 'scale(0.9)',
                    accentColor: '#ff6b35'
                  }}
                />
                AC/DC Lines
              </label>
              <label
                className={`category-toggle ${lineToggles.parans ? 'active' : 'inactive'}`}
                style={{ minWidth: '90px', fontSize: '12px', padding: '0.3rem 0.5rem', cursor: 'pointer' }}
              >
                <input
                  type="checkbox"
                  checked={lineToggles.parans}
                  onChange={() => {
                    setLineToggles(prev => ({ ...prev, parans: !prev.parans }));
                    forceMapUpdate();
                  }}
                  style={{
                    marginRight: 5,
                    transform: 'scale(0.9)',
                    accentColor: '#ff6b35'
                  }}
                />
                Parans              </label>
            </div>
          </div>

          {/* Bodies Section */}
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
              <div style={{ display: 'flex', gap: '0.3rem' }}>
                <button
                  onClick={() => {
                    setBodyToggles(Object.fromEntries(allBodies.map(name => [name, true])));
                    forceMapUpdate();
                  }}
                  className="control-button success"
                  style={{ fontSize: '10px', padding: '0.2rem 0.4rem' }}
                >
                  All
                </button>
                <button
                  onClick={() => {
                    setBodyToggles(Object.fromEntries(allBodies.map(name => [name, false])));
                    forceMapUpdate();
                  }}
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
                    onChange={() => {
                      setBodyToggles(toggles => ({ ...toggles, [name]: !toggles[name] }));
                      forceMapUpdate();
                    }}
                    style={{
                      marginRight: 4,
                      transform: 'scale(0.8)',
                      accentColor: '#ff6b35'
                    }}
                  />
                  <span style={{ fontSize: '11px' }}>{name}</span>
                </label>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default TransitControls;

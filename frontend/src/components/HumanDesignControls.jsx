import React from 'react';

function HumanDesignControls({
  layerManager,
  forceMapUpdate,
  handleGenerateHD,
  loadingStep,
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
        Human Design Overlay Controls
      </h3>
      
      {/* Main HD Layer Toggle */}
      <div style={{ marginBottom: '0.75rem', textAlign: 'center' }}>
        <label
          className={`category-toggle ${layerManager.isLayerVisible('HD_DESIGN') ? 'active' : 'inactive'}`}
          style={{ fontSize: '13px', padding: '0.4rem 0.6rem', cursor: 'pointer' }}
        >
          <input
            type="checkbox"
            checked={layerManager.isLayerVisible('HD_DESIGN')}
            onChange={() => {
              layerManager.toggleLayer('HD_DESIGN');
              forceMapUpdate();
            }}
            style={{
              marginRight: 6,
              transform: 'scale(0.9)',
              accentColor: '#D47AFF'
            }}
          />
          Show Human Design Overlay
        </label>
      </div>

      {/* Generate Button */}
      <div style={{ textAlign: 'center', marginBottom: '0.75rem' }}>
        <button
          type="button"
          onClick={handleGenerateHD}
          className="control-button primary"
          disabled={loadingStep === 'hd_calculation'}
          style={{
            fontSize: '11px',
            padding: '0.4rem 0.8rem',
            background: loadingStep === 'hd_calculation' ? '#999' : '#D47AFF',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: loadingStep === 'hd_calculation' ? 'not-allowed' : 'pointer'
          }}
        >
          {loadingStep === 'hd_calculation' ? 'Calculating...' : 'Generate Human Design Overlay'}
        </button>
      </div>

      {/* Feature Type Toggles - Only show when HD layer is visible */}
      {layerManager.isLayerVisible('HD_DESIGN') && (
        <>
          <div style={{ borderTop: '1px solid #555', paddingTop: '0.5rem' }}>
            <h4 style={{ color: '#fff', textAlign: 'center', margin: '0 0 0.5rem 0', fontSize: '0.8rem' }}>
              Feature Types
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
                    accentColor: '#D47AFF'
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
                    accentColor: '#D47AFF'
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
                    accentColor: '#D47AFF'
                  }}
                />
                Parans
              </label>
              <label
                className={`category-toggle ${lineToggles.hermetic_lot ? 'active' : 'inactive'}`}
                style={{ minWidth: '110px', fontSize: '12px', padding: '0.3rem 0.5rem', cursor: 'pointer' }}
              >
                <input
                  type="checkbox"
                  checked={lineToggles.hermetic_lot}
                  onChange={() => {
                    setLineToggles(prev => ({ ...prev, hermetic_lot: !prev.hermetic_lot }));
                    forceMapUpdate();
                  }}
                  style={{
                    marginRight: 5,
                    transform: 'scale(0.9)',
                    accentColor: '#D47AFF'
                  }}
                />
                Hermetic Lots
              </label>
              <label
                className={`category-toggle ${lineToggles.mc_aspects ? 'active' : 'inactive'}`}
                style={{ minWidth: '100px', fontSize: '12px', padding: '0.3rem 0.5rem', cursor: 'pointer' }}
              >
                <input
                  type="checkbox"
                  checked={lineToggles.mc_aspects}
                  onChange={() => {
                    setLineToggles(prev => ({ ...prev, mc_aspects: !prev.mc_aspects }));
                    forceMapUpdate();
                  }}
                  style={{
                    marginRight: 5,
                    transform: 'scale(0.9)',
                    accentColor: '#D47AFF'
                  }}
                />
                MC Aspects
              </label>
              <label
                className={`category-toggle ${lineToggles.ac_aspects ? 'active' : 'inactive'}`}
                style={{ minWidth: '100px', fontSize: '12px', padding: '0.3rem 0.5rem', cursor: 'pointer' }}
              >
                <input
                  type="checkbox"
                  checked={lineToggles.ac_aspects}
                  onChange={() => {
                    setLineToggles(prev => ({ ...prev, ac_aspects: !prev.ac_aspects }));
                    forceMapUpdate();
                  }}
                  style={{
                    marginRight: 5,
                    transform: 'scale(0.9)',
                    accentColor: '#D47AFF'
                  }}
                />
                AC Aspects
              </label>
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
                      accentColor: '#D47AFF'
                    }}
                  />
                  {name}
                </label>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default HumanDesignControls;

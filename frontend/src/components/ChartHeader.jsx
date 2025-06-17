import React from 'react';
import './ChartHeader.css';

const ChartHeader = ({ formData, response, astroData }) => {
  if (!response || !astroData) return null;

  // Helper for coordinates
  const formatCoordinates = (coords) => {
    if (!coords) return '';
    const lat = Math.abs(coords.latitude);
    const lon = Math.abs(coords.longitude);
    const latDir = coords.latitude >= 0 ? 'N' : 'S';
    const lonDir = coords.longitude >= 0 ? 'E' : 'W';
    return `${lat.toFixed(6)}°${latDir}, ${lon.toFixed(6)}°${lonDir}`;
  };

  // Get UT time from backend response
  const ut = response.utc_time;
  const utString = ut
    ? `${ut.year}-${String(ut.month).padStart(2, '0')}-${String(ut.day).padStart(2, '0')} ${String(ut.hour).padStart(2, '0')}:${String(ut.minute).padStart(2, '0')}`
    : 'N/A';

  // Compose location string
  const locationString = [
    formData.birth_city,
    formData.birth_state,
    formData.birth_country
  ].filter(Boolean).join(', ');

  return (
    <div className="chart-header">
      <div className="chart-header-main">
        <div className="chart-title">
          <h2>{formData.name || 'Chart'}</h2>          <div className="birth-info" style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ 
              background: 'linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%)',
              padding: '12px 16px',
              borderRadius: '8px',
              border: '1px solid #444',
              marginTop: '8px',
              boxShadow: '0 2px 6px rgba(0,0,0,0.3)',
              maxWidth: '600px',
              textAlign: 'center'
            }}>
              <div style={{ 
                color: '#98d982', 
                fontSize: '0.85rem', 
                fontWeight: 600,
                marginBottom: '6px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                📋 Input Verification
              </div>
              <div style={{ color: '#e0e0e0', fontSize: '0.9rem', lineHeight: '1.4' }}>
                <div style={{ marginBottom: '4px' }}>
                  <span style={{ color: '#98d982' }}>Name:</span> <span style={{ color: '#fff', fontWeight: 500 }}>{formData.name || '(none)'}</span> • 
                  <span style={{ color: '#98d982' }}> Date:</span> <span style={{ color: '#fff', fontWeight: 500 }}>{formData.birth_date}</span> • 
                  <span style={{ color: '#98d982' }}> Time:</span> <span style={{ color: '#fff', fontWeight: 500 }}>{formData.birth_time}</span>
                </div>
                <div style={{ marginBottom: '4px' }}>
                  <span style={{ color: '#98d982' }}>Timezone:</span> <span style={{ color: '#fff', fontWeight: 500 }}>{formData.timezone}</span> • 
                  <span style={{ color: '#98d982' }}> Location:</span> <span style={{ color: '#fff', fontWeight: 500 }}>{locationString}</span>
                </div>
                <div style={{ marginBottom: '4px' }}>
                  <span style={{ color: '#98d982' }}>Coordinates:</span> <span style={{ color: '#ffb347', fontFamily: 'monospace', fontSize: '0.85rem' }}>{formatCoordinates(response.coordinates)}</span>
                </div>
                <div style={{ 
                  borderTop: '1px solid #333', 
                  paddingTop: '6px', 
                  marginTop: '6px',
                  color: '#ccc',
                  fontSize: '0.85rem'
                }}>
                  <span style={{ color: '#98d982' }}>UT sent to ephemeris:</span> <span style={{ color: '#ffb347', fontFamily: 'monospace' }}>{utString}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="chart-meta">
          <div className="generation-info">
            Chart Generated: {new Date().toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChartHeader;

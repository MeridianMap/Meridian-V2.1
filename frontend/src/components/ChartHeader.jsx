import React from 'react';
import './ChartHeader.css';

const ChartHeader = ({ formData, response, astroData }) => {
  if (!response || !astroData) return null;

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const formatCoordinates = (coords) => {
    if (!coords) return '';
    const lat = Math.abs(coords.latitude);
    const lon = Math.abs(coords.longitude);
    const latDir = coords.latitude >= 0 ? 'N' : 'S';
    const lonDir = coords.longitude >= 0 ? 'E' : 'W';
    
    return `${lat.toFixed(1)}°${latDir} ${lon.toFixed(1)}°${lonDir}`;
  };

  const generateTime = new Date().toLocaleDateString('en-US', { 
    month: 'long', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });

  return (
    <div className="chart-header">
      <div className="chart-header-main">
        <div className="chart-title">
          <h2>{formData.name || 'Chart'}</h2>
          <div className="birth-info">
            Born {formatDate(formData.birth_date)} at {formData.birth_time} in {formData.birth_city}
            {formData.birth_state && `, ${formData.birth_state}`}
          </div>
        </div>
        <div className="chart-meta">
          <div className="generation-info">
            Chart Generated: {generateTime}
          </div>
          <div className="coordinates">
            {formatCoordinates(response.coordinates)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChartHeader;

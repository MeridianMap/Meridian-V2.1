import React, { useState, useEffect } from 'react';
import './TimeControls.css';

const TimeControls = ({ timeManager, onTimeChange }) => {
  const [currentTime, setCurrentTime] = useState(timeManager.getCurrentTime());
  const [sliderPosition, setSliderPosition] = useState(0);
  
  // Hover tooltip state
  const [hoveredButton, setHoveredButton] = useState(null);
  const [sliderHover, setSliderHover] = useState({ show: false, x: 0, date: '' });
  
  // Subscribe to time manager changes
  useEffect(() => {
    const unsubscribe = timeManager.addListener((event, data) => {
      if (event === 'currentTimeChanged') {
        setCurrentTime(data);
        setSliderPosition(timeManager.getSliderPosition());
        if (onTimeChange) {
          onTimeChange(data);
        }
      }
    });

    // Initial state
    setCurrentTime(timeManager.getCurrentTime());
    setSliderPosition(timeManager.getSliderPosition());

    return unsubscribe;
  }, [timeManager, onTimeChange]);
  
  const handleSliderChange = (e) => {
    const position = parseFloat(e.target.value);
    setSliderPosition(position);
    timeManager.setTimeBySliderPosition(position);
  };

  const handleSliderMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const width = rect.width;
    const position = x / width;
    
    // Calculate the date at this position
    const timeRange = timeManager.getTimeRange();
    const timeDiff = timeRange.end.getTime() - timeRange.start.getTime();
    const targetTime = new Date(timeRange.start.getTime() + (timeDiff * position));
    
    setSliderHover({
      show: true,
      x: x,
      date: targetTime.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' ,
        hour: 'numeric',
        minute: '2-digit'
      })
    });
  };

  const handleSliderMouseLeave = () => {
    setSliderHover({ show: false, x: 0, date: '' });
  };  

  const handleJumpToNow = () => {
    timeManager.jumpToNow();
  };
  const handleJumpRelative = (days) => {
    timeManager.jumpRelative(days);
  };

  const formatDateTime = (date) => {
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString(),
      iso: date.toISOString().slice(0, 16) // Format for datetime-local input
    };
  };
  const formatted = formatDateTime(currentTime);

  // Helper function to calculate future/past dates for tooltips
  const calculateJumpDate = (days) => {
    const newDate = new Date(currentTime);
    newDate.setDate(newDate.getDate() + days);
    return newDate.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  // Enhanced button component with tooltip
  const JumpButton = ({ days, label, className = '' }) => (
    <button 
      onClick={() => handleJumpRelative(days)}
      className={className}
      title={`${label} → ${calculateJumpDate(days)}`}
      onMouseEnter={() => setHoveredButton(label)}
      onMouseLeave={() => setHoveredButton(null)}
    >
      {label}
      {hoveredButton === label && (
        <div className="button-tooltip">
          {calculateJumpDate(days)}
        </div>
      )}
    </button>
  );

  return (
    <div className="time-controls">
      <div className="time-controls-header">
        <h3>🕐 Time Controls</h3>
        <div className="current-time">
          <strong>{formatted.date} {formatted.time}</strong>
        </div>
      </div>{/* Time Slider */}
      <div className="time-slider-section">
        <label>Time Slider</label>
        <div className="slider-container" style={{ position: 'relative' }}>
          <input
            type="range"
            min="0"
            max="1"
            step="0.001"
            value={sliderPosition}
            onChange={handleSliderChange}
            onMouseMove={handleSliderMouseMove}
            onMouseLeave={handleSliderMouseLeave}
            className="time-slider"
          />
          {sliderHover.show && (
            <div 
              className="slider-tooltip"
              style={{
                position: 'absolute',
                left: `${sliderHover.x}px`,
                top: '-35px',
                background: 'rgba(0, 0, 0, 0.8)',
                color: 'white',
                padding: '4px 8px',
                borderRadius: '4px',
                fontSize: '12px',
                whiteSpace: 'nowrap',
                pointerEvents: 'none',
                transform: 'translateX(-50%)',
                zIndex: 1000
              }}
            >
              {sliderHover.date}
            </div>
          )}
        </div>
        <div className="time-range-labels">
          <span>{formatDateTime(timeManager.getTimeRange().start).date}</span>
          <span>{formatDateTime(timeManager.getTimeRange().end).date}</span>
        </div>
      </div>{/* Quick Jump Controls */}
      <div className="quick-jump-controls">
        <div className="jump-buttons">
          <JumpButton days={-365} label="-1 Year" />
          <JumpButton days={-30} label="-1 Month" />
          <JumpButton days={-7} label="-1 Week" />
          <JumpButton days={-1} label="-1 Day" />
          
          <button onClick={handleJumpToNow} className="now-btn" title="Jump to current time">NOW</button>
          
          <JumpButton days={1} label="+1 Day" />
          <JumpButton days={7} label="+1 Week" />
          <JumpButton days={30} label="+1 Month" />
          <JumpButton days={365} label="+1 Year" />        </div>
      </div>
    </div>
  );
};

export default TimeControls;

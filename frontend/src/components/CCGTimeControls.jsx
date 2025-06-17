import React from 'react';

const increments = [
  { label: '± Day', value: { days: 1 } },
  { label: '± Week', value: { days: 7 } },
  { label: '± Month', value: { days: 30 } },
  { label: '± Year', value: { days: 365 } },
];

export default function CCGTimeControls({ onShift }) {
  return (
    <div className="ccg-time-controls">
      {increments.map((inc, idx) => (
        <button key={idx} onClick={() => onShift(inc.value)}>{inc.label}</button>
      ))}
    </div>
  );
}

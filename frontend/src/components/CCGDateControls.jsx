import React from 'react';

const increments = [
  { label: '− Day', value: -1, unit: 'day' },
  { label: '+ Day', value: 1, unit: 'day' },
  { label: '− Week', value: -7, unit: 'day' },
  { label: '+ Week', value: 7, unit: 'day' },
  { label: '− Month', value: -1, unit: 'month' },
  { label: '+ Month', value: 1, unit: 'month' },
  { label: '− Year', value: -1, unit: 'year' },
  { label: '+ Year', value: 1, unit: 'year' }
];

function addToDate(date, value, unit) {
  const d = new Date(date);
  if (unit === 'day') d.setDate(d.getDate() + value);
  if (unit === 'month') d.setMonth(d.getMonth() + value);
  if (unit === 'year') d.setFullYear(d.getFullYear() + value);
  return d.toISOString().slice(0, 10);
}

export default function CCGDateControls({ ccgDate, setCCGDate }) {
  return (
    <div className="ccg-date-controls" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <input
        type="date"
        value={ccgDate}
        onChange={e => setCCGDate(e.target.value)}
        style={{ fontSize: 14, padding: '2px 6px' }}
      />
      {increments.map((inc, idx) => (
        <button
          key={idx}
          onClick={() => setCCGDate(prev => addToDate(prev, inc.value, inc.unit))}
          style={{ fontSize: 12, padding: '2px 8px' }}
        >
          {inc.label}
        </button>
      ))}
    </div>
  );
}

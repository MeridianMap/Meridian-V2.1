import React, { useRef } from 'react';
import useCitySuggestions from '../hooks/useCitySuggestions';

function ChartForm({ formData, setFormData, onSubmit, error }) {
  const dropdownRef = useRef(null);
  const {
    suggestions,
    showSuggestions,
    handleInputChange,
    handleSuggestionSelect,
    setShowSuggestions
  } = useCitySuggestions(formData, setFormData);

  return (
    <form onSubmit={onSubmit}>
      <input type="text" name="name" placeholder="Full Name" value={formData.name} onChange={handleInputChange} required />
      <input type="date" name="birth_date" value={formData.birth_date} onChange={handleInputChange} required />
      <input type="time" name="birth_time" value={formData.birth_time} onChange={handleInputChange} required />
      <div style={{ position: 'relative' }} ref={dropdownRef}>
        <input
          type="text"
          name="birth_city"
          placeholder="City"
          value={formData.birth_city}
          onChange={handleInputChange}
          onFocus={() => formData.birth_city.length > 2 && handleInputChange({ target: { name: 'birth_city', value: formData.birth_city } })}
          required
        />
        {showSuggestions && suggestions.length > 0 && (
          <ul style={{
            position: 'absolute', background: '#fff', border: '1px solid #ccc',
            zIndex: 1000, maxHeight: '200px', overflowY: 'auto', margin: 0, padding: 0,
            listStyle: 'none', width: '100%'
          }}>
            {suggestions.map((s, i) => {
              const city = s.city || s.properties?.city || s.formatted || 'Unknown City';
              const state = s.state || s.properties?.state || '';
              const country = s.country || s.properties?.country || '';
              const label = `${city}, ${state}, ${country}`;
              return (
                <li
                  key={i}
                  style={{ padding: '0.5rem', cursor: 'pointer' }}
                  onMouseDown={e => {
                    e.preventDefault();
                    handleSuggestionSelect(s);
                  }}
                >
                  {label}
                </li>
              );
            })}
          </ul>
        )}
      </div>
      <button type="submit">Generate Chart</button>
      {error && <p style={{ color: 'red', marginTop: '1rem' }}>{error}</p>}
    </form>
  );
}

export default ChartForm;

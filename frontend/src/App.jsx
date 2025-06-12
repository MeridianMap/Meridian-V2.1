import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './App.css'
import AstroMap from './Astromap';

const GEOAPIFY_API_KEY = '89b7ba6d03ca4cfc871fac9f5d3dade0'
const TIMEZONEDB_API_KEY = 'YHIFBIVJIA14'

function App() {
  const [formData, setFormData] = useState({
    name: '',
    birth_date: '',
    birth_time: '',
    birth_city: '',
    birth_state: '',
    birth_country: '',
    timezone: ''
  })
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [response, setResponse] = useState(null)
  const [error, setError] = useState(null)
  const [astroData, setAstroData] = useState(null)
  const [showJson, setShowJson] = useState(false)
  const [showAstroJson, setShowAstroJson] = useState(false)
  const [lineToggles, setLineToggles] = useState({
    planet: true,
    aspect: true,
    fixed_star: true,
    hermetic_lot: true,
  });

  // List of all planets and asteroids for individual toggles
  const allBodies = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "North Node",
    "South Node", "Chiron", "Ceres", "Pallas", "Juno", "Vesta", "Black Moon Lilith", "Pholus"
  ];

  // State for individual planet/asteroid toggles (default all on)
  const [bodyToggles, setBodyToggles] = React.useState(
    Object.fromEntries(allBodies.map(name => [name, true]))
  );

  // Accordion state for planet/asteroid toggles
  const [showBodyAccordion, setShowBodyAccordion] = React.useState(false);

  const dropdownRef = useRef(null)
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData({ ...formData, [name]: value })
    if (name === 'birth_city' && value.length > 2) fetchCitySuggestions(value)
  }

  const fetchCitySuggestions = async (input) => {
    try {
      const result = await axios.get(
        `https://api.geoapify.com/v1/geocode/autocomplete?text=${encodeURIComponent(input)}&limit=5&type=city&format=json&apiKey=${GEOAPIFY_API_KEY}`
      )
      setSuggestions(result.data.results)
      setShowSuggestions(true)
    } catch (err) {
      console.error('Geoapify error:', err)
    }
  }

  const handleSuggestionSelect = async (suggestion) => {
    const city = suggestion.city || suggestion.properties?.city || ''
    const state = suggestion.state || suggestion.properties?.state || ''
    const country = suggestion.country || suggestion.properties?.country || ''
    const lat = suggestion.lat || suggestion.properties?.lat || suggestion.geometry?.coordinates?.[1]
    const lon = suggestion.lon || suggestion.properties?.lon || suggestion.geometry?.coordinates?.[0]
    if (!lat || !lon) return setError("Could not determine coordinates. Please try another city.")

    setFormData(prev => ({ ...prev, birth_city: city, birth_state: state, birth_country: country, timezone: '' }))
    try {
      const tzRes = await axios.get(`https://api.timezonedb.com/v2.1/get-time-zone`, {
        params: { key: TIMEZONEDB_API_KEY, format: 'json', by: 'position', lat, lng: lon }
      })
      setFormData(prev => ({ ...prev, timezone: tzRes.data.zoneName }))
      setShowSuggestions(false)
      setError(null)
    } catch {
      setError("Unable to determine timezone for selected location.")
    }
  }

  // Progress bar state
  const [loadingStep, setLoadingStep] = React.useState(null); // null | 'ephemeris' | 'astro' | 'done'

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoadingStep('ephemeris');
    try {
      // 1. Generate chart (ephemeris)
      const chartResult = await axios.post('http://localhost:5000/api/calculate', {
        ...formData,
        use_extended_planets: true // Always request extended planets
      })
      setResponse(chartResult.data);
      setLoadingStep('astro');
      // 2. Fetch astrocartography data, using the new chartResult
      if (chartResult) {
        await handleFetchAstro(chartResult.data);
      }
      setLoadingStep('done');
    } catch (err) {
      setError("Failed to generate chart or fetch astrocartography data.");
      setLoadingStep(null);
    }
  }

  const handleFetchAstro = async (chartData) => {
    try {
      // Use chartData instead of response
      const payload = {
        birth_date: formData.birth_date,
        birth_time: formData.birth_time,
        timezone: formData.timezone,
        coordinates: { latitude: chartData.coordinates.latitude, longitude: chartData.coordinates.longitude },
        planets: chartData.planets,
        utc_time: chartData.utc_time,
        lots: chartData.lots
      };
      const res = await axios.post('http://localhost:5000/api/astrocartography', payload);
      setAstroData(res.data);
    } catch {
      setError("Failed to fetch astrocartography data.");
    }
  }

  // Filter astroData.features by toggles
  const filteredAstroData = astroData
    ? {
        ...astroData,
        features: astroData.features.filter(f => {
          const cat = f.properties?.category;
          // Category filter
          if (cat in lineToggles && !lineToggles[cat]) return false;
          // Planet/asteroid filter (for lines/points with a planet/asteroid name)
          let body = f.properties?.planet || f.properties?.body || f.properties?.name;
          // Normalize for Pallas Athena
          if (body === 'Pallas Athena') body = 'Pallas';
          // In the filter logic, normalize Black Moon Lilith variants
          if (body === 'Lilith' || body === 'BML' || body === 'Black Moon') body = 'Black Moon Lilith';
          // In the filter logic, normalize South Node and Pholus variants
          if (body === 'South Node' || body === 'SN' || body === 'Ketu') body = 'South Node';
          if (body === 'Pholus') body = 'Pholus';
          if (body && bodyToggles[body] === false) return false;
          return true;
        }),
      }
    : null;

  // Removed Parans-related state and helpers as Parans UI is removed

  // User-friendly labels for line categories
  const lineLabels = {
    planet: 'Main Planets',
    aspect: 'Aspects',
    fixed_star: 'Fixed Stars',
    hermetic_lot: 'Hermetic Lots',
  };

  return (
    <div className="app">
      {/* JSON buttons at the top, only show after chart is generated */}
      {(response || astroData) && (
        <div style={{ display: 'flex', gap: 16, margin: '2rem 0 1.5rem 0', justifyContent: 'center' }}>
          <button
            onClick={() => setShowJson(prev => !prev)}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: 4,
              border: '1px solid #aaa',
              background: '#222',
              color: '#fff',
              fontWeight: 600,
              fontSize: 18,
              cursor: 'pointer',
              boxShadow: 'none',
              transition: 'background 0.2s, color 0.2s',
            }}
          >
            {showJson ? 'Hide' : 'Show'} Natal Chart JSON
          </button>
          <button
            onClick={() => setShowAstroJson(v => !v)}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: 4,
              border: '1px solid #aaa',
              background: '#222',
              color: '#fff',
              fontWeight: 600,
              fontSize: 18,
              cursor: 'pointer',
              boxShadow: 'none',
              transition: 'background 0.2s, color 0.2s',
            }}
          >
            {showAstroJson ? 'Hide' : 'Show'} Astrocartography JSON Output
          </button>
        </div>
      )}
      {/* JSON output blocks */}
      {showJson && response && (
        <pre style={{
          maxHeight: 400,
          overflow: 'auto',
          background: '#222',
          color: '#fff',
          padding: 12,
          borderRadius: 4,
          fontSize: 13,
          margin: '0 auto 1rem auto',
          width: '90%',
        }}>
          {JSON.stringify(response, null, 2)}
        </pre>
      )}
      {showAstroJson && astroData && (
        <pre style={{
          maxHeight: 400,
          overflow: 'auto',
          background: '#222',
          color: '#fff',
          padding: 12,
          borderRadius: 4,
          fontSize: 13,
          margin: '0 auto 1rem auto',
          width: '90%',
        }}>
          {JSON.stringify(astroData, null, 2)}
        </pre>
      )}
      <h1>Meridian V2</h1>
      <form onSubmit={handleSubmit}>
        <input type="text" name="name" placeholder="Full Name" value={formData.name} onChange={handleChange} required />
        <input type="date" name="birth_date" value={formData.birth_date} onChange={handleChange} required />
        <input type="time" name="birth_time" value={formData.birth_time} onChange={handleChange} required />

        <div style={{ position: 'relative' }} ref={dropdownRef}>
          <input
            type="text"
            name="birth_city"
            placeholder="City"
            value={formData.birth_city}
            onChange={handleChange}
            onFocus={() => formData.birth_city.length > 2 && fetchCitySuggestions(formData.birth_city)}
            required
          />
          {showSuggestions && suggestions.length > 0 && (
            <ul style={{
              position: 'absolute', background: '#fff', border: '1px solid #ccc',
              zIndex: 1000, maxHeight: '200px', overflowY: 'auto', margin: 0, padding: 0,
              listStyle: 'none', width: '100%'
            }}>
              {suggestions.map((s, i) => {
                const city = s.city || s.properties?.city || s.formatted || 'Unknown City'
                const state = s.state || s.properties?.state || ''
                const country = s.country || s.properties?.country || ''
                const label = `${city}, ${state}, ${country}`
                return (
                  <li
                    key={i}
                    style={{ padding: '0.5rem', cursor: 'pointer' }}
                    onMouseDown={e => { e.preventDefault(); setFormData(prev => ({ ...prev, birth_city: city })); handleSuggestionSelect(s) }}
                  >
                    {label}
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        <button type="submit" style={{ marginTop: '1rem' }}>Generate Chart</button>
      </form>
      {loadingStep && (
        <div style={{ width: 340, maxWidth: '90%', margin: '12px auto', textAlign: 'center' }}>
          <div style={{ height: 8, background: '#333', borderRadius: 4, overflow: 'hidden', marginBottom: 6 }}>
            <div style={{
              width: loadingStep === 'ephemeris' ? '33%' : loadingStep === 'astro' ? '66%' : '100%',
              height: '100%',
              background: '#4caf50',
              transition: 'width 0.4s',
            }} />
          </div>
          <span style={{ color: '#bbb', fontSize: 14 }}>
            {loadingStep === 'ephemeris' && 'Calculating ephemeris...'}
            {loadingStep === 'astro' && 'Fetching astrocartography...'}
            {loadingStep === 'done' && 'Done!'}
          </span>
        </div>
      )}
      {error && <p style={{ color: 'red', marginTop: '1rem' }}>{error}</p>}

      {/* Minimal, discrete birth info verification */}
      <pre className="json-preview" style={{
        width: 340,
        maxWidth: '90%',
        margin: '16px auto 8px auto',
        display: 'block',
        textAlign: 'left',
        background: 'rgba(34,34,34,0.7)',
        color: '#bbb',
        fontSize: 13,
        borderRadius: 6,
        boxShadow: 'none',
        padding: '8px 12px',
        border: '1px solid #333',
      }}>{JSON.stringify(formData, null, 2)}</pre>

      {/* Astrocartography visualization */}
      {astroData && (
        <>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', margin: '0 0 1.5rem 0' }}>
            {Object.entries(lineToggles).map(([key, value]) => (
              <label key={key} style={{ color: '#fff', fontWeight: 500, fontSize: 16 }}>
                <input
                  type="checkbox"
                  checked={value}
                  onChange={() => setLineToggles(toggles => ({ ...toggles, [key]: !toggles[key] }))}
                  style={{ marginRight: 6 }}
                />
                {lineLabels[key]}
              </label>
            ))}
          </div>
          {/* Accordion for planet/asteroid toggles */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 16 }}>
            <button
              onClick={() => setShowBodyAccordion(v => !v)}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: 4,
                border: '1px solid #aaa',
                background: '#222',
                color: '#fff',
                fontWeight: 600,
                fontSize: 16,
                cursor: 'pointer',
                marginBottom: 8,
                boxShadow: 'none',
                transition: 'background 0.2s, color 0.2s',
              }}
            >
              {showBodyAccordion ? 'Hide' : 'Show'} Planets & Asteroids
            </button>
            {showBodyAccordion && (
              <div style={{
                display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'center',
                background: 'rgba(34,34,34,0.85)', borderRadius: 8, padding: 16, border: '1px solid #333',
                maxWidth: 700
              }}>
                {/* Check/Uncheck All */}
                <label style={{ color: '#fff', fontWeight: 600, fontSize: 15, minWidth: 120 }}>
                  <input
                    type="checkbox"
                    checked={Object.values(bodyToggles).every(Boolean)}
                    indeterminate={Object.values(bodyToggles).some(v => v) && !Object.values(bodyToggles).every(v => v)}
                    onChange={() => {
                      const allOn = Object.values(bodyToggles).every(Boolean);
                      setBodyToggles(Object.fromEntries(allBodies.map(name => [name, !allOn])));
                    }}
                    style={{ marginRight: 6 }}
                  />
                  Check/Uncheck All
                </label>
                {allBodies.map(name => (
                  <label key={name} style={{ color: '#fff', fontWeight: 500, fontSize: 15, minWidth: 120 }}>
                    <input
                      type="checkbox"
                      checked={bodyToggles[name]}
                      onChange={() => setBodyToggles(toggles => ({ ...toggles, [name]: !toggles[name] }))}
                      style={{ marginRight: 6 }}
                    />
                    {name}
                  </label>
                ))}
              </div>
            )}
          </div>
          {/* Map and JSON buttons at the bottom */}
          <div className="json-preview" style={{ width: 1000, maxWidth: '100%', margin: '3rem auto 0 auto', display: 'flex', flexDirection: 'column', alignItems: 'center', border: '1px solid #222', borderRadius: 12, background: 'rgba(34,34,34,0.7)' }}>
            <AstroMap data={filteredAstroData} />
          </div>
        </>
      )}
    </div>
  )
}

export default App

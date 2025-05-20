import { useState, useEffect, useRef } from 'react'
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
  const [interpretation, setInterpretation] = useState(null)
  const [loadingInterpretation, setLoadingInterpretation] = useState(false)
  const [astroData, setAstroData] = useState(null)
  const [showJson, setShowJson] = useState(false)
  const [showAstroLines, setShowAstroLines] = useState(false)
  const [showAstroJson, setShowAstroJson] = useState(false)
  const [paransData, setParansData] = useState(null);
  const [showParansJson, setShowParansJson] = useState(false);
  const [paransLoading, setParansLoading] = useState(false);
  const [selectedPlanetId, setSelectedPlanetId] = useState(null);

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

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const res = await axios.post('http://localhost:5000/api/calculate', {
        ...formData,
        use_extended_planets: true // Always request extended planets
      })
      setResponse(res.data)
      setInterpretation(null)
    } catch {
      setError('Failed to fetch chart. Please check your input.')
    }
  }

  const handleInterpret = async () => {
    setLoadingInterpretation(true)
    setError(null)
    try {
      const res = await axios.post('http://localhost:5000/api/interpret', response)
      setInterpretation(res.data.interpretation)
    } catch {
      setError('Failed to generate interpretation.')
    } finally {
      setLoadingInterpretation(false)
    }
  }

  const handleFetchAstro = async () => {
    try {
      if (!response?.coordinates?.latitude || !response?.utc_time || !formData.timezone) {
        return setError("Missing data needed for astrocartography request.")
      }
      // Debug: print planets being sent to backend
      console.log('Planets sent to /api/astrocartography:', response.planets?.map(p => p.name));
      const payload = {
        birth_date: formData.birth_date,
        birth_time: formData.birth_time,
        timezone: formData.timezone,
        coordinates: { latitude: response.coordinates.latitude, longitude: response.coordinates.longitude },
        planets: response.planets,
        utc_time: response.utc_time,
        lots: response.lots // <-- ensure Hermetic Lots are sent to backend
      }
      const res = await axios.post('http://localhost:5000/api/astrocartography', payload)
      setAstroData(res.data)
    } catch {
      setError("Failed to fetch astrocartography data.")
    }
  }

  // Helper to get valid planet options
  const validPlanets = response?.planets?.filter(p => [0,1,2,3,4,5,6,7,8,9,15].includes(p.id)) || [];

  const handleCalculateParans = async () => {
    if (!response?.utc_time?.julian_day || !response?.coordinates?.latitude || !response?.coordinates?.longitude || !selectedPlanetId) {
      setError('Missing data for parans calculation.');
      return;
    }
    setParansLoading(true);
    setError(null);
    try {
      const res = await axios.post('http://localhost:5000/api/parans', {
        jd_ut: response.utc_time.julian_day,
        lat: response.coordinates.latitude,
        lon: response.coordinates.longitude,
        planet_id: selectedPlanetId
      });
      setParansData(res.data);
    } catch {
      setError('Failed to fetch parans data.');
    } finally {
      setParansLoading(false);
    }
  };

  return (
    <div className="app">
      <h1>Meridian V1</h1>
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

      {response && (
        <>
          <button type="button" onClick={handleInterpret} style={{ marginTop: '1rem', padding: '0.5rem 1rem', backgroundColor: '#333', color: '#fff', border: 'none' }}>
            {loadingInterpretation ? 'Interpreting...' : 'Interpret Chart'}
          </button>
          <button type="button" onClick={handleFetchAstro} style={{ marginTop: '1rem', padding: '0.5rem 1rem', backgroundColor: '#444', color: '#fff', border: 'none' }}>
            Fetch Astrocartography Data
          </button>
        </>
      )}

      {error && <p style={{ color: 'red', marginTop: '1rem' }}>{error}</p>}

      <pre className="json-preview">{JSON.stringify(formData, null, 2)}</pre>

      {response && (
        <div className="json-preview">
          <button onClick={() => setShowJson(prev => !prev)} style={{ marginBottom: '0.5rem', padding: '0.5rem 1rem', backgroundColor: '#333', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            {showJson ? 'Hide Raw Chart JSON' : 'Show Raw Chart JSON'}
          </button>
          {showJson && <pre>{JSON.stringify(response, null, 2)}</pre>}
        </div>
      )}

      {interpretation && (
        <div className="interpretation-box">
          <h3>Interpretation</h3>
          <p>{interpretation}</p>
        </div>
      )}

      {/* Parans calculation UI */}
      {response && (
        <div style={{ marginTop: '2rem' }}>
          <h3>Calculate Parans</h3>
          <div style={{ marginBottom: 8 }}>
            <label>Select planet:&nbsp;</label>
            <select value={selectedPlanetId || ''} onChange={e => setSelectedPlanetId(Number(e.target.value))}>
              <option value="">-- Select --</option>
              {validPlanets.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <button onClick={handleCalculateParans} disabled={!selectedPlanetId || paransLoading} style={{ marginLeft: 12, padding: '0.5rem 1rem', backgroundColor: '#5a2', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
              {paransLoading ? 'Calculating...' : 'Calculate Parans'}
            </button>
            <button onClick={() => setShowParansJson(prev => !prev)} style={{ marginLeft: 12, padding: '0.5rem 1rem', backgroundColor: '#222', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
              {showParansJson ? 'Hide Parans JSON' : 'Show Parans JSON'}
            </button>
          </div>
          {showParansJson && paransData && (
            <pre className="json-preview" style={{ marginTop: '0.5rem' }}>{JSON.stringify(paransData, null, 2)}</pre>
          )}
        </div>
      )}

      {/* Astrocartography visualization */}
      {astroData && (
        <div style={{ marginTop: '2rem' }}>
          <button onClick={() => setShowAstroLines(prev => !prev)} style={{ marginBottom: '0.5rem', padding: '0.5rem 1rem', backgroundColor: '#333', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            {showAstroLines ? 'Hide Astrocartography Lines' : 'Show Astrocartography Lines'}
          </button>
          <button onClick={() => setShowAstroJson(prev => !prev)} style={{ marginLeft: '1rem', marginBottom: '0.5rem', padding: '0.5rem 1rem', backgroundColor: '#222', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            {showAstroJson ? 'Hide Astrocartography JSON' : 'Show Astrocartography JSON'}
          </button>
          {showAstroJson && (
            <pre className="json-preview" style={{ marginTop: '0.5rem' }}>{JSON.stringify(astroData, null, 2)}</pre>
          )}
          {showAstroLines && <AstroMap data={astroData} paransData={paransData} />}
        </div>
      )}
    </div>
  )
}

export default App

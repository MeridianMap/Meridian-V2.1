import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './App.css'
import AstroMap from './Astromap';
import LayerManager from './utils/LayerManager';
import TimeManager from './utils/TimeManager';
import TimeControls from './components/TimeControls';
import ChartHeader from './components/ChartHeader';

const GEOAPIFY_API_KEY = '89b7ba6d03ca4cfc871fac9f5d3dade0'
const TIMEZONEDB_API_KEY = 'YHIFBIVJIA14'

function App() {
  // Initialize managers
  const [layerManager] = useState(() => new LayerManager());
  const [timeManager] = useState(() => new TimeManager());
  
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
    mc_aspects: true,
    ac_aspects: true,
    fixed_star: true,
    hermetic_lot: true,
    parans: true
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
  const [showBodyAccordion, setShowBodyAccordion] = React.useState(true);

  // Transit layer state
  const [transitData, setTransitData] = useState(null); // eslint-disable-line no-unused-vars
  const [isTransitEnabled, setIsTransitEnabled] = useState(false);
  const [transitToggles, setTransitToggles] = useState({ // eslint-disable-line no-unused-vars
    ac_dc: true,
    ic_mc: true,
    parans: true
  });
  const [isUpdatingTransits, setIsUpdatingTransits] = useState(false);
  const transitUpdateTimeout = useRef(null);

  // Force re-render trigger for map updates
  const [mapUpdateTrigger, setMapUpdateTrigger] = useState(0);

  // Force map update when layer data changes
  const forceMapUpdate = React.useCallback(() => {
    setMapUpdateTrigger(prev => prev + 1);
  }, []);

  // Initialize layers
  React.useEffect(() => {
    // Set up natal layer
    layerManager.addLayer('natal', {
      visible: true,
      order: 0,
      type: 'natal',
      style: {
        color: 'inherit', // Use existing planet colors
        width: 2,
        opacity: 1.0
      }
    });

    // Set up transit layer  
    layerManager.addLayer('transit', {
      visible: false,
      order: 1,
      type: 'transit',
      style: {
        color: 'inherit', // Same color as natal
        width: 3,         // Slightly wider
        opacity: 0.6      // Reduced opacity
      },
      subLayers: {
        ac_dc: true,
        ic_mc: true,
        parans: true
      }
    });

    // Listen for layer changes
    const unsubscribe = layerManager.addListener((event) => {
      if (event === 'layerToggled' || event === 'subLayerToggled') {
        // Force re-render when layers change
        setTransitToggles(prev => ({ ...prev }));
      }
    });

    return unsubscribe;
  }, [layerManager]);

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

    // Display "City, State" in the input field if state exists, otherwise just city
    const displayLocation = state ? `${city}, ${state}` : city;
    setFormData(prev => ({ ...prev, birth_city: displayLocation, birth_state: state, birth_country: country, timezone: '' }))
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
      
      // Set up time manager with natal data
      timeManager.setNatalTime({
        birth_date: formData.birth_date,
        birth_time: formData.birth_time,
        timezone: formData.timezone,
        coordinates: chartResult.data.coordinates
      });
      
      setLoadingStep('astro');
      // 2. Fetch astrocartography data, using the new chartResult
      if (chartResult) {
        await handleFetchAstro(chartResult.data);
      }
      setLoadingStep('done');
    } catch {
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
        lots: chartData.lots,
        // Explicitly include all filter options for natal chart
        include_aspects: true,
        include_fixed_stars: true,
        include_hermetic_lots: true,
        include_parans: true,
        include_ac_dc: true,
        include_ic_mc: true
      };
      
      console.log('Sending natal astrocartography payload:', payload);
      const res = await axios.post('http://localhost:5000/api/astrocartography', payload);
      console.log('Received natal astrocartography response:', res.data);
      console.log('NATAL FEATURES COUNT:', res.data.features?.length);
      console.log('NATAL FEATURES BY CATEGORY:', res.data.features?.reduce((acc, f) => {
        const cat = f.properties?.category || 'unknown';
        acc[cat] = (acc[cat] || 0) + 1;
        return acc;
      }, {}));
      setAstroData(res.data);
      
      // Set natal layer data in layer manager
      layerManager.setLayerData('natal', res.data);
      forceMapUpdate(); // Force map re-render with natal data
      
      // Enable transit generation
      setIsTransitEnabled(true);
    } catch {
      setError("Failed to fetch astrocartography data.");
    }
  }

  // Get merged and filtered data from all visible layers (memoized)
  const mergedFilteredData = React.useMemo(() => {
    console.log('useMemo recomputing mergedFilteredData - trigger:', mapUpdateTrigger);
    const visibleLayers = layerManager.getVisibleLayers();
    let allFeatures = [];

    console.log('getMergedFilteredData - visible layers:', visibleLayers.map(l => ({ name: l.name, featureCount: l.data?.features?.length || 0 })));

    visibleLayers.forEach(layer => {
      if (layer.data && layer.data.features) {
        // Apply filtering based on layer type
        let layerFeatures = layer.data.features;
        
        console.log(`Processing ${layer.name} layer with ${layerFeatures.length} features`);
        
        if (layer.name === 'natal') {
          // Apply natal filtering logic
          console.log('Processing natal layer - initial features:', layerFeatures.length);
          console.log('Current lineToggles:', lineToggles);
          console.log('Current bodyToggles enabled count:', Object.values(bodyToggles).filter(Boolean).length);
          
          // Log all categories before filtering
          const categoryCounts = layerFeatures.reduce((acc, f) => {
            const cat = f.properties?.category || 'unknown';
            acc[cat] = (acc[cat] || 0) + 1;
            return acc;
          }, {});
          console.log('All categories before filtering:', categoryCounts);
          
          layerFeatures = layerFeatures.filter(f => {
            const cat = f.properties?.category;
            const lineType = f.properties?.line_type;
            const aspectTo = f.properties?.to;
            
            // Parans toggle
            if (cat === 'parans' && !lineToggles.parans) return false;
            
            // Aspect handling
            if (cat === 'aspect') {
              if (aspectTo === 'MC' || lineType === 'MC' || lineType === 'IC') {
                if (!lineToggles.mc_aspects) return false;
              } else if (aspectTo === 'ASC' || lineType === 'ASC' || lineType === 'DSC' || lineType === 'HORIZON') {
                if (!lineToggles.ac_aspects) return false;
              } else {
                if (!lineToggles.mc_aspects && !lineToggles.ac_aspects) return false;
              }
            } else {
              // For other categories, only filter if the category exists in lineToggles and is false
              // This allows unknown categories to pass through
              if (cat in lineToggles && !lineToggles[cat]) return false;
            }
            
            // Planet/body filtering
            let body = f.properties?.planet || f.properties?.body || f.properties?.name;
            if (body === 'Pallas Athena') body = 'Pallas';
            if (body === 'Lilith' || body === 'BML' || body === 'Black Moon') body = 'Black Moon Lilith';
            if (body === 'South Node' || body === 'SN' || body === 'Ketu') body = 'South Node';
            if (body && bodyToggles[body] === false) return false;
            
            return true;
          });
          
          console.log('Natal layer after filtering:', layerFeatures.length);
        } else if (layer.name === 'transit') {
          // Apply transit-specific filtering
          layerFeatures = layerFeatures.filter(f => {
            const lineType = f.properties?.line_type;
            const cat = f.properties?.category;
            
            // Filter by sub-layer toggles
            if (lineType === 'AC' || lineType === 'DC' || f.properties?.ac_dc_indices) {
              if (!layerManager.isSubLayerVisible('transit', 'ac_dc')) return false;
            }
            if (lineType === 'MC' || lineType === 'IC') {
              if (!layerManager.isSubLayerVisible('transit', 'ic_mc')) return false;
            }
            if (cat === 'parans' || f.properties?.type === 'crossing_latitude') {
              if (!layerManager.isSubLayerVisible('transit', 'parans')) return false;
            }
            
            // Apply body filtering (same as natal)
            let body = f.properties?.planet || f.properties?.body || f.properties?.name;
            if (body === 'Pallas Athena') body = 'Pallas';
            if (body === 'Lilith' || body === 'BML' || body === 'Black Moon') body = 'Black Moon Lilith';
            if (body === 'South Node' || body === 'SN' || body === 'Ketu') body = 'South Node';
            if (body && bodyToggles[body] === false) return false;
            
            return true;
          });
        }
        
        // Add layer metadata to features
        const layerFeaturesWithMeta = layerFeatures.map(feature => ({
          ...feature,
          layerName: layer.name,
          layerStyle: layer.style,
          layerOrder: layer.order
        }));
        
        allFeatures = [...allFeatures, ...layerFeaturesWithMeta];
      }
    });

    console.log(`getMergedFilteredData returning ${allFeatures.length} total features`);
    return { features: allFeatures };
  }, [layerManager, lineToggles, bodyToggles, mapUpdateTrigger]);

  // Debug logging for mergedFilteredData
  console.log('App.jsx - mergedFilteredData:', mergedFilteredData?.features?.length || 0);

  // Removed Parans-related state and helpers as Parans UI is removed

  // User-friendly labels for line categories
  const lineLabels = {
    planet: 'Planet Lines',
    mc_aspects: 'MC Aspects',
    ac_aspects: 'AC Aspects',
    fixed_star: 'Fixed Stars',
    hermetic_lot: 'Hermetic Lots',
    parans: 'Parans', // <-- Add label for parans
  };

  // Handle transit generation
  const handleGenerateTransits = async () => {
    if (!timeManager.isReadyForTransits()) {
      setError("Natal chart must be generated first before calculating transits.");
      return;
    }

    try {
      setLoadingStep('transit_ephemeris');
      
      // Get current time parameters
      const transitParams = timeManager.getTransitParams();
      console.log('Transit params:', transitParams);
      
      // 1. Generate transit ephemeris
      const transitChartPayload = {
        name: `${formData.name} - Transits`,
        birth_city: formData.birth_city,
        birth_state: formData.birth_state,
        birth_country: formData.birth_country,
        ...transitParams,
        use_extended_planets: true
      };
      console.log('Transit chart payload:', transitChartPayload);
      
      const transitChartResult = await axios.post('http://localhost:5000/api/calculate', transitChartPayload);

      setLoadingStep('transit_astro');
      
      // 2. Generate transit astrocartography (AC/DC, IC/MC, parans only)
      const transitPayload = {
        ...transitParams,
        coordinates: transitParams.coordinates,
        planets: transitChartResult.data.planets,
        utc_time: transitChartResult.data.utc_time,
        lots: transitChartResult.data.lots,
        // Transit-specific filtering
        include_aspects: false,    // No aspect lines for transits
        include_fixed_stars: false, // No fixed stars for transits  
        include_hermetic_lots: false, // No hermetic lots for transits
        include_parans: true,     // Include parans
        include_ac_dc: true,      // Include AC/DC lines
        include_ic_mc: true       // Include IC/MC lines
      };

      const transitRes = await axios.post('http://localhost:5000/api/astrocartography', transitPayload);
      
      // Set transit layer data
      layerManager.setLayerData('transit', transitRes.data);
      setTransitData(transitRes.data);
      
      // Enable transit layer visibility
      layerManager.setLayerVisible('transit', true);
      setIsTransitEnabled(true);
      forceMapUpdate(); // Force map re-render with transit data
      
      // Set up a reasonable time range for the slider (±6 months from now)
      const now = new Date();
      const startRange = new Date(now.getTime() - 0.5 * 365 * 24 * 60 * 60 * 1000); // 6 months ago
      const endRange = new Date(now.getTime() + 0.5 * 365 * 24 * 60 * 60 * 1000);   // 6 months ahead
      timeManager.setTimeRange(startRange, endRange);
      
      setLoadingStep('done');
    } catch (error) {
      console.error('Transit generation error:', error);
      setError("Failed to generate transit data.");
      setLoadingStep(null);
    }
  }

  // Transit animation and real-time updates
  const updateTransitsDebounced = React.useCallback(async (newTime) => {
    // Clear any existing timeout
    if (transitUpdateTimeout.current) {
      clearTimeout(transitUpdateTimeout.current);
    }

    // Set a new timeout for debounced updates
    transitUpdateTimeout.current = setTimeout(async () => {
      if (!timeManager.isReadyForTransits()) return;

      try {
        setIsUpdatingTransits(true);
        console.log('Updating transits for time:', newTime);

        // Get transit parameters for the new time
        const transitParams = timeManager.getTransitParams();
        console.log('Transit params:', transitParams);
        
        // 1. Generate NEW ephemeris for this specific time
        const transitChartPayload = {
          name: `${formData.name} - Transits`,
          birth_city: formData.birth_city,
          birth_state: formData.birth_state,
          birth_country: formData.birth_country,
          ...transitParams,
          use_extended_planets: true
        };
        console.log('Transit chart payload:', transitChartPayload);
        
        const transitChartResult = await axios.post('http://localhost:5000/api/calculate', transitChartPayload);
        console.log('Transit chart result:', transitChartResult.data);

        // 2. Generate transit astrocartography with the new ephemeris
        const transitPayload = {
          ...transitParams,
          coordinates: transitParams.coordinates,
          planets: transitChartResult.data.planets,
          utc_time: transitChartResult.data.utc_time,
          lots: transitChartResult.data.lots,
          // Transit-specific filtering
          include_aspects: false,
          include_fixed_stars: false,
          include_hermetic_lots: false,
          include_parans: true,
          include_ac_dc: true,
          include_ic_mc: true
        };

        const transitRes = await axios.post('http://localhost:5000/api/astrocartography', transitPayload);
        
        // Update transit layer data
        layerManager.setLayerData('transit', transitRes.data);
        setTransitData(transitRes.data);
        forceMapUpdate(); // Force map re-render with new transit data
        
        console.log('Transits updated successfully with', transitRes.data.features.length, 'features');
      } catch (err) {
        console.error('Error updating transits:', err);
      } finally {
        setIsUpdatingTransits(false);
      }
    }, 100); // 100ms debounce for faster animation response
  }, [timeManager, formData, layerManager, forceMapUpdate]);

  // Listen for time changes and update transits
  React.useEffect(() => {
    const unsubscribe = timeManager.addListener((event, data) => {
      if (event === 'currentTimeChanged' && isTransitEnabled) {
        // Only trigger transit updates if not in buffered animation mode
        if (timeManager.bufferFrames && timeManager.bufferFrames.length > 0 && timeManager.isAnimating) {
          console.log('⏰ Time changed during buffered animation (slider update only)');
          // During buffered animation, only update the time display, don't fetch new transits
          return;
        }
        console.log('⏰ Time changed for transits:', data);
        updateTransitsDebounced(data);
      } else if (event === 'frameDataUpdate') {
        // Handle buffered frame data updates during animation
        console.log('🎬 Received frame data update with', data?.features?.length || 0, 'features');
        layerManager.setLayerData('transit', data);
        setTransitData(data);
        forceMapUpdate(); // Force map re-render with new transit data
      }
    });

    return unsubscribe;
  }, [timeManager, updateTransitsDebounced, isTransitEnabled, layerManager, forceMapUpdate]);

  // Buffering function for smooth 48-frame animation
  const bufferTransitFrames = React.useCallback(async () => {
    if (!timeManager.isReadyForTransits()) {
      throw new Error('TimeManager not ready for transits');
    }

    // Create a transit generator function for each frame
    const generateTransitForTime = async (frameTime) => {
      try {
        // Set the time in TimeManager temporarily for this frame
        const originalTime = timeManager.getCurrentTime();
        timeManager.setCurrentTime(frameTime);
        
        // Get transit parameters for this time
        const transitParams = timeManager.getTransitParams();
        
        // Generate ephemeris for this frame time
        const transitChartPayload = {
          name: `${formData.name} - Transits`,
          birth_city: formData.birth_city,
          birth_state: formData.birth_state,
          birth_country: formData.birth_country,
          ...transitParams,
          use_extended_planets: true
        };
        
        const transitChartResult = await axios.post('http://localhost:5000/api/calculate', transitChartPayload);
        
        // Generate transit astrocartography
        const transitPayload = {
          ...transitParams,
          coordinates: transitParams.coordinates,
          planets: transitChartResult.data.planets,
          utc_time: transitChartResult.data.utc_time,
          lots: transitChartResult.data.lots,
          // Transit-specific filtering
          include_aspects: false,
          include_fixed_stars: false,
          include_hermetic_lots: false,
          include_parans: true,
          include_ac_dc: true,
          include_ic_mc: true
        };
        
        const transitRes = await axios.post('http://localhost:5000/api/astrocartography', transitPayload);
        
        // Restore original time
        timeManager.setCurrentTime(originalTime);
        
        return transitRes.data;
      } catch (error) {
        console.error('Error generating transit frame:', error);
        throw error;
      }
    };

    // Start buffering with the transit generator
    await timeManager.bufferAnimationFrames(generateTransitForTime);
  }, [timeManager, formData]);

  // Handle play button - buffer frames then start animation
  const handlePlayAnimation = React.useCallback(async () => {
    try {
      console.log('Starting buffered animation process...');
      
      // Step 1: Buffer all frames first
      await bufferTransitFrames();
      
      console.log('Buffering complete, starting playback...');
      
      // Step 2: Start buffered animation playback
      timeManager.startBufferedAnimation();
    } catch (error) {
      console.error('Animation playback failed:', error);
      setError('Failed to start animation');
    }
  }, [bufferTransitFrames, timeManager]);

  return (
    <div className="app">
      {/* JSON buttons at the top, only show after chart is generated */}
      {(response || astroData) && (
        <div className="json-buttons">
          <button
            onClick={() => setShowJson(prev => !prev)}
            className="json-button"
          >
            {showJson ? 'Hide' : 'Show'} Natal Chart JSON
          </button>
          <button
            onClick={() => setShowAstroJson(v => !v)}
            className="json-button"
          >
            {showAstroJson ? 'Hide' : 'Show'} Astrocartography JSON
          </button>
        </div>
      )}
      {/* JSON output blocks */}
      {showJson && response && (
        <pre style={{
          maxHeight: 300,
          overflow: 'auto',
          background: '#222',
          color: '#fff',
          padding: 8,
          borderRadius: 4,
          fontSize: 11,
          margin: '0 auto 0.5rem auto',
          width: '95%',
        }}>
          {JSON.stringify(response, null, 2)}
        </pre>
      )}
      {showAstroJson && astroData && (
        <pre style={{
          maxHeight: 300,
          overflow: 'auto',
          background: '#222',
          color: '#fff',
          padding: 8,
          borderRadius: 4,
          fontSize: 11,
          margin: '0 auto 0.5rem auto',
          width: '95%',
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
                    onMouseDown={e => { 
                      e.preventDefault(); 
                      // Show the full location display in dropdown but handle selection properly
                      handleSuggestionSelect(s);
                    }}
                  >
                    {label}
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        <button type="submit">Generate Chart</button>
      </form>
      
      {/* Generate Transits Button */}
      {response && !isTransitEnabled && (
        <div style={{ textAlign: 'center', margin: '1rem 0' }}>
          <button 
            type="button"
            onClick={handleGenerateTransits}
            disabled={loadingStep !== null && loadingStep !== 'done'}
            className="generate-btn transit-btn"
            style={{
              padding: '12px 24px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: loadingStep !== null && loadingStep !== 'done' ? 'not-allowed' : 'pointer',
              opacity: loadingStep !== null && loadingStep !== 'done' ? 0.6 : 1,
              fontSize: '1rem',
              fontWeight: '500'
            }}
          >
            Generate Transits
          </button>
        </div>
      )}
      {loadingStep && (
        <div className="progress-container">
          <div className="progress-bar">
            <div className="progress-fill" style={{
              width: loadingStep === 'ephemeris' ? '25%' : 
                     loadingStep === 'astro' ? '50%' :
                     loadingStep === 'transit_ephemeris' ? '75%' :
                     loadingStep === 'transit_astro' ? '90%' : '100%'
            }} />
          </div>
          <span className="progress-text">
            {loadingStep === 'ephemeris' && 'Calculating natal ephemeris...'}
            {loadingStep === 'astro' && 'Fetching natal astrocartography...'}
            {loadingStep === 'transit_ephemeris' && 'Calculating transit ephemeris...'}
            {loadingStep === 'transit_astro' && 'Fetching transit astrocartography...'}
            {loadingStep === 'done' && 'Done!'}
          </span>
        </div>
      )}

      {/* Transit Update Indicator */}
      {isUpdatingTransits && (
        <div className="transit-update-indicator" style={{
          textAlign: 'center',
          padding: '8px',
          background: 'rgba(74, 144, 226, 0.1)',
          border: '1px solid rgba(74, 144, 226, 0.3)',
          borderRadius: '4px',
          color: '#4A90E2',
          fontSize: '0.9em',
          margin: '10px 0'
        }}>
          🔄 Updating transit lines...
        </div>
      )}
      
      {/* Summary sentence after completion */}
      {/* REMOVED: This was the green chart summary block marked with X in the screenshot */}
      {error && <p style={{ color: 'red', marginTop: '1rem' }}>{error}</p>}

      

      {/* Astrocartography visualization */}
      {astroData && (
        <>
          {/* Chart Header */}
          <ChartHeader 
            formData={formData}
            response={response}
            astroData={astroData}
          />

          {/* Map Container - Full Width */}
          <div className="map-container" style={{ width: '100%', marginBottom: '1rem' }}>
            <AstroMap data={mergedFilteredData} />
          </div>

          {/* Controls Section - Two Columns Below Map */}
          <div className="controls-below-map">
            {/* Natal Display Controls */}
            <div className="filter-control-panel">
              <h3 style={{ color: '#fff', textAlign: 'center', margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>
                Natal Display Controls
              </h3>
              
              {/* Category toggles - more compact layout */}
              <div style={{ 
                display: 'flex', 
                flexWrap: 'wrap',
                gap: '0.4rem', 
                justifyContent: 'center',
                marginBottom: '0.75rem' 
              }}>
                {Object.entries(lineToggles).map(([key, value]) => (
                  <label 
                    key={key} 
                    className={`category-toggle ${value ? 'active' : 'inactive'}`}
                    style={{ minWidth: '110px', fontSize: '12px', padding: '0.3rem 0.5rem' }}
                  >
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={() => setLineToggles(toggles => ({ ...toggles, [key]: !toggles[key] }))}
                      style={{ 
                        marginRight: 5, 
                        transform: 'scale(0.9)',
                        accentColor: '#4caf50'
                      }}
                    />
                    {lineLabels[key]}
                  </label>
                ))}
              </div>

              {/* Planet/asteroid controls - more compact */}
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
                      onClick={() => setBodyToggles(Object.fromEntries(allBodies.map(name => [name, true])))}
                      className="control-button success"
                      style={{ fontSize: '10px', padding: '0.2rem 0.4rem' }}
                    >
                      All
                    </button>
                    <button
                      onClick={() => setBodyToggles(Object.fromEntries(allBodies.map(name => [name, false])))}
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
                        onChange={() => setBodyToggles(toggles => ({ ...toggles, [name]: !toggles[name] }))}
                        style={{ 
                          marginRight: 4,
                          transform: 'scale(0.8)',
                          accentColor: '#4caf50'
                        }}
                      />
                      {name}
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Transit Display Controls */}
            {isTransitEnabled && (
              <div className="filter-control-panel">
                <h3 style={{ color: '#fff', textAlign: 'center', margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>
                  Transit Display Controls
                </h3>
                
                {/* Main transit toggle */}
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
                        accentColor: '#4caf50'
                      }}
                    />
                    Show Transit Lines
                  </label>
                </div>
                
                {/* Transit line type toggles */}
                {layerManager.isLayerVisible('transit') && (
                  <div style={{ 
                    display: 'flex', 
                    flexWrap: 'wrap',
                    gap: '0.4rem', 
                    justifyContent: 'center',
                    marginBottom: '0.75rem' 
                  }}>
                    <label 
                      className={`category-toggle ${layerManager.isSubLayerVisible('transit', 'ac_dc') ? 'active' : 'inactive'}`}
                      style={{ minWidth: '80px', fontSize: '12px', padding: '0.3rem 0.5rem', cursor: 'pointer' }}
                    >
                      <input
                        type="checkbox"
                        checked={layerManager.isSubLayerVisible('transit', 'ac_dc')}
                        onChange={() => {
                          layerManager.toggleSubLayer('transit', 'ac_dc');
                          forceMapUpdate();
                        }}
                        style={{ 
                          marginRight: 5, 
                          transform: 'scale(0.9)',
                          accentColor: '#4caf50'
                        }}
                      />
                      AC/DC Lines
                    </label>
                    <label 
                      className={`category-toggle ${layerManager.isSubLayerVisible('transit', 'ic_mc') ? 'active' : 'inactive'}`}
                      style={{ minWidth: '80px', fontSize: '12px', padding: '0.3rem 0.5rem', cursor: 'pointer' }}
                    >
                      <input
                        type="checkbox"
                        checked={layerManager.isSubLayerVisible('transit', 'ic_mc')}
                        onChange={() => {
                          layerManager.toggleSubLayer('transit', 'ic_mc');
                          forceMapUpdate();
                        }}
                        style={{ 
                          marginRight: 5, 
                          transform: 'scale(0.9)',
                          accentColor: '#4caf50'
                        }}
                      />
                      IC/MC Lines
                    </label>
                    <label 
                      className={`category-toggle ${layerManager.isSubLayerVisible('transit', 'parans') ? 'active' : 'inactive'}`}
                      style={{ minWidth: '80px', fontSize: '12px', padding: '0.3rem 0.5rem', cursor: 'pointer' }}
                    >
                      <input
                        type="checkbox"
                        checked={layerManager.isSubLayerVisible('transit', 'parans')}
                        onChange={() => {
                          layerManager.toggleSubLayer('transit', 'parans');
                          forceMapUpdate();
                        }}
                        style={{ 
                          marginRight: 5, 
                          transform: 'scale(0.9)',
                          accentColor: '#4caf50'
                        }}
                      />
                      Parans
                    </label>
                  </div>
                )}

                {/* Update transits button */}
                <div style={{ textAlign: 'center', marginTop: '0.75rem' }}>
                  <button 
                    type="button"
                    onClick={handleGenerateTransits}
                    disabled={loadingStep !== null && loadingStep !== 'done'}
                    className="control-button primary"
                    style={{
                      fontSize: '11px',
                      padding: '0.4rem 0.8rem',
                      opacity: loadingStep !== null && loadingStep !== 'done' ? 0.6 : 1
                    }}
                  >
                    Update Transits
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Transit Timeline Section - Below Controls */}
          {isTransitEnabled && layerManager.isLayerVisible('transit') && (
            <div className="transit-timeline-section">
              <h3 style={{ color: '#fff', textAlign: 'center', margin: '0 0 1rem 0', fontSize: '1rem' }}>
                Transit Timeline Controls
              </h3>
              <TimeControls 
                timeManager={timeManager}
                onTimeChange={updateTransitsDebounced}
                onPlayAnimation={handlePlayAnimation}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default App

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'
import AstroMap from './Astromap';
import LayerManager from './utils/LayerManager';
import TimeManager from './utils/TimeManager';
import ChartHeader from './components/ChartHeader';
import CCGDateControls from './components/CCGDateControls';
import ChartForm from './components/ChartForm';
import NatalDisplayControls from './components/NatalDisplayControls';
import TransitControls from './components/TransitControls';
import CCGControls from './components/CCGControls';
import HumanDesignControls from './components/HumanDesignControls';
import useChartData from './hooks/useChartData';
import useAstroData from './hooks/useAstroData';
import useTransitData from './hooks/useTransitData';
import useCCGData from './hooks/useCCGData';
import useHumanDesignData from './hooks/useHumanDesignData';

const GEOAPIFY_API_KEY = '89b7ba6d03ca4cfc871fac9f5d3dade0'
const TIMEZONEDB_API_KEY = 'YHIFBIVJIA14'

function App() {
  // Force re-render trigger for map updates
  const [mapUpdateTrigger, setMapUpdateTrigger] = useState(0);
  const forceMapUpdate = React.useCallback(() => {
    setMapUpdateTrigger(prev => prev + 1);
  }, []);

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
  // Replace chart, astro, transit, and CCG state/handlers with hooks
  const { response, loadingStep: chartLoading, error: chartError, fetchChart } = useChartData(timeManager);
  const { astroData, fetchAstro } = useAstroData(layerManager, forceMapUpdate);
  const { isTransitEnabled, fetchTransits } = useTransitData(layerManager, forceMapUpdate, timeManager);
  const { fetchCCG } = useCCGData(layerManager, forceMapUpdate);
  const { fetchHumanDesign } = useHumanDesignData(layerManager, forceMapUpdate);

  // Combine loading and error states for display
  const loadingStep = chartLoading;
  const error = chartError;

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

    // Set up transit layer with unique colors 
    layerManager.addLayer('transit', {
      visible: false,
      order: 1,
      type: 'transit',
      style: {
        color: '#ff6600', // Bright orange
        width: 3,         // Slightly wider than natal
        opacity: 0.9      // Good visibility
      },
      subLayers: {
        ac_dc: true,
        ic_mc: true,
        parans: true
      }
    });

    // Register CCG layer (with hermetic lots toggle)
    layerManager.addLayer('CCG', {
      visible: false,
      order: 1.5,
      type: 'overlay',
      style: { color: '#4A90E2', width: 3, opacity: 0.8 },
      subLayers: { ac_dc: true, ic_mc: true, parans: true, lots: true }
    });

    // Register Human Design layer (with all natal features except fixed stars)
    layerManager.addLayer('HD_DESIGN', {
      visible: false,
      order: 2,
      type: 'overlay',
      style: { color: '#D47AFF', width: 3, opacity: 0.85 }, // Purple color for HD
      subLayers: { 
        ac_dc: true, 
        ic_mc: true, 
        parans: true, 
        lots: true,
        aspects: true // HD includes aspects unlike CCG/Transit
      }
    });

    // Listen for layer changes
    const unsubscribe = layerManager.addListener((event) => {
      if (event === 'layerToggled' || event === 'subLayerToggled') {
        // Force re-render when layers change
        forceMapUpdate();
      }
    });

    return unsubscribe;
  }, [layerManager, forceMapUpdate]);

  // Current transit date/time state
  const [currentTransitDateTime, setCurrentTransitDateTime] = useState(new Date());

  // Update handleGenerateTransits to use fetchTransits
  const handleGenerateTransits = async (customDateTime = null) => {
    try {
      console.log('handleGenerateTransits called with:', customDateTime);
      console.log('formData:', formData);
      console.log('currentTransitDateTime:', currentTransitDateTime);
      await fetchTransits(formData, customDateTime || currentTransitDateTime);
      console.log('fetchTransits completed');
    } catch (error) {
      console.error('Error in handleGenerateTransits:', error);
    }
  };

  // CCG date state (default to today)
  const [ccgDate, setCCGDate] = useState(() => {
    const today = new Date();
    return today.toISOString().slice(0, 10);
  });

  // Re-generate CCG overlay when ccgDate changes
  useEffect(() => {
    if (layerManager.isLayerVisible('CCG')) {
      handleGenerateCCG();
    }
    // eslint-disable-next-line
  }, [ccgDate]);

  // UI toggles for JSON display
  const [showJson, setShowJson] = useState(false);
  const [showAstroJson, setShowAstroJson] = useState(false);
  // Progress/animation indicator
  // Natal/planet toggles
  const [lineToggles, setLineToggles] = useState({
    planet: true,
    mc_aspects: true,
    ac_aspects: true,
    fixed_star: true,
    hermetic_lot: true,
    parans: true,
    ic_mc: true,
    ac_dc: true
  });
  // CCG toggles (mirrors natal toggles)
  const [ccgLineToggles, setCCGLineToggles] = useState({
    planet: true,
    mc_aspects: true,
    ac_aspects: true,
    hermetic_lot: true,
    parans: true,
    ic_mc: true,
    ac_dc: true
  });
  // Human Design toggles (includes aspects unlike CCG/Transit)
  const [hdLineToggles, setHDLineToggles] = useState({
    planet: true,
    mc_aspects: true,
    ac_aspects: true,
    hermetic_lot: true,
    parans: true,
    ic_mc: true,
    ac_dc: true
  });
  const allBodies = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Lunar Node",
    "Chiron", "Ceres", "Pallas", "Juno", "Vesta", "Black Moon Lilith", "Pholus"
  ];
  const ccgBodies = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "Chiron", "Ceres", "Pallas", "Juno", "Vesta", "Black Moon Lilith", "Pholus"
  ];
  const [bodyToggles, setBodyToggles] = useState(
    Object.fromEntries(allBodies.map(name => [name, true]))
  );
  // CCG body toggles (exclude nodes)
  const [ccgBodyToggles, setCCGBodyToggles] = useState(
    Object.fromEntries(ccgBodies.map(name => [name, true]))
  );
  // Human Design body toggles (includes all bodies like natal)
  const [hdBodyToggles, setHDBodyToggles] = useState(
    Object.fromEntries(allBodies.map(name => [name, true]))
  );
  const [showBodyAccordion, setShowBodyAccordion] = useState(true);
  const [ccgShowBodyAccordion, setCCGShowBodyAccordion] = useState(true);
  const [hdShowBodyAccordion, setHDShowBodyAccordion] = useState(true);

  // Transit toggles (similar to CCG but separate)
  const [transitLineToggles, setTransitLineToggles] = useState({
    planet: true,
    mc_aspects: true,
    ac_aspects: true,
    hermetic_lot: true,
    parans: true,
    ic_mc: true,
    ac_dc: true
  });
  // Transit bodies (all bodies like natal)
  const transitBodies = allBodies;
  const [transitBodyToggles, setTransitBodyToggles] = useState(
    Object.fromEntries(transitBodies.map(name => [name, true]))
  );
  const [transitShowBodyAccordion, setTransitShowBodyAccordion] = useState(true);

  // Line labels
  const lineLabels = {
    planet: 'Planet Lines',
    mc_aspects: 'MC Aspects',
    ac_aspects: 'AC Aspects',
    fixed_star: 'Fixed Stars',
    hermetic_lot: 'Hermetic Lots',
    parans: 'Parans',
  };
  // Form submit handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    const chartData = await fetchChart(formData);
    if (chartData) {
      await fetchAstro(formData, chartData);
    }
  };
  // Restore handleGenerateCCG for CCGControls
  const handleGenerateCCG = async () => {
    await fetchCCG(formData, ccgDate);
    forceMapUpdate(); // Ensure map updates immediately after CCG overlay is generated
  };

  // Human Design handler
  const handleGenerateHD = async () => {
    await fetchHumanDesign(formData);
    forceMapUpdate(); // Ensure map updates immediately after HD overlay is generated
  };

  // Merged/filtered data for map
  const mergedFilteredData = React.useMemo(() => {
    let features = [];
    // Natal layer
    if (astroData && layerManager.isLayerVisible('natal')) {
      let natalFeatures = astroData.features || [];
      natalFeatures = natalFeatures.filter(f => {
        // FIRST: Exclude any features tagged as CCG
        if (f.properties?.layer === 'CCG') return false;
        
        const cat = f.properties?.category;
        const lineType = f.properties?.line_type;
        const aspectTo = f.properties?.to;
        // Parans toggle
        if (cat === 'parans' && !lineToggles.parans) return false;
        
        // Handle hermetic lots first - they have their own toggle and should NOT be affected by IC/MC toggle
        if (cat === 'hermetic_lot' || cat === 'lot' || f.properties?.body_type === 'lot') {
          return lineToggles.hermetic_lot; // Only check hermetic lot toggle, ignore IC/MC toggle
        }
        
        // Aspect handling
        if (cat === 'aspect') {
          if (aspectTo === 'MC' || lineType === 'MC' || lineType === 'IC') {
            if (!lineToggles.mc_aspects) return false;
          } else if (aspectTo === 'ASC' || lineType === 'ASC' || lineType === 'DSC' || lineType === 'HORIZON') {
            if (!lineToggles.ac_aspects) return false;
          } else {
            if (!lineToggles.mc_aspects && !lineToggles.ac_aspects) return false;
          }
        }
        // IC/MC line toggle
        if (lineType === 'IC' || lineType === 'MC') {
          if (!lineToggles.ic_mc) return false;
        }
        // AC/DC line toggle
        if (lineType === 'AC' || lineType === 'DC' || lineType === 'HORIZON') {
          if (!lineToggles.ac_dc) return false;
        }
        // Other categories
        if (cat in lineToggles && !lineToggles[cat]) return false;
        // Planet/body filtering
        let body = f.properties?.planet || f.properties?.body || f.properties?.name;
        if (body === 'Pallas Athena') body = 'Pallas';
        if (body === 'Lilith' || body === 'BML' || body === 'Black Moon') body = 'Black Moon Lilith';
        if (body === 'North Node' || body === 'NN' || body === 'Rahu') body = 'Lunar Node';
        if (body && bodyToggles[body] === false) return false;
        return true;
      });
      features = features.concat(natalFeatures.map(f => ({ ...f, layerName: 'natal' })));
    }
    // CCG overlay - simplified filtering using unified controls
    const ccgLayer = layerManager.getLayer('CCG');
    if (layerManager.isLayerVisible('CCG') && ccgLayer && ccgLayer.data && ccgLayer.data.features) {
      let ccgFeatures = ccgLayer.data.features;
      ccgFeatures = ccgFeatures.filter(f => {
        // FIRST: Only process features that are properly tagged as CCG
        if (f.properties?.layer !== 'CCG') return false;
        
        const cat = f.properties?.category;
        const lineType = f.properties?.line_type;
        
        // CCG Feature Type Filtering
        if (cat === 'parans' && !ccgLineToggles.parans) return false;
        
        // Handle hermetic lots first - they have their own toggle and should NOT be affected by IC/MC toggle
        if (cat === 'hermetic_lot' || cat === 'lot' || f.properties?.body_type === 'lot') {
          return ccgLineToggles.hermetic_lot; // Only check hermetic lot toggle, ignore IC/MC toggle
        }
        
        // CCG Body Filtering (extract body name first)
        let body = f.properties?.planet || f.properties?.body || f.properties?.name;
        // Remove " CCG" suffix if present in the name
        if (body && body.endsWith(' CCG')) {
          body = body.replace(' CCG', '');
        }
        if (body === 'Pallas Athena') body = 'Pallas';
        if (body === 'Lilith' || body === 'BML' || body === 'Black Moon') body = 'Black Moon Lilith';
        if (body === 'North Node' || body === 'NN' || body === 'Rahu') body = 'Lunar Node';
        
        // For planet lines (IC/MC/AC/DC), check both line type AND body toggles
        if (lineType === 'IC' || lineType === 'MC') {
          if (!ccgLineToggles.ic_mc) return false; // Line type disabled
          if (body && ccgBodyToggles[body] === false) return false; // Body disabled
        } else if (lineType === 'AC' || lineType === 'DC' || lineType === 'HORIZON') {
          if (!ccgLineToggles.ac_dc) return false; // Line type disabled  
          if (body && ccgBodyToggles[body] === false) return false; // Body disabled
        } else {
          // For other features (parans, etc.), check body if it exists
          if (body && ccgBodyToggles[body] === false) return false;
        }
        
        return true;
      });
      features = features.concat(ccgFeatures.map(f => ({ ...f, layerName: 'CCG' })));
    }

    // Human Design overlay - filtering using unified controls
    const hdLayer = layerManager.getLayer('HD_DESIGN');
    console.log('[DEBUG] HD Layer in mergedFilteredData:', hdLayer);
    if (layerManager.isLayerVisible('HD_DESIGN') && hdLayer && hdLayer.data && hdLayer.data.features) {
      console.log('[DEBUG] HD Layer visible and has data, features count:', hdLayer.data.features.length);
      let hdFeatures = hdLayer.data.features;
      hdFeatures = hdFeatures.filter(f => {
        // FIRST: Only process features that are properly tagged as HD_DESIGN
        if (f.properties?.layer !== 'HD_DESIGN') return false;
        
        const cat = f.properties?.category;
        const lineType = f.properties?.line_type;
        
        // HD Feature Type Filtering
        if (cat === 'parans' && !hdLineToggles.parans) return false;
        
        // Handle hermetic lots first - they have their own toggle and should NOT be affected by IC/MC toggle
        if (cat === 'hermetic_lot' || cat === 'lot' || f.properties?.body_type === 'lot') {
          return hdLineToggles.hermetic_lot; // Only check hermetic lot toggle, ignore IC/MC toggle
        }
        
        // Aspect handling for HD (unlike CCG/Transit, HD includes aspects)
        if (cat === 'aspect') {
          const aspectTo = f.properties?.to;
          if (aspectTo === 'MC' && !hdLineToggles.mc_aspects) return false;
          if (aspectTo === 'AC' && !hdLineToggles.ac_aspects) return false;
          if (!aspectTo) {
            if (!hdLineToggles.mc_aspects && !hdLineToggles.ac_aspects) return false;
          }
        }
        
        // HD Body Filtering (extract body name first)
        let body = f.properties?.planet || f.properties?.body || f.properties?.name;
        // Remove " HD" suffix if present in the name
        if (body && body.endsWith(' HD')) {
          body = body.replace(' HD', '');
        }
        if (body === 'Pallas Athena') body = 'Pallas';
        if (body === 'Lilith' || body === 'BML' || body === 'Black Moon') body = 'Black Moon Lilith';
        if (body === 'North Node' || body === 'NN' || body === 'Rahu') body = 'Lunar Node';
        
        // For planet lines (IC/MC/AC/DC), check both line type AND body toggles
        if (lineType === 'IC' || lineType === 'MC') {
          if (!hdLineToggles.ic_mc) return false; // Line type disabled
          if (body && hdBodyToggles[body] === false) return false; // Body disabled
        } else if (lineType === 'AC' || lineType === 'DC' || lineType === 'HORIZON') {
          if (!hdLineToggles.ac_dc) return false; // Line type disabled  
          if (body && hdBodyToggles[body] === false) return false; // Body disabled
        } else {
          // For other features (parans, aspects, etc.), check body if it exists
          if (body && hdBodyToggles[body] === false) return false;
        }
        
        return true;
      });
      console.log('[DEBUG] HD Features after filtering:', hdFeatures.length);
      features = features.concat(hdFeatures.map(f => ({ ...f, layerName: 'HD_DESIGN' })));
    }

    // Transit Overlay
    if (layerManager.isLayerVisible('transit')) {
      console.log('Transit layer is visible, processing transit data...');
      const transitData = layerManager.getLayer('transit')?.data;
      console.log('Transit data from layer manager:', transitData);
      let transitFeatures = transitData?.features || [];
      console.log('Transit features before filtering:', transitFeatures.length);
      
      transitFeatures = transitFeatures.filter(f => {
        try {
          // Defensive null checks
          if (!f || !f.properties) return false;
          
          console.log('Processing transit feature:', f.properties);
          
          if (f.properties?.layer !== 'transit') {
            console.log('Feature filtered out - not transit layer:', f.properties?.layer);
            return false;
          }
          
          const cat = f.properties?.category;
          const lineType = f.properties?.line_type;
          
          // Transit Feature Type Filtering
          if (cat === 'parans' && !transitLineToggles.parans) return false;
          
          // Handle hermetic lots first - they have their own toggle and should NOT be affected by IC/MC toggle
          if (cat === 'hermetic_lot' || cat === 'lot' || f.properties?.body_type === 'lot') {
            return transitLineToggles.hermetic_lot; // Only check hermetic lot toggle, ignore IC/MC toggle
          }
          
          // Transit Body Filtering (extract body name first)
          let body = f.properties?.planet || f.properties?.body || f.properties?.name;
          // Remove " Transit" suffix if present in the name
          if (body && body.endsWith && body.endsWith(' Transit')) {
            body = body.replace(' Transit', '');
          }
          if (body === 'Pallas Athena') body = 'Pallas';
          if (body === 'Lilith' || body === 'BML' || body === 'Black Moon') body = 'Black Moon Lilith';
          if (body === 'North Node' || body === 'NN' || body === 'Rahu') body = 'Lunar Node';
          
          // For planet lines (IC/MC/AC/DC), check both line type AND body toggles
          if (lineType === 'IC' || lineType === 'MC') {
            if (!transitLineToggles.ic_mc) return false; // Line type disabled
            if (body && transitBodyToggles[body] === false) return false; // Body disabled
          } else if (lineType === 'AC' || lineType === 'DC' || lineType === 'HORIZON') {
            if (!transitLineToggles.ac_dc) return false; // Line type disabled  
            if (body && transitBodyToggles[body] === false) return false; // Body disabled
          } else {
            // For other features (parans, etc.), check body if it exists
            if (body && transitBodyToggles[body] === false) return false;
          }
          
          return true;
        } catch (err) {
          console.error('Error filtering transit feature:', err, f);
          return false; // Filter out problematic features
        }
      });
      features = features.concat(transitFeatures.map(f => ({ ...f, layerName: 'transit' })));
    }

    console.log('[DEBUG] Total merged features:', features.length);
    return { features };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [astroData, lineToggles, bodyToggles, ccgLineToggles, ccgBodyToggles, hdLineToggles, hdBodyToggles, transitLineToggles, transitBodyToggles, layerManager, mapUpdateTrigger]);

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
      <ChartForm formData={formData} setFormData={setFormData} onSubmit={handleSubmit} error={error} />
      
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
            <NatalDisplayControls
              lineToggles={lineToggles}
              setLineToggles={setLineToggles}
              lineLabels={lineLabels}
              allBodies={allBodies}
              bodyToggles={bodyToggles}
              setBodyToggles={setBodyToggles}
              showBodyAccordion={showBodyAccordion}
              setShowBodyAccordion={setShowBodyAccordion}
            />
            {/* CCG Controls Section */}
            <CCGControls
              layerManager={layerManager}
              forceMapUpdate={forceMapUpdate}
              ccgDate={ccgDate}
              setCCGDate={setCCGDate}
              handleGenerateCCG={handleGenerateCCG}
              lineToggles={ccgLineToggles}
              setLineToggles={setCCGLineToggles}
              allBodies={ccgBodies}
              bodyToggles={ccgBodyToggles}
              setBodyToggles={setCCGBodyToggles}
              showBodyAccordion={ccgShowBodyAccordion}
              setShowBodyAccordion={setCCGShowBodyAccordion}
            />
            {/* Human Design Controls Section */}
            <HumanDesignControls
              layerManager={layerManager}
              forceMapUpdate={forceMapUpdate}
              handleGenerateHD={handleGenerateHD}
              loadingStep={loadingStep}
              lineToggles={hdLineToggles}
              setLineToggles={setHDLineToggles}
              allBodies={allBodies}
              bodyToggles={hdBodyToggles}
              setBodyToggles={setHDBodyToggles}
              showBodyAccordion={hdShowBodyAccordion}
              setShowBodyAccordion={setHDShowBodyAccordion}
            />
            {/* Transit Controls */}
            <TransitControls
              isTransitEnabled={isTransitEnabled}
              layerManager={layerManager}
              forceMapUpdate={forceMapUpdate}
              handleGenerateTransits={handleGenerateTransits}
              loadingStep={loadingStep}
              currentTransitDateTime={currentTransitDateTime}
              setCurrentTransitDateTime={setCurrentTransitDateTime}
              lineToggles={transitLineToggles}
              setLineToggles={setTransitLineToggles}
              allBodies={transitBodies}
              bodyToggles={transitBodyToggles}
              setBodyToggles={setTransitBodyToggles}
              showBodyAccordion={transitShowBodyAccordion}
              setShowBodyAccordion={setTransitShowBodyAccordion}
            />
          </div>
        </>
      )}
    </div>
  )
}

export default App

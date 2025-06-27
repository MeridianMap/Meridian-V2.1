import { useState } from 'react';
import axios from 'axios';

export default function useTransitData(layerManager, forceMapUpdate, timeManager) {
  const [transitData, setTransitData] = useState(null);
  const [isTransitEnabled, setIsTransitEnabled] = useState(false);
  const [loadingStep, setLoadingStep] = useState(null);
  const [error, setError] = useState(null);

  const fetchTransits = async (formData, currentTransitDateTime) => {
    if (!timeManager.isReadyForTransits()) {
      setError('Natal chart must be generated first before calculating transits.');
      return;
    }
    try {
      setLoadingStep('transit_ephemeris');
      const targetDateTime = currentTransitDateTime;
      const year = targetDateTime.getFullYear();
      const month = String(targetDateTime.getMonth() + 1).padStart(2, '0');
      const day = String(targetDateTime.getDate()).padStart(2, '0');
      const hours = String(targetDateTime.getHours()).padStart(2, '0');
      const minutes = String(targetDateTime.getMinutes()).padStart(2, '0');
      const transitParams = {
        birth_date: `${year}-${month}-${day}`,
        birth_time: `${hours}:${minutes}`,
        timezone: formData.timezone,
        coordinates: timeManager.coordinates
      };
      const transitChartPayload = {
        name: `${formData.name} - Transits`,
        birth_city: formData.birth_city,
        birth_state: formData.birth_state,
        birth_country: formData.birth_country,
        ...transitParams,
        use_extended_planets: true
      };
      const transitChartResult = await axios.post('/api/calculate', transitChartPayload);
      setLoadingStep('transit_astro');
      
      const transitPayload = {
        ...transitParams,
        coordinates: transitParams.coordinates,
        planets: transitChartResult.data.planets,
        utc_time: transitChartResult.data.utc_time,
        lots: transitChartResult.data.lots,
        layer_type: 'transit', // Add layer type for backend tagging
        include_aspects: false,
        include_fixed_stars: false,
        include_hermetic_lots: false,
        include_parans: true,
        include_ac_dc: true,
        include_ic_mc: true
      };
      const transitRes = await axios.post('/api/astrocartography', transitPayload);
      layerManager.setLayerData('transit', transitRes.data);
      setTransitData(transitRes.data);
      layerManager.setLayerVisible('transit', true);
      setIsTransitEnabled(true);
      forceMapUpdate();
      setLoadingStep('done');
    } catch (err) {
      console.error('Transit generation error:', err);
      setError(`Failed to generate transit data: ${err.message}`);
      setLoadingStep(null);
    }
  };

  return { transitData, isTransitEnabled, loadingStep, error, fetchTransits, setTransitData };
}

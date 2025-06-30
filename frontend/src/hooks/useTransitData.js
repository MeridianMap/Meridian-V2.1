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
      console.log('🟪 fetchTransits called with:', { formData, currentTransitDateTime });
      
      const targetDateTime = currentTransitDateTime;
      const year = targetDateTime.getFullYear();
      const month = String(targetDateTime.getMonth() + 1).padStart(2, '0');
      const day = String(targetDateTime.getDate()).padStart(2, '0');
      const hours = String(targetDateTime.getHours()).padStart(2, '0');
      const minutes = String(targetDateTime.getMinutes()).padStart(2, '0');
      
      const transitPayload = {
        name: `${formData.name || 'Transit'} - Transits`,
        birth_date: `${year}-${month}-${day}`,
        birth_time: `${hours}:${minutes}`,
        birth_city: formData.birth_city,
        birth_state: formData.birth_state,
        birth_country: formData.birth_country,
        timezone: formData.timezone,
        use_extended_planets: true,
        layer_type: 'transit' // Add layer type for backend tagging
      };
      
      console.log('🟪 Transit API payload:', transitPayload);
      const transitChartResult = await axios.post('/api/calculate', transitPayload);
      console.log('🟪 Transit chart result:', transitChartResult.data);
      
      // Use the astrocartography data from the chart response
      if (transitChartResult.data.astrocartography) {
        // Tag all features with transit layer type
        const taggedData = {
          ...transitChartResult.data.astrocartography,
          features: transitChartResult.data.astrocartography.features.map(f => ({
            ...f,
            properties: {
              ...f.properties,
              layer: 'transit'
            }
          }))
        };
        
        layerManager.setLayerData('transit', taggedData);
        layerManager.setLayerVisible('transit', true);
        setIsTransitEnabled(true);
        forceMapUpdate();
        console.log('🟪 Transit data set with', taggedData.features.length, 'features');
      } else {
        console.log('🟪 No astrocartography data in transit response');
      }
      
      setLoadingStep('done');
    } catch (err) {
      console.error('🟪 Transit generation error:', err);
      setError(`Failed to generate transit data: ${err.message}`);
      setLoadingStep(null);
    }
  };

  return { transitData, isTransitEnabled, loadingStep, error, fetchTransits, setTransitData };
}

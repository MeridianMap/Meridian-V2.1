import { useState } from 'react';
import axios from 'axios';

export default function useHumanDesignData(layerManager, forceMapUpdate) {
  const [loadingStep, setLoadingStep] = useState(null);
  const [error, setError] = useState(null);
  const fetchHumanDesign = async (formData) => {
    setError(null);
    setLoadingStep('chart_calculation');
    
    try {
      // First, get the chart data to obtain coordinates
      const chartResult = await axios.post('/api/calculate', {
        ...formData
      });
      
      setLoadingStep('hd_calculation');
      
      // Prepare Human Design request with layer type
      const hdPayload = {
        birth_date: formData.birth_date,
        birth_time: formData.birth_time,
        timezone: formData.timezone,
        coordinates: chartResult.data.coordinates,
        house_system: formData.house_system || 'whole_sign',
        use_extended_planets: true,
        filter_options: {
          layer_type: "HD_DESIGN",
          include_parans: true,
          include_ac_dc: true,
          include_ic_mc: true,
          include_aspects: true,
          include_fixed_stars: false, // HD never includes fixed stars
          include_hermetic_lots: true,
          subLayers: {
            ac_dc: layerManager.isSubLayerVisible('HD_DESIGN', 'ac_dc'),
            ic_mc: layerManager.isSubLayerVisible('HD_DESIGN', 'ic_mc'),
            parans: layerManager.isSubLayerVisible('HD_DESIGN', 'parans'),
            lots: layerManager.isSubLayerVisible('HD_DESIGN', 'lots'),
            aspects: layerManager.isSubLayerVisible('HD_DESIGN', 'aspects')
          }
        }
      };

      console.log('[HD] Sending Human Design request:', hdPayload);
      
      const hdRes = await axios.post('/api/astrocartography', hdPayload);
      
      console.log('[HD] Received Human Design response:', hdRes.data);
      
      // Store the data in layer manager
      layerManager.setLayerData('HD_DESIGN', hdRes.data);
      layerManager.setLayerVisible('HD_DESIGN', true);
      
      forceMapUpdate();
      setLoadingStep('done');
      
    } catch (err) {
      console.error('Human Design generation error:', err);
      setError(`Failed to generate Human Design data: ${err.message}`);
      setLoadingStep(null);
    }
  };

  return { loadingStep, error, fetchHumanDesign };
}

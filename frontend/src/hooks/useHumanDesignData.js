import { useState } from 'react';
import axios from 'axios';

export default function useHumanDesignData(layerManager, forceMapUpdate) {
  const [loadingStep, setLoadingStep] = useState(null);
  const [error, setError] = useState(null);
  const fetchHumanDesign = async (formData) => {
    setError(null);
    setLoadingStep('hd_calculation');
    
    try {
      console.log('🟣 fetchHumanDesign called with:', formData);
      
      // Validate required fields
      if (!formData.birth_date || !formData.birth_time || !formData.timezone) {
        throw new Error('Missing required birth data for Human Design calculation');
      }
      
      const hdPayload = {
        name: `${formData.name || 'HD'} - Human Design`,
        birth_date: formData.birth_date,
        birth_time: formData.birth_time,
        birth_city: formData.birth_city,
        birth_state: formData.birth_state,
        birth_country: formData.birth_country,
        timezone: formData.timezone,
        house_system: formData.house_system || 'whole_sign',
        use_extended_planets: true,
        layer_type: 'HD_DESIGN' // Add layer type for backend tagging
      };
      
      console.log('🟣 HD API payload:', hdPayload);
      const hdResult = await axios.post('/api/calculate', hdPayload);
      console.log('🟣 HD chart result:', hdResult.data);
      
      // Use the astrocartography data from the chart response
      if (hdResult.data.astrocartography) {
        // Tag all features with HD_DESIGN layer type
        const taggedData = {
          ...hdResult.data.astrocartography,
          features: hdResult.data.astrocartography.features.map(f => ({
            ...f,
            properties: {
              ...f.properties,
              layer: 'HD_DESIGN'
            }
          }))
        };
        
        // Store the data in layer manager
        layerManager.setLayerData('HD_DESIGN', taggedData);
        layerManager.setLayerVisible('HD_DESIGN', true);
        
        forceMapUpdate();
        console.log('🟣 HD data set with', taggedData.features.length, 'features');
      } else {
        console.log('🟣 No astrocartography data in HD response');
      }
      
      setLoadingStep('done');
      setLoadingStep('done');
    } catch (err) {
      console.error('🟣 Human Design generation error:', err);
      setError(`Failed to generate Human Design data: ${err.message}`);
      setLoadingStep(null);
    }
  };

  return { loadingStep, error, fetchHumanDesign };
}

import { useState } from 'react';
import axios from 'axios';

export default function useCCGData(layerManager, forceMapUpdate) {
  const [loadingStep, setLoadingStep] = useState(null);
  const [error, setError] = useState(null);

  const fetchCCG = async (formData, ccgDate) => {
    setError(null);
    setLoadingStep('ephemeris');
    try {
      console.log('🟦 fetchCCG called with:', { formData, ccgDate });
      
      // Validate required fields
      if (!formData.birth_date || !formData.birth_time || !formData.timezone) {
        throw new Error('Missing required birth data for CCG calculation');
      }
      
      const ccgPayload = {
        name: `${formData.name || 'CCG'} - CCG`,
        birth_date: ccgDate, // Use CCG date instead of birth date
        birth_time: formData.birth_time,
        birth_city: formData.birth_city,
        birth_state: formData.birth_state,
        birth_country: formData.birth_country,
        timezone: formData.timezone,
        use_extended_planets: true,
        layer_type: 'CCG' // Add layer type for backend tagging
      };
      
      console.log('🟦 CCG API payload:', ccgPayload);
      const chartResult = await axios.post('/api/calculate', ccgPayload);
      console.log('🟦 CCG chart result:', chartResult.data);
      
      // Use the astrocartography data from the chart response
      if (chartResult.data.astrocartography) {
        // Tag all features with CCG layer type
        const taggedData = {
          ...chartResult.data.astrocartography,
          features: chartResult.data.astrocartography.features.map(f => ({
            ...f,
            properties: {
              ...f.properties,
              layer: 'CCG'
            }
          }))
        };
        
        layerManager.setLayerData('CCG', taggedData);
        layerManager.setLayerVisible('CCG', true);
        forceMapUpdate();
        console.log('🟦 CCG data set with', taggedData.features.length, 'features');
      } else {
        console.log('🟦 No astrocartography data in CCG response');
      }
      
      setLoadingStep('done');
    } catch (error) {
      console.error('🟦 CCG error:', error);
      setError('Failed to generate CCG overlay.');
      setLoadingStep(null);
    }
  };

  return { loadingStep, error, fetchCCG };
}

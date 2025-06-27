import { useState } from 'react';
import axios from 'axios';

export default function useCCGData(layerManager, forceMapUpdate) {
  const [loadingStep, setLoadingStep] = useState(null);
  const [error, setError] = useState(null);

  const fetchCCG = async (formData, ccgDate) => {
    setError(null);
    setLoadingStep('ephemeris');
    try {
      const chartResult = await axios.post('/api/calculate', {
        ...formData,
        progressed_for: ["Sun", "Moon", "Mercury", "Venus", "Mars"],
        progression_method: "secondary",
        progressed_date: ccgDate
      });
      setLoadingStep('astro');
      const astroRes = await axios.post('/api/astrocartography', {
        birth_date: formData.birth_date,
        birth_time: formData.birth_time,
        coordinates: chartResult.data.coordinates,
        planets: chartResult.data.planets,
        utc_time: chartResult.data.utc_time,
        lots: chartResult.data.lots,
        include_parans: true,
        include_angles: ["AC", "DC", "MC", "IC"],
        include_aspects: false,
        filter_options: {
          layer_type: "CCG",
          include_parans: true,
          include_ac_dc: true,
          include_ic_mc: true,
          include_aspects: false,
          include_fixed_stars: false,
          subLayers: {
            ac_dc: layerManager.isSubLayerVisible('CCG', 'ac_dc'),
            ic_mc: layerManager.isSubLayerVisible('CCG', 'ic_mc'),
            parans: layerManager.isSubLayerVisible('CCG', 'parans'),
            lots: layerManager.isSubLayerVisible('CCG', 'lots')
          }
        }
      });
      layerManager.setLayerData('CCG', astroRes.data);
      layerManager.setLayerVisible('CCG', true);
      forceMapUpdate();
      setLoadingStep('done');
    } catch {
      setError('Failed to generate CCG overlay.');
      setLoadingStep(null);
    }
  };

  return { loadingStep, error, fetchCCG };
}

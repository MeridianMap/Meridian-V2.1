import { useState } from 'react';
import axios from 'axios';

export default function useAstroData(layerManager, forceMapUpdate) {
  const [astroData, setAstroData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchAstro = async (formData, chartData) => {
    setLoading(true);
    try {
      const payload = {
        birth_date: formData.birth_date,
        birth_time: formData.birth_time,
        timezone: formData.timezone,
        coordinates: { latitude: chartData.coordinates.latitude, longitude: chartData.coordinates.longitude },
        planets: chartData.planets,
        utc_time: chartData.utc_time,
        lots: chartData.lots,
        include_aspects: true,
        include_fixed_stars: true,
        include_hermetic_lots: true,
        include_parans: true,
        include_ac_dc: true,
        include_ic_mc: true
      };
      const res = await axios.post('/api/astrocartography', payload);
      setAstroData(res.data);
      layerManager.setLayerData('natal', res.data);
      forceMapUpdate();
      return res.data;
    } catch (error) {
      console.error('Astrocartography fetch failed:', error);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { astroData, fetchAstro, setAstroData, loading };
}

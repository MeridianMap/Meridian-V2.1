import { useState } from 'react';
import { calculateChart } from '../apiClient';

export default function useChartData(timeManager) {
  const [response, setResponse] = useState(null);
  const [loadingStep, setLoadingStep] = useState(null);
  const [error, setError] = useState(null);

  const fetchChart = async (formData) => {
    setError(null);
    setLoadingStep('ephemeris');
    try {
      console.log('🚀 Calling calculateChart with:', formData);
      const chartResult = await calculateChart({ ...formData, use_extended_planets: true });
      console.log('✅ Chart result received:', {
        keys: Object.keys(chartResult),
        astrocartography_features: chartResult.astrocartography?.features?.length || 0,
        chart_data_keys: Object.keys(chartResult.chart_data || {}),
      });
      setResponse(chartResult);
      timeManager.setNatalTime && timeManager.setNatalTime({
        birth_date: formData.birth_date,
        birth_time: formData.birth_time,
        timezone: formData.timezone,
        coordinates: chartResult.coordinates
      });
      setLoadingStep('done');
      return chartResult;
    } catch (e) {
      setError(e.message || 'Failed to generate chart.');
      setLoadingStep(null);
      return null;
    }
  };

  return { response, loadingStep, error, fetchChart, setError, setLoadingStep };
}

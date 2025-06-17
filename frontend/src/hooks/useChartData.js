import { useState } from 'react';
import axios from 'axios';

export default function useChartData(timeManager) {
  const [response, setResponse] = useState(null);
  const [loadingStep, setLoadingStep] = useState(null);
  const [error, setError] = useState(null);

  const fetchChart = async (formData) => {
    setError(null);
    setLoadingStep('ephemeris');
    try {
      const chartResult = await axios.post('http://localhost:5000/api/calculate', {
        ...formData,
        use_extended_planets: true
      });
      setResponse(chartResult.data);
      timeManager.setNatalTime({
        birth_date: formData.birth_date,
        birth_time: formData.birth_time,
        timezone: formData.timezone,
        coordinates: chartResult.data.coordinates
      });
      setLoadingStep('done');
      return chartResult.data;
    } catch (e) {
      setError('Failed to generate chart.');
      setLoadingStep(null);
      return null;
    }
  };

  return { response, loadingStep, error, fetchChart, setError, setLoadingStep };
}

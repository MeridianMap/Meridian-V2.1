import { useState } from 'react';
import axios from 'axios';

const GEOAPIFY_API_KEY = import.meta.env.VITE_GEO_API_KEY;
const TIMEZONEDB_API_KEY = 'YHIFBIVJIA14';

function useCitySuggestions(formData, setFormData) {
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const handleInputChange = async (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (name === 'birth_city' && value.length > 2) {
      try {
        const result = await axios.get(
          `https://api.geoapify.com/v1/geocode/autocomplete?text=${encodeURIComponent(value)}&limit=5&type=city&format=json&apiKey=${GEOAPIFY_API_KEY}`
        );
        setSuggestions(result.data.results);
        setShowSuggestions(true);
      } catch (err) {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }
  };

  const handleSuggestionSelect = async (suggestion) => {
    const city = suggestion.city || suggestion.properties?.city || '';
    const state = suggestion.state || suggestion.properties?.state || '';
    const country = suggestion.country || suggestion.properties?.country || '';
    const lat = suggestion.lat || suggestion.properties?.lat || suggestion.geometry?.coordinates?.[1];
    const lon = suggestion.lon || suggestion.properties?.lon || suggestion.geometry?.coordinates?.[0];
    if (!lat || !lon) return;
    const displayLocation = state ? `${city}, ${state}` : city;
    setFormData(prev => ({ ...prev, birth_city: displayLocation, birth_state: state, birth_country: country, timezone: '' }));
    try {
      const tzRes = await axios.get(`https://api.timezonedb.com/v2.1/get-time-zone`, {
        params: { key: TIMEZONEDB_API_KEY, format: 'json', by: 'position', lat, lng: lon }
      });
      setFormData(prev => ({ ...prev, timezone: tzRes.data.zoneName }));
      setShowSuggestions(false);
    } catch {
      setShowSuggestions(false);
    }
  };

  return {
    suggestions,
    showSuggestions,
    handleInputChange,
    handleSuggestionSelect,
    setShowSuggestions
  };
}

export default useCitySuggestions;

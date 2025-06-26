import { useState, useEffect } from 'react';

const useHouseSystems = () => {
  const [houseSystems, setHouseSystems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHouseSystems = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/house-systems');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setHouseSystems(data.house_systems || []);
        setError(null);
      } catch (err) {
        console.error('Error fetching house systems:', err);
        setError(err.message);
        // Fallback to basic house systems if API fails
        setHouseSystems([
          { id: 'whole_sign', name: 'Whole Sign', description: 'Each zodiac sign equals one house' },
          { id: 'placidus', name: 'Placidus', description: 'Most popular modern system' },
          { id: 'koch', name: 'Koch', description: 'Similar to Placidus' },
          { id: 'equal', name: 'Equal House', description: 'Equal 30° segments from Ascendant' }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchHouseSystems();
  }, []);

  return { houseSystems, loading, error };
};

export default useHouseSystems;

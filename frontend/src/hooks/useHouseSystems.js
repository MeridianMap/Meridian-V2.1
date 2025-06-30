import { useState, useEffect } from 'react';
import { getHouseSystems } from '../apiClient';

const useHouseSystems = () => {
  const [houseSystems, setHouseSystems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHouseSystems = async () => {
      try {
        setLoading(true);
        const data = await getHouseSystems();
        setHouseSystems(data.house_systems || []);
        setError(null);
      } catch (err) {
        console.error('Error fetching house systems:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHouseSystems();
  }, []);

  return { houseSystems, loading, error };
};

export default useHouseSystems;

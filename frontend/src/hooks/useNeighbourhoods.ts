import { useState, useEffect, useRef } from 'react';
import type { FeatureCollection } from 'geojson';
import { fetchNeighbourhoods } from '../lib/api';

export function useNeighbourhoods() {
  const [geojson, setGeojson] = useState<FeatureCollection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetched = useRef(false);

  useEffect(() => {
    if (fetched.current) return;
    fetched.current = true;
    fetchNeighbourhoods()
      .then(setGeojson)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { geojson, loading, error };
}

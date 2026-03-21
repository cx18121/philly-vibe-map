import { useEffect, useRef } from 'react';
import { fetchTemporal } from '../lib/api';
import { useMapStore } from '../store/mapStore';

export function useTemporal() {
  const temporalData = useMapStore((s) => s.temporalData);
  const setTemporalData = useMapStore((s) => s.setTemporalData);
  const fetched = useRef(false);

  useEffect(() => {
    if (fetched.current || temporalData) return;
    fetched.current = true;
    fetchTemporal()
      .then(setTemporalData)
      .catch((e) => console.error('Failed to load temporal data:', e));
  }, [temporalData, setTemporalData]);

  return temporalData;
}

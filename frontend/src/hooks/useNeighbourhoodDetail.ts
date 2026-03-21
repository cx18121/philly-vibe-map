import { useEffect } from 'react';
import { useMapStore } from '../store/mapStore';
import { fetchDetail } from '../lib/api';

export function useNeighbourhoodDetail() {
  const selectedId = useMapStore((s) => s.selectedId);
  const setDetail = useMapStore((s) => s.setDetail);
  const setLoading = useMapStore((s) => s.setLoading);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    setLoading(true);
    fetchDetail(selectedId)
      .then(setDetail)
      .catch(() => setDetail(null));
  }, [selectedId, setDetail, setLoading]);
}

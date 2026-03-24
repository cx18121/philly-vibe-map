import { useEffect } from 'react';
import { useMapStore } from '../store/mapStore';
import { fetchDetail } from '../lib/api';

export function useNeighbourhoodDetail() {
  const selectedId = useMapStore((s) => s.selectedId);
  const setDetail = useMapStore((s) => s.setDetail);
  const setLoading = useMapStore((s) => s.setLoading);
  const setDetailError = useMapStore((s) => s.setDetailError);
  const detailFetchKey = useMapStore((s) => s.detailFetchKey);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      setDetailError(false);
      return;
    }
    let stale = false;
    setLoading(true);
    setDetailError(false);
    fetchDetail(selectedId)
      .then((d) => { if (!stale) setDetail(d); })
      .catch(() => { if (!stale) setDetailError(true); });
    return () => { stale = true; };
  }, [selectedId, setDetail, setLoading, setDetailError, detailFetchKey]);
}

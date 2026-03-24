import { useMapStore } from '../store/mapStore';

/**
 * Subscribe to store changes and write selectedId + currentYear to URL params.
 * Call once at app init (outside React render cycle).
 * Returns an unsubscribe function for cleanup (useful in tests).
 */
export function initUrlSync(): () => void {
  // Track last-written values to avoid calling replaceState on every animation frame.
  // currentYear updates at 60fps during playback — only sync when the rounded year changes.
  let lastSelected: string | null = null;
  let lastYear = -1;

  return useMapStore.subscribe((state) => {
    const year = Math.round(state.currentYear);
    if (state.selectedId === lastSelected && year === lastYear) return;
    lastSelected = state.selectedId;
    lastYear = year;

    const params = new URLSearchParams();
    if (state.selectedId) params.set('nid', state.selectedId);
    if (year) params.set('year', String(year));
    const qs = params.toString();
    window.history.replaceState(null, '', qs ? `?${qs}` : window.location.pathname);
  });
}

/**
 * Read URL search params and hydrate Zustand store.
 * Call AFTER GeoJSON and temporal data have loaded to avoid race conditions.
 */
export function hydrateFromUrl(): void {
  const params = new URLSearchParams(window.location.search);
  const nid = params.get('nid');
  const year = params.get('year');
  if (year) useMapStore.getState().setYear(Number(year));
  if (nid) useMapStore.getState().setSelected(nid);
}

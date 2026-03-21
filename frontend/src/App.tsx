import { useEffect } from 'react';
import VibeMap from './components/VibeMap';
import Legend from './components/Legend';
import TimeSlider from './components/TimeSlider';
import Sidebar from './components/Sidebar';
import BottomSheet from './components/BottomSheet';
import { useMapStore } from './store/mapStore';
import { useMediaQuery } from './hooks/useMediaQuery';
import { MOBILE_BREAKPOINT } from './lib/constants';
import { initUrlSync, hydrateFromUrl } from './lib/urlSync';

// Module-level: subscribe to store -> URL sync
initUrlSync();

export default function App() {
  const selectedId = useMapStore((s) => s.selectedId);
  const clearSelection = useMapStore((s) => s.clearSelection);
  const isMobile = useMediaQuery(MOBILE_BREAKPOINT);
  const isOpen = selectedId !== null;
  const temporalData = useMapStore((s) => s.temporalData);

  useEffect(() => {
    if (temporalData) hydrateFromUrl();
  }, [temporalData]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh' }}>
      <VibeMap />
      <Legend />
      <TimeSlider />
      {isMobile
        ? <BottomSheet isOpen={isOpen} onClose={clearSelection} />
        : <Sidebar isOpen={isOpen} onClose={clearSelection} />
      }
    </div>
  );
}

import VibeMap from './components/VibeMap';
import Legend from './components/Legend';
import Sidebar from './components/Sidebar';
import BottomSheet from './components/BottomSheet';
import { useMapStore } from './store/mapStore';
import { useMediaQuery } from './hooks/useMediaQuery';
import { MOBILE_BREAKPOINT } from './lib/constants';

export default function App() {
  const selectedId = useMapStore((s) => s.selectedId);
  const clearSelection = useMapStore((s) => s.clearSelection);
  const isMobile = useMediaQuery(MOBILE_BREAKPOINT);
  const isOpen = selectedId !== null;

  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh' }}>
      <VibeMap />
      <Legend />
      {isMobile
        ? <BottomSheet isOpen={isOpen} onClose={clearSelection} />
        : <Sidebar isOpen={isOpen} onClose={clearSelection} />
      }
    </div>
  );
}

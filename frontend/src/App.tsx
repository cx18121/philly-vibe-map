import { useEffect } from 'react';
import { motion } from 'framer-motion';
import VibeMap from './components/VibeMap';
import Legend from './components/Legend';
import TimeSlider from './components/TimeSlider';
import Sidebar from './components/Sidebar';
import BottomSheet from './components/BottomSheet';
import FirstTimeHint from './components/FirstTimeHint';
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

      {/* Editorial title — top left, non-interactive */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.35 }}
        style={{
          position: 'absolute',
          top: 16,
          left: 16,
          zIndex: 10,
          pointerEvents: 'none',
          userSelect: 'none',
        }}
      >
        <div
          style={{
            fontFamily: "'Fraunces', serif",
            fontSize: '1.2rem',
            fontWeight: 700,
            color: 'rgba(240,240,240,0.92)',
            letterSpacing: '-0.025em',
            lineHeight: 1.2,
          }}
        >
          Vibe Mapper
        </div>
        {/* Editorial accent line — warm gold, always visible */}
        <div
          style={{
            height: 1,
            width: 52,
            background: 'linear-gradient(to right, #DDCC77, transparent)',
            marginTop: 6,
            marginBottom: 3,
          }}
        />
        <div
          style={{
            fontSize: '0.6rem',
            color: 'rgba(240,240,240,0.32)',
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            fontFamily: "'Outfit', sans-serif",
          }}
        >
          Philadelphia
        </div>
      </motion.div>

      <Legend />
      <FirstTimeHint />
      <TimeSlider />

      {isMobile
        ? <BottomSheet isOpen={isOpen} onClose={clearSelection} />
        : <Sidebar isOpen={isOpen} onClose={clearSelection} />
      }
    </div>
  );
}

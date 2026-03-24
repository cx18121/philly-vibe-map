import { useCallback, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMapStore } from '../store/mapStore';
import { useAnimationFrame } from '../hooks/useAnimationFrame';
import { MOBILE_BREAKPOINT } from '../lib/constants';
import { useMediaQuery } from '../hooks/useMediaQuery';
import { VIBE_COLORS } from '../lib/colors';
import type { VibeArchetype } from '../lib/types';

const YEAR_ADVANCE_INTERVAL = 1500;

function PlayIcon() {
  return (
    <svg width="11" height="13" viewBox="0 0 11 13" fill="currentColor" aria-hidden="true">
      <path d="M1 1.2L10 6.5L1 11.8V1.2Z" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg width="11" height="13" viewBox="0 0 11 13" fill="currentColor" aria-hidden="true">
      <rect x="0.5" y="0.5" width="3.5" height="12" rx="1.5" />
      <rect x="7" y="0.5" width="3.5" height="12" rx="1.5" />
    </svg>
  );
}

export default function TimeSlider() {
  const currentYear = useMapStore((s) => s.currentYear);
  const isPlaying = useMapStore((s) => s.isPlaying);
  const availableYears = useMapStore((s) => s.availableYears);
  const setYear = useMapStore((s) => s.setYear);
  const togglePlay = useMapStore((s) => s.togglePlay);
  const detail = useMapStore((s) => s.detail);
  const isMobile = useMediaQuery(MOBILE_BREAKPOINT);
  const [btnHovered, setBtnHovered] = useState(false);
  const [hasPlayed, setHasPlayed] = useState(() => !!localStorage.getItem('vibe-played-v1'));

  const accentColor = detail
    ? (VIBE_COLORS[detail.dominant_vibe as VibeArchetype] ?? null)
    : null;

  const reducedMotion = useRef(
    typeof window !== 'undefined' && typeof window.matchMedia === 'function'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false,
  );
  const elapsedRef = useRef(0);

  const minYear = availableYears.length > 0 ? availableYears[0] : 0;
  const maxYear = availableYears.length > 0 ? availableYears[availableYears.length - 1] : 0;

  const advance = useCallback(
    (dt: number) => {
      if (reducedMotion.current) {
        elapsedRef.current += dt;
        if (elapsedRef.current >= YEAR_ADVANCE_INTERVAL) {
          elapsedRef.current = 0;
          const next = Math.round(currentYear) + 1;
          setYear(next > maxYear ? minYear : next);
        }
      } else {
        const increment = dt / YEAR_ADVANCE_INTERVAL;
        const next = currentYear + increment;
        setYear(next >= maxYear ? minYear : next);
      }
    },
    [currentYear, maxYear, minYear, setYear],
  );

  useAnimationFrame(advance, isPlaying && availableYears.length > 1);

  if (availableYears.length === 0) return null;

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (isPlaying) togglePlay();
    setYear(Number(e.target.value));
  };

  const handleTogglePlay = () => {
    if (!hasPlayed) {
      setHasPlayed(true);
      localStorage.setItem('vibe-played-v1', '1');
    }
    togglePlay();
  };

  return (
    <motion.div
      role="group"
      aria-label="Time controls"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1], delay: 0.45 }}
      style={{
        position: 'fixed',
        bottom: isMobile ? 72 : 24,
        left: '50%',
        transform: 'translateX(-50%)',
        width: isMobile ? 'calc(100vw - 24px)' : 'min(520px, calc(100vw - 40px))',
        background: 'rgba(12, 12, 24, 0.88)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: 20,
        padding: isMobile ? '14px 16px' : '14px 20px',
        zIndex: 15,
        display: 'flex',
        alignItems: 'center',
        gap: 14,
      }}
    >
      {/* Play / Pause — wrapped in motion.div for first-time pulse ring */}
      <motion.div
        style={{ flexShrink: 0, borderRadius: '50%', display: 'inline-flex' }}
        animate={
          !hasPlayed
            ? { boxShadow: ['0 0 0 0px rgba(255,255,255,0.18)', '0 0 0 8px rgba(255,255,255,0)'] }
            : { boxShadow: '0 0 0 0px rgba(255,255,255,0)' }
        }
        transition={!hasPlayed ? { repeat: Infinity, duration: 2.2, ease: 'easeOut' } : { duration: 0.4 }}
      >
      <motion.button
        onClick={handleTogglePlay}
        onMouseEnter={() => setBtnHovered(true)}
        onMouseLeave={() => setBtnHovered(false)}
        whileTap={{ scale: 0.88 }}
        transition={{ type: 'spring', stiffness: 400, damping: 20 }}
        aria-label={isPlaying ? 'Pause timeline' : 'Play timeline'}
        style={{
          width: 44,
          height: 44,
          background: btnHovered ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.06)',
          border: accentColor && isPlaying
            ? `1px solid ${accentColor}55`
            : '1px solid rgba(255,255,255,0.1)',
          borderRadius: '50%',
          color: '#f0f0f0',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'background 0.15s ease, border-color 0.3s ease, box-shadow 0.3s ease',
          boxShadow: accentColor && isPlaying ? `0 0 10px ${accentColor}30` : 'none',
          paddingLeft: isPlaying ? 0 : 2,
        }}
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={isPlaying ? 'pause' : 'play'}
            initial={{ opacity: 0, scale: 0.75 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.75 }}
            transition={{ duration: 0.12, ease: [0.16, 1, 0.3, 1] }}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            {isPlaying ? <PauseIcon /> : <PlayIcon />}
          </motion.span>
        </AnimatePresence>
      </motion.button>
      </motion.div>

      {/* Track + year labels */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 7 }}>
        <input
          type="range"
          min={minYear}
          max={maxYear}
          step={1}
          value={Math.round(currentYear)}
          onChange={handleSliderChange}
          aria-label="Year"
          aria-valuetext={String(Math.round(currentYear))}
          style={accentColor ? { '--thumb-glow': `${accentColor}30` } as React.CSSProperties : undefined}
        />
      </div>

      {/* Year — the hero element */}
      <div
        aria-live="polite"
        aria-atomic="true"
        style={{
          fontFamily: "'Outfit', sans-serif",
          fontSize: isMobile ? '1.8rem' : '2.25rem',
          fontWeight: 600,
          color: '#f0f0f0',
          letterSpacing: '-0.04em',
          flexShrink: 0,
          lineHeight: 1,
          minWidth: isMobile ? 62 : 78,
          textAlign: 'right',
          textShadow: accentColor ? `0 0 16px ${accentColor}38` : 'none',
          transition: 'text-shadow 0.5s ease',
        }}
      >
        {Math.round(currentYear)}
      </div>
    </motion.div>
  );
}

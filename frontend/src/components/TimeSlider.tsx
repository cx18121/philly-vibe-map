import { useCallback, useRef } from 'react';
import { useMapStore } from '../store/mapStore';
import { useAnimationFrame } from '../hooks/useAnimationFrame';
import { MOBILE_BREAKPOINT } from '../lib/constants';
import { useMediaQuery } from '../hooks/useMediaQuery';

const YEAR_ADVANCE_INTERVAL = 1500;

export default function TimeSlider() {
  const currentYear = useMapStore((s) => s.currentYear);
  const isPlaying = useMapStore((s) => s.isPlaying);
  const availableYears = useMapStore((s) => s.availableYears);
  const setYear = useMapStore((s) => s.setYear);
  const togglePlay = useMapStore((s) => s.togglePlay);
  const isMobile = useMediaQuery(MOBILE_BREAKPOINT);

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
        // Reduced motion: snap by whole years every YEAR_ADVANCE_INTERVAL ms
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

  return (
    <div
      role="group"
      aria-label="Time controls"
      style={{
        position: 'fixed',
        bottom: isMobile ? 80 : 32,
        left: '50%',
        transform: 'translateX(-50%)',
        width: isMobile ? 'calc(100vw - 24px)' : 'min(480px, calc(100vw - 32px))',
        background: 'rgba(26, 26, 46, 0.9)',
        backdropFilter: 'blur(8px)',
        borderRadius: 12,
        padding: '16px 16px 12px',
        zIndex: 15,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
      }}
    >
      {/* Play/Pause button */}
      <button
        onClick={togglePlay}
        aria-label={isPlaying ? 'Pause timeline' : 'Play timeline'}
        style={{
          width: 44,
          height: 44,
          background: 'transparent',
          border: 'none',
          color: '#e0e0e0',
          fontSize: 20,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {isPlaying ? '\u23F8' : '\u25B6'}
      </button>

      {/* Range input */}
      <input
        type="range"
        min={minYear}
        max={maxYear}
        step={1}
        value={Math.round(currentYear)}
        onChange={handleSliderChange}
        aria-label="Year"
        aria-valuetext={String(Math.round(currentYear))}
        style={{
          flex: 1,
          marginLeft: 8,
          marginRight: 12,
        }}
      />

      {/* Current year label */}
      <span
        style={{
          fontSize: 28,
          fontWeight: 600,
          color: '#e0e0e0',
          width: 56,
          textAlign: 'right',
          flexShrink: 0,
        }}
      >
        {Math.round(currentYear)}
      </span>

      {/* Endpoint year labels */}
      {!isMobile && (
        <div
          style={{
            width: '100%',
            display: 'flex',
            justifyContent: 'space-between',
            paddingLeft: 52,
            paddingRight: 68,
          }}
        >
          <span style={{ fontSize: 12, color: '#999999' }}>{minYear}</span>
          <span style={{ fontSize: 12, color: '#999999' }}>{maxYear}</span>
        </div>
      )}
    </div>
  );
}

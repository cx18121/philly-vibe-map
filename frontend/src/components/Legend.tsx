import { useState } from 'react';
import { motion } from 'framer-motion';
import { VIBE_COLORS } from '../lib/colors';
import { ARCHETYPE_ORDER } from '../lib/constants';
import { useMediaQuery } from '../hooks/useMediaQuery';
import { MOBILE_BREAKPOINT } from '../lib/constants';

export default function Legend() {
  const isMobile = useMediaQuery(MOBILE_BREAKPOINT);
  const [hoveredArch, setHoveredArch] = useState<string | null>(null);

  // Hide on mobile — bottom sheet takes over; legend would overlap the time slider
  if (isMobile) return null;

  return (
    <motion.div
      data-testid="legend"
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1], delay: 0.5 }}
      style={{
        position: 'absolute',
        bottom: 130,
        left: 16,
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        gap: 7,
      }}
    >
      <p
        style={{
          fontSize: '0.6rem',
          letterSpacing: '0.18em',
          textTransform: 'uppercase',
          color: 'rgba(240,240,240,0.28)',
          fontFamily: "'Outfit', sans-serif",
          fontWeight: 600,
          marginBottom: 2,
        }}
      >
        Dominant Vibe
      </p>
      {ARCHETYPE_ORDER.map((arch) => (
        <div
          key={arch}
          style={{ display: 'flex', alignItems: 'center', gap: 9, cursor: 'default' }}
          onMouseEnter={() => setHoveredArch(arch)}
          onMouseLeave={() => setHoveredArch(null)}
        >
          <motion.span
            animate={{ scale: hoveredArch === arch ? 1.35 : 1 }}
            transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
            style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: VIBE_COLORS[arch as keyof typeof VIBE_COLORS],
              display: 'inline-block',
              flexShrink: 0,
            }}
          />
          <span
            style={{
              fontSize: '0.72rem',
              textTransform: 'capitalize',
              color: hoveredArch === arch ? 'rgba(240,240,240,0.88)' : 'rgba(240,240,240,0.55)',
              fontFamily: "'Outfit', sans-serif",
              fontWeight: hoveredArch === arch ? 500 : 400,
              transition: 'color 0.18s ease, font-weight 0.18s ease',
            }}
          >
            {arch}
          </span>
        </div>
      ))}
    </motion.div>
  );
}

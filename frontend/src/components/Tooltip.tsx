import { motion } from 'framer-motion';
import { VIBE_COLORS } from '../lib/colors';
import type { VibeArchetype } from '../lib/types';

interface TooltipProps {
  x: number;
  y: number;
  flipX?: boolean;
  name: string;
  vibe: string;
}

export default function Tooltip({ x, y, flipX, name, vibe }: TooltipProps) {
  const color = VIBE_COLORS[vibe as VibeArchetype] ?? '#888888';

  return (
    <motion.div
      data-testid="tooltip"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 6 }}
      transition={{ duration: 0.13, ease: [0.16, 1, 0.3, 1] }}
      style={{
        position: 'absolute',
        left: flipX ? x - 14 : x + 14,
        top: Math.max(10, y - 10),
        transform: flipX ? 'translateX(-100%)' : undefined,
        pointerEvents: 'none',
        background: '#0c0c18',
        borderTop: '1px solid rgba(255,255,255,0.07)',
        borderRight: '1px solid rgba(255,255,255,0.07)',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        borderLeft: `3px solid ${color}`,
        padding: '8px 14px 8px 12px',
        borderRadius: '0 8px 8px 0',
        zIndex: 20,
        whiteSpace: 'nowrap',
        boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      }}
    >
      <div
        style={{
          fontFamily: "'Fraunces', serif",
          fontSize: '1rem',
          fontWeight: 700,
          color: '#f0f0f0',
          letterSpacing: '-0.01em',
          marginBottom: 3,
          lineHeight: 1.2,
        }}
      >
        {name}
      </div>
      <div
        style={{
          fontSize: '0.62rem',
          color: color,
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          fontFamily: "'Outfit', sans-serif",
          fontWeight: 500,
        }}
      >
        {vibe}
      </div>
    </motion.div>
  );
}

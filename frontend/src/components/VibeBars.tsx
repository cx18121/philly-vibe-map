import { useState } from 'react';
import { motion } from 'framer-motion';
import { ARCHETYPE_ORDER } from '../lib/constants';
import { VIBE_COLORS } from '../lib/colors';
import type { VibeArchetype } from '../lib/types';

interface Props {
  vibeScores: Record<string, number>;
}

export default function VibeBars({ vibeScores }: Props) {
  const maxScore = Math.max(...Object.values(vibeScores), 0.01);
  const dominantArch = ARCHETYPE_ORDER.find((a) => (vibeScores[a] ?? 0) === maxScore);
  const [hoveredArch, setHoveredArch] = useState<string | null>(null);

  return (
    <div data-testid="vibe-bars" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {ARCHETYPE_ORDER.map((arch) => {
        const score = vibeScores[arch] ?? 0;
        const pct = (score / maxScore) * 100;
        const color = VIBE_COLORS[arch as VibeArchetype];
        const isHovered = hoveredArch === arch;
        const isDominant = arch === dominantArch;

        return (
          <div
            key={arch}
            style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'default' }}
            onMouseEnter={() => setHoveredArch(arch)}
            onMouseLeave={() => setHoveredArch(null)}
          >
            <span
              style={{
                width: 62,
                fontSize: '0.72rem',
                textTransform: 'capitalize',
                color: isDominant
                  ? 'rgba(240,240,240,0.92)'
                  : isHovered
                  ? 'rgba(240,240,240,0.88)'
                  : 'rgba(240,240,240,0.55)',
                fontFamily: "'Outfit', sans-serif",
                fontWeight: isDominant ? 600 : 400,
                letterSpacing: '0.02em',
                flexShrink: 0,
                transition: 'color 0.18s ease',
              }}
            >
              {arch}
            </span>

            <div
              style={{
                flex: 1,
                background: isHovered ? 'rgba(255,255,255,0.09)' : 'rgba(255,255,255,0.06)',
                borderRadius: 2,
                height: 4,
                overflow: 'hidden',
                transition: 'background 0.18s ease',
              }}
            >
              <motion.div
                style={{
                  height: '100%',
                  borderRadius: 2,
                  background: color,
                  filter: isHovered ? 'brightness(1.25)' : 'brightness(1)',
                  transition: 'filter 0.18s ease',
                }}
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={
                  arch === dominantArch
                    ? { type: 'spring', stiffness: 190, damping: 18, delay: 0.2 }
                    : { duration: 0.65, ease: [0.16, 1, 0.3, 1] }
                }
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

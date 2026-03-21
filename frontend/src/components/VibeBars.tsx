import { motion } from 'framer-motion';
import { ARCHETYPE_ORDER } from '../lib/constants';
import { VIBE_COLORS } from '../lib/colors';
import type { VibeArchetype } from '../lib/types';

interface Props {
  vibeScores: Record<string, number>;
}

export default function VibeBars({ vibeScores }: Props) {
  const maxScore = Math.max(...Object.values(vibeScores), 0.01);
  return (
    <div data-testid="vibe-bars">
      {ARCHETYPE_ORDER.map((arch) => {
        const score = vibeScores[arch] ?? 0;
        const pct = (score / maxScore) * 100;
        return (
          <div key={arch} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span style={{ width: 70, fontSize: '0.8rem', textTransform: 'capitalize' }}>{arch}</span>
            <div style={{ flex: 1, background: '#2a2a4a', borderRadius: 4, height: 16, overflow: 'hidden' }}>
              <motion.div
                style={{
                  height: '100%',
                  borderRadius: 4,
                  background: VIBE_COLORS[arch as VibeArchetype],
                }}
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>
            <span style={{ width: 40, fontSize: '0.75rem', textAlign: 'right' }}>{score.toFixed(2)}</span>
          </div>
        );
      })}
    </div>
  );
}

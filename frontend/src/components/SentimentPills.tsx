import { motion } from 'framer-motion';
import { VIBE_COLORS } from '../lib/colors';
import type { VibeArchetype } from '../lib/types';

interface Props {
  vibeScores: Record<string, number>;
  dominantVibe: string;
}

const container = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.07 } },
};

const item = {
  hidden: { opacity: 0, y: 5 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.32, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] },
  },
};

export default function SentimentPills({ vibeScores, dominantVibe }: Props) {
  const sorted = Object.entries(vibeScores)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3);

  return (
    <motion.div
      data-testid="sentiment-pills"
      variants={container}
      initial="hidden"
      animate="visible"
      style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}
    >
      {sorted.map(([vibe]) => {
        const color = VIBE_COLORS[vibe as VibeArchetype];
        const isDominant = vibe === dominantVibe;

        return (
          <motion.div
            key={vibe}
            variants={item}
            style={{ display: 'flex', alignItems: 'center', gap: 5 }}
          >
            <span
              style={{
                width: isDominant ? 7 : 6,
                height: isDominant ? 7 : 6,
                borderRadius: '50%',
                background: color,
                display: 'inline-block',
                flexShrink: 0,
              }}
            />
            <span
              style={{
                fontSize: isDominant ? '0.9rem' : '0.72rem',
                color: isDominant ? color : 'rgba(240,240,240,0.38)',
                textTransform: 'capitalize',
                fontFamily: "'Outfit', sans-serif",
                fontWeight: isDominant ? 600 : 400,
                letterSpacing: isDominant ? '0.01em' : '0.02em',
              }}
            >
              {vibe}
            </span>
          </motion.div>
        );
      })}

    </motion.div>
  );
}

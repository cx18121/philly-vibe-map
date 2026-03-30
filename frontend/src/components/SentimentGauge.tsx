import { motion } from 'framer-motion';
import type { SentimentSummary } from '../lib/types';

interface Props {
  sentiment: SentimentSummary;
}

const BAR_HEIGHT = 4;
const BAR_RADIUS = 2;

const COLORS = {
  positive: '#44AA99',
  neutral: 'rgba(240,240,240,0.25)',
  negative: '#CC6677',
};

function getLabel(score: number): string {
  if (score >= 0.4) return 'Very Positive';
  if (score >= 0.15) return 'Positive';
  if (score > -0.15) return 'Mixed';
  if (score > -0.4) return 'Negative';
  return 'Very Negative';
}

function getLabelColor(score: number): string {
  if (score >= 0.15) return COLORS.positive;
  if (score > -0.15) return COLORS.neutral;
  return COLORS.negative;
}

export default function SentimentGauge({ sentiment }: Props) {
  const { positive, neutral, negative, mean_score } = sentiment;
  const label = getLabel(mean_score);
  const labelColor = getLabelColor(mean_score);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {/* Label + score */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span
          style={{
            fontSize: '0.82rem',
            fontFamily: "'Outfit', sans-serif",
            fontWeight: 600,
            color: labelColor,
            letterSpacing: '0.01em',
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontSize: '0.65rem',
            fontFamily: "'Outfit', sans-serif",
            color: 'rgba(240,240,240,0.3)',
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {mean_score > 0 ? '+' : ''}{mean_score.toFixed(2)}
        </span>
      </div>

      {/* Stacked proportion bar */}
      <div
        style={{
          display: 'flex',
          width: '100%',
          height: BAR_HEIGHT,
          borderRadius: BAR_RADIUS,
          overflow: 'hidden',
          gap: 1,
        }}
      >
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
          style={{
            width: `${positive * 100}%`,
            height: '100%',
            background: COLORS.positive,
            transformOrigin: 'left',
          }}
        />
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
          style={{
            width: `${neutral * 100}%`,
            height: '100%',
            background: COLORS.neutral,
            transformOrigin: 'left',
          }}
        />
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
          style={{
            width: `${negative * 100}%`,
            height: '100%',
            background: COLORS.negative,
            transformOrigin: 'left',
          }}
        />
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 14 }}>
        {([
          ['positive', positive, COLORS.positive],
          ['neutral', neutral, COLORS.neutral],
          ['negative', negative, COLORS.negative],
        ] as const).map(([name, pct, color]) => (
          <div
            key={name}
            style={{ display: 'flex', alignItems: 'center', gap: 4 }}
          >
            <span
              style={{
                width: 5,
                height: 5,
                borderRadius: '50%',
                background: color,
                display: 'inline-block',
                flexShrink: 0,
              }}
            />
            <span
              style={{
                fontSize: '0.6rem',
                fontFamily: "'Outfit', sans-serif",
                color: 'rgba(240,240,240,0.35)',
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {(pct * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

import { VIBE_COLORS } from '../lib/colors';
import type { VibeArchetype } from '../lib/types';

interface Props {
  vibeScores: Record<string, number>;
  dominantVibe: string;
}

export default function SentimentPills({ vibeScores, dominantVibe }: Props) {
  const sorted = Object.entries(vibeScores)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3);

  return (
    <div data-testid="sentiment-pills" style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      {sorted.map(([vibe, score]) => {
        const color = VIBE_COLORS[vibe as VibeArchetype];
        return (
          <span
            key={vibe}
            style={{
              padding: '4px 12px',
              borderRadius: 16,
              fontSize: '0.8rem',
              fontWeight: vibe === dominantVibe ? 700 : 400,
              background: color + '33',
              color: color,
              border: `1px solid ${color}55`,
            }}
          >
            {vibe}: {score.toFixed(2)}
          </span>
        );
      })}
    </div>
  );
}

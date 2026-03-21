import { VIBE_COLORS } from '../lib/colors';
import type { VibeArchetype } from '../lib/types';

interface TooltipProps {
  x: number;
  y: number;
  name: string;
  vibe: string;
}

export default function Tooltip({ x, y, name, vibe }: TooltipProps) {
  const color = VIBE_COLORS[vibe as VibeArchetype] ?? '#888888';

  return (
    <div
      data-testid="tooltip"
      style={{
        position: 'absolute',
        left: x + 10,
        top: y + 10,
        pointerEvents: 'none',
        background: '#1a1a2eee',
        padding: 8,
        borderRadius: 4,
        color: '#ffffff',
        zIndex: 20,
        whiteSpace: 'nowrap',
      }}
    >
      <div style={{ fontWeight: 700 }}>{name}</div>
      <div style={{ color, textTransform: 'capitalize' }}>{vibe}</div>
    </div>
  );
}

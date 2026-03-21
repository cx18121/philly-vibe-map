import { VIBE_COLORS } from '../lib/colors';
import { ARCHETYPE_ORDER } from '../lib/constants';

export default function Legend() {
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 24,
        left: 12,
        background: 'rgba(26, 26, 46, 0.9)',
        padding: '12px 16px',
        borderRadius: 8,
        zIndex: 10,
        fontSize: '0.85rem',
      }}
      data-testid="legend"
    >
      <div style={{ fontWeight: 600, marginBottom: 8 }}>Neighbourhood Vibes</div>
      {ARCHETYPE_ORDER.map((arch) => (
        <div key={arch} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: 3,
              background: VIBE_COLORS[arch as keyof typeof VIBE_COLORS],
              display: 'inline-block',
              flexShrink: 0,
            }}
          />
          <span style={{ textTransform: 'capitalize' }}>{arch}</span>
        </div>
      ))}
    </div>
  );
}

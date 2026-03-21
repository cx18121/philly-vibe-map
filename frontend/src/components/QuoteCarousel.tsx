interface Props {
  quotes: Record<string, string[]>;
  dominantVibe: string;
}

export default function QuoteCarousel({ quotes, dominantVibe }: Props) {
  const vibeQuotes = quotes[dominantVibe] ?? Object.values(quotes).flat();
  const display = vibeQuotes.slice(0, 3);

  return (
    <div data-testid="quote-carousel">
      {display.map((q, i) => (
        <blockquote
          key={i}
          style={{
            borderLeft: '3px solid #444',
            paddingLeft: 12,
            margin: '8px 0',
            fontSize: '0.85rem',
            fontStyle: 'italic',
            color: '#bbb',
          }}
        >
          &ldquo;{q}&rdquo;
        </blockquote>
      ))}
      {display.length === 0 && (
        <p style={{ color: '#666', fontSize: '0.85rem' }}>No quotes available</p>
      )}
    </div>
  );
}

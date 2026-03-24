import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { VIBE_COLORS } from '../lib/colors';
import type { VibeArchetype } from '../lib/types';

interface Props {
  quotes: Record<string, string[]>;
  dominantVibe: string;
}

const PAGE_SIZE = 2;

export default function QuoteCarousel({ quotes, dominantVibe }: Props) {
  const vibeQuotes = quotes[dominantVibe] ?? Object.values(quotes).flat();
  const accentColor = VIBE_COLORS[dominantVibe as VibeArchetype] ?? '#888888';
  const totalPages = Math.max(1, Math.ceil(vibeQuotes.length / PAGE_SIZE));

  const [page, setPage] = useState(0);
  const [direction, setDirection] = useState(1);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [prevHovered, setPrevHovered] = useState(false);
  const [nextHovered, setNextHovered] = useState(false);
  const [hoveredDot, setHoveredDot] = useState<number | null>(null);

  const display = vibeQuotes.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);

  const goTo = (next: number) => {
    setDirection(next > page ? 1 : -1);
    setPage(next);
  };

  const goNext = () => goTo((page + 1) % totalPages);
  const goPrev = () => goTo((page - 1 + totalPages) % totalPages);

  return (
    <div data-testid="quote-carousel">
      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={page}
          custom={direction}
          initial={(dir: number) => ({ opacity: 0, x: dir * 18 })}
          animate={{ opacity: 1, x: 0 }}
          exit={(dir: number) => ({ opacity: 0, x: dir * -12 })}
          transition={{ duration: 0.38, ease: [0.16, 1, 0.3, 1] }}
          style={{ display: 'flex', flexDirection: 'column', gap: 20 }}
        >
          {display.map((q, i) => (
            <motion.blockquote
              key={i}
              onHoverStart={() => setHoveredIdx(i)}
              onHoverEnd={() => setHoveredIdx(null)}
              whileHover={{ x: 4 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
              style={{
                borderLeft: `2px solid ${hoveredIdx === i ? `${accentColor}75` : `${accentColor}45`}`,
                paddingLeft: 14,
                margin: 0,
                fontFamily: "'Fraunces', serif",
                fontStyle: 'italic',
                fontSize: '0.88rem',
                color: hoveredIdx === i ? 'rgba(240,240,240,0.88)' : 'rgba(240,240,240,0.75)',
                lineHeight: 1.7,
                cursor: 'default',
                transition: 'color 0.2s ease, border-left-color 0.2s ease',
                display: '-webkit-box',
                WebkitLineClamp: 6,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              &ldquo;{q}&rdquo;
            </motion.blockquote>
          ))}

          {display.length === 0 && (
            <p
              style={{
                fontSize: '0.8rem',
                color: 'rgba(240,240,240,0.25)',
                fontFamily: "'Outfit', sans-serif",
              }}
            >
              No quotes found for this neighbourhood.
            </p>
          )}
        </motion.div>
      </AnimatePresence>

      {totalPages > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', marginTop: 12 }}>
          {/* Prev — 44×44 minimum touch target via padding */}
          <button
            onClick={goPrev}
            onMouseEnter={() => setPrevHovered(true)}
            onMouseLeave={() => setPrevHovered(false)}
            aria-label="Previous quotes"
            style={{
              background: 'none',
              border: 'none',
              padding: '16px 12px',
              cursor: 'pointer',
              color: prevHovered ? 'rgba(240,240,240,0.65)' : 'rgba(240,240,240,0.28)',
              display: 'flex',
              alignItems: 'center',
              lineHeight: 1,
              transition: 'color 0.15s ease',
            }}
          >
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
              <path d="M8 2L3.5 6.5L8 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          {/* Dots — visual element separated from touch target */}
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {Array.from({ length: totalPages }).map((_, i) => (
              <button
                key={i}
                onClick={() => goTo(i)}
                onMouseEnter={() => setHoveredDot(i)}
                onMouseLeave={() => setHoveredDot(null)}
                aria-label={`Go to quotes page ${i + 1}`}
                style={{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '20px 6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <span
                  style={{
                    display: 'block',
                    width: i === page ? 16 : 4,
                    height: 4,
                    borderRadius: 2,
                    background: i === page
                      ? accentColor
                      : hoveredDot === i
                      ? 'rgba(255,255,255,0.32)'
                      : 'rgba(255,255,255,0.14)',
                    transition: 'width 0.28s ease, background 0.2s ease',
                  }}
                />
              </button>
            ))}
          </div>

          {/* Next — 44×44 minimum touch target via padding */}
          <button
            onClick={goNext}
            onMouseEnter={() => setNextHovered(true)}
            onMouseLeave={() => setNextHovered(false)}
            aria-label="Next quotes"
            style={{
              background: 'none',
              border: 'none',
              padding: '16px 12px',
              cursor: 'pointer',
              color: nextHovered ? 'rgba(240,240,240,0.65)' : 'rgba(240,240,240,0.28)',
              display: 'flex',
              alignItems: 'center',
              lineHeight: 1,
              transition: 'color 0.15s ease',
            }}
          >
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
              <path d="M5 2L9.5 6.5L5 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}

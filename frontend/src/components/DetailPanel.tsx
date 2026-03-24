import { useEffect, useRef, useState } from 'react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useMapStore } from '../store/mapStore';
import VibeBars from './VibeBars';
import TopicList from './TopicList';
import SentimentPills from './SentimentPills';
import QuoteCarousel from './QuoteCarousel';
import { VIBE_COLORS } from '../lib/colors';
import type { VibeArchetype } from '../lib/types';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] },
  },
};

function Divider({ loose }: { loose?: boolean }) {
  return (
    <div
      style={{
        height: 1,
        background: 'rgba(255,255,255,0.06)',
        margin: loose ? '30px 0 24px' : '22px 0',
      }}
    />
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p
      style={{
        fontSize: '0.6rem',
        letterSpacing: '0.18em',
        textTransform: 'uppercase',
        color: 'rgba(240,240,240,0.28)',
        fontFamily: "'Outfit', sans-serif",
        fontWeight: 600,
        marginBottom: 14,
      }}
    >
      {children}
    </p>
  );
}

export default function DetailPanel() {
  const isLoading = useMapStore((s) => s.isLoading);
  const detail = useMapStore((s) => s.detail);
  const detailError = useMapStore((s) => s.detailError);
  const retryDetailFetch = useMapStore((s) => s.retryDetailFetch);
  const [retryHovered, setRetryHovered] = useState(false);

  const reviewCountMv = useMotionValue(0);
  const displayCount = useTransform(reviewCountMv, (v) => Math.round(v).toLocaleString());
  const reducedMotion = useRef(
    typeof window !== 'undefined' && typeof window.matchMedia === 'function'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false,
  );

  useEffect(() => {
    if (!detail) return;
    if (reducedMotion.current) {
      reviewCountMv.set(detail.review_count);
      return;
    }
    reviewCountMv.set(0);
    const controls = animate(reviewCountMv, detail.review_count, {
      duration: 1.3,
      ease: [0.16, 1, 0.3, 1],
      delay: 0.5,
    });
    return controls.stop;
  }, [detail?.neighbourhood_id]);

  if (isLoading) {
    return (
      <div data-testid="detail-panel" style={{ padding: '56px 24px 24px' }}>
        {([0.6, 0.32, 0.48, 0.42, 0.52, 0.28] as number[]).map((w, i) => (
          <div
            key={i}
            style={{
              height: i === 0 ? 28 : 10,
              width: `${w * 100}%`,
              background: 'rgba(255,255,255,0.05)',
              borderRadius: 4,
              marginBottom: i === 0 ? 14 : 10,
              animation: 'pulse 1.6s ease-in-out infinite',
              animationDelay: `${i * 0.08}s`,
            }}
          />
        ))}
      </div>
    );
  }

  if (!detail) {
    if (detailError) {
      return (
        <div data-testid="detail-panel" style={{ padding: '56px 24px 24px' }}>
          <p
            style={{
              fontSize: '0.8rem',
              color: 'rgba(240,240,240,0.35)',
              fontFamily: "'Outfit', sans-serif",
              lineHeight: 1.6,
              marginBottom: 20,
            }}
          >
            Couldn't load neighbourhood details. Check your connection and try again.
          </p>
          <button
            onClick={retryDetailFetch}
            onMouseEnter={() => setRetryHovered(true)}
            onMouseLeave={() => setRetryHovered(false)}
            style={{
              background: retryHovered ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 4,
              color: retryHovered ? 'rgba(240,240,240,0.88)' : 'rgba(240,240,240,0.7)',
              cursor: 'pointer',
              fontFamily: "'Outfit', sans-serif",
              fontSize: '0.75rem',
              letterSpacing: '0.04em',
              padding: '8px 16px',
              transition: 'background 0.15s ease, color 0.15s ease',
            }}
          >
            Try again
          </button>
        </div>
      );
    }
    return null;
  }

  const accentColor =
    VIBE_COLORS[detail.dominant_vibe as VibeArchetype] ?? '#888888';

  return (
    <motion.div
      data-testid="detail-panel"
      style={{ padding: '52px 24px 36px', overflowY: 'auto' }}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      key={detail.neighbourhood_id}
    >
      {/* Header */}
      <motion.div variants={itemVariants} style={{ marginBottom: 20 }}>
        <h2
          style={{
            fontFamily: "'Fraunces', serif",
            fontSize: '2.1rem',
            fontWeight: 700,
            color: '#f0f0f0',
            letterSpacing: '-0.03em',
            lineHeight: 1.05,
            marginBottom: 10,
            overflowWrap: 'break-word',
            wordBreak: 'break-word',
          }}
        >
          {detail.neighbourhood_name ?? 'Unknown Neighbourhood'}
        </h2>
        {/* Top 3 vibes as colored dots + labels */}
        <SentimentPills
          vibeScores={detail.vibe_scores}
          dominantVibe={detail.dominant_vibe}
        />
      </motion.div>

      {/* Thin accent line in dominant vibe color */}
      <motion.div
        variants={itemVariants}
        style={{
          height: 1,
          background: `linear-gradient(to right, ${accentColor}60, transparent)`,
          marginBottom: 22,
        }}
      />

      {/* Vibe breakdown */}
      <motion.div variants={itemVariants}>
        <SectionLabel>Vibe Breakdown</SectionLabel>
        <VibeBars vibeScores={detail.vibe_scores} />
      </motion.div>

      <Divider />

      {/* Topics */}
      <motion.div variants={itemVariants}>
        <SectionLabel>Conversation Topics</SectionLabel>
        <TopicList topics={detail.topics} accentColor={accentColor} />
      </motion.div>

      <Divider loose />

      {/* Quotes — supplementary, given more visual breathing room */}
      <motion.div variants={itemVariants}>
        <SectionLabel>Locals Say</SectionLabel>
        <QuoteCarousel
          quotes={detail.quotes}
          dominantVibe={detail.dominant_vibe}
        />
      </motion.div>

      {/* Footer metadata */}
      <motion.div variants={itemVariants}>
        <p
          style={{
            fontSize: '0.65rem',
            color: 'rgba(240,240,240,0.22)',
            marginTop: 28,
            fontFamily: "'Outfit', sans-serif",
            letterSpacing: '0.04em',
          }}
        >
          <motion.span style={{ fontVariantNumeric: 'tabular-nums' }}>{displayCount}</motion.span> reviews analysed
        </p>
      </motion.div>
    </motion.div>
  );
}

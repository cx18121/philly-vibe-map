import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { VIBE_COLORS } from '../lib/colors';
import { ARCHETYPE_ORDER } from '../lib/constants';

const LOADING_MESSAGES = [
  'Reading the city\u2019s neighbourhoods\u2026',
  'Mapping vibe signals across Philly\u2026',
  'Weighing six years of local reviews\u2026',
  'Surfacing what makes each block feel alive\u2026',
];

export default function MapSkeleton() {
  const [msgIdx, setMsgIdx] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setMsgIdx((i) => (i + 1) % LOADING_MESSAGES.length);
    }, 2600);
    return () => clearInterval(id);
  }, []);

  return (
    <div
      style={{
        width: '100%',
        height: '100vh',
        background: '#0f0f1a',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 36,
      }}
    >
      {/* Animated equalizer bars, one per vibe archetype */}
      <div style={{ display: 'flex', gap: 5, alignItems: 'flex-end', height: 44 }}>
        {ARCHETYPE_ORDER.map((arch, i) => (
          <div
            key={arch}
            style={{
              width: 5,
              borderRadius: 3,
              background: VIBE_COLORS[arch as keyof typeof VIBE_COLORS],
              animation: `vibeLoad 1.2s ease-in-out ${i * 0.1}s infinite alternate`,
            }}
          />
        ))}
      </div>

      <div style={{ textAlign: 'center' }}>
        <div
          style={{
            fontFamily: "'Fraunces', serif",
            fontSize: '1.5rem',
            fontWeight: 700,
            color: '#f0f0f0',
            letterSpacing: '-0.03em',
            lineHeight: 1.1,
            marginBottom: 10,
          }}
        >
          Vibe Mapper
        </div>
        <div style={{ height: 18, overflow: 'hidden', position: 'relative' }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={msgIdx}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.38, ease: [0.16, 1, 0.3, 1] }}
              style={{
                fontSize: '0.65rem',
                color: 'rgba(240,240,240,0.28)',
                letterSpacing: '0.18em',
                textTransform: 'uppercase',
                fontFamily: "'Outfit', sans-serif",
                fontWeight: 500,
                whiteSpace: 'nowrap',
              }}
            >
              {LOADING_MESSAGES[msgIdx]}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

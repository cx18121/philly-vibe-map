import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMapStore } from '../store/mapStore';
import { useMediaQuery } from '../hooks/useMediaQuery';
import { MOBILE_BREAKPOINT } from '../lib/constants';

const HINT_KEY = 'vibe-explore-hint-v1';

export default function FirstTimeHint() {
  const [visible, setVisible] = useState(false);
  const selectedId = useMapStore((s) => s.selectedId);
  const isMobile = useMediaQuery(MOBILE_BREAKPOINT);

  // Show hint after a short delay, but only if never dismissed
  useEffect(() => {
    if (localStorage.getItem(HINT_KEY)) return;
    const timer = setTimeout(() => setVisible(true), 1400);
    return () => clearTimeout(timer);
  }, []);

  // Dismiss on first neighbourhood click
  useEffect(() => {
    if (!selectedId) return;
    setVisible(false);
    localStorage.setItem(HINT_KEY, '1');
  }, [selectedId]);

  // Auto-dismiss after 5 seconds
  useEffect(() => {
    if (!visible) return;
    const timer = setTimeout(() => {
      setVisible(false);
      localStorage.setItem(HINT_KEY, '1');
    }, 5000);
    return () => clearTimeout(timer);
  }, [visible]);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 6, transition: { duration: 0.25 } }}
          transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
          style={{
            position: 'fixed',
            top: '44%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 11,
            pointerEvents: 'none',
            userSelect: 'none',
          }}
        >
          <div
            style={{
              background: 'rgba(12, 12, 24, 0.72)',
              backdropFilter: 'blur(16px)',
              WebkitBackdropFilter: 'blur(16px)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 24,
              padding: isMobile ? '9px 16px' : '10px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            {/* Cursor icon */}
            <svg
              width="11"
              height="13"
              viewBox="0 0 11 13"
              fill="none"
              aria-hidden="true"
              style={{ flexShrink: 0, opacity: 0.5 }}
            >
              <path
                d="M1 1L1 10L3.5 7.5L5.5 12L6.8 11.4L4.8 6.9L8 6.9Z"
                fill="rgba(240,240,240,0.9)"
                stroke="rgba(240,240,240,0.3)"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
            </svg>
            <span
              style={{
                fontSize: '0.8rem',
                color: 'rgba(240,240,240,0.55)',
                fontFamily: "'Outfit', sans-serif",
                letterSpacing: '0.03em',
                whiteSpace: 'nowrap',
              }}
            >
              {isMobile
                ? 'Tap any neighbourhood to explore'
                : 'Click any neighbourhood to explore'}
            </span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

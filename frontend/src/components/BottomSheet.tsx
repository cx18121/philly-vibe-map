import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import DetailPanel from './DetailPanel';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

function CloseIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      aria-hidden="true"
    >
      <path d="M1 1L11 11M11 1L1 11" />
    </svg>
  );
}

export default function BottomSheet({ isOpen, onClose }: Props) {
  const [closeHovered, setCloseHovered] = useState(false);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          data-testid="bottom-sheet"
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            maxHeight: '65vh',
            background: '#0c0c18',
            borderTop: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '20px 20px 0 0',
            zIndex: 20,
            overflowY: 'auto',
          }}
          initial={{ y: '100%' }}
          animate={{ y: 0 }}
          exit={{ y: '100%' }}
          transition={{ type: 'spring', damping: 28, stiffness: 320 }}
        >
          {/* Drag handle */}
          <div
            style={{
              width: 36,
              height: 3,
              background: 'rgba(255,255,255,0.14)',
              borderRadius: 2,
              margin: '12px auto 0',
            }}
          />

          {/* Close */}
          <button
            onClick={onClose}
            onMouseEnter={() => setCloseHovered(true)}
            onMouseLeave={() => setCloseHovered(false)}
            aria-label="Close panel"
            style={{
              position: 'absolute',
              top: 8,
              right: 12,
              width: 44,
              height: 44,
              background: closeHovered
                ? 'rgba(255,255,255,0.1)'
                : 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '50%',
              color: closeHovered
                ? 'rgba(240,240,240,0.9)'
                : 'rgba(240,240,240,0.4)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'background 0.15s ease, color 0.15s ease',
            }}
          >
            <CloseIcon />
          </button>

          <DetailPanel />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

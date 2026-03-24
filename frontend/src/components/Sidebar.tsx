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

export default function Sidebar({ isOpen, onClose }: Props) {
  const [closeHovered, setCloseHovered] = useState(false);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.aside
          data-testid="sidebar"
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: 360,
            height: '100%',
            background: '#0c0c18',
            borderLeft: '1px solid rgba(255,255,255,0.06)',
            zIndex: 20,
            overflowY: 'auto',
            overflowX: 'hidden',
          }}
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 28, stiffness: 320 }}
        >
          <button
            onClick={onClose}
            onMouseEnter={() => setCloseHovered(true)}
            onMouseLeave={() => setCloseHovered(false)}
            aria-label="Close sidebar"
            style={{
              position: 'absolute',
              top: 16,
              right: 16,
              width: 32,
              height: 32,
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
              zIndex: 1,
              flexShrink: 0,
            }}
          >
            <CloseIcon />
          </button>
          <DetailPanel />
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

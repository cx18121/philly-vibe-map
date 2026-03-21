import { motion, AnimatePresence } from 'framer-motion';
import DetailPanel from './DetailPanel';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function BottomSheet({ isOpen, onClose }: Props) {
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
            maxHeight: '60vh',
            background: '#1a1a2e',
            borderTop: '1px solid #333',
            borderRadius: '16px 16px 0 0',
            zIndex: 20,
            overflowY: 'auto',
          }}
          initial={{ y: '100%' }}
          animate={{ y: 0 }}
          exit={{ y: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        >
          <div style={{ width: 40, height: 4, background: '#555', borderRadius: 2, margin: '8px auto' }} />
          <button
            onClick={onClose}
            aria-label="Close panel"
            style={{
              position: 'absolute',
              top: 12,
              right: 12,
              background: 'none',
              border: 'none',
              color: '#999',
              fontSize: '1.5rem',
              cursor: 'pointer',
            }}
          >
            &times;
          </button>
          <DetailPanel />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

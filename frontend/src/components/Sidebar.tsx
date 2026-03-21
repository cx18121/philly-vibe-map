import { motion, AnimatePresence } from 'framer-motion';
import DetailPanel from './DetailPanel';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: Props) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.aside
          data-testid="sidebar"
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: 380,
            height: '100%',
            background: '#1a1a2e',
            borderLeft: '1px solid #333',
            zIndex: 20,
            overflowY: 'auto',
          }}
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        >
          <button
            onClick={onClose}
            aria-label="Close sidebar"
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
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

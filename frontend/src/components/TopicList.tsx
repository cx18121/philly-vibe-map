import { motion } from 'framer-motion';
import type { TopicEntry } from '../lib/types';

interface Props {
  topics: TopicEntry[];
  accentColor?: string;
}

const container = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.035 } },
};

const item = {
  hidden: { opacity: 0, scale: 0.88 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] },
  },
};

export default function TopicList({ topics, accentColor }: Props) {
  // Flatten keywords from the top 3 topics into a compact cloud
  const keywords = topics
    .slice(0, 3)
    .flatMap((t) => t.keywords.slice(0, 3));

  return (
    <motion.div
      data-testid="topic-list"
      variants={container}
      initial="hidden"
      animate="visible"
      style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 6px' }}
    >
      {keywords.map((kw, i) => (
        <motion.span
          key={i}
          variants={item}
          whileHover={{ scale: 1.04 }}
          transition={{ type: 'spring', stiffness: 280, damping: 26 }}
          style={{
            fontSize: '0.72rem',
            color: accentColor ? `${accentColor}cc` : 'rgba(240,240,240,0.5)',
            background: accentColor ? `${accentColor}12` : 'rgba(255,255,255,0.04)',
            border: `1px solid ${accentColor ? `${accentColor}28` : 'rgba(255,255,255,0.07)'}`,
            borderRadius: 4,
            padding: '4px 9px',
            fontFamily: "'Outfit', sans-serif",
            letterSpacing: '0.02em',
            lineHeight: 1,
            cursor: 'default',
            display: 'inline-block',
          }}
        >
          {kw}
        </motion.span>
      ))}
      {keywords.length === 0 && (
        <span
          style={{
            fontSize: '0.8rem',
            color: 'rgba(240,240,240,0.25)',
            fontFamily: "'Outfit', sans-serif",
          }}
        >
          No topics found
        </span>
      )}
    </motion.div>
  );
}

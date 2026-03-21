import { motion } from 'framer-motion';
import { useMapStore } from '../store/mapStore';
import VibeBars from './VibeBars';
import TopicList from './TopicList';
import SentimentPills from './SentimentPills';
import QuoteCarousel from './QuoteCarousel';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
};

export default function DetailPanel() {
  const isLoading = useMapStore((s) => s.isLoading);
  const detail = useMapStore((s) => s.detail);

  if (isLoading) {
    return (
      <div data-testid="detail-panel" style={{ padding: 20, color: '#aaa' }}>
        Loading...
      </div>
    );
  }

  if (!detail) {
    return null;
  }

  return (
    <motion.div
      data-testid="detail-panel"
      style={{ padding: 20, overflowY: 'auto' }}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      key={detail.neighbourhood_id}
    >
      <motion.div variants={itemVariants}>
        <h2 style={{ margin: '0 0 16px', fontSize: '1.25rem' }}>
          {detail.neighbourhood_name ?? 'Unknown Neighbourhood'}
        </h2>
      </motion.div>

      <motion.div variants={itemVariants}>
        <h3 style={{ fontSize: '0.9rem', margin: '12px 0 8px', color: '#ccc' }}>Vibes</h3>
        <VibeBars vibeScores={detail.vibe_scores} />
      </motion.div>

      <motion.div variants={itemVariants} style={{ margin: '12px 0' }}>
        <SentimentPills vibeScores={detail.vibe_scores} dominantVibe={detail.dominant_vibe} />
      </motion.div>

      <motion.div variants={itemVariants}>
        <h3 style={{ fontSize: '0.9rem', margin: '12px 0 8px', color: '#ccc' }}>Topics</h3>
        <TopicList topics={detail.topics} />
      </motion.div>

      <motion.div variants={itemVariants}>
        <h3 style={{ fontSize: '0.9rem', margin: '12px 0 8px', color: '#ccc' }}>Quotes</h3>
        <QuoteCarousel quotes={detail.quotes} dominantVibe={detail.dominant_vibe} />
      </motion.div>

      <motion.div variants={itemVariants}>
        <p style={{ fontSize: '0.75rem', color: '#666', marginTop: 16 }}>
          {detail.review_count.toLocaleString()} reviews
        </p>
      </motion.div>
    </motion.div>
  );
}

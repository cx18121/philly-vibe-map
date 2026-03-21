import { useMapStore } from '../store/mapStore';
import VibeBars from './VibeBars';
import TopicList from './TopicList';
import SentimentPills from './SentimentPills';
import QuoteCarousel from './QuoteCarousel';

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
    <div data-testid="detail-panel" style={{ padding: 20, overflowY: 'auto' }}>
      <h2 style={{ margin: '0 0 16px', fontSize: '1.25rem' }}>
        {detail.neighbourhood_name ?? 'Unknown Neighbourhood'}
      </h2>

      <h3 style={{ fontSize: '0.9rem', margin: '12px 0 8px', color: '#ccc' }}>Vibes</h3>
      <VibeBars vibeScores={detail.vibe_scores} />

      <div style={{ margin: '12px 0' }}>
        <SentimentPills vibeScores={detail.vibe_scores} dominantVibe={detail.dominant_vibe} />
      </div>

      <h3 style={{ fontSize: '0.9rem', margin: '12px 0 8px', color: '#ccc' }}>Topics</h3>
      <TopicList topics={detail.topics} />

      <h3 style={{ fontSize: '0.9rem', margin: '12px 0 8px', color: '#ccc' }}>Quotes</h3>
      <QuoteCarousel quotes={detail.quotes} dominantVibe={detail.dominant_vibe} />

      <p style={{ fontSize: '0.75rem', color: '#666', marginTop: 16 }}>
        {detail.review_count.toLocaleString()} reviews
      </p>
    </div>
  );
}

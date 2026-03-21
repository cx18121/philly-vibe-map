import type { TopicEntry } from '../lib/types';

interface Props {
  topics: TopicEntry[];
}

export default function TopicList({ topics }: Props) {
  return (
    <div data-testid="topic-list">
      {topics.slice(0, 5).map((t, i) => (
        <div key={i} style={{ marginBottom: 8 }}>
          <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{t.label}</div>
          <div style={{ fontSize: '0.75rem', color: '#999' }}>{t.keywords.join(', ')}</div>
        </div>
      ))}
    </div>
  );
}

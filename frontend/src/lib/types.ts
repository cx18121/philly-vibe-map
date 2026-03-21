export interface TopicEntry {
  label: string;
  keywords: string[];
  review_share: number;
}

export interface NeighbourhoodDetail {
  neighbourhood_id: string;
  neighbourhood_name: string | null;
  vibe_scores: Record<string, number>;
  dominant_vibe: string;
  dominant_vibe_score: number;
  topics: TopicEntry[];
  quotes: Record<string, string[]>;
  review_count: number;
}

export interface SimilarNeighbourhood {
  neighbourhood_id: string;
  similarity: number;
}

export type VibeArchetype = 'artsy' | 'foodie' | 'nightlife' | 'family' | 'upscale' | 'cultural';

export type VibeVector = Record<string, number>;
export type TemporalData = Record<string, Record<string, VibeVector>>;

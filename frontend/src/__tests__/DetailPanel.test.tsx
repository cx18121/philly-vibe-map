import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';

// Mock framer-motion to render motion.div as plain divs with data-variants
vi.mock('framer-motion', () => ({
  motion: {
    div: React.forwardRef(({ children, variants, ...props }: Record<string, unknown>, ref: React.Ref<HTMLDivElement>) =>
      React.createElement(
        'div',
        {
          ...props,
          'data-variants': variants ? JSON.stringify(variants) : undefined,
          ref,
        },
        children as React.ReactNode,
      ),
    ),
  },
}));

const mockDetail = {
  neighbourhood_id: '001',
  neighbourhood_name: 'Center City',
  vibe_scores: { artsy: 0.1, foodie: 0.8, nightlife: 0.05, family: 0.02, upscale: 0.01, cultural: 0.02 },
  dominant_vibe: 'foodie',
  dominant_vibe_score: 0.8,
  topics: [{ label: 'Restaurants', keywords: ['food', 'dining'], review_share: 0.3 }],
  quotes: { foodie: ['Great food scene here'] },
  review_count: 500,
};

let mockStoreState: Record<string, unknown> = {};

vi.mock('../store/mapStore', () => ({
  useMapStore: (selector: (state: Record<string, unknown>) => unknown) => selector(mockStoreState),
}));

import DetailPanel from '../components/DetailPanel';

beforeEach(() => {
  vi.clearAllMocks();
  mockStoreState = {
    isLoading: false,
    detail: mockDetail,
  };
});

describe('DetailPanel stagger animations', () => {
  it('renders stagger container with containerVariants', () => {
    render(<DetailPanel />);
    const panel = screen.getByTestId('detail-panel');
    const variants = panel.getAttribute('data-variants');
    expect(variants).toBeTruthy();
    const parsed = JSON.parse(variants!);
    expect(parsed.visible.transition.staggerChildren).toBe(0.08);
  });

  it('renders item wrappers with itemVariants', () => {
    render(<DetailPanel />);
    const panel = screen.getByTestId('detail-panel');
    // Find child divs with data-variants containing y: 12
    const children = panel.querySelectorAll('[data-variants]');
    // Filter for item variants (not the container itself)
    const items = Array.from(children).filter((el) => {
      const v = el.getAttribute('data-variants');
      if (!v) return false;
      const parsed = JSON.parse(v);
      return parsed.hidden?.y === 12;
    });
    // Should have 6 item wrappers: heading, vibes, pills, topics, quotes, review count
    expect(items.length).toBe(6);
  });

  it('uses neighbourhood_id as key for re-animation', () => {
    render(<DetailPanel />);
    expect(screen.getByTestId('detail-panel')).toBeInTheDocument();
  });

  it('renders all sidebar sections', () => {
    render(<DetailPanel />);
    expect(screen.getByTestId('vibe-bars')).toBeInTheDocument();
    expect(screen.getByTestId('sentiment-pills')).toBeInTheDocument();
    expect(screen.getByTestId('topic-list')).toBeInTheDocument();
    expect(screen.getByTestId('quote-carousel')).toBeInTheDocument();
  });

  it('returns null when no detail', () => {
    mockStoreState = { isLoading: false, detail: null };
    const { container } = render(<DetailPanel />);
    expect(container.innerHTML).toBe('');
  });
});

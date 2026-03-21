import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock framer-motion to render children synchronously
vi.mock('framer-motion', () => ({
  motion: {
    aside: ({ children, ...props }: any) => <aside {...props}>{children}</aside>,
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock useMapStore to provide detail data
const mockDetail = {
  neighbourhood_id: '001',
  neighbourhood_name: 'Center City',
  vibe_scores: { artsy: 0.1, foodie: 0.35, nightlife: 0.28, family: 0.05, upscale: 0.15, cultural: 0.07 },
  dominant_vibe: 'foodie',
  dominant_vibe_score: 0.35,
  topics: [{ label: 'Brunch Spots', keywords: ['coffee', 'brunch'], review_share: 0.12 }],
  quotes: { foodie: ['Great brunch spot!', 'Amazing coffee', 'Best food in Philly'] },
  review_count: 4521,
};

vi.mock('../store/mapStore', () => ({
  useMapStore: (selector: any) => {
    const state = {
      selectedId: '001',
      hoveredId: null,
      isLoading: false,
      detail: mockDetail,
      setSelected: vi.fn(),
      setHovered: vi.fn(),
      setDetail: vi.fn(),
      setLoading: vi.fn(),
      clearSelection: vi.fn(),
    };
    return selector(state);
  },
}));

import Sidebar from '../components/Sidebar';

describe('Sidebar', () => {
  it('renders detail on selection', () => {
    render(<Sidebar isOpen={true} onClose={() => {}} />);
    expect(screen.getByTestId('detail-panel')).toBeInTheDocument();
    expect(screen.getByText('Center City')).toBeInTheDocument();
  });

  it('shows vibe bars', () => {
    render(<Sidebar isOpen={true} onClose={() => {}} />);
    expect(screen.getByTestId('vibe-bars')).toBeInTheDocument();
  });

  it('shows quotes', () => {
    render(<Sidebar isOpen={true} onClose={() => {}} />);
    expect(screen.getByTestId('quote-carousel')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<Sidebar isOpen={false} onClose={() => {}} />);
    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
  });
});

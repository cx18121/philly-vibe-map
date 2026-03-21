import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('framer-motion', () => ({
  motion: {
    aside: ({ children, ...props }: any) => <aside {...props}>{children}</aside>,
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('../store/mapStore', () => ({
  useMapStore: (selector: any) => {
    const state = {
      selectedId: '001',
      hoveredId: null,
      isLoading: false,
      detail: null,
      setSelected: vi.fn(),
      setHovered: vi.fn(),
      setDetail: vi.fn(),
      setLoading: vi.fn(),
      clearSelection: vi.fn(),
    };
    return selector(state);
  },
}));

import BottomSheet from '../components/BottomSheet';

describe('BottomSheet', () => {
  it('renders bottom sheet container when open', () => {
    render(<BottomSheet isOpen={true} onClose={() => {}} />);
    expect(screen.getByTestId('bottom-sheet')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<BottomSheet isOpen={false} onClose={() => {}} />);
    expect(screen.queryByTestId('bottom-sheet')).not.toBeInTheDocument();
  });
});

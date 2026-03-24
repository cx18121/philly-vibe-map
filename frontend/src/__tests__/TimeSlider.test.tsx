import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

// Default mock state
let mockState: Record<string, unknown>;
const mockSetYear = vi.fn();
const mockTogglePlay = vi.fn();

vi.mock('../store/mapStore', () => ({
  useMapStore: (selector: (state: Record<string, unknown>) => unknown) => {
    return selector(mockState);
  },
}));

vi.mock('../hooks/useAnimationFrame', () => ({
  useAnimationFrame: vi.fn(),
}));

vi.mock('../hooks/useMediaQuery', () => ({
  useMediaQuery: () => false,
}));

import TimeSlider from '../components/TimeSlider';

beforeEach(() => {
  vi.clearAllMocks();
  mockState = {
    currentYear: 2019,
    isPlaying: false,
    availableYears: [2019, 2020, 2021, 2022],
    setYear: mockSetYear,
    togglePlay: mockTogglePlay,
  };
});

describe('TimeSlider', () => {
  it('renders play button with aria-label "Play timeline"', () => {
    render(<TimeSlider />);
    expect(screen.getByLabelText('Play timeline')).toBeInTheDocument();
  });

  it('renders range input with min/max from availableYears', () => {
    render(<TimeSlider />);
    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('min', '2019');
    expect(slider).toHaveAttribute('max', '2022');
  });

  it('displays current year', () => {
    render(<TimeSlider />);
    // Year appears in both the main display and the endpoint label
    const yearElements = screen.getAllByText('2019');
    expect(yearElements.length).toBeGreaterThanOrEqual(1);
    expect(yearElements[0]).toBeInTheDocument();
  });

  it('calls setYear when slider changes', () => {
    render(<TimeSlider />);
    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '2021' } });
    expect(mockSetYear).toHaveBeenCalledWith(2021);
  });

  it('calls togglePlay when play button clicked', () => {
    render(<TimeSlider />);
    const playButton = screen.getByLabelText('Play timeline');
    fireEvent.click(playButton);
    expect(mockTogglePlay).toHaveBeenCalled();
  });

  it('shows pause label when isPlaying is true', () => {
    mockState = { ...mockState, isPlaying: true };
    render(<TimeSlider />);
    expect(screen.getByLabelText('Pause timeline')).toBeInTheDocument();
  });

  it('returns null when no available years', () => {
    mockState = { ...mockState, availableYears: [] };
    const { container } = render(<TimeSlider />);
    expect(container.querySelector('[role="group"]')).not.toBeInTheDocument();
  });
});

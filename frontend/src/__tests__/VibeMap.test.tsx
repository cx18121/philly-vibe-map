import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import React from 'react';

// Capture handlers passed to the mock Map for direct invocation in tests
let capturedHandlers: Record<string, (...args: unknown[]) => void> = {};

// Mock react-map-gl/maplibre since it relies on WebGL not available in jsdom
vi.mock('react-map-gl/maplibre', () => {
  return {
    default: React.forwardRef(
      (
        { children, onMouseMove, onMouseLeave, onClick }: Record<string, unknown>,
        ref: React.Ref<HTMLDivElement>,
      ) => {
        capturedHandlers = {
          onMouseMove: onMouseMove as (...args: unknown[]) => void,
          onMouseLeave: onMouseLeave as (...args: unknown[]) => void,
          onClick: onClick as (...args: unknown[]) => void,
        };
        return React.createElement(
          'div',
          { 'data-testid': 'map', ref },
          children as React.ReactNode,
        );
      },
    ),
    Source: ({ children, ...props }: Record<string, unknown>) =>
      React.createElement(
        'div',
        { 'data-testid': 'source', ...props },
        children as React.ReactNode,
      ),
    Layer: (props: Record<string, unknown>) =>
      React.createElement('div', { 'data-testid': `layer-${props.id}` }),
  };
});

// Test GeoJSON fixture
const testGeojson = {
  type: 'FeatureCollection' as const,
  features: [
    {
      type: 'Feature' as const,
      properties: {
        NEIGHBORHOOD_NUMBER: '001',
        NEIGHBORHOOD_NAME: 'Center City',
        dominant_vibe: 'upscale',
      },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]],
      },
    },
    {
      type: 'Feature' as const,
      properties: {
        NEIGHBORHOOD_NUMBER: '002',
        NEIGHBORHOOD_NAME: 'Fishtown',
        dominant_vibe: 'artsy',
      },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]],
      },
    },
  ],
};

// Mock useNeighbourhoods to return test GeoJSON
vi.mock('../hooks/useNeighbourhoods', () => ({
  useNeighbourhoods: () => ({
    geojson: testGeojson,
    loading: false,
    error: null,
  }),
}));

vi.mock('../hooks/useNeighbourhoodDetail', () => ({
  useNeighbourhoodDetail: () => {},
}));

// Track store calls for keyboard/hover assertions
const mockSetSelected = vi.fn();
const mockSetHovered = vi.fn();
const mockClearSelection = vi.fn();

vi.mock('../store/mapStore', () => ({
  useMapStore: (selector: (state: Record<string, unknown>) => unknown) => {
    const state = {
      selectedId: null,
      hoveredId: null,
      isLoading: false,
      detail: null,
      setSelected: mockSetSelected,
      setHovered: mockSetHovered,
      setDetail: vi.fn(),
      setLoading: vi.fn(),
      clearSelection: mockClearSelection,
    };
    return selector(state);
  },
}));

import VibeMap from '../components/VibeMap';

beforeEach(() => {
  vi.clearAllMocks();
  capturedHandlers = {};
});

describe('VibeMap', () => {
  it('renders fill and outline layers', () => {
    render(<VibeMap />);
    expect(screen.getByTestId('layer-neighbourhood-fill')).toBeInTheDocument();
    expect(screen.getByTestId('layer-neighbourhood-outline')).toBeInTheDocument();
  });

  it('renders source with geojson data', () => {
    render(<VibeMap />);
    expect(screen.getByTestId('source')).toBeInTheDocument();
  });

  it('has aria-label for accessibility', () => {
    render(<VibeMap />);
    expect(screen.getByLabelText(/Neighbourhood vibe map/)).toBeInTheDocument();
  });
});

describe('MAP-03: Hover tooltip', () => {
  it('shows tooltip with name and vibe when hovering a feature', () => {
    render(<VibeMap />);

    const mockEvent = {
      features: [
        {
          properties: {
            NEIGHBORHOOD_NUMBER: '001',
            NEIGHBORHOOD_NAME: 'Center City',
            dominant_vibe: 'upscale',
          },
        },
      ],
      point: { x: 100, y: 200 },
    };

    act(() => {
      capturedHandlers.onMouseMove(mockEvent);
    });

    expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    expect(screen.getByText('Center City')).toBeInTheDocument();
    expect(mockSetHovered).toHaveBeenCalledWith('001');
  });

  it('hides tooltip on mouse leave', () => {
    render(<VibeMap />);

    // First hover to show tooltip
    const hoverEvent = {
      features: [
        {
          properties: {
            NEIGHBORHOOD_NUMBER: '001',
            NEIGHBORHOOD_NAME: 'Center City',
            dominant_vibe: 'upscale',
          },
        },
      ],
      point: { x: 100, y: 200 },
    };

    act(() => {
      capturedHandlers.onMouseMove(hoverEvent);
    });

    // Then leave
    act(() => {
      capturedHandlers.onMouseLeave();
    });

    expect(screen.queryByTestId('tooltip')).not.toBeInTheDocument();
    expect(mockSetHovered).toHaveBeenCalledWith(null);
  });
});

describe('MAP-09: Keyboard navigation', () => {
  it('Escape key calls clearSelection', () => {
    render(<VibeMap />);
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(mockClearSelection).toHaveBeenCalled();
  });

  it('Tab key cycles through neighbourhoods and calls setHovered', () => {
    render(<VibeMap />);
    // Focus the map container so Tab is captured
    const container = screen.getByLabelText(/Neighbourhood vibe map/);
    container.focus();

    fireEvent.keyDown(window, { key: 'Tab' });
    // After first Tab, should hover the first neighbourhood
    expect(mockSetHovered).toHaveBeenCalledWith('001');
  });

  it('Enter key selects the focused neighbourhood', () => {
    render(<VibeMap />);
    const container = screen.getByLabelText(/Neighbourhood vibe map/);
    container.focus();

    // Tab to focus first neighbourhood
    fireEvent.keyDown(window, { key: 'Tab' });
    // Enter to select it
    fireEvent.keyDown(window, { key: 'Enter' });
    expect(mockSetSelected).toHaveBeenCalledWith('001');
  });
});

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MapSkeleton from '../components/MapSkeleton';

describe('MapSkeleton', () => {
  it('renders loading text', () => {
    render(<MapSkeleton />);
    expect(screen.getByText('Loading map...')).toBeInTheDocument();
  });
});

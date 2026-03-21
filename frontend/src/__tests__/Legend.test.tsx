import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Legend from '../components/Legend';

describe('Legend', () => {
  it('renders all 6 archetypes', () => {
    render(<Legend />);
    expect(screen.getByText('artsy')).toBeInTheDocument();
    expect(screen.getByText('foodie')).toBeInTheDocument();
    expect(screen.getByText('nightlife')).toBeInTheDocument();
    expect(screen.getByText('family')).toBeInTheDocument();
    expect(screen.getByText('upscale')).toBeInTheDocument();
    expect(screen.getByText('cultural')).toBeInTheDocument();
  });

  it('renders heading', () => {
    render(<Legend />);
    expect(screen.getByText('Neighbourhood Vibes')).toBeInTheDocument();
  });

  it('has legend test id', () => {
    render(<Legend />);
    expect(screen.getByTestId('legend')).toBeInTheDocument();
  });
});

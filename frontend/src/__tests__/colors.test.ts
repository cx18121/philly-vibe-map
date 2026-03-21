import { describe, it, expect } from 'vitest';
import { VIBE_COLORS, VIBE_MATCH_EXPR } from '../lib/colors';

describe('VIBE_COLORS', () => {
  it('has all 6 archetypes', () => {
    const keys = Object.keys(VIBE_COLORS);
    expect(keys).toEqual(['artsy', 'foodie', 'nightlife', 'family', 'upscale', 'cultural']);
  });

  it('all archetypes have distinct colours', () => {
    const values = Object.values(VIBE_COLORS);
    expect(new Set(values).size).toBe(6);
  });

  it('all colours are valid hex', () => {
    Object.values(VIBE_COLORS).forEach((c) => {
      expect(c).toMatch(/^#[0-9A-Fa-f]{6}$/);
    });
  });
});

describe('VIBE_MATCH_EXPR', () => {
  it('starts with match expression', () => {
    expect(VIBE_MATCH_EXPR[0]).toBe('match');
  });

  it('has a default fallback as last element', () => {
    expect(VIBE_MATCH_EXPR[VIBE_MATCH_EXPR.length - 1]).toBe('#888888');
  });
});

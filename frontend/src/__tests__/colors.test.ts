import { describe, it, expect } from 'vitest';
import { VIBE_COLORS, VIBE_MATCH_EXPR, getDominantColor, getInterpolatedColor } from '../lib/colors';

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

const mockTemporal = {
  '001': {
    '2019': { artsy: 0.1, foodie: 0.8, nightlife: 0.05, family: 0.02, upscale: 0.01, cultural: 0.02 },
    '2020': { artsy: 0.7, foodie: 0.1, nightlife: 0.05, family: 0.05, upscale: 0.05, cultural: 0.05 },
  },
};

describe('getDominantColor', () => {
  it('returns the colour of the highest-scoring archetype', () => {
    const scores = { artsy: 0.1, foodie: 0.8, nightlife: 0.05, family: 0.02, upscale: 0.01, cultural: 0.02 };
    expect(getDominantColor(scores)).toBe(VIBE_COLORS.foodie);
  });

  it('returns fallback for all-zero scores', () => {
    const scores = { artsy: 0, foodie: 0, nightlife: 0, family: 0, upscale: 0, cultural: 0 };
    expect(getDominantColor(scores)).toBe('#888888');
  });
});

describe('getInterpolatedColor', () => {
  it('returns dominant colour for an integer year', () => {
    expect(getInterpolatedColor(mockTemporal, '001', 2019)).toBe(VIBE_COLORS.foodie);
  });

  it('computes blended colour for a fractional year', () => {
    // At 2019.5: artsy = 0.1*0.5 + 0.7*0.5 = 0.4, foodie = 0.8*0.5 + 0.1*0.5 = 0.45
    // foodie (0.45) > artsy (0.4) so dominant is foodie
    expect(getInterpolatedColor(mockTemporal, '001', 2019.5)).toBe(VIBE_COLORS.foodie);
  });

  it('returns fallback for missing nid', () => {
    expect(getInterpolatedColor(mockTemporal, '999', 2019)).toBe('#888888');
  });
});

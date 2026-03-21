import type { VibeArchetype } from './types';

export const VIBE_COLORS: Record<VibeArchetype, string> = {
  artsy:     '#882255',
  foodie:    '#CC6677',
  nightlife: '#44AA99',
  family:    '#117733',
  upscale:   '#DDCC77',
  cultural:  '#332288',
};

export const VIBE_MATCH_EXPR = [
  'match', ['get', 'dominant_vibe'],
  'artsy',     VIBE_COLORS.artsy,
  'foodie',    VIBE_COLORS.foodie,
  'nightlife', VIBE_COLORS.nightlife,
  'family',    VIBE_COLORS.family,
  'upscale',   VIBE_COLORS.upscale,
  'cultural',  VIBE_COLORS.cultural,
  '#888888',
] as const;

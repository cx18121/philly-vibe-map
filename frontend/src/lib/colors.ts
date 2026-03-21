import type { VibeArchetype, TemporalData } from './types';
import { ARCHETYPE_ORDER } from './constants';

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

const FALLBACK_COLOR = '#888888';

export function getDominantColor(scores: Record<string, number>): string {
  let maxKey: string | null = null;
  let maxVal = 0;
  for (const key of ARCHETYPE_ORDER) {
    const val = scores[key] ?? 0;
    if (val > maxVal) {
      maxVal = val;
      maxKey = key;
    }
  }
  if (!maxKey || maxVal <= 0) return FALLBACK_COLOR;
  return VIBE_COLORS[maxKey as VibeArchetype] ?? FALLBACK_COLOR;
}

export function getInterpolatedColor(
  temporal: TemporalData,
  nid: string,
  year: number,
): string {
  const nidData = temporal[nid];
  if (!nidData) return FALLBACK_COLOR;

  const floorYear = Math.floor(year);
  const ceilYear = Math.ceil(year);
  const t = year - floorYear;

  const floorScores = nidData[String(floorYear)];
  if (!floorScores) return FALLBACK_COLOR;

  // Exact integer year or ceil not available — use floor directly
  if (t === 0 || !nidData[String(ceilYear)]) {
    return getDominantColor(floorScores);
  }

  // Interpolate between floor and ceil
  const ceilScores = nidData[String(ceilYear)];
  const blended: Record<string, number> = {};
  for (const key of ARCHETYPE_ORDER) {
    const a = floorScores[key] ?? 0;
    const b = ceilScores[key] ?? 0;
    blended[key] = a * (1 - t) + b * t;
  }
  return getDominantColor(blended);
}

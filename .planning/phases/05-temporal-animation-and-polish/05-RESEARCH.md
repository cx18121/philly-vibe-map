# Phase 5: Temporal Animation and Polish - Research

**Researched:** 2026-03-21
**Domain:** MapLibre GL JS paint transitions, Framer Motion sidebar animations, CSS glow effects
**Confidence:** HIGH

## Summary

Phase 5 adds a time slider (2019-2025) that drives colour transitions on the choropleth, play/pause auto-advance, hover glow/pulse effects, and Framer Motion stagger animations on sidebar content. The existing frontend already uses Framer Motion (v12.38), MapLibre GL JS (v5.21) via react-map-gl (v8.1), and Zustand for state. The temporal data is already served by `GET /temporal` -- a dict keyed by neighbourhood ID, each containing year-keyed vibe vectors with 6 archetype scores.

The main technical challenge is smooth colour interpolation between years. MapLibre GL JS does NOT support transitions on data-driven paint properties (Mapbox GL JS issue #3170, inherited by MapLibre fork, still unresolved). The standard workaround is client-side colour interpolation using `requestAnimationFrame` with `setPaintProperty` or updating GeoJSON source data directly with pre-interpolated colours. Since we have only ~159 features, updating the GeoJSON source with computed fill colours per frame is performant and the recommended approach.

**Primary recommendation:** Store temporal data in Zustand, compute interpolated vibe colours client-side per animation frame, and update GeoJSON feature properties directly. Use CSS `filter: drop-shadow()` on a duplicate highlight layer for glow effects. Use Framer Motion variants with `staggerChildren` for sidebar content entrance animations.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VIZ-01 | Time slider (2019-2025) scrubs years; fill colours transition smoothly | Temporal data from `GET /temporal`; client-side colour interpolation via GeoJSON source update; Zustand stores `currentYear` |
| VIZ-02 | Play/pause button auto-advances years with configurable speed | `setInterval` or `requestAnimationFrame` loop controlled by Zustand `isPlaying` state |
| VIZ-03 | Colour transitions between years are interpolated smoothly (not hard cut) | Client-side linear interpolation between year N and year N+1 vibe vectors; convert interpolated vibe to colour via dominant-archetype lookup or weighted blend |
| VIZ-04 | Hovered neighbourhood pulses/glows to indicate interactivity | MapLibre `feature-state` to toggle highlight; separate highlight fill layer with elevated opacity + CSS filter or `fill-opacity` animation |
| VIZ-05 | Dominant-vibe fills have subtle ambient glow that intensifies on hover | Duplicate layer with higher opacity for selected/hovered state; CSS `filter: drop-shadow()` on map canvas parent for ambient glow; `feature-state` for hover intensity |
| VIZ-06 | Sidebar content animates in on neighbourhood selection | Framer Motion `variants` with `staggerChildren` on DetailPanel children; `AnimatePresence` already wraps Sidebar/BottomSheet |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| maplibre-gl | 5.21.0 | Map rendering, paint properties, feature-state | Already in use; `setFeatureState` and `setPaintProperty` for hover effects |
| react-map-gl | 8.1.0 | React wrapper for MapLibre | Already in use; `useMap` hook gives access to underlying map instance |
| framer-motion | 12.38.0 | Sidebar/content entrance animations | Already in use for Sidebar/BottomSheet slide animations |
| zustand | 5.0.12 | State management for year, playing, temporal data | Already in use for selectedId, hoveredId, detail |

### Supporting (no new dependencies needed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none) | - | Colour interpolation is ~15 lines of code | See "Don't Hand-Roll" exceptions below |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Client-side GeoJSON update | MapLibre `setPaintProperty` per frame | setPaintProperty with data-driven expressions does NOT transition smoothly -- known limitation |
| CSS glow via `filter` | MapLibre `fill-extrusion` layer | fill-extrusion adds 3D rendering overhead for a 2D glow effect; CSS filter is simpler and more controllable |
| d3-interpolate for colour lerp | Manual RGB interpolation | d3-interpolate is overkill for hex-to-hex lerp; 15 lines of utility code suffices for 6 fixed colours |

**Installation:**
```bash
# No new packages needed -- all dependencies already installed
```

## Architecture Patterns

### Recommended Changes to Existing Structure
```
src/
├── components/
│   ├── TimeSlider.tsx         # NEW: range input + play/pause + year label
│   ├── VibeMap.tsx            # MODIFY: consume currentYear, update GeoJSON source
│   ├── DetailPanel.tsx        # MODIFY: wrap children in stagger variants
│   ├── VibeBars.tsx           # Already uses framer-motion; no change needed
│   ├── SentimentPills.tsx     # MODIFY: wrap in motion.div with variant
│   ├── QuoteCarousel.tsx      # MODIFY: wrap in motion.div with variant
│   └── TopicList.tsx          # MODIFY: wrap in motion.div with variant
├── hooks/
│   ├── useTemporal.ts         # NEW: fetch + cache temporal data
│   └── useAnimationFrame.ts   # NEW: requestAnimationFrame hook for smooth year interpolation
├── lib/
│   ├── colors.ts              # MODIFY: add interpolateVibeColor() utility
│   └── types.ts               # MODIFY: add TemporalData type
└── store/
    └── mapStore.ts            # MODIFY: add currentYear, isPlaying, temporalData, setYear, togglePlay
```

### Pattern 1: Client-Side Colour Interpolation via GeoJSON Source Update
**What:** Instead of relying on MapLibre paint transitions (which do not work for data-driven properties), compute interpolated colours in JS and update the GeoJSON source data directly.
**When to use:** Every time the year slider moves or animation ticks.
**Example:**
```typescript
// For each feature, compute the interpolated dominant vibe colour
// between year N and year N+1 based on fractional year position
function getInterpolatedColor(
  temporal: TemporalData,
  nid: string,
  year: number, // e.g., 2021.5 for midpoint between 2021 and 2022
): string {
  const yearFloor = Math.floor(year);
  const yearCeil = Math.ceil(year);
  const t = year - yearFloor; // 0..1 fraction

  if (t === 0 || yearFloor === yearCeil) {
    const scores = temporal[nid]?.[String(yearFloor)];
    return scores ? getDominantColor(scores) : '#888888';
  }

  const scoresA = temporal[nid]?.[String(yearFloor)];
  const scoresB = temporal[nid]?.[String(yearCeil)];
  if (!scoresA || !scoresB) return '#888888';

  // Interpolate each archetype score, then pick dominant
  const blended: Record<string, number> = {};
  for (const arch of ARCHETYPE_ORDER) {
    blended[arch] = scoresA[arch] * (1 - t) + scoresB[arch] * t;
  }
  return getDominantColor(blended);
}
```

### Pattern 2: Feature-State Driven Hover Glow
**What:** Use MapLibre `setFeatureState` to mark hovered features, then use `feature-state` expressions in a highlight layer's paint properties.
**When to use:** On mouse enter/leave events.
**Example:**
```typescript
// In VibeMap, access the map instance via useMap() hook
// On hover:
map.setFeatureState(
  { source: 'neighbourhoods', id: featureId },
  { hover: true }
);

// Highlight layer paint using feature-state:
const highlightLayer = {
  id: 'neighbourhood-highlight',
  type: 'fill',
  paint: {
    'fill-color': VIBE_MATCH_EXPR, // same as base
    'fill-opacity': [
      'case',
      ['boolean', ['feature-state', 'hover'], false],
      0.85, // intensified on hover
      0.0,  // invisible normally (base layer handles ambient)
    ],
  },
};
```

### Pattern 3: Framer Motion Stagger Variants for DetailPanel
**What:** Wrap DetailPanel children in a motion container with `staggerChildren` so bars, pills, topics, and quotes animate in sequentially.
**When to use:** When a neighbourhood is selected and detail data loads.
**Example:**
```typescript
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

// In DetailPanel:
<motion.div variants={containerVariants} initial="hidden" animate="visible" key={detail.neighbourhood_id}>
  <motion.div variants={itemVariants}><VibeBars ... /></motion.div>
  <motion.div variants={itemVariants}><SentimentPills ... /></motion.div>
  <motion.div variants={itemVariants}><TopicList ... /></motion.div>
  <motion.div variants={itemVariants}><QuoteCarousel ... /></motion.div>
</motion.div>
```

### Anti-Patterns to Avoid
- **setPaintProperty with data-driven expression for smooth transitions:** MapLibre does NOT interpolate between data-driven paint property values. The change is instant. Use GeoJSON source update instead.
- **Updating source data on every mouse pixel move:** Throttle GeoJSON updates to animation frames, not raw mouse events.
- **fill-extrusion for 2D glow:** Adds WebGL overhead, requires light configuration, and produces 3D shadows -- not a glow. Use CSS `filter: drop-shadow()` or a duplicate fill layer with higher opacity.
- **Adding animate prop to Framer Motion children that should inherit parent variants:** Breaks variant inheritance. Children should only define `variants`, not `animate`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sidebar slide animation | Custom CSS transitions | Framer Motion `AnimatePresence` (already done) | Already implemented in Phase 4 |
| Time slider UI | Canvas-based custom slider | HTML `<input type="range">` styled with CSS | Native range input is accessible, keyboard-navigable, and trivial to style |
| Colour interpolation between hex values | Full colour science library | ~15-line `lerpColor(a, b, t)` utility | Only need RGB lerp between 6 known colours |
| Animation frame loop | Manual rAF + cleanup | Tiny `useAnimationFrame` custom hook (10 lines) | Cleanup on unmount is the only tricky part |

**Key insight:** This phase is primarily glue code -- connecting existing temporal API data to existing map layers via interpolation, and adding motion variants to existing components. No new heavy libraries needed.

## Common Pitfalls

### Pitfall 1: Data-Driven Paint Transitions Don't Animate
**What goes wrong:** Developer sets `fill-color` to a `match` expression and expects MapLibre to smoothly transition between values when the expression inputs change. The change is instant.
**Why it happens:** MapLibre (and Mapbox) never implemented transitions for data-driven paint properties (issue #3170, open since 2016).
**How to avoid:** Compute interpolated colours in JavaScript and update the GeoJSON source data with literal colour values per feature, OR use `feature-state` with a limited set of opacity/colour stops.
**Warning signs:** Colours "snap" between years instead of fading.

### Pitfall 2: GeoJSON Source Update Causes Full Re-Render
**What goes wrong:** Calling `map.getSource('id').setData(newGeoJSON)` on every animation frame causes the map to re-parse and re-tile the entire source.
**Why it happens:** setData replaces the entire source. For small feature counts (~159 polygons) this is acceptable, but the GeoJSON object should be reused/mutated rather than deep-cloned each frame.
**How to avoid:** Mutate feature properties in-place on the existing GeoJSON object, then call setData. Or use `feature-state` for properties that change frequently (hover) and reserve setData for year changes (7 discrete steps, not 60fps).
**Warning signs:** Map stutters during animation, high GC pressure in devtools.

### Pitfall 3: Temporal Data Shape Mismatch
**What goes wrong:** Frontend assumes years 2019-2025 but the actual temporal_series.json contains years 2007-2022 (the real Yelp data coverage).
**Why it happens:** Requirements say 2019-2025 but the Yelp Academic Dataset for Philadelphia has reviews starting from 2007.
**How to avoid:** Read available years from the temporal data dynamically rather than hardcoding 2019-2025. Use `Object.keys(temporal[firstNid])` to determine the year range.
**Warning signs:** Slider shows years with no data; empty map for certain years.

### Pitfall 4: Animation Frame Leak
**What goes wrong:** `requestAnimationFrame` loop continues after component unmount, causing state updates on unmounted components.
**Why it happens:** Missing cleanup in useEffect.
**How to avoid:** Store the rAF ID and call `cancelAnimationFrame` in the useEffect cleanup function.
**Warning signs:** Console warnings about state updates on unmounted components.

### Pitfall 5: Framer Motion Variant Inheritance Break
**What goes wrong:** Adding `animate` prop directly to a child component breaks parent variant propagation. Children animate independently instead of staggering.
**Why it happens:** Framer Motion's variant system requires children to only define `variants`, not their own `animate` prop, to inherit from the parent.
**How to avoid:** VibeBars already uses `motion.div` with its own `animate` prop for bar width. Wrap it in a motion container for the stagger effect, but let its internal animation remain separate.
**Warning signs:** All sidebar items appear at once instead of staggering in.

### Pitfall 6: Feature ID Requirement for setFeatureState
**What goes wrong:** `map.setFeatureState({ source, id }, state)` silently fails because GeoJSON features lack numeric `id` properties.
**Why it happens:** MapLibre requires features to have an `id` property (numeric) for feature-state to work, OR you must set `promoteId` on the source.
**How to avoid:** Set `promoteId: 'NEIGHBORHOOD_NUMBER'` on the GeoJSON source, OR add a numeric `id` to each feature. `promoteId` is the cleaner approach since NEIGHBORHOOD_NUMBER is already unique.
**Warning signs:** `setFeatureState` calls have no visible effect; hover highlight doesn't appear.

## Code Examples

### Temporal Data Type (from actual API response)
```typescript
// temporal_series.json shape: { [nid: string]: { [year: string]: { [archetype: string]: number } } }
// Example: { "001": { "2019": { "artsy": 0.11, "foodie": 0.54, ... }, "2020": { ... } } }
export type VibeVector = Record<string, number>;
export type TemporalData = Record<string, Record<string, VibeVector>>;
```

### Time Slider Component Pattern
```typescript
// Simple accessible range input with play/pause
interface TimeSliderProps {
  years: number[];
  currentYear: number;
  isPlaying: boolean;
  onYearChange: (year: number) => void;
  onTogglePlay: () => void;
}

function TimeSlider({ years, currentYear, isPlaying, onYearChange, onTogglePlay }: TimeSliderProps) {
  const min = years[0];
  const max = years[years.length - 1];
  return (
    <div role="group" aria-label="Time controls">
      <button onClick={onTogglePlay} aria-label={isPlaying ? 'Pause' : 'Play'}>
        {isPlaying ? '⏸' : '▶'}
      </button>
      <input
        type="range"
        min={min}
        max={max}
        step={1}
        value={currentYear}
        onChange={(e) => onYearChange(Number(e.target.value))}
        aria-label="Year"
        aria-valuetext={String(currentYear)}
      />
      <span>{currentYear}</span>
    </div>
  );
}
```

### Zustand Store Extension
```typescript
// Add to existing mapStore:
interface MapStore {
  // ... existing fields ...
  currentYear: number;
  isPlaying: boolean;
  temporalData: TemporalData | null;
  availableYears: number[];
  setYear: (year: number) => void;
  togglePlay: () => void;
  setTemporalData: (data: TemporalData) => void;
}
```

### GeoJSON Source with promoteId
```typescript
// In VibeMap, add promoteId to Source for feature-state support:
<Source id="neighbourhoods" type="geojson" data={geojson} promoteId="NEIGHBORHOOD_NUMBER">
```

### Hover Glow via Highlight Layer
```typescript
// Add after the fill layer, before the outline layer:
const highlightLayer: Omit<FillLayerSpecification, 'source'> = {
  id: 'neighbourhood-highlight',
  type: 'fill',
  paint: {
    'fill-color': '#ffffff',
    'fill-opacity': [
      'case',
      ['boolean', ['feature-state', 'hover'], false],
      0.15,
      0.0,
    ],
  },
};
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Mapbox data-driven transitions (hoped for) | Client-side interpolation + source update | Never implemented (issue #3170, 2016-present) | Must compute colours in JS, not rely on GL transitions |
| Framer Motion v6 `AnimatePresence` + `positionTransition` | Framer Motion v12 `AnimatePresence` + `layout` prop | v7+ (2023) | Already using v12; `layout` prop replaces old position transitions |
| react-map-gl v7 `useControl` | react-map-gl v8 `useMap` hook | v8 (2024) | `useMap()` provides direct access to underlying MapLibre map instance |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 + @testing-library/react 16.3.2 |
| Config file | frontend/vitest.config.ts |
| Quick run command | `cd frontend && npx vitest run --reporter=verbose` |
| Full suite command | `cd frontend && npx vitest run --reporter=verbose` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VIZ-01 | Time slider renders, year change updates store | unit | `cd frontend && npx vitest run src/__tests__/TimeSlider.test.tsx -x` | Wave 0 |
| VIZ-02 | Play/pause toggles auto-advance; pause stops | unit | `cd frontend && npx vitest run src/__tests__/TimeSlider.test.tsx -x` | Wave 0 |
| VIZ-03 | Colour interpolation produces smooth intermediate values | unit | `cd frontend && npx vitest run src/__tests__/colors.test.ts -x` | Partial (extend) |
| VIZ-04 | Hover sets feature-state; highlight layer opacity changes | unit | `cd frontend && npx vitest run src/__tests__/VibeMap.test.tsx -x` | Partial (extend) |
| VIZ-05 | Ambient glow layer exists with correct paint expression | unit | `cd frontend && npx vitest run src/__tests__/VibeMap.test.tsx -x` | Partial (extend) |
| VIZ-06 | Sidebar children render with stagger animation variants | unit | `cd frontend && npx vitest run src/__tests__/DetailPanel.test.tsx -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd frontend && npx vitest run --reporter=verbose`
- **Per wave merge:** `cd frontend && npx vitest run --reporter=verbose`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `src/__tests__/TimeSlider.test.tsx` -- covers VIZ-01, VIZ-02
- [ ] `src/__tests__/DetailPanel.test.tsx` -- covers VIZ-06 (stagger variants)
- [ ] Extend `src/__tests__/colors.test.ts` -- add interpolation tests for VIZ-03
- [ ] Extend `src/__tests__/VibeMap.test.tsx` -- add highlight layer and promoteId assertions for VIZ-04, VIZ-05

## Open Questions

1. **Temporal data year range mismatch**
   - What we know: Requirements specify 2019-2025, but actual temporal_series.json contains years 2007-2022 (Yelp Academic Dataset coverage for Philadelphia)
   - What's unclear: Should the slider show all available years (2007-2022) or only the subset with good coverage?
   - Recommendation: Derive year range dynamically from the data. Show all available years -- this is more honest and makes the portfolio piece more impressive with a longer timeline.

2. **Smooth interpolation granularity**
   - What we know: Temporal data has discrete year buckets (e.g., 2019, 2020). Interpolation between years produces fractional positions.
   - What's unclear: Should the slider snap to integer years or allow continuous scrubbing?
   - Recommendation: Snap to integer years on release (discrete steps) for clarity, but allow visual preview during drag. During play animation, interpolate between years for smooth colour transitions (advance fractional year via rAF, update colours continuously, snap display label to nearest integer).

## Sources

### Primary (HIGH confidence)
- Existing codebase: mapStore.ts, VibeMap.tsx, DetailPanel.tsx, colors.ts, api.ts -- direct inspection of current implementation
- Existing temporal_series.json artifact -- verified data shape: `{ nid: { year: { archetype: score } } }`
- [MapLibre Style Spec - Layers](https://maplibre.org/maplibre-style-spec/layers/) -- fill-color is transitionable but NOT for data-driven expressions
- [Mapbox GL JS Issue #3170](https://github.com/mapbox/mapbox-gl-js/issues/3170) -- data-driven paint transitions never implemented; applies to MapLibre fork

### Secondary (MEDIUM confidence)
- [Framer Motion stagger pattern](https://www.framer.com/motion/stagger/) -- staggerChildren API for sequential child animations
- [Framer Motion variants guide](https://reference.nirajankhatiwada.com.np/posts/pages/framermotion/variants-and-staggering-children/) -- variant inheritance rules
- [CSS drop-shadow for polygon glow](https://www.sitepoint.com/creating-shadows-around-polygons-in-css/) -- filter: drop-shadow approach

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already installed and in use; no new dependencies
- Architecture: HIGH - patterns verified against MapLibre limitations and existing code structure
- Pitfalls: HIGH - data-driven transition limitation confirmed via upstream issue tracker; temporal data shape verified from actual artifact

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (stable -- no fast-moving dependencies)

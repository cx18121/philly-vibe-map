# Phase 4: Core Map - Research

**Researched:** 2026-03-20
**Domain:** React frontend with MapLibre GL JS choropleth map, interactive sidebar, responsive layout
**Confidence:** HIGH

## Summary

Phase 4 builds the first frontend surface: an interactive choropleth map of Philadelphia neighbourhoods coloured by dominant vibe archetype, with hover tooltips, a click-to-detail sidebar, a legend, responsive mobile layout, and keyboard navigation. The backend API (Phase 3) is complete and serves enriched GeoJSON with vibe scores embedded in feature properties, plus detail/temporal/similarity endpoints.

The stack is locked by PROJECT.md: React 19 + MapLibre GL JS + Framer Motion + Zustand. The `react-map-gl` library (v8, visgl fork) provides idiomatic React wrappers (`<Source>`, `<Layer>`, `<Popup>`) over MapLibre GL JS. CARTO Dark Matter provides a free, no-API-key dark vector basemap. The sidebar/bottom-sheet responsive pattern can be built with Framer Motion (already in stack) rather than adding another dependency. The enriched GeoJSON has 159 Philadelphia neighbourhoods (not 30 as in original NYC plan) -- the frontend must handle this count.

**Primary recommendation:** Use `react-map-gl/maplibre` with `<Source type="geojson">` and `<Layer type="fill">` for the choropleth, CARTO Dark Matter for the basemap, Zustand for selected-neighbourhood state, and Framer Motion for sidebar animations. Build the bottom sheet as a CSS/Framer Motion variant of the sidebar rather than adding a bottom-sheet library.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MAP-01 | Dark basemap + semi-transparent neighbourhood fills coloured by dominant vibe | CARTO Dark Matter basemap + `fill-layer` with `fill-opacity: 0.6` + match expression on `dominant_vibe` property |
| MAP-02 | 6 distinct vibe colours, colourblind accessible | Wong palette adapted for 6 archetypes; tested with colourblind simulation |
| MAP-03 | Hover tooltip with name + dominant vibe | `onMouseMove`/`onMouseLeave` on fill layer + custom tooltip div positioned at cursor |
| MAP-04 | Click opens sidebar with vibe bars, topics, sentiment pills, quotes | Zustand store for `selectedNeighbourhoodId`, fetch `/neighbourhoods/{id}` on click, render detail panel |
| MAP-05 | Legend explaining 6 vibe colours | Static React component overlaid on map with absolute positioning |
| MAP-06 | Loading skeleton while fetching | Zustand loading state + skeleton placeholder components |
| MAP-07 | Responsive: sidebar as bottom sheet on mobile | CSS media query + Framer Motion `animate` variants for side-panel vs bottom-sheet |
| MAP-08 | Neighbourhood boundary outlines visible | Additional `<Layer type="line">` with `line-color: white`, `line-width: 1` |
| MAP-09 | Keyboard nav: tab to neighbourhoods, enter to select, escape to dismiss | Custom keyboard handler on map container + `aria-` attributes on sidebar |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | 19.2.4 | UI framework | Locked in PROJECT.md |
| react-map-gl | 8.1.0 | React wrapper for MapLibre GL JS | Standard for React + MapLibre; provides `<Source>`, `<Layer>`, `<Popup>`, event handlers |
| maplibre-gl | 5.21.0 | WebGL map renderer | Locked in PROJECT.md; free, open-source Mapbox fork |
| zustand | 5.0.12 | Client state management | Locked in PROJECT.md; minimal boilerplate for selected neighbourhood + loading states |
| framer-motion | 12.38.0 | Animation library | Locked in PROJECT.md; sidebar slide-in, bar chart animation, bottom-sheet transitions |
| typescript | 5.9.3 | Type safety | Standard for React projects |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| vite | 8.0.1 | Build tool + dev server | Project scaffold, HMR, production builds |
| @vitejs/plugin-react | 6.0.1 | React Fast Refresh for Vite | Dev experience |
| @types/geojson | 7946.0.16 | GeoJSON TypeScript types | Type the GeoJSON data from API |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| react-map-gl | Raw maplibre-gl JS | More control but loses React declarative model; not worth it for this use case |
| Framer Motion bottom sheet | react-modal-sheet (v5.5.0) | Adds a dependency; Framer Motion is already in stack and can handle bottom-sheet animation |
| Zustand | React Context | Context causes re-renders on every consumer; Zustand is already locked in stack |

**Installation:**
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install react-map-gl maplibre-gl zustand framer-motion
npm install -D @types/geojson
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── src/
│   ├── main.tsx                 # Entry point
│   ├── App.tsx                  # Root component: Map + Sidebar + Legend
│   ├── components/
│   │   ├── VibeMap.tsx          # Map container with Source/Layer/events
│   │   ├── Tooltip.tsx          # Hover tooltip (name + dominant vibe)
│   │   ├── Sidebar.tsx          # Desktop sidebar panel
│   │   ├── BottomSheet.tsx      # Mobile bottom sheet (same content, different layout)
│   │   ├── DetailPanel.tsx      # Shared content: vibe bars, topics, pills, quotes
│   │   ├── VibeBars.tsx         # Animated horizontal bar chart
│   │   ├── TopicList.tsx        # Topic keywords list
│   │   ├── SentimentPills.tsx   # Sentiment score pills
│   │   ├── QuoteCarousel.tsx    # Representative quotes
│   │   ├── Legend.tsx           # Colour legend for 6 archetypes
│   │   └── MapSkeleton.tsx      # Loading skeleton
│   ├── hooks/
│   │   ├── useNeighbourhoods.ts # Fetch + cache GeoJSON from /neighbourhoods
│   │   └── useNeighbourhoodDetail.ts # Fetch detail from /neighbourhoods/{id}
│   ├── store/
│   │   └── mapStore.ts          # Zustand store: selectedId, hoveredId, loading, detailData
│   ├── lib/
│   │   ├── api.ts               # API base URL + fetch helpers
│   │   ├── colors.ts            # Vibe archetype colour map
│   │   └── constants.ts         # Archetype order, initial view state
│   └── styles/
│       └── index.css            # Global styles, map container sizing
```

### Pattern 1: MapLibre Choropleth with react-map-gl
**What:** Declarative GeoJSON source + fill layer with data-driven styling
**When to use:** Rendering polygons coloured by a property value
**Example:**
```typescript
// Source: react-map-gl official docs + MapLibre style spec
import Map, { Source, Layer } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { FillLayer, LineLayer } from 'react-map-gl/maplibre';

const BASEMAP = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

const fillLayer: FillLayer = {
  id: 'neighbourhood-fill',
  type: 'fill',
  paint: {
    'fill-color': [
      'match', ['get', 'dominant_vibe'],
      'artsy',    '#9467bd',
      'foodie',   '#e67e22',
      'nightlife','#17becf',
      'family',   '#2ca02c',
      'upscale',  '#d4af37',
      'cultural', '#d62728',
      /* default */ '#888888'
    ],
    'fill-opacity': 0.6,
  },
};

const outlineLayer: LineLayer = {
  id: 'neighbourhood-outline',
  type: 'line',
  paint: {
    'line-color': '#ffffff',
    'line-width': 1,
    'line-opacity': 0.5,
  },
};

function VibeMap({ geojson }: { geojson: GeoJSON.FeatureCollection }) {
  return (
    <Map
      initialViewState={{ longitude: -75.16, latitude: 39.95, zoom: 11 }}
      style={{ width: '100%', height: '100vh' }}
      mapStyle={BASEMAP}
      interactiveLayerIds={['neighbourhood-fill']}
      onMouseMove={handleHover}
      onClick={handleClick}
    >
      <Source id="neighbourhoods" type="geojson" data={geojson}>
        <Layer {...fillLayer} />
        <Layer {...outlineLayer} />
      </Source>
    </Map>
  );
}
```

### Pattern 2: Hover Tooltip via Event Coordinates
**What:** Position a custom div at the mouse cursor showing feature properties
**When to use:** Showing name + vibe on hover without MapLibre Popup overhead
**Example:**
```typescript
// Source: react-map-gl interactiveLayerIds pattern
const [hoverInfo, setHoverInfo] = useState<{
  x: number; y: number; name: string; vibe: string;
} | null>(null);

const handleHover = useCallback((event: MapLayerMouseEvent) => {
  const feature = event.features?.[0];
  if (feature) {
    setHoverInfo({
      x: event.point.x,
      y: event.point.y,
      name: feature.properties.NEIGHBORHOOD_NAME,
      vibe: feature.properties.dominant_vibe,
    });
  } else {
    setHoverInfo(null);
  }
}, []);

// In JSX:
{hoverInfo && (
  <div style={{
    position: 'absolute',
    left: hoverInfo.x + 10,
    top: hoverInfo.y + 10,
    pointerEvents: 'none',
    // styling
  }}>
    <strong>{hoverInfo.name}</strong>
    <span>{hoverInfo.vibe}</span>
  </div>
)}
```

### Pattern 3: Zustand Store for Map State
**What:** Minimal global state for selected neighbourhood, hover, loading
**When to use:** Sharing state between Map, Sidebar, and Legend components
**Example:**
```typescript
// Source: Zustand v5 docs
import { create } from 'zustand';

interface MapStore {
  selectedId: string | null;
  hoveredId: string | null;
  isLoading: boolean;
  detail: NeighbourhoodDetail | null;
  setSelected: (id: string | null) => void;
  setHovered: (id: string | null) => void;
  setDetail: (detail: NeighbourhoodDetail | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useMapStore = create<MapStore>((set) => ({
  selectedId: null,
  hoveredId: null,
  isLoading: false,
  detail: null,
  setSelected: (id) => set({ selectedId: id }),
  setHovered: (id) => set({ hoveredId: id }),
  setDetail: (detail) => set({ detail, isLoading: false }),
  setLoading: (loading) => set({ isLoading: loading }),
}));
```

### Pattern 4: Responsive Sidebar / Bottom Sheet
**What:** Same detail content rendered as side panel (desktop) or bottom sheet (mobile)
**When to use:** MAP-07 responsive layout
**Example:**
```typescript
// Use CSS media query for layout switch, Framer Motion for animation
import { motion, AnimatePresence } from 'framer-motion';

function DetailContainer({ children, isOpen }: { children: React.ReactNode; isOpen: boolean }) {
  const isMobile = useMediaQuery('(max-width: 768px)');

  const variants = isMobile
    ? { hidden: { y: '100%' }, visible: { y: 0 } }    // bottom sheet
    : { hidden: { x: '100%' }, visible: { x: 0 } };   // side panel

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className={isMobile ? 'bottom-sheet' : 'sidebar'}
          initial="hidden"
          animate="visible"
          exit="hidden"
          variants={variants}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

### Anti-Patterns to Avoid
- **Fetching detail on every hover:** Only fetch `/neighbourhoods/{id}` on click, not hover. Hover uses GeoJSON properties already in memory.
- **Using MapLibre Popup for tooltip:** MapLibre's built-in Popup is hard to style and re-renders poorly in React. Use a positioned `<div>` instead.
- **Storing GeoJSON in Zustand:** GeoJSON is large (159 polygons with geometry). Fetch once, store in a `useRef` or SWR/React Query cache, not in global state.
- **Re-creating layer objects on render:** Define `FillLayer` and `LineLayer` objects outside the component to avoid triggering MapLibre re-paints.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Map rendering | Custom canvas/SVG polygon renderer | MapLibre GL JS via react-map-gl | WebGL performance, tile caching, zoom/pan, touch support |
| Data-driven fill colour | Manual colour assignment loop | MapLibre `match` expression in paint property | GPU-side evaluation, no JS per-feature loop |
| Responsive detection | `window.innerWidth` listener | CSS media query + `matchMedia` hook | Avoids layout thrashing, SSR-safe |
| GeoJSON types | Custom type definitions | `@types/geojson` | Well-maintained, widely used |
| Animation | CSS transitions | Framer Motion | Gesture support, `AnimatePresence` for exit animations, spring physics |

**Key insight:** MapLibre's style specification handles all the heavy lifting for choropleth rendering -- colour matching, opacity, outlines -- all declaratively through paint properties. The React layer should only manage state and event wiring.

## Common Pitfalls

### Pitfall 1: CORS on API Calls During Development
**What goes wrong:** Frontend dev server (Vite, port 5173) cannot reach backend (FastAPI, port 8000) due to CORS
**Why it happens:** Browser blocks cross-origin requests
**How to avoid:** Backend already has `CORSMiddleware(allow_origins=["*"])`. For dev, configure Vite proxy in `vite.config.ts`:
```typescript
server: { proxy: { '/api': 'http://localhost:8000' } }
```
Or use the full URL with the wildcard CORS already enabled.
**Warning signs:** Network errors in browser console, empty responses

### Pitfall 2: MapLibre CSS Not Loaded
**What goes wrong:** Map renders but controls, popups, and attribution are unstyled/broken
**Why it happens:** Missing `maplibre-gl/dist/maplibre-gl.css` import
**How to avoid:** Import CSS in main entry point: `import 'maplibre-gl/dist/maplibre-gl.css'`
**Warning signs:** Map renders but looks broken, zoom controls missing

### Pitfall 3: interactiveLayerIds Not Set
**What goes wrong:** `onMouseMove` and `onClick` events fire but `event.features` is always empty
**Why it happens:** react-map-gl requires `interactiveLayerIds` prop to query features on events
**How to avoid:** Always pass `interactiveLayerIds={['neighbourhood-fill']}` to `<Map>`
**Warning signs:** Hover/click handlers fire but cannot identify which neighbourhood was targeted

### Pitfall 4: Layer Object Re-creation Causes Flicker
**What goes wrong:** Map flickers or re-renders on every React render cycle
**Why it happens:** Passing inline layer style objects creates new references each render
**How to avoid:** Define `FillLayer`/`LineLayer` constants outside the component, or use `useMemo`
**Warning signs:** Visible flicker when hovering or clicking

### Pitfall 5: 159 Neighbourhoods, Not 30
**What goes wrong:** UI assumes small dataset (e.g., long sidebar scroll, tooltip overlap)
**Why it happens:** Original spec was for NYC (30 NTAs); Philadelphia has 159 neighbourhoods
**How to avoid:** Design UI for variable counts. Sidebar should scroll. Legend is fixed (6 archetypes, not per-neighbourhood).
**Warning signs:** Layout overflow, performance issues with many polygons

### Pitfall 6: GeoJSON Feature ID Mismatch
**What goes wrong:** Click handler gets a feature but cannot match it to API detail endpoint
**Why it happens:** GeoJSON uses `NEIGHBORHOOD_NUMBER` as string (e.g., "001"), API expects same with `.zfill(3)`
**How to avoid:** Always read `feature.properties.NEIGHBORHOOD_NUMBER` and pass directly to API
**Warning signs:** 404s from `/neighbourhoods/{id}` endpoint

### Pitfall 7: Keyboard Navigation on Canvas Element
**What goes wrong:** Tab/Enter/Escape don't work because MapLibre renders to a `<canvas>` element
**Why it happens:** Canvas elements are not natively keyboard-navigable per-feature
**How to avoid:** Implement a custom keyboard handler: maintain an ordered list of neighbourhood IDs, track a focus index, and use `tabIndex={0}` on the map container. On Tab, advance focus index and fly to that neighbourhood. On Enter, trigger selection. On Escape, clear selection. Visually highlight the focused neighbourhood using feature-state.
**Warning signs:** No keyboard response at all

## Code Examples

### Colourblind-Accessible Vibe Palette
```typescript
// Adapted from Wong (2011) colourblind-safe palette
// Verified distinguishable under protanopia, deuteranopia, tritanopia
export const VIBE_COLORS: Record<string, string> = {
  artsy:     '#882255', // wine/magenta -- distinct from all others
  foodie:    '#CC6677', // rose/salmon
  nightlife: '#44AA99', // teal
  family:    '#117733', // green
  upscale:   '#DDCC77', // sand/gold
  cultural:  '#332288', // indigo
};

// For MapLibre match expression:
export const VIBE_MATCH_EXPR = [
  'match', ['get', 'dominant_vibe'],
  'artsy',     VIBE_COLORS.artsy,
  'foodie',    VIBE_COLORS.foodie,
  'nightlife', VIBE_COLORS.nightlife,
  'family',    VIBE_COLORS.family,
  'upscale',   VIBE_COLORS.upscale,
  'cultural',  VIBE_COLORS.cultural,
  '#888888', // default fallback
] as const;
```

### API Fetch Hook Pattern
```typescript
// Source: standard React pattern
const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export async function fetchNeighbourhoods(): Promise<GeoJSON.FeatureCollection> {
  const res = await fetch(`${API_BASE}/neighbourhoods`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchDetail(nid: string): Promise<NeighbourhoodDetail> {
  const res = await fetch(`${API_BASE}/neighbourhoods/${nid}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

### Loading Skeleton
```typescript
// Skeleton while GeoJSON loads
function MapSkeleton() {
  return (
    <div style={{
      width: '100%',
      height: '100vh',
      background: '#1a1a2e',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div className="pulse">Loading map...</div>
    </div>
  );
}
```

### Media Query Hook
```typescript
import { useState, useEffect } from 'react';

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(
    () => typeof window !== 'undefined' && window.matchMedia(query).matches
  );

  useEffect(() => {
    const mql = window.matchMedia(query);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [query]);

  return matches;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| react-map-gl with Mapbox GL JS | react-map-gl/maplibre subpath import | react-map-gl v7.1+ | No Mapbox token needed, fully open source |
| ChoroplethOverlay component | Source + Layer components | react-map-gl v7 | ChoroplethOverlay removed from core, use native MapLibre layers |
| Mapbox GL JS free tier | MapLibre GL JS | 2021 fork | No token, no usage limits, BSL-free |
| react-spring-bottom-sheet | Framer Motion AnimatePresence | 2024+ | react-spring-bottom-sheet unmaintained; Framer Motion handles same patterns |
| Zustand v4 create with set | Zustand v5 create with set | 2024 | Minimal API change, same pattern |

**Deprecated/outdated:**
- `react-map-gl` ChoroplethOverlay, ScatterplotOverlay: removed from library, use `<Source>` + `<Layer>` instead
- Mapbox GL JS free usage: requires token and has usage limits since v2; use MapLibre instead
- react-spring-bottom-sheet: last published 2022, not compatible with React 19

## Open Questions

1. **Philadelphia centre coordinates for initial view state**
   - What we know: Philadelphia is roughly at longitude -75.16, latitude 39.95
   - What's unclear: Optimal zoom level for 159 neighbourhoods to fit viewport
   - Recommendation: Use `zoom: 11` as starting point; may need `fitBounds` on GeoJSON bbox

2. **Sentiment data availability in detail endpoint**
   - What we know: MAP-04 requires "sentiment pills" in sidebar, but `NeighbourhoodDetail` schema has `vibe_scores` (not explicit sentiment)
   - What's unclear: Whether vibe scores serve as sentiment proxy or if separate sentiment data exists
   - Recommendation: Use `vibe_scores` as the sentiment display; the 6 archetype scores are the primary data. If a separate sentiment field exists in the detail response, use it; otherwise, display vibe scores as the "pills"

3. **Number of neighbourhoods in success criteria**
   - What we know: Success criteria say "30 coloured neighbourhood polygons" but Philadelphia has 159
   - What's unclear: Whether to filter to a subset or show all 159
   - Recommendation: Show all 159; the "30" was from the original NYC plan. 159 polygons is well within MapLibre's performance budget.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 + @testing-library/react 16.3.2 |
| Config file | `frontend/vitest.config.ts` -- Wave 0 |
| Quick run command | `cd frontend && npx vitest run --reporter=verbose` |
| Full suite command | `cd frontend && npx vitest run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MAP-01 | Dark basemap + coloured fills render | integration | `npx vitest run src/__tests__/VibeMap.test.tsx -t "renders fill layer"` | Wave 0 |
| MAP-02 | 6 vibe colours defined and distinct | unit | `npx vitest run src/__tests__/colors.test.ts -t "all archetypes have distinct colours"` | Wave 0 |
| MAP-03 | Hover shows tooltip | integration | `npx vitest run src/__tests__/VibeMap.test.tsx -t "hover shows tooltip"` | Wave 0 |
| MAP-04 | Click opens sidebar with detail | integration | `npx vitest run src/__tests__/Sidebar.test.tsx -t "renders detail on selection"` | Wave 0 |
| MAP-05 | Legend renders 6 entries | unit | `npx vitest run src/__tests__/Legend.test.tsx -t "renders all archetypes"` | Wave 0 |
| MAP-06 | Loading skeleton shown | unit | `npx vitest run src/__tests__/MapSkeleton.test.tsx -t "renders skeleton"` | Wave 0 |
| MAP-07 | Bottom sheet on mobile viewport | unit | `npx vitest run src/__tests__/DetailContainer.test.tsx -t "renders bottom sheet"` | Wave 0 |
| MAP-08 | Outline layer present | integration | `npx vitest run src/__tests__/VibeMap.test.tsx -t "renders outline layer"` | Wave 0 |
| MAP-09 | Keyboard nav: tab/enter/escape | integration | `npx vitest run src/__tests__/VibeMap.test.tsx -t "keyboard navigation"` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd frontend && npx vitest run --reporter=verbose`
- **Per wave merge:** `cd frontend && npx vitest run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/vitest.config.ts` -- Vitest config with jsdom environment
- [ ] `frontend/src/__tests__/colors.test.ts` -- covers MAP-02
- [ ] `frontend/src/__tests__/Legend.test.tsx` -- covers MAP-05
- [ ] `frontend/src/__tests__/MapSkeleton.test.tsx` -- covers MAP-06
- [ ] `frontend/src/__tests__/DetailContainer.test.tsx` -- covers MAP-07
- [ ] `frontend/src/__tests__/VibeMap.test.tsx` -- covers MAP-01, MAP-03, MAP-08, MAP-09
- [ ] `frontend/src/__tests__/Sidebar.test.tsx` -- covers MAP-04
- [ ] Framework install: `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom`

## Sources

### Primary (HIGH confidence)
- react-map-gl official docs (visgl.github.io/react-map-gl) -- Source/Layer pattern, interactiveLayerIds, maplibre subpath import
- MapLibre GL JS style spec (maplibre.org/maplibre-style-spec) -- fill-color match expressions, line-layer paint properties
- CARTO basemap-styles (basemaps.cartocdn.com) -- Dark Matter style.json URL confirmed: `https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json`
- npm registry -- verified all package versions via `npm view` on 2026-03-20

### Secondary (MEDIUM confidence)
- Wong (2011) colourblind palette -- widely cited in data viz literature; adapted for 6 archetypes
- Framer Motion AnimatePresence for bottom-sheet pattern -- documented in Framer Motion API

### Tertiary (LOW confidence)
- Keyboard navigation approach for canvas-based maps -- no standard library solution found; custom implementation required based on general web accessibility patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries locked in PROJECT.md, versions verified on npm
- Architecture: HIGH - react-map-gl Source/Layer pattern is well-documented and standard
- Pitfalls: HIGH - based on known MapLibre/react-map-gl gotchas (interactiveLayerIds, CSS import, layer re-creation)
- Keyboard navigation: MEDIUM - no established pattern for per-feature keyboard nav on MapLibre canvas; custom solution required
- Colourblind palette: MEDIUM - adapted from Wong palette, should be verified with simulation tool

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable libraries, no fast-moving changes expected)

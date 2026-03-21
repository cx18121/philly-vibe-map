---
phase: 04-core-map
plan: 01
subsystem: ui
tags: [react, vite, typescript, zustand, maplibre, framer-motion, vitest]

# Dependency graph
requires:
  - phase: 03-backend-api
    provides: REST API endpoints (/neighbourhoods, /neighbourhoods/{nid}) and schema contracts
provides:
  - Vite React-TS project scaffold with all core dependencies
  - TypeScript interfaces mirroring backend schemas (NeighbourhoodDetail, TopicEntry, SimilarNeighbourhood)
  - Colourblind-safe vibe palette (VIBE_COLORS) and MapLibre match expression (VIBE_MATCH_EXPR)
  - Zustand store (useMapStore) for map interaction state
  - API fetch helpers (fetchNeighbourhoods, fetchDetail)
  - Data hooks (useNeighbourhoods, useNeighbourhoodDetail, useMediaQuery)
  - Loading skeleton component (MapSkeleton)
affects: [04-core-map plan-02, 04-core-map plan-03]

# Tech tracking
tech-stack:
  added: [react@19, react-map-gl@8, maplibre-gl, zustand, framer-motion, vite, vitest, @testing-library/react]
  patterns: [zustand-store, api-fetch-helpers, custom-hooks, vitest-jsdom]

key-files:
  created:
    - frontend/src/lib/types.ts
    - frontend/src/lib/colors.ts
    - frontend/src/lib/constants.ts
    - frontend/src/lib/api.ts
    - frontend/src/store/mapStore.ts
    - frontend/src/hooks/useNeighbourhoods.ts
    - frontend/src/hooks/useNeighbourhoodDetail.ts
    - frontend/src/hooks/useMediaQuery.ts
    - frontend/src/components/MapSkeleton.tsx
    - frontend/src/__tests__/colors.test.ts
    - frontend/src/__tests__/MapSkeleton.test.tsx
    - frontend/vitest.config.ts
    - frontend/vite.config.ts
  modified:
    - frontend/index.html
    - frontend/src/main.tsx
    - frontend/src/App.tsx
    - frontend/src/styles/index.css

key-decisions:
  - "Explicit FeatureCollection import from geojson types instead of GeoJSON namespace to satisfy verbatimModuleSyntax"
  - "API_BASE defaults to empty string so Vite dev proxy handles /neighbourhoods -> localhost:8000"
  - "Wong-adapted palette for 6 vibe archetypes with colourblind accessibility"

patterns-established:
  - "Zustand store pattern: create<StoreType>((set) => ({...})) with selector-based consumption"
  - "API helper pattern: async function with fetch, error check, typed return"
  - "Custom hook pattern: useState + useEffect with ref guard for StrictMode double-mount"

requirements-completed: [MAP-02, MAP-06]

# Metrics
duration: 9min
completed: 2026-03-21
---

# Phase 4 Plan 1: Frontend Foundation Summary

**Vite React-TS scaffold with Zustand store, Wong-palette vibe colours, typed API hooks, and MapSkeleton loading component**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-21T06:27:48Z
- **Completed:** 2026-03-21T06:37:03Z
- **Tasks:** 3
- **Files modified:** 17

## Accomplishments
- Scaffolded complete Vite + React 19 + TypeScript project with all core dependencies (react-map-gl, maplibre-gl, zustand, framer-motion)
- Created full TypeScript contract layer mirroring backend schemas with colourblind-safe vibe palette
- Built Zustand state management, API fetch helpers, and data hooks establishing patterns for Plans 02-03
- All 6 unit tests passing (colours + skeleton), TypeScript compiles cleanly

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold Vite project** - `bdf747c` (feat)
2. **Task 2: Core library modules** - `3a686dd` (feat)
3. **Task 3: Hooks, skeleton, tests** - `27701d7` (feat)

## Files Created/Modified
- `frontend/src/lib/types.ts` - TypeScript interfaces mirroring backend NeighbourhoodDetail, TopicEntry, SimilarNeighbourhood, VibeArchetype
- `frontend/src/lib/colors.ts` - Wong-palette VIBE_COLORS (6 archetypes) and VIBE_MATCH_EXPR for MapLibre
- `frontend/src/lib/constants.ts` - ARCHETYPE_ORDER, BASEMAP_STYLE, INITIAL_VIEW (Philadelphia), MOBILE_BREAKPOINT
- `frontend/src/lib/api.ts` - fetchNeighbourhoods() and fetchDetail() targeting backend API
- `frontend/src/store/mapStore.ts` - Zustand store with selectedId, hoveredId, isLoading, detail, setters, clearSelection
- `frontend/src/hooks/useNeighbourhoods.ts` - GeoJSON data hook with loading/error states
- `frontend/src/hooks/useNeighbourhoodDetail.ts` - Detail fetch hook wired to Zustand store
- `frontend/src/hooks/useMediaQuery.ts` - Responsive breakpoint detection hook
- `frontend/src/components/MapSkeleton.tsx` - Loading skeleton with pulse animation
- `frontend/src/__tests__/colors.test.ts` - 5 tests: 6 archetypes, distinct colours, valid hex, match expr
- `frontend/src/__tests__/MapSkeleton.test.tsx` - 1 test: renders loading text
- `frontend/vite.config.ts` - Vite config with API proxy for development
- `frontend/vitest.config.ts` - Vitest config with jsdom environment

## Decisions Made
- Used explicit `import type { FeatureCollection } from 'geojson'` instead of `GeoJSON.FeatureCollection` namespace to satisfy TypeScript verbatimModuleSyntax strict mode
- API_BASE defaults to empty string so the Vite dev proxy at `/api` handles routing to localhost:8000
- Wong-adapted colourblind-safe palette chosen for the 6 vibe archetypes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed GeoJSON namespace import for verbatimModuleSyntax**
- **Found during:** Task 2 (Core library modules)
- **Issue:** `GeoJSON.FeatureCollection` namespace not available under Vite's `verbatimModuleSyntax: true` TypeScript config
- **Fix:** Changed to explicit `import type { FeatureCollection } from 'geojson'`
- **Files modified:** frontend/src/lib/api.ts
- **Verification:** `npm run build` exits 0
- **Committed in:** 3a686dd (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minimal - import style change for TypeScript compatibility. No scope creep.

## Issues Encountered
None beyond the GeoJSON import fix documented above.

## Known Stubs
None - all modules export real implementations. The App.tsx placeholder ("Vibe Mapper" div) is intentional and will be replaced in Plan 02 with the map component.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All shared modules (types, colours, constants, API, store, hooks) ready for import by Plans 02 and 03
- Plan 02 can immediately build the MapView component using useNeighbourhoods, VIBE_MATCH_EXPR, useMapStore
- Plan 03 can build the sidebar using useNeighbourhoodDetail, useMediaQuery, useMapStore

## Self-Check: PASSED

- All 13 created files verified present on disk
- All 3 task commits verified in git log (bdf747c, 3a686dd, 27701d7)

---
*Phase: 04-core-map*
*Completed: 2026-03-21*

---
phase: 06-deployment-and-sharing
plan: 01
subsystem: infra
tags: [dockerfile, vercel, url-params, zustand, deployment]

# Dependency graph
requires:
  - phase: 05-temporal-animation-and-polish
    provides: Complete frontend with Zustand store, temporal data, and map interactions
provides:
  - Production-ready Dockerfile with dynamic PORT for Render
  - Bi-directional URL state sync (selectedId + currentYear)
  - Vercel SPA rewrite config for deep-link support
  - 8 serving artifacts committed to git (~4MB)
affects: [06-02-deploy]

# Tech tracking
tech-stack:
  added: []
  patterns: [url-state-sync, module-level-zustand-subscribe]

key-files:
  created:
    - frontend/src/lib/urlSync.ts
    - frontend/src/__tests__/urlSync.test.ts
    - frontend/vercel.json
  modified:
    - Dockerfile
    - .gitignore
    - frontend/src/App.tsx

key-decisions:
  - "initUrlSync returns unsubscribe function for test cleanup"
  - "hydrateFromUrl gated on temporalData to avoid race condition with data loading"
  - "Large ML artifacts (.npy, models, topic_assignments.json) gitignored; 8 serving artifacts committed"

patterns-established:
  - "Module-level Zustand subscribe for URL sync: call initUrlSync() outside React render cycle"
  - "URL hydration gated on data readiness: useEffect with temporalData dependency"

requirements-completed: [DEPLOY-03]

# Metrics
duration: 25min
completed: 2026-03-21
---

# Phase 06 Plan 01: Deployment Code Prep Summary

**Dynamic PORT Dockerfile, URL deep-link sync via Zustand subscribe, Vercel SPA rewrite, and 8 serving artifacts committed to git**

## Performance

- **Duration:** 25 min
- **Started:** 2026-03-21T20:31:08Z
- **Completed:** 2026-03-21T20:56:00Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Dockerfile CMD reads PORT from environment variable for Render deploy compatibility
- Bi-directional URL state sync: store changes write to URL, page load hydrates store from URL params
- Vercel SPA rewrite prevents 404 on deep-linked URLs
- 8 serving artifacts (~4MB) committed to git; large ML artifacts (~1.7GB) gitignored

## Task Commits

Each task was committed atomically:

1. **Task 1: Dockerfile dynamic PORT, Vercel config, commit serving artifacts** - `0976cd5` (chore)
2. **Task 2 RED: Failing URL sync tests** - `cdb5425` (test)
3. **Task 2 GREEN: URL sync implementation + App.tsx integration** - `45135bd` (feat)

## Files Created/Modified
- `Dockerfile` - Dynamic PORT via ${PORT:-8000} in CMD and HEALTHCHECK
- `frontend/vercel.json` - SPA rewrite rule for deep-linked URLs
- `.gitignore` - Exclude large ML artifacts, allow serving artifacts
- `frontend/src/lib/urlSync.ts` - Bi-directional URL param sync with Zustand store
- `frontend/src/__tests__/urlSync.test.ts` - 8 unit tests for URL sync module
- `frontend/src/App.tsx` - initUrlSync at module level, hydrateFromUrl after temporal data loads
- `data/output/artifacts/enriched_geojson.geojson` - Serving artifact committed
- `data/output/artifacts/representative_quotes.json` - Serving artifact committed
- `data/output/artifacts/temporal_series.json` - Serving artifact committed
- `data/output/artifacts/neighbourhood_topics.json` - Serving artifact committed
- `data/output/artifacts/vibe_scores.json` - Serving artifact committed
- `data/output/artifacts/review_counts.json` - Serving artifact committed
- `data/output/artifacts/faiss_index.bin` - Serving artifact committed
- `data/output/artifacts/faiss_id_map.json` - Serving artifact committed

## Decisions Made
- initUrlSync returns an unsubscribe function (not in original plan) to enable proper test cleanup
- hydrateFromUrl gated on temporalData being non-null to avoid race condition where URL params applied before data loads
- Used real history.replaceState for hydration tests instead of mocking window.location (jsdom does not allow location property redefinition)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed jsdom window.location mocking in tests**
- **Found during:** Task 2 (URL sync tests)
- **Issue:** jsdom does not allow Object.defineProperty or delete on window.location; tests failed with "Cannot redefine property: location"
- **Fix:** Used real window.history.replaceState to navigate to test URLs for hydration tests; used vi.spyOn for history.replaceState in serialization tests
- **Files modified:** frontend/src/__tests__/urlSync.test.ts
- **Verification:** All 8 tests pass
- **Committed in:** 45135bd

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test mocking approach adapted for jsdom compatibility. No scope creep.

## Issues Encountered
None beyond the jsdom mocking issue documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All deployment-blocking code changes are complete
- Plan 06-02 can deploy to Render (backend) and Vercel (frontend) without further code modifications
- Serving artifacts are in git, Dockerfile reads dynamic PORT, Vercel has SPA rewrite, URL deep links work

## Self-Check: PASSED

All 6 key files verified present. All 3 commits (0976cd5, cdb5425, 45135bd) verified in git log.

---
*Phase: 06-deployment-and-sharing*
*Completed: 2026-03-21*

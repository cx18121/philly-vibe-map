---
phase: 03-backend-api
plan: 01
subsystem: api
tags: [fastapi, pydantic, faiss, bertopic, pipeline, geojson]

# Dependency graph
requires:
  - phase: 02-nlp-pipeline
    provides: "All 11 NLP pipeline artifacts (embeddings, topics, vibe scores, FAISS index, GeoJSON)"
provides:
  - "neighbourhood_topics.json: per-neighbourhood top-10 topic distributions with labels/keywords/share"
  - "review_counts.json: per-neighbourhood review counts"
  - "backend/ module: FastAPI app with lifespan loading, config, loader, schemas"
  - "nid_to_name lookup built from GeoJSON at startup"
  - "Pre-serialized GeoJSON bytes for zero-cost serving"
  - "FAISS reverse map for O(1) neighbourhood-to-index lookup"
affects: [03-backend-api-02, 04-map-frontend]

# Tech tracking
tech-stack:
  added: [fastapi, pydantic]
  patterns: [lifespan-artifact-loading, dataclass-config, pre-serialized-bytes]

key-files:
  created:
    - backend/__init__.py
    - backend/config.py
    - backend/loader.py
    - backend/schemas.py
    - backend/app.py
    - tests/test_export_extension.py
  modified:
    - pipeline/stages/export.py

key-decisions:
  - "Used dataclass instead of pydantic-settings for config (pydantic-settings not installed)"
  - "Pre-serialize GeoJSON to bytes at startup for zero-cost /geojson serving"
  - "Build nid_to_name from GeoJSON features at startup instead of separate lookup file"

patterns-established:
  - "Lifespan loading: all artifacts loaded into app.state at startup via load_artifacts()"
  - "Backend config: Settings dataclass with env var defaults (ARTIFACTS_DIR, HOST, PORT)"

requirements-completed: [API-05]

# Metrics
duration: 87min
completed: 2026-03-19
---

# Phase 03 Plan 01: Export Extensions + Backend Skeleton Summary

**Extended pipeline with neighbourhood topic/count artifacts and built FastAPI backend skeleton with lifespan artifact loading, Pydantic schemas, and CORS-enabled health endpoint**

## Performance

- **Duration:** 87 min (includes DB rebuild and dependency installation)
- **Started:** 2026-03-19T18:49:14Z
- **Completed:** 2026-03-19T20:17:08Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Extended export stage with two new sub-stages producing neighbourhood_topics.json (157 neighbourhoods, top-10 topics each with labels/keywords/share) and review_counts.json (157 neighbourhoods)
- Built complete backend/ package with FastAPI app, lifespan context manager loading all 12 artifact keys into app.state
- Created Pydantic response models (HealthResponse, TopicEntry, NeighbourhoodDetail, SimilarNeighbourhood) ready for Plan 02 endpoints
- Added structure validation tests for both new artifacts

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend export stage with neighbourhood_topics.json and review_counts.json** - `62933fd` (feat)
2. **Task 2: Create backend module skeleton with config, loader, schemas, and lifespan app** - `cac1cb3` (feat)

## Files Created/Modified
- `pipeline/stages/export.py` - Added _build_neighbourhood_topics(), _build_review_counts(), updated EXPECTED_ARTIFACTS to 13
- `tests/test_export_extension.py` - Structure validation tests for both new artifacts
- `backend/__init__.py` - Package marker
- `backend/config.py` - Settings dataclass with env var defaults
- `backend/loader.py` - load_artifacts() loading 8 JSON + FAISS + nid_to_name + pre-serialized GeoJSON
- `backend/schemas.py` - Pydantic v2 response models for all API endpoints
- `backend/app.py` - FastAPI app with lifespan loading, CORS wildcard, /health endpoint

## Decisions Made
- Used dataclass for Settings instead of pydantic-settings (not installed, avoids extra dependency)
- Pre-serialize GeoJSON to bytes at startup for zero-cost /geojson endpoint serving
- Build nid_to_name lookup from GeoJSON feature properties at startup (no separate file needed)
- FAISS reverse map ({nid: faiss_idx}) built at startup for O(1) similarity lookups

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Rebuilt empty SQLite database for artifact generation**
- **Found during:** Task 1
- **Issue:** data/output/yelp_philly.db was 0 bytes (empty); needed for SQL queries in _build_neighbourhood_topics and _build_review_counts
- **Fix:** Rebuilt DB by running schema creation, neighbourhood assignment, and review ingest from raw Yelp JSON files (1.13M reviews ingested)
- **Files modified:** data/output/yelp_philly.db (not tracked)
- **Verification:** Both artifacts generated with 157 neighbourhoods each
- **Committed in:** N/A (DB is gitignored runtime artifact)

**2. [Rule 3 - Blocking] Recreated broken venv and installed dependencies**
- **Found during:** Task 1
- **Issue:** .venv had broken pip and no packages installed; needed numpy, scikit-learn, bertopic, faiss-cpu, pydantic, fastapi for execution
- **Fix:** Recreated venv, installed all required packages
- **Files modified:** .venv/ (not tracked)
- **Verification:** All imports succeed
- **Committed in:** N/A (venv is gitignored)

---

**Total deviations:** 2 auto-fixed (both blocking infrastructure issues)
**Impact on plan:** No scope creep. Both fixes were required to execute the plan in this environment. Actual code changes match plan exactly.

## Issues Encountered
- DB rebuild took ~58 minutes to ingest 1.13M reviews from the 5GB Yelp review JSON file on WSL filesystem
- Two concurrent pip install processes ran for bertopic (one background, one foreground) but resolved without conflict

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Backend skeleton is ready for Plan 02 endpoint implementation
- All Pydantic response models defined for /neighbourhood/{id}, /similar/{id}, /geojson endpoints
- nid_to_name lookup available in app.state for NeighbourhoodDetail responses
- 13 pipeline artifacts validated on disk

## Self-Check: PASSED

All 9 files verified present. Both commits (62933fd, cac1cb3) confirmed in git log. Artifact structure validated (157 neighbourhoods each, correct keys).

---
*Phase: 03-backend-api*
*Completed: 2026-03-19*

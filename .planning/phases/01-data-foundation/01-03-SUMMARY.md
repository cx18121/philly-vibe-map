---
phase: 01-data-foundation
plan: "03"
subsystem: database
tags: [python, sqlite, geopandas, shapely, orjson, spatial-join, philadelphia, tdd]

# Dependency graph
requires:
  - phase: 01-data-foundation
    plan: "01"
    provides: "Philadelphia pivot decision (01-01-DECISION.md)"
  - phase: 01-data-foundation
    plan: "02"
    provides: "data/boundaries/philadelphia_neighborhoods.geojson (159 neighbourhoods, NEIGHBORHOOD_NUMBER/NEIGHBORHOOD_NAME, EPSG:4326)"

provides:
  - "scripts/02_build_schema.py: creates SQLite database with businesses and reviews tables, WAL mode, indices; build_schema() callable"
  - "scripts/03_assign_neighbourhoods.py: streams business NDJSON, Philadelphia bbox filter, GeoPandas sjoin predicate='within', INSERT OR IGNORE; assign_neighbourhoods() callable"
  - "data/output/reviews.db: SQLite database with businesses and reviews tables and indices (gitignored; re-created by running 02_build_schema.py)"
  - "scripts/build_schema.py: importable alias for 02_build_schema.py (numeric prefix workaround)"
  - "scripts/assign_neighbourhoods.py: importable alias for 03_assign_neighbourhoods.py (numeric prefix workaround)"

affects:
  - "01-04: review streaming — businesses table must be populated before FK resolution; uses business_id from businesses table"
  - "01-05: quality report — neighbourhood_id/neighbourhood_name columns populated by 03_assign_neighbourhoods.py"
  - "Phase 2+: schema is city-agnostic; neighbourhood_id = NEIGHBORHOOD_NUMBER (e.g. '044'), neighbourhood_name = display name from curation map"

# Tech tracking
tech-stack:
  added:
    - "sqlite3 (stdlib): SQLite database with WAL mode for write-once batch pipeline"
    - "GeoPandas sjoin predicate='within': Philadelphia neighbourhood assignment"
  patterns:
    - "Pattern: numeric-prefix scripts (02_xxx.py) exposed via importable alias modules (build_schema.py, assign_neighbourhoods.py)"
    - "Pattern: assign_neighbourhoods() accepts neighbourhood_gdf and curation kwargs for in-process testability without real GeoJSON"
    - "Pattern: Philadelphia PHILLY_BBOX box(-75.28, 39.87, -74.96, 40.14) as first-pass spatial filter before sjoin"
    - "Pattern: WARN_SUPPRESS_THRESHOLD=1000 prevents log flooding for missing lat/lng records"
    - "Pattern: INSERT OR IGNORE on business_id PRIMARY KEY ensures idempotent re-runs"

key-files:
  created:
    - "scripts/02_build_schema.py"
    - "scripts/03_assign_neighbourhoods.py"
    - "scripts/build_schema.py (import alias)"
    - "scripts/assign_neighbourhoods.py (import alias)"
    - "tests/test_assign_neighbourhoods.py"
  modified:
    - "tests/conftest.py (sample_business_ndjson fixture updated to Philadelphia coords)"

key-decisions:
  - "Philadelphia fields: NEIGHBORHOOD_NUMBER/NEIGHBORHOOD_NAME used as neighbourhood_id/neighbourhood_name (not NTACode/NTAName from original plan — Philadelphia pivot)"
  - "Boundary file: data/boundaries/philadelphia_neighborhoods.geojson (not nta_2020_manhattan_brooklyn.geojson from original plan)"
  - "Geographic filter: PHILLY_BBOX box(-75.28, 39.87, -74.96, 40.14) instead of NYC_BBOX — produces ~14,568 Philadelphia candidates"
  - "Import alias pattern: created scripts/build_schema.py and scripts/assign_neighbourhoods.py as thin importlib wrappers so numeric-prefix files are testable"
  - "Curation file: data/boundaries/neighborhood_name_curation.json with NEIGHBORHOOD_NUMBER keys (created in 01-02)"

patterns-established:
  - "Pattern: importlib alias wrappers for numeric-prefix script files — avoids renaming files while keeping them importable in tests"
  - "Pattern: function signature injectability — accept optional GeoDataFrame/dict kwargs to allow pure-Python unit tests without file I/O"

requirements-completed: [DATA-02, DATA-03, DATA-04, DATA-06]

# Metrics
duration: ~4min
completed: 2026-03-16
---

# Phase 01 Plan 03: SQLite Schema and Business Ingestion Summary

**SQLite schema (WAL mode, 3 indices) and Philadelphia spatial join pipeline using GeoPandas sjoin predicate='within' against 159-polygon GeoJSON with NEIGHBORHOOD_NUMBER assignment and INSERT OR IGNORE idempotency**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-16T06:57:11Z
- **Completed:** 2026-03-16T07:01:03Z
- **Tasks:** 2 of 2 (complete)
- **Files modified:** 7

## Accomplishments
- Created `scripts/02_build_schema.py` with exact DDL from plan spec: businesses and reviews tables, 3 indices, WAL+NORMAL PRAGMA, `build_schema()` callable; all `pytest tests/test_schema.py -x` tests pass
- Implemented `scripts/03_assign_neighbourhoods.py` adapted for Philadelphia pivot: PHILLY_BBOX filter, `NEIGHBORHOOD_NUMBER`/`NEIGHBORHOOD_NAME` fields, curation map lookup, `WARN_SUPPRESS_THRESHOLD=1000`, `INSERT OR IGNORE` idempotency
- TDD cycle: 4 failing tests committed first (RED: import error), then implementation (GREEN: all 4 pass)
- Added `scripts/build_schema.py` and `scripts/assign_neighbourhoods.py` as importlib alias wrappers so numeric-prefix scripts are importable in tests without renaming
- Updated `tests/conftest.py` `sample_business_ndjson` fixture to Philadelphia coordinates (Fishtown, Rittenhouse, LA)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create SQLite schema** - `52ba2f8` (feat)
2. **Task 2: Business ingestion — TDD RED (failing tests)** - `171748b` (test)
3. **Task 2: Business ingestion — TDD GREEN (implementation)** - `cf1e5ae` (feat)

**Plan metadata:** (docs commit — follows this summary)

## Files Created/Modified
- `scripts/02_build_schema.py` - SQLite schema creation with `build_schema(db_path)` function; WAL mode; businesses+reviews+3 indices
- `scripts/03_assign_neighbourhoods.py` - Business NDJSON streaming, Philadelphia bbox filter, GeoPandas sjoin predicate='within', `NEIGHBORHOOD_NUMBER` assignment, INSERT OR IGNORE; `assign_neighbourhoods(business_path, db_path, neighbourhood_gdf=None, curation=None)` function
- `scripts/build_schema.py` - importlib wrapper exposing `build_schema` from `02_build_schema.py`
- `scripts/assign_neighbourhoods.py` - importlib wrapper exposing `assign_neighbourhoods` from `03_assign_neighbourhoods.py`
- `tests/test_assign_neighbourhoods.py` - 4 TDD tests: polygon assignment, null lat skip, idempotency, CRS guard
- `tests/conftest.py` - Updated `sample_business_ndjson` fixture to Philadelphia coordinates

## Decisions Made

**Philadelphia field names throughout:** Plan spec used `NTACode`/`NTAName` (NYC-era). Script uses `NEIGHBORHOOD_NUMBER`/`NEIGHBORHOOD_NAME` (Philadelphia GeoJSON schema from 01-02). No aliasing — clean field names.

**Geographic filter: PHILLY_BBOX not city-label:** Used spatial bounding box `(-75.28, 39.87, -74.96, 40.14)` as the first-pass filter (consistent with the approach in 00_probe_coverage.py and 01-02-SUMMARY.md recommendation to filter by `city = 'Philadelphia'` OR spatial bbox). The spatial bbox is more robust against inconsistent city-label entries in the Yelp dataset.

**Import alias pattern:** Numeric-prefix scripts (`02_build_schema.py`) cannot be `import`-ed. Created thin `importlib.util` wrappers at `scripts/build_schema.py` and `scripts/assign_neighbourhoods.py`. This avoids renaming the numbered scripts (which maintain pipeline ordering convention) while making functions testable.

**Inject-able kwargs for testability:** `assign_neighbourhoods()` accepts `neighbourhood_gdf` and `curation` optional kwargs. When None, loads from disk paths. Tests pass in-memory GeoDataFrames, eliminating test dependency on committed GeoJSON file.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Philadelphia field name adaptation — plan used NTA field names**
- **Found during:** Task 2 (Business ingestion implementation)
- **Issue:** The plan spec references `NTACode`/`NTAName` and `nta_2020_manhattan_brooklyn.geojson` (NYC-era). These don't exist — the actual boundary file uses `NEIGHBORHOOD_NUMBER`/`NEIGHBORHOOD_NAME`. Using the plan as-is would produce zero spatial join matches and empty neighbourhood assignments.
- **Fix:** Used `NEIGHBORHOOD_NUMBER`/`NEIGHBORHOOD_NAME` in sjoin column selection, `data/boundaries/philadelphia_neighborhoods.geojson` as boundary path, and `PHILLY_BBOX` instead of `NYC_BBOX`. Philadelphia-appropriate log message ("Philadelphia businesses identified") kept consistent.
- **Files modified:** `scripts/03_assign_neighbourhoods.py`
- **Verification:** TDD test `test_business_inside_polygon_gets_neighbourhood_id` verifies `neighbourhood_id == '044'` (Fishtown NEIGHBORHOOD_NUMBER) after sjoin
- **Committed in:** `cf1e5ae` (Task 2 feat commit)

**2. [Rule 2 - Missing Critical] Import alias wrappers for numeric-prefix scripts**
- **Found during:** Task 2 (TDD test writing)
- **Issue:** Tests need to `from scripts.build_schema import build_schema`. Python cannot import `02_build_schema.py` by module name due to leading digit. Without an alias, all test imports would fail with `ModuleNotFoundError`.
- **Fix:** Created `scripts/build_schema.py` and `scripts/assign_neighbourhoods.py` as `importlib.util` wrappers. Added to conftest fixture.
- **Files modified:** `scripts/build_schema.py`, `scripts/assign_neighbourhoods.py`
- **Verification:** `from scripts.build_schema import build_schema` succeeds; all 4 TDD tests pass
- **Committed in:** `171748b` (Task 2 test commit)

**3. [Rule 1 - Bug] Updated sample_business_ndjson fixture to Philadelphia coordinates**
- **Found during:** Task 2 (TDD test writing)
- **Issue:** The `sample_business_ndjson` fixture in `conftest.py` had NYC coordinates (Manhattan, Brooklyn) — these would not fall inside any Philadelphia neighbourhood polygon, making fixture-based integration tests incorrect.
- **Fix:** Updated fixture to use Philadelphia coordinates: Fishtown (-75.135, 39.965), Rittenhouse (-75.175, 39.945), LA (out-of-bbox control).
- **Files modified:** `tests/conftest.py`
- **Verification:** Fixture coordinates verified inside sample_nta_gdf polygon bounds
- **Committed in:** `171748b` (Task 2 test commit)

---

**Total deviations:** 3 auto-fixed (1 bug — plan used NYC field names, 1 missing critical — import alias needed, 1 bug — fixture coordinates wrong)
**Impact on plan:** All three are direct consequences of the Philadelphia pivot decision made in 01-01. The plan was authored before the pivot; all adaptations are correctness requirements, not scope creep.

## Issues Encountered
- None beyond the Philadelphia pivot adaptations documented above.

## User Setup Required
None — all functionality is offline. When running against real Yelp data: set `YELP_DATA_DIR` to the directory containing `yelp_academic_dataset_business.json`.

## Next Phase Readiness

**01-04 (Review streaming):** UNBLOCKED. `businesses` table schema is in place. `assign_neighbourhoods()` populates `neighbourhood_id` and `neighbourhood_name`. Review ingestion script should filter by business_id FK join.

**01-05 (Quality report):** UNBLOCKED pending 01-04. `neighbourhood_id` = `NEIGHBORHOOD_NUMBER` (e.g., `'044'`), `neighbourhood_name` = curated display name from `neighborhood_name_curation.json`.

---
*Phase: 01-data-foundation*
*Completed: 2026-03-16*

---
phase: 01-data-foundation
plan: "02"
subsystem: data
tags: [python, geopandas, geojson, wgs84, philadelphia, opendata, arcgis, requests]

# Dependency graph
requires:
  - phase: 01-data-foundation
    plan: "01"
    provides: "Philadelphia pivot decision (01-01-DECISION.md); test infrastructure (conftest.py, test_boundaries.py)"

provides:
  - "scripts/01_download_boundaries.py: downloads Philadelphia neighbourhood polygons from OpenDataPhilly ArcGIS FeatureServer"
  - "data/boundaries/philadelphia_neighborhoods.geojson: committed GeoJSON artifact — 159 Philadelphia neighbourhoods, EPSG:4326"
  - "data/boundaries/neighborhood_name_curation.json: NEIGHBORHOOD_NUMBER -> display name mapping for all 159 neighbourhoods"

affects:
  - "01-03: spatial join must use data/boundaries/philadelphia_neighborhoods.geojson with NEIGHBORHOOD_NUMBER/NEIGHBORHOOD_NAME"
  - "01-04: review streaming scoped to Philadelphia businesses (neighbourhood_id from NEIGHBORHOOD_NUMBER)"
  - "01-05: quality report targets Philadelphia neighbourhood names from neighborhood_name_curation.json"
  - "Phase 2+: NTA field names are now NEIGHBORHOOD_NUMBER/NEIGHBORHOOD_NAME not NTACode/NTAName"

# Tech tracking
tech-stack:
  added:
    - "OpenDataPhilly ArcGIS FeatureServer (services1.arcgis.com/jOy9iZUXBy03ojXb) as boundary data source"
  patterns:
    - "Pattern: ArcGIS FeatureServer GeoJSON export via ?where=1%3D1&outFields=*&f=geojson query"
    - "Pattern: CRS guard after download — assert crs.to_epsg() == 4326, reprojection if needed"
    - "Pattern: Slim GeoJSON artifact — keep only essential columns (NEIGHBORHOOD_NUMBER, NEIGHBORHOOD_NAME, DISTRICT_NO, PLANNING_PARTNER, geometry)"

key-files:
  created:
    - "scripts/01_download_boundaries.py"
    - "data/boundaries/philadelphia_neighborhoods.geojson"
    - "data/boundaries/neighborhood_name_curation.json"
  modified:
    - "tests/conftest.py (sample_nta_gdf fixture updated for Philadelphia schema)"
    - "tests/test_boundaries.py (tests updated for NEIGHBORHOOD_NUMBER/NEIGHBORHOOD_NAME)"

key-decisions:
  - "Philadelphia boundary source: OpenDataPhilly ArcGIS FeatureServer (services1.arcgis.com/jOy9iZUXBy03ojXb) — original decision.md URL (opendata.arcgis.com) returned 403; ArcGIS FeatureServer direct query works without auth"
  - "Output filename: philadelphia_neighborhoods.geojson (not nta_2020_manhattan_brooklyn.geojson) — city-appropriate naming"
  - "Key fields: NEIGHBORHOOD_NUMBER (unique ID, e.g. '001') and NEIGHBORHOOD_NAME — replaces NTACode/NTAName from NYC plan"
  - "Name curation: most Philadelphia names pass through unchanged; 'Northeast Phila Airport' expanded to 'Northeast Philadelphia Airport'; hyphenated qualifiers kept for geographic disambiguation"
  - "GeoJSON slimmed to 5 columns: NEIGHBORHOOD_NUMBER, NEIGHBORHOOD_NAME, DISTRICT_NO, PLANNING_PARTNER, geometry"

patterns-established:
  - "Pattern: test conftest fixtures must match real data schema — update sample_nta_gdf when field names change"
  - "Pattern: ArcGIS FeatureServer ?f=geojson returns WGS84 by default; CRS guard still present"

requirements-completed: [DATA-04]

# Metrics
duration: ~5min
completed: 2026-03-16
---

# Phase 01 Plan 02: Philadelphia Neighbourhood Boundaries Summary

**159 Philadelphia neighbourhood polygons downloaded from OpenDataPhilly ArcGIS FeatureServer (EPSG:4326), committed as philadelphia_neighborhoods.geojson with complete NEIGHBORHOOD_NUMBER -> display name curation map**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-16T06:48:35Z
- **Completed:** 2026-03-16T06:53:14Z
- **Tasks:** 2 of 2 (complete)
- **Files modified:** 5

## Accomplishments
- Discovered and resolved the OpenDataPhilly URL from 01-01-DECISION.md returned 403; identified working ArcGIS FeatureServer endpoint that provides all 159 Philadelphia neighbourhood polygons in WGS84 without authentication
- Implemented `download_philadelphia_boundaries()` with CRS guard, column validation, and slim GeoJSON output (5 columns vs 17 raw)
- Committed `data/boundaries/philadelphia_neighborhoods.geojson` — 159 features, EPSG:4326, ready for spatial join in 01-03
- Produced `data/boundaries/neighborhood_name_curation.json` with all 159 NEIGHBORHOOD_NUMBER keys mapped to community-recognised display names
- Updated test infrastructure (conftest.py fixture and test_boundaries.py) for Philadelphia schema — all 15 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Download and filter Philadelphia boundary GeoJSON** - `c5757cc` (feat)
2. **Task 2: Produce Philadelphia neighbourhood name curation mapping** - `eb5fdf4` (feat)

**Plan metadata:** (docs commit — follows this summary)

## Files Created/Modified
- `scripts/01_download_boundaries.py` - Downloads 159 Philadelphia neighbourhood polygons from OpenDataPhilly ArcGIS FeatureServer; `download_philadelphia_boundaries(output_path)` function; CRS guard; column validation
- `data/boundaries/philadelphia_neighborhoods.geojson` - Committed GeoJSON artifact; 159 features; EPSG:4326; columns: NEIGHBORHOOD_NUMBER, NEIGHBORHOOD_NAME, DISTRICT_NO, PLANNING_PARTNER, geometry
- `data/boundaries/neighborhood_name_curation.json` - 159 NEIGHBORHOOD_NUMBER keys mapped to display names; `_generated`, `_comment`, `_source` metadata keys
- `tests/conftest.py` - Updated `sample_nta_gdf` fixture from NYC NTA schema (NTACode/NTAName/BoroCode) to Philadelphia schema (NEIGHBORHOOD_NUMBER/NEIGHBORHOOD_NAME) with Fishtown, Rittenhouse, Society Hill as sample neighbourhoods
- `tests/test_boundaries.py` - Rewrote from NYC borough-filter tests to Philadelphia neighbourhood uniqueness, column presence, string dtype, and non-empty name tests

## Decisions Made

**OpenDataPhilly source URL substitution:**
The 01-01-DECISION.md recommended URL (`opendata.arcgis.com/datasets/neighborhood_boundaries.geojson`) returned HTTP 403. Probed alternative endpoints and identified the working ArcGIS FeatureServer: `services1.arcgis.com/jOy9iZUXBy03ojXb/arcgis/rest/services/Philadelphia_Neighborhood_Boundaries/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson`. This is the same underlying dataset (PennShare philadelphia-neighborhood-boundaries), accessible without authentication via the REST API query pattern.

**Neighbourhood count: 159 vs NYC's ~85:**
Philadelphia has 159 neighbourhood polygons vs the ~85 NTAs planned for NYC. No changes needed — more granular coverage is a project benefit.

**No NTA field name aliases:**
Downstream plans (01-03+) should use `NEIGHBORHOOD_NUMBER` and `NEIGHBORHOOD_NAME` directly. No compatibility shim was added — clean break is cleaner than aliasing.

**Name curation approach:**
Philadelphia official names are largely clean single names (unlike NYC's hyphenated merges). Curation kept most names as-is. Only change: `Northeast Phila Airport` -> `Northeast Philadelphia Airport` (spell out abbreviation for display). Hyphenated names with geographic qualifiers retained (e.g., `Germantown - Morton`, `Fishtown - Lower Kensington`) to preserve disambiguation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] OpenDataPhilly URL substitution — suggested URL returned 403**
- **Found during:** Task 1 (before writing script)
- **Issue:** `opendata.arcgis.com/datasets/neighborhood_boundaries.geojson` from 01-01-DECISION.md returned HTTP 403. The URL is an ArcGIS Hub redirect that requires authentication.
- **Fix:** Probed alternative ArcGIS endpoints; identified working ArcGIS FeatureServer REST API query that returns the same Philadelphia neighbourhood dataset without auth. Updated GEOJSON_URL constant in script.
- **Files modified:** `scripts/01_download_boundaries.py` (GEOJSON_URL constant)
- **Verification:** `requests.get(URL).status_code == 200`, 159 features returned, CRS=EPSG:4326
- **Committed in:** `c5757cc` (Task 1 commit)

**2. [Rule 2 - Missing Critical] Updated test_boundaries.py and conftest fixture for Philadelphia schema**
- **Found during:** Task 1 (after downloading Philadelphia data)
- **Issue:** `tests/test_boundaries.py` checked for `NTACode`, `NTAName`, `BoroCode` — NYC-specific fields that don't exist in Philadelphia data. Running `pytest tests/test_boundaries.py` against the real downloaded file would fail.
- **Fix:** Rewrote `tests/test_boundaries.py` to verify `NEIGHBORHOOD_NUMBER` and `NEIGHBORHOOD_NAME`. Updated `sample_nta_gdf` fixture in `conftest.py` to use Philadelphia neighbourhoods and schema.
- **Files modified:** `tests/test_boundaries.py`, `tests/conftest.py`
- **Verification:** All 15 tests pass with `pytest tests/ -x -q`
- **Committed in:** `c5757cc` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 bug — broken URL, 1 missing critical — test schema mismatch)
**Impact on plan:** Both auto-fixes required for correctness. URL substitution was the primary deviation; test schema update was a necessary consequence. No scope creep.

## Issues Encountered
- ArcGIS Hub GeoJSON export URLs frequently require authentication or have broken redirect chains. The ArcGIS FeatureServer REST API query pattern (`?where=1%3D1&outFields=*&f=geojson`) is more reliable for public datasets.

## User Setup Required
None - no external service configuration required. Boundary download is fully automated.

## Next Phase Readiness

**01-03 (SQLite ingestion):** UNBLOCKED. Philadelphia neighbourhood GeoJSON committed at `data/boundaries/philadelphia_neighborhoods.geojson`. Spatial join should use `NEIGHBORHOOD_NUMBER` as `neighbourhood_id` and `NEIGHBORHOOD_NAME` as `neighbourhood_name`. Filter businesses by `city = 'Philadelphia'` (per 01-01-DECISION.md).

**01-04 (Review streaming):** UNBLOCKED pending 01-03. No changes to review streaming pattern — business-join handles Philadelphia scoping.

**01-05 (Quality report):** UNBLOCKED pending 01-03/04. Use `neighborhood_name_curation.json` for display names in the report.

---
*Phase: 01-data-foundation*
*Completed: 2026-03-16*

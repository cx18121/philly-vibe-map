---
phase: 01-data-foundation
plan: "04"
subsystem: database
tags: [python, sqlite, orjson, streaming-ndjson, batch-insert, philadelphia, tdd, wal-mode]

# Dependency graph
requires:
  - phase: 01-data-foundation
    plan: "03"
    provides: "scripts/03_assign_neighbourhoods.py populates businesses table with Philadelphia businesses; reviews table schema exists"

provides:
  - "scripts/04_ingest_reviews.py: streaming review ingest — NDJSON -> SQLite reviews table; ingest_reviews() callable"
  - "scripts/03_assign_neighbourhoods.py: updated with ingest_stats.json sidecar write (missing_lat_lng, outside_nta)"
  - "scripts/04_ingest_reviews.py: writes ingest_stats.json merging duplicate_business_id and bad_timestamp counts"

affects:
  - "01-05: quality report — ingest_stats.json sidecar enables real skip counts in Section 4 (Skipped Records Summary)"
  - "Phase 2+: reviews table populated with Philadelphia reviews; review_date stored as YYYY-MM-DD for temporal queries"

# Tech tracking
tech-stack:
  added:
    - "orjson: fast NDJSON line parsing for 8.65 GB review file (2-4x faster than stdlib json)"
  patterns:
    - "Pattern: streaming NDJSON with BATCH_SIZE=10_000 and WAL mode — memory-efficient ingest for files > 1 GB"
    - "Pattern: pre-load known_business_ids set before streaming — O(1) lookup per record for FK filtering"
    - "Pattern: INSERT OR IGNORE with review_id PRIMARY KEY — idempotent re-runs"
    - "Pattern: date_str[:10] — store YYYY-MM-DD only (strip time component from Yelp 'YYYY-MM-DD HH:MM:SS' dates)"
    - "Pattern: ingest_stats.json sidecar — 03 writes first, 04 reads and merges, 05 reads final merged file"
    - "Pattern: PROGRESS_INTERVAL=100_000 — emit log line every N written reviews (not scanned records)"

key-files:
  created:
    - "scripts/04_ingest_reviews.py"
    - "tests/test_ingest_reviews.py"
  modified:
    - "scripts/03_assign_neighbourhoods.py (ingest_stats.json sidecar write added to __main__)"
    - "scripts/00_probe_coverage.py (NYC_BBOX replaced with PHILLY_BBOX — Philadelphia pivot fix)"

key-decisions:
  - "ingest_stats.json keys: missing_lat_lng/outside_nta (from 03), duplicate_business_id/bad_timestamp (from 04) — exact keys required by 05_quality_report.py skip_counts.get()"
  - "FK filter via pre-loaded set: loading ~14,568 Philadelphia business_ids uses ~20 MB RAM, safe and O(1) per review line"
  - "Progress milestone triggered by write_count (not parse_count): matches UI-SPEC intent — track actual DB writes"

patterns-established:
  - "Pattern: ingest_stats.json sidecar chain — 03_assign_neighbourhoods writes initial stats, 04_ingest_reviews reads and merges additional stats; 05_quality_report reads final merged file"

requirements-completed: [DATA-01, DATA-03]

# Metrics
duration: ~10min
completed: 2026-03-16
---

# Phase 01 Plan 04: Review Streaming Ingest Summary

**Streaming NDJSON review ingest with Philadelphia FK filter, INSERT OR IGNORE idempotency, WAL batch writes, and ingest_stats.json sidecar chain for quality report**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-16T15:20:00Z
- **Completed:** 2026-03-16T15:31:33Z
- **Tasks:** 2 of 2 (complete)
- **Files modified:** 4

## Accomplishments

- Created `scripts/04_ingest_reviews.py` with full streaming ingest: NDJSON line-by-line parse, Philadelphia business_id FK pre-filter set, INSERT OR IGNORE batched at 10k rows, WAL mode, date truncation to YYYY-MM-DD, progress logging every 100k written reviews, and all UI-SPEC log milestones
- TDD cycle: 5 failing tests committed first (RED), then implementation (GREEN — 24/24 tests pass)
- Added ingest_stats.json sidecar write to both `03_assign_neighbourhoods.py` (missing_lat_lng, outside_nta) and `04_ingest_reviews.py` (duplicate_business_id, bad_timestamp) enabling `05_quality_report.py` Section 4 with real non-zero counts
- Fixed pre-existing test failure in `test_coverage_probe.py` caused by Philadelphia pivot (probe script still used NYC_BBOX while fixture had Philadelphia coords)

## Task Commits

Each task was committed atomically:

1. **TDD RED — failing tests + probe fix** - `f129867` (test)
2. **Task 1: Review streaming ingest script — TDD GREEN** - `d15435b` (feat)
3. **Task 2: ingest_stats.json sidecar writes** - `177902d` (feat)

**Plan metadata:** (docs commit — follows this summary)

## Files Created/Modified

- `scripts/04_ingest_reviews.py` - Streaming review ingest with `ingest_reviews(review_path, db_path)` function; BATCH_SIZE=10_000; WAL mode; known_business_ids FK filter; INSERT OR IGNORE; date_str[:10]; PROGRESS_INTERVAL=100_000; ingest_stats.json sidecar write in __main__
- `tests/test_ingest_reviews.py` - 5 TDD tests: FK filter (3 of 5 inserted), idempotency, date truncation, "Review file open" log, "Reviews written: 100,000" milestone
- `scripts/03_assign_neighbourhoods.py` - Added ingest_stats.json write after successful assign_neighbourhoods() call in __main__
- `scripts/00_probe_coverage.py` - Updated NYC_BBOX to PHILLY_BBOX following Philadelphia pivot decision

## Decisions Made

**ingest_stats.json key names:** Used exact keys that `05_quality_report.py` expects via `skip_counts.get()`: `missing_lat_lng`, `outside_nta`, `duplicate_business_id`, `bad_timestamp`. No renaming — downstream compatibility maintained.

**Progress milestone by write_count not parse_count:** The UI-SPEC says "emit every 100,000 reviews per UI-SPEC" — this means records actually written to DB, not records scanned from NDJSON. The implementation uses `written % PROGRESS_INTERVAL == 0` which correctly tracks write_count.

**FK pre-filter as in-memory set:** Loading ~14,568 Philadelphia business_ids into a Python set before streaming is safe (~20 MB RAM) and provides O(1) lookup per of the estimated millions of review lines. No SQL lookup inside the hot loop.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pre-existing probe script used NYC_BBOX after Philadelphia pivot**
- **Found during:** Pre-execution test run (before TDD)
- **Issue:** `scripts/00_probe_coverage.py` still used `NYC_BBOX = box(-74.05, 40.57, -73.70, 40.92)` after the Philadelphia pivot. The conftest fixture was updated to Philadelphia coordinates in 01-03 but the probe script was not. This caused `test_coverage_probe.py::test_probe_returns_correct_count` to fail (expected 2 Philadelphia businesses in NYC bbox = 0 matches).
- **Fix:** Replaced `NYC_BBOX` with `PHILLY_BBOX = box(-75.28, 39.87, -74.96, 40.14)` in `00_probe_coverage.py`. Updated docstring and log messages to reference Philadelphia. Key dict (`nyc_bbox_businesses`) retained for backward test compatibility.
- **Files modified:** `scripts/00_probe_coverage.py`
- **Verification:** `test_coverage_probe.py` test passes (Philadelphia coords now match PHILLY_BBOX); 19/19 pre-existing tests green before starting TDD
- **Committed in:** `f129867` (TDD RED commit)

---

**Total deviations:** 1 auto-fixed (1 bug — probe script not updated during Philadelphia pivot in 01-03)
**Impact on plan:** Required to achieve green test baseline before TDD. Directly caused by the 01-01 Philadelphia pivot decision — the 01-03 plan updated the conftest fixture but missed the probe script itself.

## Issues Encountered

None beyond the Philadelphia pivot fix documented above.

## User Setup Required

None — all functionality is offline. When running against real Yelp data: set `YELP_DATA_DIR` to the directory containing `yelp_academic_dataset_review.json` and run after `03_assign_neighbourhoods.py` has populated the businesses table.

## Next Phase Readiness

**01-05 (Quality report):** UNBLOCKED. `reviews` table schema and `04_ingest_reviews.py` are in place. After running against real Yelp data, `ingest_stats.json` will contain real skip counts for Section 4. Quality report can now run `GROUP BY neighbourhood_name, year` over the reviews + businesses join.

---
*Phase: 01-data-foundation*
*Completed: 2026-03-16*

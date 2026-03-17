---
phase: 02-nlp-pipeline
plan: 04
subsystem: nlp-pipeline
tags: [cosine-similarity, vibe-scoring, recency-weighting, temporal-drift, archetype-embeddings, sklearn]

# Dependency graph
requires:
  - phase: 02-nlp-pipeline plan 02
    provides: embeddings.npy, review_ids.npy, topic_assignments.json
  - phase: 02-nlp-pipeline plan 01
    provides: Pipeline scaffold, archetypes.json, stage stubs
  - phase: 01-data-foundation
    provides: SQLite schema with reviews and businesses tables
provides:
  - Vibe archetype scoring with recency-weighted cosine similarity (vibe_scores.json)
  - Temporal drift computation with year-bucketed equal-weight scoring (temporal_series.json)
  - Exported helpers: compute_recency_weight, compute_topic_centroids, score_neighbourhood_vibes, load_review_metadata
affects: [02-05, api-backend, visualization, frontend-map]

# Tech tracking
tech-stack:
  added: [sklearn.metrics.pairwise.cosine_similarity]
  patterns: [log-space exponential decay with min clamp, per-neighbourhood weighted topic aggregation, year-bucketed equal-weight scoring]

key-files:
  created: []
  modified:
    - pipeline/stages/vibe_score.py
    - pipeline/stages/temporal.py
    - tests/test_vibe_score.py
    - tests/test_temporal.py

key-decisions:
  - "Recency weighting uses log-space exponential decay (log_weight = -lambda * delta_days) with MIN_WEIGHT=1e-6 clamp"
  - "Temporal year buckets use equal weight per review (1.0), no recency decay within a bucket"
  - "Topic centroids computed once and reused across all neighbourhood scoring (shared helper)"
  - "TEMPORAL_MIN_REVIEWS_PER_YEAR env var configurable (default 1000) for filtering sparse years"

patterns-established:
  - "score_neighbourhood_vibes(topic_weights, topic_centroids, archetype_centroids) reusable scoring helper"
  - "load_review_metadata(db_path) returns {rowid: (date, nid)} for neighbourhood grouping"
  - "compute_topic_centroids(embeddings, review_ids, topic_assignments) builds topic centroids from raw embeddings"

requirements-completed: [NLP-03, NLP-05, NLP-06]

# Metrics
duration: 9min
completed: 2026-03-17
---

# Phase 2 Plan 04: Vibe Archetype Scoring and Temporal Drift Summary

**Cosine-similarity vibe scoring with log-space recency weighting and year-bucketed temporal drift across all neighbourhoods**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-17T18:13:54Z
- **Completed:** 2026-03-17T18:22:44Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Vibe scoring stage computes 6-dimensional archetype vectors per neighbourhood using cosine similarity between topic centroids and seed phrase embeddings, weighted by recency-decayed topic distributions
- Temporal drift stage produces per-year vibe scores for all neighbourhoods with equal weights within year buckets and configurable minimum-reviews threshold
- Extracted reusable helpers (compute_recency_weight, compute_topic_centroids, score_neighbourhood_vibes, load_review_metadata) shared between vibe_score and temporal stages
- 14 non-slow unit tests pass covering recency weight math, artifact gating, output structure, NaN checks, and neighbourhood coverage

## Task Commits

Each task was committed atomically (TDD: test -> feat):

1. **Task 1: Implement vibe archetype scoring with recency weighting (NLP-03, NLP-05)** - `c526f8a` (test) + `1e6d859` (feat)
2. **Task 2: Implement temporal drift computation (NLP-06)** - `5320f4e` (test) + `abb69d6` (feat)

_Note: TDD tasks have separate test and implementation commits._

## Files Created/Modified
- `pipeline/stages/vibe_score.py` - Full vibe scoring: archetype embedding, topic centroids, recency-weighted cosine similarity, per-neighbourhood aggregation
- `pipeline/stages/temporal.py` - Temporal drift: year-bucketed scoring with equal weights, NaN validation, configurable min-reviews threshold
- `tests/test_vibe_score.py` - 8 non-slow tests (6 recency weight unit tests + 2 integration with mock artifacts)
- `tests/test_temporal.py` - 6 non-slow tests (artifact gate, output structure, NaN check, all-neighbourhoods, equal weights, year skipping)

## Decisions Made
- Recency weighting uses log-space formula (log_weight = -lambda * delta_days) with numpy exp and 1e-6 minimum clamp, matching the plan specification exactly
- Temporal stage reads TEMPORAL_MIN_REVIEWS_PER_YEAR from env at call time (not import time) to support test overrides
- Temporal stage imports and reuses scoring helpers from vibe_score.py rather than duplicating logic
- Reference date for recency weighting is the most recent review date in the database (not system clock)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test assertions for recency weight edge cases**
- **Found during:** Task 1 (TDD GREEN phase)
- **Issue:** Test for "10 years old = clamped to 1e-6" was incorrect -- with 365-day half-life, 10 half-lives gives ~9.77e-4, well above 1e-6. Also, log-space test used hardcoded dates that didn't match assumed delta_days.
- **Fix:** Changed 10-year test to 20-year (20 half-lives, 2^-20 ~ 9.5e-7 < 1e-6 triggers clamp). Fixed log-space test to compute delta from actual dates.
- **Files modified:** tests/test_vibe_score.py
- **Committed in:** 1e6d859 (part of Task 1 feat commit)

---

**Total deviations:** 1 auto-fixed (1 bug in test assertions)
**Impact on plan:** Minor test correction for mathematical accuracy. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- vibe_scores.json and temporal_series.json artifacts ready for Plan 02-05 (FAISS index + quotes + GeoJSON export)
- Exported helpers available for any future stage that needs recency weighting or topic centroids
- All downstream stages can now consume the full artifact chain: embeddings -> topics -> vibe scores -> temporal series

---
*Phase: 02-nlp-pipeline*
*Completed: 2026-03-17*

## Self-Check: PASSED

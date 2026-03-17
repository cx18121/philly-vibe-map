---
phase: 02-nlp-pipeline
plan: 02
subsystem: nlp-pipeline
tags: [sentence-transformers, bertopic, hdbscan, umap, embeddings, topic-modeling, outlier-reduction]

# Dependency graph
requires:
  - phase: 01-data-foundation
    provides: SQLite schema (businesses + reviews tables) with neighbourhood assignments
  - phase: 02-nlp-pipeline plan 01
    provides: Pipeline scaffold, stage stubs with artifact gating, test scaffolds, conftest fixtures
provides:
  - Sentence-transformer embedding stage producing (N, 384) embeddings.npy and review_ids.npy
  - BERTopic topic modeling stage with two-strategy outlier reduction and safetensors serialization
  - topic_assignments.json mapping review IDs to topic IDs
affects: [02-03, 02-04, 02-05, api-backend, visualization]

# Tech tracking
tech-stack:
  added: []
  patterns: [chunked SQLite reading with fetchmany, pre-computed embeddings passed to BERTopic, two-strategy outlier reduction chain]

key-files:
  created: []
  modified:
    - pipeline/stages/embed.py
    - pipeline/stages/topic_model.py
    - tests/test_embed.py
    - tests/test_topic_model.py

key-decisions:
  - "Chunked SQLite reading via iter_reviews with fetchmany(50_000) for memory-efficient embedding of 1.1M reviews"
  - "BERTopic receives pre-computed embeddings to avoid re-embedding; texts loaded separately for c-TF-IDF"

patterns-established:
  - "iter_reviews(db_path, batch_size) yields batches of (rowid, text, neighbourhood_id) using fetchmany"
  - "Outlier reduction chain: c-TF-IDF first, then embeddings if rate still >50%, then update_topics"

requirements-completed: [NLP-01, NLP-02]

# Metrics
duration: 9min
completed: 2026-03-17
---

# Phase 2 Plan 02: Embedding and Topic Modeling Summary

**Sentence-transformer embedding of all reviews into 384D vectors with BERTopic topic discovery using HDBSCAN/UMAP and two-strategy outlier reduction chain**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-17T17:52:38Z
- **Completed:** 2026-03-17T18:01:38Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Embedding stage reads reviews from SQLite in 50K-row chunks, encodes with all-MiniLM-L6-v2 in configurable batches, saves embeddings.npy (N, 384) float32 and review_ids.npy (N,) int64
- BERTopic topic modeling loads pre-computed embeddings, fits with tuned HDBSCAN (min_cluster_size=10, min_samples=3) and UMAP (5D, cosine), applies c-TF-IDF then embeddings outlier reduction, saves model with safetensors and topic_assignments.json
- Both stages are idempotent via artifact gating (skip if output exists, force=True regenerates)
- 12 non-slow unit tests pass using mocked SentenceTransformer and BERTopic

## Task Commits

Each task was committed atomically (TDD: test -> feat):

1. **Task 1: Implement embedding stage (NLP-01)** - `3850686` (test) + `7684e98` (feat)
2. **Task 2: Implement BERTopic topic modeling stage (NLP-02)** - `86f969e` (test) + `796fad2` (feat)

_Note: TDD tasks have separate test and implementation commits._

## Files Created/Modified
- `pipeline/stages/embed.py` - Full embedding stage: chunked SQLite reader, SentenceTransformer encoding, artifact saving
- `pipeline/stages/topic_model.py` - Full BERTopic stage: pre-computed embeddings, HDBSCAN/UMAP config, outlier reduction chain, safetensors save
- `tests/test_embed.py` - 8 tests (6 non-slow with mocked model, 2 slow integration)
- `tests/test_topic_model.py` - 10 tests (6 non-slow with mocked BERTopic, 4 slow integration)

## Decisions Made
- Chunked SQLite reading via `iter_reviews` with `cursor.fetchmany(50_000)` instead of loading all rows into memory -- required for 1.1M reviews
- BERTopic receives pre-computed embeddings via `embeddings=` parameter to avoid re-embedding; review texts loaded separately via same ORDER BY query for c-TF-IDF alignment
- Used `datetime.datetime.now(datetime.UTC)` instead of deprecated `datetime.datetime.utcnow()` for Python 3.12 compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing bertopic, hdbscan, umap-learn packages**
- **Found during:** Task 2 (BERTopic stage implementation)
- **Issue:** bertopic, hdbscan, and umap-learn not installed in system Python despite being in requirements-nlp.txt
- **Fix:** Installed via pip install --break-system-packages
- **Files modified:** None (system packages only)
- **Verification:** `python3 -c "import bertopic, hdbscan, umap"` succeeds
- **Committed in:** N/A (runtime dependency, not code)

**2. [Rule 1 - Bug] Fixed deprecated datetime.utcnow() call**
- **Found during:** Task 1 (embed stage implementation)
- **Issue:** Stub used `datetime.datetime.utcnow()` which is deprecated in Python 3.12
- **Fix:** Changed to `datetime.datetime.now(datetime.UTC)` in both embed.py and topic_model.py
- **Files modified:** pipeline/stages/embed.py, pipeline/stages/topic_model.py
- **Committed in:** 7684e98, 796fad2

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Minor fixes for runtime compatibility. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Embedding and topic model artifacts ready for Plan 02-03 (vibe scoring)
- embeddings.npy, review_ids.npy, bertopic_model/, topic_assignments.json will be produced when pipeline runs against real data
- All downstream stages (vibe_score, temporal, export) can now consume these artifacts

---
*Phase: 02-nlp-pipeline*
*Completed: 2026-03-17*

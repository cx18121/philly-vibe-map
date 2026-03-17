---
phase: 02-nlp-pipeline
plan: 01
subsystem: nlp-pipeline
tags: [bertopic, sentence-transformers, faiss, lora, peft, pytest, pipeline-architecture]

# Dependency graph
requires:
  - phase: 01-data-foundation
    provides: SQLite schema (businesses + reviews tables), Philadelphia neighbourhood boundaries
provides:
  - Pipeline orchestrator with 6-stage architecture and CLI interface
  - 6 stage modules with consistent interface (artifact gating, _log pattern)
  - Archetype seed phrases for 6 vibe dimensions
  - Wave 0 test scaffolds covering NLP-01 through NLP-09 (25 tests)
  - Shared test fixtures for mock DB, embeddings, and artifacts
  - NLP dependency manifest (requirements-nlp.txt)
affects: [02-02, 02-03, 02-04, 02-05, api-backend, visualization]

# Tech tracking
tech-stack:
  added: [sentence-transformers 5.3.0, bertopic 0.17.4, peft 0.18.1, faiss-cpu 1.13.2, hdbscan 0.8.41, umap-learn, datasets, accelerate, safetensors]
  patterns: [stage-based pipeline with artifact gating, consistent _log pattern, orchestrator with --force/--force-stage CLI, @pytest.mark.slow for ML tests]

key-files:
  created:
    - pipeline/__init__.py
    - pipeline/stages/__init__.py
    - pipeline/stages/embed.py
    - pipeline/stages/topic_model.py
    - pipeline/stages/vibe_score.py
    - pipeline/stages/sentiment.py
    - pipeline/stages/temporal.py
    - pipeline/stages/export.py
    - pipeline/archetypes.json
    - pipeline/PIPELINE_DECISIONS.md
    - scripts/06_run_nlp_pipeline.py
    - requirements-nlp.txt
    - tests/test_embed.py
    - tests/test_topic_model.py
    - tests/test_vibe_score.py
    - tests/test_sentiment.py
    - tests/test_temporal.py
    - tests/test_faiss_index.py
    - tests/test_quotes.py
    - tests/test_artifacts.py
  modified:
    - tests/conftest.py
    - pytest.ini

key-decisions:
  - "Stage modules use consistent interface: run_<stage>(db_path, artifacts_dir, force) -> dict with artifact gating"
  - "Registered pytest.mark.slow marker for ML tests requiring full pipeline execution"

patterns-established:
  - "Pipeline stage interface: run_<stage>(db_path: str, artifacts_dir: Path, force: bool = False) -> dict"
  - "Artifact gating: check output exists before running, skip with {skipped: True}"
  - "Orchestrator catches NotImplementedError for stub stages and continues"

requirements-completed: [NLP-09]

# Metrics
duration: 5min
completed: 2026-03-17
---

# Phase 2 Plan 01: Pipeline Scaffold Summary

**6-stage NLP pipeline skeleton with orchestrator CLI, archetype config, and 25 Wave 0 test scaffolds covering all NLP requirements**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-17T17:44:42Z
- **Completed:** 2026-03-17T17:49:33Z
- **Tasks:** 2
- **Files modified:** 22

## Accomplishments
- Pipeline project structure with 6 stage modules (embed, topic_model, vibe_score, sentiment, temporal, export), all importable with consistent interfaces and artifact gating
- Orchestrator script with --db, --artifacts-dir, --force, --force-stage CLI flags, sequential stage execution, error handling
- Archetype seed phrases config (artsy, foodie, nightlife, family, upscale, cultural) in JSON format
- 25 test functions across 8 test files covering NLP-01 through NLP-09, with shared conftest fixtures (mock DB with 90 reviews, mock embeddings, mock artifacts dir)
- PIPELINE_DECISIONS.md documenting BERTopic/LoRA/FAISS/Philadelphia rationale for portfolio

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pipeline structure, orchestrator, archetype config, and NLP dependencies** - `7ef46c8` (feat)
2. **Task 2: Create Wave 0 test scaffolds and shared fixtures** - `880a41c` (test)

## Files Created/Modified
- `pipeline/__init__.py` - Package init with NLP pipeline docstring
- `pipeline/stages/__init__.py` - Exports all 6 stage functions
- `pipeline/stages/embed.py` - Embedding stage stub with artifact gating
- `pipeline/stages/topic_model.py` - BERTopic stage stub with artifact gating
- `pipeline/stages/vibe_score.py` - Vibe scoring stage stub with artifact gating
- `pipeline/stages/sentiment.py` - Sentiment fine-tuning stage stub with artifact gating
- `pipeline/stages/temporal.py` - Temporal drift stage stub with artifact gating
- `pipeline/stages/export.py` - Export stage stub (FAISS, quotes, GeoJSON) with artifact gating
- `pipeline/archetypes.json` - 6 vibe dimensions with 7-8 seed phrases each
- `pipeline/PIPELINE_DECISIONS.md` - Technical rationale for resume/interviews
- `scripts/06_run_nlp_pipeline.py` - Pipeline orchestrator entry point
- `requirements-nlp.txt` - Pinned NLP dependencies
- `tests/conftest.py` - Extended with Phase 2 NLP fixtures
- `tests/test_embed.py` - NLP-01 tests (shape, alignment, skip)
- `tests/test_topic_model.py` - NLP-02 tests (topic count, outlier rate, save, JSON format)
- `tests/test_vibe_score.py` - NLP-03/05 tests (6 dimensions, variation, recency weighting)
- `tests/test_sentiment.py` - NLP-04 tests (LoRA config, 3-class output, model loadability)
- `tests/test_temporal.py` - NLP-06 tests (structure, no NaN, all neighbourhoods)
- `tests/test_faiss_index.py` - NLP-07 tests (k results, latency, ID map)
- `tests/test_quotes.py` - NLP-08 tests (count, length, all archetypes)
- `tests/test_artifacts.py` - NLP-09 tests (existence, loadability)
- `pytest.ini` - Added slow marker registration

## Decisions Made
- Stage modules use a consistent function signature: `run_<stage>(db_path: str, artifacts_dir: Path, force: bool = False) -> dict`
- Orchestrator catches `NotImplementedError` from stub stages and continues (logs warning instead of failing), so it can be run even before implementation
- Registered `@pytest.mark.slow` in pytest.ini so slow ML tests can be selectively skipped during development
- Mock DB fixture uses 3 Philadelphia neighbourhoods (044, 116, 121) with 90 reviews (30 per business, 10 per year across 2019-2021) for realistic but fast test data

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Registered pytest.mark.slow marker**
- **Found during:** Task 2 (test scaffold creation)
- **Issue:** pytest.ini did not register the `slow` custom marker, causing warnings on all slow-marked tests
- **Fix:** Added `markers = slow: marks tests as slow` to pytest.ini
- **Files modified:** pytest.ini
- **Verification:** pytest --collect-only runs without marker warnings
- **Committed in:** 880a41c (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Minor config fix for clean test output. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Pipeline skeleton ready for Plan 02-02 (embedding implementation)
- All stage interfaces defined; subsequent plans implement one stage each
- Test scaffolds define acceptance criteria that must pass when stages are implemented
- Archetype config ready for vibe scoring stage

## Self-Check: PASSED

- All 20 created files verified present on disk
- Commit 7ef46c8 (Task 1) verified in git log
- Commit 880a41c (Task 2) verified in git log

---
*Phase: 02-nlp-pipeline*
*Completed: 2026-03-17*

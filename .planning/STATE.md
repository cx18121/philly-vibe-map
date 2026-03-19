---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 03-02-PLAN.md
last_updated: "2026-03-19T20:23:00.000Z"
progress:
  total_phases: 6
  completed_phases: 3
  total_plans: 12
  completed_plans: 12
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-16)

**Core value:** An interactive map where anyone can feel the character of a New York City neighbourhood through its reviews -- and watch how that character has shifted year by year from 2019 to 2025.
**Current focus:** Phase 03 — backend-api

## Current Position

Phase: 03 (backend-api) — COMPLETE
Plan: 2 of 2 (DONE)

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01-data-foundation P01 | 3min | 2 tasks | 14 files |
| Phase 01-data-foundation P02 | 5min | 2 tasks | 5 files |
| Phase 01-data-foundation P03 | 4min | 2 tasks | 7 files |
| Phase 01-data-foundation P04 | 10min | 2 tasks | 4 files |
| Phase 01-data-foundation P05 | 5min | 1 tasks | 3 files |
| Phase 02-nlp-pipeline P01 | 5min | 2 tasks | 22 files |
| Phase 02-nlp-pipeline P02 | 9min | 2 tasks | 4 files |
| Phase 02-nlp-pipeline P03 | 6min | 1 tasks | 2 files |
| Phase 02-nlp-pipeline P04 | 9min | 2 tasks | 4 files |
| Phase 02-nlp-pipeline P05 | 12min | 2 tasks | 5 files |
| Phase 03-backend-api P01 | 87min | 2 tasks | 7 files |
| Phase 03-backend-api P02 | 3min | 2 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: 6 phases derived from requirement categories (DATA, NLP, API, MAP, VIZ, DEPLOY) with strict linear dependencies
- [Phase 01-data-foundation]: probe_coverage() uses shapely box NYC_BBOX for geographic filtering not city-label matching; all plans 01-02 through 01-05 blocked on user dataset decision (option-a/b/c/d)
- [Phase 01-data-foundation 01-01]: DATASET DECISION RESOLVED — option-c Philadelphia selected; Yelp NYC coverage <500 businesses; Philadelphia has ~14,568; boundary source = OpenDataPhilly; ALL plans 01-02 through 01-05 retargeted to Philadelphia, PA
- [Phase 01-data-foundation 01-02]: Philadelphia boundaries committed — 159 neighbourhoods from ArcGIS FeatureServer (opendata.arcgis.com URL returned 403; services1.arcgis.com/jOy9iZUXBy03ojXb works without auth); key fields: NEIGHBORHOOD_NUMBER (ID), NEIGHBORHOOD_NAME; test schema updated for Philadelphia
- [Phase 01-data-foundation]: Philadelphia fields: NEIGHBORHOOD_NUMBER/NEIGHBORHOOD_NAME used as neighbourhood_id/neighbourhood_name (not NTACode/NTAName from original plan); sjoin uses philadelphia_neighborhoods.geojson with PHILLY_BBOX
- [Phase 01-data-foundation]: Import alias pattern: scripts/build_schema.py and scripts/assign_neighbourhoods.py are importlib wrappers for numeric-prefix files; enables test imports without renaming pipeline scripts
- [Phase 01-data-foundation 01-04]: ingest_stats.json sidecar chain: 03_assign_neighbourhoods writes missing_lat_lng/outside_nta; 04_ingest_reviews merges duplicate_business_id/bad_timestamp; 05_quality_report reads merged file for Section 4
- [Phase 01-data-foundation 01-04]: FK filter via pre-loaded known_business_ids set: ~14,568 Philadelphia IDs loaded before streaming; O(1) per-review lookup during hot loop
- [Phase 01-data-foundation]: quality_report.md committed at empty-DB state (NOT READY) — correctly reflects pipeline must be run against real Yelp data before Phase 2 gate can pass
- [Phase 01-data-foundation]: Borough column shows Unknown for Philadelphia NEIGHBORHOOD_NUMBER codes — retained per UI-SPEC but not meaningful for Philadelphia data
- [Phase 02-nlp-pipeline 02-01]: Stage modules use consistent interface: run_<stage>(db_path, artifacts_dir, force) -> dict with artifact gating
- [Phase 02-nlp-pipeline 02-01]: Registered pytest.mark.slow marker for ML tests requiring full pipeline execution
- [Phase 02-nlp-pipeline 02-02]: Chunked SQLite reading via iter_reviews with fetchmany(50_000) for memory-efficient embedding of 1.1M reviews
- [Phase 02-nlp-pipeline 02-02]: BERTopic receives pre-computed embeddings to avoid re-embedding; texts loaded separately for c-TF-IDF alignment
- [Phase 02-nlp-pipeline]: WeightedTrainer with CrossEntropyLoss for class-balanced sentiment training; CPU fallback auto-limits to 500K samples
- [Phase 02-nlp-pipeline 02-04]: Recency weighting uses log-space exponential decay (log_weight = -lambda * delta_days) with 1e-6 min clamp; temporal year buckets use equal weight per review
- [Phase 02-nlp-pipeline 02-04]: Exported reusable helpers (compute_recency_weight, compute_topic_centroids, score_neighbourhood_vibes) for cross-stage sharing
- [Phase 02-nlp-pipeline 02-05]: FAISS IndexFlatIP with L2 normalization for cosine similarity over 6D vibe vectors; quote selection via cosine similarity between review embeddings and archetype centroids
- [Phase 02-nlp-pipeline 02-05]: GeoJSON enrichment keyed on NEIGHBORHOOD_NUMBER; 11-artifact validation gate as final pipeline step
- [Phase 03-backend-api 03-01]: Dataclass Settings instead of pydantic-settings; pre-serialized GeoJSON bytes for zero-cost serving; nid_to_name built from GeoJSON features at startup; FAISS reverse map for O(1) lookups; 13 total artifacts after adding neighbourhood_topics.json and review_counts.json
- [Phase 03-backend-api 03-02]: Module-scoped TestClient fixture with context manager for Starlette 0.52+ lifespan; ARCHETYPE_ORDER constant for FAISS query vector construction; nid.zfill(3) zero-padding pattern across all endpoints

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 1: Google Places API $200 monthly credit no longer exists (March 2025 pricing overhaul). Yelp Open Dataset may be primary source. Needs validation during Phase 1 planning.
- Phase 2: BERTopic produces 40-75% outliers on short review text without careful HDBSCAN tuning. Quality gates required.

## Session Continuity

Last session: 2026-03-19T20:23:00Z
Stopped at: Completed 03-02-PLAN.md (Phase 03 complete)
Resume file: .planning/phases/04-map-frontend/04-01-PLAN.md

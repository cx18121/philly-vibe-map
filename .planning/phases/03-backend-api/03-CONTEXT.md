# Phase 3: Backend API - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

A lightweight FastAPI server that loads pre-computed artifacts at startup and serves 4 endpoints (enriched GeoJSON, per-neighbourhood detail, temporal drift, FAISS similarity) with zero ML inference and sub-100ms responses. This phase also extends the Phase 2 pipeline export stage to produce two additional artifacts the backend needs.

</domain>

<decisions>
## Implementation Decisions

### Artifact scope
- Backend is **pure artifact-only** — zero SQLite dependency at runtime
- API-02 requires topic breakdown and review count, which are not in current artifacts; these will be added to `pipeline/stages/export.py` (existing export stage, not a new stage) as two new artifacts:
  - `neighbourhood_topics.json` — per-neighbourhood topic breakdown (top N topics with keywords + review share)
  - `review_counts.json` — per-neighbourhood total review count
- Backend loads all serving artifacts into memory at startup via FastAPI lifespan event (API-05)
- Raw embeddings (`embeddings.npy`) and `review_ids.npy` are **not** loaded — those are pipeline-only artifacts

### API-02 response shape
- `GET /neighbourhoods/{id}` returns:
  - Vibe archetype scores (all 6 dimensions)
  - Dominant vibe + dominant vibe score
  - Top **10** topics with: human-readable label (BERTopic keywords joined), keyword list, and `review_share` (fraction of neighbourhood reviews in that topic)
  - Representative quotes (all archetypes, from `representative_quotes.json`)
  - Total review count for the neighbourhood
- Topics formatted as: `[{"label": "brunch spots", "keywords": ["eggs", "mimosa", "wait"], "review_share": 0.18}, ...]`

### API-01 (GeoJSON endpoint)
- `GET /neighbourhoods` returns the enriched GeoJSON FeatureCollection directly from `enriched_geojson.geojson`
- Content-Type header: `application/geo+json`

### CORS
- Allow `*` (wildcard) for now — unblocks Phase 4 frontend development immediately
- Will be locked to specific origins in Phase 6 (deployment), configured via env var

### Deployment readiness
- Artifact directory configured via `ARTIFACTS_DIR` environment variable (default: `data/output/artifacts`)
- A `Dockerfile` is part of this phase's deliverables — Phase 6 just sets env vars, no structural changes needed
- `GET /health` endpoint included: returns `{"status": "ok", "artifacts_loaded": true/false}` — used for Railway/Render readiness checks

### Claude's Discretion
- Exact FastAPI app structure (router organization, module layout under `api/` or `backend/`)
- Uvicorn startup config (port, workers, reload flag)
- Response model / Pydantic schema design
- Error handling for invalid neighbourhood IDs (404 shape)
- FAISS k parameter validation (clamp to neighbourhood count)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — API-01 through API-06 define all acceptance criteria for this phase (sub-100ms, lifespan loading, 4 endpoints)
- `.planning/PROJECT.md` — Static artifacts constraint (never recompute on live request), resume/portfolio priority

### Artifact formats (what the backend loads)
- `data/output/artifacts/enriched_geojson.geojson` — GeoJSON FeatureCollection; properties include `NEIGHBORHOOD_NUMBER`, `NEIGHBORHOOD_NAME`, `vibe_scores`, `dominant_vibe`, `dominant_vibe_score`
- `data/output/artifacts/temporal_series.json` — `{neighbourhood_id: {year: {archetype: score}}}` — covers years present in data (2007–2022 from actual Yelp data, not 2019–2025 as originally planned)
- `data/output/artifacts/representative_quotes.json` — `{neighbourhood_id: {archetype: [quote, ...]}}`  — 5 quotes per archetype, truncated to 300 chars
- `data/output/artifacts/faiss_index.bin` — FAISS IndexFlatIP over 6D vibe vectors, L2-normalised
- `data/output/artifacts/faiss_id_map.json` — `{"0": "001", "1": "002", ...}` maps FAISS integer IDs → neighbourhood IDs
- `data/output/artifacts/vibe_scores.json` — `{neighbourhood_id: {archetype: score}}`
- `data/output/artifacts/neighbourhood_topics.json` — **NEW artifact** (to be added to export stage)
- `data/output/artifacts/review_counts.json` — **NEW artifact** (to be added to export stage)

### Pipeline export stage (to be extended)
- `pipeline/stages/export.py` — Current export stage; extend to produce `neighbourhood_topics.json` and `review_counts.json`
- `pipeline/stages/topic_model.py` — Topic model stage; source for topic assignments and BERTopic keywords
- `data/output/artifacts/topic_assignments.json` — `{review_id: topic_id}` — used to compute per-neighbourhood topic distributions

### Prior phase context
- `.planning/phases/02-nlp-pipeline/02-CONTEXT.md` — Artifact format decisions, FAISS IndexFlatIP details, Philadelphia neighbourhood IDs

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_log(level, msg)` pattern (all pipeline scripts): timestamped stdout logging — replicate in backend startup/lifespan
- `argparse` CLI pattern with env-var-style flags: follow same pattern for backend config

### Established Patterns
- **Idempotency / artifact-gating**: Phase 2 checks artifact existence before re-running stages — extend export stage with the same check for two new artifacts
- **JSON format**: `indent=2` for human readability and git diff-ability — follow for new artifacts
- **No pickle / no HDF5**: JSON + numpy + binary FAISS — backend stays within this dependency surface

### Integration Points
- Backend reads from `data/output/artifacts/` (all serving artifacts loaded into memory at startup)
- Backend does **not** read `data/output/reviews.db` — that's pipeline-only
- Frontend (Phase 4) calls this API over HTTP; CORS wildcard enables dev without coordination
- Phase 6 (deployment) consumes the Dockerfile produced here; sets `ARTIFACTS_DIR` env var pointing to artifact location on the server

</code_context>

<specifics>
## Specific Ideas

- No specific references — open to standard FastAPI patterns
- The two new artifacts (`neighbourhood_topics.json`, `review_counts.json`) should follow the same JSON structure pattern as existing artifacts (indent=2, neighbourhood_id as top-level keys)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-backend-api*
*Context gathered: 2026-03-19*

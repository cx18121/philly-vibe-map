# Roadmap: Neighbourhood Vibe Mapper -- Philadelphia

## Overview

This project delivers an interactive map of Philadelphia neighbourhood vibes derived from business reviews via a deep NLP pipeline. **City pivot (2026-03-16):** Yelp Open Dataset does not cover NYC; Philadelphia selected (option-c) with ~14,568 businesses. See 01-01-DECISION.md. The work flows linearly: collect and validate review data, run the full ML pipeline to produce pre-computed artifacts, stand up a thin serving API, build the core interactive map, layer on temporal animation and visual polish, then deploy to a public URL. Each phase produces artifacts consumed by subsequent phases -- data feeds the pipeline, the pipeline feeds the API, the API feeds the frontend.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Data Foundation** - Collect 50k+ reviews, fetch NYC boundary GeoJSON, validate temporal coverage (completed 2026-03-16)
- [x] **Phase 2: NLP Pipeline** - Embed reviews, discover topics, score vibes, build FAISS index, export all artifacts (completed 2026-03-19)
- [x] **Phase 3: Backend API** - Serve pre-computed artifacts through 4 FastAPI endpoints with sub-100ms responses (completed 2026-03-19)
- [x] **Phase 4: Core Map** - Render interactive choropleth with hover, click-to-detail sidebar, legend, and responsive layout (completed 2026-03-21)
- [ ] **Phase 5: Temporal Animation and Polish** - Add time slider with year-by-year animation, glow effects, and sidebar transitions
- [ ] **Phase 6: Deployment and Sharing** - Deploy to public URLs with shareable deep links

## Phase Details

### Phase 1: Data Foundation
**Goal**: A validated, queryable corpus of Philadelphia reviews spanning 2019-2025 with correct neighbourhood boundaries ready for NLP processing — ~14,568 Philadelphia businesses confirmed in Yelp dataset (NYC not covered; pivot recorded in 01-01-DECISION.md)
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06
**Success Criteria** (what must be TRUE):
  1. Running a count query against the SQLite database returns reviews distributed across Manhattan and Brooklyn neighbourhoods
  2. The data quality report shows every neighbourhood has reviews in at least 5 of the 7 years (2019-2025), with no neighbourhood having fewer than 500 total reviews
  3. Boundary GeoJSON loads in a map tool (e.g., geojson.io) and displays distinct neighbourhood polygons covering Manhattan and Brooklyn in WGS84 projection
  4. Every stored review has all required fields populated: text, timestamp, business name, lat/lng, source platform, and neighbourhood assignment
  5. Quality report Phase 2 readiness verdict is READY FOR PHASE 2
**Plans**: 5 plans

Plans:
- [x] 01-01-PLAN.md — Coverage probe + pytest test scaffold + dataset decision gate (COMPLETE: Philadelphia pivot, option-c)
- [x] 01-02-PLAN.md — Philadelphia neighbourhood boundary download (OpenDataPhilly) + neighbourhood name curation mapping (COMPLETE: 159 neighbourhoods, EPSG:4326, NEIGHBORHOOD_NUMBER/NEIGHBORHOOD_NAME schema)
- [x] 01-03-PLAN.md — SQLite schema + business ingestion with city=Philadelphia filter (COMPLETE: businesses table populated with ~14,568 Philadelphia businesses)
- [x] 01-04-PLAN.md — Review streaming ingest (NDJSON → reviews table) (COMPLETE: ingest_reviews() with FK filter, INSERT OR IGNORE, WAL mode, ingest_stats.json sidecar)
- [x] 01-05-PLAN.md — Quality report generation + Phase 2 readiness human verification

### Phase 2: NLP Pipeline
**Goal**: All ML computation complete -- embeddings, topics, vibe scores, sentiment, temporal drift, FAISS index, and representative quotes exported as serialized artifacts
**Depends on**: Phase 1
**Requirements**: NLP-01, NLP-02, NLP-03, NLP-04, NLP-05, NLP-06, NLP-07, NLP-08, NLP-09
**Success Criteria** (what must be TRUE):
  1. Each neighbourhood has a 6-dimensional vibe vector (artsy, foodie, nightlife, family, upscale, cultural) with scores that vary meaningfully across neighbourhoods (not uniform)
  2. BERTopic produces at least 20 distinct topics with fewer than 50% outlier reviews after outlier reduction, and topics are human-interpretable when inspected
  3. Temporal drift data exists for all 30 neighbourhoods across all years (2019-2025), showing at least some neighbourhoods with measurable vibe shifts over time
  4. FAISS nearest-neighbour query for any neighbourhood returns k similar neighbourhoods in under 10ms, and the results are intuitively plausible (e.g., SoHo similar to West Village, not East Harlem)
  5. Artifact export directory contains all required files (embeddings, vibe scores, temporal series, FAISS index, representative quotes, enriched GeoJSON) and each loads without error
**Plans**: 5 plans

Plans:
- [x] 02-01-PLAN.md — Pipeline structure, archetype config, orchestrator skeleton, and Wave 0 test scaffolds
- [x] 02-02-PLAN.md — Sentence-transformer embedding (NLP-01) and BERTopic topic modeling (NLP-02)
- [x] 02-03-PLAN.md — LoRA fine-tuned DistilBERT sentiment classifier (NLP-04)
- [x] 02-04-PLAN.md — Vibe archetype scoring with recency weighting (NLP-03, NLP-05) and temporal drift (NLP-06)
- [x] 02-05-PLAN.md — FAISS index, representative quotes, enriched GeoJSON export, and pipeline quality verification (NLP-07, NLP-08, NLP-09)

### Phase 3: Backend API
**Goal**: A lightweight FastAPI server that loads pre-computed artifacts at startup and serves neighbourhood data, temporal series, and similarity queries with zero ML inference
**Depends on**: Phase 2
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06
**Success Criteria** (what must be TRUE):
  1. `GET /neighbourhoods` returns valid GeoJSON FeatureCollection with 30 features, each containing vibe scores and dominant vibe in properties
  2. `GET /neighbourhoods/{id}` returns topic breakdown, vibe scores, representative quotes, and review count for any valid neighbourhood ID
  3. `GET /temporal` returns a JSON payload containing vibe vectors for all 30 neighbourhoods across all 7 years, suitable for client-side time-slider scrubbing
  4. `GET /similar?id={id}&k=5` returns 5 nearest-neighbour neighbourhoods via FAISS, and all 4 endpoints respond in under 100ms measured by automated test
  5. Server starts up and begins serving within 10 seconds, loading all artifacts via FastAPI lifespan event with no ML model dependencies
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md — Export extension (neighbourhood_topics.json, review_counts.json) + backend module skeleton (config, loader, schemas, lifespan app)
- [x] 03-02-PLAN.md — All 4 data endpoints, integration tests, Dockerfile, and sub-100ms response verification

### Phase 4: Core Map
**Goal**: A functional interactive choropleth map where users can explore neighbourhood vibes through hover, click, and visual cues
**Depends on**: Phase 3
**Requirements**: MAP-01, MAP-02, MAP-03, MAP-04, MAP-05, MAP-06, MAP-07, MAP-08, MAP-09
**Success Criteria** (what must be TRUE):
  1. Opening the app shows a dark basemap with 30 coloured neighbourhood polygons, each filled with a semi-transparent colour representing its dominant vibe archetype
  2. Hovering any neighbourhood displays a tooltip showing the neighbourhood name and dominant vibe; clicking opens a sidebar with animated vibe bars, topic list, sentiment pills, and representative quotes
  3. A legend is visible explaining all 6 vibe archetype colours, and the colour palette passes colourblind accessibility simulation
  4. On mobile viewports (under 768px), the sidebar renders as a bottom sheet instead of a side panel
  5. A user can tab through neighbourhoods with keyboard, press enter to select, and press escape to dismiss the sidebar
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — Vite project scaffold, dependencies, TypeScript/Vitest config, foundational modules (types, colours, store, API hooks, skeleton)
- [x] 04-02-PLAN.md — MapLibre choropleth with fill/outline layers, hover tooltip, click handler, and colour legend
- [x] 04-03-PLAN.md — Detail sidebar/bottom-sheet with vibe bars, topics, sentiment pills, quotes, keyboard navigation, and human verification

### Phase 5: Temporal Animation and Polish
**Goal**: The map comes alive with year-by-year vibe transitions and visual effects that make this a portfolio-stopping piece of interactive data art
**Depends on**: Phase 4
**Requirements**: VIZ-01, VIZ-02, VIZ-03, VIZ-04, VIZ-05, VIZ-06
**Success Criteria** (what must be TRUE):
  1. Dragging the time slider between 2019 and 2025 causes neighbourhood fill colours to transition smoothly (interpolated, not hard-cut) reflecting vibe changes per year
  2. Pressing play on the time slider auto-advances through years with visible colour transitions, and pause stops the animation at the current year
  3. Hovering a neighbourhood produces a visible pulse or glow effect, and dominant-vibe fills have a subtle ambient glow that intensifies on hover
  4. Selecting a neighbourhood triggers Framer Motion animations on sidebar content -- bars, pills, and quotes animate in rather than appearing instantly
**Plans**: 2 plans

Plans:
- [ ] 05-01-PLAN.md — Types, store extension, temporal data hook, colour interpolation, TimeSlider component with play/pause
- [ ] 05-02-PLAN.md — VibeMap temporal colour updates, highlight/glow layers, DetailPanel stagger animations, and visual verification

### Phase 6: Deployment and Sharing
**Goal**: The complete app is live at a public URL where anyone can explore NYC neighbourhood vibes and share specific views via link
**Depends on**: Phase 5
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03
**Success Criteria** (what must be TRUE):
  1. Visiting the public frontend URL loads the full interactive map without requiring login or authentication
  2. The backend is deployed to a public URL and the frontend successfully fetches all data from it (no CORS errors, no failed requests)
  3. Selecting a neighbourhood and year updates the URL; copying and pasting that URL into a new browser tab restores the exact same view (selected neighbourhood and year)
**Plans**: TBD

Plans:
- [ ] 06-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation (Philadelphia) | 5/5 | Complete   | 2026-03-16 |
| 2. NLP Pipeline | 5/5 | Complete   | 2026-03-19 |
| 3. Backend API | 2/2 | Complete   | 2026-03-19 |
| 4. Core Map | 3/3 | Complete   | 2026-03-21 |
| 5. Temporal Animation and Polish | 0/2 | In Progress | - |
| 6. Deployment and Sharing | 0/? | Not started | - |

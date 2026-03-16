# Project Research Summary

**Project:** Neighbourhood Vibe Mapper -- New York City
**Domain:** NLP-powered geospatial visualization (pre-computed ML pipeline + interactive map)
**Researched:** 2026-03-16
**Confidence:** HIGH

## Executive Summary

The Neighbourhood Vibe Mapper is an NLP-powered interactive choropleth map that assigns "vibe archetypes" (artsy, foodie, nightlife, family, upscale, cultural) to NYC neighbourhoods based on analysis of ~50k business reviews. The expert approach for this class of product is an **offline/online split**: run all ML computation (embeddings, topic modelling, sentiment, similarity indexing) offline on a local GPU, export pre-computed artifacts, and serve them through a lightweight read-only API. The frontend renders an interactive MapLibre GL JS map with animated temporal transitions. This pattern keeps deployment costs at zero, response times under 10ms, and the serving layer dependency-free from PyTorch and friends.

The recommended stack is well-established: Python 3.12 with sentence-transformers, BERTopic, and LoRA-tuned DistilBERT for the pipeline; FastAPI with SQLite for the backend; React 19, MapLibre GL JS, Framer Motion, and Zustand for the frontend. All choices are high-confidence with clear version pins and documented compatibility. The architecture is a clean three-tier system (pipeline writes artifacts, backend reads and serves them, frontend renders them) with hard boundaries enforced by separate dependency files.

The most significant risks are upstream data constraints and NLP quality issues. Google Places API returns only 5 reviews per business and its March 2025 pricing overhaul eliminated the $200 monthly credit, making Yelp Open Dataset the more viable primary source. BERTopic on short review text produces 40-75% outliers without careful HDBSCAN tuning. Exponential decay can zero out early-year reviews, undermining the temporal drift feature. These risks are all addressable with known mitigations, but they must be confronted in the correct phase order -- data collection and NLP pipeline quality gates are non-negotiable prerequisites before any frontend work begins.

## Key Findings

### Recommended Stack

The stack splits cleanly across three deployment targets. The **offline pipeline** (Python 3.12) uses sentence-transformers 5.3.0 with `all-MiniLM-L6-v2` for embeddings, BERTopic 0.17.3 for topic discovery, PEFT 0.18.1 for LoRA-based sentiment fine-tuning on DistilBERT, and FAISS for similarity indexing. The **backend** (FastAPI 0.135.x) is deliberately minimal -- it loads pre-computed JSON and a FAISS index into memory and serves them via 4 REST endpoints. SQLite stores structured artifacts with zero ops overhead. The **frontend** (React 19.2, TypeScript 5.7+, Vite 8) uses MapLibre GL JS 5.20.x for WebGL-accelerated map rendering, Framer Motion 12 for UI animations, Zustand 5 for state, and selective D3 modules for colour interpolation.

**Core technologies:**
- **sentence-transformers + `all-MiniLM-L6-v2`:** Fast (5x vs mpnet), 384-dim embeddings keep index small; trivial upgrade path to mpnet if quality disappoints
- **BERTopic 0.17.3:** Transformer-based topic modelling with native temporal topic support; interview-defensible over LDA
- **PEFT/LoRA on DistilBERT:** Minutes to train, <1GB VRAM, zero inference overhead after adapter merge; standard 2025/2026 fine-tuning approach
- **FastAPI + SQLite:** Read-only serving of pre-computed data; no PostgreSQL needed for <1MB of structured data
- **MapLibre GL JS:** BSD-licensed, WebGL-accelerated, no API key; native `fill-extrusion` and paint expressions handle 30 polygons without Deck.gl overhead
- **Framer Motion:** Declarative animations with `AnimatePresence` for mount/unmount; battle-tested with React 19 concurrent rendering

### Expected Features

**Must have (table stakes):**
- Choropleth neighbourhood fills with dark basemap
- Hover tooltip (neighbourhood name + dominant vibe)
- Click-to-detail sidebar with vibe archetype breakdown
- Legend / colour key
- Loading states with skeleton shimmer
- Basic responsive layout (mobile bottom sheet)
- Neighbourhood boundary outlines
- Basic accessibility (keyboard nav, 4.5:1 contrast)

**Should have (differentiators):**
- Time slider with animated year-by-year transitions (the "killer feature")
- Smooth colour interpolation between years
- Representative review quotes in sidebar
- Pulsing/glowing hover effects
- URL-driven deep linking for sharing
- "Find similar neighbourhoods" via FAISS
- Vibe archetype system with colour-coded pills and icons

**Defer (v2+):**
- User accounts, user-submitted reviews, real-time updates
- 3D map extrusions, comparison mode, full-text search
- PDF/image export, onboarding tutorial, chatbot
- Multiple cities (architecture should not preclude expansion, but v1 is NYC only)

### Architecture Approach

The architecture follows an **offline/online split** pattern. The offline pipeline (run once on local GPU) collects reviews, runs NLP, and exports artifacts to Cloudflare R2. The online backend (FastAPI on Railway) downloads artifacts at startup and serves them from memory via 4 endpoints: `GET /neighbourhoods` (enriched GeoJSON), `GET /neighbourhoods/{id}` (detail), `GET /temporal` (full temporal dataset for client-side scrubbing), and `GET /similar?id=X` (FAISS query). The frontend loads the enriched GeoJSON and temporal data on init, making all subsequent interactions (hover, click, time slider) purely client-side with zero additional API calls.

**Major components:**
1. **Data Collector** -- Fetches reviews from Google Places + Yelp, deduplicates, entity-resolves, stores raw in SQLite
2. **NLP Pipeline** -- Embeds reviews, runs BERTopic, computes vibe scores, builds FAISS index, performs temporal bucketing
3. **Artifact Exporter** -- Serializes pipeline outputs to JSON + FAISS binary; enriches boundary GeoJSON with vibe data
4. **Backend API** -- Loads artifacts at startup, serves via REST; only dynamic computation is FAISS nearest-neighbour query
5. **Frontend Map** -- React + MapLibre interactive choropleth with time slider, sidebar, and similarity search

### Critical Pitfalls

1. **Google Places API returns only 5 reviews per place** -- Use Yelp Open Dataset as primary source; build a source-agnostic review schema from day one; budget $50-100 for supplementary scraping if needed
2. **Google Maps Platform pricing overhaul (March 2025)** -- The $200/month credit no longer exists; reviews require Pro-tier field masks at $17/1k requests; use field masks aggressively and separate inventory passes from review fetches
3. **BERTopic produces 40-75% outliers on short review text** -- Lower `min_cluster_size` to 10, `min_samples` to 3; use `reduce_outliers()` post-hoc; consider concatenating reviews per business; validate with coherence score
4. **Exponential decay zeros out 2019-2020 review weights** -- Separate "current vibe" (decay) from "temporal drift" (equal per-bucket); compute in log-space; clamp minimum weight to 1e-6
5. **MapLibre full-map repaints on every animation frame** -- Use `setPaintProperty()` for colour transitions; debounce time slider events; test paint times <16ms on mid-range devices

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Data Foundation
**Rationale:** Everything downstream depends on having reviews with adequate temporal coverage and correct neighbourhood boundaries. Both critical pitfalls (5-review API limit, pricing changes) and the GeoJSON projection/naming issues must be resolved first.
**Delivers:** Raw review corpus (50k+ reviews spanning 2019-2025), validated NYC boundary GeoJSON in WGS84, SQLite storage with unified review schema, data quality report (review count histogram by neighbourhood and year).
**Addresses:** Data collection table stakes; boundary preparation for choropleth.
**Avoids:** Pitfalls 1 (5-review limit), 2 (pricing), 9 (boundary projection/naming).
**Research flag:** NEEDS RESEARCH. Google Places vs Yelp Open Dataset coverage for NYC must be validated. Third-party scraping API options need cost/ToS evaluation.

### Phase 2: NLP Pipeline
**Rationale:** All ML computation must complete before the backend or frontend can be built, since they serve pre-computed artifacts. This phase has the most pitfalls (4 of 11) and requires iterative tuning with quality gates.
**Delivers:** Sentence embeddings, BERTopic topics, sentiment scores, vibe archetype vectors, temporal drift data per year bucket, FAISS index, representative quotes, all serialized as artifacts.
**Uses:** sentence-transformers, BERTopic, PEFT/LoRA, FAISS, NumPy/pandas/scikit-learn.
**Implements:** Offline pipeline component, artifact export, GeoJSON enrichment.
**Avoids:** Pitfalls 3 (BERTopic outliers), 4 (embedding model mismatch), 5 (sentiment label noise), 6 (exponential decay underflow), 8 (temporal small samples), 10 (FAISS overkill).
**Research flag:** NEEDS RESEARCH. BERTopic hyperparameter tuning for review text has sparse documentation; embedding model evaluation methodology needs definition; LoRA fine-tuning on Yelp data needs verified recipes.

### Phase 3: Backend API
**Rationale:** The backend is a thin serving layer that depends on exported artifacts from Phase 2. It is architecturally simple (4 read-only endpoints) but must be built before the frontend can integrate.
**Delivers:** FastAPI application with 4 endpoints, artifact loading at startup, FAISS query wrapper, Pydantic response schemas, OpenAPI documentation.
**Uses:** FastAPI, Uvicorn, faiss-cpu, SQLite, orjson.
**Implements:** Backend API component, artifact loader service.
**Avoids:** Anti-patterns: running ML models in backend, using vector database for 50k docs, per-year temporal endpoints.
**Research flag:** STANDARD PATTERNS. FastAPI with lifespan events, Pydantic models, and static data serving are well-documented. No phase research needed.

### Phase 4: Frontend -- Core Map
**Rationale:** The map is the product. This phase delivers all table-stakes features that make the app functional and non-embarrassing. It depends on the backend API being available (or mockable).
**Delivers:** Dark basemap choropleth, hover tooltips, click-to-detail sidebar with vibe pills and topic bars, legend, loading states, responsive layout, basic accessibility.
**Addresses:** All 10 table-stakes features from FEATURES.md.
**Uses:** React 19, MapLibre GL JS, react-map-gl, Zustand, Tailwind CSS 4, Framer Motion.
**Avoids:** Pitfall 9 (GeoJSON projection -- already resolved in Phase 1).
**Research flag:** STANDARD PATTERNS. React + MapLibre choropleth rendering is well-documented. Sidebar and responsive layout are standard UI patterns.

### Phase 5: Frontend -- Temporal Animation and Polish
**Rationale:** The time slider is the top differentiator and the feature people will remember. It depends on the core map working and temporal data being available. Visual polish (glow effects, colour transitions, hover animations) elevates the product from functional to portfolio-worthy.
**Delivers:** Time slider with play/pause, smooth colour interpolation between years, pulsing hover effects, glow effects on dominant-vibe polygons, representative review quotes in sidebar.
**Addresses:** Top differentiator features from FEATURES.md.
**Avoids:** Pitfall 7 (MapLibre full repaints -- debounce slider, batch paint property updates).
**Research flag:** NEEDS RESEARCH. MapLibre animation performance optimization for choropleth transitions has limited documentation; the interplay between `requestAnimationFrame`, `setPaintProperty`, and React state needs careful design.

### Phase 6: Deployment and Sharing Features
**Rationale:** Deployment is last because it depends on everything working locally. Sharing features (deep links, OG images) maximize portfolio impact but are not functional requirements.
**Delivers:** Railway/Render deployment for backend, Vercel deployment for frontend, CI/CD via GitHub Actions, URL-driven deep linking, OG image generation, "Find similar neighbourhoods" feature.
**Addresses:** Phase 3 features from FEATURES.md (portfolio polish).
**Avoids:** Pitfall 11 (backend cold start/OOM -- no ML models in production, single worker, <512MB memory).
**Research flag:** STANDARD PATTERNS. Railway/Vercel deployment is well-documented. OG image generation may need light research if using Vercel OG.

### Phase Ordering Rationale

- **Phase 1 before Phase 2:** The NLP pipeline cannot run without review data. Data quality issues (temporal coverage gaps, boundary mismatches) discovered late would invalidate all downstream work.
- **Phase 2 before Phase 3-6:** The entire frontend and backend depend on pre-computed artifacts. The offline/online split means ML work is a hard prerequisite.
- **Phase 3 before Phase 4:** The frontend needs API endpoints to fetch data. However, Phases 3 and 4 can overlap if the API contract (Pydantic schemas) is defined early and the frontend uses mock data.
- **Phase 4 before Phase 5:** The time slider and visual effects build on top of the working choropleth map. Attempting animation before the base map works creates debugging confusion.
- **Phase 6 last:** Deployment and sharing features add zero functionality. They are polish that maximizes portfolio impact after the core product works.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Google Places vs Yelp Open Dataset NYC coverage; third-party scraping options; boundary dataset selection
- **Phase 2:** BERTopic hyperparameter tuning for short review text; embedding model evaluation protocol; LoRA fine-tuning recipe validation
- **Phase 5:** MapLibre animation performance optimization; choropleth colour transition techniques

Phases with standard patterns (skip research-phase):
- **Phase 3:** FastAPI REST API with pre-loaded static data -- textbook pattern
- **Phase 4:** React + MapLibre choropleth with sidebar -- well-documented
- **Phase 6:** Railway/Vercel deployment, GitHub Actions CI -- standard DevOps

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies verified against official PyPI/npm with version pins and compatibility notes. Alternatives systematically evaluated. |
| Features | HIGH | Feature landscape grounded in established map UI patterns (NN/g, MapUIPatterns.com). Clear MVP phasing with dependency graph. |
| Architecture | HIGH | Offline/online split is the canonical pattern for pre-computed ML serving. Data flow, component boundaries, and anti-patterns clearly documented. |
| Pitfalls | HIGH | 11 pitfalls verified against official docs (Google Maps pricing, BERTopic best practices, FAISS GitHub issues, MapLibre performance). Recovery strategies included. |

**Overall confidence:** HIGH

### Gaps to Address

- **Yelp Open Dataset NYC coverage:** The dataset is large but may not include sufficient NYC business coverage. This must be validated before committing to it as the primary source. Fallback: third-party scraping API.
- **Embedding model evaluation:** STACK.md recommends MiniLM but PITFALLS.md warns it may underperform on informal review text. A 30-minute evaluation on 100 review pairs should be the first task in Phase 2 before any downstream pipeline work.
- **2020 review volume:** COVID-era review volume is likely 20-30% of normal years. The pipeline must handle sparse year buckets gracefully (pooling, confidence intervals, "insufficient data" indicators). This is a known issue but the exact threshold needs empirical determination.
- **MapLibre animation performance budget:** The 16ms paint time target is stated but the actual performance of `setPaintProperty` with 30 polygon colour transitions has not been benchmarked. A quick prototype early in Phase 5 would de-risk this.
- **Cloudflare R2 vs committed artifacts:** The architecture recommends R2 for artifact storage, but if total artifact size is under 50MB (excluding FAISS index), committing smaller JSON files to the repo and only using R2 for the FAISS index simplifies deployment. This decision can be deferred to Phase 6.

## Sources

### Primary (HIGH confidence)
- [Google Maps Platform pricing (March 2025)](https://developers.google.com/maps/billing-and-pricing/march-2025)
- [Google Places API REST reference](https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places)
- [BERTopic documentation and best practices](https://maartengr.github.io/BERTopic/)
- [sentence-transformers pretrained models](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html)
- [FAISS documentation and GitHub](https://faiss.ai/)
- [MapLibre GL JS documentation](https://maplibre.org/maplibre-gl-js/docs/)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [PEFT/LoRA documentation](https://huggingface.co/docs/peft/en/index)

### Secondary (MEDIUM confidence)
- [NYC Geography GeoJSON repository](https://github.com/nycehs/NYC_geography)
- [Jared Lander NYC neighbourhood boundaries](https://www.jaredlander.com/2022/08/new-york-city-neighborhood-boundaries/)
- [Map UI Patterns catalogue](https://mapuipatterns.com/patterns/)
- [NN/g interactive maps research](https://www.nngroup.com/articles/interactive-ux-maps/)
- [Hopsworks FTI pipeline architecture](https://www.hopsworks.ai/post/mlops-to-ml-systems-with-fti-pipelines)

### Tertiary (LOW confidence)
- [Gibbs-BERTopic for short text (Feb 2025)](https://www.researchgate.net/publication/389929907) -- Promising for short review text but not yet widely adopted

---
*Research completed: 2026-03-16*
*Ready for roadmap: yes*

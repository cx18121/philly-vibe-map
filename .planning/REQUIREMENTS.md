# Requirements: Neighbourhood Vibe Mapper — NYC

**Defined:** 2026-03-16
**Core Value:** An interactive map where anyone can feel the character of a New York City neighbourhood through its reviews — and watch how that character has shifted year by year from 2019 to 2025.

## v1 Requirements

### Data Collection

- [x] **DATA-01**: System collects 50k+ reviews spanning 2019–2025 from Google Places API and Yelp Fusion API across 30 neighbourhoods in Manhattan and Brooklyn
- [x] **DATA-02**: System deduplicates and entity-resolves businesses appearing on both platforms using name + lat/lng proximity matching
- [x] **DATA-03**: Each stored review includes: text, timestamp, business name, business lat/lng, source platform, neighbourhood assignment
- [x] **DATA-04**: System fetches official NYC neighbourhood boundary GeoJSON from NYC Open Data (NTA or community-defined boundaries) and reprojects to WGS84
- [x] **DATA-05**: System produces a data quality report (review count by neighbourhood and by year) to validate temporal coverage before NLP begins
- [x] **DATA-06**: Raw reviews are stored in SQLite with a source-agnostic unified schema (platform-specific fields preserved as JSON)

### NLP Pipeline

- [ ] **NLP-01**: System embeds all reviews using a sentence-transformer model (`all-MiniLM-L6-v2` baseline, with evaluation gate before proceeding)
- [ ] **NLP-02**: System runs BERTopic on review embeddings to discover neighbourhood-specific topics without predefined categories (HDBSCAN tuned for short text: `min_cluster_size=10`, `min_samples=3`, with `reduce_outliers()`)
- [ ] **NLP-03**: System scores each neighbourhood against 6 vibe archetypes (artsy, foodie, nightlife, family, upscale, cultural) via cosine similarity between topic cluster centroids and archetype seed phrase embeddings
- [ ] **NLP-04**: System domain-adapts a sentiment classifier using LoRA fine-tuning on DistilBERT with the Yelp Open Dataset (star ratings as labels), merging adapter weights before export
- [ ] **NLP-05**: System computes recency-weighted vibe scores using exponential decay on review timestamps (half-life configurable; computation in log-space with minimum weight clamp of 1e-6)
- [ ] **NLP-06**: System buckets reviews by year (2019–2025), runs the full vibe scoring pipeline per bucket (equal weights within each bucket, no decay), and produces a temporal drift time series per neighbourhood
- [ ] **NLP-07**: System builds a FAISS flat index over neighbourhood vibe vectors to support nearest-neighbour similarity queries
- [ ] **NLP-08**: System selects 3–5 representative review quotes per neighbourhood per vibe archetype (highest cosine similarity to archetype centroid)
- [x] **NLP-09**: Pipeline exports all artifacts (embeddings, vibe scores, temporal series, FAISS index, representative quotes, enriched GeoJSON) as serialized files ready for backend consumption

### Backend API

- [ ] **API-01**: `GET /neighbourhoods` returns enriched GeoJSON FeatureCollection with vibe scores, dominant vibe, and sentiment scores embedded in feature properties
- [ ] **API-02**: `GET /neighbourhoods/{id}` returns per-neighbourhood detail: topic breakdown, vibe archetype scores, representative quotes, review count, data coverage by year
- [ ] **API-03**: `GET /temporal` returns the full temporal drift dataset (all neighbourhoods × all years × vibe vectors) as a single JSON payload for client-side time-slider scrubbing
- [ ] **API-04**: `GET /similar?id={neighbourhood_id}&k={n}` returns the k nearest-neighbour neighbourhoods via FAISS query
- [ ] **API-05**: Backend loads all artifacts (JSON + FAISS index) into memory at startup via FastAPI lifespan event — zero ML model loading in the serving layer
- [ ] **API-06**: All endpoints return responses in under 100ms (FAISS query included)

### Frontend — Core Map

- [ ] **MAP-01**: Map renders with a dark basemap and semi-transparent neighbourhood fills coloured by dominant vibe archetype
- [ ] **MAP-02**: Each vibe archetype has a distinct colour: artsy (purple), foodie (orange), nightlife (cyan), family (green), upscale (gold), cultural (red) — palette tested for colourblind accessibility
- [ ] **MAP-03**: Hovering a neighbourhood displays a tooltip with neighbourhood name and dominant vibe
- [ ] **MAP-04**: Clicking a neighbourhood opens a sidebar showing: vibe archetype breakdown (animated bar chart), top topics, vibe pills with sentiment scores, and 3 representative review quotes
- [ ] **MAP-05**: A legend explains the 6 vibe colour codes
- [ ] **MAP-06**: Map renders loading skeleton while GeoJSON and temporal data are fetching
- [ ] **MAP-07**: App is responsive: sidebar collapses to a bottom sheet on mobile viewports
- [ ] **MAP-08**: Neighbourhood boundary outlines are visible on the dark basemap
- [ ] **MAP-09**: Basic keyboard navigation: tab to neighbourhoods, enter to select, escape to dismiss sidebar

### Frontend — Temporal Animation & Polish

- [ ] **VIZ-01**: A time slider (2019–2025) lets users scrub through years; neighbourhood fill colours transition smoothly to reflect vibe changes per year
- [ ] **VIZ-02**: Time slider includes a play/pause button that auto-advances through years with a configurable speed
- [ ] **VIZ-03**: Colour transitions between years are interpolated smoothly (not a hard cut) using MapLibre paint property animation
- [ ] **VIZ-04**: Hovered neighbourhood pulses/glows to indicate it is interactive
- [ ] **VIZ-05**: Dominant-vibe neighbourhood fills have a subtle glow effect (via MapLibre `fill-extrusion` or equivalent) that intensifies on hover
- [ ] **VIZ-06**: Sidebar content (bars, pills, quotes) animates in on neighbourhood selection using Framer Motion

### Deployment

- [ ] **DEPLOY-01**: Backend deployed to a public URL (Railway or Render) with artifacts loaded from Cloudflare R2 or committed JSON files
- [ ] **DEPLOY-02**: Frontend deployed to Vercel with a public URL requiring no login
- [ ] **DEPLOY-03**: URL encodes selected neighbourhood and current year so any state can be shared via link

## v2 Requirements

### Sharing & Discovery

- **SHARE-01**: "Find similar neighbourhoods" UI surface (FAISS similarity already built in backend)
- **SHARE-02**: OG image generated per neighbourhood for social sharing previews
- **SHARE-03**: Embed snippet for including the map in other pages

### Extended Data

- **EXT-01**: Expand coverage to Queens, Bronx, Staten Island
- **EXT-02**: Pipeline refresh workflow to incorporate reviews beyond 2025
- **EXT-03**: Per-business drill-down view (which businesses drive a neighbourhood's vibe)

### Analytics

- **ANLT-01**: View counter or Plausible analytics to measure portfolio reach
- **ANLT-02**: Most-viewed neighbourhoods surfaced on the map

## Out of Scope

| Feature | Reason |
|---------|--------|
| User accounts / login | Read-only public app — no personalisation in v1 |
| Real-time review ingestion | Pipeline is intentionally static batch — live ingestion would require ongoing API spend |
| 3D map extrusions | Visual complexity without clear UX payoff; Deck.gl overhead not justified for 30 polygons |
| Side-by-side neighbourhood comparison | High UI complexity; FAISS similarity search is sufficient for v1 |
| Full-text review search | Would require a search index (Elasticsearch/Typesense) — not worth the ops overhead |
| PDF / image export | Low portfolio value, medium implementation effort |
| Onboarding tutorial / overlay | Adds cognitive load; good UX design should be self-explanatory |
| Chatbot / AI assistant | Scope creep; the map IS the interface |
| Boroughs beyond Manhattan + Brooklyn | Queens/Bronx/Staten Island deferred to v2 |
| Mobile native app | Web-first; responsive design is sufficient |
| Crowdsourced / user-submitted reviews | Data integrity risk, moderation overhead |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Complete |
| DATA-05 | Phase 1 | Complete |
| DATA-06 | Phase 1 | Complete |
| NLP-01 | Phase 2 | Pending |
| NLP-02 | Phase 2 | Pending |
| NLP-03 | Phase 2 | Pending |
| NLP-04 | Phase 2 | Pending |
| NLP-05 | Phase 2 | Pending |
| NLP-06 | Phase 2 | Pending |
| NLP-07 | Phase 2 | Pending |
| NLP-08 | Phase 2 | Pending |
| NLP-09 | Phase 2 | Complete |
| API-01 | Phase 3 | Pending |
| API-02 | Phase 3 | Pending |
| API-03 | Phase 3 | Pending |
| API-04 | Phase 3 | Pending |
| API-05 | Phase 3 | Pending |
| API-06 | Phase 3 | Pending |
| MAP-01 | Phase 4 | Pending |
| MAP-02 | Phase 4 | Pending |
| MAP-03 | Phase 4 | Pending |
| MAP-04 | Phase 4 | Pending |
| MAP-05 | Phase 4 | Pending |
| MAP-06 | Phase 4 | Pending |
| MAP-07 | Phase 4 | Pending |
| MAP-08 | Phase 4 | Pending |
| MAP-09 | Phase 4 | Pending |
| VIZ-01 | Phase 5 | Pending |
| VIZ-02 | Phase 5 | Pending |
| VIZ-03 | Phase 5 | Pending |
| VIZ-04 | Phase 5 | Pending |
| VIZ-05 | Phase 5 | Pending |
| VIZ-06 | Phase 5 | Pending |
| DEPLOY-01 | Phase 6 | Pending |
| DEPLOY-02 | Phase 6 | Pending |
| DEPLOY-03 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 38 total
- Mapped to phases: 38
- Unmapped: 0

---
*Requirements defined: 2026-03-16*
*Last updated: 2026-03-16 after roadmap creation*

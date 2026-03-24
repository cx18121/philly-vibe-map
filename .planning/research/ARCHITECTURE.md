# Architecture Research

**Domain:** NLP-powered geospatial visualization (pre-computed ML pipeline + interactive map)
**Researched:** 2026-03-16
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
OFFLINE (local GPU, run once)                    ONLINE (deployed, serves users)
========================================         ========================================

 +-----------------+   +-----------------+
 | Data Collection |   | NYC Open Data   |
 | (Google Places, |   | (Neighbourhood  |
 |  Yelp Fusion)   |   |  Boundaries)    |
 +--------+--------+   +--------+--------+
          |                      |
          v                      v
 +--------+--------+   +--------+--------+
 | Raw Review Store|   | Boundary GeoJSON|
 | (SQLite DB)     |   | (local file)    |
 +--------+--------+   +--------+--------+
          |                      |
          v                      |
 +------------------+            |
 | NLP Pipeline     |            |          +----------------------------+
 | - Embeddings     |            |          |  Frontend (Vercel/CDN)     |
 | - BERTopic       |            |          |  - Mapbox GL JS            |
 | - Sentiment      |            |          |  - React + Zustand         |
 | - FAISS index    |            |          |  - Time slider controls    |
 | - Temporal drift |            |          +-------------+--------------+
 +--------+---------+            |                        |
          |                      |                        | REST/JSON
          v                      v                        v
 +------------------+   +------------------+   +----------------------------+
 | Artifact Export  |   | GeoJSON Enricher |   |  Backend API               |
 | - vibe_scores.json   | (merge vibe data |   |  (FastAPI on Railway)      |
 | - topics.json    |   |  into boundaries)|   |  - /neighbourhoods         |
 | - temporal.json  |   +--------+---------+   |  - /neighbourhoods/{id}    |
 | - faiss.index    |            |              |  - /similar?id=X           |
 | - quotes.json    |            v              |  - /temporal/{id}          |
 +--------+---------+   +------------------+   +-------------+--------------+
          |              | Enriched GeoJSON |                 |
          |              +--------+---------+                 |
          |                       |                           |
          v                       v                           |
 +---------------------------------------------------+       |
 |              Artifact Storage                      |       |
 |  Cloudflare R2 bucket (or repo for small files)   +-------+
 |  - enriched_neighbourhoods.geojson                 |  load at startup
 |  - vibe_scores.json                                |
 |  - topics.json                                     |
 |  - temporal.json                                   |
 |  - quotes.json                                     |
 |  - faiss.index                                     |
 +---------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Data Collector | Fetch reviews from Google Places + Yelp, deduplicate, entity-resolve, store raw | Python scripts with rate limiting, SQLite for raw storage |
| NLP Pipeline | Embed reviews, run BERTopic, compute vibe scores, build FAISS index, temporal bucketing | Python with sentence-transformers, BERTopic, FAISS, runs on local GPU |
| Artifact Exporter | Serialize pipeline outputs to portable JSON + binary files | Python scripts producing JSON and FAISS binary index |
| GeoJSON Enricher | Merge vibe scores/topics into NYC boundary GeoJSON to produce enriched GeoJSON | Python script joining pipeline outputs with boundary polygons |
| Backend API | Load pre-computed artifacts at startup, serve them via REST endpoints | FastAPI on Railway/Render, loads JSON + FAISS index into memory |
| Frontend | Interactive map with time slider, neighbourhood detail sidebar, similarity search | React + Mapbox GL JS on Vercel |
| Artifact Storage | Host pre-computed files for backend to load | Cloudflare R2 (free egress) or committed to repo if small enough |

## Recommended Project Structure

```
philly-vibe-map/
├── pipeline/                    # Offline data + NLP pipeline (Python)
│   ├── collect/                 # Data collection scripts
│   │   ├── google_places.py     # Google Places API fetcher
│   │   ├── yelp_fusion.py       # Yelp Fusion API fetcher
│   │   ├── deduplicate.py       # Entity resolution (name + lat/lng)
│   │   └── boundaries.py        # NYC Open Data boundary fetcher
│   ├── nlp/                     # NLP pipeline stages
│   │   ├── embed.py             # sentence-transformers embedding
│   │   ├── topics.py            # BERTopic topic modelling
│   │   ├── sentiment.py         # Domain-adapted sentiment classifier
│   │   ├── vibe_scores.py       # Archetype cosine similarity scoring
│   │   ├── temporal.py          # Year-bucketed drift analysis
│   │   └── faiss_index.py       # FAISS index construction
│   ├── export/                  # Artifact serialization
│   │   ├── export_all.py        # Master export script
│   │   └── enrich_geojson.py    # Merge vibe data into boundary GeoJSON
│   ├── data/                    # Raw data (gitignored except boundaries)
│   │   ├── reviews.db           # SQLite raw review store
│   │   └── nyc_boundaries.geojson
│   ├── artifacts/               # Pipeline outputs (gitignored, uploaded to R2)
│   │   ├── enriched_neighbourhoods.geojson
│   │   ├── vibe_scores.json
│   │   ├── topics.json
│   │   ├── temporal.json
│   │   ├── quotes.json
│   │   └── faiss.index
│   ├── requirements.txt         # Pipeline Python deps (torch, transformers, etc.)
│   └── Makefile                 # Orchestrates pipeline stages
├── backend/                     # Online API server (Python/FastAPI)
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan startup loader
│   │   ├── routers/
│   │   │   ├── neighbourhoods.py
│   │   │   ├── similar.py
│   │   │   └── temporal.py
│   │   ├── services/
│   │   │   ├── artifact_loader.py  # Load JSON + FAISS from R2 or local
│   │   │   └── faiss_search.py     # FAISS query wrapper
│   │   └── models/
│   │       └── schemas.py       # Pydantic response models
│   ├── requirements.txt         # Server deps (fastapi, uvicorn, faiss-cpu)
│   └── Dockerfile
├── frontend/                    # Interactive map (TypeScript/React)
│   ├── src/
│   │   ├── components/
│   │   │   ├── Map.tsx          # Mapbox GL JS map
│   │   │   ├── Sidebar.tsx      # Neighbourhood detail panel
│   │   │   ├── TimeSlider.tsx   # Year slider (2019-2025)
│   │   │   ├── VibePills.tsx    # Archetype score display
│   │   │   └── TopicBars.tsx    # Topic breakdown chart
│   │   ├── hooks/
│   │   │   ├── useNeighbourhoods.ts
│   │   │   └── useTemporalData.ts
│   │   ├── stores/
│   │   │   └── mapStore.ts      # Zustand state
│   │   ├── api/
│   │   │   └── client.ts        # API client
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── App.tsx
│   ├── public/
│   └── package.json
└── .planning/                   # Project planning docs
```

### Structure Rationale

- **pipeline/ separate from backend/:** The offline pipeline has heavy GPU dependencies (torch, transformers, BERTopic) that must never appear in the deployed backend. Keeping them in separate directories with separate `requirements.txt` files enforces this boundary. The pipeline produces artifacts; the backend consumes them. They share nothing at runtime.
- **pipeline/collect/ vs pipeline/nlp/:** Data collection is API-bound and rate-limited; NLP is compute-bound and GPU-heavy. Separating them lets you re-run NLP without re-fetching data, and vice versa.
- **pipeline/artifacts/:** Gitignored output directory. The Makefile orchestrates stages and writes here. These files get uploaded to R2 (or committed if small).
- **backend/services/:** The artifact_loader service downloads artifacts from R2 at startup and holds them in memory. The FAISS search service wraps the loaded index. No ML dependencies -- only `faiss-cpu` for index querying.
- **frontend/stores/:** Zustand over Redux because the state is simple (selected neighbourhood, current year, active vibe filter). Zustand requires far less boilerplate.

## Architectural Patterns

### Pattern 1: Offline/Online Split (Pre-compute Everything)

**What:** All ML computation happens offline on a local GPU. The online serving layer loads static artifacts and serves them as JSON. The backend never imports torch, transformers, or BERTopic.

**When to use:** When your ML pipeline is expensive but your query patterns are predictable (fixed set of neighbourhoods, fixed time buckets, fixed vibe archetypes).

**Trade-offs:**
- Pro: Sub-millisecond API responses, zero GPU cost in production, trivial to scale
- Pro: Backend can run on the cheapest tier of Railway/Render (512MB RAM is plenty)
- Con: Adding a new neighbourhood or time bucket requires re-running the pipeline
- Con: No "ask anything" flexibility -- queries are limited to what was pre-computed

**This is the correct pattern for this project** because the query space is fully enumerable: 30 neighbourhoods x 7 years x 6 archetypes. Pre-compute all combinations.

### Pattern 2: FAISS Index as In-Memory Singleton

**What:** Load the FAISS index into memory once during FastAPI's lifespan startup event. Serve all similarity queries from this in-memory index. Never reload during the application lifecycle.

**When to use:** When the index is small enough to fit in memory on your deployment target. For 50k reviews with 384-dimensional embeddings, a flat FAISS index is approximately 77MB -- well within Railway's free tier (512MB).

**Trade-offs:**
- Pro: Sub-millisecond query latency
- Pro: No external vector database dependency
- Con: Cold start takes a few seconds to load index from R2
- Con: Index updates require redeployment

**Example:**
```python
from contextlib import asynccontextmanager
import faiss
import numpy as np

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load artifacts at startup
    app.state.faiss_index = faiss.read_index("artifacts/faiss.index")
    app.state.vibe_scores = load_json("artifacts/vibe_scores.json")
    app.state.topics = load_json("artifacts/topics.json")
    app.state.temporal = load_json("artifacts/temporal.json")
    yield

app = FastAPI(lifespan=lifespan)
```

### Pattern 3: Enriched GeoJSON as Single API Response

**What:** Pre-merge vibe scores, dominant topics, and sentiment into the neighbourhood boundary GeoJSON during the export phase. Serve this single enriched GeoJSON from one endpoint. The frontend loads it once and uses Mapbox GL's data-driven styling to colour polygons.

**When to use:** When you have fewer than ~100 features (polygons) and the properties per feature are modest (a few KB each). 30 neighbourhoods with vibe scores, topics, and quotes easily fit in a single response under 500KB.

**Trade-offs:**
- Pro: Single network request loads the entire map
- Pro: Mapbox GL JS natively consumes GeoJSON sources -- zero transformation needed
- Pro: Enables instant client-side filtering without additional API calls
- Con: If enriched GeoJSON grows very large, initial load slows down

**Example response structure:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Polygon", "coordinates": [...] },
      "properties": {
        "neighbourhood": "Williamsburg",
        "vibes": {
          "artsy": 0.82, "foodie": 0.71, "nightlife": 0.65,
          "family": 0.23, "upscale": 0.34, "cultural": 0.58
        },
        "dominant_vibe": "artsy",
        "sentiment": 0.72,
        "top_topics": ["craft cocktails", "vintage shops", "brunch spots"],
        "review_count": 1847
      }
    }
  ]
}
```

## Answers to Key Architecture Questions

### Q1: Where should pre-computed embeddings and FAISS indexes live?

**Answer: Cloudflare R2, downloaded by the backend at startup.**

- The FAISS flat index for 50k reviews at 384 dimensions is ~77MB. Too large to commit to git, but trivially small for object storage.
- Cloudflare R2 has zero egress fees (unlike S3), so the backend downloading artifacts on cold start costs nothing.
- The JSON artifacts (vibe_scores, topics, temporal, quotes) are likely 5-20MB total -- these could be committed to the repo, but R2 keeps everything in one place.
- Do NOT use a database for embeddings. A database adds latency, operational complexity, and cost for zero benefit when the dataset fits comfortably in memory.
- Do NOT use faiss-gpu in the backend. The backend runs `faiss-cpu` only -- GPU is for the offline pipeline.

**Artifact storage decision matrix:**

| Artifact | Size Estimate | Storage | Rationale |
|----------|--------------|---------|-----------|
| faiss.index | ~77MB | R2 only | Too large for git |
| enriched_neighbourhoods.geojson | ~200-500KB | R2 + could commit | Small, but keep with other artifacts |
| vibe_scores.json | ~50KB | R2 | Pipeline output |
| topics.json | ~200KB | R2 | Pipeline output |
| temporal.json | ~300KB | R2 | Per-year vibe vectors |
| quotes.json | ~2-5MB | R2 | Representative review quotes |

### Q2: What is the right separation between offline pipeline and online serving?

**Answer: Hard boundary at the artifact files. The pipeline writes files; the backend reads files. They share no code, no dependencies, no runtime.**

The pipeline directory has `requirements.txt` with torch, transformers, BERTopic, hdbscan, umap-learn, faiss-gpu. The backend has `requirements.txt` with fastapi, uvicorn, faiss-cpu, httpx (to download from R2). These two requirements files must never converge.

The pipeline produces a fixed set of artifact files with a known schema. The backend's artifact_loader knows that schema. This is the only coupling between the two systems.

A `Makefile` in the pipeline directory orchestrates stages:
```makefile
collect:     # Fetch reviews from APIs
embed:       # Run sentence-transformers
topics:      # Run BERTopic
sentiment:   # Run sentiment classifier
scores:      # Compute vibe archetype scores
temporal:    # Bucket by year, re-run pipeline per bucket
index:       # Build FAISS index
export:      # Serialize all outputs to artifacts/
upload:      # Push artifacts to R2
```

### Q3: How should temporal drift data be structured for efficient time-slider queries?

**Answer: Pre-compute a flat JSON keyed by neighbourhood, containing an array of year-snapshots. The frontend requests this once and scrubs through it client-side.**

```json
{
  "williamsburg": {
    "years": [
      {
        "year": 2019,
        "vibes": {"artsy": 0.85, "foodie": 0.60, "nightlife": 0.72, ...},
        "sentiment": 0.68,
        "review_count": 312,
        "top_topics": ["dive bars", "art galleries", "vintage"]
      },
      {
        "year": 2020,
        "vibes": {"artsy": 0.80, "foodie": 0.55, "nightlife": 0.30, ...},
        "sentiment": 0.52,
        "review_count": 98,
        "top_topics": ["takeout", "outdoor dining", "closures"]
      }
    ]
  }
}
```

This structure supports the time slider efficiently because:
- The frontend loads the full temporal dataset once (~300KB for 30 neighbourhoods x 7 years)
- Sliding the time slider is a pure client-side operation: index into the year array, update Mapbox source data
- No additional API calls on slider interaction -- instant response
- The backend serves this as a single endpoint: `GET /temporal` returns the entire structure

Do NOT structure this as `GET /temporal/{neighbourhood}/{year}` -- that would require 30 x 7 = 210 API calls to load the full dataset, or complex batching logic. Pre-compute and serve the whole thing.

### Q4: Should GeoJSON be served from the API or bundled with the frontend?

**Answer: Serve from the API, but as a single enriched GeoJSON that the frontend caches aggressively.**

- Bundle with frontend: Tempting for static data, but it couples deployment. Re-running the pipeline would require re-deploying the frontend even though the frontend code hasn't changed.
- Serve from API: The backend loads `enriched_neighbourhoods.geojson` at startup and serves it at `GET /neighbourhoods`. The frontend fetches it once on load and caches it. With `Cache-Control` headers, subsequent visits don't even hit the API.
- The GeoJSON is ~200-500KB -- small enough for a single request, large enough that bundling it into the JS bundle would hurt initial parse time.

### Q5: How to handle NYC neighbourhood boundary GeoJSON?

**Answer: Download once from NYC Open Data / community sources, commit the raw file to the repo, and enrich it during the export phase.**

NYC does not have a single canonical "neighbourhood" boundary definition. Use the NTA (Neighbourhood Tabulation Area) boundaries from NYC Planning, which are the closest to what people mean by "neighbourhoods." Filter to Manhattan and Brooklyn polygons only.

- Download the NTA GeoJSON from NYC Open Data portal
- Commit the raw boundary file to `pipeline/data/nyc_boundaries.geojson` (this IS version-controlled -- it's reference data, not a pipeline output)
- The `enrich_geojson.py` script merges vibe scores and topic data into each feature's properties
- The enriched version goes to `pipeline/artifacts/enriched_neighbourhoods.geojson` (gitignored, uploaded to R2)

If NTA boundaries don't match the desired 30 neighbourhoods well enough, use the community-maintained NYC neighbourhood GeoJSON from Jared Lander or the NYCHealth/NYC_geography repo, which offer more granular definitions.

## Data Flow

### Offline Pipeline Flow

```
Google Places API ──┐
                    ├──> Raw Reviews (SQLite) ──> Embeddings (sentence-transformers)
Yelp Fusion API ────┘         |                        |
                              |                        ├──> BERTopic Topics
                              |                        ├──> Vibe Archetype Scores
                              |                        ├──> FAISS Index
                              v                        ├──> Sentiment Scores
                    Entity Resolution                  └──> Temporal Buckets (per year)
                    (name + lat/lng dedup)                       |
                                                                v
                    NYC Boundary GeoJSON ──────────> Enriched GeoJSON
                                                        |
                                                        v
                                                  Upload to R2
```

### Online Request Flow

```
User opens app
    |
    v
Frontend loads ──> GET /neighbourhoods ──> Backend returns enriched GeoJSON from memory
    |
    v
Mapbox renders polygons coloured by dominant vibe
    |
    v
User clicks neighbourhood
    |
    v
Frontend requests ──> GET /neighbourhoods/{id} ──> Backend returns topics, quotes, scores
    |
    v
Sidebar renders topic bars, vibe pills, representative quotes
    |
    v
User drags time slider
    |
    v
Frontend already has temporal data (loaded on init via GET /temporal)
    |
    v
Client-side: index into year array, update Mapbox source data, animate transition
    |
    v
User clicks "Find similar"
    |
    v
Frontend requests ──> GET /similar?id=williamsburg ──> Backend queries FAISS index
    |
    v
Backend returns top-5 similar neighbourhoods with similarity scores
```

### Key Data Flows

1. **Initial map load:** Single `GET /neighbourhoods` returns enriched GeoJSON (~300KB). Frontend caches this. One request paints the entire map.
2. **Temporal scrubbing:** `GET /temporal` returns the full temporal dataset (~300KB). Loaded once on init. All slider interactions are client-side thereafter.
3. **Neighbourhood detail:** `GET /neighbourhoods/{id}` returns detailed topics, quotes, and scores for a single neighbourhood. Loaded on click, cached per-neighbourhood.
4. **Similarity search:** `GET /similar?id={id}` queries the in-memory FAISS index. Returns top-N similar neighbourhoods with cosine similarity scores. Sub-millisecond.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 users | Current architecture is perfect. Single FastAPI instance, all data in memory. |
| 100-10k users | Add `Cache-Control: public, max-age=86400` headers. Frontend and CDN cache everything. Backend barely gets hit. |
| 10k+ users | If needed, move enriched GeoJSON and temporal JSON to a CDN (R2 public bucket). Backend only needed for FAISS similarity queries. Everything else is static. |

### Scaling Priorities

1. **First bottleneck: Cold start time.** Downloading ~80MB from R2 on Railway cold start could take 5-10 seconds. Mitigation: Railway keeps containers warm if they receive traffic. Add a health check endpoint that warms the container.
2. **Second bottleneck: Concurrent FAISS queries.** FAISS is not thread-safe by default. Mitigation: At this scale (50k vectors, flat index), queries take microseconds. Use a threading lock around searches -- the contention is negligible.

## Anti-Patterns

### Anti-Pattern 1: Running ML Models in the Backend

**What people do:** Import sentence-transformers or BERTopic in the FastAPI backend to compute embeddings on user request.
**Why it's wrong:** Massive cold start (loading model weights), enormous container size (2GB+ for PyTorch), unpredictable latency, GPU required for reasonable speed, cost prohibitive.
**Do this instead:** Pre-compute everything offline. The backend serves JSON. Its heaviest dependency is `faiss-cpu` (~30MB).

### Anti-Pattern 2: Using a Vector Database for 50k Documents

**What people do:** Deploy Pinecone, Weaviate, or Qdrant to serve embeddings, adding infrastructure cost and complexity.
**Why it's wrong:** 50k vectors at 384 dimensions is ~77MB. This fits in memory on the cheapest deployment tier. A managed vector database costs $25-70/month for a dataset that loads in 2 seconds.
**Do this instead:** Load the FAISS flat index into memory at startup. Query it directly. Zero external dependencies.

### Anti-Pattern 3: Per-Year API Endpoints for Temporal Data

**What people do:** Create `GET /temporal/{neighbourhood}/{year}` and make 210 requests (30 x 7) to load the full dataset, or fetch on each slider tick.
**Why it's wrong:** Latency on slider interaction destroys the "interactive data art" experience. Network requests on every slider tick cause visible lag.
**Do this instead:** Serve the entire temporal dataset as a single JSON response (~300KB). Client loads once, scrubs instantly.

### Anti-Pattern 4: Serving Raw Boundary GeoJSON + Separate Vibe Data

**What people do:** Serve the boundary GeoJSON from one endpoint and vibe scores from another, then join them on the frontend.
**Why it's wrong:** Two requests instead of one, client-side join logic, race conditions on load, harder to cache.
**Do this instead:** Pre-merge vibe data into GeoJSON properties during the export phase. One request, zero client-side joins.

### Anti-Pattern 5: Committing Large Binary Artifacts to Git

**What people do:** `git add faiss.index` (77MB binary file) or commit the SQLite database.
**Why it's wrong:** Bloats repo history permanently. Git LFS adds complexity. Every clone downloads every historical version.
**Do this instead:** Upload to R2. The backend downloads on startup. Keep the repo lean.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Google Places API | Batch fetch with rate limiting, store to SQLite | $200/month free credit ceiling. Fetch reviews + metadata in batches. Monitor quota. |
| Yelp Fusion API | Batch fetch for coverage gaps | 5000 API calls/day limit. Use to fill neighbourhoods underrepresented in Google data. |
| NYC Open Data | One-time GeoJSON download | Commit boundary file to repo. No ongoing integration. |
| Cloudflare R2 | S3-compatible upload (pipeline) + download (backend) | Zero egress fees. Use boto3 with R2 endpoint. |
| Mapbox | GL JS map tiles in frontend | Free tier covers 50k map loads/month. Use style API for dark basemap. |
| Railway/Render | Container hosting for FastAPI | Dockerfile-based deploy. Health check endpoint at /health. |
| Vercel | Static hosting for React frontend | Automatic deploys from git. Edge caching built in. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Pipeline -> Artifacts | File writes (JSON + FAISS binary) | Schema is the contract. Pipeline writes; nothing else does. |
| Artifacts -> Backend | File reads at startup (R2 download) | Backend artifact_loader knows the schema. Fails fast if artifacts missing/malformed. |
| Backend -> Frontend | REST/JSON over HTTPS | OpenAPI spec generated by FastAPI. Frontend typed with generated types. |
| Frontend -> Mapbox | GeoJSON source + style expressions | Data-driven styling uses feature properties for polygon colours. |

## Suggested Build Order

Based on component dependencies:

1. **Pipeline: Data Collection** -- everything downstream depends on having reviews
2. **Pipeline: NLP Core** (embeddings, BERTopic, sentiment) -- depends on collected data
3. **Pipeline: Scoring + Temporal** (vibe scores, temporal buckets, FAISS) -- depends on NLP outputs
4. **Pipeline: Export + GeoJSON Enrichment** -- depends on all pipeline stages
5. **Backend API** -- depends on exported artifacts existing
6. **Frontend Map** -- depends on backend API being available
7. **Frontend Detail Views** (sidebar, time slider, similarity) -- depends on map working
8. **Deployment + Polish** -- depends on everything working locally

Steps 1-4 are sequential (each depends on the previous). Steps 5-6 can overlap if you mock artifacts for the backend during frontend development. Step 7 is parallelizable across features once the map renders.

## Sources

- [Faiss Documentation](https://faiss.ai/) - Official FAISS docs for index types and memory characteristics
- [FAISS Index Memory Discussion](https://github.com/facebookresearch/faiss/issues/2624) - Index sizing for high-dimensional sentence-transformer embeddings
- [BERTopic Best Practices](https://maartengr.github.io/BERTopic/getting_started/best_practices/best_practices.html) - Pre-computed embeddings pattern
- [Hopsworks FTI Pipeline Architecture](https://www.hopsworks.ai/post/mlops-to-ml-systems-with-fti-pipelines) - Feature/Training/Inference pipeline separation pattern
- [Offline vs Online ML Pipelines](https://www.decodingai.com/p/offline-vs-online-ml-pipelines) - Architectural separation of offline and online systems
- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/) - Zero-egress object storage for ML artifacts
- [NYC Open Data Boundaries Map](https://opendata.cityofnewyork.us/projects/boundaries-map/) - NYC boundary data sources
- [NYC Geography Repository](https://github.com/nycehs/NYC_geography) - Simplified GeoJSON boundaries
- [NYC Neighbourhood Boundaries (Jared Lander)](https://www.jaredlander.com/2022/08/new-york-city-neighborhood-boundaries/) - Community neighbourhood definitions
- [Leaflet.timeline](https://github.com/skeate/Leaflet.timeline) - Temporal GeoJSON animation patterns (informed time slider approach)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/) - Startup loading pattern for pre-computed resources

---
*Architecture research for: Neighbourhood Vibe Mapper -- NLP-powered geospatial visualization*
*Researched: 2026-03-16*

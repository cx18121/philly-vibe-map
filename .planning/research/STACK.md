# Technology Stack

**Project:** Neighbourhood Vibe Mapper -- New York City
**Researched:** 2026-03-16

---

## Recommended Stack

### 1. NLP Pipeline (Python)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12 | Runtime | Mature ecosystem, broad library compatibility; 3.13 still has rough edges with some scientific libraries | HIGH |
| sentence-transformers | 5.3.0 | Review embedding | Industry-standard sentence embedding library; wraps HF Transformers with clean APIs for encoding, fine-tuning, and similarity | HIGH |
| `all-MiniLM-L6-v2` | -- | Embedding model | 5x faster than `all-mpnet-base-v2` with minimal quality loss; 384-dim embeddings keep FAISS index small; sufficient for 50k reviews. Use mpnet if quality disappoints during eval | HIGH |
| transformers | 5.3.0 | Model backbone | Required by sentence-transformers and PEFT; v5 is a major refactor with cleaner APIs and weekly minor releases | HIGH |
| BERTopic | 0.17.3 | Topic modelling | Unsupervised topic discovery built on transformer embeddings + HDBSCAN + c-TF-IDF. Supports temporal topics natively (`topics_over_time`), model merging, and HuggingFace Hub push/pull. Interview-defensible over LDA | HIGH |
| umap-learn | 0.5.8 | Dimensionality reduction | BERTopic dependency; reduces embedding dimensions before HDBSCAN clustering. Use `n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine'` as starting point for review data | HIGH |
| hdbscan | (via scikit-learn) | Clustering | BERTopic default clusterer; finds variable-density clusters without specifying k. Use scikit-learn's built-in `sklearn.cluster.HDBSCAN` (integrated since sklearn 1.3) rather than the standalone `hdbscan` package | HIGH |
| faiss-cpu | 1.13.2 | Nearest-neighbour search | Production-grade ANN from Meta; `IndexFlatIP` for 30-neighbourhood corpus (brute-force is fine at this scale), `IndexIVFFlat` if you add more. Pre-build the index offline, serialize with `faiss.write_index()`, load at serving time | HIGH |
| PEFT | 0.18.1 | LoRA fine-tuning | Parameter-efficient fine-tuning for sentiment classifier; LoRA adapters merge into base weights at inference for zero latency overhead | HIGH |
| `distilbert-base-uncased` | -- | Sentiment base model | 40% smaller and 60% faster than BERT-base with 97% of its performance. Fine-tune with LoRA (rank=8, alpha=16) on Yelp Open Dataset star ratings mapped to sentiment labels | MEDIUM |
| NumPy | >=1.26 | Numerical operations | Exponential decay weighting, cosine similarity, temporal bucketing math | HIGH |
| pandas | >=2.2 | Data wrangling | Review deduplication, temporal bucketing, entity resolution pipeline | HIGH |
| scikit-learn | >=1.5 | ML utilities | Cosine similarity, HDBSCAN, preprocessing | HIGH |

**Model selection rationale:**

- **Why `all-MiniLM-L6-v2` over `all-mpnet-base-v2`:** For 50k reviews across 30 neighbourhoods, the quality difference is marginal but the speed difference is 5x. The 384-dim vectors also mean a smaller FAISS index and faster cosine computations. If topic coherence scores are low during eval, upgrade to mpnet -- the pipeline code stays identical.
- **Why LoRA over continued pre-training for sentiment:** LoRA trains in minutes on a single GPU with <1GB VRAM overhead. Continued pre-training on the full Yelp dataset requires significantly more compute and risks catastrophic forgetting. LoRA adapters also merge cleanly into the base model, so the serving artifact is a single model file with zero inference overhead.
- **Why `distilbert-base-uncased` over `roberta-base` for sentiment:** DistilBERT is sufficient for binary/ternary sentiment on review text. RoBERTa would yield marginal gains at 2x the inference cost. For a pre-computed pipeline this doesn't matter at runtime, but it matters for iteration speed during development.

### 2. Backend API (Python)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| FastAPI | 0.135.x | Web framework | Async by default, automatic OpenAPI docs, Pydantic validation, 2x JSON serialization speedup via Rust-backed Pydantic. Perfect for serving pre-computed GeoJSON and time-series endpoints | HIGH |
| Uvicorn | >=0.34 | ASGI server | Production ASGI server for FastAPI; use `--workers 2` for the lightweight serving load | HIGH |
| SQLite | 3.x (stdlib) | Artifact storage | Store pre-computed vibe scores, topic breakdowns, temporal vectors, and representative quotes. Zero-config, single-file database. No PostgreSQL needed -- this is a read-only app serving pre-computed data | HIGH |
| GeoJSON (flat files) | -- | Neighbourhood boundaries | NYC Open Data GeoJSON loaded at startup, enriched with vibe scores in-memory. Serve directly as JSON responses | HIGH |
| orjson | >=3.10 | JSON serialization | 3-10x faster than stdlib json for GeoJSON responses; drops in as a FastAPI response class | HIGH |

**Why SQLite over PostgreSQL:** This app is read-only, serving pre-computed artifacts. There are no concurrent writes, no transactions, no need for a database server. SQLite gives you a single `.db` file that deploys alongside the app -- zero ops overhead. The entire dataset (30 neighbourhoods x 7 years x ~20 metrics) fits comfortably in a single table.

**Why SQLite over DuckDB:** DuckDB excels at analytical queries over large datasets. This app serves pre-aggregated results via simple key lookups (`SELECT * FROM vibe_scores WHERE neighbourhood_id = ?`). SQLite is faster for point queries and has broader deployment support.

**Why SQLite over flat JSON files:** Flat files work for v0 but become unwieldy when you need to query by neighbourhood + year + vibe dimension. SQLite gives you indexed queries with zero additional infrastructure.

### 3. Frontend (TypeScript/React)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| React | 19.2.x | UI framework | Stable, battle-tested, excellent ecosystem for data visualization. Concurrent rendering helps with map + animation workloads | HIGH |
| Vite | 8.0 | Build tool | Sub-second HMR, Rolldown bundler, tiny bundles. Use `@vitejs/plugin-react` v6 (Oxc-based, no Babel dependency) | HIGH |
| TypeScript | 5.7+ | Type safety | Non-negotiable for a project with complex GeoJSON types, vibe score interfaces, and temporal data structures | HIGH |
| MapLibre GL JS | 5.20.x | Map rendering | Open-source (BSD), no API key needed for the library itself, WebGL-accelerated vector tiles. Feature-parity with Mapbox GL JS v1 and growing. Avoids Mapbox's proprietary license and per-map-load pricing | HIGH |
| react-map-gl | 8.1.0 | React wrapper for MapLibre | Maintained by Vis.gl (Uber's viz team). Use `react-map-gl/maplibre` import for proper MapLibre types. Fully controlled component model integrates cleanly with React state | HIGH |
| Framer Motion | 12.36.x | UI animations | Sidebar transitions, topic bar animations, vibe pill entrances, hover effects. `AnimatePresence` for mount/unmount. `layout` prop for smooth reflows. Battle-tested with React 19 concurrent rendering | HIGH |
| Zustand | 5.x | State management | Lightweight (~3KB), minimal boilerplate. Single store for: selected neighbourhood, active vibe, current year, sidebar state. No Redux overhead for an app with simple global state | HIGH |
| Tailwind CSS | 4.2.x | Styling | CSS-native config (no `tailwind.config.js`), 5x faster builds, great for the dark theme. Use `@theme` for custom vibe colors (artsy purple, foodie orange, nightlife blue, etc.) | HIGH |
| D3 (d3-scale, d3-interpolate, d3-color) | 7.x | Color scales and interpolation | **Use D3 modules selectively** -- NOT as a rendering library. `d3-scale` for mapping vibe scores to color ramps, `d3-interpolate` for smooth color transitions during time slider animation, `d3-color` for glow effect color math. Tree-shake to ~15KB | HIGH |

**Map tile provider:** Use a free dark basemap from [CARTO](https://basemaps.cartocdn.com/) (`dark_all` style) or [Stadia Maps](https://stadiamaps.com/) (Alidade Smooth Dark). Both are free-tier compatible and designed for data overlay visualization.

### 4. Visual Effects Strategy

| Effect | Implementation | Why This Approach |
|--------|---------------|-------------------|
| Glowing choropleth fills | MapLibre `fill-extrusion` layer with low height + `fill-color` opacity gradient, OR CSS `filter: drop-shadow()` on the map canvas overlay | Native MapLibre paint properties avoid DOM manipulation; CSS filter is simpler but less precise |
| Colour transitions on vibe switch | `setPaintProperty()` with MapLibre's built-in interpolation (`['interpolate', ['linear'], ...]`) | GPU-accelerated, no React re-renders, 60fps |
| Time slider animation | `requestAnimationFrame` loop updating MapLibre paint properties per frame; Framer Motion for the slider UI itself | Decouples map animation (WebGL) from UI animation (React DOM) for smooth performance |
| Sidebar animations | Framer Motion `motion.div` with `layout`, `AnimatePresence`, spring physics | Declarative, handles enter/exit, works with React 19 |
| Hover pulsing highlights | MapLibre `feature-state` with `['case', ['boolean', ['feature-state', 'hover'], false], ...]` paint expression | Native MapLibre feature, GPU-rendered, no React involvement |

**Why NOT Deck.gl:** Deck.gl adds ~200KB+ bundle size and is designed for rendering millions of points. This app renders 30 neighbourhood polygons. MapLibre's native `fill-extrusion` and paint expressions handle this with zero additional dependencies.

### 5. Deployment

| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| Railway / Render | Backend hosting | Free tier for low-traffic portfolio apps; supports Python + SQLite. Railway has persistent disk for SQLite file | MEDIUM |
| Vercel / Netlify | Frontend hosting | Free tier, automatic deploys from git, CDN edge distribution | HIGH |
| GitHub Actions | CI/CD | Free for public repos; run lint + type-check on push | HIGH |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Embedding model | `all-MiniLM-L6-v2` | `all-mpnet-base-v2` | 5x slower, marginal quality gain for review-length text. Upgrade path is trivial if needed |
| Embedding model | `all-MiniLM-L6-v2` | OpenAI `text-embedding-3-small` | Adds API cost, external dependency, and rate limits. Local model runs offline with zero cost |
| Topic modelling | BERTopic | LDA (gensim) | Bag-of-words, no semantic understanding, not defensible in interview vs. transformer-based approach |
| Sentiment | LoRA fine-tuned DistilBERT | VADER / TextBlob | Rule-based, poor on review slang ("mid", "slaps", "lowkey fire"). Not defensible as "domain-adapted" |
| Sentiment | LoRA fine-tuned DistilBERT | Full fine-tune | 100x more VRAM, slower iteration, marginal quality gain. LoRA is the 2025/2026 standard |
| Sentiment | LoRA on DistilBERT | Continued pre-training + fine-tune | Overkill for sentiment; continued pre-training helps for domain vocab but LoRA captures task adaptation efficiently |
| ANN search | FAISS | Annoy / ScaNN | FAISS is the industry standard, best documented, supports GPU. Annoy is simpler but less flexible. ScaNN requires complex build |
| Backend | FastAPI | Flask | No async, no auto-docs, no Pydantic integration, slower JSON serialization |
| Backend | FastAPI | Django | Massive overkill -- ORM, admin, auth, middleware stack for 4 read-only endpoints |
| Database | SQLite | PostgreSQL | Operational overhead (server process, connection pooling, credentials) for a read-only app with <1MB of structured data |
| Database | SQLite | DuckDB | Columnar storage optimized for analytics scans, not point lookups. SQLite is faster for `WHERE id = ?` |
| Map library | MapLibre GL JS | Mapbox GL JS v2+ | Proprietary license since v2, per-map-load pricing, API key required. MapLibre is BSD-licensed and free |
| Map library | MapLibre GL JS | Deck.gl | Overkill for 30 polygons. ~200KB bundle. Better for millions of points, not choropleth visualization |
| Map library | MapLibre GL JS | Leaflet | No WebGL, no vector tiles, no smooth zoom/rotation. Can't achieve the "data art" visual quality |
| State management | Zustand | Redux Toolkit | Over-engineered for ~5 pieces of global state (selected hood, vibe, year, sidebar, hover) |
| State management | Zustand | Jotai | Atomic model is better for complex interdependent state; this app has simple centralized state |
| Animation | Framer Motion | React Spring | Framer Motion has better React 19 support, `AnimatePresence` for exit animations, larger ecosystem |
| Animation | Framer Motion | GSAP | Imperative API clashes with React's declarative model; adds licensing complexity |
| Frontend framework | Vite + React | Next.js | SSR/SSG adds complexity for zero SEO benefit -- the map is client-rendered. Vite is simpler, faster builds |
| Styling | Tailwind CSS 4 | CSS Modules | Tailwind's utility classes are faster for prototyping; v4's CSS-native config removes build complexity |

---

## Installation

### Python Pipeline

```bash
# Core NLP pipeline
pip install sentence-transformers==5.3.0 \
            bertopic==0.17.3 \
            faiss-cpu==1.13.2 \
            peft==0.18.1 \
            transformers==5.3.0 \
            umap-learn==0.5.8 \
            scikit-learn>=1.5

# Data processing
pip install pandas>=2.2 numpy>=1.26 orjson>=3.10

# Backend
pip install fastapi>=0.135.0 uvicorn>=0.34.0

# Dev tools
pip install ruff pytest httpx
```

### Frontend

```bash
# Scaffold
npm create vite@latest frontend -- --template react-ts

# Core
npm install react-map-gl maplibre-gl framer-motion zustand

# Styling
npm install -D tailwindcss@latest @tailwindcss/vite

# D3 modules (cherry-pick, don't install all of d3)
npm install d3-scale d3-interpolate d3-color
npm install -D @types/d3-scale @types/d3-interpolate @types/d3-color

# Dev tools
npm install -D eslint @eslint/js typescript-eslint prettier
```

---

## Key Version Pins and Compatibility Notes

| Concern | Detail |
|---------|--------|
| sentence-transformers 5.x requires transformers 5.x | Pin both together; don't mix v4 and v5 |
| BERTopic 0.17.x works with sentence-transformers 5.x | Verified via PyPI dependency metadata |
| PEFT 0.18.x requires transformers >=4.45 | Compatible with transformers 5.3.0 |
| react-map-gl 8.x requires maplibre-gl >=4.0 | Use `react-map-gl/maplibre` import path |
| Tailwind CSS 4.x uses CSS-native config | No `tailwind.config.js`; use `@theme` in CSS |
| Vite 8.x requires Node.js >=20.19 | Use Node 22 LTS for best compatibility |
| Framer Motion 12.x works with React 19 | Tested with concurrent rendering |

---

## Sources

- [sentence-transformers PyPI](https://pypi.org/project/sentence-transformers/) - version 5.3.0
- [sentence-transformers GitHub](https://github.com/huggingface/sentence-transformers) - model recommendations
- [BERTopic PyPI](https://pypi.org/project/bertopic/) - version 0.17.3
- [BERTopic Documentation](https://maartengr.github.io/BERTopic/changelog.html) - changelog and features
- [faiss-cpu PyPI](https://pypi.org/project/faiss-cpu/) - version 1.13.2
- [PEFT PyPI](https://pypi.org/project/peft/) - version 0.18.1
- [PEFT Documentation](https://huggingface.co/docs/peft/en/index) - LoRA guide
- [FastAPI PyPI](https://pypi.org/project/fastapi/) - version 0.135.x
- [MapLibre GL JS GitHub](https://github.com/maplibre/maplibre-gl-js) - version 5.20.x
- [react-map-gl npm](https://www.npmjs.com/package/react-map-gl) - version 8.1.0
- [Framer Motion npm](https://www.npmjs.com/package/framer-motion) - version 12.36.x
- [Vite Releases](https://vite.dev/releases) - version 8.0
- [Tailwind CSS v4](https://tailwindcss.com/blog/tailwindcss-v4) - version 4.2.x
- [React Versions](https://react.dev/versions) - version 19.2.x
- [transformers PyPI](https://pypi.org/project/transformers/) - version 5.3.0
- [UMAP Documentation](https://umap-learn.readthedocs.io/) - version 0.5.8

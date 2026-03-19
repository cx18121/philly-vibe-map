# Phase 3: Backend API - Research

**Researched:** 2026-03-19
**Domain:** FastAPI backend serving pre-computed NLP artifacts
**Confidence:** HIGH

## Summary

Phase 3 builds a lightweight FastAPI server that loads pre-computed artifacts into memory at startup and serves them through 4 data endpoints plus a health check. The artifacts are small (total ~3.7 MB for serving artifacts), FAISS queries over 157 6D vectors are sub-millisecond, and all JSON payloads are pre-computed. This is a straightforward read-only API with no database, no ML inference, and no complex business logic.

The phase also requires extending the existing `pipeline/stages/export.py` to produce two new artifacts (`neighbourhood_topics.json` and `review_counts.json`) that the `/neighbourhoods/{id}` endpoint needs. The BERTopic model is already saved with topic representations accessible via `get_topic()` and `get_topic_info()`, and `topic_assignments.json` maps review IDs to topic IDs. The export extension needs to join these with neighbourhood assignments from the database to compute per-neighbourhood topic distributions.

**Primary recommendation:** Use FastAPI with lifespan context manager, Pydantic v2 response models, and `starlette.testclient.TestClient` for synchronous endpoint testing. Keep the app in a single module with a separate routes file -- this is a 5-endpoint API, not a microservices platform.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Backend is **pure artifact-only** -- zero SQLite dependency at runtime
- API-02 requires topic breakdown and review count via two NEW artifacts added to `pipeline/stages/export.py`:
  - `neighbourhood_topics.json` -- per-neighbourhood topic breakdown (top N topics with keywords + review share)
  - `review_counts.json` -- per-neighbourhood total review count
- Backend loads all serving artifacts into memory at startup via FastAPI lifespan event (API-05)
- Raw embeddings (`embeddings.npy`) and `review_ids.npy` are NOT loaded -- pipeline-only
- `GET /neighbourhoods/{id}` returns: vibe archetype scores (6D), dominant vibe + score, top 10 topics with label/keywords/review_share, representative quotes (all archetypes), total review count
- Topics formatted as: `[{"label": "brunch spots", "keywords": ["eggs", "mimosa", "wait"], "review_share": 0.18}, ...]`
- `GET /neighbourhoods` returns enriched GeoJSON FeatureCollection directly, Content-Type: `application/geo+json`
- CORS: Allow `*` (wildcard) -- will be locked in Phase 6 via env var
- Artifact directory via `ARTIFACTS_DIR` env var (default: `data/output/artifacts`)
- Dockerfile is a deliverable of this phase
- `GET /health` endpoint: `{"status": "ok", "artifacts_loaded": true/false}`

### Claude's Discretion
- Exact FastAPI app structure (router organization, module layout under `api/` or `backend/`)
- Uvicorn startup config (port, workers, reload flag)
- Response model / Pydantic schema design
- Error handling for invalid neighbourhood IDs (404 shape)
- FAISS k parameter validation (clamp to neighbourhood count)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | `GET /neighbourhoods` returns enriched GeoJSON FeatureCollection with vibe scores, dominant vibe, and sentiment scores in feature properties | Enriched GeoJSON artifact exists (1.9 MB, 159 features, 157 enriched). Serve directly with `application/geo+json` Content-Type via `Response` class. |
| API-02 | `GET /neighbourhoods/{id}` returns per-neighbourhood detail: topic breakdown, vibe archetype scores, representative quotes, review count | Requires TWO NEW artifacts from export stage. BERTopic model has 880 topics; `topic_assignments.json` has 965K assignments. Export extension joins assignments with DB neighbourhood mapping to compute per-neighbourhood distributions. |
| API-03 | `GET /temporal` returns full temporal drift dataset (all neighbourhoods x all years x vibe vectors) as single JSON payload | `temporal_series.json` (584 KB) already in exact needed format: `{nid: {year: {archetype: score}}}`. 157 neighbourhoods x 16 years (2007-2022). Serve directly. |
| API-04 | `GET /similar?id={id}&k={n}` returns k nearest-neighbour neighbourhoods via FAISS query | FAISS IndexFlatIP with 157 vectors, dim=6. Query pattern verified: `faiss.normalize_L2(vec); D, I = index.search(vec, k+1)`. Sub-millisecond. Must exclude self from results and map indices via `faiss_id_map.json`. |
| API-05 | Backend loads all artifacts into memory at startup via FastAPI lifespan event -- zero ML model loading | All serving artifacts total ~3.7 MB. Use `@asynccontextmanager` lifespan function. FAISS index loaded via `faiss.read_index()`. JSON artifacts via `json.load()`. Store in `app.state`. |
| API-06 | All endpoints return responses in under 100ms (FAISS query included) | Artifacts are tiny and in-memory. FAISS search over 157 6D vectors is sub-millisecond. JSON serialization of largest payload (GeoJSON, 1.9 MB) is the only concern -- verify in tests. |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.135.1 | ASGI web framework | Already installed. Lifespan events, Pydantic integration, auto OpenAPI docs. |
| uvicorn | 0.27.1 | ASGI server | Already installed. Standard FastAPI companion. |
| pydantic | 2.12.5 | Response models, validation | Already installed (FastAPI dependency). V2 with model_validator. |
| faiss-cpu | 1.13.2 | Similarity search at serving time | Already installed. Only runtime dependency beyond standard lib for serving. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | 0.28.1 | TestClient transport for FastAPI | Already installed. Required by `starlette.testclient.TestClient`. |
| pytest | 9.0.2 | Test runner | Already installed and configured. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| fastapi | Flask | No async, no auto-docs, no Pydantic integration -- worse in every way for this use case |
| uvicorn | gunicorn+uvicorn | Overkill for single-process artifact serving with 157 neighbourhoods |

**Installation:** No new packages needed. All dependencies already installed.

## Architecture Patterns

### Recommended Project Structure
```
backend/
    __init__.py
    app.py           # FastAPI app, lifespan, CORS config
    routes.py        # All endpoint handlers
    schemas.py       # Pydantic response models
    loader.py        # Artifact loading logic
    config.py        # Settings (ARTIFACTS_DIR, port, etc.)
Dockerfile
```

**Rationale:** 5 endpoints do not justify a `routers/` directory with separate files per resource. A single `routes.py` keeps everything discoverable. The `loader.py` separation is important because the export extension (new artifacts) and the backend loader both need to agree on artifact formats -- separating loading logic makes this contract explicit.

### Pattern 1: Lifespan Context Manager
**What:** FastAPI's modern startup/shutdown pattern replacing deprecated `on_event`
**When to use:** Always for this app -- all artifacts loaded at startup
**Example:**
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load all artifacts into app.state
    app.state.geojson = load_geojson(settings.artifacts_dir)
    app.state.vibe_scores = load_json(settings.artifacts_dir / "vibe_scores.json")
    app.state.temporal = load_json(settings.artifacts_dir / "temporal_series.json")
    app.state.quotes = load_json(settings.artifacts_dir / "representative_quotes.json")
    app.state.topics = load_json(settings.artifacts_dir / "neighbourhood_topics.json")
    app.state.review_counts = load_json(settings.artifacts_dir / "review_counts.json")
    app.state.faiss_index = faiss.read_index(str(settings.artifacts_dir / "faiss_index.bin"))
    app.state.faiss_id_map = load_json(settings.artifacts_dir / "faiss_id_map.json")
    app.state.artifacts_loaded = True
    yield
    # Shutdown: nothing to clean up

app = FastAPI(lifespan=lifespan)
```
Source: FastAPI official docs (lifespan events)

### Pattern 2: Custom Response for GeoJSON
**What:** Return pre-loaded GeoJSON with correct Content-Type
**When to use:** API-01 endpoint
**Example:**
```python
from fastapi.responses import Response
import json

@router.get("/neighbourhoods")
def get_neighbourhoods(request: Request):
    return Response(
        content=json.dumps(request.app.state.geojson),
        media_type="application/geo+json",
    )
```
**Optimization note:** Pre-serialize the GeoJSON to a string at startup to avoid re-serializing on every request. This is the largest payload (1.9 MB) and serialization could add latency.

### Pattern 3: FAISS Query with Self-Exclusion
**What:** Query FAISS for k+1 results, drop self from results
**When to use:** API-04 similarity endpoint
**Example:**
```python
import faiss
import numpy as np

def find_similar(nid: str, k: int, app_state) -> list[dict]:
    # Build reverse map: nid -> faiss integer index
    reverse_map = {v: int(k_) for k_, v in app_state.faiss_id_map.items()}
    if nid not in reverse_map:
        raise ValueError(f"Unknown neighbourhood: {nid}")

    idx = reverse_map[nid]
    vibe_scores = app_state.vibe_scores[nid]
    archetype_order = ["artsy", "foodie", "nightlife", "family", "upscale", "cultural"]
    query = np.array([[vibe_scores[a] for a in archetype_order]], dtype=np.float32)
    faiss.normalize_L2(query)

    D, I = app_state.faiss_index.search(query, k + 1)
    results = []
    for dist, faiss_idx in zip(D[0], I[0]):
        result_nid = app_state.faiss_id_map[str(faiss_idx)]
        if result_nid == nid:
            continue
        results.append({"neighbourhood_id": result_nid, "similarity": float(dist)})
    return results[:k]
```

### Pattern 4: Pre-computed Reverse Lookups at Startup
**What:** Build lookup dictionaries during lifespan so endpoints do O(1) lookups
**When to use:** Neighbourhood ID validation, FAISS reverse mapping
**Example:**
```python
# During lifespan:
app.state.valid_nids = set(app.state.vibe_scores.keys())
app.state.faiss_reverse = {v: int(k) for k, v in app.state.faiss_id_map.items()}
```

### Anti-Patterns to Avoid
- **Re-serializing GeoJSON per request:** The 1.9 MB GeoJSON should be pre-serialized to bytes at startup and returned directly. Do not call `json.dumps()` on every request.
- **Loading BERTopic model in backend:** The model is 100+ MB with ML dependencies. The backend must only load pre-computed JSON artifacts.
- **Using SQLite at runtime:** All data is in JSON artifacts. No database connection in the serving layer.
- **`on_event("startup")` decorator:** Deprecated in FastAPI. Use lifespan context manager.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CORS | Custom middleware | `fastapi.middleware.cors.CORSMiddleware` | One-liner setup, handles preflight correctly |
| Request validation | Manual query param parsing | Pydantic models + FastAPI dependency injection | Auto-validates, auto-documents in OpenAPI |
| OpenAPI docs | Manual API documentation | FastAPI auto-generated `/docs` | Free Swagger UI, good for portfolio demo |
| GeoJSON serialization | Custom serializer | `json.dumps` with pre-serialized bytes | GeoJSON is already valid JSON |
| Environment config | Manual `os.environ` calls | Pydantic `BaseSettings` | Type validation, `.env` file support, defaults |

**Key insight:** This is a dead-simple read-only API. The complexity is in getting artifacts right, not in the web framework. Resist over-engineering the API layer.

## Common Pitfalls

### Pitfall 1: GeoJSON Content-Type
**What goes wrong:** FastAPI default `JSONResponse` uses `application/json`, not `application/geo+json`
**Why it happens:** FastAPI auto-wraps dict returns in JSONResponse
**How to avoid:** Return `Response(content=..., media_type="application/geo+json")` explicitly
**Warning signs:** Frontend GeoJSON parsing works but Content-Type header is wrong

### Pitfall 2: FAISS Index Returning Self in Results
**What goes wrong:** Querying FAISS for a neighbourhood returns itself as the top result (similarity = 1.0)
**Why it happens:** The query vector is in the index. IndexFlatIP has no built-in self-exclusion.
**How to avoid:** Query for k+1, filter out the query neighbourhood ID, take first k
**Warning signs:** First result always has similarity ~1.0

### Pitfall 3: FAISS Vector Not L2-Normalized Before Query
**What goes wrong:** Inner product distances are meaningless without normalization
**Why it happens:** The index was built with `faiss.normalize_L2()` on the data vectors. Query vectors must also be normalized.
**How to avoid:** Always call `faiss.normalize_L2(query_vec)` before `index.search()`
**Warning signs:** Similarity scores > 1.0 or nonsensical rankings

### Pitfall 4: 159 GeoJSON Features vs 157 Neighbourhoods with Data
**What goes wrong:** 2 GeoJSON features have no vibe data (no `vibe_scores` in properties)
**Why it happens:** 159 Philadelphia neighbourhood boundaries exist, but only 157 had Yelp reviews
**How to avoid:** The GeoJSON endpoint serves all 159 features (with nulls for 2). The detail endpoint `/neighbourhoods/{id}` should 404 for IDs not in `vibe_scores.json`.
**Warning signs:** Frontend crashes on null vibe_scores for 2 neighbourhoods

### Pitfall 5: Neighbourhood ID Type Mismatch
**What goes wrong:** Route parameter is string but might not match artifact keys
**Why it happens:** Neighbourhood IDs are zero-padded strings ("001", "002") in all artifacts. URL path param must match this format.
**How to avoid:** Validate that the path parameter exists in `vibe_scores` keys. Consider accepting both "1" and "001" by zero-padding in the endpoint.
**Warning signs:** 404s for valid neighbourhoods when ID format differs

### Pitfall 6: Topic Label Construction from BERTopic
**What goes wrong:** BERTopic topic representations are `[(word, score), ...]` tuples, not human-readable labels
**Why it happens:** BERTopic stores c-TF-IDF word scores, not pre-made labels
**How to avoid:** In the export extension, construct labels by joining top 3-4 keywords: `" ".join([w for w, _ in topic_rep[:3]])`
**Warning signs:** Topic labels showing as raw tuples or None

### Pitfall 7: Export Stage Needs Database but Backend Does Not
**What goes wrong:** Confusion about when SQLite is needed
**Why it happens:** The NEW export artifacts (`neighbourhood_topics.json`, `review_counts.json`) require joining `topic_assignments.json` with the DB to get `business_id -> neighbourhood_id` mapping. But the backend never touches SQLite.
**How to avoid:** The export stage extension runs as part of the pipeline (has DB access). The backend only reads the resulting JSON files.
**Warning signs:** Backend importing sqlite3

## Code Examples

### Export Extension: neighbourhood_topics.json Generation
```python
# In pipeline/stages/export.py -- new sub-stage
def _build_neighbourhood_topics(
    db_path: str,
    artifacts_dir: Path,
) -> dict:
    """Compute per-neighbourhood topic distributions from topic_assignments.json.

    Joins topic assignments (review_id -> topic_id) with DB
    (review rowid -> business -> neighbourhood) to get per-neighbourhood distributions.
    """
    # Load topic assignments: {review_rowid_str: topic_id}
    with open(artifacts_dir / "topic_assignments.json") as f:
        assignments = json.load(f)

    # Load BERTopic model for topic representations (keywords)
    from bertopic import BERTopic
    topic_model = BERTopic.load(str(artifacts_dir / "bertopic_model"))

    # Get review -> neighbourhood mapping from DB
    conn = sqlite3.connect(db_path)
    review_to_nid = {}
    for row in conn.execute("""
        SELECT r.rowid, b.neighbourhood_id
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
    """):
        review_to_nid[str(row[0])] = row[1]
    conn.close()

    # Count topics per neighbourhood
    from collections import Counter
    nid_topic_counts: dict[str, Counter] = {}
    nid_review_totals: dict[str, int] = Counter()

    for rid, tid in assignments.items():
        nid = review_to_nid.get(rid)
        if nid is None or tid == -1:  # skip outliers
            continue
        if nid not in nid_topic_counts:
            nid_topic_counts[nid] = Counter()
        nid_topic_counts[nid][tid] += 1
        nid_review_totals[nid] += 1

    # Build output: top 10 topics per neighbourhood
    result = {}
    for nid in sorted(nid_topic_counts.keys()):
        counts = nid_topic_counts[nid]
        total = nid_review_totals[nid]
        top_topics = counts.most_common(10)
        topics_list = []
        for topic_id, count in top_topics:
            rep = topic_model.get_topic(topic_id)
            if not rep:
                continue
            keywords = [w for w, _ in rep[:5]]
            label = " ".join(keywords[:3])
            topics_list.append({
                "label": label,
                "keywords": keywords,
                "review_share": round(count / total, 4),
            })
        result[nid] = topics_list

    with open(artifacts_dir / "neighbourhood_topics.json", "w") as f:
        json.dump(result, f, indent=2)
    return result
```

### Export Extension: review_counts.json Generation
```python
def _build_review_counts(db_path: str, artifacts_dir: Path) -> dict:
    """Count total reviews per neighbourhood."""
    conn = sqlite3.connect(db_path)
    counts = {}
    for row in conn.execute("""
        SELECT b.neighbourhood_id, COUNT(*)
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
        GROUP BY b.neighbourhood_id
    """):
        counts[row[0]] = row[1]
    conn.close()

    with open(artifacts_dir / "review_counts.json", "w") as f:
        json.dump(counts, f, indent=2)
    return counts
```

### FastAPI TestClient Pattern
```python
# tests/test_api.py
from starlette.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_neighbourhoods_geojson():
    resp = client.get("/neighbourhoods")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/geo+json"
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 157

def test_similar_endpoint():
    resp = client.get("/similar", params={"id": "001", "k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    assert all("neighbourhood_id" in n for n in data)
    assert all("similarity" in n for n in data)
    # Self should not be in results
    assert all(n["neighbourhood_id"] != "001" for n in data)
```

### Pydantic Settings for Config
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    artifacts_dir: Path = Path("data/output/artifacts")
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_prefix": ""}  # ARTIFACTS_DIR, HOST, PORT
```

**Note:** `pydantic-settings` is a separate package from `pydantic` since v2. May need `pip install pydantic-settings`.

### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY backend/ backend/
COPY data/output/artifacts/ data/output/artifacts/

ENV ARTIFACTS_DIR=data/output/artifacts
EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` | `lifespan` context manager | FastAPI 0.93+ (2023) | Deprecated decorator pattern; use lifespan |
| Pydantic v1 `BaseSettings` | `pydantic-settings` separate package | Pydantic v2 (2023) | Must `pip install pydantic-settings` |
| `TestClient` from `fastapi.testclient` | `starlette.testclient.TestClient` | Always was Starlette's | Both imports work; Starlette is canonical |

**Deprecated/outdated:**
- `@app.on_event("startup")`/`@app.on_event("shutdown")`: Use lifespan context manager
- `from pydantic import BaseSettings`: Moved to `pydantic-settings` in Pydantic v2

## Open Questions

1. **pydantic-settings availability**
   - What we know: Pydantic v2 moved BaseSettings to a separate `pydantic-settings` package
   - What's unclear: Whether it's already installed in this environment
   - Recommendation: Check at plan time; if not installed, add to requirements. Alternatively, use a simple dataclass + `os.environ` -- this is a 3-setting app.

2. **Pre-serialized GeoJSON bytes vs on-demand serialization**
   - What we know: GeoJSON is 1.9 MB. `json.dumps` on a 1.9 MB dict takes ~10-20ms depending on CPU.
   - What's unclear: Whether this matters for the 100ms target
   - Recommendation: Pre-serialize to bytes at startup. Zero-cost per request.

3. **Neighbourhood ID zero-padding in URL**
   - What we know: All artifact keys are zero-padded 3-digit strings ("001", "002", etc.)
   - What's unclear: Whether the URL should accept "1" and auto-pad to "001"
   - Recommendation: Accept raw integer in URL, zero-pad to 3 digits internally: `nid = str(id).zfill(3)`

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pytest.ini` (existing) |
| Quick run command | `pytest tests/test_api.py -x -q` |
| Full suite command | `pytest tests/ -x -q -m "not slow"` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | GET /neighbourhoods returns GeoJSON FeatureCollection with correct Content-Type and 157+ enriched features | integration | `pytest tests/test_api.py::test_neighbourhoods_geojson -x` | No -- Wave 0 |
| API-02 | GET /neighbourhoods/{id} returns topic breakdown, vibe scores, quotes, review count | integration | `pytest tests/test_api.py::test_neighbourhood_detail -x` | No -- Wave 0 |
| API-03 | GET /temporal returns all neighbourhoods x years x vibe vectors | integration | `pytest tests/test_api.py::test_temporal -x` | No -- Wave 0 |
| API-04 | GET /similar?id=001&k=5 returns 5 nearest neighbours excluding self | integration | `pytest tests/test_api.py::test_similar -x` | No -- Wave 0 |
| API-05 | Server starts via lifespan, loads all artifacts into app.state | integration | `pytest tests/test_api.py::test_health -x` | No -- Wave 0 |
| API-06 | All endpoints respond in under 100ms | integration | `pytest tests/test_api.py::test_response_times -x` | No -- Wave 0 |

### Additional Tests Needed
| Behavior | Test Type | Automated Command |
|----------|-----------|-------------------|
| Export extension produces neighbourhood_topics.json | unit | `pytest tests/test_export_extension.py::test_neighbourhood_topics -x` |
| Export extension produces review_counts.json | unit | `pytest tests/test_export_extension.py::test_review_counts -x` |
| Invalid neighbourhood ID returns 404 | integration | `pytest tests/test_api.py::test_invalid_neighbourhood_404 -x` |
| FAISS k parameter validation (k > total, k < 1) | integration | `pytest tests/test_api.py::test_similar_k_validation -x` |

### Sampling Rate
- **Per task commit:** `pytest tests/test_api.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q -m "not slow"`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_api.py` -- covers API-01 through API-06 (all endpoint tests)
- [ ] `tests/test_export_extension.py` -- covers new artifact generation
- [ ] `pip install pydantic-settings` -- if not already available

## Key Data Facts (Verified from Artifacts)

These numbers are verified from the actual artifacts on disk:

| Fact | Value | Source |
|------|-------|--------|
| Neighbourhoods with vibe data | 157 | `vibe_scores.json` |
| GeoJSON features total | 159 | `enriched_geojson.geojson` |
| GeoJSON features enriched | 157 | `enriched_geojson.geojson` (2 without vibe data) |
| Temporal years | 2007-2022 (16 years) | `temporal_series.json` |
| Vibe archetypes | 6: artsy, foodie, nightlife, family, upscale, cultural | All artifacts |
| Quotes per archetype per neighbourhood | 5 | `representative_quotes.json` |
| FAISS index vectors | 157, dim=6, IndexFlatIP | `faiss_index.bin` |
| Total topic assignments | 965,269 | `topic_assignments.json` |
| Unique topics (excl. outliers) | 880 | `topic_assignments.json` |
| Outlier assignments | 12 | `topic_assignments.json` |
| Total serving artifact size | ~3.7 MB | All serving JSON + FAISS binary |
| Neighbourhood ID format | Zero-padded 3-digit string ("001") | All artifacts |
| BERTopic topic representation | List of (word, score) tuples | `bertopic_model` via `get_topic()` |

## Sources

### Primary (HIGH confidence)
- **Actual artifact files on disk** -- all data shapes, sizes, and formats verified by reading real files
- **`pipeline/stages/export.py`** -- current export stage code, shows existing patterns
- **`pipeline/stages/topic_model.py`** -- BERTopic model saving format, topic assignment structure
- **`pip show` output** -- verified installed package versions (FastAPI 0.135.1, Pydantic 2.12.5, uvicorn 0.27.1, faiss-cpu 1.13.2, httpx 0.28.1, pytest 9.0.2)
- **FAISS query test** -- verified search pattern returns correct results with similarity scores

### Secondary (MEDIUM confidence)
- FastAPI lifespan pattern -- from FastAPI official documentation, verified against installed version
- Pydantic v2 BaseSettings migration -- confirmed separate `pydantic-settings` package

### Tertiary (LOW confidence)
- GeoJSON serialization latency estimate (~10-20ms for 1.9 MB) -- rough estimate, should verify in test

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all packages already installed and verified
- Architecture: HIGH -- straightforward read-only API with well-understood patterns
- Pitfalls: HIGH -- verified from actual artifact data (ID formats, feature counts, FAISS behavior)
- Export extension: MEDIUM -- BERTopic `get_topic()` API verified, but join logic is planned not tested

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable domain, no moving targets)

# Phase 1: Data Foundation - Research

**Researched:** 2026-03-16
**Domain:** Data ingestion — Yelp Open Dataset, GeoPandas spatial join, NYC NTA boundaries, SQLite
**Confidence:** MEDIUM (technical stack HIGH; Yelp NYC coverage LOW — requires empirical validation)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Primary source: Yelp Open Dataset only** — free academic dataset (~6.9M reviews, covers to ~mid-2024). No Google Places API, no Yelp Fusion API.
- Cross-platform deduplication (DATA-02) is dropped — single-source dataset has no cross-platform duplicates.
- **Coverage validation is the first pipeline step**: count NYC reviews before building the full schema.
- **Flexible review target**: if fewer than 50k NYC reviews exist, lower the target rather than supplementing with paid API.
- **NTA (Neighbourhood Tabulation Areas) geometry** from NYC Open Data (2020 NTAs) as authoritative boundary source — official, clean GeoJSON, WGS84.
- **Full Manhattan + Brooklyn coverage**: all NTAs from both boroughs, no gaps.
- **Point-in-polygon only** via GeoPandas `sjoin()` — do not trust Yelp's neighbourhood label field.
- **Streaming parse**: parse review NDJSON line-by-line — never load the full file into memory.
- **Idempotent writes**: use `INSERT OR IGNORE` into SQLite.
- **Static file download** — no API calls, no checkpoint/resume system needed.

### Claude's Discretion
- Exact SQLite schema column types and indices (beyond required fields in DATA-03)
- How to handle Yelp records with missing lat/lng (log and skip vs. attempt geocoding)
- Progress logging format and granularity

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | Collect 50k+ reviews spanning 2019–2025 from Yelp Open Dataset across Manhattan and Brooklyn neighbourhoods | Coverage validation step; flexible target if NYC count is below 50k |
| DATA-02 | Deduplication — superseded by Yelp-only decision; no cross-platform duplicates to resolve | `INSERT OR IGNORE` on `review_id` primary key handles intra-dataset duplicates |
| DATA-03 | Each stored review includes: text, timestamp, business name, business lat/lng, source platform, neighbourhood assignment | Schema design section; GeoPandas sjoin adds neighbourhood_id column |
| DATA-04 | Fetch official NYC neighbourhood boundary GeoJSON from NYC Open Data (NTA) and reproject to WGS84 | NTA dataset is already in WGS84; direct GeoJSON export URL documented |
| DATA-05 | Produce data quality report (review count by neighbourhood and by year) | Simple SQL GROUP BY query after ingestion |
| DATA-06 | Raw reviews stored in SQLite with source-agnostic unified schema (platform-specific fields as JSON) | Schema and PRAGMA settings documented |
</phase_requirements>

---

## Summary

The Yelp Open Dataset is a static, newline-delimited JSON archive (~8.65 GB uncompressed for the review file) covering approximately 6.9 million reviews across **8 metropolitan areas: Atlanta, Austin, Boston, Boulder, Columbus, Orlando, Portland, and Vancouver**. **New York City is not one of the covered metropolitan areas.** This is the most critical finding of this research and must be addressed before building out the full data pipeline. Specifically, a user who queried the dataset found "only one row labeled 'New York' city and 22 rows labeled 'NY' state" — effectively zero usable NYC coverage.

The planner must design the first wave of work around a **mandatory coverage probe**: load the business file, filter by lat/lng bounding box for Manhattan and Brooklyn, and count the results before building any schema or pipeline logic. The CONTEXT.md already anticipates this contingency and mandates lowering the review target rather than using a paid API. However, if the count is so low as to make the project unviable (e.g., fewer than a few thousand reviews across all years), the planner must surface a decision point for the user.

Assuming adequate coverage is confirmed, the remaining technical stack is well-understood and low-risk: GeoPandas 1.1.x with `sjoin(predicate='within')` is the standard approach for point-in-polygon, the 2020 NTA GeoJSON is directly downloadable from NYC Open Data in WGS84, and SQLite with WAL mode and `executemany` batch inserts is appropriate for this write-once workload.

**Primary recommendation:** Make Wave 0 a standalone coverage probe script that produces a count report. Gate all subsequent waves on that report. Do not design schema or pipeline until coverage is confirmed.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| geopandas | 1.1.3 | Spatial join of Yelp business points to NTA polygons | Industry standard for GeoPandas Python; vectorised R-tree sjoin |
| shapely | (bundled with geopandas) | Geometry types for points and polygons | Required by geopandas; no alternative |
| pyproj | (bundled with geopandas) | CRS reprojection | Required by geopandas |
| sqlite3 | stdlib | Persistent review store | Zero-dependency, appropriate for batch/offline pipeline |
| orjson | latest | Fast NDJSON line parsing | 2-4x faster than stdlib json on loads(); material for 8.65 GB file |
| tqdm | latest | Progress bar for streaming parse | Minimal overhead; visibility into long-running process |
| requests | latest | Download NTA GeoJSON from NYC Open Data | Standard HTTP; only one download needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.x | Test framework for validation tests | Unit tests for spatial join logic, schema validation |
| pandas | (bundled with geopandas) | DataFrame manipulation for quality report | GROUP BY equivalent for review counts |
| pyogrio | (bundled with geopandas) | Read/write GeoJSON | Faster than fiona for this use case |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| orjson | stdlib json | stdlib is 2-4x slower on loads; material for 8.65 GB file |
| sqlite3 | PostgreSQL + PostGIS | PostGIS has native spatial types but requires a running server; overkill for a one-time batch pipeline |
| geopandas sjoin | shapely loop | Loop is O(n*m); sjoin uses R-tree index; sjoin is 100-1000x faster for large point sets |

**Installation:**
```bash
pip install geopandas orjson tqdm requests pytest
```
Note: On some Linux systems, install geopandas via conda to avoid GDAL binary issues:
```bash
conda install -c conda-forge geopandas
```

---

## Architecture Patterns

### Recommended Project Structure
```
data/
├── raw/                        # Yelp NDJSON files (gitignored — large)
│   ├── yelp_academic_dataset_business.json
│   └── yelp_academic_dataset_review.json
├── boundaries/
│   └── nta_2020_manhattan_brooklyn.geojson   # Committed artifact
└── output/
    ├── reviews.db              # SQLite output
    └── data_quality_report.json

scripts/
├── 00_probe_coverage.py        # Wave 0: count NYC records — GATE
├── 01_download_boundaries.py   # Download + filter NTA GeoJSON
├── 02_build_schema.py          # Create SQLite schema
├── 03_assign_neighbourhoods.py # GeoPandas sjoin businesses -> NTA
├── 04_ingest_reviews.py        # Stream NDJSON -> SQLite
└── 05_quality_report.py        # GROUP BY neighbourhood + year

tests/
├── conftest.py
├── test_spatial_join.py
└── test_schema.py
```

### Pattern 1: Streaming NDJSON Parse with Batch Inserts
**What:** Open the review NDJSON file, parse line-by-line with orjson, accumulate rows into a list of tuples, and flush to SQLite with `executemany` every N rows.
**When to use:** Any file > 1 GB where loading to memory would OOM.
**Example:**
```python
# Source: SQLite forum + orjson docs
import orjson
import sqlite3

BATCH_SIZE = 10_000

def ingest_reviews(ndjson_path: str, db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    batch = []
    with open(ndjson_path, "rb") as f:
        for line in f:
            record = orjson.loads(line)
            batch.append((
                record["review_id"],
                record["business_id"],
                record["text"],
                record["stars"],
                record["date"],
                record.get("useful"),
                record.get("funny"),
                record.get("cool"),
            ))
            if len(batch) >= BATCH_SIZE:
                conn.executemany(
                    "INSERT OR IGNORE INTO reviews VALUES (?,?,?,?,?,?,?,?)",
                    batch
                )
                conn.commit()
                batch.clear()
    if batch:
        conn.executemany(
            "INSERT OR IGNORE INTO reviews VALUES (?,?,?,?,?,?,?,?)",
            batch
        )
        conn.commit()
    conn.close()
```

### Pattern 2: GeoPandas Point-in-Polygon Spatial Join
**What:** Build a GeoDataFrame of business lat/lng points, load NTA polygon GeoDataFrame, call `sjoin(predicate='within', how='left')` to assign each business to its NTA.
**When to use:** Any point-in-polygon assignment at scale (here: ~150k businesses against 74 NTA polygons).
**Example:**
```python
# Source: geopandas.org/en/stable/docs/reference/api/geopandas.sjoin.html
import geopandas as gpd
from shapely.geometry import Point

def assign_neighbourhoods(businesses_df, nta_gdf):
    # Both must be in the same CRS — NTA GeoJSON is WGS84 (EPSG:4326)
    gdf_businesses = gpd.GeoDataFrame(
        businesses_df,
        geometry=gpd.points_from_xy(
            businesses_df["longitude"],
            businesses_df["latitude"]
        ),
        crs="EPSG:4326"
    )
    # left join: businesses without a matching NTA get NaN nta_id
    joined = gpd.sjoin(
        gdf_businesses,
        nta_gdf[["NTACode", "NTAName", "geometry"]],
        how="left",
        predicate="within"
    )
    return joined
```
Key: `predicate='within'` is correct for "point inside polygon". `predicate='intersects'` can produce duplicates for points exactly on shared boundaries.

### Pattern 3: NTA GeoJSON Download and Borough Filter
**What:** Download the full 5-borough NTA GeoJSON from NYC Open Data, then filter to Manhattan (BoroCode 1) and Brooklyn (BoroCode 3) only. Commit the filtered file as a project artifact.
**When to use:** Phase setup — download once, commit, never re-download.
**Example:**
```python
import requests
import geopandas as gpd
import io

GEOJSON_URL = (
    "https://data.cityofnewyork.us/api/geospatial/9nt8-h7nd"
    "?method=export&type=GeoJSON"
)

def download_nta_boundaries(output_path: str) -> gpd.GeoDataFrame:
    resp = requests.get(GEOJSON_URL, timeout=60)
    resp.raise_for_status()
    gdf = gpd.read_file(io.BytesIO(resp.content))
    # Filter to Manhattan (1) and Brooklyn (3) only
    mask = gdf["BoroCode"].isin(["1", "3"])  # Socrata exports as str
    filtered = gdf[mask].copy()
    filtered.to_file(output_path, driver="GeoJSON")
    return filtered
```

### Anti-Patterns to Avoid
- **Loading full NDJSON into memory:** `json.load(f)` on an 8.65 GB file will OOM on most machines. Always iterate line-by-line.
- **Row-by-row INSERT in a loop:** Each `conn.execute("INSERT...")` without batching creates one transaction per row. With 6.9M reviews, this is ~100x slower than `executemany` with batched commits.
- **Trusting Yelp's neighbourhood field:** The `neighborhood` attribute in business.json is user-generated text, inconsistent and often blank. Always use the spatial join result.
- **Using `predicate='intersects'` instead of `predicate='within'`:** Points exactly on a shared boundary will match both polygons and produce duplicate rows. Use `'within'`.
- **Not checking CRS before sjoin:** If business points and NTA polygons are in different CRS, the join silently returns wrong results or NaN. Always assert `gdf.crs == nta_gdf.crs` before joining.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Point-in-polygon at scale | Loop over polygons with shapely | `geopandas.sjoin()` | sjoin uses R-tree spatial index; loop is O(n*m) |
| CRS reprojection | Manual coordinate math | `gdf.to_crs("EPSG:4326")` | Pyproj handles datum shifts, ellipsoid transforms correctly |
| Fast JSON parsing | Custom C extension or regex | `orjson.loads()` | orjson is already a Rust-backed C extension |
| Progress display | Print every N rows | `tqdm` | tqdm handles ETA, rate, iteration count with zero code |
| SQLite duplicate handling | SELECT then INSERT logic | `INSERT OR IGNORE` | Single atomic statement; SELECT+INSERT is a TOCTOU race |

**Key insight:** Spatial operations have subtle correctness edge cases (boundary ties, CRS mismatch, ring orientation). GeoPandas encapsulates all of these. Custom implementations get the edge cases wrong.

---

## Critical Finding: Yelp Open Dataset NYC Coverage

**CONFIDENCE: HIGH (multiple sources confirm)**

The Yelp Open Dataset covers **8 metropolitan areas**: Atlanta GA, Austin TX, Boston MA, Boulder CO, Columbus OH, Orlando FL, Portland OR, and Vancouver Canada. **New York City is not included.**

Evidence:
- A user querying the dataset for NYC healthcare businesses found "only one row labeled 'New York' city and 22 rows labeled 'NY' state" (GitHub issue #47 on Yelp/dataset-examples)
- The 8-city list is consistent across multiple independent sources and confirmed by Yelp's blog posts
- The April 2024 version (6.99M reviews, 150k businesses) shows the same 8-city composition

**Implication for Phase 1:**
The coverage probe (first task) will almost certainly find near-zero NYC reviews. The CONTEXT.md anticipates this with "flexible review target" — but the planner needs to design a decision gate:

- If probe finds > 10k NYC reviews: proceed with flexible target
- If probe finds < 1k NYC reviews: the dataset is functionally empty for this project; surface to user for decision (alternative data sources, change of project scope)

**Alternative data sources (for planner awareness — user decision required before any pivot):**
- NYC Health + Hospitals reviews — public but thin data
- Foursquare Open Places — has NYC data, different schema
- Google Maps reviews via Common Crawl — complex, not clean
- The user could manually expand the project city if they have access to a different city in the Yelp dataset (e.g., Boston has strong Yelp coverage)

---

## Common Pitfalls

### Pitfall 1: Yelp NDJSON Not Valid JSON Per File
**What goes wrong:** Attempting `json.load(f)` on the entire review file fails with a parse error — the file is not a JSON array, it's one JSON object per line (newline-delimited JSON / NDJSON).
**Why it happens:** Common misconception that `.json` files always contain a single top-level value.
**How to avoid:** Always iterate `for line in f: record = orjson.loads(line)`.
**Warning signs:** `json.JSONDecodeError: Extra data after JSON` or immediate memory exhaustion.

### Pitfall 2: CRS Mismatch in Spatial Join
**What goes wrong:** `gpd.sjoin()` returns all NaN for the NTA columns, or assigns every point to the wrong neighbourhood.
**Why it happens:** Business points created from raw lat/lng are implicitly EPSG:4326, but if NTA GeoJSON was downloaded in a projected CRS (e.g., EPSG:2263 New York State Plane), the coordinate systems don't align.
**How to avoid:** After loading NTA GeoJSON, assert `nta_gdf.crs.to_epsg() == 4326`; if not, call `nta_gdf.to_crs("EPSG:4326")`. NYC Open Data exports are already WGS84 by default.
**Warning signs:** All sjoin results return NaN; businesses visually outside their reported neighbourhood.

### Pitfall 3: SQLite Without WAL Mode Is Slow for Batch Writes
**What goes wrong:** Ingesting 6.9M rows takes hours instead of minutes.
**Why it happens:** Default SQLite journal mode issues an fsync after each transaction; without WAL mode and batching, each `executemany` call with `conn.commit()` is slow.
**How to avoid:** Set `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;` immediately after opening connection. Batch 10,000 rows per `executemany` call.
**Warning signs:** Insert rate < 1,000 rows/sec.

### Pitfall 4: BoroCode Type Mismatch When Filtering NTA GeoJSON
**What goes wrong:** `gdf[gdf["BoroCode"] == 1]` returns empty DataFrame.
**Why it happens:** Socrata GeoJSON export serialises all attribute values as strings. `BoroCode` is `"1"` not `1`.
**How to avoid:** Use `gdf["BoroCode"].isin(["1", "3"])` or cast: `gdf["BoroCode"].astype(int).isin([1, 3])`.
**Warning signs:** Filter returns 0 rows despite correct dataset.

### Pitfall 5: Missing lat/lng Records
**What goes wrong:** Yelp business records occasionally have `null` or missing latitude/longitude. Creating a Point geometry from null coordinates raises an exception that kills the pipeline.
**Why it happens:** User-submitted business data; some records were never geolocated.
**How to avoid:** Filter out businesses with `pd.isna(latitude) or pd.isna(longitude)` before building GeoDataFrame. Log count of skipped records for the quality report.
**Warning signs:** `TypeError: Cannot convert null to float` during geometry creation.

---

## Code Examples

### SQLite Schema for DATA-03 and DATA-06
```python
# Source: DATA-03 field requirements + platform-agnostic DATA-06 pattern
CREATE_BUSINESSES = """
CREATE TABLE IF NOT EXISTS businesses (
    business_id   TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    latitude      REAL,
    longitude     REAL,
    neighbourhood_id TEXT,   -- NTACode from spatial join; NULL if unmatched
    neighbourhood_name TEXT, -- NTAName from spatial join; NULL if unmatched
    city          TEXT,
    state         TEXT,
    attributes    TEXT        -- platform-specific fields as JSON blob (DATA-06)
);
"""

CREATE_REVIEWS = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id     TEXT PRIMARY KEY,
    business_id   TEXT NOT NULL REFERENCES businesses(business_id),
    text          TEXT NOT NULL,
    stars         INTEGER NOT NULL,
    review_date   TEXT NOT NULL,   -- YYYY-MM-DD, indexed for temporal queries
    source        TEXT NOT NULL DEFAULT 'yelp',  -- DATA-03: source platform
    useful        INTEGER,
    funny         INTEGER,
    cool          INTEGER,
    FOREIGN KEY (business_id) REFERENCES businesses(business_id)
);
"""

CREATE_INDICES = """
CREATE INDEX IF NOT EXISTS idx_reviews_business ON reviews(business_id);
CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(review_date);
CREATE INDEX IF NOT EXISTS idx_businesses_neighbourhood ON businesses(neighbourhood_id);
"""
```

### Coverage Probe Script Pattern (Wave 0 Gate)
```python
# scripts/00_probe_coverage.py
import orjson
import geopandas as gpd
from shapely.geometry import Point, box

# Manhattan + Brooklyn bounding box (approximate)
NYC_BBOX = box(-74.05, 40.57, -73.70, 40.92)

def probe_coverage(business_path: str) -> dict:
    total = 0
    nyc_count = 0
    missing_coords = 0
    with open(business_path, "rb") as f:
        for line in f:
            total += 1
            record = orjson.loads(line)
            lat = record.get("latitude")
            lon = record.get("longitude")
            if lat is None or lon is None:
                missing_coords += 1
                continue
            pt = Point(lon, lat)
            if NYC_BBOX.contains(pt):
                nyc_count += 1
    return {
        "total_businesses": total,
        "nyc_bbox_businesses": nyc_count,
        "missing_coords": missing_coords,
    }
```

### Data Quality Report (DATA-05)
```python
# scripts/05_quality_report.py — SQL query approach
import sqlite3, json

def generate_quality_report(db_path: str, output_path: str) -> None:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT
            b.neighbourhood_name,
            substr(r.review_date, 1, 4) AS year,
            COUNT(*) AS review_count
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
          AND substr(r.review_date, 1, 4) BETWEEN '2019' AND '2025'
        GROUP BY b.neighbourhood_name, year
        ORDER BY b.neighbourhood_name, year
    """).fetchall()
    conn.close()
    report = {}
    for neighbourhood, year, count in rows:
        report.setdefault(neighbourhood, {})[year] = count
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
```

---

## NTA Boundary Reference Data

**Confirmed NTA counts** (source: prisonpolicy.org NYC NTA appendix, cross-referenced with NYC Open Data):
- **Manhattan:** 32 NTAs (the dataset includes sub-area splits like "Upper West Side (Central)", "Harlem (South)", "Harlem (North)", etc.)
- **Brooklyn:** 53 NTAs (includes fine-grained splits like "East Flatbush-Erasmus", "East Flatbush-Farragut", etc.)
- **Total for project:** ~85 NTAs covering Manhattan + Brooklyn

**Direct GeoJSON download URL (HIGH confidence — Socrata standard pattern):**
```
https://data.cityofnewyork.us/api/geospatial/9nt8-h7nd?method=export&type=GeoJSON
```

**NTA attribute fields relevant to this project:**
- `NTACode` — unique identifier (e.g., "MN0101"), use as `neighbourhood_id`
- `NTAName` — official name (may be long merged names like "Financial District-Battery Park City")
- `BoroCode` — "1" = Manhattan, "3" = Brooklyn (string in Socrata export)
- `BoroName` — "Manhattan" or "Brooklyn"
- geometry — MultiPolygon, WGS84 (EPSG:4326), no reprojection needed

**Names that need curation** (raw NTA names vs. community-recognised names — planner task):
Example awkward names:
- "Financial District-Battery Park City" → "Financial District" + "Battery Park City" or accept merged
- "SoHo-Little Italy-Hudson Square" → "SoHo" or accept merged
- "Carroll Gardens-Cobble Hill-Gowanus-Red Hook" → potentially split or accept
- "Manhattanville-West Harlem" → "West Harlem"

The CONTEXT.md states the planner produces the curated neighbourhood list. Research confirms the raw NTAs exist and the names are the issue — not the geometries.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| fiona for GeoJSON I/O | pyogrio (default in geopandas ≥ 0.12) | 2022 | ~5x faster reads; no action needed, geopandas uses pyogrio automatically |
| `op=` parameter in sjoin | `predicate=` parameter | geopandas 0.10 | `op=` is deprecated; use `predicate=` |
| SQLite json_each() for JSON import | Python-side parse + executemany | n/a | Python orjson + executemany is faster per SQLite forum benchmarks |

**Deprecated/outdated:**
- `gdf.to_crs(epsg=4326)`: still works but `gdf.to_crs("EPSG:4326")` is the modern style
- `op='within'` in `sjoin`: use `predicate='within'` — the `op` parameter raises DeprecationWarning in geopandas 1.x

---

## Open Questions

1. **Yelp NYC coverage — actual count**
   - What we know: The Yelp Open Dataset's 8 metropolitan areas do not include NYC; a user found "1 row" of NYC city data
   - What's unclear: Whether lat/lng filtering of the full dataset yields any businesses within the Manhattan/Brooklyn bounding box (some businesses near covered metros could be nearby; coverage is geographic, not city-label-based)
   - Recommendation: The Wave 0 coverage probe must run before any other work. If `nyc_bbox_businesses < 500`, surface to user immediately.

2. **NTA name curation**
   - What we know: There are ~85 NTAs; many have hyphenated merged names that New Yorkers would not recognise
   - What's unclear: The planner is tasked with producing the curated name list
   - Recommendation: Planner should produce the mapping table as a task deliverable, using the raw NTA names identified above

3. **Review date range in Yelp 2024 dataset**
   - What we know: Dataset was released April 2024 and covers "to ~mid-2024" per CONTEXT.md
   - What's unclear: The exact cutoff date for the most recent reviews
   - Recommendation: Quality report (DATA-05) will reveal the actual date range empirically

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | `pytest.ini` or `pyproject.toml` — Wave 0 creates |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | NYC business count > 0 after probe | smoke | `pytest tests/test_coverage_probe.py -x` | Wave 0 |
| DATA-02 | Duplicate review_id rejected by INSERT OR IGNORE | unit | `pytest tests/test_schema.py::test_duplicate_insert_ignored -x` | Wave 0 |
| DATA-03 | Review row contains all required fields | unit | `pytest tests/test_schema.py::test_required_fields -x` | Wave 0 |
| DATA-04 | NTA GeoJSON loads with BoroCode 1 and 3 | unit | `pytest tests/test_boundaries.py::test_nta_borough_filter -x` | Wave 0 |
| DATA-05 | Quality report JSON has neighbourhood and year keys | integration | `pytest tests/test_quality_report.py -x` | Wave 0 |
| DATA-06 | businesses.attributes column stores valid JSON | unit | `pytest tests/test_schema.py::test_attributes_json -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` — shared fixtures (in-memory SQLite, sample NTA GeoJSON, sample business NDJSON)
- [ ] `tests/test_coverage_probe.py` — smoke test for probe script
- [ ] `tests/test_schema.py` — unit tests for schema and INSERT OR IGNORE
- [ ] `tests/test_boundaries.py` — unit tests for NTA download + filter
- [ ] `tests/test_quality_report.py` — integration test for report generation
- [ ] `pytest.ini` — framework config with testpaths = tests
- [ ] Framework install: `pip install pytest`

---

## Sources

### Primary (HIGH confidence)
- [geopandas.org sjoin docs](https://geopandas.org/en/stable/docs/reference/api/geopandas.sjoin.html) — predicate parameter, how parameter, return behavior
- [GeoPandas installation docs](https://geopandas.org/en/stable/getting_started/install.html) — version 1.1.3 confirmed current
- [NYC Open Data 2020 NTAs](https://data.cityofnewyork.us/City-Government/2020-Neighborhood-Tabulation-Areas-NTAs-/9nt8-h7nd) — canonical boundary source
- [Yelp/dataset-examples GitHub Issue #47](https://github.com/Yelp/dataset-examples/issues/47) — confirms near-zero NYC coverage ("1 row labeled 'New York' city")
- [SQLite WAL mode documentation](https://sqlite.org/wal.html) — WAL + synchronous=NORMAL for batch write performance

### Secondary (MEDIUM confidence)
- [Prison Policy NYC NTA appendix](https://www.prisonpolicy.org/origin/ny/2020/nyc_nta.html) — NTA counts per borough (Manhattan 32, Brooklyn 53) and full name lists
- [orjson PyPI / GitHub](https://github.com/ijl/orjson) — 2-4x faster than stdlib json on loads
- Multiple Yelp dataset analyses confirming 8-city coverage (Atlanta, Austin, Boston, Boulder, Columbus, Orlando, Portland, Vancouver) — consistent across Kaggle, Medium, and blog sources

### Tertiary (LOW confidence)
- NYC Open Data Socrata GeoJSON export URL pattern `?method=export&type=GeoJSON` — inferred from Socrata standard; must be validated by hitting the URL

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — geopandas, SQLite, orjson are well-documented and version-confirmed
- Architecture: HIGH — streaming NDJSON + batch insert + sjoin is the standard pattern for this workload
- Pitfalls: HIGH — all are empirically documented issues from primary sources
- Yelp NYC coverage: LOW — empirically near-zero based on one GitHub issue; the coverage probe will determine actual count; this is the most important unknown in the project

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable ecosystem; Yelp dataset content does not change)

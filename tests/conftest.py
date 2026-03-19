"""Shared pytest fixtures for Phase 1 and Phase 2 (NLP pipeline) tests."""
from __future__ import annotations

import io
import json
import random
import sqlite3
import tempfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import orjson
import pytest
from shapely.geometry import box


# ---------------------------------------------------------------------------
# Fixture: in-memory SQLite database with Phase 1 schema
# ---------------------------------------------------------------------------
@pytest.fixture
def in_memory_db():
    """Return an open sqlite3.Connection with Phase 1 schema created."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            business_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            neighbourhood_id TEXT,
            neighbourhood_name TEXT,
            city TEXT,
            state TEXT,
            attributes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id TEXT PRIMARY KEY,
            business_id TEXT NOT NULL,
            text TEXT NOT NULL,
            stars INTEGER NOT NULL,
            review_date TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'yelp',
            useful INTEGER,
            funny INTEGER,
            cool INTEGER
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_business ON reviews(business_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(review_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_businesses_neighbourhood ON businesses(neighbourhood_id)")
    conn.commit()
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Fixture: sample business NDJSON file (3 records — Philadelphia pivot)
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_business_ndjson(tmp_path):
    """Write 3 business records to a temp NDJSON file and return the path.

    Record 1: inside Philadelphia bbox (Fishtown area, -75.135, 39.965)
    Record 2: inside Philadelphia bbox (Rittenhouse area, -75.175, 39.945)
    Record 3: outside Philadelphia bbox (Los Angeles, -118.25, 34.05)
    """
    records = [
        {"business_id": "b1", "name": "Pizza Fishtown", "latitude": 39.965, "longitude": -75.135, "city": "Philadelphia", "state": "PA", "attributes": {}},
        {"business_id": "b2", "name": "Coffee Rittenhouse", "latitude": 39.945, "longitude": -75.175, "city": "Philadelphia", "state": "PA", "attributes": {}},
        {"business_id": "b3", "name": "Tacos LA", "latitude": 34.05, "longitude": -118.25, "city": "Los Angeles", "state": "CA", "attributes": {}},
    ]
    ndjson_path = tmp_path / "yelp_academic_dataset_business.json"
    with open(ndjson_path, "wb") as f:
        for rec in records:
            f.write(orjson.dumps(rec) + b"\n")
    return str(ndjson_path)


# ---------------------------------------------------------------------------
# Fixture: sample business NDJSON with one missing-coords record
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_business_ndjson_missing_coords(tmp_path):
    """One record with null latitude."""
    record = {"business_id": "b_null", "name": "No Coords", "latitude": None, "longitude": None, "city": "Unknown", "state": "XX"}
    ndjson_path = tmp_path / "yelp_business_missing.json"
    with open(ndjson_path, "wb") as f:
        f.write(orjson.dumps(record) + b"\n")
    return str(ndjson_path)


# ---------------------------------------------------------------------------
# Fixture: sample Philadelphia neighbourhood GeoDataFrame (minimal, in-memory)
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_nta_gdf():
    """Return a minimal GeoDataFrame with 3 Philadelphia neighbourhood features.

    Matches the schema produced by scripts/01_download_boundaries.py from
    OpenDataPhilly ArcGIS FeatureServer (Philadelphia pivot — see 01-01-DECISION.md).

    Key columns:
      - NEIGHBORHOOD_NUMBER: unique string identifier, e.g. "044"
      - NEIGHBORHOOD_NAME:   community-recognised display name
    """
    from shapely.geometry import Polygon
    data = {
        "NEIGHBORHOOD_NUMBER": ["044", "116", "121"],
        "NEIGHBORHOOD_NAME": ["Fishtown - Lower Kensington", "Rittenhouse", "Society Hill"],
        "DISTRICT_NO": ["01", "08", "05"],
        "PLANNING_PARTNER": ["DVRPC", "DVRPC", "DVRPC"],
        "geometry": [
            # Fishtown area (NE Philly, near ~39.97N, -75.13W)
            Polygon([(-75.14, 39.96), (-75.13, 39.96), (-75.13, 39.97), (-75.14, 39.97)]),
            # Rittenhouse area (Center City, ~39.95N, -75.17W)
            Polygon([(-75.18, 39.94), (-75.17, 39.94), (-75.17, 39.95), (-75.18, 39.95)]),
            # Society Hill area (~39.94N, -75.14W)
            Polygon([(-75.15, 39.93), (-75.14, 39.93), (-75.14, 39.94), (-75.15, 39.94)]),
        ],
    }
    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
    return gdf


# ---------------------------------------------------------------------------
# Phase 2 Fixtures: NLP Pipeline
# ---------------------------------------------------------------------------

_REVIEW_TEMPLATES = [
    "Great food and atmosphere in {neighbourhood}",
    "Lovely cafe with amazing coffee in {neighbourhood}",
    "The best brunch spot in {neighbourhood}, highly recommend",
    "Nice bar with live music in {neighbourhood}",
    "Family friendly restaurant in {neighbourhood}",
    "Beautiful art gallery in {neighbourhood}",
    "Upscale dining experience in {neighbourhood}",
    "Historic landmark worth visiting in {neighbourhood}",
    "Fun nightlife scene in {neighbourhood}",
    "Cozy neighborhood pub in {neighbourhood}",
]

_NEIGHBOURHOODS = [
    ("044", "Fishtown - Lower Kensington"),
    ("116", "Rittenhouse"),
    ("121", "Society Hill"),
]


@pytest.fixture
def mock_db_with_reviews(tmp_path):
    """Create a temp SQLite DB with Phase 1 schema, 3 businesses, and 90 reviews.

    3 businesses (neighbourhoods 044, 116, 121) with 30 reviews each:
    10 reviews per neighbourhood per year (2019, 2020, 2021).
    Returns the DB path string.
    """
    db_path = str(tmp_path / "test_reviews.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            business_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            neighbourhood_id TEXT,
            neighbourhood_name TEXT,
            city TEXT,
            state TEXT,
            attributes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id TEXT PRIMARY KEY,
            business_id TEXT NOT NULL,
            text TEXT NOT NULL,
            stars INTEGER NOT NULL,
            review_date TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'yelp',
            useful INTEGER,
            funny INTEGER,
            cool INTEGER
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_business ON reviews(business_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(review_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_businesses_neighbourhood ON businesses(neighbourhood_id)")

    # Insert 3 businesses
    businesses = [
        ("biz_044", "Pizza Fishtown", 39.965, -75.135, "044", "Fishtown - Lower Kensington", "Philadelphia", "PA", "{}"),
        ("biz_116", "Coffee Rittenhouse", 39.945, -75.175, "116", "Rittenhouse", "Philadelphia", "PA", "{}"),
        ("biz_121", "Bistro Society Hill", 39.940, -75.145, "121", "Society Hill", "Philadelphia", "PA", "{}"),
    ]
    conn.executemany(
        "INSERT INTO businesses VALUES (?,?,?,?,?,?,?,?,?)",
        businesses,
    )

    # Insert 90 reviews: 30 per business, 10 per year (2019, 2020, 2021)
    rng = random.Random(42)
    review_id = 1
    reviews = []
    for biz_id, _, _, _, nid, nname, _, _, _ in businesses:
        for year in [2019, 2020, 2021]:
            for i in range(10):
                template = _REVIEW_TEMPLATES[i % len(_REVIEW_TEMPLATES)]
                text = template.format(neighbourhood=nname)
                stars = rng.randint(1, 5)
                month = rng.randint(1, 12)
                day = rng.randint(1, 28)
                date_str = f"{year}-{month:02d}-{day:02d}"
                reviews.append((
                    str(review_id), biz_id, text, stars, date_str, "yelp",
                    rng.randint(0, 10), rng.randint(0, 5), rng.randint(0, 5),
                ))
                review_id += 1

    conn.executemany(
        "INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?,?)",
        reviews,
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def mock_embeddings(tmp_path):
    """Create mock embeddings.npy (90, 384) and review_ids.npy (90,).

    Returns the tmp artifacts directory Path.
    """
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    np.random.seed(42)
    embeddings = np.random.randn(90, 384).astype(np.float32)
    review_ids = np.arange(1, 91, dtype=np.int64)
    np.save(artifacts_dir / "embeddings.npy", embeddings)
    np.save(artifacts_dir / "review_ids.npy", review_ids)
    return artifacts_dir


@pytest.fixture
def mock_artifacts_dir(tmp_path):
    """Return an empty artifacts directory (created)."""
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    return artifacts_dir


@pytest.fixture
def archetypes_path():
    """Return the path to the real archetypes config file."""
    return Path("pipeline/archetypes.json")


# ---------------------------------------------------------------------------
# Phase 2 Export Stage Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_export_setup(tmp_path, monkeypatch):
    """Create a complete mock environment for the export stage.

    Returns (db_path, artifacts_dir, boundaries_geojson_path) with:
    - SQLite DB: 3 businesses, 90 reviews (30 per neighbourhood)
    - artifacts_dir pre-populated with: embeddings.npy, review_ids.npy,
      topic_assignments.json, vibe_scores.json, temporal_series.json,
      bertopic_model/, sentiment_model/
    - A mock GeoJSON boundaries file
    """
    # 1. Create DB with businesses and reviews
    db_path = str(tmp_path / "test_reviews.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            business_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            neighbourhood_id TEXT,
            neighbourhood_name TEXT,
            city TEXT,
            state TEXT,
            attributes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id TEXT PRIMARY KEY,
            business_id TEXT NOT NULL,
            text TEXT NOT NULL,
            stars INTEGER NOT NULL,
            review_date TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'yelp',
            useful INTEGER,
            funny INTEGER,
            cool INTEGER
        )
    """)

    businesses = [
        ("biz_044", "Pizza Fishtown", 39.965, -75.135, "044", "Fishtown", "Philadelphia", "PA", "{}"),
        ("biz_116", "Coffee Rittenhouse", 39.945, -75.175, "116", "Rittenhouse", "Philadelphia", "PA", "{}"),
        ("biz_121", "Bistro Society Hill", 39.940, -75.145, "121", "Society Hill", "Philadelphia", "PA", "{}"),
    ]
    conn.executemany("INSERT INTO businesses VALUES (?,?,?,?,?,?,?,?,?)", businesses)

    rng = random.Random(42)
    reviews = []
    review_texts = [
        "Great food and atmosphere",
        "Lovely cafe with amazing coffee",
        "The best brunch spot, highly recommend this place for weekend mornings",
        "Nice bar with live music and cool vibes",
        "Family friendly restaurant with great kids menu",
        "Beautiful art gallery with rotating exhibits",
        "Upscale dining experience, excellent wine list",
        "Historic landmark worth visiting for the architecture alone",
        "Fun nightlife scene with great cocktails",
        "Cozy neighborhood pub with craft beer selection",
    ]
    review_id = 1
    for biz_id, _, _, _, nid, nname, _, _, _ in businesses:
        for year in [2019, 2020, 2021]:
            for i in range(10):
                text = review_texts[i % len(review_texts)]
                stars = rng.randint(1, 5)
                month = rng.randint(1, 12)
                day = rng.randint(1, 28)
                date_str = f"{year}-{month:02d}-{day:02d}"
                reviews.append((
                    str(review_id), biz_id, text, stars, date_str, "yelp",
                    rng.randint(0, 10), rng.randint(0, 5), rng.randint(0, 5),
                ))
                review_id += 1

    conn.executemany("INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?,?)", reviews)
    conn.commit()
    conn.close()

    # 2. Create artifacts directory with pre-computed inputs
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()

    np.random.seed(42)

    # embeddings.npy: (90, 384) -- one per review
    embeddings = np.random.randn(90, 384).astype(np.float32)
    np.save(artifacts_dir / "embeddings.npy", embeddings)

    # review_ids.npy: rowids 1..90
    review_ids = np.arange(1, 91, dtype=np.int64)
    np.save(artifacts_dir / "review_ids.npy", review_ids)

    # topic_assignments.json: assign reviews to 3 topics (0, 1, 2)
    topic_assignments = {}
    for rid in range(1, 91):
        topic_assignments[str(rid)] = rid % 3
    with open(artifacts_dir / "topic_assignments.json", "w") as f:
        json.dump(topic_assignments, f)

    # vibe_scores.json: 3 neighbourhoods with 6 archetype scores
    vibe_scores = {
        "044": {"artsy": 0.42, "foodie": 0.78, "nightlife": 0.35, "family": 0.60, "upscale": 0.25, "cultural": 0.50},
        "116": {"artsy": 0.30, "foodie": 0.65, "nightlife": 0.55, "family": 0.40, "upscale": 0.70, "cultural": 0.45},
        "121": {"artsy": 0.55, "foodie": 0.50, "nightlife": 0.20, "family": 0.50, "upscale": 0.60, "cultural": 0.75},
    }
    with open(artifacts_dir / "vibe_scores.json", "w") as f:
        json.dump(vibe_scores, f, indent=2)

    # temporal_series.json
    temporal_series = {
        nid: {str(y): scores for y in [2019, 2020, 2021]}
        for nid, scores in vibe_scores.items()
    }
    with open(artifacts_dir / "temporal_series.json", "w") as f:
        json.dump(temporal_series, f, indent=2)

    # bertopic_model/ directory (stub) — mock BERTopic.load so tests don't
    # need real model weights; get_topic() returns plausible (word, score) pairs.
    (artifacts_dir / "bertopic_model").mkdir()
    (artifacts_dir / "bertopic_model" / "config.json").write_text("{}")
    from unittest.mock import MagicMock
    import bertopic as _bertopic_module

    _mock_topic_model = MagicMock()
    _mock_topic_model.get_topic.side_effect = lambda tid: [
        (f"word{tid}_{i}", round(0.5 / (i + 1), 4)) for i in range(5)
    ]
    monkeypatch.setattr(_bertopic_module.BERTopic, "load", classmethod(lambda cls, path, **kw: _mock_topic_model))

    # sentiment_model/ directory (stub)
    (artifacts_dir / "sentiment_model").mkdir()
    (artifacts_dir / "sentiment_model" / "config.json").write_text("{}")

    # 3. Create mock boundaries GeoJSON
    boundaries_dir = tmp_path / "data" / "boundaries"
    boundaries_dir.mkdir(parents=True)
    mock_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "NEIGHBORHOOD_NUMBER": "044",
                    "NEIGHBORHOOD_NAME": "Fishtown - Lower Kensington",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-75.14, 39.96], [-75.13, 39.96], [-75.13, 39.97], [-75.14, 39.97], [-75.14, 39.96]]],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "NEIGHBORHOOD_NUMBER": "116",
                    "NEIGHBORHOOD_NAME": "Rittenhouse",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-75.18, 39.94], [-75.17, 39.94], [-75.17, 39.95], [-75.18, 39.95], [-75.18, 39.94]]],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "NEIGHBORHOOD_NUMBER": "121",
                    "NEIGHBORHOOD_NAME": "Society Hill",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-75.15, 39.93], [-75.14, 39.93], [-75.14, 39.94], [-75.15, 39.94], [-75.15, 39.93]]],
                },
            },
        ],
    }
    geojson_path = boundaries_dir / "philadelphia_neighborhoods.geojson"
    with open(geojson_path, "w") as f:
        json.dump(mock_geojson, f, indent=2)

    return db_path, artifacts_dir, str(geojson_path)

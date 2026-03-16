"""Shared pytest fixtures for Phase 1 tests."""
from __future__ import annotations

import io
import json
import sqlite3
import tempfile
from pathlib import Path

import geopandas as gpd
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

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
# Fixture: sample business NDJSON file (3 records)
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_business_ndjson(tmp_path):
    """Write 3 business records to a temp NDJSON file and return the path.

    Record 1: inside NYC bbox (Manhattan, -73.98, 40.75)
    Record 2: inside NYC bbox (Brooklyn, -73.95, 40.65)
    Record 3: outside NYC bbox (Los Angeles, -118.25, 34.05)
    """
    records = [
        {"business_id": "b1", "name": "Pizza NYC", "latitude": 40.75, "longitude": -73.98, "city": "New York", "state": "NY", "attributes": {}},
        {"business_id": "b2", "name": "Bagels Brooklyn", "latitude": 40.65, "longitude": -73.95, "city": "Brooklyn", "state": "NY", "attributes": {}},
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
# Fixture: sample NTA GeoJSON GeoDataFrame (minimal, in-memory)
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_nta_gdf():
    """Return a minimal GeoDataFrame with 3 NTA-like features: BoroCode 1, 2, 3."""
    import pandas as pd
    from shapely.geometry import Polygon
    data = {
        "NTACode": ["MN01", "BX01", "BK01"],
        "NTAName": ["West Village", "Mott Haven", "Williamsburg"],
        "BoroCode": ["1", "2", "3"],
        "BoroName": ["Manhattan", "Bronx", "Brooklyn"],
        "geometry": [
            Polygon([(-74.01, 40.73), (-74.00, 40.73), (-74.00, 40.74), (-74.01, 40.74)]),
            Polygon([(-73.93, 40.80), (-73.92, 40.80), (-73.92, 40.81), (-73.93, 40.81)]),
            Polygon([(-73.96, 40.71), (-73.95, 40.71), (-73.95, 40.72), (-73.96, 40.72)]),
        ],
    }
    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
    return gdf

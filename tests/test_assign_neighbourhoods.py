"""
Unit tests for scripts/03_assign_neighbourhoods.py — TDD RED.

Behaviour under test (from 01-03-PLAN.md):
1. Single record inside Fishtown polygon -> inserted with non-null neighbourhood_id
2. Record with null latitude -> skipped, missing_coords += 1, no DB error
3. Idempotent: calling assign_neighbourhoods twice yields exactly 1 row
4. CRS guard: AssertionError if nta_gdf CRS is not EPSG:4326
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest import mock

import geopandas as gpd
import orjson
import pytest
from shapely.geometry import Polygon, Point


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ndjson(tmp_path: Path, records: list[dict]) -> str:
    """Write records to a temp NDJSON file and return its path as string."""
    p = tmp_path / "yelp_academic_dataset_business.json"
    with open(p, "wb") as f:
        for rec in records:
            f.write(orjson.dumps(rec) + b"\n")
    return str(p)


def _make_db(tmp_path: Path) -> str:
    """Create a fresh reviews.db with Phase 1 schema in tmp_path."""
    from scripts.build_schema import build_schema  # noqa: F401 (may not exist yet)
    db_path = str(tmp_path / "reviews.db")
    # Import here so missing module causes test failure in RED phase
    from scripts.build_schema import build_schema
    build_schema(db_path)
    return db_path


# ---------------------------------------------------------------------------
# Fixture: minimal Philadelphia GeoDataFrame (3 neighbourhoods)
# ---------------------------------------------------------------------------
@pytest.fixture
def philly_gdf():
    """3-polygon Philadelphia GeoDataFrame matching 01-02 schema."""
    data = {
        "NEIGHBORHOOD_NUMBER": ["044", "116", "121"],
        "NEIGHBORHOOD_NAME": ["Fishtown - Lower Kensington", "Rittenhouse", "Society Hill"],
        "geometry": [
            # Fishtown polygon: lon -75.14 to -75.13, lat 39.96 to 39.97
            Polygon([(-75.14, 39.96), (-75.13, 39.96), (-75.13, 39.97), (-75.14, 39.97)]),
            # Rittenhouse polygon: lon -75.18 to -75.17, lat 39.94 to 39.95
            Polygon([(-75.18, 39.94), (-75.17, 39.94), (-75.17, 39.95), (-75.18, 39.95)]),
            # Society Hill polygon: lon -75.15 to -75.14, lat 39.93 to 39.94
            Polygon([(-75.15, 39.93), (-75.14, 39.93), (-75.14, 39.94), (-75.15, 39.94)]),
        ],
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


# ---------------------------------------------------------------------------
# Test 1: Record inside Fishtown polygon gets neighbourhood_id assigned
# ---------------------------------------------------------------------------
def test_business_inside_polygon_gets_neighbourhood_id(tmp_path, philly_gdf):
    """A business whose point falls inside the Fishtown polygon is inserted
    with a non-null neighbourhood_id matching the NEIGHBORHOOD_NUMBER '044'."""
    # Point inside the Fishtown polygon defined above
    record = {
        "business_id": "bfish",
        "name": "Fishtown Diner",
        "latitude": 39.965,
        "longitude": -75.135,
        "city": "Philadelphia",
        "state": "PA",
        "attributes": {"wifi": "free"},
    }
    ndjson_path = _make_ndjson(tmp_path, [record])
    db_path = str(tmp_path / "reviews.db")

    from scripts.build_schema import build_schema
    build_schema(db_path)

    from scripts.assign_neighbourhoods import assign_neighbourhoods
    result = assign_neighbourhoods(
        ndjson_path,
        db_path,
        neighbourhood_gdf=philly_gdf,
        curation={},
    )

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT business_id, neighbourhood_id, neighbourhood_name FROM businesses WHERE business_id = 'bfish'"
    ).fetchone()
    conn.close()

    assert row is not None, "business 'bfish' should be in businesses table"
    assert row[1] == "044", f"neighbourhood_id should be '044' (Fishtown), got {row[1]!r}"
    assert result["assigned"] == 1


# ---------------------------------------------------------------------------
# Test 2: Record with null latitude is skipped, missing_coords incremented
# ---------------------------------------------------------------------------
def test_null_lat_business_is_skipped(tmp_path, philly_gdf):
    """A business with null latitude is skipped: missing_coords == 1, no DB row."""
    record = {
        "business_id": "b_null",
        "name": "No Coords",
        "latitude": None,
        "longitude": None,
        "city": "Philadelphia",
        "state": "PA",
    }
    ndjson_path = _make_ndjson(tmp_path, [record])
    db_path = str(tmp_path / "reviews.db")

    from scripts.build_schema import build_schema
    build_schema(db_path)

    from scripts.assign_neighbourhoods import assign_neighbourhoods
    result = assign_neighbourhoods(
        ndjson_path,
        db_path,
        neighbourhood_gdf=philly_gdf,
        curation={},
    )

    assert result["missing_coords"] == 1, (
        f"Expected missing_coords=1, got {result['missing_coords']}"
    )
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]
    conn.close()
    assert count == 0, f"No rows should be inserted for a null-coord business, got {count}"


# ---------------------------------------------------------------------------
# Test 3: Idempotent — calling twice yields exactly 1 row (INSERT OR IGNORE)
# ---------------------------------------------------------------------------
def test_idempotent_insert(tmp_path, philly_gdf):
    """Calling assign_neighbourhoods twice on the same record yields 1 row."""
    record = {
        "business_id": "bfish2",
        "name": "Duplicate Test",
        "latitude": 39.965,
        "longitude": -75.135,
        "city": "Philadelphia",
        "state": "PA",
        "attributes": {},
    }
    ndjson_path = _make_ndjson(tmp_path, [record])
    db_path = str(tmp_path / "reviews.db")

    from scripts.build_schema import build_schema
    build_schema(db_path)

    from scripts.assign_neighbourhoods import assign_neighbourhoods
    assign_neighbourhoods(ndjson_path, db_path, neighbourhood_gdf=philly_gdf, curation={})
    assign_neighbourhoods(ndjson_path, db_path, neighbourhood_gdf=philly_gdf, curation={})

    conn = sqlite3.connect(db_path)
    count = conn.execute(
        "SELECT COUNT(*) FROM businesses WHERE business_id = 'bfish2'"
    ).fetchone()[0]
    conn.close()
    assert count == 1, f"INSERT OR IGNORE should yield exactly 1 row, got {count}"


# ---------------------------------------------------------------------------
# Test 4: CRS guard — AssertionError if GeoDataFrame CRS is not EPSG:4326
# ---------------------------------------------------------------------------
def test_crs_guard_raises_assertion_error(tmp_path, philly_gdf):
    """If neighbourhood_gdf CRS is not EPSG:4326, AssertionError raised before inserts."""
    record = {
        "business_id": "b_crs",
        "name": "CRS Test",
        "latitude": 39.965,
        "longitude": -75.135,
        "city": "Philadelphia",
        "state": "PA",
        "attributes": {},
    }
    ndjson_path = _make_ndjson(tmp_path, [record])
    db_path = str(tmp_path / "reviews.db")

    from scripts.build_schema import build_schema
    build_schema(db_path)

    # Reproject to EPSG:3857 (Web Mercator) — should trigger CRS guard
    wrong_crs_gdf = philly_gdf.to_crs("EPSG:3857")

    from scripts.assign_neighbourhoods import assign_neighbourhoods
    with pytest.raises(AssertionError):
        assign_neighbourhoods(
            ndjson_path,
            db_path,
            neighbourhood_gdf=wrong_crs_gdf,
            curation={},
        )

    # No rows should have been inserted
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]
    conn.close()
    assert count == 0, "No rows should be inserted after CRS guard failure"

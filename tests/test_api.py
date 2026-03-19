"""Integration tests for all API data endpoints.

Requires real artifacts on disk (marked slow).
"""
from __future__ import annotations

import time

import pytest
from starlette.testclient import TestClient

from backend.app import app

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def client():
    """TestClient with lifespan events (loads real artifacts)."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------
def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["artifacts_loaded"] is True


# ---------------------------------------------------------------------------
# GET /neighbourhoods  (GeoJSON FeatureCollection)
# ---------------------------------------------------------------------------
def test_neighbourhoods_returns_geojson(client):
    resp = client.get("/neighbourhoods")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/geo+json"


def test_neighbourhoods_is_feature_collection(client):
    resp = client.get("/neighbourhoods")
    body = resp.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 159


# ---------------------------------------------------------------------------
# GET /neighbourhoods/{nid}  (Neighbourhood detail)
# ---------------------------------------------------------------------------
def test_neighbourhood_detail_valid(client):
    resp = client.get("/neighbourhoods/001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["neighbourhood_id"] == "001"
    assert "vibe_scores" in body
    assert "dominant_vibe" in body
    assert "dominant_vibe_score" in body
    assert "topics" in body
    assert "quotes" in body
    assert "review_count" in body


def test_neighbourhood_detail_has_name(client):
    resp = client.get("/neighbourhoods/001")
    body = resp.json()
    assert body["neighbourhood_name"] is not None
    assert isinstance(body["neighbourhood_name"], str)
    assert len(body["neighbourhood_name"]) > 0


def test_neighbourhood_detail_topics_structure(client):
    resp = client.get("/neighbourhoods/001")
    body = resp.json()
    topics = body["topics"]
    assert len(topics) <= 10
    for t in topics:
        assert "label" in t
        assert "keywords" in t
        assert "review_share" in t


def test_neighbourhood_detail_not_found(client):
    resp = client.get("/neighbourhoods/999")
    assert resp.status_code == 404


def test_neighbourhood_detail_zero_padding(client):
    """GET /neighbourhoods/1 should return same as /neighbourhoods/001."""
    resp = client.get("/neighbourhoods/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["neighbourhood_id"] == "001"


# ---------------------------------------------------------------------------
# GET /temporal
# ---------------------------------------------------------------------------
def test_temporal_returns_all(client):
    resp = client.get("/temporal")
    assert resp.status_code == 200
    body = resp.json()
    # Should have 157+ neighbourhood IDs
    assert len(body) >= 157
    # Pick first entry and verify structure
    first_nid = next(iter(body))
    years = body[first_nid]
    assert isinstance(years, dict)
    # Each year has archetype scores
    for year_key, scores in years.items():
        assert isinstance(scores, dict)
        assert len(scores) > 0


# ---------------------------------------------------------------------------
# GET /similar
# ---------------------------------------------------------------------------
def test_similar_returns_k_results(client):
    resp = client.get("/similar", params={"id": "001", "k": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 5


def test_similar_excludes_self(client):
    resp = client.get("/similar", params={"id": "001", "k": 5})
    body = resp.json()
    nids = [r["neighbourhood_id"] for r in body]
    assert "001" not in nids


def test_similar_clamps_k(client):
    """k=200 should clamp to max available (156) without error."""
    resp = client.get("/similar", params={"id": "001", "k": 200})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) <= 156


def test_similar_not_found(client):
    resp = client.get("/similar", params={"id": "999", "k": 5})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Response time assertions (< 100ms each)
# ---------------------------------------------------------------------------
_ENDPOINTS = [
    "/health",
    "/neighbourhoods",
    "/neighbourhoods/001",
    "/temporal",
    "/similar?id=001&k=5",
]


@pytest.mark.parametrize("endpoint", _ENDPOINTS)
def test_response_time(client, endpoint):
    start = time.time()
    resp = client.get(endpoint)
    elapsed = time.time() - start
    assert resp.status_code == 200, f"{endpoint} returned {resp.status_code}"
    assert elapsed < 0.1, f"{endpoint} took {elapsed:.3f}s (> 100ms)"

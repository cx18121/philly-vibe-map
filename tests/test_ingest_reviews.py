"""TDD tests for scripts/04_ingest_reviews.py — review streaming ingest."""
from __future__ import annotations

import importlib.util
import io
import sqlite3
import tempfile
from pathlib import Path

import orjson
import pytest


# ---------------------------------------------------------------------------
# Helper: load 04_ingest_reviews module via importlib (numeric prefix)
# ---------------------------------------------------------------------------
def _load_ingest_reviews():
    spec = importlib.util.spec_from_file_location(
        "ingest_reviews_module",
        Path(__file__).parent.parent / "scripts" / "04_ingest_reviews.py",
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def ingest_module():
    return _load_ingest_reviews()


# ---------------------------------------------------------------------------
# Helper: create temp SQLite DB with Phase 1 schema + known businesses
# ---------------------------------------------------------------------------
def _make_db_with_businesses(tmp_path: Path, business_ids: list[str]) -> str:
    """Create a reviews.db with schema and the given business_ids pre-inserted."""
    db_path = str(tmp_path / "reviews.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE businesses (
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
        CREATE TABLE reviews (
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
    conn.executemany(
        "INSERT INTO businesses (business_id, name) VALUES (?, ?)",
        [(bid, f"Biz {bid}") for bid in business_ids],
    )
    conn.commit()
    conn.close()
    return db_path


def _make_review_ndjson(tmp_path: Path, records: list[dict]) -> str:
    """Write review records to a temp NDJSON file and return path."""
    p = tmp_path / "yelp_academic_dataset_review.json"
    with open(p, "wb") as f:
        for rec in records:
            f.write(orjson.dumps(rec) + b"\n")
    return str(p)


# ---------------------------------------------------------------------------
# Test 1: FK filter — only reviews for known businesses are inserted
# ---------------------------------------------------------------------------
def test_only_known_business_reviews_inserted(ingest_module, tmp_path):
    """5 reviews: 3 with known business_ids, 2 with unknown — exactly 3 inserted."""
    known_ids = ["b1", "b2", "b3"]
    db_path = _make_db_with_businesses(tmp_path, known_ids)

    records = [
        {"review_id": "r1", "business_id": "b1", "text": "Great!", "stars": 5, "date": "2021-06-01 10:00:00", "useful": 1, "funny": 0, "cool": 0},
        {"review_id": "r2", "business_id": "b2", "text": "Good", "stars": 4, "date": "2021-06-02 10:00:00", "useful": 0, "funny": 0, "cool": 0},
        {"review_id": "r3", "business_id": "b3", "text": "OK", "stars": 3, "date": "2021-06-03 10:00:00", "useful": 0, "funny": 0, "cool": 0},
        {"review_id": "r4", "business_id": "unknown1", "text": "Skip me", "stars": 1, "date": "2021-06-04 10:00:00", "useful": 0, "funny": 0, "cool": 0},
        {"review_id": "r5", "business_id": "unknown2", "text": "Skip me too", "stars": 2, "date": "2021-06-05 10:00:00", "useful": 0, "funny": 0, "cool": 0},
    ]
    review_path = _make_review_ndjson(tmp_path, records)

    result = ingest_module.ingest_reviews(review_path, db_path)

    assert result["written"] == 3, f"Expected 3 reviews written, got {result['written']}"
    assert result["skipped_unknown_biz"] == 2, f"Expected 2 skipped, got {result['skipped_unknown_biz']}"

    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    conn.close()
    assert count == 3


# ---------------------------------------------------------------------------
# Test 2: Idempotency — calling twice leaves the same row count
# ---------------------------------------------------------------------------
def test_ingest_reviews_idempotent(ingest_module, tmp_path):
    """INSERT OR IGNORE: second run produces same row count as first run."""
    known_ids = ["b1", "b2", "b3"]
    db_path = _make_db_with_businesses(tmp_path, known_ids)

    records = [
        {"review_id": "r1", "business_id": "b1", "text": "Great!", "stars": 5, "date": "2021-06-01 10:00:00", "useful": 1, "funny": 0, "cool": 0},
        {"review_id": "r2", "business_id": "b2", "text": "Good", "stars": 4, "date": "2021-06-02 10:00:00", "useful": 0, "funny": 0, "cool": 0},
        {"review_id": "r3", "business_id": "b3", "text": "OK", "stars": 3, "date": "2021-06-03 10:00:00", "useful": 0, "funny": 0, "cool": 0},
    ]
    review_path = _make_review_ndjson(tmp_path, records)

    ingest_module.ingest_reviews(review_path, db_path)
    ingest_module.ingest_reviews(review_path, db_path)

    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    conn.close()
    assert count == 3, f"Expected 3 rows after second run, got {count}"


# ---------------------------------------------------------------------------
# Test 3: Date truncation — "2021-06-15 18:30:00" stored as "2021-06-15"
# ---------------------------------------------------------------------------
def test_date_truncated_to_yyyy_mm_dd(ingest_module, tmp_path):
    """review_date is stored as YYYY-MM-DD only (no time component)."""
    known_ids = ["b1"]
    db_path = _make_db_with_businesses(tmp_path, known_ids)

    records = [
        {"review_id": "r1", "business_id": "b1", "text": "Test", "stars": 4,
         "date": "2021-06-15 18:30:00", "useful": 0, "funny": 0, "cool": 0},
    ]
    review_path = _make_review_ndjson(tmp_path, records)

    ingest_module.ingest_reviews(review_path, db_path)

    conn = sqlite3.connect(db_path)
    review_date = conn.execute(
        "SELECT review_date FROM reviews WHERE review_id = 'r1'"
    ).fetchone()[0]
    conn.close()
    assert review_date == "2021-06-15", f"Expected '2021-06-15', got '{review_date}'"


# ---------------------------------------------------------------------------
# Test 4: Progress logging — "Review file open" is emitted first
# ---------------------------------------------------------------------------
def test_review_file_open_log_emitted(ingest_module, tmp_path, capsys):
    """First log line contains 'Review file open — streaming parse started'."""
    known_ids = ["b1"]
    db_path = _make_db_with_businesses(tmp_path, known_ids)

    records = [
        {"review_id": "r1", "business_id": "b1", "text": "Test", "stars": 4,
         "date": "2021-06-15 10:00:00", "useful": 0, "funny": 0, "cool": 0},
    ]
    review_path = _make_review_ndjson(tmp_path, records)

    ingest_module.ingest_reviews(review_path, db_path)

    captured = capsys.readouterr()
    assert "Review file open — streaming parse started" in captured.out, (
        f"Expected 'Review file open — streaming parse started' in stdout, got:\n{captured.out}"
    )


# ---------------------------------------------------------------------------
# Test 5: Progress milestone — "Reviews written: 100000" emitted at 100k
# ---------------------------------------------------------------------------
def test_progress_milestone_emitted_at_100k(ingest_module, tmp_path, capsys):
    """'Reviews written: 100,000' is emitted when write_count reaches 100,000."""
    known_ids = ["b1"]
    db_path = _make_db_with_businesses(tmp_path, known_ids)

    # Generate 100,001 reviews for b1 to trigger the 100k milestone
    records = [
        {
            "review_id": f"r{i}",
            "business_id": "b1",
            "text": f"Review {i}",
            "stars": (i % 5) + 1,
            "date": "2021-01-01 00:00:00",
            "useful": 0,
            "funny": 0,
            "cool": 0,
        }
        for i in range(100_001)
    ]
    review_path = _make_review_ndjson(tmp_path, records)

    ingest_module.ingest_reviews(review_path, db_path)

    captured = capsys.readouterr()
    assert "Reviews written: 100,000" in captured.out, (
        f"Expected 'Reviews written: 100,000' in stdout, got:\n{captured.out[:500]}"
    )

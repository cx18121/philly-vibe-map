"""Unit tests for SQLite schema: DATA-02 (dedup), DATA-03 (required fields), DATA-06 (JSON attributes)."""
import json
import sqlite3


def test_duplicate_insert_ignored(in_memory_db):
    """DATA-02: INSERT OR IGNORE rejects duplicate review_id -- no error, exactly 1 row."""
    conn = in_memory_db
    # Insert a business first (FK dependency)
    conn.execute(
        "INSERT INTO businesses (business_id, name) VALUES (?, ?)", ("b1", "Test Biz")
    )
    conn.execute(
        "INSERT OR IGNORE INTO reviews (review_id, business_id, text, stars, review_date, source) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("r1", "b1", "Great place", 5, "2022-06-01", "yelp"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO reviews (review_id, business_id, text, stars, review_date, source) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("r1", "b1", "Duplicate review", 1, "2022-07-01", "yelp"),
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM reviews WHERE review_id = 'r1'").fetchone()[0]
    assert count == 1, f"Expected 1 row after duplicate insert, got {count}"


def test_required_fields(in_memory_db):
    """DATA-03: A valid review row has all 9 required columns non-null."""
    conn = in_memory_db
    conn.execute(
        "INSERT INTO businesses (business_id, name, latitude, longitude) VALUES (?, ?, ?, ?)",
        ("b2", "Biz2", 40.75, -73.98),
    )
    conn.execute(
        "INSERT OR IGNORE INTO reviews "
        "(review_id, business_id, text, stars, review_date, source, useful, funny, cool) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("r2", "b2", "Lovely spot", 4, "2021-03-15", "yelp", 2, 0, 1),
    )
    conn.commit()
    row = conn.execute(
        "SELECT review_id, business_id, text, stars, review_date, source, useful, funny, cool "
        "FROM reviews WHERE review_id = 'r2'"
    ).fetchone()
    assert row is not None
    assert len(row) == 9
    # All DATA-03 required fields present
    assert row[0] == "r2"          # review_id
    assert row[1] == "b2"          # business_id
    assert row[2] == "Lovely spot" # text
    assert row[3] == 4             # stars
    assert row[4] == "2021-03-15"  # review_date (timestamp)
    assert row[5] == "yelp"        # source platform


def test_attributes_json(in_memory_db):
    """DATA-06: business.attributes column stores and round-trips valid JSON."""
    conn = in_memory_db
    attrs = {"wifi": True, "parking": "free", "categories": ["Italian", "Pizza"]}
    attrs_json = json.dumps(attrs)
    conn.execute(
        "INSERT INTO businesses (business_id, name, attributes) VALUES (?, ?, ?)",
        ("b3", "Biz3", attrs_json),
    )
    conn.commit()
    stored = conn.execute(
        "SELECT attributes FROM businesses WHERE business_id = 'b3'"
    ).fetchone()[0]
    parsed = json.loads(stored)
    assert parsed["wifi"] is True
    assert parsed["parking"] == "free"
    assert "Italian" in parsed["categories"]

"""
02_build_schema.py
Create (or verify) the Phase 1 SQLite schema.

Usage:
    python scripts/02_build_schema.py [--db data/output/reviews.db]
"""
from __future__ import annotations

import argparse
import datetime
import sqlite3
import sys
from pathlib import Path

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"

def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


CREATE_BUSINESSES = """
CREATE TABLE IF NOT EXISTS businesses (
    business_id        TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    latitude           REAL,
    longitude          REAL,
    neighbourhood_id   TEXT,
    neighbourhood_name TEXT,
    city               TEXT,
    state              TEXT,
    attributes         TEXT
);
"""

CREATE_REVIEWS = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id   TEXT PRIMARY KEY,
    business_id TEXT NOT NULL,
    text        TEXT NOT NULL,
    stars       INTEGER NOT NULL,
    review_date TEXT NOT NULL,
    source      TEXT NOT NULL DEFAULT 'yelp',
    useful      INTEGER,
    funny       INTEGER,
    cool        INTEGER,
    FOREIGN KEY (business_id) REFERENCES businesses(business_id)
);
"""

CREATE_INDICES = """
CREATE INDEX IF NOT EXISTS idx_reviews_business    ON reviews(business_id);
CREATE INDEX IF NOT EXISTS idx_reviews_date        ON reviews(review_date);
CREATE INDEX IF NOT EXISTS idx_businesses_neighbourhood ON businesses(neighbourhood_id);
"""


def build_schema(db_path: str) -> None:
    """Create (or verify) Phase 1 schema in the SQLite database at db_path."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript(CREATE_BUSINESSES)
    conn.executescript(CREATE_REVIEWS)
    conn.executescript(CREATE_INDICES)
    conn.commit()
    conn.close()
    _log("INFO", f"Schema created/verified at {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/output/reviews.db")
    args = parser.parse_args()
    try:
        build_schema(args.db)
    except Exception as exc:
        _log("FAIL", f"Database write failed: {exc}. Check disk space and file permissions at {args.db}.")
        sys.exit(1)

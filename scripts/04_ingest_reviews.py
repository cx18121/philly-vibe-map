"""
04_ingest_reviews.py
Stream yelp_academic_dataset_review.json, filter to Philadelphia businesses,
write to reviews table in reviews.db.

Usage:
    YELP_DATA_DIR=/path/to/yelp python scripts/04_ingest_reviews.py [--db data/output/reviews.db]
"""
from __future__ import annotations

import argparse
import datetime
import os
import sqlite3
import sys
from pathlib import Path

import orjson

BATCH_SIZE = 10_000
PROGRESS_INTERVAL = 100_000  # emit log line every N reviews written

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def ingest_reviews(review_path: str, db_path: str) -> dict:
    """Stream review NDJSON and insert all reviews for known Philadelphia businesses.

    Args:
        review_path: Path to yelp_academic_dataset_review.json
        db_path: Path to reviews.db (schema and businesses must already exist)

    Returns:
        dict: {total_scanned, written, skipped_unknown_biz, skipped_missing_fields}

    Raises:
        FileNotFoundError: if review_path does not exist
    """
    if not Path(review_path).exists():
        raise FileNotFoundError(f"Review file not found: {review_path}")

    # Load known business_ids from DB — pre-filter before any INSERT
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    known_business_ids: set[str] = {
        row[0] for row in conn.execute("SELECT business_id FROM businesses")
    }
    _log("INFO", f"Loaded {len(known_business_ids):,} known Philadelphia business IDs from database")

    _log("INFO", "Review file open — streaming parse started")

    total_scanned = 0
    written = 0
    skipped_unknown_biz = 0
    skipped_missing_fields = 0
    batch: list[tuple] = []

    with open(review_path, "rb") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total_scanned += 1

            try:
                record = orjson.loads(line)
            except Exception:
                skipped_missing_fields += 1
                continue

            business_id = record.get("business_id")
            if business_id not in known_business_ids:
                skipped_unknown_biz += 1
                continue

            text = record.get("text")
            stars = record.get("stars")
            date_str = record.get("date", "")
            review_id = record.get("review_id")

            # DATA-03: text, stars, review_date, review_id are required
            if not text or stars is None or not date_str or not review_id:
                skipped_missing_fields += 1
                continue

            # Store date as YYYY-MM-DD only (strip time component if present)
            review_date = date_str[:10]  # "2021-06-15 18:30:00" -> "2021-06-15"

            batch.append((
                review_id,
                business_id,
                text,
                int(stars),
                review_date,
                "yelp",           # source platform (DATA-03)
                record.get("useful"),
                record.get("funny"),
                record.get("cool"),
            ))

            if len(batch) >= BATCH_SIZE:
                conn.executemany(
                    "INSERT OR IGNORE INTO reviews "
                    "(review_id, business_id, text, stars, review_date, source, useful, funny, cool) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    batch,
                )
                conn.commit()
                written += len(batch)
                batch.clear()

                if written % PROGRESS_INTERVAL == 0:
                    _log("INFO", f"Reviews written: {written:,}")

    # Flush remaining batch
    if batch:
        conn.executemany(
            "INSERT OR IGNORE INTO reviews "
            "(review_id, business_id, text, stars, review_date, source, useful, funny, cool) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            batch,
        )
        conn.commit()
        written += len(batch)

    conn.close()
    _log("INFO", f"Import complete — {written:,} total reviews in database")
    return {
        "total_scanned": total_scanned,
        "written": written,
        "skipped_unknown_biz": skipped_unknown_biz,
        "skipped_missing_fields": skipped_missing_fields,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/output/reviews.db")
    args = parser.parse_args()

    data_dir = os.environ.get("YELP_DATA_DIR")
    if not data_dir:
        _log("FAIL", "YELP_DATA_DIR not set. Export it to the directory containing the Yelp Open Dataset files.")
        sys.exit(1)

    review_file = Path(data_dir) / "yelp_academic_dataset_review.json"
    if not review_file.exists():
        _log("FAIL", f"Dataset file not found at {review_file}. Set YELP_DATA_DIR to the directory containing yelp_academic_dataset_review.json.")
        sys.exit(1)

    try:
        result = ingest_reviews(str(review_file), args.db)
        _log("INFO", f"Scanned: {result['total_scanned']:,} | Written: {result['written']:,} | Skipped (unknown biz): {result['skipped_unknown_biz']:,} | Skipped (bad data): {result['skipped_missing_fields']:,}")
    except Exception as exc:
        _log("FAIL", f"Database write failed: {exc}. Check disk space and file permissions at {args.db}.")
        sys.exit(1)

    # --- Write / merge ingest_stats.json sidecar ---
    import json as _json
    _stats_path = Path("data/output/ingest_stats.json")
    # Read existing sidecar written by 03_assign_neighbourhoods.py (may not exist on first run)
    _stats: dict = {}
    if _stats_path.exists():
        with open(_stats_path) as _f:
            _stats = _json.load(_f)
    # Merge this script's counts; overwrite keys for 04's domain
    _stats["duplicate_business_id"] = result["skipped_unknown_biz"]
    _stats["bad_timestamp"] = result["skipped_missing_fields"]
    _stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(_stats_path, "w") as _f:
        _json.dump(_stats, _f, indent=2)
    _log("INFO", f"Wrote ingest_stats.json: {_stats}")

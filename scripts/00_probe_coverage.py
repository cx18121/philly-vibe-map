"""
00_probe_coverage.py
Wave 0 gate: stream yelp_academic_dataset_business.json, count businesses
whose lat/lng falls inside the Manhattan+Brooklyn bounding box.

Usage:
    YELP_DATA_DIR=/path/to/yelp python scripts/00_probe_coverage.py

Decision thresholds:
    > 10,000 businesses  -> proceed normally
    500-10,000           -> proceed with reduced review target
    < 500                -> STOP -- dataset likely does not cover NYC
"""
from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path

import orjson
from shapely.geometry import Point, box

# Manhattan + Brooklyn bounding box (minx, miny, maxx, maxy)
NYC_BBOX = box(-74.05, 40.57, -73.70, 40.92)

# ANSI color codes (applied only when stdout is a TTY)
_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def probe_coverage(business_path: str) -> dict:
    """Stream business NDJSON and count records inside NYC bounding box.

    Args:
        business_path: Path to yelp_academic_dataset_business.json

    Returns:
        dict with keys: total_businesses, nyc_bbox_businesses, missing_coords, nyc_pct

    Raises:
        FileNotFoundError: if business_path does not exist
    """
    path = Path(business_path)
    if not path.exists():
        raise FileNotFoundError(f"Business file not found: {business_path}")

    total = 0
    nyc_count = 0
    missing_coords = 0

    with open(path, "rb") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            record = orjson.loads(line)
            lat = record.get("latitude")
            lon = record.get("longitude")
            if lat is None or lon is None:
                missing_coords += 1
                continue
            pt = Point(float(lon), float(lat))
            if NYC_BBOX.contains(pt):
                nyc_count += 1

    nyc_pct = round(nyc_count / total * 100, 2) if total > 0 else 0.0
    return {
        "total_businesses": total,
        "nyc_bbox_businesses": nyc_count,
        "missing_coords": missing_coords,
        "nyc_pct": nyc_pct,
    }


if __name__ == "__main__":
    data_dir = os.environ.get("YELP_DATA_DIR")
    if not data_dir:
        _log("FAIL", "YELP_DATA_DIR not set. Export it to the directory containing the Yelp Open Dataset files.")
        sys.exit(1)

    business_file = Path(data_dir) / "yelp_academic_dataset_business.json"
    if not business_file.exists():
        _log("FAIL", f"Dataset file not found at {business_file}. Set YELP_DATA_DIR to the directory containing yelp_academic_dataset_business.json.")
        sys.exit(1)

    _log("INFO", "Yelp business file open -- streaming parse started")
    result = probe_coverage(str(business_file))

    _log("INFO", f"NYC businesses identified: {result['nyc_bbox_businesses']} records")
    _log("INFO", f"Total businesses scanned: {result['total_businesses']}")
    _log("INFO", f"Missing lat/lng: {result['missing_coords']}")

    print(json.dumps(result, indent=2))

    if result["nyc_bbox_businesses"] < 500:
        _log("WARN", (
            f"Only {result['nyc_bbox_businesses']} NYC businesses found. "
            "Dataset may not cover New York City. "
            "DO NOT proceed to ingestion -- consult project owner."
        ))
    elif result["nyc_bbox_businesses"] < 10_000:
        _log("WARN", (
            f"{result['nyc_bbox_businesses']} NYC businesses found -- below 10k. "
            "Proceeding is possible with a reduced review target."
        ))
    else:
        _log("INFO", f"Coverage adequate ({result['nyc_bbox_businesses']} businesses). Proceed to ingestion.")

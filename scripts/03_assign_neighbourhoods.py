"""
03_assign_neighbourhoods.py
Stream Yelp business NDJSON, assign each Philadelphia business to a neighbourhood
via GeoPandas sjoin, write results to the businesses table in reviews.db.

Usage:
    YELP_DATA_DIR=/path/to/yelp python scripts/03_assign_neighbourhoods.py [--db data/output/reviews.db]
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Optional

import geopandas as gpd
import orjson
from shapely.geometry import Point, box

# Philadelphia bounding box (minx, miny, maxx, maxy) — slightly larger than city boundary
PHILLY_BBOX = box(-75.28, 39.87, -74.96, 40.14)

BOUNDARY_PATH = "data/boundaries/philadelphia_neighborhoods.geojson"
CURATION_PATH = "data/boundaries/neighborhood_name_curation.json"

BATCH_SIZE = 10_000
WARN_SUPPRESS_THRESHOLD = 1_000

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def assign_neighbourhoods(
    business_path: str,
    db_path: str,
    neighbourhood_gdf: Optional[gpd.GeoDataFrame] = None,
    curation: Optional[dict] = None,
) -> dict:
    """Stream business NDJSON, spatially join to Philadelphia neighbourhoods, write to SQLite.

    Args:
        business_path: Path to yelp_academic_dataset_business.json
        db_path: Path to reviews.db (schema must already exist)
        neighbourhood_gdf: Optional pre-loaded GeoDataFrame (for testing). If None,
            loads from BOUNDARY_PATH.
        curation: Optional dict of NEIGHBORHOOD_NUMBER -> display name (for testing).
            If None, loads from CURATION_PATH.

    Returns:
        dict: {total_scanned, philly_candidates, assigned, missing_coords, outside_neighbourhood}
    """
    import pandas as pd

    # Load Philadelphia neighbourhood boundaries
    if neighbourhood_gdf is None:
        nta_gdf = gpd.read_file(BOUNDARY_PATH)
    else:
        nta_gdf = neighbourhood_gdf

    # CRS guard — both sides must be EPSG:4326 before sjoin
    assert nta_gdf.crs is not None and nta_gdf.crs.to_epsg() == 4326, (
        f"Neighbourhood GeoDataFrame CRS must be EPSG:4326, got {nta_gdf.crs}"
    )

    # Load name curation map
    if curation is None:
        with open(CURATION_PATH) as f:
            curation = json.load(f)

    # First pass: stream businesses, pre-filter to Philadelphia bounding box
    _log("INFO", "Yelp business file open — streaming parse started")
    total_scanned = 0
    missing_coords = 0
    warn_count = 0
    philly_records: list[dict] = []

    with open(business_path, "rb") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total_scanned += 1
            record = orjson.loads(line)
            lat = record.get("latitude")
            lon = record.get("longitude")
            if lat is None or lon is None:
                missing_coords += 1
                if missing_coords <= WARN_SUPPRESS_THRESHOLD:
                    _log("WARN", f"Skipped business {record.get('business_id', '?')}: missing lat/lng")
                continue
            pt = Point(float(lon), float(lat))
            if PHILLY_BBOX.contains(pt):
                philly_records.append({
                    "business_id": record["business_id"],
                    "name": record.get("name", ""),
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "city": record.get("city"),
                    "state": record.get("state"),
                    "attributes": json.dumps(record.get("attributes") or {}),
                    "_geometry": pt,
                })

    if missing_coords > WARN_SUPPRESS_THRESHOLD:
        _log("WARN", f"{missing_coords} records skipped for missing lat/lng (suppressed individual warnings)")

    _log("INFO", f"NYC businesses identified: {len(philly_records)} records")

    if not philly_records:
        _log("WARN", "No Philadelphia businesses found — businesses table will be empty. Review probe results.")
        return {
            "total_scanned": total_scanned,
            "philly_candidates": 0,
            "assigned": 0,
            "missing_coords": missing_coords,
            "outside_neighbourhood": 0,
        }

    # Spatial join: build GeoDataFrame from accumulated Philadelphia records
    df = pd.DataFrame(philly_records)
    gdf_biz = gpd.GeoDataFrame(df, geometry="_geometry", crs="EPSG:4326")
    assert gdf_biz.crs.to_epsg() == 4326  # sanity check on business side

    joined = gpd.sjoin(
        gdf_biz,
        nta_gdf[["NEIGHBORHOOD_NUMBER", "NEIGHBORHOOD_NAME", "geometry"]],
        how="left",
        predicate="within",
    )
    _log("INFO", f"Spatial join complete — {joined['NEIGHBORHOOD_NUMBER'].notna().sum()} businesses assigned to neighbourhoods")

    # Write to SQLite
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    batch: list[tuple] = []
    assigned = 0
    outside_neighbourhood = 0

    for _, row in joined.iterrows():
        nbr_num = row.get("NEIGHBORHOOD_NUMBER")
        nbr_name = None
        if pd.notna(nbr_num):
            nbr_name = curation.get(str(nbr_num), row.get("NEIGHBORHOOD_NAME"))
            assigned += 1
        else:
            outside_neighbourhood += 1

        batch.append((
            row["business_id"],
            row["name"],
            row["latitude"],
            row["longitude"],
            str(nbr_num) if pd.notna(nbr_num) else None,
            nbr_name,
            row.get("city"),
            row.get("state"),
            row["attributes"],
        ))

        if len(batch) >= BATCH_SIZE:
            conn.executemany(
                "INSERT OR IGNORE INTO businesses "
                "(business_id, name, latitude, longitude, neighbourhood_id, neighbourhood_name, city, state, attributes) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                batch,
            )
            conn.commit()
            batch.clear()

    if batch:
        conn.executemany(
            "INSERT OR IGNORE INTO businesses "
            "(business_id, name, latitude, longitude, neighbourhood_id, neighbourhood_name, city, state, attributes) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            batch,
        )
        conn.commit()

    conn.close()
    return {
        "total_scanned": total_scanned,
        "philly_candidates": len(philly_records),
        "assigned": assigned,
        "missing_coords": missing_coords,
        "outside_neighbourhood": outside_neighbourhood,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/output/reviews.db")
    args = parser.parse_args()

    data_dir = os.environ.get("YELP_DATA_DIR")
    if not data_dir:
        _log("FAIL", "YELP_DATA_DIR not set. Export it to the directory containing the Yelp Open Dataset files.")
        sys.exit(1)

    business_file = Path(data_dir) / "yelp_academic_dataset_business.json"
    if not business_file.exists():
        _log("FAIL", f"Dataset file not found at {business_file}.")
        sys.exit(1)

    try:
        from scripts.build_schema import build_schema
        build_schema(args.db)
        result = assign_neighbourhoods(str(business_file), args.db)
        _log("INFO", f"Import complete — {result['assigned']} businesses assigned to neighbourhoods")
        _log("INFO", f"Outside neighbourhood polygons (no neighbourhood_id): {result['outside_neighbourhood']}")
    except Exception as exc:
        _log("FAIL", f"Database write failed: {exc}. Check disk space and file permissions at {args.db}.")
        sys.exit(1)

    # --- Write ingest_stats.json sidecar (first write; 04 will merge into this) ---
    import json as _json
    _stats_path = Path("data/output/ingest_stats.json")
    _stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(_stats_path, "w") as _f:
        _json.dump(
            {
                "missing_lat_lng": result["missing_coords"],
                "outside_nta": result["outside_neighbourhood"],
            },
            _f,
            indent=2,
        )
    _log("INFO", f"Wrote ingest_stats.json: missing_lat_lng={result['missing_coords']}, outside_nta={result['outside_neighbourhood']}")

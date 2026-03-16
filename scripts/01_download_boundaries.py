"""
01_download_boundaries.py
Download Philadelphia neighbourhood boundary GeoJSON from OpenDataPhilly
(ArcGIS FeatureServer), write to data/boundaries/philadelphia_neighborhoods.geojson.

Project pivoted from NYC to Philadelphia — see .planning/phases/01-data-foundation/01-01-DECISION.md.

Field mapping vs original NYC NTA plan:
  NTACode  -> NEIGHBORHOOD_NUMBER  (e.g., "001")
  NTAName  -> NEIGHBORHOOD_NAME    (e.g., "Fishtown - Lower Kensington")

Usage:
    python scripts/01_download_boundaries.py
"""
from __future__ import annotations

import datetime
import io
import json
import sys
from pathlib import Path

import geopandas as gpd
import requests

# OpenDataPhilly / PennShare ArcGIS FeatureServer — Philadelphia neighbourhood polygons
# Source: services1.arcgis.com PennShare::philadelphia-neighborhood-boundaries (public)
GEOJSON_URL = (
    "https://services1.arcgis.com/jOy9iZUXBy03ojXb/arcgis/rest/services"
    "/Philadelphia_Neighborhood_Boundaries/FeatureServer/0/query"
    "?where=1%3D1&outFields=*&f=geojson"
)

OUTPUT_DIR = Path("data/boundaries")
OUTPUT_PATH = OUTPUT_DIR / "philadelphia_neighborhoods.geojson"

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def download_philadelphia_boundaries(output_path: str) -> gpd.GeoDataFrame:
    """Download Philadelphia neighbourhood polygons from OpenDataPhilly ArcGIS FeatureServer.

    Produces a GeoDataFrame with key columns:
      - NEIGHBORHOOD_NUMBER: unique identifier string, e.g. "001"
      - NEIGHBORHOOD_NAME:   official neighbourhood name, e.g. "Fishtown - Lower Kensington"
    CRS: EPSG:4326 (WGS84) — the FeatureServer returns WGS84 by default.

    Args:
        output_path: Where to write the GeoJSON file.

    Returns:
        GeoDataFrame with all 159 Philadelphia neighbourhood polygons, EPSG:4326.

    Raises:
        requests.HTTPError: if the download fails.
        ValueError: if the response contains no features.
    """
    _log("INFO", "Downloading Philadelphia neighbourhood boundaries from OpenDataPhilly...")
    resp = requests.get(GEOJSON_URL, timeout=60)
    resp.raise_for_status()
    _log("INFO", f"Downloaded {len(resp.content):,} bytes")

    gdf = gpd.read_file(io.BytesIO(resp.content))
    _log("INFO", f"Loaded {len(gdf)} neighbourhood features")

    if len(gdf) == 0:
        raise ValueError(
            "FeatureServer returned 0 features. Check the URL and service availability."
        )

    # Verify CRS — ArcGIS FeatureServer with f=geojson always returns WGS84
    assert gdf.crs is not None, "GeoJSON has no CRS"
    if gdf.crs.to_epsg() != 4326:
        _log("WARN", f"CRS is {gdf.crs}; reprojecting to EPSG:4326")
        gdf = gdf.to_crs("EPSG:4326")

    # Verify required columns present
    for col in ("NEIGHBORHOOD_NUMBER", "NEIGHBORHOOD_NAME"):
        if col not in gdf.columns:
            raise ValueError(
                f"Expected column '{col}' not found in downloaded data. "
                f"Columns present: {list(gdf.columns)}"
            )

    # Write filtered GeoJSON (keep only essential columns + geometry to reduce file size)
    keep_cols = [
        "NEIGHBORHOOD_NUMBER",
        "NEIGHBORHOOD_NAME",
        "DISTRICT_NO",
        "PLANNING_PARTNER",
        "geometry",
    ]
    keep_cols = [c for c in keep_cols if c in gdf.columns]
    out_gdf = gdf[keep_cols].copy()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out_gdf.to_file(str(out), driver="GeoJSON")
    _log("INFO", f"Boundary GeoJSON written: {out}")
    return out_gdf


if __name__ == "__main__":
    try:
        gdf = download_philadelphia_boundaries(str(OUTPUT_PATH))
        _log("INFO", f"Philadelphia neighbourhoods: {len(gdf)}")
        _log("INFO", f"CRS: EPSG:{gdf.crs.to_epsg()}")
        _log("INFO", f"Columns: {list(gdf.columns)}")
        sample = gdf["NEIGHBORHOOD_NAME"].sort_values().head(5).tolist()
        _log("INFO", f"Sample names: {sample}")
    except Exception as exc:
        _log("FAIL", str(exc))
        sys.exit(1)

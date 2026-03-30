"""Artifact loading for the backend API.

Loads all pipeline artifacts into memory at startup for zero-cost serving.
"""
from __future__ import annotations

import datetime
import json
import math
import sys
from pathlib import Path


_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def load_artifacts(artifacts_dir: Path) -> dict:
    """Load all serving artifacts from disk into a dict for app.state.

    Args:
        artifacts_dir: Path to the artifacts directory.

    Returns:
        Dict with keys: geojson, geojson_bytes, vibe_scores, temporal,
        quotes, topics, review_counts, faiss_index, faiss_id_map,
        faiss_reverse, valid_nids, nid_to_name
    """
    import faiss

    # GeoJSON — loaded first; dominant_vibe will be patched after vibe_scores normalisation
    with open(artifacts_dir / "enriched_geojson.geojson") as f:
        geojson = json.load(f)

    # Vibe scores — vibe_score.py already applies cross-neighbourhood z-score
    # normalization + clip, so scores are already on a comparable scale.
    with open(artifacts_dir / "vibe_scores.json") as f:
        vibe_scores = json.load(f)
    archetypes = list(next(iter(vibe_scores.values())).keys())
    _log("INFO", f"Vibe scores loaded: {len(vibe_scores)} neighbourhoods")

    # Patch GeoJSON dominant_vibe/vibe_scores with normalised values
    for feature in geojson["features"]:
        nid = feature.get("properties", {}).get("NEIGHBORHOOD_NUMBER")
        if nid and nid in vibe_scores:
            scores = vibe_scores[nid]
            dominant = max(scores, key=scores.get)
            feature["properties"]["vibe_scores"] = scores
            feature["properties"]["dominant_vibe"] = dominant
            feature["properties"]["dominant_vibe_score"] = scores[dominant]
    geojson_bytes = json.dumps(geojson).encode("utf-8")
    _log("INFO", f"GeoJSON patched with normalised vibes: {len(geojson['features'])} features, {len(geojson_bytes):,} bytes pre-serialized")

    # Temporal series — apply the same cross-neighbourhood z-score normalization
    # per year per archetype so time-slider colors are consistent with the static map.

    with open(artifacts_dir / "temporal_series.json") as f:
        temporal = json.load(f)

    all_years = sorted({year for nid_data in temporal.values() for year in nid_data})
    for year in all_years:
        nids_this_year = [nid for nid, d in temporal.items() if year in d]
        if not nids_this_year:
            continue
        for arch in archetypes:
            vals = [temporal[nid][year].get(arch, 0.0) for nid in nids_this_year]
            mean = sum(vals) / len(vals)
            variance = sum((v - mean) ** 2 for v in vals) / len(vals)
            std = math.sqrt(variance)
            for nid, v in zip(nids_this_year, vals):
                normed = (v - mean) / std if std > 0 else v - mean
                temporal[nid][year][arch] = max(0.0, normed)

    _log("INFO", f"Temporal series loaded and normalised: {len(temporal)} neighbourhoods, {len(all_years)} years")

    # Representative quotes
    with open(artifacts_dir / "representative_quotes.json") as f:
        quotes = json.load(f)
    _log("INFO", f"Representative quotes loaded: {len(quotes)} neighbourhoods")

    # Neighbourhood topics
    with open(artifacts_dir / "neighbourhood_topics.json") as f:
        topics = json.load(f)
    _log("INFO", f"Neighbourhood topics loaded: {len(topics)} neighbourhoods")

    # Review counts
    with open(artifacts_dir / "review_counts.json") as f:
        review_counts = json.load(f)
    _log("INFO", f"Review counts loaded: {len(review_counts)} neighbourhoods")

    # FAISS index
    faiss_index = faiss.read_index(str(artifacts_dir / "faiss_index.bin"))
    _log("INFO", f"FAISS index loaded: {faiss_index.ntotal} vectors, dim={faiss_index.d}")

    # FAISS ID map
    with open(artifacts_dir / "faiss_id_map.json") as f:
        faiss_id_map = json.load(f)
    _log("INFO", f"FAISS ID map loaded: {len(faiss_id_map)} entries")

    # Reverse map: neighbourhood_id -> FAISS integer index
    faiss_reverse = {v: int(k) for k, v in faiss_id_map.items()}

    # Valid neighbourhood IDs
    valid_nids = set(vibe_scores.keys())
    _log("INFO", f"Valid neighbourhood IDs: {len(valid_nids)}")

    # Neighbourhood name lookup from GeoJSON features
    nid_to_name: dict[str, str] = {}
    for feature in geojson["features"]:
        props = feature.get("properties", {})
        nid = props.get("NEIGHBORHOOD_NUMBER")
        name = props.get("NEIGHBORHOOD_NAME")
        if nid and name:
            nid_to_name[nid] = name
    _log("INFO", f"Neighbourhood name lookup: {len(nid_to_name)} entries")

    return {
        "geojson": geojson,
        "geojson_bytes": geojson_bytes,
        "vibe_scores": vibe_scores,
        "temporal": temporal,
        "quotes": quotes,
        "topics": topics,
        "review_counts": review_counts,
        "faiss_index": faiss_index,
        "faiss_id_map": faiss_id_map,
        "faiss_reverse": faiss_reverse,
        "valid_nids": valid_nids,
        "nid_to_name": nid_to_name,
    }

"""Stage 5: Temporal drift -- year-bucketed vibe scoring."""
from __future__ import annotations

import datetime
import json
import os
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from pipeline.stages.vibe_score import (
    compute_topic_centroids,
    load_review_metadata,
    score_neighbourhood_vibes,
)

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"

MIN_REVIEWS_PER_YEAR = int(os.environ.get("TEMPORAL_MIN_REVIEWS_PER_YEAR", "1000"))


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def run_temporal(db_path: str, artifacts_dir: Path, force: bool = False) -> dict:
    """Compute year-bucketed vibe scores for temporal drift analysis.

    Year buckets use equal weights (no recency decay within a bucket).

    Outputs:
        artifacts_dir / temporal_series.json -- {neighbourhood_id: {year: {archetype: score}}}
    """
    output_path = artifacts_dir / "temporal_series.json"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'temporal': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    _log("INFO", "Stage 'temporal': starting...")

    # Re-read threshold at call time (tests may have changed env var after import)
    min_reviews = int(os.environ.get("TEMPORAL_MIN_REVIEWS_PER_YEAR", "1000"))

    # 1. Determine year range from actual data
    conn = sqlite3.connect(db_path)
    min_year, max_year = conn.execute(
        """
        SELECT MIN(CAST(SUBSTR(r.review_date, 1, 4) AS INTEGER)),
               MAX(CAST(SUBSTR(r.review_date, 1, 4) AS INTEGER))
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
        """
    ).fetchone()
    conn.close()

    _log("INFO", f"Data year range: {min_year}-{max_year}")

    # 2. Load shared artifacts
    embeddings = np.load(artifacts_dir / "embeddings.npy")
    review_ids = np.load(artifacts_dir / "review_ids.npy")
    with open(artifacts_dir / "topic_assignments.json") as f:
        topic_assignments = json.load(f)

    # 3. Compute topic centroids (shared across all years)
    topic_centroids = compute_topic_centroids(embeddings, review_ids, topic_assignments)
    _log("INFO", f"Computed {len(topic_centroids)} topic centroids")

    # 4. Embed archetype seed phrases
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    archetypes_path = Path(__file__).parent.parent / "archetypes.json"
    with open(archetypes_path) as f:
        archetypes = json.load(f)

    archetype_centroids: dict[str, np.ndarray] = {}
    for name, phrases in archetypes.items():
        phrase_embs = model.encode(phrases)
        archetype_centroids[name] = phrase_embs.mean(axis=0)

    _log("INFO", f"Embedded {len(archetypes)} archetype centroids")

    # 5. Load review metadata
    review_meta = load_review_metadata(db_path)
    all_nids = sorted(set(nid for _, (_, nid) in review_meta.items()))
    _log("INFO", f"Loaded metadata for {len(review_meta)} reviews across {len(all_nids)} neighbourhoods")

    # 6. Per-year bucketing and scoring
    temporal_series: dict[str, dict[str, dict[str, float]]] = {
        nid: {} for nid in all_nids
    }
    years_used = []

    for year in range(min_year, max_year + 1):
        year_str = str(year)

        # Filter reviews for this year
        year_reviews = {
            rid: meta for rid, meta in review_meta.items()
            if meta[0][:4] == year_str
        }

        if len(year_reviews) < min_reviews:
            _log("WARN", f"Year {year}: only {len(year_reviews)} reviews, skipping (min={min_reviews})")
            continue

        years_used.append(year_str)
        _log("INFO", f"Year {year}: {len(year_reviews)} reviews")

        for nid in all_nids:
            nid_reviews = [
                rid for rid, (_, n) in year_reviews.items() if n == nid
            ]

            if not nid_reviews:
                # No reviews for this neighbourhood in this year -- zero scores
                temporal_series[nid][year_str] = {a: 0.0 for a in archetypes}
                continue

            # Topic weights: equal weight = 1.0 per review (no decay)
            topic_weights: dict[int, float] = defaultdict(float)
            for rid in nid_reviews:
                tid = topic_assignments.get(str(rid))
                if tid is not None and tid != -1 and tid in topic_centroids:
                    topic_weights[tid] += 1.0

            # Score vibes using shared helper
            scores = score_neighbourhood_vibes(
                topic_weights, topic_centroids, archetype_centroids
            )
            temporal_series[nid][year_str] = scores

    # 7. Validate no NaN values
    nan_count = 0
    for nid, years in temporal_series.items():
        for year, scores in years.items():
            for arch, val in scores.items():
                if np.isnan(val):
                    _log("WARN", f"NaN detected: nid={nid}, year={year}, arch={arch}, setting to 0.0")
                    temporal_series[nid][year][arch] = 0.0
                    nan_count += 1

    if nan_count > 0:
        _log("WARN", f"Fixed {nan_count} NaN values")

    # 8. Save artifact
    with open(output_path, "w") as f:
        json.dump(temporal_series, f, indent=2)

    _log("INFO", f"Stage 'temporal': complete -- {len(temporal_series)} neighbourhoods, {len(years_used)} years")

    return {
        "skipped": False,
        "n_neighbourhoods": len(temporal_series),
        "years": sorted(years_used),
        "n_years": len(years_used),
    }

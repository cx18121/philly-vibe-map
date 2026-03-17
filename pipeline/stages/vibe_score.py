"""Stage 3: Score 6 vibe archetypes via cosine similarity."""
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

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


# ---------------------------------------------------------------------------
# Recency weighting (public -- reused by temporal.py for reference_date logic)
# ---------------------------------------------------------------------------

HALF_LIFE_DAYS = int(os.environ.get("VIBE_HALF_LIFE_DAYS", "365"))
MIN_WEIGHT = 1e-6


def compute_recency_weight(
    review_date: str,
    reference_date: str,
    half_life_days: int = HALF_LIFE_DAYS,
) -> float:
    """Compute exponential decay weight in log-space.

    Args:
        review_date: ISO date string "YYYY-MM-DD"
        reference_date: ISO date string for "now"
        half_life_days: decay half-life in days

    Returns:
        float weight in [MIN_WEIGHT, 1.0]
    """
    d_review = datetime.datetime.strptime(review_date[:10], "%Y-%m-%d")
    d_ref = datetime.datetime.strptime(reference_date[:10], "%Y-%m-%d")
    delta_days = (d_ref - d_review).days
    if delta_days <= 0:
        return 1.0
    decay_lambda = np.log(2) / half_life_days
    log_weight = -decay_lambda * delta_days
    weight = np.exp(log_weight)
    return float(max(weight, MIN_WEIGHT))


# ---------------------------------------------------------------------------
# Helper: load review metadata from DB
# ---------------------------------------------------------------------------

def load_review_metadata(db_path: str) -> dict:
    """Load {rowid: (review_date, neighbourhood_id)} from SQLite.

    Returns:
        dict mapping review rowid (int) to (review_date_str, neighbourhood_id_str)
    """
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """
        SELECT r.rowid, r.review_date, b.neighbourhood_id
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
        ORDER BY r.rowid
        """
    ).fetchall()
    conn.close()
    return {rowid: (review_date, nid) for rowid, review_date, nid in rows}


# ---------------------------------------------------------------------------
# Helper: compute topic centroids from embeddings
# ---------------------------------------------------------------------------

def compute_topic_centroids(
    embeddings: np.ndarray,
    review_ids: np.ndarray,
    topic_assignments: dict,
) -> dict:
    """Compute mean embedding (centroid) for each topic.

    Args:
        embeddings: shape (N, 384) float32
        review_ids: shape (N,) int64 -- aligned to embeddings rows
        topic_assignments: {review_rowid_str: topic_id_int}

    Returns:
        dict {topic_id_int: np.ndarray of shape (384,)}
    """
    topic_indices: dict[int, list[int]] = defaultdict(list)
    for idx, rid in enumerate(review_ids):
        tid = topic_assignments.get(str(int(rid)))
        if tid is not None and tid != -1:
            topic_indices[tid].append(idx)

    topic_centroids = {}
    for tid, indices in topic_indices.items():
        topic_centroids[tid] = embeddings[indices].mean(axis=0)
    return topic_centroids


# ---------------------------------------------------------------------------
# Helper: score neighbourhood vibes given topic weights and centroids
# ---------------------------------------------------------------------------

def score_neighbourhood_vibes(
    topic_weights: dict[int, float],
    topic_centroids: dict[int, np.ndarray],
    archetype_centroids: dict[str, np.ndarray],
) -> dict[str, float]:
    """Compute vibe scores for one neighbourhood.

    Args:
        topic_weights: {topic_id: aggregated_weight} for this neighbourhood
        topic_centroids: {topic_id: centroid_embedding}
        archetype_centroids: {archetype_name: centroid_embedding}

    Returns:
        {archetype_name: float score}
    """
    total_weight = sum(topic_weights.values())
    if total_weight == 0:
        return {a: 0.0 for a in archetype_centroids}

    scores = {}
    for arch_name, arch_centroid in archetype_centroids.items():
        weighted_sim = 0.0
        for tid, tw in topic_weights.items():
            sim = cosine_similarity(
                topic_centroids[tid].reshape(1, -1),
                arch_centroid.reshape(1, -1),
            )[0, 0]
            weighted_sim += (tw / total_weight) * sim
        scores[arch_name] = float(weighted_sim)
    return scores


# ---------------------------------------------------------------------------
# Main stage entry point
# ---------------------------------------------------------------------------

def run_vibe_score(db_path: str, artifacts_dir: Path, force: bool = False) -> dict:
    """Compute vibe archetype scores per neighbourhood.

    Outputs:
        artifacts_dir / vibe_scores.json -- {neighbourhood_id: {archetype: score}}
    """
    output_path = artifacts_dir / "vibe_scores.json"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'vibe_score': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    _log("INFO", "Stage 'vibe_score': starting...")

    # 1. Load archetype seed phrases and embed them
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

    # 2. Load pre-computed embeddings and topic assignments
    embeddings = np.load(artifacts_dir / "embeddings.npy")
    review_ids = np.load(artifacts_dir / "review_ids.npy")
    with open(artifacts_dir / "topic_assignments.json") as f:
        topic_assignments = json.load(f)

    _log("INFO", f"Loaded {len(embeddings)} embeddings, {len(topic_assignments)} topic assignments")

    # 3. Compute topic centroids
    topic_centroids = compute_topic_centroids(embeddings, review_ids, topic_assignments)
    _log("INFO", f"Computed {len(topic_centroids)} topic centroids")

    # 4. Load review metadata from DB
    review_meta = load_review_metadata(db_path)
    _log("INFO", f"Loaded metadata for {len(review_meta)} reviews")

    # 5. Determine reference date (most recent review)
    reference_date = max(date for _, (date, _) in review_meta.items())
    _log("INFO", f"Reference date for recency weighting: {reference_date}")

    # 6. Compute per-neighbourhood vibe scores
    all_nids = sorted(set(nid for _, (_, nid) in review_meta.items()))
    neighbourhood_scores: dict[str, dict[str, float]] = {}

    for nid in all_nids:
        # Get reviews for this neighbourhood
        nid_reviews = [
            (rid, review_meta[rid])
            for rid in review_meta
            if review_meta[rid][1] == nid
        ]

        # Weighted topic distribution with recency
        topic_weights: dict[int, float] = defaultdict(float)
        for rid, (rdate, _) in nid_reviews:
            tid = topic_assignments.get(str(rid))
            if tid is not None and tid != -1 and tid in topic_centroids:
                w = compute_recency_weight(rdate, reference_date)
                topic_weights[tid] += w

        # Score vibes
        scores = score_neighbourhood_vibes(
            topic_weights, topic_centroids, archetype_centroids
        )
        neighbourhood_scores[nid] = scores

    # 7. Save artifact
    with open(output_path, "w") as f:
        json.dump(neighbourhood_scores, f, indent=2)

    _log("INFO", f"Stage 'vibe_score': complete -- {len(neighbourhood_scores)} neighbourhoods scored")

    return {
        "skipped": False,
        "n_neighbourhoods": len(neighbourhood_scores),
        "archetypes": list(archetypes.keys()),
    }

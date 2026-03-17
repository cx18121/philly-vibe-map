"""Stage 1: Embed all reviews with sentence-transformer (all-MiniLM-L6-v2)."""
from __future__ import annotations

import datetime
import os
import sqlite3
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def iter_reviews(db_path: str, batch_size: int = 50_000):
    """Yield batches of (rowid, text, neighbourhood_id) from SQLite.

    Uses fetchmany for memory-efficient chunked reading.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        """
        SELECT r.rowid, r.text, b.neighbourhood_id
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
        ORDER BY r.rowid
        """
    )
    while True:
        batch = cursor.fetchmany(batch_size)
        if not batch:
            break
        yield batch
    conn.close()


def run_embed(db_path: str, artifacts_dir: Path, force: bool = False) -> dict:
    """Generate sentence embeddings for all reviews.

    Outputs:
        artifacts_dir / embeddings.npy  -- shape (n_reviews, 384), float32
        artifacts_dir / review_ids.npy  -- shape (n_reviews,), int64
    """
    output_path = artifacts_dir / "embeddings.npy"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'embed': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    _log("INFO", "Stage 'embed': starting...")

    # Load model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Configurable encoding batch size
    embed_batch_size = int(os.environ.get("EMBED_BATCH_SIZE", "256"))

    # Count total for progress logging (cheap query)
    conn = sqlite3.connect(db_path)
    (estimated_total,) = conn.execute(
        """
        SELECT COUNT(*)
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
        """
    ).fetchone()
    conn.close()
    _log("INFO", f"Stage 'embed': {estimated_total:,} reviews to embed")

    all_embeddings: list[np.ndarray] = []
    all_ids: list[int] = []
    total_done = 0

    for batch in iter_reviews(db_path, batch_size=50_000):
        ids = [row[0] for row in batch]
        texts = [row[1] for row in batch]

        embs = model.encode(
            texts,
            batch_size=embed_batch_size,
            show_progress_bar=True,
            normalize_embeddings=False,
        )

        all_embeddings.append(embs)
        all_ids.extend(ids)
        total_done += len(batch)
        _log("INFO", f"Embedded {total_done}/{estimated_total} reviews")

    # Save artifacts
    embeddings = np.vstack(all_embeddings)  # shape (N, 384), dtype float32
    review_ids = np.array(all_ids, dtype=np.int64)  # shape (N,)

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    np.save(artifacts_dir / "embeddings.npy", embeddings)
    np.save(artifacts_dir / "review_ids.npy", review_ids)

    n = embeddings.shape[0]
    dims = embeddings.shape[1]
    _log("INFO", f"Stage 'embed': complete -- {n:,} reviews, {dims}D embeddings saved")

    return {"skipped": False, "count": n, "dimensions": dims}

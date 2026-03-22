"""Stage 2: BERTopic topic discovery with HDBSCAN tuning and outlier reduction."""
from __future__ import annotations

import datetime
import json
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
from bertopic import BERTopic
from hdbscan import HDBSCAN
from umap import UMAP

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def _load_texts_by_rowid_order(db_path: str) -> list[str]:
    """Load review texts from SQLite in rowid order (matching embed stage order).

    Uses the same query and ORDER BY as the embedding stage to guarantee
    alignment between texts and embeddings.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        """
        SELECT r.text
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
        ORDER BY r.rowid
        """
    )
    texts = [row[0] for row in cursor]
    conn.close()
    return texts


def run_topic_model(db_path: str, artifacts_dir: Path, force: bool = False) -> dict:
    """Fit BERTopic on pre-computed embeddings, reduce outliers, save model.

    Outputs:
        artifacts_dir / bertopic_model/       -- safetensors serialized model
        artifacts_dir / topic_assignments.json -- {review_id: topic_id}
    """
    output_path = artifacts_dir / "bertopic_model"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'topic_model': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    _log("INFO", "Stage 'topic_model': starting...")

    checkpoint_path = artifacts_dir / "_topics_checkpoint.npy"
    if force and checkpoint_path.exists():
        checkpoint_path.unlink()
        _log("INFO", "Cleared stale transform checkpoint (--force)")

    # ---- Load pre-computed embeddings ----
    embeddings = np.load(artifacts_dir / "embeddings.npy")
    review_ids = np.load(artifacts_dir / "review_ids.npy")
    _log("INFO", f"Loaded embeddings: {embeddings.shape}, review_ids: {review_ids.shape}")

    # ---- Load review texts (needed for c-TF-IDF) ----
    docs = _load_texts_by_rowid_order(db_path)
    assert len(docs) == len(review_ids), (
        f"Text count {len(docs)} != review_ids count {len(review_ids)}"
    )
    _log("INFO", f"Loaded {len(docs):,} review texts from DB")

    # ---- Subsample for fitting (UMAP/HDBSCAN can't handle ~1M points) ----
    FIT_SAMPLE = 100_000
    n_total = len(docs)
    if n_total > FIT_SAMPLE:
        rng = np.random.default_rng(42)
        sample_idx = rng.choice(n_total, size=FIT_SAMPLE, replace=False)
        sample_idx.sort()
        sample_docs = [docs[i] for i in sample_idx]
        sample_embeddings = embeddings[sample_idx]
        _log("INFO", f"Subsampled {FIT_SAMPLE:,} / {n_total:,} reviews for BERTopic fit")
    else:
        sample_idx = None
        sample_docs = docs
        sample_embeddings = embeddings

    # ---- Configure BERTopic components ----
    umap_model = UMAP(
        n_components=5,
        n_neighbors=15,
        min_dist=0.0,
        metric="cosine",
        low_memory=True,
        random_state=42,
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=10,
        min_samples=3,
        prediction_data=True,
    )

    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        calculate_probabilities=False,
        verbose=True,
    )

    # ---- Fit on sample, transform full corpus ----
    _log("INFO", "Fitting BERTopic on sample...")
    topic_model.fit_transform(sample_docs, embeddings=sample_embeddings)

    _log("INFO", f"Transforming full corpus ({n_total:,} reviews)...")
    TRANSFORM_BATCH = 25_000   # smaller batches = lower peak RAM per step
    BATCH_PAUSE_S = 2.0        # seconds to sleep between batches (lets RAM/CPU settle)

    # Resume from checkpoint if it exists and covers fewer than all reviews
    if checkpoint_path.exists():
        all_topics = list(np.load(checkpoint_path, allow_pickle=False).astype(int))
        resume_start = len(all_topics)
        _log("INFO", f"Resuming from checkpoint: {resume_start:,} / {n_total:,} already done")
    else:
        all_topics = []
        resume_start = 0

    for start in range(resume_start, n_total, TRANSFORM_BATCH):
        batch_docs = docs[start : start + TRANSFORM_BATCH]
        batch_emb = embeddings[start : start + TRANSFORM_BATCH]
        batch_topics, _ = topic_model.transform(batch_docs, embeddings=batch_emb)
        all_topics.extend(batch_topics)
        np.save(checkpoint_path, np.array(all_topics, dtype=np.int32))
        done = min(start + TRANSFORM_BATCH, n_total)
        _log("INFO", f"  Transformed {done:,} / {n_total:,} — pausing {BATCH_PAUSE_S}s")
        if done < n_total:
            time.sleep(BATCH_PAUSE_S)

    topics = all_topics
    probs = None  # not computed (calculate_probabilities=False)

    # ---- Outlier reduction chain ----
    outlier_count = sum(1 for t in topics if t == -1)
    outlier_rate = outlier_count / len(topics)
    _log("INFO", f"Initial outlier rate: {outlier_rate:.1%} ({outlier_count}/{len(topics)})")

    # Strategy 1: c-TF-IDF (best for short text)
    new_topics = topic_model.reduce_outliers(docs, topics, strategy="c-tf-idf")

    outlier_rate = sum(1 for t in new_topics if t == -1) / len(new_topics)
    _log("INFO", f"After c-TF-IDF reduction: {outlier_rate:.1%}")

    # Strategy 2: embeddings if still above 50% — sample-based to avoid OOM
    if outlier_rate > 0.5:
        _log("WARN", "Outlier rate still high; applying embeddings strategy on sample")
        outlier_mask = np.array([t == -1 for t in new_topics])
        outlier_indices = np.where(outlier_mask)[0]
        # cap at 200K to stay memory-safe
        if len(outlier_indices) > 200_000:
            rng2 = np.random.default_rng(0)
            outlier_indices = rng2.choice(outlier_indices, 200_000, replace=False)
            outlier_indices.sort()
        sub_docs = [docs[i] for i in outlier_indices]
        sub_emb = embeddings[outlier_indices]
        sub_topics = [new_topics[i] for i in outlier_indices]
        reduced = topic_model.reduce_outliers(
            sub_docs, sub_topics, strategy="embeddings", embeddings=sub_emb
        )
        for idx, new_t in zip(outlier_indices, reduced):
            new_topics[idx] = new_t
        outlier_rate = sum(1 for t in new_topics if t == -1) / len(new_topics)
        _log("INFO", f"After embeddings reduction: {outlier_rate:.1%}")

    # CRITICAL: update topic representations after outlier reduction
    # use sample docs/embeddings — c-TF-IDF update doesn't need the full corpus
    topic_model.update_topics(sample_docs, topics=[new_topics[i] for i in sample_idx] if sample_idx is not None else new_topics)

    # ---- Save BERTopic model ----
    _log("INFO", "Saving BERTopic model with safetensors serialization...")
    topic_model.save(
        str(artifacts_dir / "bertopic_model"),
        serialization="safetensors",
        save_ctfidf=True,
        save_embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    )

    # ---- Save topic assignments ----
    assignments = {str(int(rid)): int(tid) for rid, tid in zip(review_ids, new_topics)}
    assignments_path = artifacts_dir / "topic_assignments.json"
    with open(assignments_path, "w") as f:
        json.dump(assignments, f, indent=2)
    _log("INFO", f"Saved topic assignments to {assignments_path}")

    # Clean up transform checkpoint now that we have a complete run
    if checkpoint_path.exists():
        checkpoint_path.unlink()
        _log("INFO", "Removed transform checkpoint")

    # ---- Log summary ----
    n_topics = len(set(new_topics) - {-1})
    _log("INFO", f"Topics discovered: {n_topics}")
    _log("INFO", f"Final outlier rate: {outlier_rate:.1%}")

    try:
        topic_info = topic_model.get_topic_info()
        top_topics = topic_info.head(6)  # top 5 + outlier row
        for _, row in top_topics.iterrows():
            _log("INFO", f"  Topic {row['Topic']}: {row.get('Name', 'N/A')} ({row['Count']} docs)")
    except Exception:
        pass  # topic info display is non-critical

    _log("INFO", "Stage 'topic_model': complete")

    return {
        "skipped": False,
        "n_topics": n_topics,
        "outlier_rate": outlier_rate,
        "n_reviews": len(docs),
    }

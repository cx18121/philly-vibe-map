"""Stage 2: BERTopic topic discovery with HDBSCAN tuning and outlier reduction."""
from __future__ import annotations

import datetime
import json
import sqlite3
import sys
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

    # ---- Configure BERTopic components ----
    umap_model = UMAP(
        n_components=5,
        n_neighbors=15,
        min_dist=0.0,
        metric="cosine",
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
        calculate_probabilities=True,
        verbose=True,
    )

    # ---- Fit BERTopic with pre-computed embeddings ----
    _log("INFO", "Fitting BERTopic...")
    topics, probs = topic_model.fit_transform(docs, embeddings=embeddings)

    # ---- Outlier reduction chain ----
    outlier_count = sum(1 for t in topics if t == -1)
    outlier_rate = outlier_count / len(topics)
    _log("INFO", f"Initial outlier rate: {outlier_rate:.1%} ({outlier_count}/{len(topics)})")

    # Strategy 1: c-TF-IDF (best for short text)
    new_topics = topic_model.reduce_outliers(docs, topics, strategy="c-tf-idf")

    outlier_rate = sum(1 for t in new_topics if t == -1) / len(new_topics)
    _log("INFO", f"After c-TF-IDF reduction: {outlier_rate:.1%}")

    # Strategy 2: embeddings if still above 50%
    if outlier_rate > 0.5:
        new_topics = topic_model.reduce_outliers(
            docs, new_topics, strategy="embeddings",
            embeddings=embeddings,
        )
        outlier_rate = sum(1 for t in new_topics if t == -1) / len(new_topics)
        _log("INFO", f"After embeddings reduction: {outlier_rate:.1%}")

    # CRITICAL: update topic representations after outlier reduction
    topic_model.update_topics(docs, topics=new_topics)

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

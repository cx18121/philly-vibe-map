"""Stage 3b: Aggregate per-neighbourhood sentiment from fine-tuned model.

Runs inference with the merged DistilBERT+LoRA sentiment model on all
reviews, then aggregates per-neighbourhood sentiment distributions.

Requires: sentiment_model/ (from sentiment stage)
Produces: neighbourhood_sentiment.json
"""
from __future__ import annotations

import datetime
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"

INFERENCE_BATCH_SIZE = 64
MAX_SEQ_LENGTH = 256
LABEL_NAMES = ["negative", "neutral", "positive"]


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def run_sentiment_agg(db_path: str, artifacts_dir: Path, force: bool = False) -> dict:
    """Run sentiment inference on all reviews and aggregate per neighbourhood.

    Outputs:
        artifacts_dir / neighbourhood_sentiment.json --
            {neighbourhood_id: {positive: float, neutral: float, negative: float,
                                mean_score: float, review_count: int}}
    """
    output_path = artifacts_dir / "neighbourhood_sentiment.json"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'sentiment_agg': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    model_dir = artifacts_dir / "sentiment_model"
    if not model_dir.exists():
        raise FileNotFoundError(
            f"Sentiment model not found at {model_dir}. Run the 'sentiment' stage first."
        )

    _log("INFO", "Stage 'sentiment_agg': starting...")

    # ------------------------------------------------------------------
    # Load model and tokenizer
    # ------------------------------------------------------------------
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
    model.to(device)
    model.eval()
    _log("INFO", f"Loaded sentiment model on {device}")

    # ------------------------------------------------------------------
    # Load reviews with neighbourhood mapping
    # ------------------------------------------------------------------
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """
        SELECT r.rowid, r.text, b.neighbourhood_id
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
        ORDER BY r.rowid
        """
    ).fetchall()
    conn.close()
    _log("INFO", f"Loaded {len(rows)} reviews for sentiment inference")

    # ------------------------------------------------------------------
    # Batch inference
    # ------------------------------------------------------------------
    # Accumulate per-neighbourhood: sum of softmax probabilities + count
    nid_sentiment: dict[str, dict] = defaultdict(
        lambda: {"positive": 0.0, "neutral": 0.0, "negative": 0.0, "count": 0}
    )

    n_total = len(rows)
    for start in range(0, n_total, INFERENCE_BATCH_SIZE):
        batch = rows[start : start + INFERENCE_BATCH_SIZE]
        texts = [r[1] for r in batch]
        nids = [r[2] for r in batch]

        encodings = tokenizer(
            texts,
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            padding=True,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            logits = model(**encodings).logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()

        for i, nid in enumerate(nids):
            acc = nid_sentiment[nid]
            acc["negative"] += float(probs[i, 0])
            acc["neutral"] += float(probs[i, 1])
            acc["positive"] += float(probs[i, 2])
            acc["count"] += 1

        if (start // INFERENCE_BATCH_SIZE) % 200 == 0:
            _log("INFO", f"Inference progress: {start + len(batch)}/{n_total}")

    # ------------------------------------------------------------------
    # Normalize to proportions and compute mean sentiment score
    # ------------------------------------------------------------------
    result: dict[str, dict] = {}
    for nid, acc in nid_sentiment.items():
        count = acc["count"]
        if count == 0:
            continue
        pos = acc["positive"] / count
        neu = acc["neutral"] / count
        neg = acc["negative"] / count
        # Mean score: weighted average on [-1, 1] scale
        # negative=-1, neutral=0, positive=1
        mean_score = pos - neg
        result[nid] = {
            "positive": round(pos, 4),
            "neutral": round(neu, 4),
            "negative": round(neg, 4),
            "mean_score": round(mean_score, 4),
            "review_count": count,
        }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    _log("INFO", f"Stage 'sentiment_agg': complete -- {len(result)} neighbourhoods scored")

    return {
        "skipped": False,
        "n_neighbourhoods": len(result),
        "total_reviews": n_total,
    }

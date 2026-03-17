"""Stage 2: BERTopic topic discovery with HDBSCAN tuning and outlier reduction."""
from __future__ import annotations

import datetime
import sys
from pathlib import Path


_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def run_topic_model(db_path: str, artifacts_dir: Path, force: bool = False) -> dict:
    """Fit BERTopic on pre-computed embeddings, reduce outliers, save model.

    Outputs:
        artifacts_dir / bertopic_model/       — safetensors serialized model
        artifacts_dir / topic_assignments.json — {review_id: topic_id}
    """
    output_path = artifacts_dir / "bertopic_model"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'topic_model': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    _log("INFO", "Stage 'topic_model': starting...")
    raise NotImplementedError("Stage not yet implemented")

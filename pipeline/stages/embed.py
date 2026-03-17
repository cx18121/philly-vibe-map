"""Stage 1: Embed all reviews with sentence-transformer (all-MiniLM-L6-v2)."""
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


def run_embed(db_path: str, artifacts_dir: Path, force: bool = False) -> dict:
    """Generate sentence embeddings for all reviews.

    Outputs:
        artifacts_dir / embeddings.npy  — shape (n_reviews, 384), float32
        artifacts_dir / review_ids.npy  — shape (n_reviews,), int64
    """
    output_path = artifacts_dir / "embeddings.npy"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'embed': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    _log("INFO", "Stage 'embed': starting...")
    raise NotImplementedError("Stage not yet implemented")

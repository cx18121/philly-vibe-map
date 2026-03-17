"""Stage 3: Score 6 vibe archetypes via cosine similarity."""
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


def run_vibe_score(db_path: str, artifacts_dir: Path, force: bool = False) -> dict:
    """Compute vibe archetype scores per neighbourhood.

    Outputs:
        artifacts_dir / vibe_scores.json — {neighbourhood_id: {archetype: score}}
    """
    output_path = artifacts_dir / "vibe_scores.json"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'vibe_score': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    _log("INFO", "Stage 'vibe_score': starting...")
    raise NotImplementedError("Stage not yet implemented")

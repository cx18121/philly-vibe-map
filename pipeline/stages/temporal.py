"""Stage 5: Temporal drift — year-bucketed vibe scoring."""
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


def run_temporal(db_path: str, artifacts_dir: Path, force: bool = False) -> dict:
    """Compute year-bucketed vibe scores for temporal drift analysis.

    Outputs:
        artifacts_dir / temporal_series.json — {neighbourhood_id: {year: {archetype: score}}}
    """
    output_path = artifacts_dir / "temporal_series.json"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'temporal': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    _log("INFO", "Stage 'temporal': starting...")
    raise NotImplementedError("Stage not yet implemented")

"""Stage 4: LoRA fine-tune DistilBERT sentiment classifier, merge adapter."""
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


def run_sentiment(db_path: str, artifacts_dir: Path, force: bool = False) -> dict:
    """Fine-tune DistilBERT with LoRA for 3-class sentiment, merge and save.

    Outputs:
        artifacts_dir / sentiment_model/ — merged DistilBERT weights
    """
    output_path = artifacts_dir / "sentiment_model"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'sentiment': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    _log("INFO", "Stage 'sentiment': starting...")
    raise NotImplementedError("Stage not yet implemented")

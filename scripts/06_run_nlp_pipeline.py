"""
06_run_nlp_pipeline.py
Orchestrate the NLP pipeline: embed, topic model, vibe score, sentiment,
temporal drift, and export stages — in order.

Usage:
    python scripts/06_run_nlp_pipeline.py [--db data/output/reviews.db] \
        [--artifacts-dir data/output/artifacts] [--force] [--force-stage embed]
"""
from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

# Ensure project root is on sys.path so `from pipeline.stages` works
# when invoked as `python scripts/06_run_nlp_pipeline.py`
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from pipeline.stages import (
    run_embed,
    run_export,
    run_sentiment,
    run_temporal,
    run_topic_model,
    run_vibe_score,
)

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


STAGES = [
    ("embed", run_embed),
    ("topic_model", run_topic_model),
    ("vibe_score", run_vibe_score),
    ("sentiment", run_sentiment),
    ("temporal", run_temporal),
    ("export", run_export),
]

VALID_STAGE_NAMES = [name for name, _ in STAGES]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the NLP pipeline for neighbourhood vibe scoring."
    )
    parser.add_argument(
        "--db",
        default="data/output/reviews.db",
        help="Path to the SQLite reviews database (default: data/output/reviews.db)",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="data/output/artifacts",
        help="Directory for pipeline output artifacts (default: data/output/artifacts)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run all stages regardless of existing artifacts",
    )
    parser.add_argument(
        "--force-stage",
        choices=VALID_STAGE_NAMES,
        help="Re-run a single named stage: " + ", ".join(VALID_STAGE_NAMES),
    )
    args = parser.parse_args()

    artifacts_dir = Path(args.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    _log("INFO", f"Pipeline starting — db={args.db}, artifacts={artifacts_dir}")
    _log("INFO", f"Stages: {', '.join(VALID_STAGE_NAMES)}")

    for stage_name, stage_fn in STAGES:
        force = args.force or (args.force_stage == stage_name)
        _log("INFO", f"--- Stage: {stage_name} (force={force}) ---")
        try:
            result = stage_fn(db_path=args.db, artifacts_dir=artifacts_dir, force=force)
            skipped = result.get("skipped", False) if result else False
            status = "skipped (artifact exists)" if skipped else "complete"
            _log("INFO", f"Stage '{stage_name}': {status}")
        except NotImplementedError:
            _log("WARN", f"Stage '{stage_name}': not yet implemented, skipping")
            continue
        except Exception as exc:
            _log("FAIL", f"Stage '{stage_name}' failed: {exc}")
            sys.exit(1)

    _log("INFO", "Pipeline complete.")


if __name__ == "__main__":
    main()

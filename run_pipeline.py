"""Run the full NLP pipeline end-to-end.

Stages (in order):
  1. embed        — sentence-transformer embeddings (all-MiniLM-L6-v2)
  2. topic_model  — BERTopic topic discovery
  3. sentiment    — domain-adapted sentiment classifier
  4. vibe_score   — 6-archetype vibe scoring + recency weighting
  5. temporal     — year-bucketed temporal drift
  6. export       — FAISS index, representative quotes, enriched GeoJSON

Usage:
  python run_pipeline.py                  # run all stages, skip if artifacts exist
  python run_pipeline.py --force          # re-run everything
  python run_pipeline.py --from embed     # re-run from a specific stage
  python run_pipeline.py --only export    # run a single stage
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

DB_PATH = "data/output/reviews.db"
ARTIFACTS_DIR = Path("data/output/artifacts")

STAGES = [
    ("embed",       "pipeline.stages.embed",       "run_embed"),
    ("topic_model", "pipeline.stages.topic_model", "run_topic_model"),
    ("sentiment",   "pipeline.stages.sentiment",   "run_sentiment"),
    ("vibe_score",  "pipeline.stages.vibe_score",  "run_vibe_score"),
    ("temporal",    "pipeline.stages.temporal",    "run_temporal"),
    ("export",      "pipeline.stages.export",      "run_export"),
]


def run_stage(name: str, module: str, fn: str, force: bool) -> bool:
    import importlib
    print(f"\n{'='*60}")
    print(f"  Stage: {name}")
    print(f"{'='*60}")
    t0 = time.time()
    try:
        mod = importlib.import_module(module)
        result = getattr(mod, fn)(DB_PATH, ARTIFACTS_DIR, force=force)
        elapsed = time.time() - t0
        status = result.get("status", "unknown")
        print(f"\n[OK] {name} — {status} ({elapsed:.1f}s)")
        return True
    except Exception as exc:
        elapsed = time.time() - t0
        print(f"\n[FAIL] {name} failed after {elapsed:.1f}s: {exc}", file=sys.stderr)
        import traceback; traceback.print_exc()
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the neighbourhood vibe NLP pipeline")
    parser.add_argument("--force", action="store_true", help="Re-run stages even if artifacts exist")
    parser.add_argument("--from", dest="from_stage", metavar="STAGE", help="Start from this stage")
    parser.add_argument("--only", metavar="STAGE", help="Run only this one stage")
    args = parser.parse_args()

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    stage_names = [s[0] for s in STAGES]

    if args.only:
        if args.only not in stage_names:
            print(f"Unknown stage '{args.only}'. Options: {', '.join(stage_names)}", file=sys.stderr)
            sys.exit(1)
        stages_to_run = [s for s in STAGES if s[0] == args.only]
    elif args.from_stage:
        if args.from_stage not in stage_names:
            print(f"Unknown stage '{args.from_stage}'. Options: {', '.join(stage_names)}", file=sys.stderr)
            sys.exit(1)
        idx = stage_names.index(args.from_stage)
        stages_to_run = STAGES[idx:]
    else:
        stages_to_run = STAGES

    print(f"Running {len(stages_to_run)} stage(s): {', '.join(s[0] for s in stages_to_run)}")
    print(f"DB: {DB_PATH}  |  Artifacts: {ARTIFACTS_DIR}  |  force={args.force}")

    t_total = time.time()
    for name, module, fn in stages_to_run:
        ok = run_stage(name, module, fn, force=args.force)
        if not ok:
            print(f"\nPipeline aborted at stage '{name}'.", file=sys.stderr)
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Pipeline complete — {time.time() - t_total:.1f}s total")
    print(f"  Artifacts in: {ARTIFACTS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

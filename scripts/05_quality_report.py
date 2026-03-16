"""
05_quality_report.py
Generate data quality report (DATA-05) from reviews.db.
Output: data/output/quality_report.md

Usage:
    python scripts/05_quality_report.py [--db data/output/reviews.db] [--out data/output/quality_report.md]
"""
from __future__ import annotations

import argparse
import datetime
import sqlite3
import sys
from pathlib import Path

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"

MIN_TOTAL_REVIEWS = 500
MIN_YEARS_WITH_COVERAGE = 5
YEARS = ["2019", "2020", "2021", "2022", "2023", "2024"]  # 2025 may be incomplete/absent


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def _borough(nta_code: str | None) -> str:
    """Infer borough from NTACode prefix (NYC legacy — for Philadelphia data returns Unknown)."""
    if nta_code and nta_code.startswith("MN"):
        return "Manhattan"
    if nta_code and nta_code.startswith("BK"):
        return "Brooklyn"
    return "Unknown"


def generate_quality_report(
    db_path: str,
    output_path: str,
    skip_counts: dict | None = None,
) -> None:
    """Generate Markdown quality report from reviews.db.

    Args:
        db_path: Path to reviews.db
        output_path: Where to write quality_report.md
        skip_counts: Optional dict with keys: missing_lat_lng, outside_nta,
                     duplicate_business_id, bad_timestamp — used in Section 4.
                     If None, Section 4 shows 0 for all counts.
    """
    conn = sqlite3.connect(db_path)

    # --- Overall counts ---
    total_reviews = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    unique_businesses = conn.execute(
        "SELECT COUNT(DISTINCT business_id) FROM businesses WHERE neighbourhood_id IS NOT NULL"
    ).fetchone()[0]
    total_ntas = conn.execute(
        "SELECT COUNT(DISTINCT neighbourhood_id) FROM businesses WHERE neighbourhood_id IS NOT NULL"
    ).fetchone()[0]
    date_range = conn.execute(
        "SELECT MIN(review_date), MAX(review_date) FROM reviews"
    ).fetchone()
    earliest = date_range[0] or "N/A"
    latest = date_range[1] or "N/A"

    # --- Per-neighbourhood, per-year counts (2019-2025) ---
    rows = conn.execute("""
        SELECT
            b.neighbourhood_name,
            b.neighbourhood_id,
            substr(r.review_date, 1, 4) AS year,
            COUNT(*) AS review_count
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
          AND substr(r.review_date, 1, 4) BETWEEN '2019' AND '2025'
        GROUP BY b.neighbourhood_name, b.neighbourhood_id, year
        ORDER BY b.neighbourhood_name, year
    """).fetchall()
    conn.close()

    # Build per-neighbourhood summary
    # {neighbourhood_name: {nta_code, years: {year: count}}}
    nbhd: dict[str, dict] = {}
    for name, nta_code, year, count in rows:
        if name not in nbhd:
            nbhd[name] = {"nta_code": nta_code, "years": {}}
        nbhd[name]["years"][year] = count

    # Sort by total reviews descending
    def _total(nd: dict) -> int:
        return sum(nd["years"].values())

    sorted_nbhd = sorted(nbhd.items(), key=lambda kv: _total(kv[1]), reverse=True)

    # --- Build Markdown ---
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = []

    # Section 1: Summary Header
    lines += [
        "# Data Quality Report",
        f"Generated: {now} UTC",
        "Source: Yelp Open Dataset",
        "",
    ]

    # Section 2: Overall Counts Table
    lines += [
        "## Overall Counts",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Total reviews imported | {total_reviews:,} |",
        f"| Unique businesses | {unique_businesses:,} |",
        f"| Neighbourhoods covered | {total_ntas} of {total_ntas} |",
        f"| Date range | {earliest} to {latest} |",
        "",
    ]

    # Section 3: Coverage by Neighbourhood
    lines += [
        "## Coverage by Neighbourhood",
        "",
        "> **GATE**: Every neighbourhood must have reviews in at least 5 of 7 years (2019–2025) and at least 500 total reviews. Rows failing this gate are marked **FAIL**.",
        "",
        "| Neighbourhood | Borough | Total Reviews | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Years with Coverage |",
        "|---------------|---------|--------------|------|------|------|------|------|------|---------------------|",
    ]

    fail_count = 0
    for name, nd in sorted_nbhd:
        nta_code = nd["nta_code"]
        borough = _borough(nta_code)
        year_counts = nd["years"]
        total = _total(nd)
        years_with_data = sum(
            1 for y in ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]
            if year_counts.get(y, 0) > 0
        )
        cols = [year_counts.get(y, 0) for y in YEARS]
        passing = total >= MIN_TOTAL_REVIEWS and years_with_data >= MIN_YEARS_WITH_COVERAGE
        coverage_cell = str(years_with_data) if passing else f"**FAIL** ({years_with_data})"
        if not passing:
            fail_count += 1
        lines.append(
            f"| {name} | {borough} | {total:,} | "
            + " | ".join(str(c) for c in cols)
            + f" | {coverage_cell} |"
        )

    lines.append("")
    if fail_count > 0:
        lines.append(
            f"**Coverage gate: {fail_count} neighbourhood{'s' if fail_count != 1 else ''} FAIL. "
            "Do not proceed to Phase 2.**"
        )
    else:
        lines.append("Coverage gate: PASS. All neighbourhoods meet minimum thresholds.")
    lines.append("")

    # Section 4: Skipped Records Summary
    sc = skip_counts or {}
    lines += [
        "## Skipped Records Summary",
        "",
        "| Reason | Count |",
        "|--------|-------|",
        f"| Missing lat/lng | {sc.get('missing_lat_lng', 0):,} |",
        f"| Outside Manhattan/Brooklyn NTA polygons | {sc.get('outside_nta', 0):,} |",
        f"| Duplicate business_id (INSERT OR IGNORE) | {sc.get('duplicate_business_id', 0):,} |",
        f"| Review timestamp unparseable | {sc.get('bad_timestamp', 0):,} |",
        "",
    ]

    # Section 5: Phase 2 Readiness
    lines += ["## Phase 2 Readiness", ""]
    if fail_count == 0 and total_reviews > 0:
        lines.append("READY FOR PHASE 2  \u2713")
    else:
        lines.append("NOT READY \u2014 resolve coverage failures above before proceeding.")
    lines.append("")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    _log("INFO", f"Data quality report written: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/output/reviews.db")
    parser.add_argument("--out", default="data/output/quality_report.md")
    parser.add_argument("--stats", default="data/output/ingest_stats.json")
    args = parser.parse_args()

    # Read skip counts written by 03_assign_neighbourhoods.py and 04_ingest_reviews.py
    import json as _json
    _skip_counts = None
    _stats_path = Path(args.stats)
    if _stats_path.exists():
        with open(_stats_path) as _f:
            _skip_counts = _json.load(_f)

    try:
        generate_quality_report(args.db, args.out, skip_counts=_skip_counts)
    except Exception as exc:
        _log("FAIL", f"Report generation failed: {exc}")
        sys.exit(1)

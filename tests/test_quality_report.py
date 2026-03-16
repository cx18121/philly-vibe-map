"""Integration test for data quality report generation -- DATA-05."""
import importlib
import json
import sqlite3
import sys
import tempfile
from pathlib import Path


def _build_report_data(conn):
    """Generate the quality report dict from an in-memory DB (mirrors 05_quality_report.py logic)."""
    rows = conn.execute("""
        SELECT
            b.neighbourhood_name,
            substr(r.review_date, 1, 4) AS year,
            COUNT(*) AS review_count
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
          AND substr(r.review_date, 1, 4) BETWEEN '2019' AND '2025'
        GROUP BY b.neighbourhood_name, year
        ORDER BY b.neighbourhood_name, year
    """).fetchall()
    report = {}
    for neighbourhood, year, count in rows:
        report.setdefault(neighbourhood, {})[year] = count
    return report


def test_report_has_neighbourhood_and_year_keys(in_memory_db):
    """DATA-05: quality report has at least one neighbourhood key with at least one year key."""
    conn = in_memory_db
    # Seed: business with neighbourhood assignment
    conn.execute(
        "INSERT INTO businesses (business_id, name, neighbourhood_id, neighbourhood_name) "
        "VALUES (?, ?, ?, ?)",
        ("b_q1", "Test Biz", "MN0101", "West Village"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO reviews "
        "(review_id, business_id, text, stars, review_date, source) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("r_q1", "b_q1", "Nice", 5, "2021-05-01", "yelp"),
    )
    conn.commit()
    report = _build_report_data(conn)
    assert len(report) >= 1, "Report must have at least one neighbourhood"
    assert "West Village" in report
    assert "2021" in report["West Village"]
    assert report["West Village"]["2021"] == 1


def test_report_excludes_reviews_outside_date_range(in_memory_db):
    """Reviews before 2019 or after 2025 are excluded from the quality report."""
    conn = in_memory_db
    conn.execute(
        "INSERT INTO businesses (business_id, name, neighbourhood_id, neighbourhood_name) "
        "VALUES (?, ?, ?, ?)",
        ("b_q2", "Old Biz", "MN0102", "SoHo"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO reviews "
        "(review_id, business_id, text, stars, review_date, source) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("r_q2", "b_q2", "Ancient review", 3, "2010-01-01", "yelp"),
    )
    conn.commit()
    report = _build_report_data(conn)
    # SoHo should not appear because the only review is from 2010
    assert "SoHo" not in report


def test_report_excludes_unassigned_businesses(in_memory_db):
    """Businesses with neighbourhood_id IS NULL are excluded from quality report."""
    conn = in_memory_db
    conn.execute(
        "INSERT INTO businesses (business_id, name) VALUES (?, ?)",
        ("b_q3", "No Neighbourhood"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO reviews "
        "(review_id, business_id, text, stars, review_date, source) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("r_q3", "b_q3", "Review", 4, "2022-06-01", "yelp"),
    )
    conn.commit()
    report = _build_report_data(conn)
    assert "No Neighbourhood" not in report


# ---------------------------------------------------------------------------
# Helper: build a minimal SQLite DB with seeded data for generate_quality_report tests
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE businesses (
    business_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    neighbourhood_id TEXT,
    neighbourhood_name TEXT,
    city TEXT,
    state TEXT,
    attributes TEXT
);
CREATE TABLE reviews (
    review_id TEXT PRIMARY KEY,
    business_id TEXT NOT NULL,
    text TEXT NOT NULL,
    stars INTEGER NOT NULL,
    review_date TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'yelp',
    useful INTEGER,
    funny INTEGER,
    cool INTEGER
);
CREATE INDEX idx_reviews_business ON reviews(business_id);
CREATE INDEX idx_reviews_date ON reviews(review_date);
CREATE INDEX idx_businesses_neighbourhood ON businesses(neighbourhood_id);
"""


def _make_db(tmp_path: Path, neighbourhoods: dict) -> Path:
    """
    Create a minimal reviews.db at tmp_path/reviews.db.

    neighbourhoods: {name: {nta_code: str, year_counts: {year: count}}}
      where year_counts is {year_str: n_reviews}
    """
    db_path = tmp_path / "reviews.db"
    conn = sqlite3.connect(str(db_path))
    for stmt in _SCHEMA.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(stmt)
    conn.commit()

    review_seq = 0
    for biz_seq, (name, spec) in enumerate(neighbourhoods.items()):
        bid = f"b_gen_{biz_seq}"
        conn.execute(
            "INSERT INTO businesses (business_id, name, neighbourhood_id, neighbourhood_name) "
            "VALUES (?, ?, ?, ?)",
            (bid, f"Biz {name}", spec["nta_code"], name),
        )
        for year, count in spec["year_counts"].items():
            for i in range(count):
                review_seq += 1
                conn.execute(
                    "INSERT OR IGNORE INTO reviews "
                    "(review_id, business_id, text, stars, review_date, source) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (f"r_gen_{review_seq}", bid, "review text", 4, f"{year}-06-01", "yelp"),
                )
    conn.commit()
    conn.close()
    return db_path


def _import_generate():
    """Import generate_quality_report from scripts/05_quality_report.py."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location(
        "quality_report_05",
        scripts_dir / "05_quality_report.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.generate_quality_report


# ---------------------------------------------------------------------------
# TDD tests: generate_quality_report() function behaviour
# ---------------------------------------------------------------------------

def test_generate_report_produces_markdown_with_both_neighbourhoods(tmp_path):
    """generate_quality_report on a DB with 2 neighbourhoods produces a Markdown file listing both."""
    db_path = _make_db(tmp_path, {
        "Fishtown": {"nta_code": "044", "year_counts": {"2019": 100, "2020": 100, "2021": 100}},
        "Rittenhouse": {"nta_code": "116", "year_counts": {"2019": 80, "2020": 80, "2021": 80}},
    })
    out_path = tmp_path / "report.md"
    gen = _import_generate()
    gen(str(db_path), str(out_path))
    content = out_path.read_text()
    assert "Fishtown" in content
    assert "Rittenhouse" in content


def test_generate_report_marks_fail_for_low_review_count(tmp_path):
    """A neighbourhood with fewer than 500 total reviews is marked FAIL in Years with Coverage."""
    # 6 years of data but only 10 reviews/year = 60 total (below 500 threshold)
    db_path = _make_db(tmp_path, {
        "Low Volume": {
            "nta_code": "099",
            "year_counts": {"2019": 10, "2020": 10, "2021": 10, "2022": 10, "2023": 10, "2024": 10},
        },
    })
    out_path = tmp_path / "report.md"
    gen = _import_generate()
    gen(str(db_path), str(out_path))
    content = out_path.read_text()
    assert "**FAIL**" in content


def test_generate_report_marks_fail_for_insufficient_year_coverage(tmp_path):
    """A neighbourhood with coverage in only 3 of 7 years is marked FAIL."""
    # 500 reviews total but only 3 years covered
    db_path = _make_db(tmp_path, {
        "Sparse Years": {
            "nta_code": "077",
            "year_counts": {"2019": 200, "2021": 200, "2023": 100},
        },
    })
    out_path = tmp_path / "report.md"
    gen = _import_generate()
    gen(str(db_path), str(out_path))
    content = out_path.read_text()
    assert "**FAIL**" in content


def test_generate_report_fail_gate_message_when_any_neighbourhood_fails(tmp_path):
    """If any neighbourhood FAILs, report contains the gate failure message."""
    db_path = _make_db(tmp_path, {
        "Under Threshold": {"nta_code": "010", "year_counts": {"2021": 5}},
    })
    out_path = tmp_path / "report.md"
    gen = _import_generate()
    gen(str(db_path), str(out_path))
    content = out_path.read_text()
    assert "FAIL. Do not proceed to Phase 2." in content


def test_generate_report_pass_gate_message_when_all_pass(tmp_path):
    """If all neighbourhoods pass, report contains the PASS gate message."""
    # 500+ reviews across 5+ years
    db_path = _make_db(tmp_path, {
        "Good Neighbourhood": {
            "nta_code": "055",
            "year_counts": {
                "2019": 100, "2020": 100, "2021": 100, "2022": 100, "2023": 100, "2024": 100,
            },
        },
    })
    out_path = tmp_path / "report.md"
    gen = _import_generate()
    gen(str(db_path), str(out_path))
    content = out_path.read_text()
    assert "Coverage gate: PASS. All neighbourhoods meet minimum thresholds." in content


def test_generate_report_ready_verdict_when_all_pass(tmp_path):
    """Phase 2 readiness section says READY FOR PHASE 2 when all pass."""
    db_path = _make_db(tmp_path, {
        "Good Neighbourhood": {
            "nta_code": "055",
            "year_counts": {
                "2019": 100, "2020": 100, "2021": 100, "2022": 100, "2023": 100, "2024": 100,
            },
        },
    })
    out_path = tmp_path / "report.md"
    gen = _import_generate()
    gen(str(db_path), str(out_path))
    content = out_path.read_text()
    assert "READY FOR PHASE 2" in content


def test_generate_report_not_ready_verdict_when_any_fail(tmp_path):
    """Phase 2 readiness section says NOT READY when any neighbourhood fails."""
    db_path = _make_db(tmp_path, {
        "Tiny": {"nta_code": "001", "year_counts": {"2021": 1}},
    })
    out_path = tmp_path / "report.md"
    gen = _import_generate()
    gen(str(db_path), str(out_path))
    content = out_path.read_text()
    assert "NOT READY" in content


def test_generate_report_section1_header(tmp_path):
    """Section 1 header contains '# Data Quality Report' as first line."""
    db_path = _make_db(tmp_path, {
        "Any": {"nta_code": "001", "year_counts": {"2021": 1}},
    })
    out_path = tmp_path / "report.md"
    gen = _import_generate()
    gen(str(db_path), str(out_path))
    content = out_path.read_text()
    assert content.startswith("# Data Quality Report")

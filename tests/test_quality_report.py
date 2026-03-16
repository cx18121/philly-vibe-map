"""Integration test for data quality report generation -- DATA-05."""
import json


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

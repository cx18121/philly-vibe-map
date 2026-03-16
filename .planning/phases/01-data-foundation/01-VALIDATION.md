---
phase: 1
slug: data-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pytest.ini` — Wave 0 creates |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | DATA-01 | smoke | `pytest tests/test_coverage_probe.py -x` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 0 | DATA-02 | unit | `pytest tests/test_schema.py::test_duplicate_insert_ignored -x` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 0 | DATA-03 | unit | `pytest tests/test_schema.py::test_required_fields -x` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 0 | DATA-04 | unit | `pytest tests/test_boundaries.py::test_nta_borough_filter -x` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 0 | DATA-05 | integration | `pytest tests/test_quality_report.py -x` | ❌ W0 | ⬜ pending |
| 1-01-06 | 01 | 0 | DATA-06 | unit | `pytest tests/test_schema.py::test_attributes_json -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures (in-memory SQLite, sample NTA GeoJSON, sample business NDJSON)
- [ ] `tests/test_coverage_probe.py` — smoke test for coverage probe script (DATA-01)
- [ ] `tests/test_schema.py` — unit tests for schema and INSERT OR IGNORE (DATA-02, DATA-03, DATA-06)
- [ ] `tests/test_boundaries.py` — unit tests for NTA download + BoroCode filter (DATA-04)
- [ ] `tests/test_quality_report.py` — integration test for quality report generation (DATA-05)
- [ ] `pytest.ini` — framework config with `testpaths = tests`
- [ ] Framework install: `pip install pytest geopandas orjson tqdm requests`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Coverage probe decision gate (< 500 businesses) | DATA-01 | Requires user decision on dataset pivot; cannot be automated | Run `python scripts/00_probe_coverage.py`; if `nyc_bbox_businesses < 500`, stop and consult user before proceeding |
| NTA GeoJSON visually displays 30+ correct polygons | DATA-04 | Visual map inspection | Open `data/boundaries/nta_2020_manhattan_brooklyn.geojson` in geojson.io; verify Manhattan + Brooklyn polygons display correctly |
| SQLite final review count ≥ flexible target | DATA-01 | Count depends on probe outcome | `sqlite3 data/output/reviews.db "SELECT COUNT(*) FROM reviews"` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

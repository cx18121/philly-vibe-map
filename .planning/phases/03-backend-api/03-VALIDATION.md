---
phase: 3
slug: backend-api
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` |
| **Quick run command** | `pytest tests/test_api.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_api.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | API-01 | stub | `pytest tests/test_api.py -x -q` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 1 | API-01 | integration | `pytest tests/test_api.py::test_get_neighbourhoods -q` | ❌ W0 | ⬜ pending |
| 3-01-03 | 01 | 1 | API-02 | integration | `pytest tests/test_api.py::test_get_neighbourhood_by_id -q` | ❌ W0 | ⬜ pending |
| 3-01-04 | 01 | 1 | API-03 | integration | `pytest tests/test_api.py::test_get_temporal -q` | ❌ W0 | ⬜ pending |
| 3-01-05 | 01 | 1 | API-04 | integration | `pytest tests/test_api.py::test_get_similar -q` | ❌ W0 | ⬜ pending |
| 3-01-06 | 01 | 1 | API-05 | performance | `pytest tests/test_api.py::test_response_times -q` | ❌ W0 | ⬜ pending |
| 3-01-07 | 01 | 1 | API-06 | integration | `pytest tests/test_api.py::test_startup_time -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_api.py` — stubs for API-01 through API-06
- [ ] `tests/conftest.py` — shared fixtures (TestClient, artifact paths)
- [ ] Verify `httpx` installed for async test client support

*Existing pytest.ini infrastructure covers framework setup.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Server starts within 10s loading artifacts | API-06 | Startup timing is hard to measure in unit tests | Run `time uvicorn api.main:app` and observe first log line |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

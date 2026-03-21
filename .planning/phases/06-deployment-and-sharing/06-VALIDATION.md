---
phase: 6
slug: deployment-and-sharing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) + manual browser checks (deployment) |
| **Config file** | pytest.ini |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 6-01-01 | 01 | 1 | DEPLOY-01 | unit | `pytest tests/ -x -q` | ✅ | ⬜ pending |
| 6-01-02 | 01 | 1 | DEPLOY-01 | manual | Browser: visit public URL | N/A | ⬜ pending |
| 6-02-01 | 02 | 1 | DEPLOY-02 | unit | `pytest tests/ -x -q` | ✅ | ⬜ pending |
| 6-02-02 | 02 | 1 | DEPLOY-02 | manual | Browser: check CORS, data loads | N/A | ⬜ pending |
| 6-03-01 | 03 | 2 | DEPLOY-03 | manual | Browser: URL updates on nav, restore on paste | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Frontend loads at public URL without login | DEPLOY-01 | Requires live deployment environment | Visit Vercel URL in browser, confirm map renders with no auth prompt |
| Backend API reachable, no CORS errors | DEPLOY-02 | Requires live deployment environment | Open browser devtools network tab, confirm API calls return 200 with no CORS errors |
| URL state sync: neighbourhood + year restored | DEPLOY-03 | Requires browser navigation simulation | Select a neighbourhood and year, copy URL, open in new tab, confirm same view restored |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---
phase: 5
slug: temporal-animation-and-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.1.0 + @testing-library/react 16.3.2 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose`
- **After every plan wave:** Run `cd frontend && npx vitest run --reporter=verbose`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 0 | VIZ-01, VIZ-02 | unit | `cd frontend && npx vitest run src/__tests__/TimeSlider.test.tsx -x` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 0 | VIZ-06 | unit | `cd frontend && npx vitest run src/__tests__/DetailPanel.test.tsx -x` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 1 | VIZ-03 | unit | `cd frontend && npx vitest run src/__tests__/colors.test.ts -x` | ✅ extend | ⬜ pending |
| 05-02-02 | 02 | 1 | VIZ-04, VIZ-05 | unit | `cd frontend && npx vitest run src/__tests__/VibeMap.test.tsx -x` | ✅ extend | ⬜ pending |
| 05-02-03 | 02 | 1 | VIZ-01, VIZ-02 | unit | `cd frontend && npx vitest run src/__tests__/TimeSlider.test.tsx -x` | ❌ W0 | ⬜ pending |
| 05-02-04 | 02 | 2 | VIZ-06 | unit | `cd frontend && npx vitest run src/__tests__/DetailPanel.test.tsx -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/__tests__/TimeSlider.test.tsx` — stubs for VIZ-01, VIZ-02
- [ ] `frontend/src/__tests__/DetailPanel.test.tsx` — stubs for VIZ-06 (stagger animation variants)
- [ ] Extend `frontend/src/__tests__/colors.test.ts` — add `interpolateVibeColor()` tests for VIZ-03
- [ ] Extend `frontend/src/__tests__/VibeMap.test.tsx` — add highlight layer and `promoteId` assertions for VIZ-04, VIZ-05

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Smooth colour transition during play animation | VIZ-03 | Visual smoothness cannot be asserted programmatically | Press play; confirm colours fade between years rather than snapping |
| Hover pulse/glow effect visible on map | VIZ-04 | WebGL rendering; jsdom cannot render canvas | Open browser, hover a neighbourhood; confirm visible white overlay intensification |
| Ambient glow intensifies on hover | VIZ-05 | Same as above — visual WebGL output | Hover neighbourhood; confirm glow intensifies vs. ambient resting state |
| Sidebar stagger animation visible | VIZ-06 | Animation timing is visual | Select a neighbourhood; confirm bars/pills/quotes animate in sequentially (~80ms stagger) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---
phase: 4
slug: core-map
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.1.0 + @testing-library/react 16.3.2 |
| **Config file** | `frontend/vitest.config.ts` — Wave 0 installs |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd frontend && npx vitest run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose`
- **After every plan wave:** Run `cd frontend && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-W0-01 | W0 | 0 | MAP-02 | unit | `cd frontend && npx vitest run src/__tests__/colors.test.ts -t "all archetypes have distinct colours"` | ❌ W0 | ⬜ pending |
| 4-W0-02 | W0 | 0 | MAP-05 | unit | `cd frontend && npx vitest run src/__tests__/Legend.test.tsx -t "renders all archetypes"` | ❌ W0 | ⬜ pending |
| 4-W0-03 | W0 | 0 | MAP-06 | unit | `cd frontend && npx vitest run src/__tests__/MapSkeleton.test.tsx -t "renders skeleton"` | ❌ W0 | ⬜ pending |
| 4-W0-04 | W0 | 0 | MAP-07 | unit | `cd frontend && npx vitest run src/__tests__/DetailContainer.test.tsx -t "renders bottom sheet"` | ❌ W0 | ⬜ pending |
| 4-W0-05 | W0 | 0 | MAP-01,MAP-03,MAP-08,MAP-09 | integration | `cd frontend && npx vitest run src/__tests__/VibeMap.test.tsx` | ❌ W0 | ⬜ pending |
| 4-W0-06 | W0 | 0 | MAP-04 | integration | `cd frontend && npx vitest run src/__tests__/Sidebar.test.tsx -t "renders detail on selection"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/vitest.config.ts` — Vitest config with jsdom environment
- [ ] `frontend/src/__tests__/colors.test.ts` — stubs for MAP-02
- [ ] `frontend/src/__tests__/Legend.test.tsx` — stubs for MAP-05
- [ ] `frontend/src/__tests__/MapSkeleton.test.tsx` — stubs for MAP-06
- [ ] `frontend/src/__tests__/DetailContainer.test.tsx` — stubs for MAP-07
- [ ] `frontend/src/__tests__/VibeMap.test.tsx` — stubs for MAP-01, MAP-03, MAP-08, MAP-09
- [ ] `frontend/src/__tests__/Sidebar.test.tsx` — stubs for MAP-04
- [ ] Framework install: `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Colourblind simulation passes | MAP-02 | Visual palette check | Open app, run through Colour Oracle or browser DevTools color blindness emulation; verify all 6 archetypes are distinguishable |
| Tooltip positioning correct | MAP-03 | Visual/spatial | Hover neighbourhoods across edge cases (top-right, bottom-left) and confirm tooltip doesn't clip off screen |
| Sidebar animation feels smooth | MAP-04 | Subjective UX | Click several neighbourhoods; confirm slide-in/out doesn't jank or flash |
| Bottom sheet gesture on real mobile | MAP-07 | Touch events not fully simulatable | Load on physical device or Chrome DevTools touch emulation; drag bottom sheet |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

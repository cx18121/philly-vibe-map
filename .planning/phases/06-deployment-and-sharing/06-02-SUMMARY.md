---
phase: 06-deployment-and-sharing
plan: 02
subsystem: infra
tags: [render, vercel, deployment, live, production]

# Dependency graph
requires:
  - phase: 06-01
    provides: render.yaml, Dockerfile with dynamic PORT, Vercel config, 8 committed serving artifacts
provides:
  - Live backend API at https://vibe-mapper-api.onrender.com
  - Live frontend at https://philly-vibe-map.vercel.app
  - Full end-to-end public product

# Tech tracking
tech-stack:
  added: [Render (Docker web service), Vercel (Vite static hosting)]
  patterns: []

key-files:
  created:
    - render.yaml
  modified: []

key-decisions:
  - "Render free plan with Docker runtime; render.yaml at repo root for auto-detection"
  - "Vercel Root Directory set to frontend; VITE_API_URL env var wires frontend to Render backend"

requirements-completed: [DEPLOY-01, DEPLOY-02]

# Metrics
duration: ~5min (human deploy steps)
completed: 2026-03-24
---

# Phase 06 Plan 02: Deploy to Render + Vercel

**Backend live at Render, frontend live at Vercel — full stack publicly accessible**

## Live URLs

- **Frontend:** https://philly-vibe-map.vercel.app
- **Backend API:** https://vibe-mapper-api.onrender.com

## Accomplishments

- render.yaml committed at repo root; Render auto-detected Dockerfile and deployed as a web service
- Vercel imported the repo with Root Directory `frontend` and Framework Preset Vite
- `VITE_API_URL` env var set to the Render URL — frontend correctly routes all API calls to backend
- `/health` endpoint confirmed returning `{"status":"ok","artifacts_loaded":true}`
- Map loads with coloured neighbourhood polygons
- Clicking a neighbourhood opens the detail panel with vibe data fetched from Render
- Time slider changes colours by year
- URL deep links (`?nid=XXX&year=YYYY`) restore view in new tab
- No CORS errors in browser DevTools

## Task Commits

1. **Task 1: Add render.yaml** — `45a16d1` feat(06-02): add render.yaml for backend deploy
2. **Task 2: Human deploy verified** — Render + Vercel dashboards configured; live URLs confirmed

## Verification

- [x] `https://vibe-mapper-api.onrender.com/health` → `{"status":"ok","artifacts_loaded":true}`
- [x] `https://philly-vibe-map.vercel.app` → full interactive map loads
- [x] Neighbourhood click → vibe data from Render backend (no CORS errors)
- [x] URL deep link restores selected neighbourhood and year in new tab

## Self-Check: PASSED

All acceptance criteria met. Project is live and publicly accessible.

---
*Phase: 06-deployment-and-sharing*
*Completed: 2026-03-24*

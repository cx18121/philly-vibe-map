# Phase 6: Deployment and Sharing - Research

**Researched:** 2026-03-21
**Domain:** Cloud deployment (PaaS), SPA hosting, URL state management
**Confidence:** HIGH

## Summary

Phase 6 deploys the completed Neighbourhood Vibe Mapper to public URLs. The backend is a FastAPI app serving pre-computed JSON artifacts (~4MB total) with a FAISS index -- it already has a working Dockerfile. The frontend is a Vite React SPA with no server-side rendering requirements. The third requirement is URL-based deep linking so users can share a selected neighbourhood and year.

The deployment surface is small and well-understood. The backend needs a Docker-capable PaaS (Render recommended for its permanent free tier). The frontend deploys as static files to Vercel (zero-config for Vite). Deep linking requires syncing two Zustand store fields (`selectedId`, `currentYear`) with URL search params -- Zustand's official docs provide a pattern for this.

**Primary recommendation:** Deploy backend to Render free tier (Docker web service), frontend to Vercel (Vite auto-detected), and implement URL state sync using `URLSearchParams` with `window.history.replaceState` driven from a Zustand `subscribe` listener.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEPLOY-01 | Backend deployed to a public URL (Railway or Render) with artifacts loaded from committed JSON files | Render free tier supports Docker; existing Dockerfile works; only ~4MB of serving artifacts needed (not 1.7GB full artifacts dir); FAISS dependency handled via requirements-api.txt |
| DEPLOY-02 | Frontend deployed to Vercel with a public URL requiring no login | Vercel auto-detects Vite; needs `vercel.json` SPA rewrite for deep links; `VITE_API_URL` env var points frontend at deployed backend |
| DEPLOY-03 | URL encodes selected neighbourhood and current year so any state can be shared via link | Zustand subscribe + `URLSearchParams` + `history.replaceState` pattern; on mount, read params and hydrate store |
</phase_requirements>

## Standard Stack

### Core
| Library/Service | Version/Tier | Purpose | Why Standard |
|-----------------|-------------|---------|--------------|
| Render | Free tier | Backend hosting (Docker web service) | Permanent free tier with 750h/month; Docker support; auto-deploy from GitHub; no credit card required to start |
| Vercel | Hobby (free) | Frontend static hosting | Zero-config Vite detection; global CDN; automatic HTTPS; free for personal projects |
| Zustand | 5.0.12 (already installed) | URL state sync | Already the app's state manager; official docs show URL hash/param sync pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None new | - | - | No new dependencies needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Render | Railway | Railway free trial is $5/30 days then $1/mo; Render gives 750h/month permanently free. Railway has no cold-start spin-down but costs money after trial |
| Render | Fly.io | Fly.io free tier is more complex to configure; requires flyctl CLI; Docker support is good but Render is simpler for a single service |
| Vercel | Netlify | Both work; Vercel has better Vite auto-detection and is the project standard per DEPLOY-02 |
| URLSearchParams | react-router | Would require adding a routing library for just 2 params; overkill for this use case |

**Installation:**
```bash
# No new packages needed -- all tools are platform-side or already installed
```

## Architecture Patterns

### Deployment Topology
```
                    [GitHub repo]
                    /            \
        [Render]                 [Vercel]
        Docker web service       Static site (CDN)
        backend:8000             frontend (dist/)
        /neighbourhoods          VITE_API_URL -> Render URL
        /temporal                vercel.json SPA rewrite
        /similar
        /health
```

### Pattern 1: Backend Artifact Slimming
**What:** The full `data/output/artifacts/` directory is 1.7GB (embeddings, ML models, etc.) but the backend only loads 8 JSON/GeoJSON files + 1 FAISS binary totalling ~4MB. Deploy only the serving artifacts.
**When to use:** Always -- the Dockerfile must COPY only the files the loader reads.
**Required files (from `loader.py` analysis):**
```
enriched_geojson.geojson   1.9 MB
representative_quotes.json 1.2 MB
temporal_series.json       584 KB
neighbourhood_topics.json  300 KB
vibe_scores.json           36 KB
review_counts.json         4 KB
faiss_index.bin            4 KB
faiss_id_map.json          4 KB
                    TOTAL: ~4 MB
```

### Pattern 2: Render Docker Deploy
**What:** Render auto-detects Dockerfile at repo root. Set environment variables via Render dashboard. The existing Dockerfile already works -- it copies `backend/` and `data/output/artifacts/`, installs from `requirements-api.txt`, and runs uvicorn.
**Configuration needed:**
- Create a `render.yaml` (optional) or configure via dashboard
- Set PORT env var (Render expects the app to bind to its assigned `PORT`)
- The existing Dockerfile uses `ENV PORT=8000` but Render overrides with its own PORT

**Critical detail:** Render sets a `PORT` environment variable. The backend `config.py` already reads `os.environ.get("PORT", "8080")` -- this works. The Dockerfile CMD hardcodes `--port 8000` which must be changed to use `$PORT` or the config value.

### Pattern 3: Vercel SPA Fallback
**What:** Vercel needs a rewrite rule so that deep-linked URLs (e.g., `/?nid=42&year=2022`) don't 404. Without it, Vercel tries to find a literal file for the path.
**Config:**
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```
Place `vercel.json` in the `frontend/` directory (or repo root with `"buildCommand"` and `"outputDirectory"` overrides).

### Pattern 4: URL State Sync with Zustand
**What:** Bi-directional sync between URL search params and Zustand store. Two params: `nid` (neighbourhood ID) and `year` (current year).
**Flow:**
1. On app mount: read `URLSearchParams`, if `nid`/`year` present, hydrate store
2. On store change: `useMapStore.subscribe` updates URL via `history.replaceState` (no page reload)
3. URL format: `https://app.example.com/?nid=42&year=2022`

**Example:**
```typescript
// Source: Zustand official docs - connect to state with URL
// https://zustand.docs.pmnd.rs/guides/connect-to-state-with-url-hash

// Write store -> URL (subscribe outside React)
useMapStore.subscribe((state) => {
  const params = new URLSearchParams();
  if (state.selectedId) params.set('nid', state.selectedId);
  if (state.currentYear) params.set('year', String(state.currentYear));
  const search = params.toString();
  const url = search ? `?${search}` : window.location.pathname;
  window.history.replaceState(null, '', url);
});

// Read URL -> store (on app init)
function hydrateFromURL() {
  const params = new URLSearchParams(window.location.search);
  const nid = params.get('nid');
  const year = params.get('year');
  if (nid) useMapStore.getState().setSelected(nid);
  if (year) useMapStore.getState().setYear(Number(year));
}
```

### Anti-Patterns to Avoid
- **Deploying the full 1.7GB artifacts directory:** Only ~4MB is needed for serving. The embeddings, ML models, and topic assignments are pipeline-only artifacts.
- **Hardcoding backend URL in frontend source:** Use `VITE_API_URL` environment variable (already implemented in `api.ts`).
- **Using `history.pushState` for state sync:** Creates excessive browser history entries. Use `replaceState` instead.
- **Committing large artifacts to git:** The serving artifacts (~4MB) can be committed to git for simple deploys. The ML artifacts (1.7GB) must NOT be committed.
- **Forgetting CORS:** Already handled -- `app.py` has `allow_origins=["*"]`. This is fine for a portfolio project.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Static file CDN | Custom nginx/S3 setup | Vercel | Zero-config, free, global CDN, automatic HTTPS |
| Docker hosting | VPS + Docker Compose | Render | Managed platform, auto-deploy from Git, health checks built in |
| URL parsing | Custom string splitting | `URLSearchParams` API | Built-in browser API, handles encoding edge cases |
| SSL certificates | Let's Encrypt setup | Platform-managed (both Render and Vercel) | Automatic HTTPS on custom domains and *.onrender.com / *.vercel.app |

**Key insight:** For a portfolio project with static pre-computed data, PaaS platforms eliminate all ops overhead. There are exactly zero reasons to manage infrastructure manually.

## Common Pitfalls

### Pitfall 1: Render PORT Mismatch
**What goes wrong:** App starts on hardcoded port 8000 but Render expects it to listen on the PORT environment variable it injects.
**Why it happens:** Dockerfile CMD hardcodes `--port 8000`.
**How to avoid:** Change CMD to read from env: `CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]` or rely on the `config.py` Settings class.
**Warning signs:** Render health check fails; deploy shows "port scan timeout".

### Pitfall 2: Render Free Tier Cold Start
**What goes wrong:** First visit after 15 minutes of inactivity takes ~30-60 seconds while Render spins up the container.
**Why it happens:** Render free tier spins down after 15 min inactivity.
**How to avoid:** Accept it for a portfolio project. The frontend loads instantly from Vercel CDN; show a loading state while the backend wakes up. Optionally add a note in the UI.
**Warning signs:** Users see "API error" on first load if there is no retry/loading handling.

### Pitfall 3: VITE_API_URL Not Set at Build Time
**What goes wrong:** Frontend calls `/api/neighbourhoods` (dev proxy path) in production, gets 404.
**Why it happens:** `VITE_API_URL` env var must be set at BUILD time (Vite inlines it during build). Setting it at runtime has no effect.
**How to avoid:** In Vercel dashboard, set `VITE_API_URL=https://your-app.onrender.com` as an environment variable. Vite replaces `import.meta.env.VITE_API_URL` at build time.
**Warning signs:** Network tab shows requests going to `/api/neighbourhoods` instead of `https://your-app.onrender.com/neighbourhoods`.

### Pitfall 4: SPA Deep Link 404s on Vercel
**What goes wrong:** Sharing a URL like `/?nid=42&year=2022` returns 404 if Vercel does not have the SPA rewrite.
**Why it happens:** Vercel looks for a literal file matching the path.
**How to avoid:** Add `vercel.json` with `{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }`.
**Warning signs:** Direct URL access works on `localhost` but 404s on Vercel.

### Pitfall 5: Artifacts Not in Git
**What goes wrong:** Render clones the repo but `data/output/artifacts/` is gitignored, so the backend has no data.
**Why it happens:** The `.gitignore` does not explicitly exclude the artifacts directory, but it is also not tracked in git currently.
**How to avoid:** Either (a) commit the 8 serving-only artifact files to git (only ~4MB), or (b) create a separate `backend/artifacts/` directory with just the serving files and commit those. Option (a) is simplest.
**Warning signs:** Backend starts but returns empty responses or 500 errors.

### Pitfall 6: URL Hydration Race Condition
**What goes wrong:** URL params are read before temporal data is loaded, so `setYear` and `setSelected` fire before the store has valid data.
**Why it happens:** Hydration runs on mount but API data arrives asynchronously.
**How to avoid:** Defer URL hydration until after the GeoJSON and temporal data hooks resolve. Use an effect that depends on data-ready state.
**Warning signs:** Selected neighbourhood does not highlight on shared URL; year resets to default.

## Code Examples

### Dockerfile Fix for Dynamic PORT
```dockerfile
# Source: Render docs - Docker deploy
# Current CMD (hardcoded):
# CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]

# Fixed CMD (reads PORT env var):
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### vercel.json for Frontend
```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

### URL State Sync Module
```typescript
// frontend/src/lib/urlSync.ts
import { useMapStore } from '../store/mapStore';

/** Write selected state to URL (call once at app init) */
export function initUrlSync(): void {
  useMapStore.subscribe((state, prev) => {
    if (state.selectedId === prev.selectedId && state.currentYear === prev.currentYear) return;
    const params = new URLSearchParams();
    if (state.selectedId) params.set('nid', state.selectedId);
    if (state.currentYear) params.set('year', String(state.currentYear));
    const qs = params.toString();
    window.history.replaceState(null, '', qs ? `?${qs}` : window.location.pathname);
  });
}

/** Read URL params and hydrate store (call after data is loaded) */
export function hydrateFromUrl(): void {
  const params = new URLSearchParams(window.location.search);
  const nid = params.get('nid');
  const year = params.get('year');
  if (year) useMapStore.getState().setYear(Number(year));
  if (nid) useMapStore.getState().setSelected(nid);
}
```

### Render Service Configuration (render.yaml)
```yaml
# render.yaml (optional - can also configure via dashboard)
services:
  - type: web
    name: vibe-mapper-api
    runtime: docker
    plan: free
    healthCheckPath: /health
    envVars:
      - key: ARTIFACTS_DIR
        value: data/output/artifacts
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Heroku free tier | Render/Railway free tiers | Heroku removed free tier Nov 2022 | Render is now the standard free Docker PaaS |
| CRA + Netlify | Vite + Vercel | 2023-2024 | Vite is the standard React build tool; Vercel auto-detects it |
| react-router for URL state | URLSearchParams + history API | Always available | No routing library needed for simple param sync in SPAs |

**Deprecated/outdated:**
- Heroku free tier: Removed November 2022. Do not reference.
- `create-react-app`: Deprecated. This project already uses Vite.

## Open Questions

1. **Custom domain?**
   - What we know: Both Render and Vercel support custom domains on free tiers
   - What's unclear: Whether the user wants a custom domain or is fine with `*.onrender.com` / `*.vercel.app`
   - Recommendation: Deploy with platform subdomains first; custom domain is a stretch goal

2. **Serving artifact commit strategy**
   - What we know: The 8 serving files are ~4MB total; currently not in git
   - What's unclear: Whether to commit them to the main repo or use a separate mechanism
   - Recommendation: Commit the 8 serving-only files to git. 4MB is well within GitHub limits and makes deployment trivially simple with no external storage needed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (backend) | pytest (via pytest.ini) |
| Framework (frontend) | vitest 4.1.0 (via vitest.config.ts) |
| Config file (backend) | `pytest.ini` |
| Config file (frontend) | `frontend/vitest.config.ts` |
| Quick run command (backend) | `python -m pytest tests/test_api.py -x -q` |
| Quick run command (frontend) | `cd frontend && npx vitest run --reporter=verbose` |
| Full suite command | `python -m pytest -x -q && cd frontend && npx vitest run` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEPLOY-01 | Backend serves /health on deployed URL | smoke | `curl -f https://<render-url>/health` | N/A (manual/CI) |
| DEPLOY-02 | Frontend loads at public URL without auth | smoke | `curl -f https://<vercel-url>/` | N/A (manual/CI) |
| DEPLOY-03 | URL params restore state | unit | `cd frontend && npx vitest run src/__tests__/urlSync.test.ts` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_api.py -x -q && cd frontend && npx vitest run`
- **Per wave merge:** Full suite
- **Phase gate:** Manual smoke test of deployed URLs + full local suite green

### Wave 0 Gaps
- [ ] `frontend/src/__tests__/urlSync.test.ts` -- covers DEPLOY-03 URL param hydration and serialization
- [ ] Smoke test checklist for DEPLOY-01 and DEPLOY-02 (manual verification against live URLs)

## Sources

### Primary (HIGH confidence)
- Project codebase analysis: `backend/loader.py`, `backend/config.py`, `backend/app.py`, `Dockerfile`, `frontend/src/lib/api.ts`, `frontend/src/store/mapStore.ts`
- [Zustand URL state docs](https://zustand.docs.pmnd.rs/guides/connect-to-state-with-url-hash) -- official URL sync pattern

### Secondary (MEDIUM confidence)
- [Render Docker deploy docs](https://render.com/docs/deploy-fastapi) -- FastAPI deployment guide
- [Render free tier docs](https://render.com/docs/free) -- 750h/month, 15-min spin-down
- [Railway pricing docs](https://docs.railway.com/pricing/plans) -- $5 trial, then $1/mo free tier
- [Vercel Vite docs](https://vercel.com/docs/frameworks/frontend/vite) -- auto-detection, build config
- [Vercel rewrites docs](https://vercel.com/docs/rewrites) -- SPA fallback pattern

### Tertiary (LOW confidence)
- None -- all findings verified with official sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Render and Vercel are well-documented, stable platforms with clear free tiers
- Architecture: HIGH -- deployment topology is straightforward; existing Dockerfile and Vite config cover 90% of the work
- Pitfalls: HIGH -- PORT mismatch, cold start, build-time env vars are well-documented issues
- URL sync: HIGH -- Zustand official docs provide the exact pattern; browser APIs are stable

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (stable platforms, unlikely to change)

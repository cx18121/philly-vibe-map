---
phase: 2
slug: nlp-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 9.0 |
| **Config file** | `pytest.ini` (exists: `testpaths = tests`, `addopts = -x -q`) |
| **Quick run command** | `pytest tests/test_nlp_pipeline.py -x` |
| **Full suite command** | `pytest -x -q` |
| **Estimated runtime** | ~30 seconds (unit suite); slow tests marked `@pytest.mark.slow` |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_nlp_pipeline.py -x`
- **After every plan wave:** Run `pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green + manual inspection of vibe scores and topic labels
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-W0-01 | Wave 0 | 0 | NLP-01 | unit | `pytest tests/test_embed.py -x` | ❌ W0 | ⬜ pending |
| 02-W0-02 | Wave 0 | 0 | NLP-02 | integration | `pytest tests/test_topic_model.py -x` | ❌ W0 | ⬜ pending |
| 02-W0-03 | Wave 0 | 0 | NLP-03, NLP-05 | unit | `pytest tests/test_vibe_score.py -x` | ❌ W0 | ⬜ pending |
| 02-W0-04 | Wave 0 | 0 | NLP-04 | unit | `pytest tests/test_sentiment.py -x` | ❌ W0 | ⬜ pending |
| 02-W0-05 | Wave 0 | 0 | NLP-06 | unit | `pytest tests/test_temporal.py -x` | ❌ W0 | ⬜ pending |
| 02-W0-06 | Wave 0 | 0 | NLP-07 | unit | `pytest tests/test_faiss_index.py -x` | ❌ W0 | ⬜ pending |
| 02-W0-07 | Wave 0 | 0 | NLP-08 | unit | `pytest tests/test_quotes.py -x` | ❌ W0 | ⬜ pending |
| 02-W0-08 | Wave 0 | 0 | NLP-09 | integration | `pytest tests/test_artifacts.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_embed.py` — stubs for NLP-01 (embeddings shape (N, 384), dtype float32, alignment with review_ids)
- [ ] `tests/test_topic_model.py` — stubs for NLP-02 (topic count ≥20, outlier rate <50% after reduction)
- [ ] `tests/test_vibe_score.py` — stubs for NLP-03, NLP-05 (archetype scoring, recency weighting in log-space, min clamp 1e-6)
- [ ] `tests/test_sentiment.py` — stubs for NLP-04 (LoRA config valid, merge_and_unload produces loadable model with 3-class output)
- [ ] `tests/test_temporal.py` — stubs for NLP-06 (year bucketing, no NaN, all neighbourhoods covered)
- [ ] `tests/test_faiss_index.py` — stubs for NLP-07 (index build, query latency <10ms, result plausibility check)
- [ ] `tests/test_quotes.py` — stubs for NLP-08 (3-5 quotes per neighbourhood per archetype, ≤300 chars)
- [ ] `tests/test_artifacts.py` — stubs for NLP-09 (all required files exist and load without error)
- [ ] `tests/conftest.py` updates — shared fixtures: mock embeddings array, mock SQLite DB with review text, mock BERTopic model

*Testing strategy: most tests use small synthetic data (100 fake reviews, 3 neighbourhoods) to keep execution under 30 seconds. Slow ML tests marked `@pytest.mark.slow`, excluded from quick run.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| BERTopic topic labels are human-interpretable | NLP-02 | Semantic quality cannot be auto-checked | Print top 10 topics with representative words; confirm labels make sense (e.g., "food/dining", "nightlife", "family activities") |
| Vibe scores vary meaningfully across neighbourhoods | NLP-03 | "Meaningful" variation is subjective | Print vibe matrix for 5 diverse neighbourhoods; confirm SoHo scores differ from East Harlem on nightlife/cultural dimensions |
| FAISS similarity results are plausible | NLP-07 | Plausibility requires domain knowledge | Query SoHo; confirm results include West Village, NoHo, not East Harlem or Bronx neighbourhoods |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

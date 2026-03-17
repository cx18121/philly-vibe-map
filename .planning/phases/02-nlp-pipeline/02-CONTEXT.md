# Phase 2: NLP Pipeline - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Run the full ML computation pipeline on the Philadelphia review corpus produced by Phase 1: embed all reviews with a sentence-transformer, discover topics via BERTopic, score each neighbourhood against 6 vibe archetypes, fine-tune a sentiment classifier, compute temporal drift per year, build a FAISS nearest-neighbour index, select representative review quotes, and export all results as serialized artifact files. This phase produces the static ML artifacts consumed by the Phase 3 backend — no live ML inference ever runs after this phase completes.

**Important:** Phase 1 pivoted from NYC to Philadelphia (Yelp NYC coverage was <500 businesses; Philadelphia has ~14,568). All neighbourhood references in this phase are Philadelphia neighbourhoods from `data/scripts/boundaries/` and the `businesses`/`reviews` tables in `data/output/reviews.db`.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
The user delegated all implementation decisions to Claude. Choices below represent the best technical approach given the project constraints (local GPU, portfolio/resume priority, static artifacts, Python stack).

### Topic modeling scope
- **Global BERTopic model** — train one BERTopic model over all Philadelphia reviews combined, not per-neighbourhood. Per-neighbourhood runs would have 500–2,000 reviews max per neighbourhood; too few for stable HDBSCAN clustering. A global model produces coherent topics that generalize across the dataset; neighbourhood vibe scores are then computed by aggregating topic assignments per-neighbourhood post-hoc.
- HDBSCAN params per NLP-02: `min_cluster_size=10`, `min_samples=3`, with `reduce_outliers()` after fitting.
- Target ≥20 distinct topics after outlier reduction with <50% outlier rate.

### Embedding execution
- Model: `all-MiniLM-L6-v2` (NLP-01 baseline) — 384-dimensional, fast, well-suited for short review text.
- Batch size: 256 reviews per forward pass (tunable via env var `EMBED_BATCH_SIZE`). Balances GPU memory and throughput.
- Checkpointing: if `data/output/artifacts/embeddings.npy` already exists, skip re-embedding. Each subsequent step similarly checks for its output artifact before running — `exists check` idempotency, same philosophy as Phase 1's `INSERT OR IGNORE`.
- Embeddings saved as numpy `.npy` format — simplest possible, fast `np.load()`, no dependencies.

### Sentiment fine-tuning setup
- Fine-tune on the full Yelp Open Dataset (all 6.9M reviews), not just the Philadelphia subset — more training data = better generalisation on review text.
- Architecture: DistilBERT + LoRA (NLP-04) with rank=16, alpha=32, dropout=0.1.
- Labels: star ratings remapped to 3-class sentiment (1–2 stars → negative, 3 stars → neutral, 4–5 stars → positive). Binary (positive/negative) loses nuance; 5-class is noisy on 3-star reviews.
- Class balance: weighted random sampling during training (negative reviews are underrepresented in Yelp).
- Training: 3 epochs, batch size 32, AdamW lr=2e-4 with linear warmup. Merge LoRA adapter weights before export (NLP-04 spec).
- Checkpoint: if `data/output/artifacts/sentiment_model/` exists, skip fine-tuning.

### Vibe archetype scoring
- Archetype seed phrases embedded with the same `all-MiniLM-L6-v2` model (not a separate embedding — consistency matters for cosine similarity).
- Seed phrases for each archetype are hardcoded in a config file (`pipeline/archetypes.json`) so they're easy to inspect and tune without touching code.
- Vibe score = mean cosine similarity between all topic cluster centroids for a neighbourhood and the archetype seed phrase embedding, weighted by how many reviews in the neighbourhood belong to each topic.
- Recency weighting (NLP-05): apply exponential decay with configurable half-life (default 365 days). Computation in log-space with minimum weight clamp of 1e-6 (per requirement).

### Temporal drift
- Bucket reviews by year 2019–2025 (NLP-06). Run full vibe scoring pipeline per year bucket with equal weights (no decay within a bucket — the bucket IS the time slice).
- Produce a `temporal_series.json`: `{neighbourhood_id: {year: {vibe_dimension: score, ...}, ...}}` — flat JSON, easy for backend to load in one shot.

### FAISS index
- Flat index (NLP-07) over 6-dimensional neighbourhood vibe vectors. 30-ish neighbourhoods means brute-force is instantaneous; a flat index is correct, avoids approximate search approximation errors.
- Saved as `faiss_index.bin` (binary) + `faiss_id_map.json` (maps FAISS integer IDs → neighbourhood IDs).

### Representative quotes
- 3–5 quotes per neighbourhood per vibe archetype (NLP-08), selected as the reviews with highest cosine similarity to the archetype centroid embedding.
- Quotes truncated to 300 characters max for frontend display.
- Saved in `representative_quotes.json`: `{neighbourhood_id: {archetype: [quote, ...]}}`.

### Artifact output format
- All artifacts land in `data/output/artifacts/`:
  - `embeddings.npy` — numpy array, shape `(n_reviews, 384)`
  - `review_ids.npy` — numpy int array of review DB row IDs aligned to embeddings
  - `bertopic_model/` — BERTopic serialised model directory
  - `topic_assignments.json` — `{review_id: topic_id}` mapping
  - `vibe_scores.json` — `{neighbourhood_id: {archetype: score, ...}}`
  - `temporal_series.json` — `{neighbourhood_id: {year: {archetype: score}}}`
  - `faiss_index.bin` — FAISS flat index binary
  - `faiss_id_map.json` — FAISS integer ID → neighbourhood ID
  - `representative_quotes.json` — `{neighbourhood_id: {archetype: [quote, ...]}}`
  - `sentiment_model/` — merged DistilBERT+LoRA weights directory
  - `enriched_geojson.geojson` — NTA GeoJSON with vibe scores injected into feature properties
- JSON files use `indent=2` for human-readability and git diff-ability.
- No pickle, no HDF5, no parquet — JSON + numpy + binary FAISS is the entire dependency surface for the backend.

### Pipeline resumability
- Each of the 6 pipeline stages (embed, topic-model, score-vibes, fine-tune-sentiment, temporal-drift, build-faiss) checks for its output artifact at startup and skips if found.
- `--force` flag re-runs all stages regardless of existing artifacts.
- `--force-stage <name>` re-runs a single named stage.
- Script entry point: `scripts/06_run_nlp_pipeline.py` orchestrates all stages in order with consistent logging (same `_log()` pattern as Phase 1 scripts).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 outputs (pipeline inputs)
- `scripts/02_build_schema.py` — SQLite schema definition for `businesses` and `reviews` tables; Phase 2 reads from these tables
- `scripts/04_ingest_reviews.py` — Shows the review record structure: `review_id`, `business_id`, `text`, `stars`, `date`, `useful`, `funny`, `cool`
- `data/output/reviews.db` — The actual SQLite database (may be empty at planning time; schema is authoritative)

### Phase 1 boundaries output
- `scripts/03_assign_neighbourhoods.py` — Produces `businesses.neighbourhood_id` and `businesses.neighbourhood_name`; Phase 2 groups reviews by `neighbourhood_id` via JOIN on `businesses`

### Project requirements
- `.planning/REQUIREMENTS.md` — NLP-01 through NLP-09 define all acceptance criteria for this phase
- `.planning/PROJECT.md` — Resume/portfolio priority (BERTopic, FAISS, LoRA choices must be technically defensible), static artifacts constraint, local GPU compute

### Phase 1 context (prior decisions)
- `.planning/phases/01-data-foundation/01-CONTEXT.md` — Philadelphia pivot decision, streaming patterns, SQLite idempotency patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_log(level, msg)` pattern (in all Phase 1 scripts): consistent timestamped logging to stdout — replicate in Phase 2 scripts
- `argparse` CLI pattern with `--db` flag: all Phase 1 scripts expose a `--db` argument for the SQLite path; Phase 2 pipeline script should follow the same pattern for `--db` and `--artifacts-dir`
- `BATCH_SIZE` / `PROGRESS_INTERVAL` constants pattern (04_ingest_reviews.py): use same pattern for `EMBED_BATCH_SIZE` in pipeline

### Established Patterns
- **Idempotent writes**: Phase 1 used `INSERT OR IGNORE`; Phase 2 equivalent is "check artifact exists before running stage"
- **Streaming over loading**: Phase 1 streamed 8.65 GB NDJSON line-by-line; Phase 2 should stream reviews from SQLite in chunks (not `SELECT *` into memory for 100k+ rows)
- **Progress logging**: Phase 1 logs every N records; Phase 2 should log progress per embedding batch

### Integration Points
- Phase 2 reads from `data/output/reviews.db` (businesses + reviews tables)
- Phase 2 reads from `scripts/data/boundaries/` (GeoJSON for enriched GeoJSON output)
- Phase 2 writes all outputs to `data/output/artifacts/` (new directory, created by pipeline)
- Phase 3 (backend) loads everything from `data/output/artifacts/` at startup

</code_context>

<specifics>
## Specific Ideas

- The NLP pipeline is the centrepiece resume artefact — BERTopic over LDA, sentence-transformers over bag-of-words, LoRA fine-tuning over generic VADER, FAISS over brute-force: each choice should be documented with its rationale in a `pipeline/PIPELINE_DECISIONS.md` file so it can be pointed to in interviews
- Pipeline should be runnable end-to-end with a single command: `python scripts/06_run_nlp_pipeline.py`
- Intermediate artifact existence checks mean a partial run can be resumed by simply re-running the same command

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-nlp-pipeline*
*Context gathered: 2026-03-17*

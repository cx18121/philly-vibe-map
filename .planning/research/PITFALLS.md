# Pitfalls Research

**Domain:** NLP-powered neighbourhood vibe visualization (NYC reviews)
**Researched:** 2026-03-16
**Confidence:** HIGH (verified against official docs and library documentation)

## Critical Pitfalls

### Pitfall 1: Google Places API Returns Only 5 Reviews Per Place

**What goes wrong:**
The Google Places API (New) hard-caps responses at 5 reviews per place. With 30 neighbourhoods and roughly 200-400 businesses per neighbourhood, you get at most 5 reviews x ~9,000 businesses = 45,000 reviews. But the 5 returned are Google's "most relevant" (not most recent), so you have zero control over temporal coverage. You cannot get reviews from 2019-2020 if Google decides a 2024 review is more relevant. This fundamentally undermines the temporal drift analysis that is core to the project.

**Why it happens:**
Developers assume "Google Places API" means "access to all Google reviews." The 5-review limit has been a longstanding issue (Google Issue Tracker #35825957, open since 2015, still unresolved). The API is designed for consumer-facing apps showing a handful of reviews, not for data collection.

**How to avoid:**
- Accept the 5-review limit for supplementary data but do NOT treat Google Places API as the primary review source for temporal analysis.
- Use Yelp Fusion API as the primary source -- it returns up to 3 reviews per business via the API, but the Yelp Open Dataset (academic) contains millions of reviews with full timestamps. Check if NYC businesses are covered.
- For Google reviews at scale, consider third-party scraping APIs (Outscraper, SerpAPI) that bypass the 5-review limit. Budget ~$50-100 for a one-time scrape of ~50k reviews. Be aware this may violate Google's ToS -- acceptable for a portfolio project, risky for commercial use.
- Build the pipeline to be source-agnostic from day one: a unified review schema (text, rating, timestamp, source, business_id, lat, lng) that accepts any provider.

**Warning signs:**
- You run the data collection phase and end up with only 30-45k reviews with heavily skewed temporal distribution (mostly 2023-2025).
- Temporal drift analysis shows suspiciously flat trends because you lack early-period reviews.

**Phase to address:**
Data Collection (Phase 1). This must be resolved before any NLP work begins. The entire temporal drift feature depends on having adequate review coverage across 2019-2025.

---

### Pitfall 2: Google Maps Platform Pricing Change (March 2025) -- The $200 Credit No Longer Exists

**What goes wrong:**
As of March 1, 2025, Google replaced the $200/month universal credit with per-SKU free usage thresholds. For Place Details (which includes reviews), you get 10,000 free Essentials-tier requests/month. But reviews require the "Pro" tier field mask, which costs $17.00 per 1,000 requests after the free threshold. If you request reviews for 9,000 businesses, you will pay $17 x 9 = $153 in a single month at Pro tier -- and that assumes no retries, pagination, or errors.

**Why it happens:**
The PROJECT.md references the "$200 free monthly credit" which is now outdated. The new pricing model is SKU-specific and tiered by field mask complexity. Requesting `reviews` fields bumps you from Essentials ($5/1k) to Pro ($17/1k).

**How to avoid:**
- Use field masks aggressively. First pass: Text Search with Essentials fields only (place_id, name, location) to build a business inventory. This is free up to 10,000/month.
- Second pass: Place Details with Pro fields (reviews) only for businesses you actually need. Budget carefully: 9,000 businesses x $17/1k = $153.
- Spread collection across 2-3 months if needed to stay within free tiers.
- Set billing alerts at $50, $100, $150 in Google Cloud Console.
- Cache every response. Never re-fetch a place you already have.

**Warning signs:**
- Google Cloud billing dashboard shows unexpected charges in the first week of data collection.
- You hit the 10,000 free threshold faster than expected due to retries or redundant requests.

**Phase to address:**
Data Collection (Phase 1). Must calculate exact costs before making the first API call.

---

### Pitfall 3: BERTopic on Short Review Text Produces 40-75% Outliers

**What goes wrong:**
HDBSCAN (BERTopic's default clustering algorithm) is density-based, meaning it labels low-density points as noise (topic -1). Short review texts (1-3 sentences) produce embeddings that cluster poorly because there is less semantic signal per document. In practice, 40-75% of short review documents end up as outliers, making topic analysis meaningless for the majority of your corpus.

**Why it happens:**
BERTopic was designed for longer documents (abstracts, articles). Short texts produce embeddings closer to the centroid of the embedding space (less discriminative). HDBSCAN's default `min_cluster_size=10` and `min_samples=10` are tuned for well-separated clusters, not the fuzzy clusters that short text embeddings produce.

**How to avoid:**
- Lower `min_cluster_size` to 5-15 and `min_samples` to 1-5 for review corpora. Start with `min_cluster_size=10, min_samples=3`.
- Reduce UMAP `n_neighbors` to 10-15 (default 15) and set `n_components=5` (default 5 is fine, but experiment with 3-10).
- After fitting, use `topic_model.reduce_outliers(docs, topics, strategy="embeddings")` to reassign outliers to their nearest topic using embedding similarity.
- Set `calculate_probabilities=True` so you can soft-assign outliers based on topic probability distributions.
- Consider concatenating reviews per business (aggregate 5 reviews into one "document") to increase document length before topic modelling. This reduces document count but dramatically improves cluster quality.
- Validate with topic coherence score (c_v) -- aim for 0.4-0.7. Below 0.3 means topics are not meaningful.

**Warning signs:**
- Topic -1 contains more than 30% of documents after initial fit.
- Coherence score below 0.3.
- Topic labels are generic ("good place nice food") rather than neighbourhood-specific.

**Phase to address:**
NLP Pipeline (Phase 2). Build an evaluation harness that reports outlier percentage and coherence score on every BERTopic run. Iterate hyperparameters systematically.

---

### Pitfall 4: Sentence-Transformer Model Mismatch for Review Text

**What goes wrong:**
Choosing `all-MiniLM-L6-v2` (the most commonly recommended model) because it is fast and popular. While it works, it was trained on general NLI/STS tasks, not on informal review language. Review text contains slang ("lowkey fire," "mid af"), sarcasm, emoji references, and domain-specific food/nightlife vocabulary that generic models handle poorly. The resulting embeddings fail to separate semantically distinct reviews about, say, "dive bar vibes" vs "craft cocktail scene."

**Why it happens:**
Developers pick the first model they see in tutorials. The MTEB leaderboard ranks models by average performance across many tasks, but review-specific semantic similarity is not well-represented in those benchmarks.

**How to avoid:**
- Use `all-mpnet-base-v2` as the baseline -- it is larger (420MB vs 80MB) but significantly better on semantic similarity tasks and handles informal text better.
- If compute allows, evaluate `BAAI/bge-base-en-v1.5` or `intfloat/e5-base-v2` which perform well on retrieval-like tasks (finding similar reviews).
- Run a small manual evaluation: embed 50 hand-picked review pairs that should be similar and 50 that should not. Compute cosine similarity and check if the model separates them. This takes 30 minutes and prevents months of downstream issues.
- Do NOT fine-tune the embedding model unless you have 10k+ labeled pairs. The ROI is not there for a portfolio project. Use the best off-the-shelf model instead.

**Warning signs:**
- FAISS nearest-neighbour queries return reviews that feel semantically unrelated.
- BERTopic produces topics that are syntactically similar but semantically different (clusters by sentence structure rather than meaning).
- Archetype cosine similarity scores cluster tightly (everything scores 0.3-0.5) instead of showing clear differentiation.

**Phase to address:**
NLP Pipeline (Phase 2). Model selection should be the FIRST decision in the pipeline phase, before BERTopic or sentiment work begins, since all downstream components depend on embedding quality.

---

### Pitfall 5: Domain-Adapted Sentiment Classifier Overfits to Star Ratings

**What goes wrong:**
Using Yelp star ratings as sentiment labels for fine-tuning creates a classifier that predicts star ratings, not sentiment. A 3-star review can be positive ("solid, reliable, nothing fancy but gets the job done") or negative ("used to be great, now it is mediocre"). Star ratings are noisy proxies for sentiment, and the class distribution is heavily skewed (Yelp reviews cluster at 1-star and 5-star, with fewer 2-4 star reviews).

**Why it happens:**
Star ratings are the easiest "free labels" available. Developers skip examining label quality because the training set is large (millions of reviews) and assume volume compensates for noise.

**How to avoid:**
- Collapse to 3 classes: negative (1-2 stars), neutral (3 stars), positive (4-5 stars). This reduces label noise significantly.
- Use stratified sampling to balance classes. Undersample 5-star reviews or oversample 3-star reviews.
- Evaluate on macro F1, not accuracy. Accuracy will be misleadingly high (85%+) because the model just predicts "positive" for everything.
- Hold out 500 reviews and manually verify sentiment labels. If more than 15% of labels disagree with the star rating, the label noise is too high for reliable fine-tuning.
- Consider using a pre-trained sentiment model (e.g., `cardiffnlp/twitter-roberta-base-sentiment-latest`) and only fine-tuning the last layer, rather than training from scratch. This is more robust to label noise.
- Report precision/recall per class, confusion matrix, and calibration curve -- not just F1.

**Warning signs:**
- Model achieves 90%+ accuracy but macro F1 is below 0.6.
- Confusion matrix shows near-zero recall on the neutral class.
- Model predicts "positive" for 80%+ of reviews regardless of content.

**Phase to address:**
NLP Pipeline (Phase 2). Sentiment classifier evaluation must include per-class metrics and manual spot-checks. Do not ship until neutral-class recall exceeds 0.4.

---

### Pitfall 6: Exponential Decay Produces Zero Weights for 2019-2020 Reviews

**What goes wrong:**
With a naive exponential decay `w = exp(-lambda * delta_t)`, a half-life of 1 year and `delta_t = 6 years` (2019 to 2025) produces `w = exp(-0.693 * 6) = 0.0156`. With a half-life of 6 months, the weight for a 2019 review is `exp(-1.386 * 6) = 0.00025` -- effectively zero. This means your temporal drift analysis for 2019-2020 is based on near-zero-weighted reviews, making the "vibe shift" visualization meaningless for early years.

**Why it happens:**
Developers implement exponential decay for recency weighting (correct for the live vibe score) but then reuse the same weights for temporal analysis (incorrect). Temporal analysis needs EQUAL weighting within each year bucket, not decay across the full timeline.

**How to avoid:**
- Separate the two use cases: (1) "Current vibe" score uses exponential decay with a 1-2 year half-life applied to the full timeline. (2) "Temporal drift" analysis uses NO decay -- each year bucket gets equal treatment, and the pipeline runs independently per bucket.
- For the "current vibe" score, use `half_life = 1.5 years` as a starting point. This gives 2019 reviews a weight of ~0.06 (small but non-zero).
- Implement decay in log-space to avoid underflow: compute `log_weight = -lambda * delta_t`, then use `logsumexp` when aggregating. Never compute `exp()` on individual weights and sum -- this causes numerical underflow.
- Clamp minimum weight to `1e-6` to prevent division-by-zero in weighted averages.

**Warning signs:**
- Sum of weights for a neighbourhood is dominated by the last 12 months (>95% of total weight).
- Temporal drift chart shows 2019-2020 as flat/identical despite known pandemic effects.
- NaN or inf values in aggregated scores.

**Phase to address:**
NLP Pipeline (Phase 2) for implementation, Frontend (Phase 3) for validating temporal visualizations make sense.

---

### Pitfall 7: MapLibre Full-Map Repaints on Every Animation Frame

**What goes wrong:**
MapLibre GL JS re-renders the entire map when any feature in any layer changes. When animating choropleth transitions (e.g., time slider moving year-by-year), updating fill colours triggers a full repaint per frame. At 60fps with 30 neighbourhood polygons, the browser struggles, causing janky animations, dropped frames, and high CPU/GPU usage -- especially on lower-end devices.

**Why it happens:**
MapLibre's rendering architecture is optimized for static or infrequently updated maps. The WebGL pipeline repaints all layers when the style changes, even if only one property on one layer changed. This is a known issue (maplibre-gl-js #96).

**How to avoid:**
- Use `map.setPaintProperty()` for colour transitions rather than replacing the entire style. This is the least expensive update path.
- Implement animation via CSS transitions on a DOM overlay for the sidebar/UI, and only update map fill colours at key frames (7 frames for 7 years), not continuously.
- Pre-compute interpolated colour arrays for each transition and apply them in a single batch `setPaintProperty` call.
- Use `map.triggerRepaint()` sparingly -- do NOT call it in a requestAnimationFrame loop.
- Test on a mid-range device (not just your development machine). Chrome DevTools Performance panel should show paint times under 16ms.
- For the time slider, debounce updates: only trigger map repaint when the slider stops, not on every drag event. Use `requestAnimationFrame` with frame skipping if continuous animation is needed.

**Warning signs:**
- Chrome DevTools shows paint times >16ms (missed frames at 60fps).
- GPU memory usage climbs during animation.
- Animation is smooth on MacBook Pro but janky on a 2-year-old laptop.

**Phase to address:**
Frontend / Visualization (Phase 3). Performance testing must be part of the acceptance criteria for the time slider feature.

---

### Pitfall 8: Temporal Drift Analysis with Insufficient Reviews Per Year Bucket

**What goes wrong:**
With ~50k total reviews across 30 neighbourhoods over 7 years, the average is ~240 reviews per neighbourhood-year. But distribution is not uniform: COVID-era 2020 may have 30-50 reviews for a neighbourhood while 2024 has 500+. Running BERTopic on 30 reviews produces meaningless topics. Comparing vibe vectors across years when one year has 30 reviews and another has 500 is statistically unsound.

**Why it happens:**
Developers treat temporal analysis as "just run the pipeline per year bucket" without checking if each bucket has enough data. The visualization looks convincing even when the underlying data is sparse, because colour interpolation smooths over noise.

**How to avoid:**
- Set a minimum threshold: do not compute vibe scores for neighbourhood-year buckets with fewer than 50 reviews. Show "insufficient data" in the UI instead.
- For sparse buckets, consider pooling adjacent years (2019-2020 combined) to reach minimum sample sizes. Label these pooled periods clearly in the UI.
- Use confidence intervals or error bars on vibe scores. A neighbourhood-year with 30 reviews should show wide uncertainty; one with 500 should show narrow uncertainty.
- Do NOT run BERTopic per year bucket. Instead, run BERTopic once on the full corpus to discover topics, then compute topic distributions per year bucket using the fitted model. This avoids the "different topics per year" problem and works with small samples.
- For statistical significance of drift: use bootstrap resampling (1000 iterations) to compute confidence intervals on the year-over-year vibe vector difference. If the confidence interval includes zero, the drift is not significant.

**Warning signs:**
- Some neighbourhood-year cells have fewer than 30 reviews.
- Year-over-year vibe changes are wildly different when you re-run the pipeline (instability = insufficient data).
- 2020 shows dramatic vibe shifts that are actually just sampling noise from low review volume.

**Phase to address:**
NLP Pipeline (Phase 2) for the methodology, Frontend (Phase 3) for communicating uncertainty to users.

---

### Pitfall 9: NYC Neighbourhood Boundaries -- No Official Standard, Projection Mismatch

**What goes wrong:**
There is no single official NYC neighbourhood boundary dataset. NYC Department of City Planning publishes NTAs (Neighbourhood Tabulation Areas), community districts, and census tracts -- none of which align with how New Yorkers actually think about neighbourhoods. The Williamsburg NTA boundary does not match what locals call "Williamsburg." Additionally, NYC government data uses EPSG:2263 (NAD83 / New York Long Island State Plane, feet), while web maps use EPSG:4326 (WGS84). Loading EPSG:2263 data directly into MapLibre produces polygons rendered in the wrong location (often in the ocean or off-screen).

**Why it happens:**
Developers download the first "NYC neighbourhoods" GeoJSON they find on GitHub without checking projection, boundary definitions, or topology. Multiple competing datasets exist (NYC Planning NTAs, Zillow neighbourhoods, Pediacities, custom academic datasets) with incompatible boundaries.

**How to avoid:**
- Use the NYC Department of Health's "NYC Geography" repository (github.com/nycehs/NYC_geography) which provides pre-processed GeoJSON files already transformed to WGS84 with cleaned topology.
- Alternatively, use Jared Lander's NYC neighbourhood boundaries which are curated for data analysis and available in GeoJSON/WGS84.
- Verify projection with: load into geojson.io and confirm polygons appear over NYC, not in the ocean.
- Validate topology: run `mapshaper -i boundaries.geojson -clean -o format=geojson` to fix self-intersections and gaps.
- Map your business lat/lng points to neighbourhoods using point-in-polygon (Shapely or Turf.js) and manually verify edge cases (businesses on neighbourhood borders).
- Ensure boundary names match your data pipeline's neighbourhood labels. "DUMBO" vs "Dumbo" vs "D.U.M.B.O." will silently drop data.

**Warning signs:**
- Polygons render in the wrong location (Atlantic Ocean, null island at 0,0).
- Some neighbourhoods have zero businesses mapped to them despite being well-known areas.
- Gaps or overlaps visible between adjacent neighbourhood polygons on the map.
- Name mismatches cause silent data loss (reviews exist but are not assigned to any neighbourhood).

**Phase to address:**
Data Collection (Phase 1). Boundary selection and validation must happen BEFORE business-to-neighbourhood assignment. This is a dependency for everything downstream.

---

### Pitfall 10: FAISS Index Overkill and Metadata Separation

**What goes wrong:**
Developers build a complex IVF or HNSW FAISS index for 30 neighbourhood vectors (one per neighbourhood). FAISS is designed for millions-to-billions of vectors. For 30 vectors, brute-force cosine similarity is faster than FAISS index construction, serialization, and loading. The overhead of FAISS (index file, loading time, memory mapping) adds complexity with zero performance benefit.

**Why it happens:**
The project spec says "serve embeddings and nearest-neighbour queries via FAISS" because FAISS is a resume-worthy technology. Developers apply it without considering whether the data scale justifies it.

**How to avoid:**
- Use FAISS for the review-level index (50k review embeddings) where ANN is actually beneficial. Use `IndexFlatIP` (inner product / cosine) for 50k vectors -- no training needed, fast enough, and serializes cleanly.
- For the 30 neighbourhood-level vectors, use plain NumPy cosine similarity. It is faster, simpler, and easier to debug.
- Store FAISS indexes as `.faiss` files using `faiss.write_index()`. Do NOT use pickle -- FAISS SWIG objects cannot be pickled.
- Store metadata (review text, business names, neighbourhood labels) separately in a JSON/SQLite file, keyed by the integer ID that FAISS returns. FAISS only stores vectors and integer IDs.
- Pre-build and serialize the index during the pipeline phase. Load it at server startup via `faiss.read_index()` in a FastAPI `lifespan` event. A 50k x 384-dim index is ~75MB and loads in <1 second.

**Warning signs:**
- FAISS index build takes >5 minutes for your data (means you are overcomplicating the index type).
- Pickle errors when trying to serialize a FAISS index.
- Server startup takes >10 seconds due to index loading.

**Phase to address:**
NLP Pipeline (Phase 2) for index building, Backend (Phase 3) for serving.

---

### Pitfall 11: Python ML Backend Cold Start and Memory on Free-Tier Hosting

**What goes wrong:**
Deploying a FastAPI backend that loads sentence-transformer models, FAISS indexes, and pre-computed artifacts on a free-tier platform (Render, Railway, Fly.io free tier). These platforms have 512MB-1GB RAM limits and aggressive cold-start timeouts (30 seconds). A sentence-transformer model alone is 80-420MB. Combined with FAISS index, pre-computed vibe scores, and the Python runtime itself, you easily exceed memory limits. Cold starts take 30-60 seconds as the model loads from disk.

**Why it happens:**
The project spec says "pre-computed artifacts" but developers still load the embedding model "just in case" or for the FAISS query endpoint. The design does not clearly separate "pipeline compute" from "serving."

**How to avoid:**
- The backend should NEVER load a sentence-transformer model. All embeddings are pre-computed. The backend serves pre-computed JSON artifacts and a pre-built FAISS index (which does not require the model to query).
- Serve pre-computed vibe scores, topic breakdowns, and temporal data as static JSON files. Consider hosting them on a CDN (Cloudflare Pages, Vercel static) with no backend at all for these endpoints.
- If FAISS nearest-neighbour is the only dynamic endpoint, isolate it in a minimal FastAPI service that loads only the FAISS index (~75MB) and a metadata lookup (~5MB). Total memory: ~200MB with Python overhead.
- Use FastAPI's `lifespan` context manager (not deprecated `on_event`) to load artifacts at startup.
- Set Gunicorn workers to 1 (not the default of 2*CPU+1) to avoid multiplying memory usage.

**Warning signs:**
- Deployment crashes with OOM (out of memory) errors.
- First request after idle period takes >10 seconds.
- Memory usage grows over time (memory leak from repeated model loading).

**Phase to address:**
Deployment (Phase 4). Architecture decision to NOT load ML models in production must be made during Backend design (Phase 3).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using star ratings directly as sentiment labels | Free labels, no annotation needed | 15-20% label noise, poor neutral-class performance | MVP only, with documented evaluation metrics |
| Hardcoding neighbourhood names | Fast mapping | Breaks when boundary dataset changes or names differ | Never -- use a lookup table/config file from day one |
| Storing reviews as flat JSON files | No database setup | Cannot query by neighbourhood, timestamp, or business efficiently | Phase 1 prototyping only, migrate to SQLite before pipeline |
| Skipping review deduplication | Saves pipeline complexity | Duplicate reviews inflate topic counts and bias vibe scores | Never -- dedupe by (text hash, business_id) |
| Using `all-MiniLM-L6-v2` without evaluation | Fast, small model | Weaker semantic separation for informal text | Acceptable if evaluation shows it performs adequately |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Google Places API (New) | Requesting all fields (billed at highest SKU tier) | Use explicit FieldMask; separate Essentials-only inventory pass from Pro-tier review fetch |
| Google Places API (New) | Not handling `ZERO_RESULTS` or `INVALID_REQUEST` gracefully | Implement exponential backoff, log failed place_ids for retry, never crash the batch |
| Yelp Fusion API | Exceeding 5000 requests/day rate limit | Implement rate limiter (1 req/second), spread collection over multiple days |
| MapLibre GL JS | Loading raw GeoJSON in EPSG:2263 projection | Always convert to WGS84 (EPSG:4326) before loading; validate on geojson.io |
| FAISS | Pickling FAISS index objects | Use `faiss.write_index()` / `faiss.read_index()` for serialization |
| BERTopic | Calling `.fit_transform()` per year bucket | Call `.fit_transform()` once on full corpus, then use `.transform()` or topic distributions per bucket |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Re-embedding reviews on every pipeline run | Pipeline takes hours; GPU maxed out | Cache embeddings to `.npy` file after first run; check hash of input data | First re-run after adding new reviews |
| MapLibre full repaint on time slider drag | Janky animation, high GPU usage, dropped frames | Debounce slider events; batch colour updates; use `setPaintProperty` | Any device without a discrete GPU |
| Loading full review corpus into memory for FAISS | 2-4GB RAM spike at startup | Memory-map the FAISS index with `faiss.read_index(path, faiss.IO_FLAG_MMAP)` | When corpus exceeds 100k reviews |
| Uncompressed GeoJSON with high polygon detail | Slow initial map load (2-5 seconds) | Simplify polygons with Mapshaper (tolerance 0.0001); use TopoJSON for 60-80% size reduction | >500KB GeoJSON file |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Committing API keys (Google, Yelp) to git | Key theft, unexpected billing charges | Use `.env` file with `python-dotenv`; add `.env` to `.gitignore`; use environment variables in deployment |
| Exposing FAISS query endpoint without rate limiting | DoS via expensive vector search queries | Add rate limiting (10 req/s per IP) via FastAPI middleware or Cloudflare |
| Serving review text with PII (reviewer names, phone numbers) | Privacy liability | Strip author attribution before storing; serve anonymised review excerpts only |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing vibe scores without context | Users do not know if 0.72 is high or low | Show relative ranking ("more artsy than 85% of neighbourhoods") or use qualitative labels |
| Time slider with no visual feedback during transition | Users think the app is frozen during year transitions | Show a loading shimmer or smooth interpolation between states |
| Colour palette that is not colourblind-accessible | ~8% of male users cannot distinguish red-green vibe categories | Use a colourblind-safe palette (viridis, cividis); test with a colourblindness simulator |
| Too many vibe categories visible at once | Cognitive overload; map becomes unreadable | Default to one vibe at a time; let users toggle additional vibes on demand |
| No explanation of what "artsy" or "foodie" means | Users do not trust opaque labels | Show the seed phrases and representative reviews that define each archetype |

## "Looks Done But Isn't" Checklist

- [ ] **Data collection:** Reviews span all 7 years (2019-2025) -- verify histogram of review timestamps per neighbourhood, not just total count
- [ ] **BERTopic:** Outlier percentage is below 30% after reduction -- check `(topics == -1).sum() / len(topics)`
- [ ] **Sentiment classifier:** Neutral class recall exceeds 0.4 -- check confusion matrix, not just overall F1
- [ ] **FAISS index:** Nearest-neighbour results make semantic sense -- manually query 10 neighbourhoods and verify the top-3 similar ones are plausible
- [ ] **Exponential decay:** 2019 reviews still have non-zero influence on current vibe -- print sum of weights per year
- [ ] **GeoJSON boundaries:** All 30 neighbourhoods have reviews mapped to them -- check for zero-count neighbourhoods caused by name mismatches
- [ ] **Map rendering:** Choropleth loads and animates smoothly on a non-development device -- test on a Chromebook or phone
- [ ] **Deployment:** Cold start completes in under 10 seconds -- time the first request after a 30-minute idle period
- [ ] **Temporal drift:** Confidence intervals are shown for sparse year buckets -- verify 2020 shows wider uncertainty than 2024

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Only 5 reviews per place from Google API | MEDIUM | Supplement with Yelp Open Dataset or third-party scraping API; re-run business inventory to identify coverage gaps |
| 60%+ BERTopic outliers | LOW | Adjust HDBSCAN parameters and re-run (minutes, not hours); use `reduce_outliers()` post-hoc without re-training |
| Sentiment model predicts only positive | MEDIUM | Collapse to 3 classes, rebalance training set, retrain with focal loss; 2-4 hours of work |
| FAISS index will not serialize | LOW | Switch from pickle to `faiss.write_index()`; 10-minute fix |
| GeoJSON in wrong projection | LOW | Run through Mapshaper or use `pyproj` to convert EPSG:2263 to EPSG:4326; 30-minute fix |
| Backend OOM on deployment | MEDIUM | Remove sentence-transformer model from backend; serve vibe scores as static JSON; restructure to load only FAISS index |
| Exponential decay zeros out early years | LOW | Switch to log-space computation; add minimum weight clamp; re-run aggregation |
| Map animation janky | MEDIUM | Reduce animation to key-frame transitions; debounce slider; simplify GeoJSON; 1-2 days of optimization |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 5-review API limit | Phase 1: Data Collection | Review count histogram by year shows coverage across 2019-2025 |
| Pricing model change | Phase 1: Data Collection | Google Cloud billing stays under $50 for initial data pull |
| BERTopic outlier flood | Phase 2: NLP Pipeline | Outlier rate < 30% reported in pipeline logs |
| Embedding model mismatch | Phase 2: NLP Pipeline | Manual evaluation of 50 review pairs shows meaningful similarity separation |
| Sentiment label noise | Phase 2: NLP Pipeline | Per-class F1 reported; neutral recall > 0.4 |
| Exponential decay underflow | Phase 2: NLP Pipeline | Weight-per-year histogram shows non-zero values for all years |
| Temporal drift small samples | Phase 2: NLP Pipeline | Minimum 50 reviews per neighbourhood-year or bucket is marked insufficient |
| GeoJSON projection/topology | Phase 1: Data Collection | All polygons render correctly on geojson.io; all neighbourhoods have mapped businesses |
| FAISS serialization | Phase 2: NLP Pipeline | Index round-trips through write/read without error |
| MapLibre animation perf | Phase 3: Frontend | Paint times < 16ms in Chrome DevTools on mid-range device |
| Backend cold start / OOM | Phase 4: Deployment | Memory usage < 512MB; cold start < 10 seconds |

## Sources

- [Google Maps Platform March 2025 pricing changes](https://developers.google.com/maps/billing-and-pricing/march-2025) -- HIGH confidence (official docs)
- [Google Maps Platform pricing list](https://developers.google.com/maps/billing-and-pricing/pricing) -- HIGH confidence (official docs)
- [Google Places API REST reference (review limit)](https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places) -- HIGH confidence (official docs)
- [Google Issue Tracker #35825957 (5 review limit)](https://issuetracker.google.com/issues/35825957) -- HIGH confidence (official issue tracker)
- [BERTopic best practices](https://maartengr.github.io/BERTopic/getting_started/best_practices/best_practices.html) -- HIGH confidence (official docs)
- [BERTopic outlier reduction](https://maartengr.github.io/BERTopic/getting_started/outlier_reduction/outlier_reduction.html) -- HIGH confidence (official docs)
- [BERTopic parameter tuning](https://maartengr.github.io/BERTopic/getting_started/parameter%20tuning/parametertuning.html) -- HIGH confidence (official docs)
- [Gibbs-BERTopic for short text (Feb 2025)](https://www.researchgate.net/publication/389929907) -- MEDIUM confidence (peer-reviewed research)
- [SBERT pretrained models](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html) -- HIGH confidence (official docs)
- [FAISS serialization issues](https://github.com/facebookresearch/faiss/issues/227) -- HIGH confidence (official GitHub)
- [FAISS indexes that do not fit in RAM](https://github.com/facebookresearch/faiss/wiki/Indexes-that-do-not-fit-in-RAM) -- HIGH confidence (official wiki)
- [NYC Geography GeoJSON repository](https://github.com/nycehs/NYC_geography) -- MEDIUM confidence (NYC government adjacent)
- [MapLibre GL JS repaint performance issue #96](https://github.com/maplibre/maplibre-gl-js/issues/96) -- HIGH confidence (official GitHub)
- [MapLibre large GeoJSON optimization guide](https://maplibre.org/maplibre-gl-js/docs/guides/large-data/) -- HIGH confidence (official docs)
- [Forward Decay paper (Rutgers)](https://dimacs.rutgers.edu/~graham/pubs/papers/fwddecay.pdf) -- HIGH confidence (academic paper)

---
*Pitfalls research for: NLP-powered neighbourhood vibe visualization (NYC reviews)*
*Researched: 2026-03-16*

# Phase 2: NLP Pipeline - Research

**Researched:** 2026-03-17
**Domain:** NLP / Topic Modeling / Sentence Embeddings / FAISS / LoRA Fine-Tuning
**Confidence:** HIGH

## Summary

Phase 2 transforms 1.1M Philadelphia Yelp reviews (from the Phase 1 SQLite database) into static ML artifacts: sentence embeddings, BERTopic topics, 6-dimensional vibe archetype scores, a fine-tuned sentiment model, temporal drift series, a FAISS similarity index, and representative quotes. All computation runs once offline; the backend (Phase 3) loads only serialized artifacts.

The core libraries are well-established and their APIs are stable: sentence-transformers 5.x for embedding, BERTopic 0.17.x for topic modeling, PEFT 0.18.x for LoRA fine-tuning, and faiss-cpu 1.13.x for nearest-neighbour search. The main risk areas are (1) BERTopic outlier rate on short review text (40-75% outliers without tuning), (2) the temporal window mismatch (Yelp data covers 2005-2022, not 2019-2025 as originally scoped for NYC), and (3) memory management when embedding 1.1M reviews.

**Primary recommendation:** Build the pipeline as 6 sequential stages in a single orchestrator script, each gated by artifact-exists checks. Pre-compute all embeddings first (reused by BERTopic and vibe scoring), then topic model, then score vibes, then fine-tune sentiment, then temporal drift, then FAISS + quotes + GeoJSON export. Each stage streams data from SQLite in chunks to avoid loading 1.1M reviews into memory at once.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
The user delegated all implementation decisions to Claude. Choices below represent the best technical approach given the project constraints (local GPU, portfolio/resume priority, static artifacts, Python stack).

- **Global BERTopic model** -- train one BERTopic model over all Philadelphia reviews combined, not per-neighbourhood. HDBSCAN params: `min_cluster_size=10`, `min_samples=3`, with `reduce_outliers()` after fitting. Target >=20 distinct topics with <50% outlier rate.
- **Embedding model:** `all-MiniLM-L6-v2` (384-dimensional). Batch size 256, configurable via `EMBED_BATCH_SIZE` env var. Checkpointing via artifact existence.
- **Sentiment fine-tuning:** DistilBERT + LoRA (rank=16, alpha=32, dropout=0.1) on full 6.9M Yelp reviews. 3-class (negative/neutral/positive). 3 epochs, batch 32, AdamW lr=2e-4. Merge LoRA weights before export.
- **Vibe scoring:** cosine similarity between topic cluster centroids and archetype seed phrase embeddings, weighted by per-neighbourhood topic distribution. Recency weighting with exponential decay (half-life 365 days, log-space, min clamp 1e-6).
- **Temporal drift:** bucket by year, run full vibe scoring per year bucket with equal weights.
- **FAISS:** flat index over 6D neighbourhood vibe vectors. `faiss_index.bin` + `faiss_id_map.json`.
- **Representative quotes:** 3-5 per neighbourhood per archetype, highest cosine similarity to archetype centroid, truncated to 300 chars.
- **Artifacts directory:** `data/output/artifacts/` with JSON (indent=2) + numpy + FAISS binary formats. No pickle, HDF5, or parquet.
- **Pipeline resumability:** each stage checks for output artifact, `--force` reruns all, `--force-stage <name>` reruns one.
- **Entry point:** `scripts/06_run_nlp_pipeline.py`

### Claude's Discretion
All implementation decisions were delegated to Claude -- the CONTEXT.md decisions above ARE the discretion-exercised choices.

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NLP-01 | Embed all reviews with sentence-transformer (`all-MiniLM-L6-v2`) | sentence-transformers 5.3.0 `model.encode()` with batch_size, numpy output; checkpoint via `embeddings.npy` existence |
| NLP-02 | BERTopic topic discovery with HDBSCAN tuning and `reduce_outliers()` | BERTopic 0.17.4 with pre-computed embeddings; 4 outlier reduction strategies documented; safetensors serialization |
| NLP-03 | Score 6 vibe archetypes via cosine similarity between topic centroids and seed phrases | numpy cosine similarity on 384D vectors; archetype config in JSON; weighted aggregation per neighbourhood |
| NLP-04 | LoRA fine-tune DistilBERT sentiment classifier, merge adapter | PEFT 0.18.1 LoraConfig with task_type="SEQ_CLS"; `merge_and_unload()` then `save_pretrained()` |
| NLP-05 | Recency-weighted vibe scores with exponential decay | Log-space computation: `log_weight = -lambda * delta_days`; `np.exp(log_weight).clip(min=1e-6)` |
| NLP-06 | Temporal drift: year-bucketed vibe scoring (2019-2021 actual range) | Yelp data ends Jan 2022; meaningful years are 2010-2021; quality gate used 2019-2021 |
| NLP-07 | FAISS flat index over neighbourhood vibe vectors | faiss-cpu 1.13.2 `IndexFlatIP` with L2-normalized vectors for cosine similarity |
| NLP-08 | Representative quotes (3-5 per neighbourhood per archetype) | Cosine similarity ranking of review embeddings vs archetype embeddings; truncate to 300 chars |
| NLP-09 | Export all artifacts as serialized files | Artifact manifest: 11 outputs in `data/output/artifacts/` directory |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sentence-transformers | 5.3.0 | Review embedding with `all-MiniLM-L6-v2` | Installed locally; stable encode API; 384D vectors ideal for short text |
| bertopic | 0.17.4 | Topic modeling over review embeddings | Standard BERTopic with HDBSCAN/UMAP/c-TF-IDF pipeline; safetensors serialization |
| peft | 0.18.1 | LoRA adapter for DistilBERT fine-tuning | Official HuggingFace PEFT; `merge_and_unload()` for clean export |
| transformers | 5.3.0 | DistilBERT base model + Trainer API | Installed locally; AutoModelForSequenceClassification + TrainingArguments |
| torch | 2.10.0 | Deep learning backend | Installed locally; powers sentence-transformers and transformers |
| faiss-cpu | 1.13.2 | Nearest-neighbour index over vibe vectors | CPU-only sufficient for 157 6D vectors; flat index is exact |
| numpy | (installed) | Embedding storage and vector math | .npy format for embeddings; cosine similarity computation |
| hdbscan | 0.8.41 | Clustering backend for BERTopic | Required by BERTopic; `min_cluster_size` and `min_samples` tuning |
| umap-learn | (latest) | Dimensionality reduction for BERTopic | Required by BERTopic; UMAP reduces 384D to ~5D before HDBSCAN |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scikit-learn | (installed) | CountVectorizer for BERTopic c-TF-IDF | Automatically used by BERTopic internals |
| datasets | (latest) | Load Yelp review dataset for sentiment fine-tuning | HuggingFace datasets for efficient data loading with streaming |
| accelerate | (latest) | Training acceleration for Trainer API | Required by transformers Trainer when using GPU |
| safetensors | (latest) | BERTopic model serialization | Smaller, faster model saving than pickle |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| all-MiniLM-L6-v2 | all-mpnet-base-v2 | Higher quality but 2x slower, 768D; MiniLM is sufficient for short reviews |
| BERTopic | LDA (gensim) | LDA is bag-of-words, loses semantic meaning; BERTopic is resume-differentiator |
| LoRA fine-tune | VADER sentiment | VADER is rule-based, no domain adaptation; LoRA shows ML depth for portfolio |
| FAISS flat | brute-force numpy | FAISS is the industry standard; flat index IS brute-force but with optimized implementation |

**Installation:**
```bash
pip install sentence-transformers==5.3.0 bertopic==0.17.4 peft==0.18.1 faiss-cpu==1.13.2 hdbscan==0.8.41 umap-learn datasets accelerate safetensors
```

**Note:** torch 2.10.0 and transformers 5.3.0 are already installed locally.

## Architecture Patterns

### Recommended Project Structure
```
scripts/
  06_run_nlp_pipeline.py          # Orchestrator: runs all stages in order
pipeline/
  __init__.py
  stages/
    __init__.py
    embed.py                       # Stage 1: sentence-transformer encoding
    topic_model.py                 # Stage 2: BERTopic fit + outlier reduction
    vibe_score.py                  # Stage 3: archetype cosine similarity scoring
    sentiment.py                   # Stage 4: DistilBERT + LoRA fine-tuning
    temporal.py                    # Stage 5: year-bucketed vibe drift
    export.py                      # Stage 6: FAISS index + quotes + GeoJSON
  archetypes.json                  # Vibe archetype seed phrases (configurable)
  PIPELINE_DECISIONS.md            # Technical rationale for resume/interviews
data/output/artifacts/
  embeddings.npy                   # (n_reviews, 384) float32
  review_ids.npy                   # (n_reviews,) int64 aligned to embeddings
  bertopic_model/                  # safetensors serialized BERTopic
  topic_assignments.json           # {review_id: topic_id}
  vibe_scores.json                 # {neighbourhood_id: {archetype: score}}
  temporal_series.json             # {neighbourhood_id: {year: {archetype: score}}}
  faiss_index.bin                  # FAISS flat index binary
  faiss_id_map.json                # FAISS int ID -> neighbourhood_id
  representative_quotes.json       # {neighbourhood_id: {archetype: [quote, ...]}}
  sentiment_model/                 # merged DistilBERT weights
  enriched_geojson.geojson         # NTA GeoJSON with vibe scores in properties
```

### Pattern 1: Stage-Based Pipeline with Artifact Gating
**What:** Each pipeline stage checks for its output artifact before running; skips if found.
**When to use:** Every stage in the pipeline.
**Example:**
```python
from pathlib import Path

ARTIFACTS_DIR = Path("data/output/artifacts")

def run_stage(name: str, output_path: Path, force: bool, fn, *args, **kwargs):
    """Generic stage runner with artifact gating."""
    if output_path.exists() and not force:
        _log("INFO", f"Stage '{name}': artifact exists at {output_path}, skipping")
        return
    _log("INFO", f"Stage '{name}': starting...")
    fn(*args, **kwargs)
    _log("INFO", f"Stage '{name}': complete -> {output_path}")
```

### Pattern 2: Chunked SQLite Reading
**What:** Stream reviews from SQLite in batches to avoid loading 1.1M rows into memory.
**When to use:** Embedding stage, any stage that reads all reviews.
**Example:**
```python
def iter_reviews(db_path: str, batch_size: int = 10_000):
    """Yield batches of (review_id, text, stars, review_date, neighbourhood_id)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("""
        SELECT r.rowid, r.text, r.stars, r.review_date, b.neighbourhood_id
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
        ORDER BY r.rowid
    """)
    batch = []
    for row in cursor:
        batch.append(row)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
    conn.close()
```

### Pattern 3: Pre-computed Embeddings Passed to BERTopic
**What:** Compute embeddings once, pass as numpy array to `BERTopic.fit_transform()`.
**When to use:** BERTopic stage -- avoids re-embedding inside BERTopic.
**Example:**
```python
from bertopic import BERTopic
from hdbscan import HDBSCAN
from umap import UMAP

# Pre-computed embeddings (from Stage 1)
embeddings = np.load("data/output/artifacts/embeddings.npy")

umap_model = UMAP(n_components=5, n_neighbors=15, min_dist=0.0,
                   metric="cosine", random_state=42)
hdbscan_model = HDBSCAN(min_cluster_size=10, min_samples=3,
                         prediction_data=True)

topic_model = BERTopic(
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    calculate_probabilities=True,
    verbose=True
)

topics, probs = topic_model.fit_transform(docs, embeddings=embeddings)
```

### Pattern 4: Outlier Reduction Chain
**What:** Apply outlier reduction after BERTopic fitting to bring outlier rate below 50%.
**When to use:** After `fit_transform()` returns.
**Example:**
```python
# Check initial outlier rate
outlier_count = sum(1 for t in topics if t == -1)
outlier_rate = outlier_count / len(topics)
_log("INFO", f"Initial outlier rate: {outlier_rate:.1%} ({outlier_count}/{len(topics)})")

# Strategy 1: c-TF-IDF based (best for short text per research)
new_topics = topic_model.reduce_outliers(docs, topics, strategy="c-tf-idf")

# If still above threshold, chain with embeddings strategy
outlier_rate = sum(1 for t in new_topics if t == -1) / len(new_topics)
if outlier_rate > 0.5:
    new_topics = topic_model.reduce_outliers(
        docs, new_topics, strategy="embeddings",
        embeddings=embeddings
    )

# CRITICAL: update topic representations after outlier reduction
topic_model.update_topics(docs, topics=new_topics)
```

### Pattern 5: LoRA Fine-Tuning with Merge
**What:** Fine-tune DistilBERT with LoRA, merge weights, save standalone model.
**When to use:** Sentiment training stage.
**Example:**
```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType

base_model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased", num_labels=3
)
lora_config = LoraConfig(
    task_type=TaskType.SEQ_CLS,
    r=16, lora_alpha=32, lora_dropout=0.1,
    target_modules=["q_lin", "v_lin"]  # DistilBERT attention layers
)
model = get_peft_model(base_model, lora_config)

# ... train with Trainer API ...

# Merge and save
merged_model = model.merge_and_unload()  # NOT in-place -- must capture return value
merged_model.save_pretrained("data/output/artifacts/sentiment_model")
tokenizer.save_pretrained("data/output/artifacts/sentiment_model")
```

### Anti-Patterns to Avoid
- **Loading all reviews into memory at once:** 1.1M reviews with text is multiple GB. Stream from SQLite in chunks.
- **Re-embedding inside BERTopic:** BERTopic will re-embed if you don't pass `embeddings=` parameter. Always pass pre-computed embeddings.
- **Forgetting `update_topics()` after `reduce_outliers()`:** Topic representations become stale if you only update the topic assignments without calling `update_topics()`.
- **Using `merge_and_unload()` as in-place:** It returns a new model. `model.merge_and_unload()` without assignment discards the merged model.
- **FAISS with un-normalized vectors for cosine similarity:** `IndexFlatIP` computes inner product, which equals cosine similarity ONLY if vectors are L2-normalized first.
- **Exponential decay inside temporal year buckets:** Decay is for current-vibe scoring only; temporal buckets use equal weights within each year.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sentence embedding | Custom word2vec averaging | `SentenceTransformer("all-MiniLM-L6-v2").encode()` | Pre-trained contextual embeddings vastly outperform averaging |
| Topic modeling | K-means on TF-IDF | BERTopic with HDBSCAN | Density-based clustering finds natural topic count; no k to guess |
| Outlier reduction | Manual threshold reassignment | `topic_model.reduce_outliers()` | 4 built-in strategies, tested on short text |
| Cosine similarity | Manual dot product + norm | `sklearn.metrics.pairwise.cosine_similarity` or `np.dot` on normalized vectors | Edge cases (zero vectors, numerical stability) handled |
| FAISS index | Brute-force numpy distance matrix | `faiss.IndexFlatIP` | FAISS is optimized C++ under the hood; standard for portfolio |
| LoRA fine-tuning | Manual weight matrix injection | `peft.get_peft_model()` + `LoraConfig` | Merge/unload, gradient checkpointing, all handled |
| Class-imbalanced sampling | Manual oversampling/undersampling | `WeightedRandomSampler` from PyTorch | Correct probability weighting per-sample |

**Key insight:** Every "hand-roll" temptation in this phase has a battle-tested library solution. The portfolio value comes from correctly orchestrating these tools together, not from reimplementing them.

## Common Pitfalls

### Pitfall 1: BERTopic Outlier Explosion on Short Text
**What goes wrong:** HDBSCAN assigns 40-75% of short review documents as outliers (topic -1) because short texts have sparse, noisy embeddings in high-dimensional space.
**Why it happens:** HDBSCAN density estimation struggles when many points are equidistant in high dimensions. Short reviews (1-3 sentences) produce less distinctive embeddings than longer documents.
**How to avoid:**
1. Use `min_cluster_size=10` (small) and `min_samples=3` (permissive) as specified
2. Set UMAP `n_components=5` (not 2) to preserve more information before clustering
3. Apply `reduce_outliers()` with c-TF-IDF strategy first (best for short text), then embeddings strategy if still above 50%
4. Always call `update_topics()` after reducing outliers
**Warning signs:** Outlier rate above 50% after fitting, fewer than 20 topics discovered.

### Pitfall 2: Memory Exhaustion Embedding 1.1M Reviews
**What goes wrong:** Loading all 1.1M review texts into a Python list consumes 2-4 GB RAM. Then `model.encode()` creates a (1.1M, 384) float32 array = ~1.6 GB. Total peak can exceed 6 GB.
**Why it happens:** sentence-transformers `encode()` returns the full numpy array at once, and the input texts must all be in memory too.
**How to avoid:**
1. Stream review texts from SQLite in chunks (e.g., 50,000 at a time)
2. Encode each chunk, append to a growing numpy array on disk using `np.save` incrementally or pre-allocate the output array
3. Alternative: encode all at once if machine has 16+ GB RAM (the 1.6 GB output is manageable; the text list is the bottleneck)
4. Use `show_progress_bar=True` on `model.encode()` to monitor progress
**Warning signs:** Python process exceeds available RAM, OOM kill, machine becomes unresponsive.

### Pitfall 3: Temporal Window Mismatch
**What goes wrong:** Requirements specify 2019-2025, but Yelp Open Dataset for Philadelphia only covers reviews through January 2022. Years 2023, 2024, 2025 have zero reviews.
**Why it happens:** The project pivoted from NYC (where the temporal window was aspirational) to Philadelphia (Yelp Open Dataset). The Yelp Academic Dataset was last refreshed in early 2022.
**How to avoid:**
1. Adapt temporal bucketing to actual data range. Meaningful years with substantial review counts: 2010-2021 (2022 has only 3,293 reviews, truncated).
2. For the quality gate "all 30 neighbourhoods across all years", note there are 157 Philadelphia neighbourhoods (not 30). Use the years that actually have data.
3. Success criterion #3 should be validated against actual available years (e.g., 2015-2021 or 2019-2021) not the aspirational 2019-2025.
4. Document this discrepancy in `PIPELINE_DECISIONS.md` for transparency.
**Warning signs:** Empty year buckets producing NaN/zero vibe scores, misleading temporal drift charts.

### Pitfall 4: Sentiment Fine-Tuning on 6.9M Reviews Requires Streaming
**What goes wrong:** Loading the full Yelp review dataset (6.9M reviews) into memory for fine-tuning causes OOM.
**Why it happens:** 6.9M reviews with text fields is ~30 GB of raw text.
**How to avoid:**
1. Use HuggingFace `datasets` library with memory-mapped files or streaming
2. Stream the NDJSON file line-by-line, tokenize on-the-fly
3. Use `Trainer` with `dataloader_num_workers` and `per_device_train_batch_size=32`
4. If GPU memory is limited (no CUDA detected in current env), consider training on a subset (e.g., 500K reviews) or using CPU with gradient accumulation
**Warning signs:** OOM during tokenization, training taking days on CPU.

### Pitfall 5: FAISS Cosine Similarity Requires L2 Normalization
**What goes wrong:** `IndexFlatIP` returns inner product scores, not cosine similarity. If vectors are not unit-normalized, results are magnitude-biased.
**Why it happens:** FAISS does not have a native cosine similarity index. The standard pattern is to L2-normalize vectors first, then use inner product (which equals cosine similarity for unit vectors).
**How to avoid:**
```python
import faiss
import numpy as np

vibe_vectors = np.array(...)  # shape (157, 6), float32
faiss.normalize_L2(vibe_vectors)  # in-place L2 normalization
index = faiss.IndexFlatIP(6)
index.add(vibe_vectors)
```
**Warning signs:** Similarity scores outside [-1, 1] range, neighbourhoods with more reviews always appearing "most similar".

### Pitfall 6: DistilBERT LoRA Target Module Names
**What goes wrong:** LoRA config specifies wrong `target_modules` for DistilBERT architecture.
**Why it happens:** DistilBERT uses different attention layer names than BERT. BERT uses `query`, `value`; DistilBERT uses `q_lin`, `v_lin`.
**How to avoid:** Use `target_modules=["q_lin", "v_lin"]` for DistilBERT. Verify with `model.print_trainable_parameters()` after applying LoRA.
**Warning signs:** Zero trainable parameters reported, or error about module names not found.

## Code Examples

### Embedding Stage (NLP-01)
```python
# Source: sentence-transformers official API
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

# Stream from SQLite, encode in batches
all_embeddings = []
all_ids = []
for batch in iter_reviews(db_path, batch_size=50_000):
    ids = [row[0] for row in batch]
    texts = [row[1] for row in batch]
    embs = model.encode(texts, batch_size=256, show_progress_bar=True,
                        normalize_embeddings=False)
    all_embeddings.append(embs)
    all_ids.extend(ids)

embeddings = np.vstack(all_embeddings)  # (N, 384)
np.save(ARTIFACTS_DIR / "embeddings.npy", embeddings)
np.save(ARTIFACTS_DIR / "review_ids.npy", np.array(all_ids, dtype=np.int64))
```

### BERTopic with Outlier Reduction (NLP-02)
```python
# Source: BERTopic official docs - best practices + outlier reduction
from bertopic import BERTopic
from hdbscan import HDBSCAN
from umap import UMAP

umap_model = UMAP(n_components=5, n_neighbors=15, min_dist=0.0,
                   metric="cosine", random_state=42)
hdbscan_model = HDBSCAN(min_cluster_size=10, min_samples=3,
                         prediction_data=True)

topic_model = BERTopic(
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    calculate_probabilities=True,
    verbose=True
)

topics, probs = topic_model.fit_transform(docs, embeddings=embeddings)

# Reduce outliers (c-TF-IDF best for short text)
new_topics = topic_model.reduce_outliers(docs, topics, strategy="c-tf-idf")
topic_model.update_topics(docs, topics=new_topics)

# Save with safetensors
topic_model.save(
    str(ARTIFACTS_DIR / "bertopic_model"),
    serialization="safetensors",
    save_ctfidf=True,
    save_embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)
```

### Vibe Archetype Scoring (NLP-03 + NLP-05)
```python
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Load archetype seed phrases and embed them
with open("pipeline/archetypes.json") as f:
    archetypes = json.load(f)  # {"artsy": ["art gallery", "creative", ...], ...}

archetype_embeddings = {}
for name, phrases in archetypes.items():
    phrase_embs = model.encode(phrases)
    archetype_embeddings[name] = phrase_embs.mean(axis=0)  # centroid

# Per-neighbourhood: aggregate topic centroids weighted by review count
# then compute cosine similarity to each archetype
```

### FAISS Index (NLP-07)
```python
# Source: FAISS official docs
import faiss
import numpy as np

vibe_matrix = np.array([scores[nid] for nid in sorted_nids], dtype=np.float32)
faiss.normalize_L2(vibe_matrix)  # MUST normalize for cosine similarity

index = faiss.IndexFlatIP(6)  # 6 vibe dimensions
index.add(vibe_matrix)
faiss.write_index(index, str(ARTIFACTS_DIR / "faiss_index.bin"))

# Query example
query = vibe_matrix[0:1]  # single neighbourhood
D, I = index.search(query, k=5)  # returns distances and indices
```

### Archetype Config File
```json
{
  "artsy": ["art gallery", "creative space", "street art", "indie music", "bohemian", "artist studio"],
  "foodie": ["amazing food", "best restaurant", "culinary experience", "farm to table", "food scene"],
  "nightlife": ["great bar", "nightclub", "live music venue", "cocktail bar", "late night", "DJ"],
  "family": ["kid friendly", "family restaurant", "playground nearby", "safe neighborhood", "family owned"],
  "upscale": ["fine dining", "luxury", "upscale boutique", "high end", "exclusive", "elegant"],
  "cultural": ["museum", "historic landmark", "cultural center", "heritage", "diversity", "ethnic cuisine"]
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| BERTopic pickle serialization | safetensors serialization | BERTopic 0.16+ | 25x smaller model files, no arbitrary code execution risk |
| sentence-transformers 2.x API | sentence-transformers 5.x API | 2025 | Major version jump; `encode()` API is stable but check for breaking changes |
| PEFT 0.4-0.8 merge workflow | PEFT 0.18 `merge_and_unload()` | 2025 | Return value semantics unchanged; more model types supported |
| faiss-cpu 1.7.x | faiss-cpu 1.13.2 | 2025 | API stable; `IndexFlatIP` unchanged |

**Deprecated/outdated:**
- **BERTopic pickle save:** Use safetensors instead (smaller, safer)
- **VADER for sentiment:** Rule-based, no domain adaptation. LoRA fine-tuning is the modern approach for portfolio projects.
- **LDA for topic modeling:** Bag-of-words loses semantic meaning. BERTopic leverages transformer embeddings.

## Open Questions

1. **GPU Availability for Training**
   - What we know: Current environment shows `torch.cuda.is_available() = False` (WSL2 without CUDA configured).
   - What's unclear: Whether the user's local machine has a GPU that can be exposed to WSL2, or if training must be CPU-only.
   - Recommendation: Design pipeline to work CPU-only but with GPU acceleration as optional speedup. Sentiment fine-tuning on 6.9M reviews will be extremely slow on CPU (days). Consider training on a subset (e.g., 500K-1M reviews) if CPU-only, or using a Colab/cloud GPU for the sentiment stage.

2. **Sentiment Training Data Source**
   - What we know: CONTEXT.md says "fine-tune on the full Yelp Open Dataset (all 6.9M reviews)". The user has the review NDJSON file locally.
   - What's unclear: Whether 6.9M reviews is feasible on CPU or if we should automatically fall back to a subset.
   - Recommendation: Implement with configurable `MAX_TRAIN_SAMPLES` (default: all). Log estimated training time after first batch and warn if > 4 hours.

3. **157 Neighbourhoods vs "30" in Requirements**
   - What we know: Requirements say "30 neighbourhoods" (from NYC scope). Philadelphia has 157 neighbourhoods with reviews.
   - What's unclear: Whether to use all 157 or filter to top-N with most reviews.
   - Recommendation: Use all 157 for pipeline computation (FAISS handles it fine). Frontend can show all or filter later. The quality report already shows all 157 pass the coverage gate.

4. **Temporal Range Adaptation**
   - What we know: Yelp data covers 2005-01-2022. Requirements specify 2019-2025 temporal window.
   - What's unclear: Whether to use 2019-2021 (matching quality gate) or a wider range like 2015-2021 for richer temporal drift.
   - Recommendation: Use 2015-2021 for temporal drift (7 years of substantial data). 2022 has only 3,293 reviews (truncated) so exclude it. Document the adaptation rationale.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 9.0 |
| Config file | `pytest.ini` (exists: `testpaths = tests`, `addopts = -x -q`) |
| Quick run command | `pytest tests/test_nlp_pipeline.py -x` |
| Full suite command | `pytest -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NLP-01 | Embeddings shape (N, 384) and review_ids alignment | unit | `pytest tests/test_embed.py -x` | Wave 0 |
| NLP-02 | BERTopic produces >=20 topics, outlier rate <50% after reduction | integration | `pytest tests/test_topic_model.py -x` | Wave 0 |
| NLP-03 | Vibe scores vary meaningfully across neighbourhoods (not uniform) | unit | `pytest tests/test_vibe_score.py -x` | Wave 0 |
| NLP-04 | LoRA config valid, merge_and_unload produces loadable model | unit | `pytest tests/test_sentiment.py -x` | Wave 0 |
| NLP-05 | Recency weights computed in log-space, min clamp 1e-6 | unit | `pytest tests/test_vibe_score.py::test_recency_weighting -x` | Wave 0 |
| NLP-06 | Temporal series covers all available years, no NaN values | unit | `pytest tests/test_temporal.py -x` | Wave 0 |
| NLP-07 | FAISS query returns k results in <10ms, plausible similarity | unit | `pytest tests/test_faiss_index.py -x` | Wave 0 |
| NLP-08 | 3-5 quotes per neighbourhood per archetype, <=300 chars | unit | `pytest tests/test_quotes.py -x` | Wave 0 |
| NLP-09 | All artifact files exist and load without error | integration | `pytest tests/test_artifacts.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_nlp_pipeline.py -x` (fast unit tests with mock data)
- **Per wave merge:** `pytest -x -q` (full suite including Phase 1 tests)
- **Phase gate:** Full suite green + manual inspection of vibe scores and topic labels

### Wave 0 Gaps
- [ ] `tests/test_embed.py` -- covers NLP-01 (embeddings shape, dtype, alignment with review_ids)
- [ ] `tests/test_topic_model.py` -- covers NLP-02 (topic count, outlier rate, model save/load)
- [ ] `tests/test_vibe_score.py` -- covers NLP-03, NLP-05 (archetype scoring, recency weighting)
- [ ] `tests/test_sentiment.py` -- covers NLP-04 (LoRA config, merge, 3-class output)
- [ ] `tests/test_temporal.py` -- covers NLP-06 (year bucketing, no NaN, all neighbourhoods)
- [ ] `tests/test_faiss_index.py` -- covers NLP-07 (index build, query latency, result plausibility)
- [ ] `tests/test_quotes.py` -- covers NLP-08 (quote count, length, cosine ranking)
- [ ] `tests/test_artifacts.py` -- covers NLP-09 (all files exist, load without error)
- [ ] `tests/conftest.py` updates -- shared fixtures for mock embeddings, mock DB with review text, mock BERTopic model

**Testing strategy note:** Most tests should use small synthetic data (e.g., 100 fake reviews, 3 neighbourhoods) to keep test execution under 30 seconds. Integration tests that run actual ML models should be marked with `@pytest.mark.slow` and excluded from the quick run.

## Sources

### Primary (HIGH confidence)
- [BERTopic outlier reduction docs](https://maartengr.github.io/BERTopic/getting_started/outlier_reduction/outlier_reduction.html) -- all 4 strategies, parameters, chaining
- [BERTopic best practices](https://maartengr.github.io/BERTopic/getting_started/best_practices/best_practices.html) -- pre-computed embeddings, HDBSCAN tuning, reproducibility, safetensors
- [BERTopic serialization docs](https://maartengr.github.io/BERTopic/getting_started/serialization/serialization.html) -- safetensors save/load, what is/isn't saved
- [PEFT LoRA docs](https://huggingface.co/docs/peft/main/en/developer_guides/lora) -- LoraConfig, merge_and_unload, task types
- [PEFT sequence classification example](https://github.com/huggingface/peft/blob/main/examples/sequence_classification/LoRA.ipynb) -- DistilBERT + LoRA workflow
- [FAISS cosine similarity pattern](https://github.com/facebookresearch/faiss/issues/95) -- normalize_L2 + IndexFlatIP = cosine similarity
- pip index versions (verified 2026-03-17): sentence-transformers 5.3.0, bertopic 0.17.4, peft 0.18.1, faiss-cpu 1.13.2, hdbscan 0.8.41
- Local environment: torch 2.10.0, transformers 5.3.0 installed; CUDA not available

### Secondary (MEDIUM confidence)
- [BERTopic parameter tuning](https://maartengr.github.io/BERTopic/getting_started/parameter%20tuning/parametertuning.html) -- UMAP n_components, HDBSCAN min_cluster_size guidance
- [HuggingFace text classification guide](https://huggingface.co/docs/transformers/tasks/sequence_classification) -- Trainer API, TrainingArguments

### Tertiary (LOW confidence)
- GPU availability for training in WSL2 -- could not verify; assumed CPU-only as fallback
- `all-MiniLM-L6-v2` performance on Yelp-style short reviews -- no direct benchmark found; model is general-purpose and widely used for similar tasks

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions verified via pip index, locally installed
- Architecture: HIGH -- patterns drawn from official docs and established project patterns
- Pitfalls: HIGH -- BERTopic outlier issue well-documented; memory/temporal issues verified against actual DB data
- Data reality: HIGH -- queried actual SQLite database (1.1M reviews, 157 neighbourhoods, 2005-2022 range)

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable libraries, unlikely to change within 30 days)

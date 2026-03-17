# NLP Pipeline Technical Decisions

This document records the key technical choices made for the NLP pipeline, with rationale for each. Intended as a reference for portfolio discussions and interviews.

## BERTopic over LDA

**Choice:** BERTopic with HDBSCAN clustering on sentence-transformer embeddings.
**Alternative:** Latent Dirichlet Allocation (LDA) via gensim.

**Rationale:**
- LDA uses bag-of-words representations, losing word order and semantic meaning. "Great food" and "food great" are identical to LDA.
- BERTopic leverages contextual embeddings from a pre-trained transformer, capturing semantic similarity between reviews even when they use different vocabulary.
- HDBSCAN discovers the natural number of topics (no need to guess k), unlike LDA which requires a fixed topic count.
- BERTopic's c-TF-IDF topic representations are more interpretable than LDA word distributions.
- The main trade-off is BERTopic's higher outlier rate on short text (40-75% without tuning), mitigated by `reduce_outliers()` with c-TF-IDF and embeddings strategies.

## sentence-transformers over word2vec

**Choice:** `all-MiniLM-L6-v2` sentence-transformer (384-dimensional).
**Alternative:** word2vec or GloVe with averaging.

**Rationale:**
- Word2vec/GloVe produce static word embeddings — "bank" has the same vector whether it means a river bank or a financial institution.
- Sentence-transformers produce contextual embeddings for entire sentences, capturing meaning that depends on surrounding words.
- `all-MiniLM-L6-v2` is fast (22M parameters), well-suited for short review text, and produces high-quality embeddings without fine-tuning.
- The 384-dimensional output balances expressiveness with computational efficiency for downstream cosine similarity.

## LoRA fine-tuning over VADER

**Choice:** DistilBERT + LoRA (rank=16, alpha=32) fine-tuned on Yelp reviews for 3-class sentiment.
**Alternative:** VADER (rule-based sentiment lexicon).

**Rationale:**
- VADER is a rule-based system with no domain adaptation — it misclassifies review-specific language (e.g., "sick beats" as negative).
- LoRA fine-tuning adapts a pre-trained language model to the Yelp review domain with minimal additional parameters (~0.5% of base model).
- 3-class output (negative/neutral/positive) maps naturally to star ratings: 1-2 stars negative, 3 stars neutral, 4-5 stars positive.
- LoRA demonstrates modern ML techniques (parameter-efficient fine-tuning) relevant to industry practice.
- The merged model (via `merge_and_unload()`) is a standalone model with no runtime LoRA dependency.

## FAISS over brute-force numpy

**Choice:** FAISS `IndexFlatIP` with L2-normalized vectors for cosine similarity.
**Alternative:** Manual numpy dot product / distance matrix.

**Rationale:**
- FAISS is the industry-standard library for similarity search, developed by Meta AI Research.
- Even for our small dataset (157 neighbourhoods, 6 dimensions), FAISS demonstrates familiarity with production ML infrastructure.
- `IndexFlatIP` on L2-normalized vectors gives exact cosine similarity — no approximation error.
- The FAISS binary index format is compact and loads instantly at backend startup.
- Using FAISS positions the project for scaling (if more neighbourhoods or dimensions are added later).

## Philadelphia pivot

**Choice:** Philadelphia, PA as the target city with 157 neighbourhoods.
**Alternative:** Original plan targeted New York City.

**Rationale:**
- Yelp Open Dataset NYC coverage was <500 businesses — insufficient for meaningful topic modeling.
- Philadelphia has ~14,568 businesses and ~1.1M reviews in the Yelp Academic Dataset.
- 157 neighbourhoods from OpenDataPhilly ArcGIS FeatureServer provide well-defined geographic boundaries.
- Neighbourhood boundaries use `NEIGHBORHOOD_NUMBER` (ID) and `NEIGHBORHOOD_NAME` fields.
- Decision made during Phase 1 data foundation; all downstream phases retargeted accordingly.

## Temporal range: actual data years

**Choice:** Use actual Yelp data years (2005-2022, with meaningful coverage 2015-2021) for temporal analysis.
**Alternative:** Original plan specified 2019-2025.

**Rationale:**
- The Yelp Academic Dataset was last refreshed in early 2022. No data exists for 2023-2025.
- The 2019-2025 range was aspirational, designed for NYC. After the Philadelphia pivot, we use the actual available data range.
- Years 2015-2021 have substantial review counts for robust temporal drift analysis.
- 2022 has only ~3,293 reviews (truncated January release), excluded to avoid misleading trends.
- This is transparently documented rather than padding with empty year buckets.

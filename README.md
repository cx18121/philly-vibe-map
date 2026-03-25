# philly vibe map
An interactive map of Philadelphia neighbourhoods, where each colour represents a "vibe" derived from ~1.1 million Yelp reviews. The map lets you go through time to watch neighbourhoods change character.

**Live:** [philly-vibe-map.vercel.app](https://philly-vibe-map.vercel.app)

---

## What it does

Pick a neighbourhood on the map. You get:

- Its dominant vibe category (one of six archetypes: *Nightlife*, *Family*, *Arts*, *Food*, *Outdoor*, *Shopping*)
- A sentiment breakdown and representative quotes pulled straight from Yelp reviews
- A time slider — drag it and watch the colours shift as the neighbourhood changes year over year
- A "similar neighbourhoods" list powered by cosine similarity over vibe vectors

---

## How it works

There are three distinct layers:

### 1. NLP Pipeline (`/pipeline`)

Runs once offline to produce pre-computed artifacts the backend serves at query time.

- **Embeddings:** Every review is encoded with `all-MiniLM-L6-v2` (sentence-transformers). Contextual embeddings beat bag-of-words for short, colloquial review text.
- **Topic modelling:** BERTopic + HDBSCAN discovers topic clusters without you specifying how many. LDA requires a fixed topic count and loses word order — BERTopic doesn't. The main challenge was the outlier rate on short text (HDBSCAN clusters aggressively); `reduce_outliers()` with c-TF-IDF + embedding strategies brings it down to acceptable levels.
- **Sentiment:** DistilBERT fine-tuned with LoRA (rank=16, α=32) on Yelp data for 3-class classification. VADER misreads domain-specific language ("sick", "insane", "dead") — a fine-tuned model doesn't.
- **Vibe scoring:** Each neighbourhood × year bucket gets a 6-dimensional vibe vector. Exponential decay is only used for the "current vibe" score, not for historical buckets.
- **Similarity index:** FAISS `IndexFlatIP` on L2-normalized vectors. Exact cosine similarity, loads in milliseconds.

### 2. Backend (`/backend`)

FastAPI + SQLite. Serves pre-computed artifacts — no ML models loaded at runtime. Containerised with Docker, deployed on Render.

### 3. Frontend (`/frontend`)

React 19 + MapLibre GL JS + Framer Motion + Zustand.

---

## Data

Yelp Open Dataset (Philadelphia). ~14,568 businesses, ~1.1M reviews. The dataset has real coverage from 2015–2021; 

Neighbourhood boundaries from OpenDataPhilly (157 neighbourhoods).

---

## Tech decisions worth discussing

| Decision | Why |
|---|---|
| BERTopic over LDA | Contextual embeddings, no fixed k, better short-text handling |
| sentence-transformers over word2vec | Context-aware, no "bank" ambiguity problem |
| LoRA fine-tuning over VADER | Domain adaptation with ~0.5% of base model parameters |
| FAISS over numpy | Industry-standard similarity search; trivial to scale |

---

## Running locally

**Backend:**
```bash
pip install -r requirements-api.txt
uvicorn backend.app:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Full pipeline** (needs the Yelp dataset files in `/data`):
```bash
pip install -r requirements-nlp.txt
python run_pipeline.py
```

---

## Stack

- **Pipeline:** Python 3.12, sentence-transformers, BERTopic, PEFT/LoRA, FAISS
- **Backend:** FastAPI, SQLite, Docker → Render
- **Frontend:** React 19, TypeScript, MapLibre GL JS, Framer Motion, Zustand → Vercel

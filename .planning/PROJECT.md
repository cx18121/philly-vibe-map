# Neighbourhood Vibe Mapper — New York City

## What This Is

A web app that ingests Google Places and Yelp reviews for businesses across Manhattan and Brooklyn, runs a deep NLP pipeline to extract neighbourhood "personality" signals, and renders the results as a stunning interactive map. The technical depth of the pipeline (sentence-transformer embeddings, BERTopic topic modelling, FAISS nearest-neighbour search, temporal drift analysis) is as important as the visual output — this is designed to be a serious resume/portfolio artefact as well as a live public product.

## Core Value

An interactive map where anyone can feel the character of a New York City neighbourhood through its reviews — and watch how that character has shifted year by year from 2019 to 2025.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Data Collection**
- [ ] Collect 50k+ reviews from Google Places API across 30 neighbourhoods in Manhattan and Brooklyn
- [ ] Supplement coverage gaps with Yelp Fusion API reviews
- [ ] Deduplicate and entity-resolve businesses appearing on both platforms (name + lat/lng proximity match)
- [ ] Store raw reviews with timestamps for temporal analysis
- [ ] Fetch official neighbourhood boundary GeoJSON from NYC Open Data portal
- [ ] Cover review window: 2019–2025

**NLP Pipeline**
- [ ] Embed all reviews using a sentence-transformer model (no bag-of-words or LDA)
- [ ] Run BERTopic for unsupervised topic discovery per neighbourhood
- [ ] Score each neighbourhood against 6 vibe archetypes (artsy, foodie, nightlife, family, upscale, cultural) via cosine similarity between topic embeddings and archetype seed phrases
- [ ] Domain-adapt sentiment classifier on review corpora (Yelp public dataset) rather than using a generic off-the-shelf classifier
- [ ] Weight reviews by recency using exponential decay on timestamps
- [ ] Temporal drift analysis: bucket reviews by year (2019–2025), run full pipeline per bucket, track how each neighbourhood's vibe vector shifts over time
- [ ] Serve embeddings and nearest-neighbour queries via FAISS

**Backend**
- [ ] Cache all NLP pipeline results — never recompute on a live request
- [ ] Expose endpoint: enriched GeoJSON with vibe scores per neighbourhood
- [ ] Expose endpoint: per-neighbourhood topic breakdown with representative review quotes
- [ ] Expose endpoint: temporal drift time series (vibe vectors by year)
- [ ] Expose endpoint: FAISS nearest-neighbour query (find neighbourhoods similar to a given one)

**Frontend / Visualization**
- [ ] Dark map basemap with semi-transparent, richly coloured neighbourhood fills that glow by dominant vibe
- [ ] Smooth animated transitions when switching between vibes or selecting neighbourhoods
- [ ] Sidebar with beautiful typography, animated topic bars, and vibe pills with sentiment scores
- [ ] Time slider animating neighbourhood vibe shifts year by year from 2019 to 2025
- [ ] Hover effects, pulsing highlights, and fluid interactions throughout
- [ ] Visual quality that stops scrollers — feels like interactive data art, not a dashboard

**Deployment**
- [ ] Deployed to a public URL accessible without login
- [ ] Architecture supports static pre-computed artifacts with hooks for future data refresh

### Out of Scope

- User accounts / authentication — read-only public app, no login needed
- Real-time review ingestion — static batch pipeline is correct for v1
- Boroughs beyond Manhattan and Brooklyn — Queens/Bronx/Staten Island deferred
- Mobile-native app — web-first, responsive is sufficient
- Review submission or crowdsourcing — consumption only

## Context

- **Resume priority**: The NLP pipeline decisions (why BERTopic over LDA, why sentence-transformers, why FAISS, exponential decay weighting) must be technically defensible in an interview. Architecture choices should be explainable and non-trivial.
- **API setup**: Google Places and Yelp Fusion keys need to be obtained before data collection can begin. Google's $200 free monthly credit is the budget ceiling — batch strategy must stay within it.
- **Compute**: NLP pipeline (embeddings, BERTopic, FAISS indexing) runs locally on GPU. Results are pre-computed and committed/uploaded as static artifacts so the live app never re-runs the pipeline.
- **Data freshness**: Static first (one-time batch for v1), with architecture hooks left open for periodic refresh in the future.
- **Temporal window**: 2019–2025 (extended from original 2019–2024 spec).

## Constraints

- **Budget**: Google Places API must stay within $200/month free credit — requires batching strategy and careful quota management
- **Compute**: Pipeline runs on local GPU; no cloud GPU budget assumed for pipeline execution
- **Scope**: Manhattan + Brooklyn only for v1 — 30 neighbourhoods
- **Data**: Reviews from 2019–2025 only; older reviews excluded from temporal analysis
- **Pipeline**: All NLP results must be pre-computed; zero live ML inference on user requests

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| sentence-transformers over bag-of-words/LDA | Semantically richer embeddings; far more defensible in technical interviews; captures nuance that word-count models miss | — Pending |
| BERTopic for topic discovery | Unsupervised, no predefined categories; surfaces genuine neighbourhood-specific themes; built on top of transformer embeddings for coherence | — Pending |
| FAISS for nearest-neighbour | Production-grade ANN library; avoids O(n²) brute-force cosine; demonstrates systems thinking beyond pure ML | — Pending |
| Domain adaptation for sentiment | Generic classifiers (VADER, TextBlob) perform poorly on review slang; Yelp public dataset enables fine-tuning without manual labelling | — Pending |
| Exponential decay on timestamps | Recency-weighted signals reflect current neighbourhood character; older reviews discounted without being discarded | — Pending |
| Static pre-computed artifacts | Never recompute on live request — instant responses, zero inference cost at runtime, correct for a portfolio/public app | — Pending |
| Extend temporal window to 2025 | Captures post-pandemic recovery and more recent neighbourhood shifts | — Pending |

---
*Last updated: 2026-03-16 after initialization*

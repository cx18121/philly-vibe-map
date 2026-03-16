# Phase 1: Data Foundation - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Collect and validate a review corpus from the Yelp Open Dataset covering all Manhattan and Brooklyn neighbourhoods, assign reviews to neighbourhoods via spatial join against curated NTA boundaries, store in SQLite, and produce a data quality report confirming temporal coverage. This phase produces the review corpus and boundary GeoJSON that the NLP pipeline (Phase 2) will consume.

</domain>

<decisions>
## Implementation Decisions

### Data sourcing
- **Primary source: Yelp Open Dataset only** — free academic dataset (~6.9M reviews, covers to ~mid-2024). No Google Places API (free credit gone as of March 2025), no Yelp Fusion API.
- Cross-platform deduplication (DATA-02) is dropped — single-source dataset has no cross-platform duplicates.
- **Coverage validation is the first pipeline step**: count NYC reviews in the dataset before building the full schema. If NYC coverage is thin, catch it early.
- **Flexible review target**: if the Yelp Open Dataset has fewer than 50k NYC reviews, lower the target to whatever is available rather than supplementing with a paid API. 50k was always an estimate.

### Neighbourhood definition
- **Use NTA (Neighbourhood Tabulation Areas) geometry** from NYC Open Data (2020 NTAs) as the authoritative boundary source — official, clean GeoJSON, WGS84.
- **Full Manhattan + Brooklyn coverage**: the curated neighbourhood list must tile all of Manhattan and Brooklyn with no gaps. Use all NTAs from both boroughs — no hard limit on count, however many is needed for complete coverage.
- **Curate recognisable names**: where NTA names are awkward merges (e.g., "SoHo-TriBeCa-Civic Center-Little Italy"), the planner will propose clean community-recognised names. The planner produces the specific neighbourhood list as part of Phase 1 planning.

### Business-to-neighbourhood assignment
- **Point-in-polygon only** — use the business lat/lng from the Yelp dataset to determine which NTA polygon it falls inside. Do not trust Yelp's neighbourhood label field (user-generated, inconsistent).
- **Implementation**: GeoPandas `sjoin()` — vectorised spatial join with R-tree index. Single call over all NYC businesses, not a loop.
- **Boundary ties**: if a point falls exactly on a boundary, assign to whichever polygon the point-in-polygon algorithm resolves to first (deterministic, not duplicated).
- Since all of Manhattan and Brooklyn is covered, no businesses are discarded as "outside scope."

### Collection resilience
- The Yelp Open Dataset is a **static file download** (not API calls), so the failure modes are different from a live scrape.
- **Streaming parse**: the Yelp reviews file is newline-delimited JSON (~8.65 GB uncompressed). Parse line-by-line — never load the full file into memory.
- **Idempotent writes**: use `INSERT OR IGNORE` into SQLite so re-runs don't duplicate records.
- **Good progress logging** throughout — no complex checkpoint/resume system needed for a static file parse.

### Claude's Discretion
- Exact SQLite schema column types and indices (beyond required fields in DATA-03)
- How to handle Yelp records with missing lat/lng (log and skip vs. attempt geocoding)
- Progress logging format and granularity

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Neighbourhood boundaries
- NYC Open Data 2020 NTAs: `https://data.cityofnewyork.us/City-Government/2020-Neighborhood-Tabulation-Areas-NTAs-/9nt8-h7nd` — Official NTA boundary GeoJSON for Manhattan and Brooklyn; download and commit as a project artifact

### Review data
- Yelp Open Dataset: `https://business.yelp.com/data/resources/open-dataset/` — Source for all reviews; newline-delimited JSON, ~8.65 GB uncompressed. Review file is `yelp_academic_dataset_review.json`, business file is `yelp_academic_dataset_business.json`

### Project requirements
- `.planning/REQUIREMENTS.md` — DATA-01 through DATA-06 define the acceptance criteria for this phase (note: DATA-02 cross-platform deduplication is superseded by the Yelp-only decision above)
- `.planning/PROJECT.md` — Budget constraints (no API spend), compute context, resume/portfolio priorities

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — codebase is empty at the start of Phase 1.

### Established Patterns
- None established yet. Phase 1 sets the patterns downstream phases will follow.

### Integration Points
- SQLite database produced here is the direct input to Phase 2 (NLP pipeline)
- NTA GeoJSON produced here feeds Phase 2 (neighbourhood assignment), Phase 3 (API GeoJSON response), and Phase 4 (map rendering)
- Data quality report (DATA-05) is a gate: Phase 2 should not begin until report confirms acceptable coverage

</code_context>

<specifics>
## Specific Ideas

- Neighbourhood boundaries should feel right to New Yorkers — NTA geometry is used but names should be curated to match community-recognised names (not raw NTA merged labels)
- Complete Manhattan + Brooklyn tiling: every sq metre of both boroughs should fall inside exactly one neighbourhood polygon

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-data-foundation*
*Context gathered: 2026-03-16*

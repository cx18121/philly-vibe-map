# Dataset Coverage Decision — Plan 01-01

**Decision recorded:** 2026-03-16
**Checkpoint type:** checkpoint:decision (blocking gate)

## Probe Results

The Yelp Open Dataset does NOT cover New York City. The Manhattan+Brooklyn bounding box
(`NYC_BBOX = box(-74.05, 40.57, -73.70, 40.92)`) returned fewer than 500 matching businesses,
confirming the research finding that the dataset covers only 8 metropolitan areas (Atlanta,
Austin, Boston, Boulder, Columbus, Orlando, Portland, Vancouver).

## Decision Selected

**Option C — Pivot to Philadelphia, PA**

Philadelphia is the strongest Yelp-covered city by business count in the dataset:
- **Philadelphia businesses in dataset:** ~14,568
- **Threshold met:** > 10,000 (adequate coverage — proceed normally)

## Rationale

Philadelphia provides:
1. Highest single-city coverage in the Yelp dataset
2. Rich neighbourhood diversity (Center City, Fishtown, South Philly, West Philly, etc.)
3. Same pipeline architecture — no structural changes needed
4. Strong portfolio piece: "Philadelphia Neighbourhood Vibe Mapper"

## Impact on Subsequent Plans

All plans 01-02 through 01-05 must target Philadelphia instead of NYC:

| Plan | Change Required |
|------|----------------|
| 01-02 | NTA boundary source: use Philadelphia neighbourhood GeoJSON (OpenDataPhilly or Census TIGER) instead of NYC Socrata NTA |
| 01-03 | SQLite ingestion: filter `city = 'Philadelphia'` instead of spatial join to NYC_BBOX |
| 01-04 | Review streaming: no city filter change needed (business-join handles scoping) |
| 01-05 | Quality report: Philadelphia neighbourhoods replace NYC NTAs; READY FOR PHASE 2 verdict targets Philadelphia coverage |

## Boundary Source (for 01-02 planner)

Replace NYC NTA (Socrata) with one of:
- **OpenDataPhilly** neighbourhood polygons (recommended — well-maintained, WGS84)
  URL: https://opendata.arcgis.com/datasets/neighborhood_boundaries.geojson
- **Census TIGER** tract-level aggregation as fallback

## Probe Script Status

`scripts/00_probe_coverage.py` remains valid infrastructure. The NYC_BBOX constant will
be replaced in 01-03 with a Philadelphia bounding box or city-label filter.

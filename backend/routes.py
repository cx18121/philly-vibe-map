"""Data endpoint routes for the Neighbourhood Vibe Mapper API."""
from __future__ import annotations

import numpy as np
import faiss
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from backend.schemas import NeighbourhoodDetail, SentimentSummary, SimilarNeighbourhood, TopicEntry

router = APIRouter()

ARCHETYPE_ORDER = ["artsy", "foodie", "nightlife", "family", "upscale", "cultural"]


@router.get("/neighbourhoods")
def get_neighbourhoods(request: Request) -> Response:
    """Return all neighbourhoods as a GeoJSON FeatureCollection."""
    return Response(
        content=request.app.state.geojson_bytes,
        media_type="application/geo+json",
    )


@router.get("/neighbourhoods/{nid}", response_model=NeighbourhoodDetail)
def get_neighbourhood_detail(nid: str, request: Request) -> NeighbourhoodDetail:
    """Return vibe detail for a single neighbourhood."""
    nid = nid.zfill(3)
    if nid not in request.app.state.valid_nids:
        raise HTTPException(status_code=404, detail=f"Neighbourhood {nid} not found")

    vibe_scores = request.app.state.vibe_scores[nid]
    dominant_vibe = max(vibe_scores, key=vibe_scores.get)

    raw_topics = request.app.state.topics.get(nid, [])
    topics = [TopicEntry(**t) for t in raw_topics]

    raw_sentiment = request.app.state.neighbourhood_sentiment.get(nid)
    sentiment = SentimentSummary(**raw_sentiment) if raw_sentiment else None

    return NeighbourhoodDetail(
        neighbourhood_id=nid,
        neighbourhood_name=request.app.state.nid_to_name.get(nid),
        vibe_scores=vibe_scores,
        dominant_vibe=dominant_vibe,
        dominant_vibe_score=vibe_scores[dominant_vibe],
        topics=topics,
        quotes=request.app.state.quotes.get(nid, {}),
        review_count=request.app.state.review_counts.get(nid, 0),
        sentiment=sentiment,
    )


@router.get("/temporal")
def get_temporal(request: Request) -> dict:
    """Return temporal vibe series for all neighbourhoods."""
    return request.app.state.temporal


@router.get("/similar", response_model=list[SimilarNeighbourhood])
def get_similar(
    request: Request,
    id: str = Query(..., description="Neighbourhood ID"),
    k: int = Query(default=5, ge=1, description="Number of similar neighbours"),
) -> list[SimilarNeighbourhood]:
    """Return k most similar neighbourhoods by vibe vector cosine similarity."""
    nid = id.zfill(3)
    if nid not in request.app.state.valid_nids:
        raise HTTPException(status_code=404, detail=f"Neighbourhood {nid} not found")

    max_k = len(request.app.state.valid_nids) - 1
    k = min(k, max_k)

    # Build query vector in archetype order, normalise for cosine similarity
    scores = request.app.state.vibe_scores[nid]
    query = np.array(
        [[scores[a] for a in ARCHETYPE_ORDER]], dtype=np.float32
    )
    faiss.normalize_L2(query)

    # Search k+1 to account for self-match
    distances, indices = request.app.state.faiss_index.search(query, k + 1)

    results: list[SimilarNeighbourhood] = []
    for dist, idx in zip(distances[0], indices[0]):
        matched_nid = request.app.state.faiss_id_map[str(int(idx))]
        if matched_nid == nid:
            continue
        results.append(
            SimilarNeighbourhood(
                neighbourhood_id=matched_nid,
                similarity=round(float(dist), 6),
            )
        )
        if len(results) >= k:
            break

    return results

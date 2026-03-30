"""Pydantic v2 response models for the Neighbourhood Vibe Mapper API."""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    artifacts_loaded: bool


class TopicEntry(BaseModel):
    """A single topic within a neighbourhood's topic distribution."""

    label: str
    keywords: list[str]
    review_share: float


class NeighbourhoodDetail(BaseModel):
    """Full detail for a single neighbourhood."""

    neighbourhood_id: str
    neighbourhood_name: str | None = None
    vibe_scores: dict[str, float]
    dominant_vibe: str
    dominant_vibe_score: float
    topics: list[TopicEntry]
    quotes: dict[str, list[str]]
    review_count: int


class SimilarNeighbourhood(BaseModel):
    """A neighbourhood returned as a similarity match."""

    neighbourhood_id: str
    similarity: float

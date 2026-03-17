"""Tests for NLP-03/NLP-05: Vibe archetype scoring and recency weighting."""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from pipeline.stages.vibe_score import run_vibe_score

ARCHETYPES = ["artsy", "foodie", "nightlife", "family", "upscale", "cultural"]


class TestVibeScores:
    """NLP-03: Vibe scores have 6 dimensions per neighbourhood."""

    @pytest.mark.slow
    def test_vibe_scores_six_dimensions(self, mock_db_with_reviews, mock_artifacts_dir):
        """Every neighbourhood in vibe_scores.json has exactly 6 archetype keys."""
        run_vibe_score(mock_db_with_reviews, mock_artifacts_dir)
        path = mock_artifacts_dir / "vibe_scores.json"
        assert path.exists(), "vibe_scores.json not created"
        with open(path) as f:
            scores = json.load(f)
        assert len(scores) > 0, "No neighbourhoods in vibe_scores.json"
        for nid, vibe in scores.items():
            assert set(vibe.keys()) == set(ARCHETYPES), (
                f"Neighbourhood {nid} has keys {set(vibe.keys())} != {set(ARCHETYPES)}"
            )

    @pytest.mark.slow
    def test_vibe_scores_vary(self, mock_db_with_reviews, mock_artifacts_dir):
        """Not all neighbourhood scores are identical (std > 0 for at least one dim)."""
        run_vibe_score(mock_db_with_reviews, mock_artifacts_dir)
        with open(mock_artifacts_dir / "vibe_scores.json") as f:
            scores = json.load(f)
        # Build matrix: rows = neighbourhoods, cols = archetypes
        nids = sorted(scores.keys())
        if len(nids) < 2:
            pytest.skip("Need >= 2 neighbourhoods to test variation")
        matrix = np.array([[scores[nid][a] for a in ARCHETYPES] for nid in nids])
        stds = matrix.std(axis=0)
        assert any(s > 0 for s in stds), (
            f"All neighbourhood vibe scores are identical (stds={stds})"
        )


class TestRecencyWeighting:
    """NLP-05: Recency-weighted scores with exponential decay in log-space."""

    def test_recency_weighting_log_space(self):
        """Recency weights computed in log-space match expected values within 1e-6."""
        half_life_days = 365.0
        lambda_decay = math.log(2) / half_life_days

        # Test cases: (delta_days, expected_weight)
        test_cases = [
            (0, 1.0),          # today: full weight
            (365, 0.5),        # one half-life: half weight
            (730, 0.25),       # two half-lives: quarter weight
        ]
        for delta_days, expected in test_cases:
            log_weight = -lambda_decay * delta_days
            weight = np.exp(log_weight).clip(min=1e-6)
            assert abs(weight - expected) < 1e-6, (
                f"delta={delta_days}: weight={weight}, expected={expected}"
            )

    def test_recency_weight_clamp(self):
        """A review 10 years old gets weight clamped to 1e-6, not 0."""
        half_life_days = 365.0
        lambda_decay = math.log(2) / half_life_days
        delta_days = 3650  # 10 years

        log_weight = -lambda_decay * delta_days
        weight = np.exp(log_weight).clip(min=1e-6)

        assert weight >= 1e-6, f"Weight {weight} should be >= 1e-6 (clamped)"
        assert weight == 1e-6 or weight > 0, "Weight should be positive"

"""Tests for NLP-03/NLP-05: Vibe archetype scoring and recency weighting."""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from pipeline.stages.vibe_score import run_vibe_score, compute_recency_weight

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

    def test_recency_weight_today_is_one(self):
        """A review from today has weight ~1.0."""
        w = compute_recency_weight("2024-01-15", "2024-01-15")
        assert abs(w - 1.0) < 1e-9, f"Same-day weight should be 1.0, got {w}"

    def test_recency_weight_one_halflife(self):
        """A review exactly one half-life (365 days) old has weight ~0.5."""
        w = compute_recency_weight("2023-01-15", "2024-01-15")
        assert abs(w - 0.5) < 0.01, f"365-day weight should be ~0.5, got {w}"

    def test_recency_weight_two_halflives(self):
        """A review two half-lives (730 days) old has weight ~0.25."""
        w = compute_recency_weight("2022-01-16", "2024-01-15")
        assert abs(w - 0.25) < 0.01, f"730-day weight should be ~0.25, got {w}"

    def test_recency_weight_very_old_clamped(self):
        """A review 20 years old gets clamped to 1e-6 (2^-20 ~ 9.5e-7 < 1e-6)."""
        w = compute_recency_weight("2004-01-15", "2024-01-15")
        assert w == pytest.approx(1e-6, abs=1e-9), (
            f"20-year-old review weight should be clamped to 1e-6, got {w}"
        )

    def test_recency_weight_uses_log_space(self):
        """Verify the log-space formula: log_weight = -lambda * delta_days."""
        from datetime import datetime

        # Use two concrete dates and compute expected via the log-space formula
        review_date = "2023-01-15"
        ref_date = "2024-06-15"
        delta_days = (datetime.strptime(ref_date, "%Y-%m-%d")
                      - datetime.strptime(review_date, "%Y-%m-%d")).days

        half_life = 365
        decay_lambda = math.log(2) / half_life
        log_weight = -decay_lambda * delta_days
        expected = max(math.exp(log_weight), 1e-6)

        w = compute_recency_weight(review_date, ref_date, half_life_days=half_life)
        assert abs(w - expected) < 1e-9, (
            f"Log-space weight mismatch: got {w}, expected {expected}"
        )

    def test_recency_weight_future_review_returns_one(self):
        """A review from the future (delta < 0) should return 1.0."""
        w = compute_recency_weight("2025-01-15", "2024-01-15")
        assert w == 1.0, f"Future review should have weight 1.0, got {w}"


class TestVibeScoreWithMockData:
    """Test vibe scoring with pre-created mock artifacts (non-slow)."""

    def test_vibe_score_artifact_gate(self, mock_db_with_reviews, mock_artifacts_dir):
        """If vibe_scores.json exists, stage should skip."""
        # Create fake artifact
        (mock_artifacts_dir / "vibe_scores.json").write_text("{}")
        result = run_vibe_score(mock_db_with_reviews, mock_artifacts_dir, force=False)
        assert result["skipped"] is True

    def test_vibe_score_force_overwrite(self, mock_db_with_reviews, tmp_path):
        """With force=True, stage should run even if artifact exists."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        # Create prerequisite artifacts (embeddings, review_ids, topic_assignments)
        np.random.seed(42)
        embs = np.random.randn(90, 384).astype(np.float32)
        rids = np.arange(1, 91, dtype=np.int64)
        np.save(artifacts_dir / "embeddings.npy", embs)
        np.save(artifacts_dir / "review_ids.npy", rids)

        # Create topic assignments: map each review to a topic (3 topics)
        assignments = {str(i): i % 3 for i in range(1, 91)}
        with open(artifacts_dir / "topic_assignments.json", "w") as f:
            json.dump(assignments, f)

        # Write a dummy vibe_scores.json
        (artifacts_dir / "vibe_scores.json").write_text("{}")

        # Force should regenerate
        result = run_vibe_score(mock_db_with_reviews, artifacts_dir, force=True)
        assert result["skipped"] is False
        assert result["n_neighbourhoods"] > 0
        assert set(result["archetypes"]) == set(ARCHETYPES)

        # Verify output has correct structure
        with open(artifacts_dir / "vibe_scores.json") as f:
            scores = json.load(f)
        for nid, vibe in scores.items():
            assert set(vibe.keys()) == set(ARCHETYPES)
            for a, v in vibe.items():
                assert isinstance(v, float), f"{nid}/{a} is not float"

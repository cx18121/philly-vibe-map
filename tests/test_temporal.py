"""Tests for NLP-06: Temporal drift — year-bucketed vibe scoring."""
from __future__ import annotations

import json
import math
import sqlite3

import pytest

from pipeline.stages.temporal import run_temporal

ARCHETYPES = ["artsy", "foodie", "nightlife", "family", "upscale", "cultural"]


class TestTemporalSeries:
    """NLP-06: Temporal series structure and correctness."""

    @pytest.mark.slow
    def test_temporal_series_structure(self, mock_db_with_reviews, mock_artifacts_dir):
        """temporal_series.json has neighbourhood_id -> year -> 6 archetype scores."""
        run_temporal(mock_db_with_reviews, mock_artifacts_dir)
        path = mock_artifacts_dir / "temporal_series.json"
        assert path.exists(), "temporal_series.json not created"
        with open(path) as f:
            series = json.load(f)
        assert len(series) > 0, "No neighbourhoods in temporal series"
        for nid, years in series.items():
            assert isinstance(years, dict), f"Neighbourhood {nid} value is not a dict"
            for year, scores in years.items():
                assert isinstance(scores, dict), (
                    f"Neighbourhood {nid}, year {year} value is not a dict"
                )
                assert set(scores.keys()) == set(ARCHETYPES), (
                    f"Neighbourhood {nid}, year {year} has keys "
                    f"{set(scores.keys())} != {set(ARCHETYPES)}"
                )

    @pytest.mark.slow
    def test_temporal_no_nan(self, mock_db_with_reviews, mock_artifacts_dir):
        """No NaN values in any temporal score."""
        run_temporal(mock_db_with_reviews, mock_artifacts_dir)
        with open(mock_artifacts_dir / "temporal_series.json") as f:
            series = json.load(f)
        for nid, years in series.items():
            for year, scores in years.items():
                for archetype, value in scores.items():
                    assert not math.isnan(value), (
                        f"NaN found at {nid}/{year}/{archetype}"
                    )

    @pytest.mark.slow
    def test_temporal_all_neighbourhoods(self, mock_db_with_reviews, mock_artifacts_dir):
        """Every neighbourhood_id from DB appears in temporal series."""
        run_temporal(mock_db_with_reviews, mock_artifacts_dir)
        with open(mock_artifacts_dir / "temporal_series.json") as f:
            series = json.load(f)

        # Get neighbourhood IDs from the DB
        conn = sqlite3.connect(mock_db_with_reviews)
        db_nids = {
            row[0] for row in conn.execute(
                "SELECT DISTINCT neighbourhood_id FROM businesses "
                "WHERE neighbourhood_id IS NOT NULL"
            )
        }
        conn.close()

        series_nids = set(series.keys())
        missing = db_nids - series_nids
        assert not missing, f"Neighbourhoods missing from temporal series: {missing}"

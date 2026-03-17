"""Tests for NLP-08: Representative quotes per neighbourhood per archetype."""
from __future__ import annotations

import json

import pytest

from pipeline.stages.export import run_export

ARCHETYPES = ["artsy", "foodie", "nightlife", "family", "upscale", "cultural"]


class TestRepresentativeQuotes:
    """NLP-08: 3-5 quotes per neighbourhood per archetype, <= 300 chars."""

    def test_quotes_per_neighbourhood(self, mock_export_setup):
        """Each neighbourhood has 3-5 quotes per archetype."""
        db_path, artifacts_dir, geojson_path = mock_export_setup
        run_export(db_path, artifacts_dir, geojson_path=geojson_path)

        path = artifacts_dir / "representative_quotes.json"
        assert path.exists(), "representative_quotes.json not created"
        with open(path) as f:
            quotes = json.load(f)

        assert len(quotes) > 0, "No neighbourhoods in quotes file"
        for nid, archetypes in quotes.items():
            for archetype, quote_list in archetypes.items():
                assert 3 <= len(quote_list) <= 5, (
                    f"Neighbourhood {nid}, archetype {archetype}: "
                    f"expected 3-5 quotes, got {len(quote_list)}"
                )

    def test_quote_max_length(self, mock_export_setup):
        """Every quote is <= 300 characters."""
        db_path, artifacts_dir, geojson_path = mock_export_setup
        run_export(db_path, artifacts_dir, geojson_path=geojson_path)

        with open(artifacts_dir / "representative_quotes.json") as f:
            quotes = json.load(f)

        for nid, archetypes in quotes.items():
            for archetype, quote_list in archetypes.items():
                for i, quote in enumerate(quote_list):
                    assert len(quote) <= 300, (
                        f"Neighbourhood {nid}, {archetype}[{i}]: "
                        f"length {len(quote)} > 300"
                    )

    def test_quotes_all_archetypes(self, mock_export_setup):
        """All 6 archetypes present per neighbourhood."""
        db_path, artifacts_dir, geojson_path = mock_export_setup
        run_export(db_path, artifacts_dir, geojson_path=geojson_path)

        with open(artifacts_dir / "representative_quotes.json") as f:
            quotes = json.load(f)

        for nid, archetypes in quotes.items():
            assert set(archetypes.keys()) == set(ARCHETYPES), (
                f"Neighbourhood {nid} archetypes {set(archetypes.keys())} "
                f"!= {set(ARCHETYPES)}"
            )

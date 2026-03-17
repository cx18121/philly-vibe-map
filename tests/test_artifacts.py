"""Tests for NLP-09: All artifacts exist and are loadable."""
from __future__ import annotations

import json

import numpy as np
import pytest

REQUIRED_ARTIFACTS = [
    "embeddings.npy",
    "review_ids.npy",
    "bertopic_model",
    "topic_assignments.json",
    "vibe_scores.json",
    "temporal_series.json",
    "faiss_index.bin",
    "faiss_id_map.json",
    "representative_quotes.json",
    "sentiment_model",
    "enriched_geojson.geojson",
]


class TestArtifactExistence:
    """NLP-09: All 11 artifact files/directories exist."""

    @pytest.mark.slow
    def test_all_artifacts_exist(self, mock_artifacts_dir):
        """All 11 artifact files/directories exist in artifacts_dir."""
        # This test assumes the full pipeline has been run against mock_artifacts_dir.
        # In practice, it will be run after all stages complete.
        missing = []
        for name in REQUIRED_ARTIFACTS:
            path = mock_artifacts_dir / name
            if not path.exists():
                missing.append(name)
        assert not missing, f"Missing artifacts: {missing}"


class TestArtifactLoadability:
    """NLP-09: Each artifact loads without error."""

    @pytest.mark.slow
    def test_artifacts_loadable(self, mock_artifacts_dir):
        """Each artifact loads without error using appropriate loader."""
        errors = []

        # numpy arrays
        for npy_file in ["embeddings.npy", "review_ids.npy"]:
            path = mock_artifacts_dir / npy_file
            if path.exists():
                try:
                    np.load(path)
                except Exception as e:
                    errors.append(f"{npy_file}: {e}")

        # JSON files
        json_files = [
            "topic_assignments.json",
            "vibe_scores.json",
            "temporal_series.json",
            "faiss_id_map.json",
            "representative_quotes.json",
        ]
        for json_file in json_files:
            path = mock_artifacts_dir / json_file
            if path.exists():
                try:
                    with open(path) as f:
                        json.load(f)
                except Exception as e:
                    errors.append(f"{json_file}: {e}")

        # FAISS index
        faiss_path = mock_artifacts_dir / "faiss_index.bin"
        if faiss_path.exists():
            try:
                import faiss
                faiss.read_index(str(faiss_path))
            except Exception as e:
                errors.append(f"faiss_index.bin: {e}")

        # GeoJSON (just JSON)
        geojson_path = mock_artifacts_dir / "enriched_geojson.geojson"
        if geojson_path.exists():
            try:
                with open(geojson_path) as f:
                    json.load(f)
            except Exception as e:
                errors.append(f"enriched_geojson.geojson: {e}")

        assert not errors, f"Artifact load errors: {errors}"

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
    """NLP-09: All 11 artifact files/directories exist after export."""

    def test_all_artifacts_exist(self, mock_export_setup):
        """All 11 artifact files/directories exist after running export."""
        from pipeline.stages.export import run_export

        db_path, artifacts_dir, geojson_path = mock_export_setup
        run_export(db_path, artifacts_dir, geojson_path=geojson_path)

        missing = []
        for name in REQUIRED_ARTIFACTS:
            path = artifacts_dir / name
            if not path.exists():
                missing.append(name)
        assert not missing, f"Missing artifacts: {missing}"


class TestArtifactLoadability:
    """NLP-09: Each artifact loads without error."""

    def test_artifacts_loadable(self, mock_export_setup):
        """Each artifact loads without error using appropriate loader."""
        from pipeline.stages.export import run_export

        db_path, artifacts_dir, geojson_path = mock_export_setup
        run_export(db_path, artifacts_dir, geojson_path=geojson_path)

        errors = []

        # numpy arrays
        for npy_file in ["embeddings.npy", "review_ids.npy"]:
            path = artifacts_dir / npy_file
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
            path = artifacts_dir / json_file
            if path.exists():
                try:
                    with open(path) as f:
                        json.load(f)
                except Exception as e:
                    errors.append(f"{json_file}: {e}")

        # FAISS index
        faiss_path = artifacts_dir / "faiss_index.bin"
        if faiss_path.exists():
            try:
                import faiss
                faiss.read_index(str(faiss_path))
            except Exception as e:
                errors.append(f"faiss_index.bin: {e}")

        # GeoJSON (just JSON)
        geojson_path = artifacts_dir / "enriched_geojson.geojson"
        if geojson_path.exists():
            try:
                with open(geojson_path) as f:
                    data = json.load(f)
                assert data.get("type") == "FeatureCollection"
            except Exception as e:
                errors.append(f"enriched_geojson.geojson: {e}")

        assert not errors, f"Artifact load errors: {errors}"


class TestEnrichedGeoJSON:
    """NLP-09: Enriched GeoJSON has vibe_scores in feature properties."""

    def test_enriched_geojson_has_vibe_scores(self, mock_export_setup):
        """Each matched feature has vibe_scores and dominant_vibe in properties."""
        from pipeline.stages.export import run_export

        db_path, artifacts_dir, geojson_path = mock_export_setup
        run_export(db_path, artifacts_dir, geojson_path=geojson_path)

        with open(artifacts_dir / "enriched_geojson.geojson") as f:
            geojson = json.load(f)

        enriched_count = 0
        for feature in geojson["features"]:
            nid = feature["properties"].get("NEIGHBORHOOD_NUMBER")
            if nid and "vibe_scores" in feature["properties"]:
                enriched_count += 1
                props = feature["properties"]
                assert "dominant_vibe" in props, f"Missing dominant_vibe for {nid}"
                assert "dominant_vibe_score" in props, f"Missing dominant_vibe_score for {nid}"
                assert isinstance(props["vibe_scores"], dict)
                assert len(props["vibe_scores"]) == 6

        assert enriched_count > 0, "No features were enriched with vibe scores"

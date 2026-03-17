"""Tests for NLP-07: FAISS flat index over neighbourhood vibe vectors."""
from __future__ import annotations

import json
import time

import numpy as np
import pytest


class TestFAISSIndex:
    """NLP-07: FAISS query returns k results in < 10ms."""

    def test_faiss_ntotal_matches_vibe_scores(self, mock_export_setup):
        """FAISS index ntotal == number of neighbourhoods in vibe_scores.json."""
        import faiss

        from pipeline.stages.export import run_export

        db_path, artifacts_dir, geojson_path = mock_export_setup
        run_export(db_path, artifacts_dir, geojson_path=geojson_path)

        index = faiss.read_index(str(artifacts_dir / "faiss_index.bin"))
        with open(artifacts_dir / "vibe_scores.json") as f:
            vibe_scores = json.load(f)

        assert index.ntotal == len(vibe_scores), (
            f"FAISS ntotal={index.ntotal} != vibe_scores count={len(vibe_scores)}"
        )

    def test_faiss_query_returns_k(self, mock_export_setup):
        """Querying FAISS index with k=3 returns 3 results (we have 3 neighbourhoods)."""
        import faiss

        from pipeline.stages.export import run_export

        db_path, artifacts_dir, geojson_path = mock_export_setup
        run_export(db_path, artifacts_dir, geojson_path=geojson_path)

        index = faiss.read_index(str(artifacts_dir / "faiss_index.bin"))
        k = min(3, index.ntotal)
        query = np.random.randn(1, 6).astype(np.float32)
        faiss.normalize_L2(query)
        D, I = index.search(query, k)
        assert I.shape == (1, k), f"Expected shape (1, {k}), got {I.shape}"

    def test_faiss_query_latency(self, mock_export_setup):
        """FAISS query completes in < 10ms."""
        import faiss

        from pipeline.stages.export import run_export

        db_path, artifacts_dir, geojson_path = mock_export_setup
        run_export(db_path, artifacts_dir, geojson_path=geojson_path)

        index = faiss.read_index(str(artifacts_dir / "faiss_index.bin"))
        query = np.random.randn(1, 6).astype(np.float32)
        faiss.normalize_L2(query)

        start = time.perf_counter()
        D, I = index.search(query, min(3, index.ntotal))
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10, f"FAISS query took {elapsed_ms:.1f}ms (limit: 10ms)"

    def test_faiss_id_map_matches(self, mock_export_setup):
        """faiss_id_map.json has same count as FAISS index ntotal."""
        import faiss

        from pipeline.stages.export import run_export

        db_path, artifacts_dir, geojson_path = mock_export_setup
        run_export(db_path, artifacts_dir, geojson_path=geojson_path)

        index = faiss.read_index(str(artifacts_dir / "faiss_index.bin"))
        with open(artifacts_dir / "faiss_id_map.json") as f:
            id_map = json.load(f)

        assert len(id_map) == index.ntotal, (
            f"ID map has {len(id_map)} entries but FAISS index has {index.ntotal}"
        )

    def test_faiss_id_map_values_are_neighbourhood_ids(self, mock_export_setup):
        """faiss_id_map.json values are neighbourhood_id strings from vibe_scores."""
        from pipeline.stages.export import run_export

        db_path, artifacts_dir, geojson_path = mock_export_setup
        run_export(db_path, artifacts_dir, geojson_path=geojson_path)

        with open(artifacts_dir / "faiss_id_map.json") as f:
            id_map = json.load(f)
        with open(artifacts_dir / "vibe_scores.json") as f:
            vibe_scores = json.load(f)

        assert set(id_map.values()) == set(vibe_scores.keys())

"""Tests for NLP-07: FAISS flat index over neighbourhood vibe vectors."""
from __future__ import annotations

import json
import time

import numpy as np
import pytest

from pipeline.stages.export import run_export


class TestFAISSIndex:
    """NLP-07: FAISS query returns k results in < 10ms."""

    @pytest.mark.slow
    def test_faiss_query_returns_k(self, mock_artifacts_dir):
        """Querying FAISS index with k=5 returns exactly 5 results."""
        import faiss

        run_export(db_path="unused", artifacts_dir=mock_artifacts_dir)
        index_path = mock_artifacts_dir / "faiss_index.bin"
        assert index_path.exists(), "faiss_index.bin not created"

        index = faiss.read_index(str(index_path))
        assert index.ntotal > 0, "FAISS index is empty"

        k = min(5, index.ntotal)
        # Create a random query vector matching index dimensionality
        d = index.d
        query = np.random.randn(1, d).astype(np.float32)
        faiss.normalize_L2(query)
        D, I = index.search(query, k)
        assert I.shape == (1, k), f"Expected shape (1, {k}), got {I.shape}"

    @pytest.mark.slow
    def test_faiss_query_latency(self, mock_artifacts_dir):
        """FAISS query completes in < 10ms."""
        import faiss

        run_export(db_path="unused", artifacts_dir=mock_artifacts_dir)
        index = faiss.read_index(str(mock_artifacts_dir / "faiss_index.bin"))

        d = index.d
        query = np.random.randn(1, d).astype(np.float32)
        faiss.normalize_L2(query)

        start = time.perf_counter()
        D, I = index.search(query, min(5, index.ntotal))
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10, f"FAISS query took {elapsed_ms:.1f}ms (limit: 10ms)"

    @pytest.mark.slow
    def test_faiss_id_map_matches(self, mock_artifacts_dir):
        """faiss_id_map.json has same count as FAISS index ntotal."""
        import faiss

        run_export(db_path="unused", artifacts_dir=mock_artifacts_dir)
        index = faiss.read_index(str(mock_artifacts_dir / "faiss_index.bin"))

        id_map_path = mock_artifacts_dir / "faiss_id_map.json"
        assert id_map_path.exists(), "faiss_id_map.json not created"
        with open(id_map_path) as f:
            id_map = json.load(f)

        assert len(id_map) == index.ntotal, (
            f"ID map has {len(id_map)} entries but FAISS index has {index.ntotal}"
        )

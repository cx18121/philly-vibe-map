"""Tests for NLP-01: Sentence embedding stage."""
from __future__ import annotations

import numpy as np
import pytest

from pipeline.stages.embed import run_embed


class TestEmbeddingsShape:
    """NLP-01: Embeddings must be (N, 384) float32."""

    @pytest.mark.slow
    def test_embeddings_shape(self, mock_db_with_reviews, mock_artifacts_dir):
        """run_embed produces embeddings.npy with shape (N, 384), dtype float32."""
        result = run_embed(mock_db_with_reviews, mock_artifacts_dir)
        emb_path = mock_artifacts_dir / "embeddings.npy"
        assert emb_path.exists(), "embeddings.npy not created"
        embeddings = np.load(emb_path)
        assert embeddings.ndim == 2
        assert embeddings.shape[1] == 384
        assert embeddings.shape[0] > 0
        assert embeddings.dtype == np.float32

    @pytest.mark.slow
    def test_review_ids_alignment(self, mock_db_with_reviews, mock_artifacts_dir):
        """review_ids.npy length matches embeddings row count."""
        run_embed(mock_db_with_reviews, mock_artifacts_dir)
        embeddings = np.load(mock_artifacts_dir / "embeddings.npy")
        review_ids = np.load(mock_artifacts_dir / "review_ids.npy")
        assert len(review_ids) == embeddings.shape[0], (
            f"review_ids length {len(review_ids)} != embeddings rows {embeddings.shape[0]}"
        )


class TestEmbedSkip:
    """Artifact gating: skip if embeddings already exist."""

    def test_embed_skip_existing(self, mock_embeddings):
        """With embeddings already present, run_embed returns skipped=True."""
        result = run_embed(
            db_path="unused",
            artifacts_dir=mock_embeddings,
            force=False,
        )
        assert result == {"skipped": True}

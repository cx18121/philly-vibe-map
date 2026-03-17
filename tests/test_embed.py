"""Tests for NLP-01: Sentence embedding stage."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from pipeline.stages.embed import run_embed


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

    def test_embed_force_regenerates(self, mock_db_with_reviews, mock_embeddings):
        """With force=True, run_embed regenerates even if artifact exists."""
        with patch("pipeline.stages.embed.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            # Return fake 384-dim embeddings for any batch of texts
            mock_model.encode.return_value = np.random.randn(90, 384).astype(np.float32)
            MockST.return_value = mock_model

            result = run_embed(
                db_path=mock_db_with_reviews,
                artifacts_dir=mock_embeddings,
                force=True,
            )
            assert result["skipped"] is False
            assert result["count"] == 90
            assert result["dimensions"] == 384
            # Model was actually loaded and used
            MockST.assert_called_once_with("all-MiniLM-L6-v2")
            mock_model.encode.assert_called()


class TestEmbeddingsOutput:
    """NLP-01: Embeddings must be (N, 384) float32 with aligned review_ids."""

    def test_embeddings_shape_and_dtype(self, mock_db_with_reviews, mock_artifacts_dir):
        """run_embed produces embeddings.npy with shape (N, 384), dtype float32."""
        with patch("pipeline.stages.embed.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.random.randn(90, 384).astype(np.float32)
            MockST.return_value = mock_model

            result = run_embed(mock_db_with_reviews, mock_artifacts_dir)
            emb_path = mock_artifacts_dir / "embeddings.npy"
            assert emb_path.exists(), "embeddings.npy not created"
            embeddings = np.load(emb_path)
            assert embeddings.ndim == 2
            assert embeddings.shape[1] == 384
            assert embeddings.shape[0] == 90
            assert embeddings.dtype == np.float32

    def test_review_ids_shape_and_dtype(self, mock_db_with_reviews, mock_artifacts_dir):
        """run_embed produces review_ids.npy with shape (N,), dtype int64."""
        with patch("pipeline.stages.embed.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.random.randn(90, 384).astype(np.float32)
            MockST.return_value = mock_model

            run_embed(mock_db_with_reviews, mock_artifacts_dir)
            ids_path = mock_artifacts_dir / "review_ids.npy"
            assert ids_path.exists(), "review_ids.npy not created"
            review_ids = np.load(ids_path)
            assert review_ids.ndim == 1
            assert review_ids.shape[0] == 90
            assert review_ids.dtype == np.int64

    def test_embeddings_and_ids_aligned(self, mock_db_with_reviews, mock_artifacts_dir):
        """review_ids length matches embeddings row count."""
        with patch("pipeline.stages.embed.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.random.randn(90, 384).astype(np.float32)
            MockST.return_value = mock_model

            run_embed(mock_db_with_reviews, mock_artifacts_dir)
            embeddings = np.load(mock_artifacts_dir / "embeddings.npy")
            review_ids = np.load(mock_artifacts_dir / "review_ids.npy")
            assert len(review_ids) == embeddings.shape[0]

    def test_return_metadata(self, mock_db_with_reviews, mock_artifacts_dir):
        """run_embed returns metadata dict with skipped, count, dimensions."""
        with patch("pipeline.stages.embed.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.random.randn(90, 384).astype(np.float32)
            MockST.return_value = mock_model

            result = run_embed(mock_db_with_reviews, mock_artifacts_dir)
            assert result["skipped"] is False
            assert result["count"] == 90
            assert result["dimensions"] == 384


class TestEmbeddingsShape:
    """NLP-01: Slow integration tests with real model."""

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

"""Tests for NLP-02: BERTopic topic discovery with HDBSCAN tuning."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import numpy as np
import pytest

from pipeline.stages.topic_model import run_topic_model


class TestTopicModelSkip:
    """Artifact gating: skip if bertopic_model/ already exists."""

    def test_skip_existing(self, mock_embeddings):
        """With bertopic_model/ present, run_topic_model returns skipped=True."""
        model_dir = mock_embeddings / "bertopic_model"
        model_dir.mkdir()
        result = run_topic_model(
            db_path="unused",
            artifacts_dir=mock_embeddings,
            force=False,
        )
        assert result == {"skipped": True}


class TestTopicModelUnit:
    """Non-slow unit tests using mocked BERTopic/HDBSCAN/UMAP."""

    def test_loads_precomputed_embeddings(self, mock_db_with_reviews, mock_embeddings):
        """run_topic_model loads embeddings from embeddings.npy."""
        n_reviews = 90
        # Create mock topics (no outliers for simplicity)
        mock_topics = list(range(n_reviews))  # each review gets a unique topic
        mock_probs = np.random.rand(n_reviews, 5).astype(np.float32)

        with patch("pipeline.stages.topic_model.BERTopic") as MockBT, \
             patch("pipeline.stages.topic_model.HDBSCAN") as MockHDB, \
             patch("pipeline.stages.topic_model.UMAP") as MockUMAP:

            mock_model = MagicMock()
            mock_model.fit_transform.return_value = (mock_topics, mock_probs)
            mock_model.reduce_outliers.return_value = mock_topics
            mock_model.get_topic_info.return_value = MagicMock()
            MockBT.return_value = mock_model

            run_topic_model(mock_db_with_reviews, mock_embeddings)

            # BERTopic.fit_transform called with embeddings= kwarg
            ft_call = mock_model.fit_transform.call_args
            assert ft_call is not None
            assert "embeddings" in ft_call.kwargs or (len(ft_call.args) > 1)

    def test_topic_assignments_json_format(self, mock_db_with_reviews, mock_embeddings):
        """topic_assignments.json maps string review IDs to integer topic IDs."""
        n_reviews = 90
        mock_topics = [i % 5 for i in range(n_reviews)]
        mock_probs = np.random.rand(n_reviews, 5).astype(np.float32)

        with patch("pipeline.stages.topic_model.BERTopic") as MockBT, \
             patch("pipeline.stages.topic_model.HDBSCAN"), \
             patch("pipeline.stages.topic_model.UMAP"):

            mock_model = MagicMock()
            mock_model.fit_transform.return_value = (mock_topics, mock_probs)
            mock_model.reduce_outliers.return_value = mock_topics
            mock_model.get_topic_info.return_value = MagicMock()
            MockBT.return_value = mock_model

            run_topic_model(mock_db_with_reviews, mock_embeddings)

            path = mock_embeddings / "topic_assignments.json"
            assert path.exists(), "topic_assignments.json not created"
            with open(path) as f:
                assignments = json.load(f)
            assert isinstance(assignments, dict)
            assert len(assignments) == n_reviews
            for k, v in assignments.items():
                assert isinstance(k, str), f"Key {k} is not a string"
                assert isinstance(v, int), f"Value {v} for key {k} is not an int"

    def test_safetensors_serialization(self, mock_db_with_reviews, mock_embeddings):
        """BERTopic model saved with safetensors serialization."""
        n_reviews = 90
        mock_topics = [i % 5 for i in range(n_reviews)]
        mock_probs = np.random.rand(n_reviews, 5).astype(np.float32)

        with patch("pipeline.stages.topic_model.BERTopic") as MockBT, \
             patch("pipeline.stages.topic_model.HDBSCAN"), \
             patch("pipeline.stages.topic_model.UMAP"):

            mock_model = MagicMock()
            mock_model.fit_transform.return_value = (mock_topics, mock_probs)
            mock_model.reduce_outliers.return_value = mock_topics
            mock_model.get_topic_info.return_value = MagicMock()
            MockBT.return_value = mock_model

            run_topic_model(mock_db_with_reviews, mock_embeddings)

            # Verify save called with safetensors
            mock_model.save.assert_called_once()
            save_call = mock_model.save.call_args
            assert "safetensors" in str(save_call), "save() not called with safetensors serialization"

    def test_outlier_reduction_applied(self, mock_db_with_reviews, mock_embeddings):
        """reduce_outliers and update_topics are called after fit_transform."""
        n_reviews = 90
        # Half are outliers initially
        mock_topics = [-1 if i < 45 else i % 5 for i in range(n_reviews)]
        reduced_topics = [i % 5 for i in range(n_reviews)]  # no outliers after reduction
        mock_probs = np.random.rand(n_reviews, 5).astype(np.float32)

        with patch("pipeline.stages.topic_model.BERTopic") as MockBT, \
             patch("pipeline.stages.topic_model.HDBSCAN"), \
             patch("pipeline.stages.topic_model.UMAP"):

            mock_model = MagicMock()
            mock_model.fit_transform.return_value = (mock_topics, mock_probs)
            mock_model.reduce_outliers.return_value = reduced_topics
            mock_model.get_topic_info.return_value = MagicMock()
            MockBT.return_value = mock_model

            run_topic_model(mock_db_with_reviews, mock_embeddings)

            # reduce_outliers was called
            mock_model.reduce_outliers.assert_called()
            # update_topics was called after reduction
            mock_model.update_topics.assert_called()

    def test_return_metadata(self, mock_db_with_reviews, mock_embeddings):
        """run_topic_model returns metadata dict with n_topics, outlier_rate, n_reviews."""
        n_reviews = 90
        mock_topics = [i % 5 for i in range(n_reviews)]
        mock_probs = np.random.rand(n_reviews, 5).astype(np.float32)

        with patch("pipeline.stages.topic_model.BERTopic") as MockBT, \
             patch("pipeline.stages.topic_model.HDBSCAN"), \
             patch("pipeline.stages.topic_model.UMAP"):

            mock_model = MagicMock()
            mock_model.fit_transform.return_value = (mock_topics, mock_probs)
            mock_model.reduce_outliers.return_value = mock_topics
            mock_model.get_topic_info.return_value = MagicMock()
            MockBT.return_value = mock_model

            result = run_topic_model(mock_db_with_reviews, mock_embeddings)

            assert result["skipped"] is False
            assert "n_topics" in result
            assert "outlier_rate" in result
            assert result["n_reviews"] == n_reviews


class TestTopicModeling:
    """NLP-02: BERTopic produces >= 20 topics, outlier rate < 50%."""

    @pytest.mark.slow
    def test_topic_count(self, mock_db_with_reviews, mock_embeddings):
        """BERTopic produces >= 20 distinct topics."""
        result = run_topic_model(mock_db_with_reviews, mock_embeddings)
        assignments_path = mock_embeddings / "topic_assignments.json"
        assert assignments_path.exists(), "topic_assignments.json not created"
        with open(assignments_path) as f:
            assignments = json.load(f)
        unique_topics = set(assignments.values())
        # Exclude outlier topic -1 from count
        non_outlier_topics = {t for t in unique_topics if t != -1}
        assert len(non_outlier_topics) >= 20, (
            f"Only {len(non_outlier_topics)} topics found (need >= 20)"
        )

    @pytest.mark.slow
    def test_outlier_rate_below_50_pct(self, mock_db_with_reviews, mock_embeddings):
        """Outlier rate < 50% after reduce_outliers()."""
        run_topic_model(mock_db_with_reviews, mock_embeddings)
        with open(mock_embeddings / "topic_assignments.json") as f:
            assignments = json.load(f)
        total = len(assignments)
        outliers = sum(1 for t in assignments.values() if t == -1)
        outlier_rate = outliers / total if total > 0 else 1.0
        assert outlier_rate < 0.5, f"Outlier rate {outlier_rate:.1%} >= 50%"

    @pytest.mark.slow
    def test_topic_model_saves(self, mock_db_with_reviews, mock_embeddings):
        """bertopic_model/ directory exists after stage runs."""
        run_topic_model(mock_db_with_reviews, mock_embeddings)
        model_dir = mock_embeddings / "bertopic_model"
        assert model_dir.exists(), "bertopic_model/ directory not created"
        assert model_dir.is_dir(), "bertopic_model should be a directory"


class TestTopicAssignments:
    """Topic assignment output format."""

    @pytest.mark.slow
    def test_topic_assignments_json(self, mock_db_with_reviews, mock_embeddings):
        """topic_assignments.json is valid JSON with review_id string keys."""
        run_topic_model(mock_db_with_reviews, mock_embeddings)
        path = mock_embeddings / "topic_assignments.json"
        assert path.exists()
        with open(path) as f:
            assignments = json.load(f)
        assert isinstance(assignments, dict)
        assert len(assignments) > 0
        # All keys should be string review IDs, all values should be ints
        for k, v in assignments.items():
            assert isinstance(k, str), f"Key {k} is not a string"
            assert isinstance(v, int), f"Value {v} for key {k} is not an int"

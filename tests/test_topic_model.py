"""Tests for NLP-02: BERTopic topic discovery with HDBSCAN tuning."""
from __future__ import annotations

import json

import pytest

from pipeline.stages.topic_model import run_topic_model


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

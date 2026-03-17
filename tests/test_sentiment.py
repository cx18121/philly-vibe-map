"""Tests for NLP-04: LoRA fine-tune DistilBERT sentiment classifier."""
from __future__ import annotations

import pytest

from pipeline.stages.sentiment import run_sentiment


class TestStarMapping:
    """NLP-04: Star rating remapping to 3-class sentiment."""

    def test_stars_1_maps_to_negative(self):
        from pipeline.stages.sentiment import _stars_to_label
        assert _stars_to_label(1) == 0

    def test_stars_2_maps_to_negative(self):
        from pipeline.stages.sentiment import _stars_to_label
        assert _stars_to_label(2) == 0

    def test_stars_3_maps_to_neutral(self):
        from pipeline.stages.sentiment import _stars_to_label
        assert _stars_to_label(3) == 1

    def test_stars_4_maps_to_positive(self):
        from pipeline.stages.sentiment import _stars_to_label
        assert _stars_to_label(4) == 2

    def test_stars_5_maps_to_positive(self):
        from pipeline.stages.sentiment import _stars_to_label
        assert _stars_to_label(5) == 2


class TestLoRAConfig:
    """NLP-04: LoRA configuration is valid for DistilBERT."""

    def test_lora_config_constants(self):
        """Verify the module exposes expected LoRA hyperparameters."""
        from pipeline.stages.sentiment import (
            MODEL_NAME,
            TRAIN_EPOCHS,
            TRAIN_BATCH_SIZE,
            LEARNING_RATE,
            MAX_SEQ_LENGTH,
        )
        assert MODEL_NAME == "distilbert-base-uncased"
        assert TRAIN_EPOCHS == 3
        assert TRAIN_BATCH_SIZE == 32
        assert LEARNING_RATE == 2e-4
        assert MAX_SEQ_LENGTH == 256

    @pytest.mark.slow
    def test_lora_config_valid(self):
        """LoraConfig with task_type SEQ_CLS, r=16, alpha=32, dropout=0.1 does not raise."""
        from peft import LoraConfig, TaskType

        config = LoraConfig(
            task_type=TaskType.SEQ_CLS,
            r=16,
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_lin", "v_lin"],
        )
        assert config.r == 16
        assert config.lora_alpha == 32
        assert config.task_type == TaskType.SEQ_CLS

    @pytest.mark.slow
    def test_three_class_output(self):
        """Model output has num_labels=3."""
        from transformers import AutoModelForSequenceClassification

        model = AutoModelForSequenceClassification.from_pretrained(
            "distilbert-base-uncased", num_labels=3
        )
        assert model.config.num_labels == 3


class TestArtifactGate:
    """NLP-04: Stage skips if sentiment_model/ already exists."""

    def test_skips_when_model_dir_exists(self, mock_artifacts_dir):
        """run_sentiment returns {skipped: True} if sentiment_model/ exists."""
        (mock_artifacts_dir / "sentiment_model").mkdir()
        result = run_sentiment(db_path="unused", artifacts_dir=mock_artifacts_dir)
        assert result == {"skipped": True}

    def test_does_not_skip_when_force(self, mock_artifacts_dir):
        """run_sentiment does not skip even if dir exists when force=True."""
        (mock_artifacts_dir / "sentiment_model").mkdir()
        # With force=True and no actual data, it should attempt to run
        # (and fail because there's no Yelp data). We just verify it doesn't return skipped.
        with pytest.raises(Exception):
            run_sentiment(db_path="unused", artifacts_dir=mock_artifacts_dir, force=True)


class TestMergedModel:
    """Merged model loadability."""

    @pytest.mark.slow
    def test_merged_model_loadable(self, mock_artifacts_dir):
        """sentiment_model/ can be loaded with AutoModelForSequenceClassification."""
        from transformers import AutoModelForSequenceClassification

        run_sentiment(db_path="unused", artifacts_dir=mock_artifacts_dir)
        model_dir = mock_artifacts_dir / "sentiment_model"
        assert model_dir.exists(), "sentiment_model/ not created"
        model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
        assert model.config.num_labels == 3

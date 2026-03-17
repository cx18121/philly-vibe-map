"""Tests for NLP-04: LoRA fine-tune DistilBERT sentiment classifier."""
from __future__ import annotations

import pytest

from pipeline.stages.sentiment import run_sentiment


class TestLoRAConfig:
    """NLP-04: LoRA configuration is valid for DistilBERT."""

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

"""Stage 4: LoRA fine-tune DistilBERT sentiment classifier, merge adapter."""
from __future__ import annotations

import datetime
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import torch

_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
MODEL_NAME = "distilbert-base-uncased"
MAX_TRAIN_SAMPLES = int(os.environ.get("MAX_TRAIN_SAMPLES", "0"))  # 0 = use all
TRAIN_EPOCHS = 3
TRAIN_BATCH_SIZE = 32
LEARNING_RATE = 2e-4
MAX_SEQ_LENGTH = 256

# CPU-specific overrides (applied when CUDA is unavailable)
CPU_TRAIN_BATCH_SIZE = 4
CPU_GRADIENT_ACCUM_STEPS = 8  # effective batch = 4 * 8 = 32
CPU_MAX_TRAIN_SAMPLES = 50_000
CPU_TRAIN_EPOCHS = 1


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


def _stars_to_label(stars: int) -> int:
    """Map Yelp star rating to 3-class sentiment.

    1-2 -> 0 (negative), 3 -> 1 (neutral), 4-5 -> 2 (positive)
    """
    if stars <= 2:
        return 0
    elif stars == 3:
        return 1
    else:
        return 2


class YelpSentimentDataset(torch.utils.data.Dataset):
    """PyTorch Dataset that tokenizes Yelp reviews on __getitem__."""

    def __init__(self, texts: list[str], labels: list[int], tokenizer, max_length: int = 256):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict:
        encoding = self.tokenizer(
            self.texts[idx],
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long),
        }


def _load_yelp_reviews(max_samples: int) -> tuple[list[str], list[int]]:
    """Stream Yelp review NDJSON and extract (text, label) pairs.

    Args:
        max_samples: Maximum number of samples to load (0 = all).

    Returns:
        Tuple of (texts, labels) lists.
    """
    import orjson

    data_dir = os.environ.get("YELP_DATA_DIR", ".")
    review_path = Path(data_dir) / "yelp_academic_dataset_review.json"

    if not review_path.exists():
        raise FileNotFoundError(
            f"Review file not found: {review_path}. "
            "Set YELP_DATA_DIR to the directory containing yelp_academic_dataset_review.json."
        )

    texts: list[str] = []
    labels: list[int] = []
    count = 0

    _log("INFO", f"Loading reviews from {review_path}")
    with open(review_path, "rb") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = orjson.loads(line)
            except Exception:
                continue

            text = record.get("text")
            stars = record.get("stars")
            if not text or stars is None:
                continue

            texts.append(text)
            labels.append(_stars_to_label(int(stars)))
            count += 1

            if max_samples > 0 and count >= max_samples:
                break

    _log("INFO", f"Loaded {count:,} reviews for sentiment training")
    return texts, labels


def run_sentiment(db_path: str, artifacts_dir: Path, force: bool = False) -> dict:
    """Fine-tune DistilBERT with LoRA for 3-class sentiment, merge and save.

    Outputs:
        artifacts_dir / sentiment_model/ -- merged DistilBERT weights + tokenizer
    """
    output_path = artifacts_dir / "sentiment_model"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'sentiment': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    _log("INFO", "Stage 'sentiment': starting...")

    # ------------------------------------------------------------------
    # CPU fallback: constrain memory footprint when no GPU is available
    # ------------------------------------------------------------------
    max_samples = MAX_TRAIN_SAMPLES
    on_cpu = not torch.cuda.is_available()
    if on_cpu:
        _log("WARN", "CUDA not available -- using CPU-optimised training settings")
        if max_samples == 0:
            max_samples = CPU_MAX_TRAIN_SAMPLES
            _log("WARN", f"Auto-setting MAX_TRAIN_SAMPLES to {max_samples:,} for CPU training")

    # ------------------------------------------------------------------
    # Load data from Yelp NDJSON
    # ------------------------------------------------------------------
    texts, labels = _load_yelp_reviews(max_samples)

    if len(texts) == 0:
        raise RuntimeError("No training samples loaded. Check YELP_DATA_DIR and review file.")

    # ------------------------------------------------------------------
    # Compute class weights for balanced training
    # ------------------------------------------------------------------
    label_counts = np.bincount(labels, minlength=3).astype(np.float64)
    # Avoid division by zero for classes with no samples
    label_counts = np.maximum(label_counts, 1.0)
    weights_per_class = 1.0 / label_counts
    # Normalize so weights sum to num_classes
    weights_per_class = weights_per_class / weights_per_class.sum() * 3.0
    class_weights_tensor = torch.tensor(weights_per_class, dtype=torch.float32)
    _log("INFO", f"Class weights: {weights_per_class.tolist()}")

    # ------------------------------------------------------------------
    # Tokenizer and Dataset
    # ------------------------------------------------------------------
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_dataset = YelpSentimentDataset(texts, labels, tokenizer, max_length=MAX_SEQ_LENGTH)

    # ------------------------------------------------------------------
    # Model setup with LoRA
    # ------------------------------------------------------------------
    from transformers import AutoModelForSequenceClassification, TrainingArguments, Trainer
    from peft import LoraConfig, get_peft_model, TaskType

    base_model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)

    lora_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,
        r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q_lin", "v_lin"],
    )
    model = get_peft_model(base_model, lora_config)
    model.print_trainable_parameters()

    # ------------------------------------------------------------------
    # Custom Trainer with weighted cross-entropy loss
    # ------------------------------------------------------------------
    class WeightedTrainer(Trainer):
        def __init__(self, class_weights, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.class_weights = class_weights

        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels_val = inputs.pop("labels")
            outputs = model(**inputs)
            loss_fn = torch.nn.CrossEntropyLoss(
                weight=self.class_weights.to(outputs.logits.device)
            )
            loss = loss_fn(outputs.logits, labels_val)
            return (loss, outputs) if return_outputs else loss

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    checkpoints_dir = str(artifacts_dir / "sentiment_checkpoints")

    batch_size = CPU_TRAIN_BATCH_SIZE if on_cpu else TRAIN_BATCH_SIZE
    grad_accum = CPU_GRADIENT_ACCUM_STEPS if on_cpu else 1
    epochs = CPU_TRAIN_EPOCHS if on_cpu else TRAIN_EPOCHS
    total_steps = (len(train_dataset) // batch_size) * epochs
    warmup_steps = int(total_steps * 0.1)

    _log("INFO", f"Training config: batch_size={batch_size}, grad_accum={grad_accum}, "
         f"epochs={epochs}, total_steps~{total_steps}, warmup_steps={warmup_steps}, cpu={on_cpu}")

    training_args = TrainingArguments(
        output_dir=checkpoints_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        learning_rate=LEARNING_RATE,
        warmup_steps=warmup_steps,
        logging_steps=100,
        save_strategy="epoch",
        report_to="none",
        remove_unused_columns=False,
        # CPU memory optimisations
        optim="adafactor" if on_cpu else "adamw_torch",
        gradient_checkpointing=on_cpu,
    )

    trainer = WeightedTrainer(
        class_weights=class_weights_tensor,
        model=model,
        args=training_args,
        train_dataset=train_dataset,
    )
    trainer.train()

    # ------------------------------------------------------------------
    # Merge LoRA adapter and export standalone model
    # ------------------------------------------------------------------
    merged_model = model.merge_and_unload()
    output_dir = str(output_path)
    merged_model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    _log("INFO", f"Merged sentiment model saved to {output_dir}")

    # Cleanup checkpoints to save disk
    checkpoints_path = artifacts_dir / "sentiment_checkpoints"
    if checkpoints_path.exists():
        shutil.rmtree(checkpoints_path)
        _log("INFO", "Removed training checkpoints directory")

    return {
        "skipped": False,
        "train_samples": len(train_dataset),
        "epochs": epochs,
        "model_dir": output_dir,
    }

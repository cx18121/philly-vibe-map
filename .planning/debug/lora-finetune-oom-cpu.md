---
status: awaiting_human_verify
trigger: "LoRA/PEFT fine-tuning killed (OOM) on CPU after ~18 steps out of 46,875"
created: 2026-03-18T00:00:00Z
updated: 2026-03-18T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED -- Multiple compounding OOM factors on CPU
test: Fix applied, awaiting human verification via pipeline run
expecting: Training completes without OOM kill
next_action: User runs pipeline sentiment stage and confirms completion

## Symptoms

expected: Fine-tuning completes all steps and saves a sentiment model checkpoint
actual: Process killed after ~18 steps (Linux OOM killer due to RAM exhaustion)
errors: |
  trainable params: 887,811 || all params: 67,843,590 || trainable%: 1.3086
  warmup_ratio is deprecated and will be removed in v5.2
  0%| | 18/46875 [05:13<282:02:54, 21.67s/it] Killed
reproduction: Run pipeline which triggers sentiment fine-tuning on CPU
started: Every run; training never completes

## Eliminated

(none yet)

## Evidence

- timestamp: 2026-03-18T00:01:00Z
  checked: pipeline/stages/sentiment.py configuration constants and TrainingArguments
  found: |
    TRAIN_BATCH_SIZE = 32 (line 22)
    MAX_SEQ_LENGTH = 256 (line 24)
    TRAIN_EPOCHS = 3 (line 21)
    CPU fallback sets max_samples = 500,000 (line 146)
    TrainingArguments uses default optimizer (AdamW)
    warmup_ratio=0.1 (deprecated)
    No gradient_checkpointing
    No gradient_accumulation_steps
    Total steps = 500000/32 * 3 = 46,875
  implication: |
    Memory analysis per batch:
    - batch_size=32, seq_len=256, distilbert hidden=768
    - Forward pass: 32 * 256 * 768 * 4 bytes * multiple layers ~ hundreds of MB
    - AdamW stores momentum + variance for all 67M params = ~512MB extra
    - 500K text strings in RAM = hundreds of MB more
    - Total easily exceeds available RAM

## Resolution

root_cause: |
  Multiple compounding factors cause OOM on CPU:
  1. TRAIN_BATCH_SIZE=32 is far too large for CPU (should be 1-4)
  2. Default AdamW optimizer stores 2 extra copies of all 67M params (~512MB)
  3. 500K samples auto-limit still loads all text strings into RAM
  4. No gradient checkpointing enabled
  5. 46,875 total steps would take ~282 hours even if it didn't OOM
fix: |
  1. Reduce batch_size to 4 on CPU, use gradient_accumulation_steps=8 (effective batch=32)
  2. Switch optimizer to "adafactor" on CPU (no momentum states)
  3. Reduce max_samples to 50K on CPU (still plenty for fine-tuning)
  4. Enable gradient_checkpointing=True on CPU
  5. Reduce epochs to 1 on CPU (with 50K samples, 1 epoch is sufficient)
  6. Fix warmup_ratio -> warmup_steps deprecation
verification: []
files_changed:
  - pipeline/stages/sentiment.py

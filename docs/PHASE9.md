# Phase 9 Evaluate Model Quality

## Purpose

Verify that system improvements do not hide unacceptable quality loss.

## Tasks

- Compute token-weighted validation loss and perplexity over 1,023,000 scored targets from 1,024,000 validation input tokens.
- Export final MLX checkpoints to Hugging Face-compatible weights.
- Pass the fixed three-prompt logit-equivalence check.
- Run `arc_easy` and `openbookqa` using `lm-eval==0.4.13`, zero-shot, seed 42, and batch size 1.
- Report `acc` and `acc_norm`, treating `acc_norm` as primary.

## Exit Criteria

- Every reported checkpoint uses identical evaluation inputs and settings.
- Exported checkpoints differ from MLX logits by at most `1e-3`.
- Benchmark versions and raw outputs are archived.

## Outputs

Validation metrics, benchmark records, exported-checkpoint verification, and quality summary.

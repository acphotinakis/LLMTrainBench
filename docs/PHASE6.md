# Phase 6 Compare Adaptation Methods

## Purpose

Compare full-parameter continued pretraining with LoRA on the same Mac, data, token budget, and production pipeline. QLoRA is optional.

## Tasks

- Run `A00`, `A10`, and `A20` from the adaptation matrix.
- Verify LoRA trainable modules and parameter counts against `BREAKDOWN.md`.
- Run `A30` only if its smoke-test gate passes.
- Evaluate all final checkpoints on the fixed validation set.
- Apply the predefined training-method selection rule.

## Exit Criteria

- Required methods complete for seeds 17, 42, and 73.
- All methods receive identical training tokens and evaluation data.
- The selected method can be derived from results without subjective weighting.

## Outputs

Full-training checkpoints, LoRA adapters, optional QLoRA adapters, quality results, and selected method.

# Phase 3 Establish the Baseline

## Purpose

Prove the full system works and establish the control measurement.

## Tasks

- Implement MLX model loading, causal-language-model loss, optimization, checkpointing, and resume validation.
- Implement the structured metrics contract in `METRICS.md`.
- Evaluate the unchanged model.
- Run smoke experiment `S00`.
- Run baseline experiment `P00` exactly as specified.

## Exit Criteria

- `S00` trains, saves, reloads, and validates successfully.
- `P00` produces three valid run records.
- No run contains missing required metrics or NaN/Inf values.
- Peak memory remains below 43 GB.

## Outputs

Verified training loop, baseline checkpoints, unchanged-model evaluation, and `P00` results.

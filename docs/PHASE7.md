# Phase 7 Test Dataset Scale

## Purpose

Measure how the selected method behaves as the nested training corpus grows.

## Tasks

- Run `D10`, `D50`, and `D100` with seed 42.
- Verify one-pass exact token accounting for every run.
- Measure runtime, throughput, memory, validation quality, and cost.
- Calculate marginal quality improvement from 10M to 50M and 50M to 100M.

## Exit Criteria

- All three scale runs use the same model, method, pipeline, and evaluation.
- Results are labeled as descriptive single-seed findings.
- Exact token counts match the manifest.

## Outputs

Scale checkpoints, structured results, and diminishing-return analysis.

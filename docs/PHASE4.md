# Phase 4 Run the Data Pipeline Experiments

## Purpose

Measure one data-pipeline factor at a time using the frozen matrix in `EXPERIMENT_PROTOCOL.md`.

## Tasks

- Run `P01` through `P22` in protocol order.
- Preserve every valid, failed, and excluded run record.
- Apply cache-state and fresh-process requirements.
- Summarize all replicates using `METRICS.md`.

## Exit Criteria

- Every required matrix row has three valid replicates or a documented feasibility failure.
- Controls differ from candidates only in the named variable.
- Results validation detects no missing fields or duplicate run IDs.

## Outputs

Pipeline run records, summaries, and diagnostic cache and streaming results.

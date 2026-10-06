# Phase 5 Select the Production Pipeline

## Purpose

Choose one stable local data pipeline using the predefined throughput, quality, memory, and tie-break rules.

## Tasks

- Rank eligible local candidates by median real-token throughput.
- Run quality control `P30` and candidate confirmation `P31`.
- Apply the Phase 5 guardrails in `BREAKDOWN.md` without changing thresholds.
- Save and commit the winner as `configs/production_pipeline.yaml`.

## Exit Criteria

- The winner passes quality, reliability, and memory guardrails.
- The selection is reproducible from structured results.
- The production configuration is frozen before adaptation runs.

## Outputs

Production pipeline configuration, selection report, and supporting result references.

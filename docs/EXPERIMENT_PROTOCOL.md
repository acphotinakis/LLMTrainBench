# Experiment Protocol

This document freezes the run-level protocol for the FineWeb-Edu continued-pretraining study. `BREAKDOWN.md` defines scope; this file determines which runs are executed and how configurations are selected.

## Readiness Gate

Official measurements may begin only when all items pass:

- The dependency lockfile installs successfully on the core Mac.
- Model, tokenizer, and dataset revisions match `BREAKDOWN.md`.
- Dataset tests prove split disjointness, nested subsets, exact token counts, and complete checksums.
- A 100-sequence smoke dataset completes data loading, training, checkpoint reload, and validation.
- The metrics logger emits every required field in `METRICS.md`.
- The process stays below 43 GB peak memory and produces no NaN or Inf values.
- The Mac is connected to power, Low Power Mode is off, and unrelated foreground workloads are closed.

## Constants

Unless a row explicitly changes one value, every run uses:

- Core Mac and locked MLX environment
- Pinned Qwen model and tokenizer
- Sequence length 1,024
- Seed 42
- Bfloat16
- Full-parameter training
- Baseline optimizer and schedule from `BREAKDOWN.md`
- Microbatch 1 and gradient accumulation 8
- 50 warmup optimizer updates, 300 measured optimizer updates, and three fresh-process repetitions for performance benchmarks
- `train_10m` for quality confirmations

For a performance benchmark, restore the same initial model state before each repetition and do not include model loading, compilation, warmup, validation, or checkpoint writing in the measured window. Report those times separately.

## Pipeline Experiment Matrix

`P00` is the control. Later rows inherit the preceding named control and change only the stated factor.

| ID | Changed factor | Configuration | Control | Repetitions | Primary outcome |
|---|---|---|---|---:|---|
| `S00` | Smoke test | 100 packed sequences; 5 optimizer updates | None | 1 | End-to-end success |
| `P00` | Baseline | Local raw text; online tokenization; padded batches; workers 0; prefetch 0 | None | 3 | Real tokens/s |
| `P01` | Tokenization | Local pretokenized examples; padded batches | `P00` | 3 | Real tokens/s |
| `P02` | Packing | Local pretokenized, packed 1,024-token sequences | `P01` | 3 | Real tokens/s |
| `P03` | Access mode | Remote streaming of the pinned source manifest; online tokenization; padded batches | `P00` | 3 | Real tokens/s and variability |
| `P04` | Cache state | `P02`, first run after reboot before another project data access | `P02` | 3 reboot blocks | Time to first batch |
| `P05` | Cache state | Immediate repeat of each matching `P04` run | `P04` | 3 | Time to first batch |
| `P10` | Workers | `P02` with 0 workers and no queued prefetch | `P02` | 3 | Real tokens/s |
| `P11` | Workers | `P02` with 2 workers and prefetch depth 2 per worker | `P10` | 3 | Real tokens/s |
| `P12` | Workers | `P02` with 4 workers and prefetch depth 2 per worker | `P10` | 3 | Real tokens/s |
| `P13` | Workers | `P02` with 8 workers and prefetch depth 2 per worker | `P10` | 3 | Real tokens/s |
| `P20` | Prefetch | Best eligible nonzero worker count with depth 1 per worker | Worker-stage winner | 3 | Real tokens/s |
| `P21` | Prefetch | Same worker count with depth 2 per worker | `P20` | 3 | Real tokens/s |
| `P22` | Prefetch | Same worker count with depth 4 per worker | `P20` | 3 | Real tokens/s |
| `P30` | Quality control | Full 10M training using `P00` | None | 1, seed 42 | Validation loss |
| `P31` | Candidate confirmation | Full 10M training using selected local candidate | `P30` | 1, seed 42 | Validation loss |

The worker-stage winner is the eligible `P10`–`P13` configuration with the highest median real-token throughput. The production pipeline is then chosen using the Phase 5 rule in `BREAKDOWN.md`. Remote `P03` and cache rows `P04`–`P05` are diagnostic and ineligible to become the production pipeline.

## Adaptation Matrix

Every core adaptation run uses the selected production pipeline and `train_10m`.

| ID | Method | Seeds | Training budget | Required |
|---|---|---|---|---|
| `A00` | Unchanged model evaluation | 42 | No training | Yes |
| `A10` | Full-parameter continued pretraining | 17, 42, 73 | 9,999,360 tokens per seed | Yes |
| `A20` | LoRA | 17, 42, 73 | 9,999,360 tokens per seed | Yes |
| `A30` | 4-bit MLX QLoRA | 17, 42, 73 | 9,999,360 tokens per seed | No |

The training-method winner is selected by the Phase 6 rule in `BREAKDOWN.md`. Hyperparameters may be changed only during an explicitly labeled pilot that uses the smoke dataset. Pilot results cannot appear as confirmatory results.

## Scale Matrix

Use the selected core adaptation method and production pipeline. Reuse `A10` or `A20` seed 42 as `D10` when its configuration is identical.

| ID | Dataset | Seed | Exact training tokens | Repetitions |
|---|---|---:|---:|---:|
| `D10` | `train_10m` | 42 | 9,999,360 | 1 |
| `D50` | `train_50m` | 42 | 49,999,872 | 1 |
| `D100` | `train_100m` | 42 | 99,999,744 | 1 |

Scale results are descriptive single-seed results. They must not be presented as estimates of seed-to-seed uncertainty.

## Optional Hardware Matrix

Hardware experiments require a protocol amendment in `DECISIONS.md` naming the GPU, driver, framework, precision, batch policy, and cost rate before execution.

| ID | Comparison | Rule |
|---|---|---|
| `H10` | Mac versus one NVIDIA GPU | Repeat one complete frozen configuration on each platform; report separate strata |
| `H20` | One versus two identical NVIDIA GPUs | DDP only; same per-GPU microbatch and sequence length; report global batch change and scaling efficiency |

## Failure and Exclusion Rules

A run is invalid if it uses the wrong revision, loses examples, reports NaN/Inf, exceeds 43 GB on the core Mac, performs checkpoint I/O in the measured window, or has an unrelated foreground workload. Do not silently rerun. Retain the failed log, assign a new run ID to the replacement, and record the reason.

An outlier is never removed solely because it is slow. Exclusion requires a documented protocol violation or system interruption. Report all valid replicates.

## Change Control

Any change to a frozen value requires a dated entry in `DECISIONS.md`, an explanation of which completed runs become incomparable, and new experiment IDs. Never overwrite prior structured results.

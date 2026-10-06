# Metrics and Results Schema

This document defines the measurements used to compare runs. Every run writes one immutable JSON record plus step-level JSON Lines data.

## Primary Metrics

- **Real-token throughput:** non-padding input tokens processed during the measured window divided by measured training seconds.
- **Validation loss:** token-weighted mean next-token negative log likelihood over exactly 1,023,000 scored targets from the 1,024,000-input-token validation set.
- **Validation perplexity:** `exp(validation_loss)`.
- **Peak process memory:** maximum resident memory attributed to the training process and children.
- **Peak unified memory:** maximum device/system unified-memory value available from the selected macOS instrumentation. Report `null` when unavailable; do not substitute process memory.

## Secondary Metrics

- Step duration in milliseconds
- Batch preparation and wait time in milliseconds
- Raw tokens/s and real tokens/s
- Padding fraction: padding tokens divided by input positions
- CPU utilization percentage
- GPU utilization percentage when the measurement source supports it
- Time to first batch
- Total wall-clock runtime
- Preprocessing runtime and output bytes
- Checkpoint or adapter bytes
- Trainable and total parameter counts
- ARC Easy and OpenBookQA `acc` and `acc_norm`
- Estimated monetary cost and energy-measurement method

Utilization values from different tools or platforms are not directly compared unless their definitions match.

## Aggregation

For each performance configuration, report all three replicate values, median, arithmetic mean, sample standard deviation, minimum, and maximum. The primary ranking uses median real-token throughput. Do not average Mac and NVIDIA results together.

For adaptation quality, report each seed and the arithmetic mean across seeds. Scale experiments are single-seed and are labeled descriptive.

## Run Record

Each `results/runs/<run_id>.json` contains at least:

```json
{
  "schema_version": "1.0",
  "run_id": "P00-r1",
  "experiment_id": "P00",
  "status": "complete",
  "started_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "git_commit": "FULL_COMMIT_SHA",
  "config_sha256": "SHA256",
  "model_revision": "060db6499f32faf8b98477b0a26969ef7d8b9987",
  "dataset_revision": "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9",
  "dataset_name": "train_10m",
  "seed": 42,
  "hardware_id": "core-mac",
  "software_lock_sha256": "SHA256",
  "warmup_steps": 50,
  "measured_steps": 300,
  "real_tokens": 0,
  "measured_seconds": 0.0,
  "real_tokens_per_second": 0.0,
  "peak_process_memory_bytes": 0,
  "validation_loss": null,
  "validation_perplexity": null,
  "failure_reason": null
}
```

Additional fields are allowed, but required fields may not be renamed. Failed and excluded runs use `status` values `failed` or `excluded` and include `failure_reason`.

## Measurement Boundaries

Synchronize pending MLX work before starting and stopping timers. The performance window excludes model loading, graph compilation, the 50 warmup steps, validation, checkpoint writing, and log upload. It includes batch preparation required during normal steady-state training.

For padded runs, report both raw and real tokens. For packed runs they are equal unless an implementation defect exists.

## Cost

Mac runs report wall-clock hours and measured energy when available; otherwise energy and monetary cost are `null`. Rented GPU runs use the invoiced hourly rate multiplied by billed duration and identify the provider and region. Do not assign an invented hourly price to university hardware.

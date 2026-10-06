# Execution Environment

The core environment is the project's Apple MacBook Pro with an M5-series chip and 48 GB unified memory. Its exact chip and hardware identifier must be captured before official runs. MLX is the only core training framework. This file defines environment capture; the generated lockfile and run metadata record the installed values.

## Core Software

- macOS on Apple silicon
- Python 3.12
- `mlx-lm==0.32.0`
- `lm-eval==0.4.13`
- Remaining direct and transitive dependencies pinned in `uv.lock`

MLX-LM supports Qwen2-family models and full, LoRA, and quantized LoRA training; its upstream usage reference is [MLX-LM LoRA documentation](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md).

The first implementation task must create `pyproject.toml` and `uv.lock`, then run the smoke test. If these versions are incompatible on the core Mac, update them before official experiments and record the replacement in `DECISIONS.md`. Dependencies are never upgraded during an experiment group.

## Required Environment Capture

Before every run, record:

- Mac model identifier, chip, CPU/GPU core counts, and total memory
- macOS build number
- Python version
- Package lockfile SHA-256
- Git commit and working-tree cleanliness
- Available disk space and dataset volume filesystem
- Power-source and Low Power Mode state
- Thermal state at start and end
- Model and dataset revisions

Use a stable power connection and close unrelated compute-heavy applications. A run affected by a macOS update, thermal warning, indexing job, backup, or foreground workload is retained but excluded with a reason.

## Storage Layout

Raw and processed data must reside on the same local volume for all core comparisons. Record whether the volume is internal or external and its filesystem. Keep at least 20% free space during benchmarks.

## Optional NVIDIA Environment

NVIDIA experiments require a separate environment document or appended section naming the exact GPU model and count, VRAM, host CPU and RAM, Linux distribution, driver, CUDA, framework and library versions, storage, provider, region, and hourly rate. PyTorch/CUDA results are a separate hardware stratum and cannot replace missing MLX core results.

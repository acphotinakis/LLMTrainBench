# FineWeb Edu Continued Pretraining Systems Study

This repository studies how data pipelines, adaptation methods, dataset scale, and hardware affect the efficiency and quality of continued pretraining for a small language model. The core study uses a pinned Qwen2.5-0.5B base model, deterministic FineWeb-Edu subsets, MLX, and the project's M5-series MacBook Pro with 48 GB unified memory.

The project is an experimental systems study, not a chatbot and not a financial-language model. Full-parameter training and LoRA are required; QLoRA, NVIDIA replication, and two-GPU DDP are optional extensions.

## Current Status

The experimental specification is frozen and the repository is ready for implementation scaffolding and the end-to-end smoke test. Official measurements must wait until the readiness gate in [Experiment Protocol](docs/EXPERIMENT_PROTOCOL.md) passes.

## Documentation

- [Project Breakdown](docs/BREAKDOWN.md): scope, frozen decisions, phases, and selection rules
- [Experiment Protocol](docs/EXPERIMENT_PROTOCOL.md): exact run matrix and readiness gate
- [Data Card](docs/DATA_CARD.md): source, transformations, manifests, and validation
- [Metrics](docs/METRICS.md): measurement definitions and result schema
- [Environment](docs/ENVIRONMENT.md): hardware and software controls
- [Runbook](docs/RUNBOOK.md): execution order and command contracts
- [Decision Log](docs/DECISIONS.md): accepted and future project decisions
- `docs/PHASE1.md` through `docs/PHASE10.md`: phase tasks and exit criteria

## Frozen Inputs

- Model and tokenizer: `Qwen/Qwen2.5-0.5B@060db6499f32faf8b98477b0a26969ef7d8b9987`
- Dataset: `HuggingFaceFW/fineweb-edu`, `sample-10BT`, `train@87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`
- Sequence length: 1,024 tokens
- Training sizes: 9,999,360; 49,999,872; and 99,999,744 tokens
- Validation size: 1,024,000 tokens

## Planned Repository Layout

```text
configs/        Frozen experiment and data configurations
data/           Local raw and processed artifacts, excluded from Git
docs/           Research and operating documentation
results/        Structured run records, summaries, and plots
src/            Data, training, evaluation, and analysis code
tests/          Dataset, configuration, checkpoint, and metric tests
```

## Implementation Order

1. Create `pyproject.toml`, `uv.lock`, configuration schemas, and environment capture.
2. Implement deterministic data construction and its validation tests.
3. Implement MLX training, checkpointing, and structured metrics.
4. Pass experiment `S00`, the end-to-end smoke test.
5. Run the pipeline, adaptation, scale, and quality matrices in protocol order.

Commands shown in `RUNBOOK.md` are interface contracts until their corresponding modules are implemented.

## License

Repository code and documentation are licensed under the included MIT License. FineWeb-Edu and Qwen retain their own upstream licenses and attribution requirements.

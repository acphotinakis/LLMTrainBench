# Project Runbook

This runbook defines the execution order. Command names are interface contracts to implement; they are not evidence that the commands already exist.

## 1 Prepare the Environment

```bash
uv lock --check
uv sync --frozen
uv run python -m llm_flow.config validate configs/core.yaml
uv run python -m llm_flow.experiment_config validate-all
uv run python -m llm_flow.environment capture --register-core-mac
uv run python -m llm_flow.environment validate --capture results/environment/<capture-id>.json
uv run python -m llm_flow.environment validate --capture results/environment/<capture-id>.json --require-artifacts
```

The capture command prints its immutable path under `results/environment/`; use that path in both validation commands. The first capture creates `results/environment/core-mac-binding.json`, which binds subsequent captures to the same physical machine. The first validation checks observed host, installed packages, storage, power, and start thermal state. Full validation also requires locally loaded pinned model, tokenizer, and dataset revision evidence and tokenizer EOS. Missing artifacts remain `unverified` and block readiness. A failed capture or validation record is retained; take a new capture after correcting the condition.

After each run, record the end thermal observation without changing the start capture:

```bash
uv run python -m llm_flow.environment observe-end --capture results/environment/<capture-id>.json
```

This writes a separate immutable `results/environment/end-<capture-id>-<suffix>.json` linked to the start capture. The Phase 1 capture records start state only.

## 2 Build and Verify Data

```bash
python -m src.data.build --config configs/data.yaml
python -m src.data.verify --manifest data/processed/dataset_manifest.json
sha256sum -c data/processed/checksums.sha256
```

Do not begin training until every `DATA_CARD.md` test passes.

## 3 Run the Smoke Test

```bash
python -m src.train --config configs/experiments/S00.yaml
python -m src.checkpoints.verify --run-id S00
python -m src.evaluate.validation --run-id S00
```

The smoke test must train, save, reload, and evaluate without NaN/Inf values or missing metrics.

## 4 Run Pipeline Benchmarks

```bash
python -m src.experiments.run --matrix configs/pipeline_matrix.yaml
python -m src.results.validate --group pipeline
python -m src.results.summarize --group pipeline
```

Run `P04` only as the first project data access after reboot; run its paired `P05` immediately afterward. Do not perform unrelated tasks during a measured window.

## 5 Confirm and Freeze the Production Pipeline

Run `P30` and `P31`, apply the frozen selection rule, write the selected configuration to `configs/production_pipeline.yaml`, and commit it before adaptation experiments.

## 6 Run Adaptation and Scale Experiments

```bash
python -m src.experiments.run --matrix configs/adaptation_matrix.yaml
python -m src.selection.training_method --results results/runs
python -m src.experiments.run --matrix configs/scale_matrix.yaml
```

QLoRA is skipped unless its smoke-test gate passes. Never substitute an NVIDIA QLoRA result into the Mac adaptation matrix.

## 7 Evaluate Quality

```bash
python -m src.evaluate.validation --all-final-checkpoints
python -m src.checkpoints.export_hf --all-final-checkpoints
python -m src.checkpoints.compare_logits --all-final-checkpoints
python -m src.evaluate.benchmarks --tasks arc_easy,openbookqa --num-fewshot 0 --seed 42
```

Stop benchmark evaluation for a checkpoint if export logit equivalence exceeds `1e-3`.

## 8 Analyze and Archive

```bash
python -m src.results.validate --all
python -m src.results.summarize --all
python -m src.results.plot --all
```

Archive configs, lockfile, manifests, checksums, logs, results, plots, and the Git commit. Raw source text is not committed to Git.

## Failure Recovery

Keep partial and failed logs. Resume training only from a verified checkpoint and issue a new run ID. Record the parent run and checkpoint digest. A resumed run cannot be used in a performance benchmark, but it may complete a quality run if total token accounting remains exact and the interruption is disclosed.

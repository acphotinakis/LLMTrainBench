# P1-002 Runtime Environment and Experiment Schemas Execution Report

- Phase: 1
- Work item: `P1-002`
- Status: Implementation complete; Phase 1 runtime exit blocked
- Date: 2026-10-14
- Plan: `docs/work-items/phase-01/plans/P1-002-runtime-environment-and-schemas-plan.md`
- Checklist: 13/13 implementation items complete; 0 implementation items remaining

## Outcome

The canonical data, training, evaluation, S00, pipeline, adaptation and scale configurations load through a strict validator. It rejects missing and unknown fields, placeholders, wrong types, duplicate rows and frozen-value changes. The P/A/D row sets match `EXPERIMENT_PROTOCOL.md`. Fixed pipeline rows resolve to concrete settings; future winner rows require a local completed selection artifact with checksummed completed source runs. D10 reuse requires a complete matching A10/A20 seed-42 run and an equal effective configuration digest.

The environment command creates immutable actual-host captures and a non-overwritable core-Mac identity binding. It records installed versions for all 89 active requirements exported from the lock, hardware, macOS build, storage, power, current start thermal state, Git state, lock digest and pinned revision declarations. It resolves pinned Hub snapshots only from local cache; model verification loads MLX weights and tokenizer, checks Qwen2 architecture and EOS, while dataset verification reads a row from local `sample-10BT` Parquet and hashes the file. Absent local artifacts remain `unverified`. `observe-end` writes a separate linked thermal record after a future run; no training run or end observation occurred in this work item.

## Files changed

- Added `src/llm_flow/experiment_config.py` and `src/llm_flow/environment.py`.
- Added `configs/data.yaml`, `configs/training.yaml`, `configs/evaluation.yaml`, `configs/experiments/S00.yaml`, and all three P/A/D matrix YAML files.
- Added `tests/test_experiment_config.py` and `tests/test_environment.py`.
- Updated `docs/RUNBOOK.md` and the P1-002 plan checklist.
- Generated `results/environment/core-mac-binding.json` and immutable captures under `results/environment/`.

No frozen model, data, optimizer, token count, threshold, package version or lockfile value changed. Unrelated workspace files were preserved.

## Test-first evidence

The first focused run failed collection because the existing editable installation did not expose `llm_flow`:

```text
ModuleNotFoundError: No module named 'llm_flow'
2 errors during collection
```

The local `.venv` tree carried macOS `UF_HIDDEN` flags, causing Python to skip the editable `.pth` file. A fresh frozen install at `/tmp/llm-flow-p1-002-fresh` imported the package. For stable unprefixed repository commands, a clean ignored `venv/` was installed from the frozen lock and `.venv` now points to it. The original `.venv` was preserved at `/tmp/llm-flow-p1-002-original-venv`. The fresh and repository environments each passed import and core validation without `PYTHONPATH`.

Focused tests now cover valid canonical files, bool-as-int and missing fields, frozen counts and budgets, duplicate/unknown rows, unresolved transitive winners, selection run checksums, D10 configuration equality, host readiness boundaries, binding immutability, missing active packages, loaded revision/EOS validation, and linked end observation. The artifact loader success tests use local test doubles and are not counted as proof of actual pinned artifacts.

## Validation

| Command | Result |
|---|---|
| `uv lock --check` | Passed; 91 packages resolved. |
| `uv sync --frozen` | Passed; 90 packages checked. |
| `uv run python -c 'import llm_flow; print(llm_flow.__file__)'` | Passed without `PYTHONPATH`. |
| `uv run python -m llm_flow.config validate configs/core.yaml` | Passed. |
| `uv run python -m llm_flow.experiment_config validate-all` | Passed; 15 P, 4 A, 3 D rows. |
| `uv run ruff check src tests` | Passed. |
| `uv run pytest tests/test_environment.py tests/test_experiment_config.py -q` | Passed; 30 tests. |
| `uv run pytest -q` | Passed; 42 tests. |

The disposable `/tmp/llm-flow-p1-002-fresh` environment also passed frozen sync, package import, and core validation. The latest actual capture is `results/environment/capture-20261014T154850510986Z-b7ebb523.json`. It records `Mac17,8`, Apple M5 Pro, 18 CPU and 20 GPU cores, 48 GiB memory, macOS build `25G83`, same local APFS volume for raw and processed paths, about 27% free, normal power mode, nominal OS-reported thermal state, and the actual dirty Git tree. The first capture retained an earlier storage probe failure; no capture was overwritten.

| Readiness command against latest capture | Result |
|---|---|
| `uv run python -m llm_flow.environment validate --capture results/environment/capture-20261014T154850510986Z-b7ebb523.json` | Exit 2: Mac is on battery. |
| Same command with `--require-artifacts` | Exit 2: battery plus pinned model, tokenizer and dataset absent locally; loaded EOS unverified. |

## Remaining blockers and next action

Phase 1's full runtime exit is not met. Connect this Mac to AC power, then take a new immutable capture. The pinned Qwen model/tokenizer and FineWeb-Edu `sample-10BT` revision must become available through the authorized data acquisition path; this work item made no large download. Repeat capture and both readiness modes after the artifacts can actually load. A future run must also call `observe-end` to record end thermal state. The current dirty Git tree is recorded as provenance and does not itself fail readiness.

## Skills and source checks

- `llm-flow-implementation-executor` and `llm-flow-work-router`: dependency order, project authority and report/checklist gates.
- `mle-workflow`, `python-patterns`, `tdd-workflow`, `python-testing`, `verification-loop`: reproducibility, strict Python validation, RED/GREEN tests and final gate.
- Primary local API checks: installed MLX-LM 0.32.0 `load` supports a local path, eager weight load and returned tokenizer; Hugging Face Hub 1.33.0 `snapshot_download` accepts `local_files_only=True`; datasets 5.1.0 repository offline fallback can reuse a different cached revision, so dataset verification reads an explicit local pinned Parquet path. macOS thermal state uses the installed Apple SDK `ProcessInfo.thermalState` enum; `pmset` power mode 0 is normal and 1 is Low Power Mode.

# P1-002 Runtime Environment and Experiment Schemas Plan

- Phase: 1
- Work item: `P1-002`
- Status: Proposed
- Scope: Designated-Mac environment capture and readiness assertions; strict data, training, evaluation, experiment and matrix schemas.
- Goal: Make the remaining Phase 1 contracts executable while preserving completed `P1-001`.
- Exit criterion: A fresh frozen install works on the designated Mac; actual host, installed packages, loaded artifact revisions and EOS pass; every canonical configuration loads without placeholders or implicit defaults. Report unavailable artifact-backed assertions as a Phase 1 blocker.

## Current-state evidence

- `docs/BREAKDOWN.md` fixes Qwen and FineWeb-Edu revisions, EOS 151643, length 1,024, exact subset sizes, baseline and LoRA settings, seeds and selection rules. `docs/EXPERIMENT_PROTOCOL.md` defines all S/P/A/D rows and readiness.
- `docs/PHASE1.md` requires schemas, capture and validation. `docs/ENVIRONMENT.md` requires before-run hardware, software, disk, power and thermal capture, plus end thermal state. `docs/DATA_CARD.md` defines data provenance and exact counts; `docs/METRICS.md` distinguishes 1,024,000 validation input tokens from 1,023,000 scored targets.
- `pyproject.toml`, `uv.lock`, `configs/core.yaml`, `src/llm_flow/config.py` and `tests/test_config.py` exist from completed `P1-001`. `load_core_config` validates declarations but does not inspect this Mac, installed packages or loaded model/dataset artifacts.
- `src/llm_flow/environment.py`, `src/llm_flow/experiment_config.py`, remaining YAML and their tests are proposed. `docs/RUNBOOK.md` still uses a non-implemented `src.environment.capture` command. `docs/work-items/README.md` records that the current `.venv` fails to import `llm_flow` without `PYTHONPATH=src`.
- Current host observation: `Mac17,8`, Apple M5 Pro, 18 CPU cores, 48 GiB, macOS 26.6.2 build `25G83`, about 27% disk free. This is not an immutable capture or proof of loaded artifact revisions. No pinned Qwen or FineWeb-Edu artifacts are cached.

## Dependencies, assumptions, decisions and non-goals

- Depends on completed `P1-001`; preserve its frozen values and evidence.
- Register the designated physical Mac at first capture using a stable machine-identity digest plus model, chip and memory. Later captures must match the binding; hardware class alone does not identify one machine.
- Software/configuration validation, observed host readiness and loaded-artifact readiness are distinct results. If pinned artifacts are absent, record them as `unverified` and fail full readiness. YAML declarations, cache names and test mocks are insufficient runtime evidence.
- Future selected pipeline, worker and method values use typed references. Their matrices are schema-valid but cannot execute until a verified selection artifact resolves them.
- Non-goals: dataset building, model training, official measurements, large model/dataset downloads, downstream winner selection and frozen research changes. A frozen incompatibility must be reported for a `docs/DECISIONS.md` entry, never silently changed.

## Dependency-ordered implementation strategy

1. Repair package discovery if needed; prove `uv sync --frozen` plus import and core validation in a disposable fresh uv environment without `PYTHONPATH`.
2. Add strict typed data, training, evaluation, experiment and matrix loaders. Require explicit values or an explicit validated named-profile reference; reject unknown/missing fields, wrong types, placeholders, duplicate IDs, bad inheritance and frozen changes. Provide all-config CLI plus separate executable-row resolution.
3. Encode the canonical data process, full/LoRA/optional QLoRA training, fixed and benchmark evaluation, S00 and every protocol matrix row. Validate controls, factors, repetitions, budgets and selection eligibility.
4. Implement actual macOS and installed-package capture, one-time physical machine binding and immutable capture records. Capture thermal state at run start; support a separate end observation after the run, linked to the start record. Preserve unknown probe observations with reasons.
5. Validate observed software, host, disk and power readiness. Assert revisions and EOS only from locally loaded pinned model/tokenizer/dataset metadata; no large download. Missing local artifacts fail full readiness.
6. Update the runbook to tested `llm_flow` commands, run focused and full validation, inspect the actual capture and report remaining blockers.

## File change map

| Path | State | Change |
|---|---|---|
| `pyproject.toml` | Existing | Repair package installation only if needed; preserve frozen dependencies. |
| `uv.lock` | Existing | Preserve resolution; verify lock. |
| `src/llm_flow/config.py` | Existing | Reuse strict core constants and errors where appropriate. |
| `src/llm_flow/experiment_config.py` | Proposed | Typed loaders, cross-file validation, all-config CLI and executable-row resolution. |
| `src/llm_flow/environment.py` | Proposed | Actual capture, immutable identity binding, readiness CLI and artifact checks. |
| `configs/data.yaml` | Proposed | Frozen source, normalization/filtering, dedup, split, ordering, EOS, packing, products and limits. |
| `configs/training.yaml` | Proposed | Full, LoRA and optional QLoRA profiles with optimizer/schedule, precision, batches, checkpoints and seeds. |
| `configs/evaluation.yaml` | Proposed | Fixed validation, benchmark settings and export tolerance. |
| `configs/experiments/S00.yaml` | Proposed | 100 sequences, five optimizer updates, explicit profiles and artifact references. |
| `configs/pipeline_matrix.yaml` | Proposed | All P rows with controls, factors, repetitions and eligibility. |
| `configs/adaptation_matrix.yaml` | Proposed | A00/A10/A20/optional A30, seeds and budgets. |
| `configs/scale_matrix.yaml` | Proposed | D10/D50/D100, exact budgets, conditional D10 reuse. |
| `tests/test_environment.py` | Proposed | Probe, binding, immutability, readiness and missing-artifact cases. |
| `tests/test_experiment_config.py` | Proposed | Canonical, malformed, boundary, cross-field and unresolved cases. |
| `docs/RUNBOOK.md` | Existing | Replace obsolete environment command with verified interfaces. |
| `results/environment/<capture-id>.json` and binding record | Generated, proposed | Immutable actual-host evidence, written atomically without overwrite. |

## Atomic implementation checklist

- [x] Repair package install if necessary; fresh `uv sync --frozen` and `uv run python -c 'import llm_flow'` pass without `PYTHONPATH`.
- [x] Add `configs/data.yaml` and strict validation for pinned source, normalization, filters, dedup, split, ordering, EOS, 1,024 packing and exact train/validation products; changed invariants fail.
- [x] Add `configs/training.yaml` and strict validation for full baseline, LoRA and optional QLoRA, AdamW, schedules, dtype, clipping, batches, accumulation, checkpoints and seeds; changed frozen fields fail.
- [x] Add `configs/evaluation.yaml` and strict validation for 1,024,000 input versus 1,023,000 scored tokens, loss/perplexity, `lm-eval==0.4.13`, `arc_easy`/`openbookqa`, zero-shot, seed 42, batch 1 and logit tolerance `1e-3`.
- [x] Add S00 and P/A/D matrices covering every named row in `EXPERIMENT_PROTOCOL.md`; validate controls, changed factors, repetitions, budgets, classifications and explicit profile references.
- [x] Use typed unresolved references for worker-stage, production-pipeline and method winners; schema loading succeeds, execution rejects them until selection artifacts bind them. P20 requires an eligible nonzero worker; P03–P05 are diagnostic and excluded from production selection.
- [x] Validate A00 as zero-training evaluation, A30 as optional, and D10 reuse only when the selected pipeline, method, seed and full configuration equal an A10/A20 seed-42 run.
- [x] Capture actual machine identity digest, Mac model/chip, CPU/GPU cores, memory, macOS build, Python, installed package versions, lock digest, Git commit/cleanliness, volume filesystem/internal status/free fraction, power/Low Power Mode and thermal state at start; provide a linked, separate thermal end observation after a run. Unknown observations retain a reason.
- [x] Bind the designated Mac in a non-overwritable record; reject subsequent identity mismatch. Write every capture atomically with a unique ID and retain failed/unverified records.
- [x] Enforce Python 3.12, frozen installed package versions, bound M5-series 48 GiB machine, same local raw/processed volume, at least 20% free, AC power, Low Power Mode off and acceptable start thermal state; record actual Git commit and working-tree cleanliness without treating a dirty tree as a contract violation. Unknown required observations fail readiness.
- [x] Assert locally loaded model/tokenizer/dataset revisions and tokenizer EOS; absent pinned artifacts produce `unverified` details and fail full readiness without a large download.
- [x] Update `docs/RUNBOOK.md` with tested all-config, capture and readiness commands and immutable artifact paths.
- [x] Run commands below, inspect the actual generated capture, and record any readiness blocker in the P1-002 execution report.

## Test matrix

| Case | Fixture or actual observation | Expected result |
|---|---|---|
| Success | Canonical YAML | Typed load and complete protocol row set. |
| Failure | Wrong installed version, identity, power, disk, revision or EOS | Named readiness failure retained in record. |
| Boundary | Exactly 20% free, exact budgets and 1,023 shifted targets | Inclusive threshold passes; off-by-one counts fail. |
| Determinism | Repeat parsing and content digest | Same resolved values/digest; separate capture IDs preserve observations. |
| Malformed | Missing/unknown field, wrong type, placeholder, duplicate ID, bad control/reference | Attributable schema error, no row execution. |
| Resource limit | Probe unavailable, low disk, absent pinned artifacts | Explicit unknown/unverified; full readiness fails. |
| Real environment | Start capture on designated Mac after fresh install; linked end observation after a run | Immutable host/package/volume/power/start-thermal/Git evidence and distinct end-thermal evidence; artifacts pass only if locally loaded. |

## Validation commands

Existing commands, run from repository root without `PYTHONPATH`:

```bash
uv lock --check
uv sync --frozen
uv run python -c 'import llm_flow; print(llm_flow.__file__)'
uv run python -m llm_flow.config validate configs/core.yaml
uv run ruff check src tests
uv run pytest tests/test_environment.py tests/test_experiment_config.py -q
uv run pytest -q
```

Implement the following exact interfaces before use. Capture prints its immutable path; substitute that path for `<capture-id>`. The first readiness mode checks software, host, storage and power; the second also requires loaded artifact metadata and EOS. The `observe-end` command is used only after a run and writes a separate record linked to its start capture.

```bash
uv run python -m llm_flow.experiment_config validate-all
uv run python -m llm_flow.environment capture --register-core-mac
uv run python -m llm_flow.environment validate --capture results/environment/<capture-id>.json
uv run python -m llm_flow.environment validate --capture results/environment/<capture-id>.json --require-artifacts
uv run python -m llm_flow.environment observe-end --capture results/environment/<capture-id>.json
```

For clean-install proof, create a disposable uv project environment, run `uv sync --frozen`, import and core validation there, then report its exact temporary path and result. `validate-all` checks schema; executable-row resolution must separately reject future winner references.

## Risks, containment and rollback

- Missing pinned artifacts block artifact-backed Phase 1 exit. Retain the capture and name each unavailable check; never promote a declaration or mock to runtime proof.
- Capture stores only a stable machine identity digest, not raw serial numbers or secrets.
- macOS probes can be unavailable. Preserve source/error, mark required readings unknown and fail readiness rather than guess.
- Preserve all capture/binding records. On failure, use a new ID. Revert only this item's code/config changes if necessary.

## Requirement and exit-criterion traceability

| Requirement | Evidence |
|---|---|
| `docs/PHASE1.md` schemas and canonical configs | Checklist 2–7; all-config CLI and tests. |
| `docs/ENVIRONMENT.md` host and before-run capture | Checklist 8–10; actual immutable record and readiness. |
| `docs/BREAKDOWN.md` and `docs/DATA_CARD.md` frozen revisions, EOS and counts | Checklist 2, 4, 11; negative tests and artifact readiness. |
| `docs/EXPERIMENT_PROTOCOL.md` run matrices and selection | Checklist 5–7; all-config and unresolved tests. |
| `docs/METRICS.md` evaluation targets/settings | Checklist 4; evaluation tests. |
| Phase 1 clean install and runtime exit | Checklist 1, 8–11; fresh uv proof and both readiness modes; missing artifacts are a documented blocker. |

## Skills used

- `llm-flow-work-router`: project authority and Phase 1 boundary.
- `llm-flow-implementation-planner`: evidence, dependencies, commands and traceability.
- `mle-workflow`: reproducibility and separation of declared configuration from observed runtime evidence.

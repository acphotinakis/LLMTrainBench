# P1-002 Runtime environment and experiment schemas Plan

- Phase: 1
- Work item: `P1-002`
- Status: Proposed
- Scope: Runtime environment and experiment schemas.
- Goal: Complete Phase 1 runtime assertions and explicit data, training, evaluation, and matrix schemas.
- Exit criterion: Phase 1 exits when the locked environment installs, runtime assertions pass and all canonical configurations load.

## Current-state evidence

- `src/llm_flow/config.py` exists and supplies the configuration baseline.
- `configs/core.yaml` exists and supplies the configuration baseline.
- `pyproject.toml` exists and supplies the research baseline.
- `uv.lock` exists and supplies the locked dependency baseline.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE1.md`, `docs/ENVIRONMENT.md`, `docs/EXPERIMENT_PROTOCOL.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P1-001`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: Hardware identifier remains unresolved until capture on designated Mac; do not substitute this host.
- Non-goals: changing frozen model, data revisions, token budgets or selection thresholds; implementing downstream work items.

## Dependency-ordered strategy

1. Verify dependency outputs and frozen contracts; stop and record any mismatch in `docs/DECISIONS.md` before changing research settings.
2. Add the smallest module/config interfaces listed below and focused correctness fixtures.
3. Produce the run/data artifact only after its validation gates pass; preserve failures and provenance.
4. Re-run repository checks and inspect the resulting artifact against the exit criterion.

## File change map

| Path | State | Intended change |
|---|---|---|
| `src/llm_flow/environment.py` | Proposed | Implement or update |
| `src/llm_flow/experiment_config.py` | Proposed | Implement or update |
| `configs/data.yaml` | Proposed | Implement or update |
| `configs/experiments/S00.yaml` | Proposed | Implement or update |
| `configs/pipeline_matrix.yaml` | Proposed | Implement or update |
| `configs/adaptation_matrix.yaml` | Proposed | Implement or update |
| `configs/scale_matrix.yaml` | Proposed | Implement or update |
| `tests/test_environment.py` | Proposed | Implement or update |
| `tests/test_experiment_config.py` | Proposed | Implement or update |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Capture exact Mac identifier, chip, cores, memory, OS, power, thermal, disk, lock digest, Git state and revisions; demonstrate this in a focused fixture or immutable run record.
- [ ] Reject wrong hardware, package versions, missing EOS/revision, placeholders, unknown matrix fields and mismatched run settings; demonstrate this in a focused fixture or immutable run record.
- [ ] Validate canonical data, training, evaluation and matrix schemas without implicit defaults; demonstrate this in a focused fixture or immutable run record.
- [ ] Prove clean locked install and record environment artifact before official runs; demonstrate this in a focused fixture or immutable run record.
- [ ] Verify `uv run python -m llm_flow.config validate configs/core.yaml` and `uv run pytest -q` succeed without `PYTHONPATH`; the current `.venv` fails to import `llm_flow` despite 12 tests passing with `PYTHONPATH=src`.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Capture exact Mac identifier, chip, cores, memory, OS, power, thermal, disk, lock digest, Git state and revisions |
| Failure | Deliberately failed or interrupted dependency/run | Explicit error or retained failed record; no silent promotion |
| Boundary | Smallest valid input and exact frozen limit | Exact counts, thresholds and limits respected |
| Determinism | Repeat fixed seed/input under locked environment | Same IDs, configuration and content-derived result where required |
| Malformed input | Missing field, corrupt artifact or wrong revision | Rejected with attributable reason |
| Resource limit | Insufficient disk, memory or unavailable hardware/source | Safe stop or documented infeasibility; no partial result called complete |

## Validation commands

These commands already exist in `pyproject.toml` and `src/llm_flow/config.py`; run them after this item's proposed files exist:

```bash
uv lock --check
uv sync --frozen
uv run python -m llm_flow.config validate configs/core.yaml
uv run ruff check src tests
uv run pytest tests/test_environment.py -q
uv run pytest tests/test_experiment_config.py -q
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- Hardware identifier remains unresolved until capture on designated Mac; do not substitute this host.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE1.md`, `docs/ENVIRONMENT.md`, `docs/EXPERIMENT_PROTOCOL.md` | Checklist items 1–5, item-specific fixtures and environment artifact |
| Phase 1 exit criterion | Checklist items 4–7 and validation commands; the locked environment installs, runtime assertions pass and canonical configurations load. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `mle-workflow`: reproducible ML data, training and evaluation contracts.


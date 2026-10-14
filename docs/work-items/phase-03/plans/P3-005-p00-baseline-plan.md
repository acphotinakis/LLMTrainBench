# P3-005 P00 three-replicate control baseline Plan

- Phase: 3
- Work item: `P3-005`
- Status: Proposed
- Scope: P00 three-replicate control baseline.
- Goal: Run the frozen local raw/online/padded control in fresh processes.
- Exit criterion: Phase 3 exits with three valid P00 records, all fields and finite values.

## Current-state evidence

- `docs/EXPERIMENT_PROTOCOL.md` exists and supplies the research baseline.
- `src/llm_flow/metrics.py` is proposed by proposed; it is not present in the current tree.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE3.md`, `docs/EXPERIMENT_PROTOCOL.md`, `docs/METRICS.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P3-004`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: Official runs require readiness gate on designated Mac.
- Non-goals: changing frozen model, data revisions, token budgets or selection thresholds; implementing downstream work items.

## Dependency-ordered strategy

1. Verify dependency outputs and frozen contracts; stop and record any mismatch in `docs/DECISIONS.md` before changing research settings.
2. Add the smallest module/config interfaces listed below and focused correctness fixtures.
3. Produce the run/data artifact only after its validation gates pass; preserve failures and provenance.
4. Re-run repository checks and inspect the resulting artifact against the exit criterion.

## File change map

| Path | State | Intended change |
|---|---|---|
| `src/llm_flow/experiments/run.py` | Proposed | Implement or update |
| `configs/experiments/P00.yaml` | Proposed | Implement or update |
| `results/runs/P00-*.json` | Generated output | Produce and retain immutable artifact |
| `tests/test_experiment_runner.py` | Proposed | Implement or update |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Restore identical initial model before each fresh process; demonstrate this in a focused fixture or immutable run record.
- [ ] Run 50 untimed warmup then 300 measured optimizer updates three times; demonstrate this in a focused fixture or immutable run record.
- [ ] Include steady-state batch prep; exclude compile, validation and checkpoint I/O; demonstrate this in a focused fixture or immutable run record.
- [ ] Preserve failed runs with new replacement IDs and verify below-43-GB memory; demonstrate this in a focused fixture or immutable run record.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Restore identical initial model before each fresh process |
| Failure | Deliberately failed or interrupted dependency/run | Explicit error or retained failed record; no silent promotion |
| Boundary | Smallest valid input and exact frozen limit | Exact counts, thresholds and limits respected |
| Determinism | Repeat fixed seed/input under locked environment | Same IDs, configuration and content-derived result where required |
| Malformed input | Missing field, corrupt artifact or wrong revision | Rejected with attributable reason |
| Resource limit | Insufficient disk, memory or unavailable hardware/source | Safe stop or documented infeasibility; no partial result called complete |

## Validation commands

These commands already exist in `pyproject.toml` and `src/llm_flow/config.py`; run them after this item's proposed files exist:

```bash
uv lock --check
uv run python -m llm_flow.config validate configs/core.yaml
uv run ruff check src tests
uv run pytest tests/test_experiment_runner.py -q
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- Official runs require readiness gate on designated Mac.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE3.md`, `docs/EXPERIMENT_PROTOCOL.md`, `docs/METRICS.md` | Checklist items 1–4, item-specific fixtures and generated artifact |
| Phase 3 exit criterion | Final two checklist items and validation commands; Phase 3 exits with three valid P00 records, all fields and finite values. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `benchmark-optimization-loop`: bounded baseline, one-factor variants and correctness gates.


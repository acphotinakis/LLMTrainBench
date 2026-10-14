# P4-002 P03/P04/P05 diagnostic runs Plan

- Phase: 4
- Work item: `P4-002`
- Status: Proposed
- Scope: P03/P04/P05 diagnostic runs.
- Goal: Measure remote streaming and paired cold/warm cache effects without promoting diagnostics.
- Exit criterion: Each diagnostic row has required repetitions or documented feasibility failure, with cache-state provenance.

## Current-state evidence

- `docs/EXPERIMENT_PROTOCOL.md` exists and supplies the research baseline.
- `docs/METRICS.md` exists and supplies the research baseline.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE4.md`, `docs/EXPERIMENT_PROTOCOL.md`, `docs/ENVIRONMENT.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P4-001`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: Remote availability and reboot scheduling are external conditions; retain failed evidence.
- Non-goals: changing frozen model, data revisions, token budgets or selection thresholds; implementing downstream work items.

## Dependency-ordered strategy

1. Verify dependency outputs and frozen contracts; stop and record any mismatch in `docs/DECISIONS.md` before changing research settings.
2. Add the smallest module/config interfaces listed below and focused correctness fixtures.
3. Produce the run/data artifact only after its validation gates pass; preserve failures and provenance.
4. Re-run repository checks and inspect the resulting artifact against the exit criterion.

## File change map

| Path | State | Intended change |
|---|---|---|
| `configs/pipeline_matrix.yaml` | Proposed by P1-002 | Extend the schema-valid config for this experiment |
| `src/llm_flow/experiments/cache.py` | Proposed | Implement or update |
| `tests/test_cache_protocol.py` | Proposed | Implement or update |
| `results/runs/P0{3,4,5}-*.json` | Generated output | Produce and retain immutable artifact |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Run P03 as pinned remote source manifest against P00 with three processes; demonstrate this in a focused fixture or immutable run record.
- [ ] Schedule P04 as first project data access after each of three reboots; demonstrate this in a focused fixture or immutable run record.
- [ ] Pair each P05 immediately after matching P04 and record time to first batch; demonstrate this in a focused fixture or immutable run record.
- [ ] Mark remote and cache rows diagnostic/ineligible for production ranking; demonstrate this in a focused fixture or immutable run record.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Run P03 as pinned remote source manifest against P00 with three processes |
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
uv run pytest tests/test_cache_protocol.py -q
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- Remote availability and reboot scheduling are external conditions; retain failed evidence.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE4.md`, `docs/EXPERIMENT_PROTOCOL.md`, `docs/ENVIRONMENT.md` | Checklist items 1–4, item-specific fixtures and generated artifact |
| Phase 4 exit criterion | Final two checklist items and validation commands; Each diagnostic row has required repetitions or documented feasibility failure, with cache-state provenance. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `benchmark-optimization-loop`: bounded baseline, one-factor variants and correctness gates.


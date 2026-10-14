# P4-003 P10–P22 worker and prefetch matrix Plan

- Phase: 4
- Work item: `P4-003`
- Status: Proposed
- Scope: P10–P22 worker and prefetch matrix.
- Goal: Benchmark all worker counts, select worker-stage winner, then vary only prefetch depth.
- Exit criterion: Every row has three valid replicates or documented feasibility failure and factors are isolated.

## Current-state evidence

- `docs/EXPERIMENT_PROTOCOL.md` exists and supplies the research baseline.
- `docs/METRICS.md` exists and supplies the research baseline.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE4.md`, `docs/EXPERIMENT_PROTOCOL.md`, `docs/BREAKDOWN.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P4-001`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: A no-eligible-worker outcome blocks prefetch rows and is recorded, not fabricated.
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
| `src/llm_flow/experiments/pipeline.py` | Proposed by dependency | Implement or update |
| `tests/test_worker_prefetch.py` | Proposed | Implement or update |
| `results/runs/P{10,11,12,13,20,21,22}-*.json` | Generated output | Produce and retain immutable artifact |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Run P10–P13 for 0/2/4/8 workers with required depth and three replicates each; demonstrate this in a focused fixture or immutable run record.
- [ ] Select eligible nonzero worker winner by median real-token throughput; demonstrate this in a focused fixture or immutable run record.
- [ ] Run P20/P21/P22 at depth 1/2/4 for chosen workers, three replicates each; demonstrate this in a focused fixture or immutable run record.
- [ ] Prove all other model/data/seed/window settings identical; demonstrate this in a focused fixture or immutable run record.
- [ ] Record memory failures and data-loss checks; demonstrate this in a focused fixture or immutable run record.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Run P10–P13 for 0/2/4/8 workers with required depth and three replicates each |
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
uv run pytest tests/test_worker_prefetch.py -q
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- A no-eligible-worker outcome blocks prefetch rows and is recorded, not fabricated.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE4.md`, `docs/EXPERIMENT_PROTOCOL.md`, `docs/BREAKDOWN.md` | Checklist items 1–5, item-specific fixtures and generated artifact |
| Phase 4 exit criterion | Final two checklist items and validation commands; Every row has three valid replicates or documented feasibility failure and factors are isolated. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `benchmark-optimization-loop`: bounded baseline, one-factor variants and correctness gates.


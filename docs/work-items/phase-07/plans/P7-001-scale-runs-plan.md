# P7-001 D10/D50/D100 scale experiments Plan

- Phase: 7
- Work item: `P7-001`
- Status: Proposed
- Scope: D10/D50/D100 scale experiments.
- Goal: Train selected core method once over each nested subset at seed 42.
- Exit criterion: Phase 7 run exit: all three token totals match manifest and results are labeled single-seed.

## Current-state evidence

- `docs/EXPERIMENT_PROTOCOL.md` exists and supplies the research baseline.
- `docs/DATA_CARD.md` exists and supplies the research baseline.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE7.md`, `docs/EXPERIMENT_PROTOCOL.md`, `docs/DATA_CARD.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P6-003`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: No seed variance can be inferred from three scale points.
- Non-goals: changing frozen model, data revisions, token budgets or selection thresholds; implementing downstream work items.

## Dependency-ordered strategy

1. Verify dependency outputs and frozen contracts; stop and record any mismatch in `docs/DECISIONS.md` before changing research settings.
2. Add the smallest module/config interfaces listed below and focused correctness fixtures.
3. Produce the run/data artifact only after its validation gates pass; preserve failures and provenance.
4. Re-run repository checks and inspect the resulting artifact against the exit criterion.

## File change map

| Path | State | Intended change |
|---|---|---|
| `configs/scale_matrix.yaml` | Proposed by P1-002 | Extend the schema-valid config for this experiment |
| `src/llm_flow/experiments/run.py` | Proposed by dependency | Implement or update |
| `tests/test_scale_matrix.py` | Proposed | Implement or update |
| `results/runs/D*.json` | Generated output | Produce and retain immutable artifact |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Reuse identical A10/A20 seed-42 checkpoint as D10 only if configurations match byte-for-byte; demonstrate this in a focused fixture or immutable run record.
- [ ] Run D50 and D100 with exact 49999872/99999744 tokens one pass; demonstrate this in a focused fixture or immutable run record.
- [ ] Verify same model, method, pipeline, precision and evaluation; demonstrate this in a focused fixture or immutable run record.
- [ ] Record runtime, real throughput, memory, validation and cost data; demonstrate this in a focused fixture or immutable run record.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Reuse identical A10/A20 seed-42 checkpoint as D10 only if configurations match byte-for-byte |
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
uv run pytest tests/test_scale_matrix.py -q
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- No seed variance can be inferred from three scale points.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE7.md`, `docs/EXPERIMENT_PROTOCOL.md`, `docs/DATA_CARD.md` | Checklist items 1–4, item-specific fixtures and generated artifact |
| Phase 7 exit criterion | Final two checklist items and validation commands; Phase 7 run exit: all three token totals match manifest and results are labeled single-seed. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `mle-workflow`: reproducible ML data, training and evaluation contracts.


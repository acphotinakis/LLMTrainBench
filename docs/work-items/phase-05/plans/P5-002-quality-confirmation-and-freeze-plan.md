# P5-002 P30/P31 quality confirmation and production freeze Plan

- Phase: 5
- Work item: `P5-002`
- Status: Proposed
- Scope: P30/P31 quality confirmation and production freeze.
- Goal: Run full 10M control/candidate, apply 1% loss guardrail and freeze chosen config.
- Exit criterion: Phase 5 exits with reproducible winner and committed production config.

## Current-state evidence

- `docs/EXPERIMENT_PROTOCOL.md` exists and supplies the research baseline.
- `docs/PHASE5.md` exists and supplies the research baseline.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE5.md`, `docs/BREAKDOWN.md`, `docs/EXPERIMENT_PROTOCOL.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P5-001`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: If no candidate passes, report infeasibility and do not silently relax thresholds.
- Non-goals: changing frozen model, data revisions, token budgets or selection thresholds; implementing downstream work items.

## Dependency-ordered strategy

1. Verify dependency outputs and frozen contracts; stop and record any mismatch in `docs/DECISIONS.md` before changing research settings.
2. Add the smallest module/config interfaces listed below and focused correctness fixtures.
3. Produce the run/data artifact only after its validation gates pass; preserve failures and provenance.
4. Re-run repository checks and inspect the resulting artifact against the exit criterion.

## File change map

| Path | State | Intended change |
|---|---|---|
| `configs/production_pipeline.yaml` | Proposed | Implement or update |
| `src/llm_flow/selection/pipeline.py` | Proposed by dependency | Implement or update |
| `tests/test_pipeline_confirmation.py` | Proposed | Implement or update |
| `results/summaries/production_selection.json` | Generated output | Produce and retain immutable artifact |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Run P30 under P00 and P31 under selected local candidate for one full 10M pass, seed 42; demonstrate this in a focused fixture or immutable run record.
- [ ] Verify candidate loss <= 1.01 times full-training control and peak process memory <43 GB; demonstrate this in a focused fixture or immutable run record.
- [ ] Apply ranking/ties only among guardrail passers and record result links; demonstrate this in a focused fixture or immutable run record.
- [ ] Write frozen production config and commit it before adaptation runs; demonstrate this in a focused fixture or immutable run record.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Run P30 under P00 and P31 under selected local candidate for one full 10M pass, seed 42 |
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
uv run pytest tests/test_pipeline_confirmation.py -q
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- If no candidate passes, report infeasibility and do not silently relax thresholds.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE5.md`, `docs/BREAKDOWN.md`, `docs/EXPERIMENT_PROTOCOL.md` | Checklist items 1–4, item-specific fixtures and generated artifact |
| Phase 5 exit criterion | Final two checklist items and validation commands; Phase 5 exits with reproducible winner and committed production config. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `mle-workflow`: reproducible ML data, training and evaluation contracts.


# P5-001 Eligible local pipeline ranking Plan

- Phase: 5
- Work item: `P5-001`
- Status: Proposed
- Scope: Eligible local pipeline ranking.
- Goal: Apply throughput, reliability, memory and tie-break rules before quality confirmation.
- Exit criterion: Ranked eligible candidate is reproducible from immutable results.

## Current-state evidence

- `docs/BREAKDOWN.md` exists and supplies the research baseline.
- `docs/METRICS.md` exists and supplies the research baseline.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE5.md`, `docs/BREAKDOWN.md`, `docs/EXPERIMENT_PROTOCOL.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P4-004`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: Quality gate is deferred to P5-002; no winner is frozen prematurely.
- Non-goals: changing frozen model, data revisions, token budgets or selection thresholds; implementing downstream work items.

## Dependency-ordered strategy

1. Verify dependency outputs and frozen contracts; stop and record any mismatch in `docs/DECISIONS.md` before changing research settings.
2. Add the smallest module/config interfaces listed below and focused correctness fixtures.
3. Produce the run/data artifact only after its validation gates pass; preserve failures and provenance.
4. Re-run repository checks and inspect the resulting artifact against the exit criterion.

## File change map

| Path | State | Intended change |
|---|---|---|
| `src/llm_flow/selection/pipeline.py` | Proposed | Implement or update |
| `tests/test_pipeline_selection.py` | Proposed | Implement or update |
| `results/summaries/pipeline_candidates.json` | Generated output | Produce and retain immutable artifact |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Exclude P03/P04/P05 and unstable local rows; demonstrate this in a focused fixture or immutable run record.
- [ ] Require three complete runs without data loss, nonfinite values or memory failure; demonstrate this in a focused fixture or immutable run record.
- [ ] Rank median real-token throughput with below-2-percent memory tie-break and stated simplicity order; demonstrate this in a focused fixture or immutable run record.
- [ ] Emit audit trail citing exact run IDs and rejected candidates; demonstrate this in a focused fixture or immutable run record.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Exclude P03/P04/P05 and unstable local rows |
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
uv run pytest tests/test_pipeline_selection.py -q
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- Quality gate is deferred to P5-002; no winner is frozen prematurely.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE5.md`, `docs/BREAKDOWN.md`, `docs/EXPERIMENT_PROTOCOL.md` | Checklist items 1–4, item-specific fixtures and generated artifact |
| Phase 5 exit criterion | Final two checklist items and validation commands; Ranked eligible candidate is reproducible from immutable results. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `benchmark-optimization-loop`: bounded baseline, one-factor variants and correctness gates.


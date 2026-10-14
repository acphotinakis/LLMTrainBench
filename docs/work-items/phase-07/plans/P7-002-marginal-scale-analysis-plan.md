# P7-002 Marginal quality and cost analysis Plan

- Phase: 7
- Work item: `P7-002`
- Status: Proposed
- Scope: Marginal quality and cost analysis.
- Goal: Quantify 10M→50M and 50M→100M gains and resource increments.
- Exit criterion: Phase 7 exits with reproducible diminishing-return table.

## Current-state evidence

- `docs/METRICS.md` exists and supplies the research baseline.
- `docs/PHASE7.md` exists and supplies the research baseline.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE7.md`, `docs/METRICS.md`, `docs/BREAKDOWN.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P7-001`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: Energy/monetary fields remain null if no measurement or invoiced rate exists.
- Non-goals: changing frozen model, data revisions, token budgets or selection thresholds; implementing downstream work items.

## Dependency-ordered strategy

1. Verify dependency outputs and frozen contracts; stop and record any mismatch in `docs/DECISIONS.md` before changing research settings.
2. Add the smallest module/config interfaces listed below and focused correctness fixtures.
3. Produce the run/data artifact only after its validation gates pass; preserve failures and provenance.
4. Re-run repository checks and inspect the resulting artifact against the exit criterion.

## File change map

| Path | State | Intended change |
|---|---|---|
| `src/llm_flow/results/scale.py` | Proposed | Implement or update |
| `tests/test_scale_analysis.py` | Proposed | Implement or update |
| `results/summaries/scale.json` | Generated output | Produce and retain immutable artifact |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Compute interval loss/perplexity change, additional tokens, hours and cost per quality gain; demonstrate this in a focused fixture or immutable run record.
- [ ] Represent zero or adverse quality gain without division error; demonstrate this in a focused fixture or immutable run record.
- [ ] Show all three raw runs and exact token provenance; demonstrate this in a focused fixture or immutable run record.
- [ ] Label all inferences descriptive single-seed; demonstrate this in a focused fixture or immutable run record.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Compute interval loss/perplexity change, additional tokens, hours and cost per quality gain |
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
uv run pytest tests/test_scale_analysis.py -q
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- Energy/monetary fields remain null if no measurement or invoiced rate exists.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE7.md`, `docs/METRICS.md`, `docs/BREAKDOWN.md` | Checklist items 1–4, item-specific fixtures and generated artifact |
| Phase 7 exit criterion | Final two checklist items and validation commands; Phase 7 exits with reproducible diminishing-return table. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `mle-workflow`: reproducible ML data, training and evaluation contracts.


# P10-002 Final analysis, recommendation and reproducibility archive Plan

- Phase: 10
- Work item: `P10-002`
- Status: Proposed
- Scope: Final analysis, recommendation and reproducibility archive.
- Goal: Write supported conclusions and package all rerun materials.
- Exit criterion: Phase 10 exits when another researcher can rebuild data and rerun core from archived materials.

## Current-state evidence

- `README.md` exists and supplies the research baseline.
- `docs/RUNBOOK.md` exists and supplies the research baseline.
- `docs/PHASE10.md` exists and supplies the research baseline.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE10.md`, `docs/BREAKDOWN.md`, `docs/ENVIRONMENT.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P10-001`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: Raw source text stays out of Git; archive location/access must be documented.
- Non-goals: changing frozen model, data revisions, token budgets or selection thresholds; implementing downstream work items.

## Dependency-ordered strategy

1. Verify dependency outputs and frozen contracts; stop and record any mismatch in `docs/DECISIONS.md` before changing research settings.
2. Add the smallest module/config interfaces listed below and focused correctness fixtures.
3. Produce the run/data artifact only after its validation gates pass; preserve failures and provenance.
4. Re-run repository checks and inspect the resulting artifact against the exit criterion.

## File change map

| Path | State | Intended change |
|---|---|---|
| `docs/FINAL_REPORT.md` | Proposed | Implement or update |
| `docs/REPRODUCIBILITY.md` | Proposed | Implement or update |
| `results/archive/` | Generated output | Produce and retain immutable artifact |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Report pipeline, adaptation, scale, memory, quality, runtime and cost comparisons; demonstrate this in a focused fixture or immutable run record.
- [ ] State limitations: one Mac, single-seed scale, contamination and short budgets; demonstrate this in a focused fixture or immutable run record.
- [ ] Give limited-compute recommendation tied to measured guardrails; demonstrate this in a focused fixture or immutable run record.
- [ ] Archive configs, lock, manifest/checksums, code commit, logs, checkpoints/adapters, raw evaluation outputs and plots; demonstrate this in a focused fixture or immutable run record.
- [ ] Document rebuild/rerun steps and audit archive links/digests; demonstrate this in a focused fixture or immutable run record.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Report pipeline, adaptation, scale, memory, quality, runtime and cost comparisons |
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
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- Raw source text stays out of Git; archive location/access must be documented.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE10.md`, `docs/BREAKDOWN.md`, `docs/ENVIRONMENT.md` | Checklist items 1–5, item-specific fixtures and generated artifact |
| Phase 10 exit criterion | Final two checklist items and validation commands; Phase 10 exits when another researcher can rebuild data and rerun core from archived materials. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `mle-workflow`: reproducible ML data, training and evaluation contracts.


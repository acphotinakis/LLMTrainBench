# P9-002 HF export and three-prompt parity gate Plan

- Phase: 9
- Work item: `P9-002`
- Status: Proposed
- Scope: HF export and three-prompt parity gate.
- Goal: Export final MLX checkpoints and block benchmarks on logit mismatch.
- Exit criterion: Every benchmark-eligible export passes parity gate.

## Current-state evidence

- `docs/PHASE9.md` exists and supplies the research baseline.
- `pyproject.toml` exists and supplies the research baseline.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE9.md`, `docs/BREAKDOWN.md`, `docs/EXPERIMENT_PROTOCOL.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P9-001`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: Export may need precision-preserving conversion; do not relax threshold.
- Non-goals: changing frozen model, data revisions, token budgets or selection thresholds; implementing downstream work items.

## Dependency-ordered strategy

1. Verify dependency outputs and frozen contracts; stop and record any mismatch in `docs/DECISIONS.md` before changing research settings.
2. Add the smallest module/config interfaces listed below and focused correctness fixtures.
3. Produce the run/data artifact only after its validation gates pass; preserve failures and provenance.
4. Re-run repository checks and inspect the resulting artifact against the exit criterion.

## File change map

| Path | State | Intended change |
|---|---|---|
| `src/llm_flow/checkpoints/export_hf.py` | Proposed | Implement or update |
| `src/llm_flow/checkpoints/compare_logits.py` | Proposed | Implement or update |
| `tests/test_export_parity.py` | Proposed | Implement or update |
| `results/evaluation/export_parity.json` | Generated output | Produce and retain immutable artifact |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Export full and merged-adapter checkpoints to HF-compatible weights without changing tokenizer revision; demonstrate this in a focused fixture or immutable run record.
- [ ] Define and freeze three test prompts before comparison; demonstrate this in a focused fixture or immutable run record.
- [ ] Compare full logits for same prompts with maximum absolute delta <=1e-3; demonstrate this in a focused fixture or immutable run record.
- [ ] Record export checksum and reject missing tensor, shape or parity failures; demonstrate this in a focused fixture or immutable run record.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Export full and merged-adapter checkpoints to HF-compatible weights without changing tokenizer revision |
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
uv run pytest tests/test_export_parity.py -q
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- Export may need precision-preserving conversion; do not relax threshold.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE9.md`, `docs/BREAKDOWN.md`, `docs/EXPERIMENT_PROTOCOL.md` | Checklist items 1–4, item-specific fixtures and generated artifact |
| Phase 9 exit criterion | Final two checklist items and validation commands; Every benchmark-eligible export passes parity gate. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `mle-workflow`: reproducible ML data, training and evaluation contracts.


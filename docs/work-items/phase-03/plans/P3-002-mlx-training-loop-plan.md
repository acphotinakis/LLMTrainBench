# P3-002 MLX full-parameter training loop Plan

- Phase: 3
- Work item: `P3-002`
- Status: Proposed
- Scope: MLX full-parameter training loop.
- Goal: Implement frozen optimizer, schedule, accumulation and exact-token one-pass training.
- Exit criterion: Full-training loop produces finite loss and exact token/update accounting.

## Current-state evidence

- `configs/core.yaml` exists and supplies the configuration baseline.
- `pyproject.toml` exists and supplies the research baseline.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE3.md`, `docs/BREAKDOWN.md`, `docs/EXPERIMENT_PROTOCOL.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P2-003`, `P3-001`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: Verify MLX-LM 0.32.0 API against installed package before coding; avoid hidden defaults.
- Non-goals: changing frozen model, data revisions, token budgets or selection thresholds; implementing downstream work items.

## Dependency-ordered strategy

1. Verify dependency outputs and frozen contracts; stop and record any mismatch in `docs/DECISIONS.md` before changing research settings.
2. Add the smallest module/config interfaces listed below and focused correctness fixtures.
3. Produce the run/data artifact only after its validation gates pass; preserve failures and provenance.
4. Re-run repository checks and inspect the resulting artifact against the exit criterion.

## File change map

| Path | State | Intended change |
|---|---|---|
| `src/llm_flow/train.py` | Proposed | Implement or update |
| `src/llm_flow/training/optimizer.py` | Proposed | Implement or update |
| `src/llm_flow/training/loader.py` | Proposed | Implement or update |
| `tests/test_training.py` | Proposed | Implement or update |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Load pinned Qwen revision in bfloat16 and assert tokenizer EOS; demonstrate this in a focused fixture or immutable run record.
- [ ] Train full parameters with AdamW 0.9/0.95/1e-8, decay 0.1 and norm clip 1.0; demonstrate this in a focused fixture or immutable run record.
- [ ] Use microbatch 1, accumulation 8, 100-update warmup and cosine 2e-5 to 2e-6; demonstrate this in a focused fixture or immutable run record.
- [ ] Flush partial final accumulation and prove one-pass exact input tokens; demonstrate this in a focused fixture or immutable run record.
- [ ] Fail safely on NaN/Inf, data loss or 43 GB memory breach; demonstrate this in a focused fixture or immutable run record.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Load pinned Qwen revision in bfloat16 and assert tokenizer EOS |
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
uv run pytest tests/test_training.py -q
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- Verify MLX-LM 0.32.0 API against installed package before coding; avoid hidden defaults.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE3.md`, `docs/BREAKDOWN.md`, `docs/EXPERIMENT_PROTOCOL.md` | Checklist items 1–5, item-specific fixtures and generated artifact |
| Phase 3 exit criterion | Final two checklist items and validation commands; Full-training loop produces finite loss and exact token/update accounting. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `mle-workflow`: reproducible ML data, training and evaluation contracts.


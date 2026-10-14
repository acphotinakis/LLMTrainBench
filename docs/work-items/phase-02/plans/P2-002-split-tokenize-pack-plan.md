# P2-002 Hash split, tokenization and packed products Plan

- Phase: 2
- Work item: `P2-002`
- Status: Proposed
- Scope: Hash split, tokenization and packed products.
- Goal: Build disjoint ordered partitions and exact nested training/validation products.
- Exit criterion: All exact token totals, sequence lengths, EOS boundaries and split disjointness pass.

## Current-state evidence

- `configs/core.yaml` exists and supplies the configuration baseline.
- `src/llm_flow/config.py` exists and supplies the configuration baseline.
- `src/llm_flow/config.py` currently implements strict core configuration loading; the other modules named below are proposed unless identified as a dependency output.
- Governing contracts: `docs/PHASE2.md`, `docs/BREAKDOWN.md`, `docs/DATA_CARD.md`. `docs/BREAKDOWN.md` has priority over phase navigation.

## Dependencies, assumptions, decisions and non-goals

- Depends on: `P2-001`.
- Assumption: upstream work items produce their stated artifacts and immutable evidence before this item begins.
- Execution constraint or unresolved decision: Spill sortable keys and packed arrays to disk; halt on insufficient source data or disk.
- Non-goals: changing frozen model, data revisions, token budgets or selection thresholds; implementing downstream work items.

## Dependency-ordered strategy

1. Verify dependency outputs and frozen contracts; stop and record any mismatch in `docs/DECISIONS.md` before changing research settings.
2. Add the smallest module/config interfaces listed below and focused correctness fixtures.
3. Produce the run/data artifact only after its validation gates pass; preserve failures and provenance.
4. Re-run repository checks and inspect the resulting artifact against the exit criterion.

## File change map

| Path | State | Intended change |
|---|---|---|
| `src/llm_flow/data/build.py` | Proposed | Implement or update |
| `src/llm_flow/data/pack.py` | Proposed | Implement or update |
| `configs/data.yaml` | Proposed by P1-002 | Extend the schema-valid config for this experiment |
| `tests/test_data_split_pack.py` | Proposed | Implement or update |
| `docs/RUNBOOK.md` | Existing | Update command contract only when this item's CLI is implemented |

## Atomic implementation checklist

- [ ] Compute SHA-256 split/order keys exactly and write disjoint ID lists; demonstrate this in a focused fixture or immutable run record.
- [ ] Assert pinned tokenizer revision, vocabulary and EOS 151643 at runtime; demonstrate this in a focused fixture or immutable run record.
- [ ] Tokenize without BOS, append one EOS per document and pack 1024-token sequences; demonstrate this in a focused fixture or immutable run record.
- [ ] Emit online manifests, offline arrays and Arrow packs with exact 9765/48828/97656/1000 sequence counts; demonstrate this in a focused fixture or immutable run record.
- [ ] Prove training prefixes byte-for-byte nested and validation excluded; demonstrate this in a focused fixture or immutable run record.
- [ ] Update `docs/RUNBOOK.md` with actual invocation and artifact locations; verify it matches the implemented interface.
- [ ] Run the commands below and inspect the item-specific artifact against the exit criterion.

## Test matrix

| Case | Fixture or run | Expected observation |
|---|---|---|
| Success | Canonical pinned config and valid dependency artifacts | Compute SHA-256 split/order keys exactly and write disjoint ID lists |
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
uv run pytest tests/test_data_split_pack.py -q
uv run pytest -q
```

Item-specific CLI commands are to be added to `docs/RUNBOOK.md` when implemented; the current runbook's `src.*` commands are interface contracts, not executable evidence.

## Risks, containment and rollback

- Spill sortable keys and packed arrays to disk; halt on insufficient source data or disk.
- Keep generated artifacts immutable and keyed by run/build ID. On failure, retain logs, correct the implementation, and create a new ID; do not overwrite prior evidence.
- Revert only this item's proposed code/config changes if its gate fails; preserve upstream data and runs.

## Requirement and exit-criterion traceability

| Source requirement | Planned evidence |
|---|---|
| `docs/PHASE2.md`, `docs/BREAKDOWN.md`, `docs/DATA_CARD.md` | Checklist items 1–5, item-specific fixtures and generated artifact |
| Phase 2 exit criterion | Final two checklist items and validation commands; All exact token totals, sequence lengths, EOS boundaries and split disjointness pass. |
| Frozen cross-phase decisions in `docs/BREAKDOWN.md` | Dependency check, config validation and result provenance |

## Skills used

- `llm-flow-work-router`: selected the smallest planning route and project authority order.
- `llm-flow-implementation-planner`: required evidence, dependency, test and traceability structure.
- `mle-workflow`: reproducible ML data, training and evaluation contracts.


# P1-001 Core Configuration Scaffold Plan

- Phase: 1
- Work item: `P1-001`
- Status: Complete
- Scope: Python package metadata, one canonical core configuration, strict configuration loading, and focused tests
- Goal: Establish a reproducible Python 3.12 project scaffold and prove that frozen core research values load without placeholders or implicit defaults.
- Exit criterion: The dependency lockfile exists, the canonical YAML validates, negative validation tests pass, and the documented validation command succeeds in the locked environment.

## Current State Evidence

- `docs/PHASE1.md` requires `pyproject.toml`, `uv.lock`, configuration schemas, canonical configs, and validation tests.
- `docs/ENVIRONMENT.md` freezes Python 3.12, `mlx-lm==0.32.0`, and `lm-eval==0.4.13`.
- `docs/BREAKDOWN.md` freezes model and dataset IDs and revisions, EOS ID 151643, sequence length 1,024, dataset token totals, validation size, core hardware class, and seeds.
- `docs/RUNBOOK.md` currently proposes `python -m src.config.validate configs/core.yaml`; no `src/`, `configs/`, `tests/`, `pyproject.toml`, or lockfile exists.
- The host `python3` is 3.9.6, while `uv` is available at `/opt/homebrew/bin/uv`; commands must therefore run through the locked uv environment rather than system Python.

## Dependencies and Assumptions

- `uv` may resolve and lock package metadata from package indexes; this requires network access.
- The canonical package will use a standard `src/llm_flow/` layout rather than making `src` an importable package.
- YAML is appropriate because the existing runbook and planned experiment files use `.yaml`.
- This work item validates declared configuration values only. It does not download the model or dataset, inspect tokenizer runtime metadata, capture exact hardware, or run MLX.

## Non Goals

- Dataset construction
- MLX model loading or training
- Environment-capture implementation
- Complete data, training, evaluation, and matrix schemas
- Smoke experiment `S00`

## Implementation Strategy

1. Add package and tool metadata with frozen runtime dependencies and test/lint development dependencies.
2. Write failing tests for canonical loading and invalid/missing/frozen-value cases.
3. Implement a strict typed configuration loader with no silent defaults.
4. Add the canonical YAML containing every required core value.
5. Update the runbook validation command to use the installed package module.
6. Generate the lockfile and run focused and complete quality checks.

## File Change Map

| Path | State | Change |
|---|---|---|
| `pyproject.toml` | Proposed | Project metadata, Python constraint, dependencies, pytest, Ruff, and package discovery |
| `uv.lock` | Proposed/generated | Exact dependency resolution |
| `src/llm_flow/__init__.py` | Proposed | Package marker and version |
| `src/llm_flow/config.py` | Proposed | Strict schema, YAML loading, validation, and CLI |
| `configs/core.yaml` | Proposed | Canonical frozen values |
| `tests/test_config.py` | Proposed | Success, missing-field, placeholder, and frozen-value tests |
| `docs/RUNBOOK.md` | Existing | Replace the invalid `src.config.validate` command with the implemented module command |

## Dependency Ordered Checklist

- [x] Add `pyproject.toml` with Python 3.12, `mlx-lm==0.32.0`, `lm-eval==0.4.13`, PyYAML, pytest, and Ruff; `uv lock` resolved 91 packages.
- [x] Add RED tests in `tests/test_config.py`; the focused test command failed with `ModuleNotFoundError: No module named 'llm_flow'` before implementation.
- [x] Implement `src/llm_flow/config.py` and package initialization; all strict success and negative tests pass.
- [x] Add `configs/core.yaml` with every required value explicit; the CLI reports it as valid and placeholder tests pass.
- [x] Update `docs/RUNBOOK.md` to call `uv run python -m llm_flow.config validate configs/core.yaml`; the command succeeds.
- [x] Generate `uv.lock`; `uv lock --check` succeeds.
- [x] Run Ruff and the complete test suite; Ruff is clean and 12 tests pass.

## Test Matrix

| Case | Input | Expected result |
|---|---|---|
| Canonical success | `configs/core.yaml` | Typed configuration returned; CLI exits 0 |
| Missing required field | Remove model revision | Validation error naming the field |
| Placeholder rejection | Value contains `{{MODEL_ID}}` | Validation error |
| Wrong frozen EOS | EOS 1 | Validation error |
| Wrong sequence length | 2,048 | Validation error |
| Wrong revision | Mutated model or dataset revision | Validation error |
| Invalid seed collection | Empty or duplicate seeds | Validation error |
| Unknown field | Add undeclared key | Validation error |
| Malformed YAML | Unterminated mapping | Parse error and nonzero CLI exit |

## Validation Commands

```bash
uv lock --check
uv run pytest tests/test_config.py -q
uv run ruff check src tests
uv run python -m llm_flow.config validate configs/core.yaml
uv run pytest -q
```

## Risks and Mitigations

- Dependency resolution may reveal that frozen package versions conflict with Python 3.12. Stop and record the evidence rather than changing versions silently.
- Importing ML libraries during configuration validation would make the command slow and fragile. The loader must not import MLX or `lm-eval`.
- Overly permissive YAML loading could hide typos. Reject unknown fields and implicit defaults.
- The exact Mac hardware identifier remains unresolved and is intentionally deferred to the environment-capture work item.

## Traceability

| Requirement | Checklist evidence |
|---|---|
| Dependency lockfile | Items 1 and 6 |
| Canonical configuration without placeholders | Items 3 and 4 |
| Frozen model, tokenizer, dataset, EOS, and sequence assertions | Items 2–4 |
| Package-version declarations | Items 1 and 6 |
| Validation command | Item 5 |
| Automated validation tests | Items 2, 3, and 7 |

## Skills Used

- `llm-flow-work-router`: selected the smallest project-specific skill set.
- `mle-workflow`: supplied the data/configuration contract and reproducibility lens.
- `python-patterns`: informed typed package and error-boundary design.
- `tdd-workflow`: required RED evidence before implementation.
- `python-testing`: supplied pytest negative and boundary coverage.
- `verification-loop`: defined the final lint, test, and diff gate.

# Phase 1 Finalize the Experimental Design

## Purpose

Turn the frozen research decisions into validated configuration files and a reproducible software environment. Shared values come from `BREAKDOWN.md`; exact runs come from `EXPERIMENT_PROTOCOL.md`.

## Tasks

- Create `pyproject.toml` and `uv.lock` with the versions in `ENVIRONMENT.md`.
- Create schemas for data, training, evaluation, and experiment configurations.
- Encode all frozen model, data, hardware, and training constants.
- Implement environment and configuration validation.
- Record any necessary change in `DECISIONS.md` before implementation continues.

## Exit Criteria

- A clean environment installs from the lockfile.
- One canonical configuration loads with no placeholder or implicit default.
- Model, tokenizer, dataset, EOS, hardware, and package-version assertions pass.

## Outputs

Dependency lockfile, configuration schemas, canonical configs, environment capture, and validation tests.

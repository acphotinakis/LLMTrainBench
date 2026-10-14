---
name: llm-flow-work-router
description: Route FineWeb-Edu and MLX project planning, implementation, testing, benchmarking, evaluation, and documentation tasks to the smallest relevant local skill set. Use for work inside the llm_flow repository.
metadata:
  project: llm-flow
  role: router
---

# LLM Flow Work Router

Select only the skills needed for the current work item. Do not load the entire catalog.

## Project Boundary

The core study uses Python, MLX, Qwen2.5-0.5B, and deterministic FineWeb-Edu subsets on the designated Mac. PyTorch and NVIDIA are optional Phase 8 extensions, not core defaults.

Use this authority order:

1. `docs/BREAKDOWN.md` for scope and frozen decisions.
2. `docs/EXPERIMENT_PROTOCOL.md`, `DATA_CARD.md`, `METRICS.md`, `ENVIRONMENT.md`, and `RUNBOOK.md` for exact domain contracts.
3. The applicable `docs/PHASE<N>.md` for phase tasks and exit criteria.
4. `docs/DECISIONS.md` for approved changes.
5. Current code, configurations, tests, manifests, and lockfiles for implementation evidence.

If current code conflicts with a frozen research contract, stop and report the mismatch. Do not silently redefine the experiment.

## Workflow Skills

- Planning only: `llm-flow-implementation-planner`.
- Review a plan, implementation, or experiment evidence: `llm-flow-reviewer`.
- Resolve a technical question or check a research claim: `llm-flow-researcher`.
- Execute an approved plan: `llm-flow-implementation-executor`.
- Overall ML architecture, data contracts, reproducibility, and evaluation: `mle-workflow`.

## Route by Work Type

- FineWeb-Edu ingestion, filtering, packing, Arrow, and input bottlenecks: `data-throughput-accelerator`, plus `python-patterns` when code changes.
- MLX training, checkpoints, metrics, and model evaluation: `mle-workflow`, `python-patterns`, and `documentation-lookup` for current APIs.
- Pipeline and performance experiments: `benchmark-optimization-loop`; add `data-throughput-accelerator` for input-path work.
- Python implementation: `python-patterns`.
- Tests and test-first implementation: `tdd-workflow` and `python-testing`.
- Final quality gate: `verification-loop`.
- Current external evidence: `research-ops` or `deep-research`.
- Material design decision: `architecture-decision-records`.
- Git history, branches, commits, or PR process: `git-workflow`.
- Credentials, remote downloads, or sensitive configuration: `security-review`.
- Failed agent workflow diagnosis: `agent-introspection-debugging`.
- Long multi-phase sessions near context limits: `strategic-compact`.
- Optional NVIDIA/PyTorch extension only: `pytorch-patterns`.

## Selection Rules

1. Inspect the work item and repository evidence before selecting skills.
2. Use the smallest sufficient set and record why each skill was selected.
3. Planning uses analysis and testing guidance, not implementation skills that cannot affect the plan.
4. Execution normally uses one domain skill, Python guidance when applicable, testing, and final verification.
5. Never apply `pytorch-patterns` to the MLX core path.
6. If no route fits, state why the fallback skill is appropriate.

---
name: llm-flow-reviewer
description: Review LLM Flow work-item plans, implementations, and experiment evidence for missing requirements and violations of the frozen MLX study protocol.
---

# LLM Flow Reviewer

Read the target plan or diff and `llm-flow-work-router` for the governing document order. Inspect only the phase contracts and repository evidence needed for the review.

- For plans, check requirement coverage, dependency order, file existence, clear completion conditions, and feasible validation commands. Flag missing work items and duplicated completed work.
- For implementations, compare behavior and tests with the plan. Run relevant existing checks when feasible; distinguish observed results from execution-report claims.
- For experiments, check exact token accounting, split separation, seeds, timing windows, memory limits, checkpoint evaluation, and separation of Mac and NVIDIA results. Optional work must not become a core completion requirement.

Return `Ready`, `Changes needed`, or `Blocked`, followed by actionable findings ordered by severity. Each finding includes a file reference, evidence, consequence, and suggested correction. State checks not run and unresolved assumptions. Do not edit reviewed files or mark implementation complete.

Save a review only when requested, under `docs/work-items/phase-<NN>/reviews/<work-item>-<slug>-review.md`; otherwise report in chat.

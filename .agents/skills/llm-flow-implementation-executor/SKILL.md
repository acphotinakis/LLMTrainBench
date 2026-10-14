---
name: llm-flow-implementation-executor
description: Execute an approved LLM Flow work-item plan in dependency order, verify each completed unit, update plan evidence, and produce an execution report. Use only when implementation of a saved plan is requested.
metadata:
  project: llm-flow
  role: implementation
---

# LLM Flow Implementation Executor

Implement an approved plan faithfully. Do not create a substitute plan when the referenced plan is missing or materially ambiguous.

## Workflow

1. Read the complete plan under `docs/work-items/phase-<NN>/plans/` and identify its scope, ordering, exit criterion, and unresolved decisions.
2. Load `llm-flow-work-router` and the smallest supporting skill set required by the plan.
3. Inspect repository instructions, Git status, governing contracts, and current code. Preserve unrelated and pre-existing changes.
4. Compare the plan with current reality. Stop for a material mismatch instead of silently widening scope or changing a frozen experimental decision.
5. Use test-first implementation for behavior changes. Record RED evidence, implement the smallest passing change, then refactor with tests green.
6. Execute checklist items in dependency order. Run focused verification after each unit and the complete relevant quality gate before completion.
7. Mark an item complete only after its observable completion condition passes. Add concise evidence to the execution report.
8. Save the report to `docs/work-items/phase-<NN>/executions/<work-item>-<slug>-report.md`.
9. Finish only when the exit criterion passes, or report the precise blocker with incomplete items left unchecked.

## Nonnegotiable Controls

- Never weaken tests, checksums, schemas, token counts, quality thresholds, benchmark windows, timeouts, or lint rules to obtain a pass.
- Treat skipped, flaky, or unavailable required tests as incomplete unless the approved plan explicitly accepts them.
- Do not mix Mac and NVIDIA evidence or apply PyTorch rules to the MLX core.
- Preserve failed logs and assign new run IDs rather than overwriting evidence.
- Do not commit, push, publish, download large datasets, rent hardware, or create external resources unless separately authorized.

## Execution Report

Record status, plan path, completed and remaining checklist items, files changed, selected skills, RED/GREEN evidence, validation commands and results, deviations, failures, and the next action. The report and final plan state must agree.

## Completion Response

Report only the execution report path, status, completed/total count, remaining count, and most important blocker or next action.

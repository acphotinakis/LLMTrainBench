---
name: llm-flow-implementation-planner
description: Create evidence-based implementation plans for a defined LLM Flow phase work item without changing product code. Use before implementing data, MLX training, benchmarking, evaluation, or project infrastructure work.
metadata:
  project: llm-flow
  role: planning
---

# LLM Flow Implementation Planner

Produce an implementation-ready plan grounded in current repository evidence. This skill plans only and must not modify product code, tests, configuration, or dependencies.

## Workflow

1. Load `llm-flow-work-router` and select the smallest relevant supporting skill set.
2. Inspect repository instructions, both Git working-tree states if more than one repository exists, and the requested scope.
3. Read `docs/BREAKDOWN.md`, the applicable phase document, and every specialized contract governing the work item.
4. Inspect actual source, tests, configurations, manifests, dependency files, and CI. Distinguish existing files from proposed files.
5. Resolve documentation contradictions explicitly. Record an assumption only when evidence cannot resolve the issue.
6. Write the plan to `docs/work-items/phase-<NN>/plans/<work-item>-<slug>-plan.md` unless the user supplies another repository-local path.
7. Re-read the saved plan and confirm every outcome and phase exit criterion is traceable to checklist items and validation commands.

## Required Plan Structure

The plan contains:

1. Title, phase, work-item ID, status `Proposed`, scope, goal, and exit criterion.
2. Current-state evidence with repository-relative paths and relevant symbols.
3. Dependencies, assumptions, decisions needed, and explicit non-goals.
4. A dependency-ordered implementation strategy.
5. A file-by-file map of proposed additions and edits.
6. Atomic Markdown checkboxes. Each item names its target and observable completion condition.
7. A test matrix covering success, failure, boundary, determinism, malformed input, and resource limits when applicable.
8. Exact validation commands derived from repository tooling; never invent an unavailable command.
9. Risks, mitigations, rollback, or containment.
10. Requirement and exit-criterion traceability.
11. A `Skills used` section explaining each selected skill's contribution.

Avoid vague items such as “add tests.” Do not present proposed paths as existing files. Keep tasks small enough to implement and verify independently.

## Completion Response

Report the saved plan path, selected skills, material uncertainties, and confirmation that no implementation files changed.

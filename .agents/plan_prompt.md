Use the native skill tool to load `llm-flow-implementation-planner`.

Create an implementation plan for the work item below. This is planning only: inspect the repository, documentation, code, tests, configurations, manifests, dependency files, and CI, but do not modify implementation files.

## Required Inputs

- Repository root: `.`
- Phase ID: `{{PHASE_ID}}`
- Work-item ID: `{{WORK_ITEM_ID}}`
- Phase brief: `docs/PHASE{{PHASE_NUMBER}}.md`
- Plan output: `docs/work-items/phase-{{PHASE_NUMBER_PADDED}}/plans/{{WORK_ITEM_ID}}-{{SLUG}}-plan.md`

Replace every placeholder before using this prompt.

## Work-item Details

{{WORK_ITEM_DETAILS}}

## Requirements

- Follow the planner skill completely and load `llm-flow-work-router`.
- Read `docs/BREAKDOWN.md`, the phase brief, and all specialized contracts governing this work item.
- Verify proposals against current source, tests, configuration, manifests, dependencies, and CI rather than planning from prose alone.
- Use the smallest relevant supporting skill set and record every selected skill and its purpose.
- Distinguish existing files from proposed files.
- Include dependency-ordered atomic checklists, an exact test matrix, runnable validation commands, and exit-criterion traceability.
- Do not change code, tests, configuration, dependency files, or frozen research decisions.
- Re-read the saved plan and confirm it exists before reporting completion.

When finished, report only the plan path, skills selected, important uncertainties or blockers, and confirmation that no implementation files changed.

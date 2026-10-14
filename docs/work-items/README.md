# Remaining work items, Phases 1–10

`P1-001` is complete: see [its plan](phase-01/plans/P1-001-core-config-scaffold-plan.md) and [execution report](phase-01/executions/P1-001-core-config-scaffold-report.md). Its lockfile, core YAML and strict loader are the only implemented study components in the current tree. All rows below are **Proposed**. An optional row is an extension and does not block core completion.

| Item | Work and plan | Depends on | Acceptance criterion | Track |
|---|---|---|---|---|
| P1-002 | [Runtime environment and experiment schemas](phase-01/plans/P1-002-runtime-environment-and-schemas-plan.md) | P1-001 | Phase 1 exits when the locked environment installs, runtime assertions pass and all canonical configurations load. | Core |
| P2-001 | [Pinned source selection and exact deduplication](phase-02/plans/P2-001-source-selection-and-dedup-plan.md) | P1-002 | Selected documents and rejection counts are reproducible from the pinned source. | Core |
| P2-002 | [Hash split, tokenization and packed products](phase-02/plans/P2-002-split-tokenize-pack-plan.md) | P2-001 | All exact token totals, sequence lengths, EOS boundaries and split disjointness pass. | Core |
| P2-003 | [Manifest, checksums and rebuild verification](phase-02/plans/P2-003-manifest-checksums-and-rebuild-plan.md) | P2-002 | Phase 2 exits with complete checksums, exact counts and matching rebuild content. | Core |
| P3-001 | [Structured metrics and run provenance](phase-03/plans/P3-001-metrics-and-run-provenance-plan.md) | P1-002, P2-003 | Logger and schema reject missing fields, duplicate IDs and nonfinite metrics. | Core |
| P3-002 | [MLX full-parameter training loop](phase-03/plans/P3-002-mlx-training-loop-plan.md) | P2-003, P3-001 | Full-training loop produces finite loss and exact token/update accounting. | Core |
| P3-003 | [Checkpoint, reload and resume verification](phase-03/plans/P3-003-checkpoint-resume-plan.md) | P3-002 | S00-compatible checkpoint reload and failure cases pass. | Core |
| P3-004 | [Unchanged-model evaluation and S00 readiness gate](phase-03/plans/P3-004-validation-and-smoke-plan.md) | P3-003 | S00 and unchanged-model evaluation pass and readiness gate is documented. | Core |
| P3-005 | [P00 three-replicate control baseline](phase-03/plans/P3-005-p00-baseline-plan.md) | P3-004 | Phase 3 exits with three valid P00 records, all fields and finite values. | Core |
| P4-001 | [P01/P02 tokenization and packing comparisons](phase-04/plans/P4-001-tokenization-and-packing-benchmarks-plan.md) | P3-005 | P01 and P02 have three valid replicates or documented feasibility failures. | Core |
| P4-002 | [P03/P04/P05 diagnostic runs](phase-04/plans/P4-002-remote-and-cache-diagnostics-plan.md) | P4-001 | Each diagnostic row has required repetitions or documented feasibility failure, with cache-state provenance. | Core |
| P4-003 | [P10–P22 worker and prefetch matrix](phase-04/plans/P4-003-worker-prefetch-matrix-plan.md) | P4-001 | Every row has three valid replicates or documented feasibility failure and factors are isolated. | Core |
| P4-004 | [Pipeline result validation and replicate summaries](phase-04/plans/P4-004-pipeline-results-validation-plan.md) | P4-002, P4-003 | Phase 4 exits with complete validated matrix or explicit feasibility failures. | Core |
| P5-001 | [Eligible local pipeline ranking](phase-05/plans/P5-001-candidate-ranking-plan.md) | P4-004 | Ranked eligible candidate is reproducible from immutable results. | Core |
| P5-002 | [P30/P31 quality confirmation and production freeze](phase-05/plans/P5-002-quality-confirmation-and-freeze-plan.md) | P5-001 | Phase 5 exits with reproducible winner and committed production config. | Core |
| P6-001 | [Frozen LoRA implementation](phase-06/plans/P6-001-lora-method-plan.md) | P5-002 | LoRA smoke has finite loss and parameter assertions pass. | Core |
| P6-002 | [A00/A10/A20 core adaptation runs](phase-06/plans/P6-002-core-adaptation-runs-plan.md) | P6-001, P3-004 | Both required methods have three valid seed results and equal training/evaluation inputs. | Core |
| P6-003 | [Core adaptation method selection](phase-06/plans/P6-003-method-selection-plan.md) | P6-002 | Phase 6 exits with deterministic winner derived only from valid core rows. | Core |
| P6-004 | [Optional A30 MLX QLoRA extension](phase-06/plans/P6-004-optional-qlora-plan.md) | P6-001, P6-002 | Optional extension is either fully gated and reported or marked not attempted/infeasible. | Optional |
| P7-001 | [D10/D50/D100 scale experiments](phase-07/plans/P7-001-scale-runs-plan.md) | P6-003 | Phase 7 run exit: all three token totals match manifest and results are labeled single-seed. | Core |
| P7-002 | [Marginal quality and cost analysis](phase-07/plans/P7-002-marginal-scale-analysis-plan.md) | P7-001 | Phase 7 exits with reproducible diminishing-return table. | Core |
| P8-001 | [Optional H10 one-GPU NVIDIA replication](phase-08/plans/P8-001-optional-nvidia-replication-plan.md) | P10-002 | Optional H10 has a complete predefined comparison or is marked not attempted. | Optional |
| P8-002 | [Optional H20 one/two-GPU DDP scaling](phase-08/plans/P8-002-optional-two-gpu-ddp-plan.md) | P8-001 | Optional H20 has comparable windows and explicit efficiency or is marked not attempted. | Optional |
| P9-001 | [Fixed validation for every final checkpoint](phase-09/plans/P9-001-fixed-validation-evaluation-plan.md) | P3-004, P6-002, P7-001 | Every reported checkpoint has comparable loss/perplexity on fixed inputs. | Core |
| P9-002 | [HF export and three-prompt parity gate](phase-09/plans/P9-002-export-and-logit-equivalence-plan.md) | P9-001 | Every benchmark-eligible export passes parity gate. | Core |
| P9-003 | [ARC Easy/OpenBookQA zero-shot benchmarks](phase-09/plans/P9-003-zero-shot-benchmarks-plan.md) | P9-002 | Phase 9 exits with identical settings, raw outputs and parity-verified checkpoints. | Core |
| P10-001 | [Reproducible final tables and plots](phase-10/plans/P10-001-tables-and-plots-plan.md) | P4-004, P5-002, P6-003, P7-002, P9-003 | Every figure/table resolves to run IDs and can be regenerated. | Core |
| P10-002 | [Final analysis, recommendation and reproducibility archive](phase-10/plans/P10-002-final-report-and-archive-plan.md) | P10-001 | Phase 10 exits when another researcher can rebuild data and rerun core from archived materials. | Core |

## Requirement coverage

| Phase | Required work | Work items |
|---|---|---|
| 1 | Locked environment on the designated Mac; runtime revision/EOS/package/hardware checks; explicit remaining schemas | P1-001 complete; P1-002 proposed |
| 2 | Pinned source, schema/filters/dedup; hash split/order; online/offline/Arrow products; manifest, checksums and deterministic rebuild | P2-001–P2-003 |
| 3 | Metrics and environment provenance; MLX full training; checkpoints/resume; unchanged-model evaluation and S00; three P00 replicates | P3-001–P3-005 |
| 4 | P01/P02; P03–P05 diagnostics and reboot pairs; P10–P13/P20–P22; all-run validation and summaries | P4-001–P4-004 |
| 5 | Eligible local ranking, P30/P31 quality confirmation and committed production config | P5-001–P5-002 |
| 6 | Frozen LoRA, A00/A10/A20 three-seed matrix and method selection | P6-001–P6-003 |
| 7 | D10/D50/D100 exact one-pass runs and marginal quality/cost analysis | P7-001–P7-002 |
| 8 | Mac core findings remain required; H10 NVIDIA replication and H20 DDP only if hardware and protocol amendment are available | P8-001–P8-002 optional |
| 9 | Fixed validation over all final checkpoints, HF export/logit parity, pinned zero-shot benchmarks | P9-001–P9-003 |
| 10 | Reproducible tables/plots, report, limitations, recommendation and archive | P10-001–P10-002 |

Optional QLoRA is P6-004. P9-001 evaluates any optional final checkpoints that actually pass their gate; it does not depend on P6-004. Phase 6 runs depend on the validation implementation in P3-004; P9-001 closes the all-checkpoint sweep after the core runs. Optional H10 starts after P10-002, because `docs/PHASE8.md` requires the Mac core study first.

## Execution and decision notes

- Follow `docs/BREAKDOWN.md` and the specialized contracts before phase summaries. The `src.*` commands in `docs/RUNBOOK.md` are future interface contracts; implementation work items update them when modules exist.
- Phase 2's exact global deduplication and ordering require a complete pinned-source scan before final selection. The data plans call for disk-backed staging and content checks. A manifest can list artifact digests, while `checksums.sha256` records the manifest digest; a self-digest inside the manifest would be circular.
- P1-001's declared completion does not imply the full Phase 1 exit gate. P1-002 must verify runtime values on the designated Mac.
- Current `.venv` resolves no `llm_flow` package: `uv run pytest -q` fails during import, while `PYTHONPATH=src uv run pytest -q` passes 12 tests. P1-002 must restore a clean locked installation and prove the package import without a source-path override.
- An external download, reboot block, hardware absence or infeasible run is recorded as such. No frozen threshold or experiment ID changes without a dated `docs/DECISIONS.md` entry. Failed/excluded runs remain in the immutable result set.
- The common validation commands in each plan are available today. Proposed item-specific modules, tests and generated artifacts are labelled as future work; their exact invocation is added to `docs/RUNBOOK.md` at implementation time.


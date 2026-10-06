# Project Decision Log

This log records choices that affect interpretation or reproducibility. New entries are appended; prior entries are never rewritten.

## D001 Base Model

- Date: 2026-10-05
- Status: Accepted
- Decision: Use `Qwen/Qwen2.5-0.5B` at revision `060db6499f32faf8b98477b0a26969ef7d8b9987` for both model and tokenizer.
- Reason: It is small enough for the 48 GB Mac and supported by MLX-LM.
- Consequence: Pythia and OLMo are out of scope for this study.

## D002 Dataset

- Date: 2026-10-05
- Status: Accepted
- Decision: Use `HuggingFaceFW/fineweb-edu`, `sample-10BT`, `train`, revision `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`.
- Reason: It supplies ordinary educational web text at a scale larger than the experimental budgets.
- Consequence: The project has no financial-domain claim.

## D003 Core Platform

- Date: 2026-10-05
- Status: Accepted
- Decision: Use MLX on the project's M5-series MacBook Pro with 48 GB unified memory for all core comparisons; capture its exact hardware identifier before official runs.
- Reason: This is the confirmed available platform.
- Consequence: NVIDIA results are optional replications and remain separate.

## D004 Optional Extensions

- Date: 2026-10-05
- Status: Accepted
- Decision: Treat QLoRA and two-GPU DDP as optional. Full training and LoRA are the required adaptation methods.
- Reason: QLoRA needs an additional validation gate, and identical multi-GPU hardware is not confirmed.
- Consequence: Missing optional results do not make the project incomplete.

## D005 Documentation Authority

- Date: 2026-10-05
- Status: Accepted
- Decision: `BREAKDOWN.md` is the high-level source of truth. Specialized documents own exact protocol, data, metrics, environment, and operations. Phase documents contain navigation, tasks, and exit criteria only.
- Reason: This avoids contradictory copies of frozen values.
- Consequence: A phase document must link to, rather than restate, shared settings.

## Entry Template

```text
## DNNN Short Title

- Date: YYYY-MM-DD
- Status: Proposed | Accepted | Superseded
- Decision:
- Reason:
- Consequence:
- Supersedes: DNNN or None
```

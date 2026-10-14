---
name: llm-flow-researcher
description: Resolve LLM Flow questions about MLX, FineWeb-Edu, Qwen, adaptation methods, and evaluation using primary sources and the project's pinned versions.
---

# LLM Flow Researcher

Read `llm-flow-work-router` and the relevant project contract. Define the specific claim or implementation question before searching.

Prefer official documentation, model and dataset cards, original papers, and upstream source code. For API behavior, check the project's locked release; label latest-version evidence that does not apply to that release. Distinguish MLX support from CUDA/PyTorch support.

Return a concise answer with direct source links, applicable versions, verified facts, uncertainty, and the implication for the work item. Treat paper speedups and quality results as configuration-specific evidence. Flag contradictions with frozen decisions and propose a correction without changing the experiment.

Do not edit code, dependencies, configurations, or frozen decisions. Save a research note only when requested, under `docs/research/<topic>.md`, including the date and sources. Use existing local research skills only when a broader investigation is needed.

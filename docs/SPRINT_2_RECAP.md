# Sprint 2 Recap

Prepared October 23, 2026.

This recap covers the October 21 implementation commits, from `c5c301b` through `b669dfb`, following the October 14 planning checkpoint (`8b6d105`). This is the working sprint boundary inferred from the commit history; no formal sprint dates were recorded in the repository.

## Sprint outcome

Sprint 2 moved the project from planning toward an operational language-model training pipeline. The repository now includes tools to prepare the financial text corpus, train a transformer from scratch, save and resume checkpoints, and support later fine-tuning and evaluation. The sprint also integrated broader model architectures, post-training methods, documentation, and a local interface for running the pipeline.

## Work completed

### Data preparation and tokenization

- Added scripts to download, partition, and prepare text data for training.
- Implemented streaming Parquet-to-HDF5 tokenization with batched encoding and buffered writes, avoiding the need to load the full corpus into memory.
- Configured training and validation inputs under `data/financial-english-source-corpus/preprocessed/` as `train.h5` and `val.h5`.
- Added tokenizer utilities and BPE support, plus preparation scripts for supervised fine-tuning and preference data.
- Updated dataset exclusions and removed tracked dataset artifacts during repository cleanup.

### Model training and hardware support

- Integrated classic and modern transformer implementations behind a shared model factory. Modern-model components include rotary position embeddings, RMSNorm, SwiGLU, grouped-query attention, and optional mixture-of-experts layers.
- Added named model presets and command-line configuration overrides for model size, batch size, training length, and data paths.
- Added device selection for CPU, Apple MPS, and CUDA, along with checkpoint saving and restoration.
- Included gradient accumulation, gradient checkpointing, and optional CUDA mixed precision to support different hardware and memory budgets.

### Fine-tuning, inference, and evaluation infrastructure

- Added implementations and configurations for supervised fine-tuning, reward-model training, DPO, PPO, and GRPO.
- Integrated LoRA support and inference utilities for sampling, KV caching, quantization, and speculative decoding.
- Added shared evaluation utilities, including held-out GSM8K scoring and tools for comparing post-training stages.
- Added small smoke-run configurations for exercising pipeline stages before larger experiments.

These are implemented capabilities, not evidence that every training stage or benchmark has been completed successfully on our data.

### Documentation and usability

- Added stage-by-stage documentation for data preparation, pretraining, fine-tuning, evaluation, and inference.
- Added explanations of transformer fundamentals and modern architecture features, with diagrams and practical guides.
- Integrated a Streamlit interface for configuring jobs, viewing metrics, evaluating checkpoints, and interacting with models.

## Training observations during the sprint

The local training run confirmed that the model and input tensors were on the Apple GPU (`mps:0`). Follow-up work corrected the conversion of stored `uint16` tokens to the integer dtype required by embeddings and added optional phase profiling.

In the reported batch-size-32 run, the first optimizer step took approximately 2.58 seconds and processed about 6,340 tokens per second. The first evaluation took approximately 203 seconds, explaining the long pause before the progress counter advanced. Backward computation was the largest measured training phase. These are initial diagnostic observations, not final benchmark results or evidence of model quality.

## Next sprint: compare our LLM with adapted open-source models

We plan to move forward by fine-tuning open-source language models on the same financial text data used to train our own LLM. For raw text, this adaptation is continued pretraining; supervised instruction tuning would require a corresponding instruction dataset.

We will then evaluate our LLM and the adapted open-source models together to measure their performance and see how they compare. The comparison will use a shared held-out evaluation set, consistent prompts and scoring rules, and documented training budgets. Each model will use its appropriate tokenizer while receiving the same underlying source-text splits.

The evaluation will consider domain-task quality, generation quality, training cost, inference speed, and memory use. Raw per-token losses from different tokenizers will not be treated as directly comparable. Unadapted versions of the selected open-source models should also serve as baselines so we can measure the benefit of adaptation.

Model selection, the final evaluation tasks, and comparison results remain future work. The sprint established the implementation foundation and demonstrated local training progress; it did not yet establish which model performs best.

## Commit references

| Commits | Main contribution |
|---|---|
| `c5c301b`, `aa35937`, `c905790`, `f886b9d` | Initial integration and repository/data cleanup |
| `eb57b49`, `66b6103` | Tokenizer changes |
| `dad9515`, `b699644` | Execution and data-preparation scripts |
| `24f9c2c` | Configuration infrastructure |
| `f1e933b` | Model, data-loader, inference, and post-training modules |
| `b669dfb` | Documentation, diagrams, UI, and additional training/optimizer support |

The training observations above also draw on the local run discussed during this sprint; they are identified separately from the commit-level implementation summary.

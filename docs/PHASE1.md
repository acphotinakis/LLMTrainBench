## Phase 1: Finalize the experimental design

The most important rule is:

> Change only one experimental variable at a time.

If you change the model, dataset, hardware, token budget, and training method simultaneously, you cannot determine which change caused the result.

### Basic Project Decisions

* One base pretrained model
  01. Model options. Once selected, that model remains fixed. Comparing Qwen with Pythia would be a separate model-comparison project.
     - Qwen2.5-0.5B for a modern, compact model
     - Pythia-410M for the cleanest scientific research design
     - OLMo-1B for the strongest transparency and reproducibility

  02. Base Pretrained Model
     1. Qwen/Qwen2.5-0.5B
     2. Serves as experimental vehicle b/c it's compact, 0.49 billion param causal lang model designed for post-training adaption

* One exact model revision
  01. Model weights will be pinned to a specific Git commit hash to guarantee reproducibility and prevent silent upstream updates
* One FineWeb-Edu dataset snapshot
  01. The sample/10BT subset of HuggingFaceFW/fineweb-edu
  02. This will also be locked to a specific commit hash, such as 20b2c9f0d743a587e1be1cc836d0ea084fd662d4
* A sequence length, initially 1, 024 tokens
  01. Strictly locked at 1,024 tokens for all reported comparisons
* Training subsets of 10M, 50M, and 100M tokens
  01. Deterministic, nested partitions of 10M, 50M, and 100M tokens
  02. The 10M slice validates the pipeline mechanics, while the larger slices test workload scaling
* A 95% training and 5% validation split
  01. A 95% training and 5% validation split executed strictly at the document level prior to tokenization
  02. This prevents text chunks from the same webpage from leaking across partitions
* The hardware used for each experiment
  01. Apple MacBook Pro featuring an M5 Pro chip and 48 GB of unified memory
  02. Final timed comparisons will run exclusively on this machine without combining metrics from secondary systems
* The software and library versions
  01. Explicitly locked versions for mlx, mlx-lm, mlx-tune, datasets, and lm-eval
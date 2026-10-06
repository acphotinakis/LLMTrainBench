# FineWeb Edu Continued Pretraining Project Breakdown

This project is a controlled systems study of continued pretraining for one small causal language model. It measures how data preparation, adaptation method, dataset scale, and hardware affect throughput, memory, runtime, cost, and model quality. It does not attempt to create a chatbot or a new model architecture.

`BREAKDOWN.md` is the authoritative high-level project plan. Exact run settings live in [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md), data rules in [DATA_CARD.md](DATA_CARD.md), and metric definitions in [METRICS.md](METRICS.md). The `PHASE*.md` files contain phase-specific procedures and exit criteria; they must not redefine frozen settings.

## Frozen Core Decisions

| Decision | Frozen value |
|---|---|
| Base model | `Qwen/Qwen2.5-0.5B` |
| Model and tokenizer revision | `060db6499f32faf8b98477b0a26969ef7d8b9987` |
| Dataset | `HuggingFaceFW/fineweb-edu`, configuration `sample-10BT`, split `train` |
| Dataset revision | `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9` |
| Core framework | MLX with MLX-LM on macOS |
| Core hardware | The project's Apple MacBook Pro with an M5-series chip and 48 GB unified memory; its exact hardware identifier is captured before official runs |
| Sequence length | 1,024 tokens |
| Training subsets | 9,999,360; 49,999,872; and 99,999,744 tokens |
| Validation set | 1,024,000 tokens in 1,000 packed sequences |
| Core adaptation methods | Full-parameter continued pretraining and LoRA |
| Optional extensions | MLX QLoRA; NVIDIA replication; two-GPU DDP scaling |
| Core random seeds | 17, 42, and 73 |

The model and tokenizer use the same pinned revision. Changing the model, tokenizer, dataset revision, sequence length, or core hardware creates a new study and must be recorded in `DECISIONS.md`.

## Hardware and Software Boundary

All comparisons inside one experiment group run on the same physical machine and software environment. The Mac/MLX results are the official core results.

An NVIDIA run is an optional replication and is reported as a separate hardware stratum. It may reproduce a complete comparison on one NVIDIA system, but it cannot be combined with Mac measurements to claim that a training method or pipeline is faster. Two-GPU DDP is optional and requires two identical GPUs. FSDP, tensor parallelism, and pipeline parallelism are out of scope.

QLoRA is optional. Its absence does not make the core project incomplete. If performed with MLX on the Mac, it may join the adaptation comparison. If performed only on NVIDIA, it is reported as an NVIDIA-only extension and is not ranked against Mac full training or Mac LoRA.

# Data

## Source Schema

The pinned FineWeb-Edu sample exposes the original FineWeb fields `text`, `id`, `dump`, `url`, `date`, `file_path`, `language`, `language_score`, and `token_count`. FineWeb-Edu records may also expose `score`, `int_score`, and `dataset`. The builder validates the schema before processing, requires `text` and `id`, preserves every available source field, and stops with an error if either required field is absent.

`token_count` is source metadata produced with the dataset's tokenizer. It is never used for experimental token accounting. Experimental counts always come from the pinned Qwen tokenizer.

## Exact Filtering and Normalization

For every streamed record, the builder performs these steps in order:

1. Require `text` to be a string and `id` to be a nonempty string.
2. Convert CRLF and CR line endings to LF and normalize Unicode to NFC.
3. Remove leading and trailing whitespace. Do not collapse internal whitespace or alter punctuation.
4. Reject text shorter than 200 Unicode code points.
5. Reject text containing a NUL character.
6. Reject text when Unicode replacement characters exceed 1% of code points.
7. Reject text when disallowed control characters exceed 1% of code points. LF, tab, and form feed are allowed.
8. Tokenize with the pinned Qwen tokenizer and reject documents containing fewer than 50 tokens before the separator is added.
9. Do not apply an additional `score`, `int_score`, or `language_score` threshold. The selected source is already FineWeb-Edu, and another quality filter would change the research population.

## Duplicate Handling Splitting and Ordering

The pipeline removes duplicates before splitting:

- Duplicate source IDs: keep the record with the lexicographically smallest SHA-256 digest of its normalized UTF-8 text.
- Exact duplicate normalized text: compute SHA-256 over UTF-8 normalized text and keep the record with the lexicographically smallest source ID.
- Near-duplicate detection is out of scope because FineWeb-Edu already includes upstream deduplication.

Use SHA-256 for every deterministic decision; never use Python's process-randomized `hash()`.

- Split key: `sha256("split:" + id)`. Interpret the first eight digest bytes as an unsigned big-endian integer. Remainders 0 through 94 modulo 100 are training; 95 through 99 are validation.
- Ordering key: `sha256("order:" + id)`, ascending by full hexadecimal digest, with `id` as the tie-breaker.
- Training and validation are ordered independently after splitting.

The pipeline writes `train_doc_ids.txt` and `validation_doc_ids.txt`. A test must prove their intersection is empty.

## Tokenization and Packing

Tokenize normalized text without adding a BOS token or chat template. Append exactly one `tokenizer.eos_token_id` after every document. For the pinned model, the configuration records EOS ID `151643`; runtime code must also assert that the loaded tokenizer reports this value.

Pack the resulting token stream with ordinary causal attention into non-overlapping sequences of exactly 1,024 tokens. Cross-document attention is allowed, with EOS marking each boundary. Drop the final incomplete sequence in each partition. Block-diagonal attention is not part of the core study.

Create nested training datasets by taking the first packed sequences in deterministic order:

| Name | Packed sequences | Exact tokens |
|---|---:|---:|
| `train_10m` | 9,765 | 9,999,360 |
| `train_50m` | 48,828 | 49,999,872 |
| `train_100m` | 97,656 | 99,999,744 |
| `validation` | 1,000 | 1,024,000 |

The builder continues streaming until all four targets can be created. The three training datasets must be nested byte-for-byte.

## Data Artifacts

The pipeline produces:

- `raw_selected_documents.jsonl.zst`
- `train_doc_ids.txt` and `validation_doc_ids.txt`
- Offline token arrays and packed datasets in Arrow format
- Online-tokenization input manifests containing the same ordered source documents
- `dataset_manifest.json`
- `checksums.sha256`

The manifest schema and checksum coverage are defined in `DATA_CARD.md`. Content determinism is required; byte-identical Arrow serialization is not claimed across different dependency versions.

# Phases

## Phase 1 Finalize the Experimental Design

Accept the frozen decisions in this document and create the dependency lockfile. Record any approved change in `DECISIONS.md`. Exit when the configuration validator can load one canonical experiment configuration without placeholders.

## Phase 2 Acquire and Organize FineWeb Edu

Build the deterministic documents, splits, offline token arrays, packed datasets, manifests, and checksums described above. Exit when automated tests verify schema, split disjointness, nesting, exact counts, EOS boundaries, and checksum completeness.

## Phase 3 Establish the Baseline

Evaluate the unchanged model, run a smoke test, and execute baseline `P00` from the experiment matrix. The frozen baseline is:

- Full-parameter training for the pipeline experiments
- AdamW with beta1 0.9, beta2 0.95, epsilon `1e-8`, and weight decay 0.1
- Bfloat16 model and computation
- Microbatch of one 1,024-token sequence
- Eight gradient-accumulation steps, for a normal effective batch of 8,192 tokens
- Gradient norm clipping at 1.0
- Peak learning rate `2e-5`
- Linear warmup for 100 optimizer updates, followed by cosine decay to `2e-6`
- One pass over the selected packed training subset; flush the final partial accumulation group
- Checkpoints every 250 optimizer updates and at the end
- Seed 42 for system benchmarks; seeds 17, 42, and 73 for reported quality runs

Performance benchmarks use 50 untimed warmup optimizer updates followed by 300 measured optimizer updates and three independent process runs. Training-quality experiments consume their full stated token budget.

## Phase 4 Run the Data Pipeline Experiments

Run the exact matrix in `EXPERIMENT_PROTOCOL.md`. Each pipeline experiment changes one factor while holding the model, seed, examples, sequence length, precision, training method, and hardware fixed. Remote streaming and cache observations are diagnostic and cannot win the stable local production-pipeline selection.

## Phase 5 Select the Production Pipeline

Among stable local candidates, select the configuration with the highest median real-token throughput across three runs, provided that:

- Its final validation loss after the 10M-token confirmation run is no more than 1% above the full-training control loss.
- All three benchmark runs complete without data loss, NaN/Inf values, or memory failure.
- Peak process memory remains below 43 GB, approximately 90% of installed unified memory.

If median throughput differs by less than 2%, choose lower peak memory; if still tied, choose the simpler configuration in this order: offline over online, local over remote, fewer workers, and lower prefetch depth.

## Phase 6 Compare Adaptation Methods

Use the selected production pipeline and the 10M-token subset.

### Full Parameter Training

Train every parameter with the baseline optimizer and schedule.

### LoRA

Freeze the base model, embeddings, normalization layers, and language-model head. Apply LoRA to all 24 transformer layers and these modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, and `down_proj`.

- Rank: 16
- Alpha: 8, represented in MLX-LM as scale 0.5
- Dropout: 0.05
- Optimizer: AdamW with the baseline beta, epsilon, and clipping values; weight decay 0.0
- Peak learning rate: `1e-4`
- Warmup: 100 optimizer updates
- Schedule: cosine decay to `1e-5`

### Optional QLoRA

Use the same LoRA settings over a frozen 4-bit base model:

- Quantization: MLX affine 4-bit weights
- Group size: 64
- Compute dtype: bfloat16
- Adapter parameters: bfloat16
- Quantization library: the locked MLX-LM release

QLoRA is included only after a smoke test confirms finite loss, checkpoint reload, and deterministic evaluation. It is not required for core completion.

### Training Method Selection

Select the core method with the lowest mean validation loss across seeds 17, 42, and 73, subject to peak memory below 43 GB. If mean losses differ by at most 0.01, select the method with lower median peak memory; if still tied, select the faster method. QLoRA is reported separately unless it completes the identical Mac protocol.

## Phase 7 Test Dataset Scale

Use the Phase 6 winner with the fixed production pipeline at 10M, 50M, and 100M tokens. Each run consumes exactly one pass over its nested subset. Report quality improvement, runtime, and cost per additional quality gain.

## Phase 8 Evaluate Hardware

The Mac is the only required hardware. If one NVIDIA system becomes available, repeat a complete, predefined comparison on that system using a separately pinned CUDA/PyTorch environment. Do not mix Mac and NVIDIA rows in a training-method effect estimate.

If two identical NVIDIA GPUs become available, optionally compare one GPU with two-GPU DDP using the identical model, precision, global batch size per GPU policy, and measured-step window. Report scaling efficiency as two-GPU throughput divided by twice one-GPU throughput.

## Phase 9 Evaluate Model Quality

Evaluate the unchanged model and every final checkpoint on the fixed 1,024,000-input-token validation set. Because each independently evaluated 1,024-token sequence contributes 1,023 shifted next-token targets, loss is averaged over exactly 1,023,000 scored target tokens. Perplexity is `exp(validation_loss)`.

Use `lm-eval==0.4.13` for `arc_easy` and `openbookqa` with zero few-shot examples. Score answer choices by conditional log likelihood. Report `acc` and `acc_norm`, with `acc_norm` primary. Use seed 42, batch size 1, no generation sampling, and the exact task definitions shipped in the pinned package.

MLX checkpoints must be exported to Hugging Face-compatible weights for benchmark evaluation. Before evaluation, compare logits for three fixed test prompts between the MLX checkpoint and exported checkpoint; maximum absolute logit difference must be at most `1e-3`. Evaluation runtime is not a training-performance metric.

## Phase 10 Analyze and Report

Report distributions and individual replicates, not only the best run. Combine system performance with quality and state limitations. Required comparisons include pipeline versus throughput, method versus memory and quality, scale versus quality and runtime, and optional hardware scaling.

The final outputs are reproducible datasets, scripts, configurations, structured logs, checkpoints or adapters, evaluation results, plots, a cost analysis, and a recommendation for continued pretraining under limited compute.

# Experiment Sequence

```text
Freeze model, data, framework, and hardware
        ↓
Build and validate deterministic datasets
        ↓
Run an end-to-end smoke test
        ↓
Measure the fixed baseline
        ↓
Change one data-pipeline factor at a time
        ↓
Select and freeze the production pipeline
        ↓
Compare full training and LoRA, with QLoRA optional
        ↓
Run 10M, 50M, and 100M scale experiments
        ↓
Run fixed quality evaluation
        ↓
Analyze performance, quality, memory, and cost
```

Implementation may begin with repository scaffolding and the smoke-test path. Official experiment collection may begin only after the readiness checklist in `EXPERIMENT_PROTOCOL.md` passes.

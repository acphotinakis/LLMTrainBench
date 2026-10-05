The project is a controlled study of how to continue training a small language model efficiently.

You are not trying to invent a new model or build a chatbot. You are using one existing model and FineWeb-Edu as a test system to answer:

> How do data preparation, training method, dataset size, and hardware affect training speed, memory use, cost, and model quality?

The current plan names Qwen2.5-0.5B. You could replace it with Pythia-410M or OLMo-1B, but you should choose one model before experimentation and keep it fixed.

## What continued pretraining means

FineWeb-Edu contains ordinary educational web documents. It does not contain questions, answers, or classification labels.

The model receives sequences such as:

```text
Photosynthesis is the process through which plants convert...
```

It learns by predicting the next token. The expected continuation might begin with `light` .

The model repeats this process across millions of tokens. This is called continued pretraining because the model was already pretrained once and you are continuing that process with additional text.

---

# Data

TODO

---

# Phases

---

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

---

## Phase 2: Acquire and organize FineWeb-Edu

FineWeb-Edu is far too large to use in full. You will stream documents from one official sample and create smaller experimental datasets.

The workflow will be:

```text
FineWeb-Edu sample
        ↓
Stream documents
        ↓
Remove empty or unusable records
        ↓
Split complete documents into training and validation sets
        ↓
Tokenize with the selected model’s tokenizer
        ↓
Build 10M, 50M, and 100M-token subsets
```

### Document-level splitting

Documents must be assigned to the training or validation partition before they are divided into smaller sequences.

For example:

```text
Document A → training only
Document B → training only
Document C → validation only
```

You should not place the first half of Document C in training and the second half in validation. That would allow the model to train on material closely related to its evaluation data. 

> This is because of a problem in ML known as data leakage, which occurs when you fail to separate your data by whole documents. 
> 1. if cut single document like docC in half, placing first half in train set and second half in validation set, model learns highl specific context, vocab, and style of exact webpage during its training
> 2. when you subsequently test model accuracy on second half of same webpage, it will score artificially high b/c the eval material is too closely related to what it just studied
> 3. Splitting strictly at document level presents these text chunks from same webpage from leaking across partitions, ensuring validation test remains a true measure of model's performance on unseen data

### Nested dataset subsets

The subsets should be nested:

```text
First 10M tokens ⊂ first 50M tokens ⊂ first 100M tokens
```

This means the 50M-token set contains everything in the 10M-token set plus an additional 40M tokens. This makes dataset-size comparisons easier to interpret.

### Data products

This phase should produce:

* Raw selected documents
  + Stream documents from versioned FineWeb-Edu dataset snapshot and filter out any empty or unusable records before further processing
    > To determine which documents in FineWeb-Edu are empty or unusable, inspect the raw fields as records stream in and filter them out using concrete heuristics before partitioning: 
    > * **Empty Text Fields:** Records where the `"text"` field is `None` , contains an empty string ( `""` ), or consists entirely of whitespace characters (e.g., `row["text"].strip() == ""` ).
    > * **Degenerate Document Lengths:** Documents that are too short to provide meaningful context or next-token prediction signals (e.g., records with fewer than 50–100 characters or fewer than 20–30 tokens), which often consist of fragmented headers, error messages, or copyright notices.
    > * **Corrupted or Repetitive Text:** Scraped records containing repetitive character loops, excessive punctuation artifacts, or garbled encoding/unprintable characters resulting from extraction failures.
    > * **Low Educational Quality / Classifier Scores:** FineWeb-Edu includes an educational quality score attribute in its metadata (e.g., `score` or `dump` ). You can filter out records below an explicit threshold if filtering out non-educational or low-signal web scrapes.
    > * **Missing Identifiers / Core Metadata:** Records lacking essential tracking fields (like a missing or invalid source URL / document ID), which undermines your requirement to keep an exact, auditable document identifier list for reproducibility.
    > * **Encoding Corruption:** Strings failing UTF-8 normalization or possessing high ratios of replacement glyphs (\ufffd) and unprintable control characters.
    > * **Storage Artifact:** Surviving raw records are saved as clean, un-tokenized JSON Lines (raw_selected_documents.jsonl), preserving raw text strings alongside their original schema.

* Training and validation document lists
  + Need to deterministically split complete, cleaned documents into non-overlapping partitions, assigning approx 95% of docs strictly to training list and 5% to validation list. 
  + separation must happen at document level to prevent text from same webpage from leaking across partitions
  + Standard sequence-chunking algorithms can split a single document across the train/validation boundary, allowing a model to memorize earlier paragraphs and artificially deflate validation perplexity.
    > **Deterministic Assignment:** Splitting occurs *before* tokenization and sequence packaging. Each document's persistent ID (e.g., `id` or `url` hash) is passed through a deterministic hashing function: 
    > $$\text{hash}(\text{doc\_id}) \pmod{100} < 95 \implies \text{Train}, \quad \text{otherwise} \implies \text{Validation}$$
    > **Audit Manifests:** The pipeline writes out explicit document ID lists ( `train_doc_ids.txt` and `val_doc_ids.txt` ).
    > **Non-Overlapping Verification:** An automated unit test confirms:
    > $$\text{Train IDs} \cap \text{Validation IDs} = \emptyset$$
    > This ensures that downstream 10M, 50M, and 100M subsets pull solely from the designated training document pool.

* Pretokenized datasets
  + Raw text from pretrained docs must be run through selected Qwen2.5 tokenizer offline to generate and save token IDs before any training begins
  + Pretokenization isolates data preparation from accelerator execution
    - if a gpu or unified-memory device tokenizes raw text on the fly during training, accelerator stalls on CPU-bound BPE encoding operations
  > * **Offline Processing:** The cleaned documents in the train/val splits are encoded using `Qwen/Qwen2.5-0.5B` 's official byte-level BPE tokenizer ( `AutoTokenizer.from_pretrained(..., use_fast=True)` ).
  > * **Zero-Copy Arrow Serialization:** Tokenized outputs ( `input_ids` ) are stored directly as Apache Arrow tables ( `.arrow` / `.feather` ).
  > * **Memory-Mapping ( `mmap` ):** When loaded during training runs, the dataset uses zero-copy memory mapping. The operating system pages token IDs straight from storage into RAM without Python heap allocation overhead, maximizing I/O throughput.

* Packed training sequences
  + Instead of padding independent short examples, multiple tokenized documents must be concatenated together to fill 1, 024 token sequences
  + Short docs leave significant portions of a fixed context window filled with padding tokens
    - Model performs full matrix mults and attention calculations over these pad tokens, wasting compute and skewing throughput metrics
  > * **Concatenation Scheme:** Pretokenized documents are streamed into a rolling token buffer. An explicit End-Of-Sequence token ( `<|im_end|>` or `tokenizer.eos_token_id` ) is inserted between adjacent documents: 
  > $$\dots [\text{Doc A Tokens}] \to \langle\text{eos}\rangle \to [\text{Doc B Tokens}] \to \langle\text{eos}\rangle \dots$$

  > * **Chunking to Fixed Context:** The contiguous stream is sliced into chunks of exactly 1, 024 tokens:

    > $$\text{Sequence}_i = \text{Buffer}[i \times 1024 : (i + 1) \times 1024]$$

  > * **Attention Mechanism:** Depending on whether cross-document contamination is evaluated, packed sequences are either trained with standard causal attention masks or paired with block-diagonal attention matrices (document boundaries reset attention so Document B does not attend to Document A).

* Dataset metadata
  + As documents are streamed and selected, must retain their original source IDs and any other relevant metadata
  + To guarantee auditability and forensic tracking, raw text is never decoupled from origin
  > **Preserved Schema:** Every processed record maintains a structured schema alongside tokenized arrays:
  > * `doc_id` : Unique document hash from FineWeb-Edu.
  > * `url` : Primary web address for source verification.
  > * `dump` : Common Crawl batch identifier.
  > * `educational_score` : FineWeb-Edu's classifier rating.
  > * `token_length` : Exact token count resulting from the Qwen tokenizer.

  > **Manifest Logs:** A central metadata file ( `dataset_manifest.json` ) records the total document count, character-to-token ratios, vocabulary distribution statistics, and date/time of extraction.
* Token counts
  + Must track exact number of tokens generated by tokenizer to carve out deterministic, nested experiemntal subsets of 10 million, 50 million, and 100 million tokens
  > * **Deterministic Nested Subsets:** The dataset builder enforces strict mathematical nesting:       
  > $$\mathcal{D}_{10\text{M}} \subset \mathcal{D}_{50\text{M}} \subset \mathcal{D}_{100\text{M}}$$
  
  > * 50M subset consists of the 10M subset plus 40M additional tokens, and the 100M subset consists of the 50M subset plus 50M additional tokens
  >     * **Hard Cutoff Accounting:** The build script increments a cumulative counter on packed 1, 024-token vectors:
  >     * **10M Subset:** $\lfloor 10{, }000{, }000 / 1{, }024 \rfloor = 9{, }765$ sequences ($9{, }999{, }360$ tokens).
  >     * **50M Subset:** $\lfloor 50{, }000{, }000 / 1{, }024 \rfloor = 48{, }828$ sequences ($49{, }999{, }872$ tokens)
  >     * **100M Subset:** $\lfloor 100{, }000{, }000 / 1{, }024 \rfloor = 97{, }656$ sequences ($99{, }999{, }744$ tokens).
  >     * Sequence counts are fixed and recorded in configuration headers to ensure every system configuration evaluates the exact same workload.

* Scripts capable of rebuilding every dataset
  + Entire data prep workflow must be written into version-controlled scripts so that dataset snapshots, document splits, and packed sequences can be programmatically reproduced for future experiements.
  > * No step in the data pipeline is performed by manual one-off terminal executions or undocumented GUI clicks.
  > * **CLI Parameterization:** The pipeline is implemented as executable scripts with deterministic CLI arguments:

    

```bash
    python -m src.data.build_pipeline \
        --dataset-snapshot "20b2c9f0d743a587e1be1cc836d0ea084fd662d4" \
        --tokenizer-name "Qwen/Qwen2.5-0.5B" \
        --seq-len 1024 \
        --train-ratio 0.95 \
        --output-dir "./data/processed" \
        --seed 42
```

  > * **Pipeline Checksums:** The scripts write out `sha256` checksums for all created Arrow tables and ID manifests.
  > * **Reproducibility Guarantee:** Re-running the pipeline on a clean machine pulls the identical dataset snapshot and generates bit-for-bit identical Arrow arrays, ensuring any observed throughput differences stem strictly from hardware and engine optimizations.

---

## Phase 3: Establish the baseline

The baseline is the unoptimized configuration against which later changes will be measured.

A possible baseline is:

* Selected base model
* 10M-token dataset
* On-the-fly tokenization
* Independent padded examples
* Local dataset loading
* One accelerator
* Fixed 1,024-token maximum sequence length
* Fixed effective batch size
* No special caching optimization
* One documented number of training steps

First, evaluate the unchanged model before training. Record:

* Validation loss
* Validation perplexity
* ARC Easy accuracy
* OpenBookQA accuracy

Then run the baseline training configuration and record:

* Tokens processed per second
* Time per training step
* Total runtime
* Peak memory
* CPU utilization
* Accelerator utilization
* Time spent preparing each batch
* Final validation perplexity

This establishes the reference point. Every optimization will be compared with it.

---

## Phase 4: Run the data-pipeline experiments

These experiments determine how efficiently text moves from storage into the model.

Use the 10M-token subset initially because the goal is to measure the system without paying for long training runs.

Use the same:

* Model
* Hardware
* Training examples
* Sequence length
* Number of measured steps
* Effective batch size
* Precision
* Training method

Each benchmark should have:

01. A warm-up period
02. A fixed measurement period
03. At least three repeated runs
04. Mean results and run-to-run variation

### Experiment 1: On-the-fly versus offline tokenization

#### Configuration A

Tokenize each document while training:

```text
Raw text → tokenizer → sequence → model
```

#### Configuration B

Tokenize everything before training:

```text
Raw text → tokenizer → saved token IDs
                              ↓
                         model training
```

#### Research question

Does offline tokenization prevent the model from waiting for the CPU?

#### Measurements

* Tokens per second
* Batch-preparation time
* CPU utilization
* Accelerator idle time
* Storage required for the tokenized dataset
* One-time preprocessing cost

Offline tokenization might make training faster, but you must report the time required to create the tokenized dataset.

---

### Experiment 2: Padding versus sequence packing

Documents and passages have different lengths.

Without packing, a short example might look like:

```text
[real tokens][padding][padding][padding]
```

The model still spends resources processing much of that padding.

With packing:

```text
[document A][separator][document B][separator][document C]
```

Multiple examples fill one fixed-length sequence.

#### Research question

Does sequence packing increase the percentage of useful tokens processed?

#### Measurements

* Real tokens per second
* Percentage of padding tokens
* Accelerator utilization
* Training step time
* Validation perplexity

Quality must still be checked because documents need appropriate separators and attention handling.

---

### Experiment 3: Local loading versus streaming

#### Local loading

Download the selected dataset before training and read it from local storage.

#### Streaming

Read records progressively without storing the entire source dataset locally.

#### Research question

When is streaming beneficial, and when does network or decoding latency cause the model to wait?

#### Measurements

* Tokens per second
* Time to first batch
* Storage use
* CPU utilization
* Accelerator idle time
* Batch latency
* Runtime variability

Streaming may reduce storage requirements but produce less stable timing. Final benchmark runs should not depend on an unreliable network connection unless network performance is itself being studied.

---

### Experiment 4: Cold cache versus warm cache

A cold-cache run begins without previously cached dataset blocks. A warm-cache run repeats the experiment after frequently used data has been placed in memory or operating-system caches.

#### Research question

Are apparent performance improvements caused by the pipeline or merely by cached data?

Report cold and warm measurements separately.

---

### Experiment 5: DataLoader workers and prefetching

Workers prepare upcoming batches while the accelerator processes the current batch.

Test a small, bounded set such as:

```text
Workers: 0, 2, 4, 8
Prefetch: supported low and high settings
```

Do not test every imaginable value.

#### Research question

How many workers keep the accelerator supplied without overwhelming the CPU or memory?

#### Measurements

* Tokens per second
* CPU utilization
* Memory use
* Batch wait time
* Accelerator utilization

More workers are not automatically better. Excessive parallelism may increase memory pressure and process-management overhead.

---

## Phase 5: Select the best data pipeline

After Phase 4, construct one recommended pipeline.

For example, the result might be:

```text
FineWeb-Edu documents
        ↓
Offline tokenization
        ↓
Arrow dataset stored locally
        ↓
Packed 1,024-token sequences
        ↓
Four DataLoader workers
        ↓
Prefetched batches
        ↓
Model training
```

This is only an example. Your measured results determine the actual configuration.

The selected pipeline becomes fixed for the model-adaptation experiments. That prevents data-pipeline differences from distorting the comparison between full training, LoRA, and QLoRA.

---

## Phase 6: Compare model-adaptation methods

These experiments compare how much of the model is updated.

All methods should receive:

* The same training corpus
* The same number of training tokens
* The same sequence length
* The same train-validation split
* The optimized data pipeline
* The same hardware
* A comparable effective batch size
* The same evaluation process

Method-specific learning rates may differ, but they must be selected during a small pilot and then documented and fixed.

## Configuration 0: Unchanged model

This model receives no additional training.

It provides the starting quality baseline.

## Configuration 1: Full-parameter continued pretraining

Every model parameter can change.

```text
Base model
    ↓
All parameters updated
```

### Expected characteristics

* Highest memory use
* Large checkpoints
* Potentially the greatest ability to adapt
* More expensive optimizer state
* Useful baseline for judging LoRA

## Configuration 2: LoRA continued pretraining

The original model weights remain frozen. Small trainable adapter matrices are added to selected layers.

```text
Frozen base model
        +
Trainable LoRA adapters
```

### Expected characteristics

* Lower memory requirements
* Much smaller saved artifacts
* Possibly different throughput
* May approach full-training quality
* Easier to run on constrained hardware

## Configuration 3: QLoRA continued pretraining

The frozen base model is stored in a quantized representation while LoRA adapters are trained.

### Expected characteristics

* Lowest model-weight memory
* May enable larger batches
* Requires a compatible quantization stack
* Most practical on supported NVIDIA hardware
* Quantization operations may affect speed

QLoRA should remain conditional. If the available environment cannot run it reliably, report that limitation rather than changing hardware midway through a comparison.

## Model-adaptation measurements

For every method, record:

* Peak memory
* Tokens per second
* Total runtime
* Final validation perplexity
* Educational benchmark accuracy
* Checkpoint or adapter size
* Number of trainable parameters
* Estimated cost

A useful result might be:

> LoRA used 45% less peak memory than full continued pretraining while finishing with validation perplexity within 3% of the full-training result.

---

## Phase 7: Test dataset scale

After identifying the best pipeline, test whether its advantages remain as the dataset grows.

Use:

* 10M tokens
* 50M tokens
* 100M tokens

Do not repeat every earlier configuration at every dataset size. That would create too many experiments.

Instead:

01. Use the best pipeline.
02. Select one principal training method, probably LoRA.
03. Train on each nested subset.
04. Keep the training procedure consistent.
05. Measure efficiency and model quality.

### Research questions

* Does throughput remain stable as the corpus grows?
* Does streaming become more useful at larger sizes?
* How much does validation perplexity improve from 10M to 50M and from 50M to 100M tokens?
* Does the additional quality justify the added runtime?

This phase examines diminishing returns. The model may improve substantially from 10M to 50M tokens but only slightly from 50M to 100M.

---

## Phase 8: Evaluate hardware

Hardware comparisons must be separated from software comparisons.

## MacBook experiments

The Mac can be used for:

* Pipeline development
* Dataset preparation
* Smoke tests
* Short training runs
* MPS-based benchmarks
* Possibly complete small experiments

Report:

* Throughput
* Runtime
* Process memory
* Unified-memory use where measurable
* CPU and accelerator utilization where available

## NVIDIA experiments

If university or rented hardware is available, run the final comparison set on one consistent NVIDIA GPU.

Report:

* Throughput
* Peak VRAM
* GPU utilization
* Runtime
* Cost

Do not compare a LoRA run on the Mac with a full-training run on NVIDIA and claim that the training method caused the difference. Both conditions must run on the same hardware.

## Optional multi-GPU experiment

If two identical NVIDIA GPUs are available:

```text
One GPU baseline
        versus
Two GPUs using DDP
```

Distributed Data Parallel places a copy of the model on each GPU and divides the batches between them. The GPUs synchronize gradients during training.

Calculate:

\[
\text{Scaling efficiency}
=
\frac{\text{two-GPU throughput}}
{2 \times \text{one-GPU throughput}}
\]

For example:

```text
One GPU: 1,000 tokens/second
Two GPUs: 1,700 tokens/second
Scaling efficiency: 1,700 / 2,000 = 85%
```

FSDP, tensor parallelism, and pipeline parallelism are outside the core project because a 0.5–1B parameter model should fit on one suitable accelerator.

---

## Phase 9: Evaluate model quality

A fast training configuration is not useful if it damages the model.

## Validation loss

Validation loss measures prediction error on FineWeb-Edu documents excluded from training. Lower is better.

## Perplexity

Perplexity is derived from validation loss and roughly measures how surprised the model is by unseen text. Lower is better.

Compare:

```text
Unchanged model
Full continued pretraining
LoRA
QLoRA
```

## Educational benchmarks

Use a small fixed set such as:

* ARC Easy
* OpenBookQA

Because these are base models, evaluate answer choices using model likelihood rather than relying entirely on conversational instruction-following.

Use the same benchmark version and evaluation settings for every model checkpoint.

---

## Phase 10: Analyze the results

The final analysis should combine systems performance with model quality.

Useful comparisons include:

* Pipeline configuration versus tokens per second
* Tokenization method versus CPU utilization
* Packing method versus padding percentage
* Training method versus peak memory
* Training method versus validation perplexity
* Corpus size versus validation perplexity
* Corpus size versus runtime
* GPU count versus throughput
* Quality improvement versus estimated cost

Avoid declaring a winner using only one metric.

A configuration could be:

* Fast but memory-intensive
* Memory-efficient but slower
* Fast but lower quality
* Slightly slower but substantially higher quality

The recommendation should account for the intended constraint.

---

# How the experiment sequence fits together

```text
01. Select one base model
        ↓
02. Create reproducible FineWeb-Edu subsets
        ↓
03. Measure the unoptimized baseline
        ↓
04. Test data-pipeline changes individually
        ↓
05. Select the best pipeline
        ↓
06. Compare full training, LoRA, and QLoRA
        ↓
07. Test 10M, 50M, and 100M-token scales
        ↓
08. Run final hardware comparisons
        ↓
09. Evaluate perplexity and benchmark quality
        ↓
10. Produce recommendations and reproducibility materials
```

## Experimental summary

| Experiment group | Variable changed | Variables held fixed | Main outcome |
|---|---|---|---|
| Tokenization | Online or offline | Model, data, hardware, steps | Throughput and CPU demand |
| Sequence construction | Padding or packing | Model, tokens, hardware | Useful-token throughput |
| Data access | Local, cached, or streamed | Model and training method | Input latency and storage tradeoff |
| DataLoader | Workers and prefetch settings | Dataset and model | Best CPU-to-accelerator delivery |
| Adaptation | Full, LoRA, or QLoRA | Data, hardware, token budget | Quality versus memory and runtime |
| Dataset scale | 10M, 50M, or 100M tokens | Model and selected pipeline | Quality improvement versus cost |
| Hardware | Mac, one NVIDIA GPU, optional two GPUs | Configuration within each comparison | Platform performance and scaling |

## Final project outputs

The completed project should produce:

* Reproducible FineWeb-Edu subsets
* Dataset-construction scripts
* A baseline training configuration
* An optimized data pipeline
* Full-training, LoRA, and possibly QLoRA results
* Training logs and structured metrics
* Model-quality results
* Performance graphs
* Hardware and cost comparisons
* A final recommendation for limited-compute continued pretraining

The trained checkpoint is one output. The main research contribution is the evidence showing why one training configuration is more efficient than another.

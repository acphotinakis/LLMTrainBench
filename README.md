# LLM Flow

LLM Flow is an MGIS 489 project exploring how a language model trained from scratch compares with open-source models adapted to the same financial text corpus. The current implementation uses Python and PyTorch, with local training on an Apple Silicon MacBook Pro with 48 GB of unified memory.

The repository includes data preparation, classic and modern transformer architectures, checkpoint management, training diagnostics, and modules for post-training and inference. Scratch-model training is underway. Adapting open-source models and completing a shared evaluation are the next steps; comparative results are not yet available.

## Project goals

1. Prepare financial text with separate training and validation splits.
2. Train our own decoder-only language model using next-token prediction.
3. Fine-tune selected open-source models on the same underlying training data.
4. Evaluate the models together on held-out tasks, comparing quality, training cost, inference speed, and memory use.

Adaptation to raw corpus text is continued pretraining; supervised instruction tuning requires instruction/response examples. Each model will use its appropriate tokenizer with the same source-text splits. Raw per-token losses from different tokenizers will not be treated as directly comparable.

## Setup

Run commands from the repository root using Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install torch numpy h5py tiktoken tqdm jaxtyping pyarrow requests
```

These dependencies cover the data preparation and scratch-training commands below. Additional features may require `datasets`, `transformers`, `pandas`, or `streamlit`. The current `pyproject.toml` does not declare all training dependencies or the `train`/`ui` extras mentioned in older guides.

## Prepare the data

The downloader targets `alwaysgood/financial-english-source-corpus` on Hugging Face. It downloads Parquet shards and partitions rows into training and validation data, using a default validation ratio of 5%.

```bash
python scripts/data_download.py
python scripts/prepare_pretrain_data.py --split train
python scripts/prepare_pretrain_data.py --split val
```

Preprocessing uses `tiktoken`'s `r50k_base` encoding, appends end-of-text markers, and writes compressed HDF5 token streams as `uint16`. The batch loader converts sampled tokens to `torch.long` for training.

```text
data/financial-english-source-corpus/
  raw/                          Downloaded Parquet shards
  partitioned/train/            Training Parquet shards
  partitioned/val/val.parquet    Validation rows
  preprocessed/train.h5         Training token stream
  preprocessed/val.h5           Validation token stream
```

The HDF5 paths are defaults in `config/config.py` and every preset in `config/presets.py`. Despite their historical names, `PILE_TRAIN` and `PILE_DEV` point to this financial corpus. The smaller presets also use it rather than TinyStories.

Preprocessing rewrites the corresponding HDF5 output. To train with existing files elsewhere, pass `--train-path` and `--dev-path`.

## Train a model

Start with the modern architecture and the `77m` preset:

```bash
python scripts/train_transformer.py --preset 77m --arch modern
```

Preset names identify configurations, not guaranteed parameter counts. With the modern architecture and vocabulary size 50,304, `77m` reports **51,455,488 parameters**. It uses eight blocks, embedding width 512, sequence length 512, batch size 24, and 20,000 optimizer steps.

For a smaller configuration:

```bash
python scripts/train_transformer.py --preset tiny --arch modern
```

Presets: `tiny`, `student`, `small`, `13m`, `77m`, and `3b`. Select one explicitly: running without a preset uses a much larger default model.

For a memory-conscious run:

```bash
python scripts/train_transformer.py --preset 77m --arch modern \
  --batch-size 32 --grad-accum 1 --grad-checkpointing
```

| Option | Behavior |
|---|---|
| `--device mps`, `cpu`, or `cuda` | Select the execution device |
| `--batch-size N` | Sequences per microbatch |
| `--grad-accum N` | Microbatches per optimizer update |
| `--grad-checkpointing` | Recompute blocks during backward to reduce saved activations |
| `--amp` | CUDA mixed precision; currently disabled on MPS and CPU |
| `--steps N` | Total optimizer-step target |
| `--eval-every N` | Evaluation interval |
| `--set KEY=VALUE` | Override a configuration field; repeat as needed |

For this single-device trainer, effective batch size is `batch-size × grad-accum`. Changing it changes the training setup. Checkpointing trades computation for lower activation memory; available memory and throughput determine whether it helps.

```bash
python scripts/train_transformer.py --help
```

### Apple GPU diagnostics and profiling

On Apple Silicon, `mps:0` means the model or tensor is on the GPU. `CUDA available: False` is expected because CUDA refers to NVIDIA hardware. The trainer prints the model, input, and target devices before the first training forward pass.

```bash
python scripts/train_transformer.py --preset 77m --arch modern \
  --batch-size 32 --grad-checkpointing --grad-accum 1 --profile
```

`--profile` reports call counts, total time, mean time, and median time separately for batch loading/transfer, forward/loss, backward, gradient clipping, optimizer updates, and evaluation.

Reports appear after periodic evaluation and final evaluation. They are cumulative and include startup warmup. GPU synchronization adds profiling overhead; omit `--profile` for normal training. This measures time rather than peak memory; the existing peak-VRAM reporter is CUDA-only and prints `N/A` on MPS.

Evaluation runs at step zero before the progress counter advances. For `77m`, periodic evaluation performs 100 training and 100 validation forward passes, which can cause a long initial pause. Final evaluation uses 200 batches per split.

### Save and resume

```bash
python scripts/train_transformer.py --preset 77m --arch modern \
  --checkpoint-every 1000 --keep-last 3

python scripts/train_transformer.py --preset 77m --arch modern --resume latest
```

Checkpoints include model weights, optimizer state, configuration, and training metadata. The `77m` preset's default final output is `models/77m.pt`; existing final output names are disambiguated. Use `--out-path`, `--checkpoint-dir`, or `--resume PATH` to control locations. Resume with the matching architecture and configuration.

## Additional capabilities and current limits

Modules and configurations are present for supervised fine-tuning, reward modeling, DPO, PPO, GRPO, LoRA, sampling, KV caching, quantization, speculative decoding, and evaluation. Their presence does not establish completed experiments or a fully connected command-line workflow.

The Streamlit interface in `ui/` is under development. Its stage definitions reference several missing trainer scripts, and its pretraining data commands include an unsupported `--out` argument. Some tutorial pages also reference older datasets, installation extras, and entry points; check those commands against the current scripts.

Existing GSM8K utilities support reasoning evaluation. Shared financial-domain evaluation tasks for the scratch-trained and adapted open-source models remain to be defined and run. No final model-quality comparison is claimed yet.

## Repository layout

```text
config/             Python defaults, presets, and configuration loading
configs/            Stage JSON configurations and smoke configurations
data_loader/        HDF5 and post-training dataset loaders
scripts/            Data preparation and available training entry points
src/models/         Classic/modern transformers and LoRA
src/post_training/  Fine-tuning, preference learning, RL, and evaluation
src/inference/      Sampling, quantization, and speculative decoding
src/tokenizer/      Tokenizer utilities and BPE
src/optim/          Optimizers and learning-rate schedules
ui/                 Streamlit interface under development
docs/               Technical guides, diagrams, and sprint recaps
data/               Local datasets, excluded from Git
models/             Training checkpoint outputs
logs/               Runtime logs
```

## Documentation

- [Sprint 2 recap](docs/SPRINT_2_RECAP.md): implementation progress and comparison plans
- [Foundations](docs/foundations/README.md): tokenization, transformers, attention, and optimization
- [Modern architecture](docs/modern/README.md): RoPE, RMSNorm, GQA, and related components
- [Data pipeline](docs/01_data_pipeline.md): pipeline background
- [Pretraining](docs/02_pretraining.md): training concepts
- [Evaluation](docs/08_evaluation.md): existing post-training evaluation approach
- [LoRA](docs/modern/lora.md): parameter-efficient adaptation implementation

This README describes the current scratch-training workflow. Older tutorial pages provide background but may need updates to match it.

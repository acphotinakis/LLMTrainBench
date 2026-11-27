# Small-model financial adaptation on Colab

These two notebooks target one NVIDIA GPU and adapt base language models to raw
financial prose using mixed-precision LoRA:

| Notebook | Model | Architecture |
|---|---|---|
| [SmolLM2-360M](../smollm2_360m_financial_lora_colab.ipynb) | `HuggingFaceTB/SmolLM2-360M` | Llama |
| [Pythia-410M](../pythia_410m_financial_lora_colab.ipynb) | `EleutherAI/pythia-410m` | GPT-NeoX |

They are similar in size to Qwen2.5-0.5B and use different model families. Ordinary
LoRA avoids 4-bit quantization dependencies for these small-model experiments.
The notebooks adapt each model's actual attention and MLP projection names.

## Run

1. Upload a notebook to Google Colab and select an A100, L4, T4, or another supported NVIDIA GPU.
2. Run installation. Restart if the installed libraries were already imported.
3. Run the remaining cells in order and authorize Drive mounting.
4. For an initial smoke run, set `MAX_STEPS=2`, `EVAL_BLOCKS=4`,
   `EVAL_EVERY=2`, and `SAVE_EVERY=2` before running the configuration cell.
5. Confirm finite forward/backward loss, successful final adapter saving, and
   generation after reloading the adapter. Then start a new longer run.

Default settings use 3,000 documents, 1,024-token blocks, effective batch 8,
and 100 optimizer steps. This processes a nominal 819,200 input
tokens, not the entire financial corpus. Inspect the reported document-pass count
and source histogram before scaling. Native BF16 support selects BF16; otherwise
the notebooks use FP16 with Trainer loss scaling. Automatic microbatch size is 4
on BF16 GPUs with at least 35 GiB, and 1 otherwise. Gradient accumulation is
calculated to preserve eight sequences per optimizer step. Override `MICRO_BATCH`
with a positive divisor of `EFFECTIVE_BATCH` if necessary.

The Qwen QLoRA notebook also supports native BF16/FP16 selection and automatic
accumulation, but conservatively retains its original microbatch size of 1 by
default. GPU allocation is not restricted by name in any of the three notebooks.

## Shared data and outputs

The first notebook saves cleaned text and split membership to
`MyDrive/llm_flow_shared/financial_sample_v1.json`. The second reuses that cache,
including its dataset revision. Run cache creation sequentially. Both notebooks
must have matching sampling settings; mismatches stop execution. To use a new
sample, choose a new shared-cache filename in both notebooks.

Each model has a separate timestamped Drive run directory containing configuration,
split hashes, token statistics, baseline/adapted loss and perplexity, checkpoints,
and a final adapter plus tokenizer. Inference reloads the exact recorded base
revision and adapter. The adapter is not a standalone full-model checkpoint.

These notebooks share documents with each other, but do not recreate the older
Qwen or scratch-model split. Align those runs separately for project-wide results.
Different tokenizers produce different token counts and block boundaries: report
within-model loss changes and use common financial tasks for cross-model ranking.
The local validation split is not an independent final test set.

## Validation limits

Notebook code is checked locally for syntax, synthetic packing and label masking,
and projection names using small Llama/GPT-NeoX model instances. Local checks do not
execute Colab installation, PEFT/TRL training, Drive access, or CUDA kernels. The
notebooks include a GPU forward/backward smoke check, but a complete Colab smoke
run remains required before claiming end-to-end success.

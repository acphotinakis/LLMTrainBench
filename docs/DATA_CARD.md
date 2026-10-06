# FineWeb Edu Experimental Data Card

This document specifies the provenance, transformation, and validation of the experimental datasets. The generated `dataset_manifest.json` is the machine-readable record of the actual build.

## Source

- Repository: `HuggingFaceFW/fineweb-edu`
- Configuration: `sample-10BT`
- Split: `train`
- Revision: `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`
- License declared by the source repository: ODC-By
- Experimental tokenizer: `Qwen/Qwen2.5-0.5B`
- Tokenizer revision: `060db6499f32faf8b98477b0a26969ef7d8b9987`

Authoritative upstream records are the [FineWeb-Edu repository](https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu/tree/87f09149ef4734204d70ed1d046ddc9ca3f2b8f9) and the [Qwen model repository](https://huggingface.co/Qwen/Qwen2.5-0.5B/tree/060db6499f32faf8b98477b0a26969ef7d8b9987).

The source is educational English web text. It may contain factual errors, bias, personal information, copyrighted text, benchmark contamination, or unsafe material inherited from web collection. The project does not treat FineWeb-Edu as ground truth and does not publish raw excerpts unnecessarily.

## Schema Contract

Required fields are `id` and `text`. Preserved source fields are `dump`, `url`, `date`, `file_path`, `language`, `language_score`, `token_count`, `score`, `int_score`, and `dataset` when present. The builder records the observed field names and types. A missing required field stops the build.

The complete normalization, filtering, deduplication, splitting, ordering, tokenization, and packing algorithms are frozen in the Data section of `BREAKDOWN.md`.

## Dataset Products

| Product | Sequences | Tokens | Purpose |
|---|---:|---:|---|
| `train_10m` | 9,765 | 9,999,360 | Pipeline confirmation and adaptation study |
| `train_50m` | 48,828 | 49,999,872 | Scale study |
| `train_100m` | 97,656 | 99,999,744 | Scale study |
| `validation` | 1,000 | 1,024,000 input tokens | Fixed held-out loss and perplexity over 1,023,000 shifted targets |

The validation set is never used for hyperparameter selection beyond the predefined guardrails. ARC Easy and OpenBookQA remain external secondary evaluations.

## Manifest Contract

`dataset_manifest.json` must contain:

- Source repository, configuration, split, and revision
- Model and tokenizer identifiers and revisions
- Tokenizer vocabulary size, EOS ID, and sequence length
- Normalization and filter-rule version
- Counts accepted and rejected by each rule
- Duplicate ID and duplicate text counts
- Train and validation document counts
- Exact packed sequence and token counts
- First and last ordering keys for each partition
- Build timestamp in UTC and build command
- Python, `datasets`, `tokenizers`, Arrow, MLX, and MLX-LM versions
- Git commit of the builder
- Relative artifact paths and SHA-256 digests

`checksums.sha256` covers the manifest, ID lists, raw selected-document archive, token arrays, and packed datasets. Paths are repository-relative and sorted bytewise.

## Required Validation Tests

- Required fields exist and have expected types.
- Every output document passed all frozen filters.
- No source ID occurs in both partitions.
- No normalized-text SHA-256 occurs in both partitions.
- Training subsets are nested byte-for-byte.
- Every stored sequence has exactly 1,024 tokens.
- Token IDs fall inside the tokenizer vocabulary.
- EOS ID matches the pinned tokenizer.
- Exact sequence and token totals match this card.
- Rebuilding with the locked environment yields the same ordered IDs, token arrays, and content checksums.

## Intended and Prohibited Uses

The products are intended only for this continued-pretraining systems study. They are not a financial dataset, instruction-tuning dataset, human-subject dataset, safety dataset, or factual reference corpus. Do not use the held-out validation data for training.

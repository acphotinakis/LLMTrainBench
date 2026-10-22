---
pretty_name: Financial English Source Corpus
language:
- en
license: other
size_categories:
- 1M<n<10M
task_categories:
- text-generation
tags:
- finance
- sec-filings
- financial-news
- earnings-calls
- fuzzy-dedup
- source-corpus
configs:
- config_name: default
  data_files:
  - split: train
    path: "train-*.parquet"
---

# Financial English Source Corpus

This dataset is a filtered, fuzzy-deduplicated English source-text corpus for
financial-domain language-model training and translation-data generation. This
version preserves the final pre-split source rows.

Derived 1280-token split versions are available separately:

- [`financial-english-source-corpus-qwen35-1280`](https://huggingface.co/datasets/alwaysgood/financial-english-source-corpus-qwen35-1280)
- [`financial-english-source-corpus-gemma4-e2b-1280`](https://huggingface.co/datasets/alwaysgood/financial-english-source-corpus-gemma4-e2b-1280)

## Dataset

Rows below are uploaded `train` rows before source-length splitting. No
validation or test split is included in this Parquet bundle. Token counts use
the qwen3.5 tokenizer used by the local preparation pipeline.

| Dataset | Source | Train rows | Source tokens | Max source tokens | Notes |
|---|---|---:|---:|---:|---|
| SEC 10-K filings | [JanosAudran/financial-reports-sec](https://huggingface.co/datasets/JanosAudran/financial-reports-sec), [PleIAs/SEC](https://huggingface.co/datasets/PleIAs/SEC) | 1,612,868 | 59,113,367 | 1,215 | 10-K text from 1993-2024. Rows were schema-normalized and fuzzy-deduplicated; table/list/exhibit fragments and high-confidence noise rows were removed. Metadata includes `year`, `cik`, `ticker`, `sic`, `sic2`, and `section`. |
| Bloomberg Financial News | [danidanou/Bloomberg_Financial_News](https://huggingface.co/datasets/danidanou/Bloomberg_Financial_News) | 397,699 | 236,686,457 | 16,823 | Bloomberg financial-news rows after filtering, fuzzy deduplication, and paragraph preservation. Metadata includes `date`, `headline`, and `link`. |
| Earnings-call transcripts | [Motley Fool scraped earnings call transcripts](https://www.kaggle.com/datasets/tpotterer/motley-fool-scraped-earnings-call-transcripts/data) | 129,827 | 13,479,273 | 353 | Earnings-call transcript rows after schema normalization, fuzzy deduplication, and noise filtering. Metadata includes `date`, `ticker`, `exchange`, and `section`. |
| FinSen financial sentiment | [eaglewhl/finsen-financial-sentiment-dataset](https://www.kaggle.com/datasets/eaglewhl/finsen-financial-sentiment-dataset) | 27,520 | 1,670,395 | 339 | Title and content rows are retained separately. Rows were schema-normalized and fuzzy-deduplicated. Metadata includes `date`, `category`, `tag`, `text_role`, and `title`. |
| FIQA corpus | [BeIR/fiqa](https://huggingface.co/datasets/BeIR/fiqa) | 31,771 | 3,615,349 | 404 | Corpus-only FIQA rows after filtering and fuzzy deduplication. |
| High-quality English sentences | [agentlans/high-quality-english-sentences](https://huggingface.co/datasets/agentlans/high-quality-english-sentences) | 100,000 | 2,701,754 | 173 | Deterministically downsampled from 164,983 final test rows to 100,000 rows with seed `20260702`; fuzzy deduplicated with the rest of the corpus. |

Total train rows: **2,299,685**. Total source tokens: **317,266,595**.

## Schema

| Column | Type | Notes |
|---|---|---|
| `source` | string | English source text after filtering, before 1280-token source splitting |
| `source_tokens` | int32 | qwen3.5 token count for `source`, computed without special tokens |
| `dataset` | string | Dataset identifier copied from metadata |
| `metadata_json` | string | Original per-row metadata serialized as compact JSON |
| `source_file` | string | Relative source file path from the local final-data directory |
| `index` | int64 | 0-based row index inside `source_file` |

## Processing

All source datasets were converted into a common source-text schema, filtered for
obvious boilerplate/noise, and fuzzy-deduplicated. Preference-pair data was
intentionally excluded from this training Parquet bundle.

This pre-split version keeps the final row boundaries before tokenizer-length
chunking. The 1280-token variant is produced from this corpus by splitting rows
that exceed 1280 qwen3.5 source tokens into sentence-boundary chunks.

| Setting | Value |
|---|---:|
| Source split | None |
| Tokenizer used for stats | qwen3.5 |
| Per-row token column | `source_tokens` |
| Uploaded shards | 23 |
| Uploaded format | Parquet |

## Loading

```python
from datasets import load_dataset

ds = load_dataset("parquet", data_files="train-*.parquet", split="train")
```

After upload to a Hugging Face dataset repository:

```python
from datasets import load_dataset

ds = load_dataset("alwaysgood/financial-english-source-corpus", split="train")
```

## Licenses and Terms

This is a derived corpus assembled from multiple upstream datasets with mixed
licenses and source terms. The dataset card therefore uses `license: other`.
Before publishing publicly, review the license and redistribution terms for each
source, especially Kaggle-hosted datasets and Motley Fool transcript content.

| Source | Upstream license or terms note |
|---|---|
| [JanosAudran/financial-reports-sec](https://huggingface.co/datasets/JanosAudran/financial-reports-sec) | Hugging Face metadata lists `apache-2.0`. |
| [PleIAs/SEC](https://huggingface.co/datasets/PleIAs/SEC) | Hugging Face metadata lists `cc0-1.0`; the upstream card should still be reviewed before redistribution. |
| [danidanou/Bloomberg_Financial_News](https://huggingface.co/datasets/danidanou/Bloomberg_Financial_News) | Hugging Face metadata lists `apache-2.0`. |
| [BeIR/fiqa](https://huggingface.co/datasets/BeIR/fiqa) | Hugging Face metadata lists `cc-by-sa-4.0`. |
| [agentlans/high-quality-english-sentences](https://huggingface.co/datasets/agentlans/high-quality-english-sentences) | Hugging Face metadata lists `odc-by`. |
| [FinSen financial sentiment](https://www.kaggle.com/datasets/eaglewhl/finsen-financial-sentiment-dataset) | Check Kaggle/source license before public redistribution. |
| [Motley Fool scraped earnings call transcripts](https://www.kaggle.com/datasets/tpotterer/motley-fool-scraped-earnings-call-transcripts/data) | Check Kaggle license and Motley Fool terms before public redistribution. |

## Quality Notes

This is intended as a high-quality English financial source corpus. The data was
fuzzy-deduplicated and aggressively cleaned to remove visible noise, boilerplate,
broken encoding artifacts, click-through prompts, transcript/video metadata,
terminal fragments, and table/list/exhibit fragments where they were not useful
as prose training examples.

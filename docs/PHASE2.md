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
  * Stream documents from versioned FineWeb-Edu dataset snapshot and filter out any empty or unusable records before further processing
    > To determine which documents in FineWeb-Edu are empty or unusable, inspect the raw fields as records stream in and filter them out using concrete heuristics before partitioning: 
    > * **Empty Text Fields:** Records where the `"text"` field is `None`, contains an empty string (`""`), or consists entirely of whitespace characters (e.g., `row["text"].strip() == ""`).
    > * **Degenerate Document Lengths:** Documents that are too short to provide meaningful context or next-token prediction signals (e.g., records with fewer than 50–100 characters or fewer than 20–30 tokens), which often consist of fragmented headers, error messages, or copyright notices.
    > * **Corrupted or Repetitive Text:** Scraped records containing repetitive character loops, excessive punctuation artifacts, or garbled encoding/unprintable characters resulting from extraction failures.
    > * **Low Educational Quality / Classifier Scores:** FineWeb-Edu includes an educational quality score attribute in its metadata (e.g., `score` or `dump`). You can filter out records below an explicit threshold if filtering out non-educational or low-signal web scrapes.
    > * **Missing Identifiers / Core Metadata:** Records lacking essential tracking fields (like a missing or invalid source URL / document ID), which undermines your requirement to keep an exact, auditable document identifier list for reproducibility.
* Training and validation document lists
* Pretokenized datasets
* Packed training sequences
* Dataset metadata
* Token counts
* Scripts capable of rebuilding every dataset

---

# Shared financial evaluation

Open [evaluate_financial_models_colab.ipynb](../evaluate_financial_models_colab.ipynb)
in a fresh Google Colab NVIDIA GPU runtime. It is self-contained and uses
lm-evaluation-harness 0.4.9 to evaluate all three saved model families, before and
after adaptation. It does not train models or modify their adapter folders.

## Required training artifacts

Finish the final save cell of each training notebook first. Each selected run
folder must contain:

```text
run_config.json
split_manifest.json
adapter/
  adapter_config.json
  adapter_model.safetensors
  tokenizer_config.json
```

The evaluation notebook searches the default Qwen, SmolLM2, and Pythia output
folders and selects the latest complete run from each. Review the printed model
IDs, revisions, and adapter paths. Set `RUN_DIRS` explicitly to compare particular
runs. It expects the same dataset revision and the 32,768-character document cap
used in the training notebooks. It refuses incomplete runs rather than evaluating
a base model under an adapted-model label.

## Pilot protocol

1. Install the evaluation packages, restarting if they were already imported.
2. Run the embedded utilities cell and mount Drive.
3. Select the completed training runs.
4. Create the frozen pilot: 20 unseen passages and 20 literal dollar-amount questions.
5. Inspect the passage/question/reference preview.
6. Run the six evaluations sequentially and inspect the exported table and samples.

The source dataset is streamed at the recorded revision. Documents whose
normalized hashes appear in any selected run's training or validation manifest
are excluded. Near duplicates, related filings, and contamination from a base
model's original pretraining are not detected. The scratch model is not included;
it needs its own harness adapter and document-level provenance checks.

The suite lives under `MyDrive/llm_flow_evaluation/suites/`. A content hash protects
it against accidental edits. Reusing it reruns the overlap audit against the newly
selected training runs. Use a new `SUITE_NAME` for different counts or questions.
Increasing to 200 passages and 100 questions expands the extraction evaluation;
it does not automatically add reasoning tasks.

## Metrics

| Metric | Interpretation |
|---|---|
| Bits per byte | Negative rolling log likelihood divided by UTF-8 bytes and ln(2); lower is better |
| QA accuracy | Whole-response match against reference answers, with numeric scale normalization; higher is better |
| Evaluation seconds | Combined harness scoring time after model loading and QA token-length checks |
| Peak allocated GiB | Peak PyTorch CUDA allocated memory during scoring; excludes allocator reservations and broader driver memory |

Bits per byte uses the same passage text across different tokenizers. All models
have the same 1,024-token context budget, but tokenization affects how much text
fits in each rolling window. It is not a tokenizer-independent architecture test.

The pilot asks for the first dollar-denominated amount in a passage and copies
the reference directly from that passage. `$1 million` and `$1,000,000` match;
`25` and `25%` do not. Verbose explanations do not count as exact answers.
This deliberately narrow task measures extraction and response-format behavior,
not broad financial reasoning. Greedy generation and no chat template are used
for every model.

All six configurations use an unquantized base with BF16 on natively supported
GPUs or FP16 otherwise. This matches precision within baseline/adapted pairs.
Qwen's QLoRA adapter therefore runs at a different base precision from its
training notebook's NF4 evaluation. Do not mix those older metrics into this
comparison. The Qwen notebook currently selects 1.5B, while SmolLM2/Pythia are
360M/410M; record that size difference in any conclusions.

## Broader questions

A new suite may contain manually reviewed questions grounded in its source
passages. For example, a passage stating cash flow rose from $20 million to
$25 million supports the question "What was the percentage increase?" with
reference `25%`. This is a schema illustration, not a corpus-derived test record.

Each custom question uses `id`, `document_id`, `context`, `question`, `answers`,
`category`, and `reviewed: true`. Its context must equal the saved source passage.
Have a person verify calculations, units, and alternate acceptable answers before
freezing the new suite. Use the same answer-scoring rules across all models.
Create and review these records before producing the new suite's freeze hash;
do not edit a frozen test after seeing model scores.

## Saved results

```text
results/<suite>_<timestamp>/
  evaluation_config.json
  comparison.csv
  comparison.json
  improvement.json
  requirements_freeze.txt
  evaluation_utils.py
  <model>_<baseline-or-adapted>/
    harness_results.json
    samples.jsonl
```

Scores and samples are written after each completed model/mode, preserving
partial results if a later evaluation fails. The notebook writes the package and
source snapshots after all evaluations finish. Keep the frozen suite alongside
the results. Sample files include source passages and answers; review the corpus
terms before redistribution. Model evaluation time is not training time or a
controlled generation-throughput benchmark.

## Validation

The implementation is also available in [src/financial_eval.py](../src/financial_eval.py).
The notebook embeds the same code so it needs no extra upload. Run local tests with:

```bash
python -m unittest discover -s tests -p test_financial_eval.py
```

Tests cover answer units, scale normalization, incomplete runs, model mismatches,
exact overlap rejection, reference/context tampering, byte-weighted aggregation,
and task definitions. They do not download models or execute the real harness/GPU
stack. A full Colab evaluation has not been performed during implementation.

References: [harness v0.4.9](https://github.com/EleutherAI/lm-evaluation-harness/tree/v0.4.9),
[task interface](https://github.com/EleutherAI/lm-evaluation-harness/blob/v0.4.9/lm_eval/api/task.py),
[Hugging Face backend](https://github.com/EleutherAI/lm-evaluation-harness/blob/v0.4.9/lm_eval/models/huggingface.py).

## Local results dashboard

Open the saved financial pilot without loading any model, downloading datasets,
or requiring a GPU. From the repository root:

```bash
python3 -m venv .venv-dashboard
source .venv-dashboard/bin/activate
python -m pip install -r requirements-dashboard.txt
python -m streamlit run ui/financial_dashboard.py
```

The dashboard defaults to
`financial_pilot_v1_20261127_213759_273737`. Use **Evaluation test** in the sidebar to select any saved test under
`llm_flow_evaluation/results/`, including nested test folders, or **All tests**
to aggregate them. Folders are discovered automatically on each app rerun. It is also available as
**Financial Results** when running the existing `ui/app.py` control panel.
The standalone viewer needs only the dependencies in `requirements-dashboard.txt`.

- **Overview:** QA accuracy, byte-weighted bits per byte, evaluation duration,
  peak allocated CUDA memory, and a downloadable filtered comparison.
- **Adaptation impact:** paired changes within a model family; QA changes use
  percentage points. Missing pairs and mismatched suites/counts are excluded.
- **Answer explorer:** search saved responses and passages, filter improvements
  or regressions, and inspect baseline/adapted outputs alongside accepted answers.
  Correctness comes from the recorded scoring output; responses are not rescored.
- **Passage scores:** individual BPB values with the source passage. Headline BPB
  weights by UTF-8 bytes rather than averaging these individual values.
- **Protocol & provenance:** evaluation settings, model/dataset revisions,
  adapter hashes, and training configurations.

Global model/configuration filters apply to every results view. An incomplete
run can still show aggregate scores; missing sample files produce warnings.
The viewer reads JSON/JSONL only and never executes saved `evaluation_utils.py`
or code strings inside harness snapshots. Time and memory describe evaluation,
not training cost. Twenty extraction questions are a pilot, not broad evidence
of financial reasoning or statistical significance.

Dashboard checks (install `pytest pytest-cov` in the dashboard environment):

```bash
python -m pytest tests/test_financial_dashboard.py -q
```

### Aggregating tests

**All tests** pools QA accuracy by question count and recomputes bits per byte
from the combined saved log likelihoods and UTF-8 byte counts. Pooled BPB is
unavailable if any contributing passage samples are missing. Evaluation seconds
are summed; peak allocated GiB is the largest observed allocation. The table
shows contributing test and suite counts, keeping model IDs and dtypes separate.
Repeated questions are repeated observations, not additional independent evidence.
Different suites and adapter checkpoints may contribute, so pooled results are
exploratory rather than the score of a single fixed checkpoint.

Adaptation deltas remain paired within each original test with matching suite
hashes and sample counts. The answer, passage, and provenance tabs each offer a
test selector; question IDs are never joined across tests. JSON/CSV exports retain
test identity or aggregate counts as appropriate. Unreadable test folders produce
warnings while other valid tests remain usable.

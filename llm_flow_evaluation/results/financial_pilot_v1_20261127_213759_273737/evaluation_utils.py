import hashlib
import csv
import json
import math
import re
import unicodedata
import gc
import time
from decimal import Decimal
from pathlib import Path


MONEY = re.compile(r"\$\s*\d[\d,]*(?:\.\d+)?(?:\s+(?:thousand|million|billion|trillion))?", re.I)


def normalize_text(text):
    return unicodedata.normalize("NFKC", text).replace("\x00", "").strip()


def normalized_hash(text):
    return hashlib.sha256(" ".join(normalize_text(text).split()).encode("utf-8")).hexdigest()


def suite_digest(suite):
    payload = json.dumps(suite, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_answer(value):
    value = " ".join(value.strip().strip('"').casefold().split())
    match = re.fullmatch(
        r"(\$)?\s*([+-]?\d[\d,]*(?:\.\d+)?)\s*(thousand|million|billion|trillion)?\s*(%)?",
        value,
    )
    if match:
        currency, number, scale, percent = match.groups()
        multiplier = {None: 1, "thousand": 10**3, "million": 10**6,
                      "billion": 10**9, "trillion": 10**12}[scale]
        number = Decimal(number.replace(",", "")) * multiplier
        return (currency or "") + format(number.normalize(), "f") + (percent or "")
    return value


def score_answer(response, answers):
    return float(canonical_answer(response) in {canonical_answer(a) for a in answers})


def load_runs(run_dirs):
    runs, excluded = [], set()
    for label, directory in run_dirs.items():
        root = Path(directory)
        adapter = root / "adapter"
        required = [root / "run_config.json", root / "split_manifest.json",
                    adapter / "adapter_config.json", adapter / "adapter_model.safetensors",
                    adapter / "tokenizer_config.json"]
        missing = [str(p) for p in required if not p.is_file()]
        if missing:
            raise ValueError(f"Incomplete run {label}: {missing}")
        config = json.loads(required[0].read_text())
        if not re.fullmatch(r"[0-9a-f]{40}", config.get("model_sha", "")):
            raise ValueError(f"Missing immutable model revision: {label}")
        adapter_config = json.loads((adapter / "adapter_config.json").read_text())
        if adapter_config.get("base_model_name_or_path") != config["MODEL_ID"]:
            raise ValueError(f"Adapter/base model mismatch: {label}")
        if config.get("MAX_DOC_CHARS") != 32768:
            raise ValueError("Overlap checking currently requires MAX_DOC_CHARS=32768 in every run.")
        manifest = json.loads(required[1].read_text())
        if set(manifest) != {"train", "eval"} or not manifest["train"]:
            raise ValueError(f"Invalid split manifest: {label}")
        for split in manifest.values():
            for row in split:
                digest = row.get("sha256", "")
                if not re.fullmatch(r"[0-9a-f]{64}", digest):
                    raise ValueError(f"Invalid document hash: {label}")
                excluded.add(digest)
        runs.append(dict(label=label, model_id=config["MODEL_ID"],
                         model_sha=config["model_sha"], dataset_id=config["DATASET_ID"],
                         dataset_sha=config["dataset_sha"], adapter=str(adapter),
                         training_config=config,
                         manifest_sha256=hashlib.sha256(required[1].read_bytes()).hexdigest(),
                         adapter_sha256=hashlib.sha256(
                             (adapter / "adapter_model.safetensors").read_bytes()).hexdigest()))
    if not runs:
        raise ValueError("At least one completed run is required.")
    if len({(r["dataset_id"], r["dataset_sha"]) for r in runs}) != 1:
        raise ValueError("Training runs use different dataset revisions; align their source data first.")
    return runs, excluded


def build_suite(rows, excluded, dataset_sha, document_count=200, question_count=20):
    if not 1 <= question_count <= document_count:
        raise ValueError("Require 1 <= question_count <= document_count.")
    documents, questions, seen = [], [], set()
    for row in rows:
        if not isinstance(row.get("source"), str):
            continue
        full = normalize_text(row["source"])
        capped = full[:32768].strip()
        digest = normalized_hash(capped)
        if digest in excluded or digest in seen or len(capped) < 80:
            continue
        seen.add(digest)
        passage = capped[:1200].strip()
        match = MONEY.search(passage)
        if not match and document_count - len(documents) <= question_count - len(questions):
            continue
        document_id = f"financial_{len(documents):04d}"
        document = dict(id=document_id, text=passage, document_sha256=digest,
                        capped_document=capped, passage_sha256=normalized_hash(passage),
                        source_label=str(row.get("dataset", "unknown")),
                        source_file=str(row.get("source_file", "")), source_index=str(row.get("index", "")))
        if len(documents) < document_count:
            documents.append(document)
            if match and len(questions) < question_count:
                questions.append(dict(
                    id=f"amount_{len(questions):04d}", document_id=document_id,
                    context=passage,
                    question="What is the first dollar-denominated amount in the passage? Copy the amount including $ and any scale word. Return only the amount.",
                    answers=[match.group(0)], category="literal_amount_extraction",
                ))
        if len(documents) == document_count and len(questions) == question_count:
            break
    if len(documents) != document_count or len(questions) != question_count:
        raise ValueError("Insufficient unseen passages with dollar amounts. Increase scan budget or choose a new suite.")
    suite = dict(schema_version=1, dataset_sha=dataset_sha, documents=documents,
                 questions=questions, purpose="pilot", reference_policy="literal_first_dollar_amount")
    audit_suite(suite, excluded)
    return suite


def audit_suite(suite, excluded):
    if suite.get("schema_version") != 1 or not suite.get("documents") or not suite.get("questions"):
        raise ValueError("Invalid or empty evaluation suite.")
    ids, hashes = set(), set()
    documents = {}
    for doc in suite["documents"]:
        if doc["id"] in ids or doc["document_sha256"] in hashes:
            raise ValueError("Duplicate evaluation document.")
        ids.add(doc["id"])
        hashes.add(doc["document_sha256"])
        if normalized_hash(doc["capped_document"]) != doc["document_sha256"]:
            raise ValueError("Document content/hash mismatch.")
        if doc["document_sha256"] in excluded:
            raise ValueError("Test document overlaps a recorded training/validation document.")
        if not doc["text"] or doc["text"] not in doc["capped_document"]:
            raise ValueError("Passage is not grounded in its source document.")
        if normalized_hash(doc["text"]) != doc["passage_sha256"]:
            raise ValueError("Passage content/hash mismatch.")
        documents[doc["id"]] = doc
    question_ids = set()
    for question in suite["questions"]:
        doc = documents.get(question["document_id"])
        if question["id"] in question_ids or doc is None or question["context"] != doc["text"]:
            raise ValueError("Invalid question ID, source, or context.")
        question_ids.add(question["id"])
        if not question["answers"] or not all(isinstance(a, str) and a.strip() for a in question["answers"]):
            raise ValueError("Reference answers are required.")
        if question.get("category") == "literal_amount_extraction":
            match = MONEY.search(question["context"])
            if not match or question["answers"] != [match.group(0)]:
                raise ValueError("Extraction reference does not match the passage.")
        elif not question.get("reviewed", False):
            raise ValueError("Custom calculation/comprehension questions require reviewed=true.")


def qa_prompt(doc):
    return f"Passage:\n{doc['context']}\n\nQuestion: {doc['question']}\nAnswer:"


def qa_results(doc, results):
    return {"acc": score_answer(results[0], doc["answers"])}


def rolling_results(doc, results):
    return {"bits_per_byte": (float(results[0]), len(doc["text"].encode("utf-8")))}


def aggregate_bpb(items):
    return -sum(ll for ll, _ in items) / (sum(count for _, count in items) * math.log(2))


def make_tasks(suite_path):
    from lm_eval.api.task import ConfigurableTask

    suite = json.loads(Path(suite_path).read_text())
    stem = Path(suite_path).parent
    text_file, qa_file = stem / "financial_text.jsonl", stem / "financial_qa.jsonl"
    for path, records in [(text_file, suite["documents"]), (qa_file, suite["questions"])]:
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    common = dict(dataset_path="json", test_split="test", num_fewshot=0)
    text = ConfigurableTask(config=dict(
        **common, task="financial_prose", dataset_kwargs={"data_files": {"test": str(text_file)}},
        output_type="loglikelihood_rolling", doc_to_text="", doc_to_target="{{text}}",
        process_results=rolling_results,
        metric_list=[dict(metric="bits_per_byte", aggregation=aggregate_bpb, higher_is_better=False)],
    ))
    qa = ConfigurableTask(config=dict(
        **common, task="financial_qa", dataset_kwargs={"data_files": {"test": str(qa_file)}},
        output_type="generate_until", doc_to_text=qa_prompt, doc_to_target=lambda d: d["answers"][0],
        process_results=qa_results,
        generation_kwargs=dict(do_sample=False, max_gen_toks=48, until=["\n"]),
        metric_list=[dict(metric="acc", aggregation="mean", higher_is_better=True)],
    ))
    return [text, qa]


def evaluate_runs(runs, suite_path, output_dir, excluded, max_length=1024):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    from lm_eval import simple_evaluate
    from lm_eval.models.huggingface import HFLM

    if not torch.cuda.is_available():
        raise RuntimeError("Select a Colab NVIDIA GPU runtime.")
    suite = json.loads(Path(suite_path).read_text())
    audit_suite(suite, excluded)
    digest = suite_digest(suite)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported(including_emulation=False) else torch.float16
    freeze = dict(suite_sha256=digest, dataset_sha=suite["dataset_sha"],
                  purpose=suite["purpose"], runs=runs, max_length=max_length,
                  dtype=str(dtype), quantization="none", gpu=torch.cuda.get_device_name(0),
                  note="Qwen QLoRA adapter evaluated on an unquantized base; differs from its notebook's NF4 baseline.")
    (output / "evaluation_config.json").write_text(json.dumps(freeze, indent=2))
    summaries = []
    for run in runs:
        if run["dataset_sha"] != suite["dataset_sha"]:
            raise ValueError("Evaluation/training dataset revision mismatch.")
        tokenizer = AutoTokenizer.from_pretrained(run["adapter"])
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        for question in suite["questions"]:
            length = len(tokenizer(qa_prompt(question), add_special_tokens=False)["input_ids"])
            if length + 48 > max_length:
                raise ValueError(f"Question {question['id']} exceeds the shared context budget for {run['label']}.")
        for mode in ("baseline", "adapted"):
            tasks = make_tasks(suite_path)
            model = wrapper = None
            try:
                model = AutoModelForCausalLM.from_pretrained(
                    run["model_id"], revision=run["model_sha"], torch_dtype=dtype,
                    device_map={"": 0}, attn_implementation="sdpa",
                )
                if max_length > model.config.max_position_embeddings:
                    raise ValueError("Evaluation context exceeds model capacity.")
                if mode == "adapted":
                    model = PeftModel.from_pretrained(model, run["adapter"], is_trainable=False)
                model.eval()
                model.config.use_cache = True
                wrapper = HFLM(pretrained=model, tokenizer=tokenizer, batch_size=1,
                               max_length=max_length, add_bos_token=False)
                torch.cuda.synchronize()
                torch.cuda.reset_peak_memory_stats()
                start = time.perf_counter()
                result = simple_evaluate(
                    model=wrapper, tasks=tasks, num_fewshot=0, log_samples=True,
                    apply_chat_template=False, bootstrap_iters=1000,
                    random_seed=42, numpy_random_seed=42, torch_random_seed=42,
                    fewshot_random_seed=42,
                )
                torch.cuda.synchronize()
                seconds = time.perf_counter() - start
                metrics = result["results"]
                row = dict(model=run["label"], model_id=run["model_id"], mode=mode,
                           suite_sha256=digest,
                           bits_per_byte=metrics["financial_prose"]["bits_per_byte,none"],
                           qa_accuracy=metrics["financial_qa"]["acc,none"],
                           seconds=seconds, peak_allocated_gib=torch.cuda.max_memory_allocated() / 2**30,
                           model_parameters=sum(p.numel() for p in model.parameters()),
                           document_count=len(suite["documents"]), question_count=len(suite["questions"]),
                           dtype=str(dtype))
                if not all(math.isfinite(row[k]) for k in ("bits_per_byte", "qa_accuracy")):
                    raise ValueError("Non-finite evaluation scores.")
                summaries.append(row)
                run_output = output / f"{run['label']}_{mode}"
                run_output.mkdir()
                (run_output / "harness_results.json").write_text(json.dumps(
                    result, indent=2, ensure_ascii=False, default=str))
                with (run_output / "samples.jsonl").open("w") as handle:
                    for task_name, samples in result.get("samples", {}).items():
                        for sample in samples:
                            handle.write(json.dumps(dict(task=task_name, **sample), ensure_ascii=False, default=str) + "\n")
                with (output / "comparison.csv").open("w", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(row))
                    writer.writeheader()
                    writer.writerows(summaries)
                (output / "comparison.json").write_text(json.dumps(summaries, indent=2, allow_nan=False))
                print(json.dumps(row, indent=2))
            finally:
                del wrapper, model, tasks
                gc.collect()
                torch.cuda.empty_cache()
    paired = []
    for run in runs:
        baseline, adapted = [r for r in summaries if r["model"] == run["label"]]
        paired.append(dict(model=run["label"],
                           qa_accuracy_change=adapted["qa_accuracy"] - baseline["qa_accuracy"],
                           bits_per_byte_change=adapted["bits_per_byte"] - baseline["bits_per_byte"]))
    (output / "improvement.json").write_text(json.dumps(paired, indent=2, allow_nan=False))
    return summaries

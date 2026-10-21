from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from llm_flow.config import (
    DATASET_CONFIGURATION,
    DATASET_ID,
    DATASET_REVISION,
    EOS_TOKEN_ID,
    MODEL_ID,
    MODEL_REVISION,
    ConfigError,
    _reject_placeholders,
    load_core_config,
)


@dataclass(frozen=True)
class Matrix:
    kind: str
    rows: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class ConfigBundle:
    data: dict[str, Any]
    training: dict[str, Any]
    evaluation: dict[str, Any]
    smoke: dict[str, Any]
    pipeline: Matrix
    adaptation: Matrix
    scale: Matrix


@dataclass(frozen=True)
class WinnerReference:
    name: str


@dataclass(frozen=True)
class VerifiedSelection:
    name: str
    value: str
    artifact_sha256: str


DATA = {
    "schema_version": "1.0",
    "source": {
        "id": DATASET_ID,
        "configuration": DATASET_CONFIGURATION,
        "split": "train",
        "revision": DATASET_REVISION,
        "required_fields": ["text", "id"],
        "preserve_available_source_fields": True,
    },
    "normalization": {
        "line_endings": "LF",
        "unicode": "NFC",
        "strip_edges": True,
        "collapse_internal_whitespace": False,
    },
    "filters": {
        "minimum_codepoints": 200,
        "minimum_qwen_tokens": 50,
        "reject_nul": True,
        "maximum_replacement_fraction": 0.01,
        "maximum_control_fraction": 0.01,
        "additional_quality_threshold": None,
        "allowed_control_characters": ["LF", "tab", "form_feed"],
    },
    "deduplication": {
        "id_winner": "smallest_normalized_text_sha256",
        "text_winner": "smallest_source_id",
    },
    "split": {
        "algorithm": "sha256_first8_big_endian_mod100",
        "training_remainders": [0, 94],
        "validation_remainders": [95, 99],
    },
    "ordering": "sha256_order_id_then_id",
    "packing": {
        "tokenizer_id": MODEL_ID,
        "tokenizer_revision": MODEL_REVISION,
        "eos_token_id": EOS_TOKEN_ID,
        "eos_per_document": 1,
        "bos": False,
        "sequence_length": 1024,
        "cross_document_attention": True,
        "drop_incomplete": True,
        "chat_template": False,
    },
    "products": {
        "train_10m": {"sequences": 9765, "tokens": 9999360},
        "train_50m": {"sequences": 48828, "tokens": 49999872},
        "train_100m": {"sequences": 97656, "tokens": 99999744},
        "validation": {"sequences": 1000, "tokens": 1024000, "scored_targets": 1023000},
    },
}
TRAINING = {
    "schema_version": "1.0",
    "shared": {
        "framework": "mlx",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "sequence_length": 1024,
        "dtype": "bfloat16",
        "microbatch_sequences": 1,
        "accumulation_steps": 8,
        "effective_batch_tokens": 8192,
        "clip_gradient_norm": 1.0,
        "warmup_updates": 100,
        "schedule": "cosine",
        "optimizer": "adamw",
        "beta1": 0.9,
        "beta2": 0.95,
        "epsilon": 1e-8,
        "checkpoint_updates": 250,
        "checkpoint_at_end": True,
        "final_partial_accumulation": "flush",
        "seeds": [17, 42, 73],
    },
    "performance_benchmark": {
        "warmup_updates": 50,
        "measured_updates": 300,
        "fresh_process_repetitions": 3,
        "reset_initial_model": True,
        "exclude_from_window": [
            "model_loading",
            "compilation",
            "warmup",
            "validation",
            "checkpoint_writing",
            "log_upload",
        ],
        "include_in_window": ["normal_batch_preparation"],
    },
    "profiles": {
        "full": {"trainable": "all", "weight_decay": 0.1, "peak_lr": 2e-5, "final_lr": 2e-6},
        "lora": {
            "trainable": "adapters_only",
            "weight_decay": 0.0,
            "peak_lr": 1e-4,
            "final_lr": 1e-5,
            "layers": 24,
            "modules": [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
            "rank": 16,
            "alpha": 8,
            "scale": 0.5,
            "dropout": 0.05,
            "frozen": ["base", "embeddings", "normalization", "lm_head"],
        },
        "qlora": {
            "optional": True,
            "inherits": "lora",
            "quantization": "mlx_affine_4bit",
            "group_size": 64,
            "compute_dtype": "bfloat16",
            "adapter_dtype": "bfloat16",
        },
    },
}
EVALUATION = {
    "schema_version": "1.0",
    "validation": {
        "input_tokens": 1024000,
        "sequences": 1000,
        "sequence_length": 1024,
        "scored_targets": 1023000,
        "loss": "shifted_next_token_cross_entropy",
        "perplexity": "exp_loss",
    },
    "benchmark": {
        "package": "lm-eval",
        "version": "0.4.13",
        "tasks": ["arc_easy", "openbookqa"],
        "num_fewshot": 0,
        "seed": 42,
        "batch_size": 1,
        "answer_scoring": "conditional_log_likelihood",
        "primary_metric": "acc_norm",
        "generation_sampling": False,
    },
    "export": {"fixed_prompts": 3, "maximum_absolute_logit_difference": 0.001},
}
SMOKE = {
    "schema_version": "1.0",
    "id": "S00",
    "kind": "smoke",
    "data_profile": "data.yaml",
    "training_profile": "training.yaml#full",
    "evaluation_profile": "evaluation.yaml",
    "dataset": "smoke_100_sequences",
    "sequences": 100,
    "optimizer_updates": 5,
    "seed": 42,
    "repetitions": 1,
    "requires": ["training", "checkpoint_reload", "validation"],
}
PIPELINE = [
    ("P00", None, "baseline", "local_raw_online_padded_workers0_prefetch0", 3, True),
    ("P01", "P00", "tokenization", "local_pretokenized_padded", 3, True),
    ("P02", "P01", "packing", "local_pretokenized_packed1024", 3, True),
    ("P03", "P00", "access", "remote_streaming_online_padded", 3, False),
    ("P04", "P02", "cache", "cold_after_reboot", 3, False),
    ("P05", "P04", "cache", "immediate_paired_repeat", 3, False),
    ("P10", "P02", "workers", "workers0_prefetch0", 3, True),
    ("P11", "P10", "workers", "workers2_prefetch2", 3, True),
    ("P12", "P10", "workers", "workers4_prefetch2", 3, True),
    ("P13", "P10", "workers", "workers8_prefetch2", 3, True),
    ("P20", "winner:eligible_nonzero_worker", "prefetch", "depth1", 3, True),
    ("P21", "P20", "prefetch", "depth2", 3, True),
    ("P22", "P20", "prefetch", "depth4", 3, True),
    ("P30", None, "quality_control", "P00_full_10m", 1, False),
    ("P31", "P30", "candidate_confirmation", "winner:production_pipeline", 1, False),
]
ADAPTATION = [
    ("A00", "unchanged", None, [42], 0, "validation", True),
    ("A10", "full", "training.yaml#full", [17, 42, 73], 9999360, "train_10m", True),
    ("A20", "lora", "training.yaml#lora", [17, 42, 73], 9999360, "train_10m", True),
    ("A30", "qlora", "training.yaml#qlora", [17, 42, 73], 9999360, "train_10m", False),
]
SCALE = [
    ("D10", "train_10m", 9999360, "matching_A10_or_A20_seed42_only"),
    ("D50", "train_50m", 49999872, "never"),
    ("D100", "train_100m", 99999744, "never"),
]
MATRICES = {
    "pipeline_matrix.yaml": {
        "schema_version": "1.0",
        "kind": "pipeline",
        "profiles": {
            "data": "data.yaml",
            "training": "training.yaml#full",
            "evaluation": "evaluation.yaml",
        },
        "rows": [
            {
                "id": i,
                "control": c,
                "factor": f,
                "value": v,
                "repetitions": n,
                "dataset": "train_10m",
                "seed": 42,
                "selection_eligible": e,
            }
            for i, c, f, v, n, e in PIPELINE
        ],
    },
    "adaptation_matrix.yaml": {
        "schema_version": "1.0",
        "kind": "adaptation",
        "profiles": {
            "data": "data.yaml",
            "training": "training.yaml",
            "evaluation": "evaluation.yaml",
        },
        "rows": [
            {
                "id": i,
                "method": m,
                "training_profile": p,
                "seeds": s,
                "tokens_per_seed": t,
                "dataset": d,
                "required": r,
                "pipeline": "winner:production_pipeline",
            }
            for i, m, p, s, t, d, r in ADAPTATION
        ],
    },
    "scale_matrix.yaml": {
        "schema_version": "1.0",
        "kind": "scale",
        "profiles": {
            "data": "data.yaml",
            "training": "training.yaml",
            "evaluation": "evaluation.yaml",
        },
        "rows": [
            {
                "id": i,
                "dataset": d,
                "tokens": t,
                "seed": 42,
                "passes": 1,
                "method": "winner:training_method",
                "pipeline": "winner:production_pipeline",
                "reuse": r,
            }
            for i, d, t, r in SCALE
        ],
    },
}
EXPECTED = {
    "data.yaml": DATA,
    "training.yaml": TRAINING,
    "evaluation.yaml": EVALUATION,
    "S00.yaml": SMOKE,
    **MATRICES,
}


def _strict_equal(actual: Any, expected: Any, path: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise ConfigError(f"{path} must be a mapping")
        for key in sorted(expected.keys() - actual.keys()):
            raise ConfigError(f"missing required field {path}.{key}")
        for key in sorted(actual.keys() - expected.keys()):
            raise ConfigError(f"unknown field {path}.{key}")
        for key, value in expected.items():
            _strict_equal(actual[key], value, f"{path}.{key}" if path else key)
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise ConfigError(f"{path} must have {len(expected)} entries")
        for index, value in enumerate(expected):
            _strict_equal(actual[index], value, f"{path}[{index}]")
    elif type(actual) is not type(expected) or actual != expected:
        raise ConfigError(f"{path} must equal frozen value {expected!r}; received {actual!r}")


def load_document(path: str | Path) -> dict[str, Any] | Matrix:
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"cannot load {path}: {exc}") from exc
    _reject_placeholders(raw)
    if path.name not in EXPECTED:
        raise ConfigError(f"unknown config document {path.name}")
    if path.name in MATRICES and isinstance(raw, dict) and isinstance(raw.get("rows"), list):
        ids = [row.get("id") for row in raw["rows"] if isinstance(row, dict)]
        if len(ids) != len(set(ids)):
            raise ConfigError("duplicate matrix row id")
        expected_rows = {row["id"]: row for row in MATRICES[path.name]["rows"]}
        for row in raw["rows"]:
            if isinstance(row, dict) and row.get("id") in expected_rows:
                _strict_equal(row, expected_rows[row["id"]], f"rows.{row['id']}")
    _strict_equal(raw, EXPECTED[path.name], "")
    if path.name in MATRICES:
        return Matrix(raw["kind"], {row["id"]: row for row in raw["rows"]})
    return raw


def load_all(config_dir: str | Path) -> ConfigBundle:
    config_dir = Path(config_dir)
    load_core_config(config_dir / "core.yaml")
    documents = [
        load_document(config_dir / name)
        for name in ("data.yaml", "training.yaml", "evaluation.yaml")
    ]
    smoke = load_document(config_dir / "experiments" / "S00.yaml")
    matrices = [load_document(config_dir / name) for name in MATRICES]
    return ConfigBundle(*documents, smoke, *matrices)


def _load_selection(name: str, path: Path, bundle: ConfigBundle) -> VerifiedSelection:
    try:
        content = path.read_bytes()
        data = json.loads(content)
    except (OSError, ValueError) as exc:
        raise ConfigError(f"selection artifact {name} unavailable: {exc}") from exc
    _strict_equal(
        set(data), {"schema_version", "name", "value", "status", "run_records"}, "selection fields"
    )
    if data["schema_version"] != "1.0" or data["name"] != name or data["status"] != "complete":
        raise ConfigError(f"selection artifact {name} is not complete or has wrong schema")
    value = data["value"]
    allowed = {
        "eligible_nonzero_worker": {"P11", "P12", "P13"},
        "production_pipeline": {
            r for r, row in bundle.pipeline.rows.items() if row["selection_eligible"]
        },
        "training_method": {"full", "lora"},
    }
    if name not in allowed or value not in allowed[name]:
        raise ConfigError(f"selection artifact {name} has ineligible value")
    records = data["run_records"]
    if not isinstance(records, list) or not records:
        raise ConfigError(f"selection artifact {name} has no run records")
    expected_experiment = (
        ("A10" if value == "full" else "A20") if name == "training_method" else value
    )
    for index, entry in enumerate(records):
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise ConfigError(f"selection artifact {name} run_records[{index}] malformed")
        run_path = (path.parent / entry["path"]).resolve()
        try:
            raw = run_path.read_bytes()
            run = json.loads(raw)
        except (OSError, ValueError) as exc:
            raise ConfigError(f"selection artifact {name} run unavailable: {exc}") from exc
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ConfigError(f"selection artifact {name} run checksum mismatch")
        if run.get("status") != "complete" or run.get("experiment_id") != expected_experiment:
            raise ConfigError(
                f"selection artifact {name} run is not a completed {expected_experiment}"
            )
    return VerifiedSelection(name, value, hashlib.sha256(content).hexdigest())


def _pipeline_settings(
    row_id: str, bundle: ConfigBundle, selections: dict[str, Path]
) -> dict[str, Any]:
    row = bundle.pipeline.rows[row_id]
    control = row["control"]
    if isinstance(control, str) and control.startswith("winner:"):
        name = WinnerReference(control.removeprefix("winner:")).name
        if name not in selections:
            raise ConfigError(f"unresolved selection {name} for {row_id}.control")
        control = _load_selection(name, selections[name], bundle).value
    settings = (
        _pipeline_settings(control, bundle, selections).copy()
        if control is not None and control != "P30"
        else {
            "access": "local",
            "tokenization": "online",
            "packing": "padded",
            "workers": 0,
            "prefetch_per_worker": 0,
            "cache": "normal",
        }
    )
    if row_id in {"P01", "P02"}:
        settings["tokenization"] = "pretokenized"
    if row_id in {"P02", "P04", "P05", "P10", "P11", "P12", "P13"}:
        settings["packing"] = "packed1024"
    if row_id == "P03":
        settings["access"] = "remote"
    if row_id == "P04":
        settings["cache"] = "first_after_reboot"
    if row_id == "P05":
        settings["cache"] = "immediate_paired_repeat"
    workers = {"P10": 0, "P11": 2, "P12": 4, "P13": 8}
    if row_id in workers:
        settings["workers"] = workers[row_id]
        settings["prefetch_per_worker"] = 0 if workers[row_id] == 0 else 2
    for key, depth in {"P20": 1, "P21": 2, "P22": 4}.items():
        if row_id == key:
            settings["prefetch_per_worker"] = depth
    if row_id == "P31":
        name = "production_pipeline"
        if name not in selections:
            raise ConfigError(f"unresolved selection {name} for P31")
        selected = _load_selection(name, selections[name], bundle).value
        settings = _pipeline_settings(selected, bundle, selections).copy()
    settings["warmup_updates"] = 50 if row_id not in {"P30", "P31"} else 0
    settings["measured_updates"] = 300 if row_id not in {"P30", "P31"} else 0
    settings["training_tokens"] = 9999360 if row_id in {"P30", "P31"} else None
    return settings


def resolve_row(
    bundle: ConfigBundle,
    matrix: str,
    row_id: str,
    *,
    selections: dict[str, Path] | None = None,
    reuse_run: dict[str, Any] | None = None,
) -> dict[str, Any]:
    table = getattr(bundle, matrix, None)
    if not isinstance(table, Matrix) or row_id not in table.rows:
        raise ConfigError(f"unknown matrix row {matrix}.{row_id}")
    row = table.rows[row_id].copy()
    selections = selections or {}
    for key, value in row.items():
        if isinstance(value, str) and value.startswith("winner:"):
            reference = WinnerReference(value.removeprefix("winner:"))
            if reference.name not in selections:
                name = reference.name
                raise ConfigError(f"unresolved selection {name} for {row_id}.{key}")
            row[key] = _load_selection(
                reference.name, Path(selections[reference.name]), bundle
            ).value
    if matrix == "pipeline":
        row["resolved_settings"] = _pipeline_settings(row_id, bundle, selections)
    elif matrix in {"adaptation", "scale"}:
        row["resolved_settings"] = {
            "pipeline": _pipeline_settings(row["pipeline"], bundle, selections),
            "training": row.get("training_profile", row.get("method")),
            "tokens": row.get("tokens_per_seed", row.get("tokens", 0)),
        }
    effective = row
    if matrix in {"adaptation", "scale"}:
        method = row["method"]
        profile = None if method == "unchanged" else bundle.training["profiles"][method]
        effective = {
            "dataset": row["dataset"],
            "tokens": row["resolved_settings"]["tokens"],
            "seed": 42,
            "method": method,
            "pipeline": row["pipeline"],
            "pipeline_settings": row["resolved_settings"]["pipeline"],
            "data": bundle.data,
            "training_shared": bundle.training["shared"],
            "training_profile": profile,
            "evaluation": bundle.evaluation,
        }
    row["config_sha256"] = hashlib.sha256(
        json.dumps(effective, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if matrix == "scale" and row_id == "D10" and reuse_run is not None:
        expected = {
            "experiment_id": "A10" if row["method"] == "full" else "A20",
            "seed": 42,
            "dataset": "train_10m",
            "tokens": 9999360,
            "pipeline": row["pipeline"],
            "method": row["method"],
            "status": "complete",
            "config_sha256": row["config_sha256"],
        }
        if any(reuse_run.get(k) != v for k, v in expected.items()) or not expected["config_sha256"]:
            raise ConfigError("D10 reuse requires matching A10/A20 seed-42 full configuration")
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["validate-all"])
    parser.add_argument("--config-dir", type=Path, default=Path("configs"))
    args = parser.parse_args(argv)
    try:
        bundle = load_all(args.config_dir)
    except ConfigError as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": "valid",
                "rows": {
                    "pipeline": len(bundle.pipeline.rows),
                    "adaptation": len(bundle.adaptation.rows),
                    "scale": len(bundle.scale.rows),
                },
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

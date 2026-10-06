"""Strict loading and validation for the project's frozen core configuration."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

MODEL_ID = "Qwen/Qwen2.5-0.5B"
MODEL_REVISION = "060db6499f32faf8b98477b0a26969ef7d8b9987"
DATASET_ID = "HuggingFaceFW/fineweb-edu"
DATASET_CONFIGURATION = "sample-10BT"
DATASET_REVISION = "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
EOS_TOKEN_ID = 151643
SEQUENCE_LENGTH = 1024
TRAINING_SUBSET_TOKENS = (9_999_360, 49_999_872, 99_999_744)
VALIDATION_INPUT_TOKENS = 1_024_000
CORE_SEEDS = (17, 42, 73)
PLACEHOLDER_PATTERN = re.compile(
    r"(\{\{[^{}]+\}\}|<[^<>]+>|\b(?:TODO|TBD)\b)", re.IGNORECASE
)


class ConfigError(ValueError):
    """Raised when a core configuration is malformed or violates frozen decisions."""


@dataclass(frozen=True)
class ProjectConfig:
    name: str


@dataclass(frozen=True)
class ModelConfig:
    id: str
    revision: str
    tokenizer_revision: str
    eos_token_id: int


@dataclass(frozen=True)
class DatasetConfig:
    id: str
    configuration: str
    split: str
    revision: str


@dataclass(frozen=True)
class TrainingConfig:
    subset_tokens: tuple[int, ...]
    validation_input_tokens: int
    seeds: tuple[int, ...]


@dataclass(frozen=True)
class FrameworkConfig:
    name: str
    mlx_lm_version: str


@dataclass(frozen=True)
class EvaluationConfig:
    lm_eval_version: str


@dataclass(frozen=True)
class HardwareConfig:
    class_name: str
    unified_memory_gb: int
    exact_identifier_required: bool


@dataclass(frozen=True)
class CoreConfig:
    schema_version: str
    project: ProjectConfig
    model: ModelConfig
    dataset: DatasetConfig
    sequence_length: int
    training: TrainingConfig
    framework: FrameworkConfig
    evaluation: EvaluationConfig
    hardware: HardwareConfig


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigError(f"{path} must be a mapping")
    return value


def _keys(value: Mapping[str, Any], expected: set[str], path: str) -> None:
    missing = expected - value.keys()
    if missing:
        field = sorted(missing)[0]
        raise ConfigError(f"missing required field {path}.{field}")
    unknown = value.keys() - expected
    if unknown:
        field = sorted(unknown)[0]
        raise ConfigError(f"unknown field {path}.{field}")


def _equals(actual: Any, expected: Any, path: str) -> None:
    if actual != expected:
        raise ConfigError(
            f"{path} must equal frozen value {expected!r}; received {actual!r}"
        )


def _reject_placeholders(value: Any, path: str = "root") -> None:
    if isinstance(value, str) and PLACEHOLDER_PATTERN.search(value):
        raise ConfigError(f"placeholder found at {path}")
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_placeholders(child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _reject_placeholders(child, f"{path}[{index}]")


def _integer_tuple(value: Any, path: str) -> tuple[int, ...]:
    if not isinstance(value, list) or any(type(item) is not int for item in value):
        raise ConfigError(f"{path} must be a list of integers")
    return tuple(value)


def _parse_core(data: Any) -> CoreConfig:
    root = _mapping(data, "root")
    _reject_placeholders(root)
    _keys(
        root,
        {
            "schema_version",
            "project",
            "model",
            "dataset",
            "sequence_length",
            "training",
            "framework",
            "evaluation",
            "hardware",
        },
        "root",
    )

    project = _mapping(root["project"], "project")
    _keys(project, {"name"}, "project")
    _equals(project["name"], "llm-flow", "project.name")

    model = _mapping(root["model"], "model")
    _keys(model, {"id", "revision", "tokenizer_revision", "eos_token_id"}, "model")
    _equals(model["id"], MODEL_ID, "model.id")
    _equals(model["revision"], MODEL_REVISION, "model.revision")
    _equals(model["tokenizer_revision"], MODEL_REVISION, "model.tokenizer_revision")
    _equals(model["eos_token_id"], EOS_TOKEN_ID, "model.eos_token_id")

    dataset = _mapping(root["dataset"], "dataset")
    _keys(dataset, {"id", "configuration", "split", "revision"}, "dataset")
    _equals(dataset["id"], DATASET_ID, "dataset.id")
    _equals(dataset["configuration"], DATASET_CONFIGURATION, "dataset.configuration")
    _equals(dataset["split"], "train", "dataset.split")
    _equals(dataset["revision"], DATASET_REVISION, "dataset.revision")

    training = _mapping(root["training"], "training")
    _keys(training, {"subset_tokens", "validation_input_tokens", "seeds"}, "training")
    subset_tokens = _integer_tuple(training["subset_tokens"], "training.subset_tokens")
    seeds = _integer_tuple(training["seeds"], "training.seeds")
    _equals(subset_tokens, TRAINING_SUBSET_TOKENS, "training.subset_tokens")
    _equals(
        training["validation_input_tokens"],
        VALIDATION_INPUT_TOKENS,
        "training.validation_input_tokens",
    )
    if not seeds or len(seeds) != len(set(seeds)):
        raise ConfigError("training.seeds must be non-empty and unique")
    _equals(seeds, CORE_SEEDS, "training.seeds")

    framework = _mapping(root["framework"], "framework")
    _keys(framework, {"name", "mlx_lm_version"}, "framework")
    _equals(framework["name"], "mlx", "framework.name")
    _equals(framework["mlx_lm_version"], "0.32.0", "framework.mlx_lm_version")

    evaluation = _mapping(root["evaluation"], "evaluation")
    _keys(evaluation, {"lm_eval_version"}, "evaluation")
    _equals(evaluation["lm_eval_version"], "0.4.13", "evaluation.lm_eval_version")

    hardware = _mapping(root["hardware"], "hardware")
    _keys(
        hardware,
        {"class", "unified_memory_gb", "exact_identifier_required"},
        "hardware",
    )
    _equals(hardware["class"], "apple-silicon-m5-series", "hardware.class")
    _equals(hardware["unified_memory_gb"], 48, "hardware.unified_memory_gb")
    _equals(
        hardware["exact_identifier_required"],
        True,
        "hardware.exact_identifier_required",
    )

    _equals(root["schema_version"], "1.0", "schema_version")
    _equals(root["sequence_length"], SEQUENCE_LENGTH, "sequence_length")

    return CoreConfig(
        schema_version=root["schema_version"],
        project=ProjectConfig(name=project["name"]),
        model=ModelConfig(**model),
        dataset=DatasetConfig(**dataset),
        sequence_length=root["sequence_length"],
        training=TrainingConfig(
            subset_tokens=subset_tokens,
            validation_input_tokens=training["validation_input_tokens"],
            seeds=seeds,
        ),
        framework=FrameworkConfig(**framework),
        evaluation=EvaluationConfig(**evaluation),
        hardware=HardwareConfig(
            class_name=hardware["class"],
            unified_memory_gb=hardware["unified_memory_gb"],
            exact_identifier_required=hardware["exact_identifier_required"],
        ),
    )


def load_core_config(path: str | Path) -> CoreConfig:
    """Load a YAML file and enforce every frozen core-project decision."""
    config_path = Path(path)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"cannot read {config_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {config_path}: {exc}") from exc
    return _parse_core(raw)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser(
        "validate", help="validate the canonical core YAML"
    )
    validate.add_argument("path", type=Path)
    args = parser.parse_args(argv)

    try:
        load_core_config(args.path)
    except ConfigError as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 2
    print(f"valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

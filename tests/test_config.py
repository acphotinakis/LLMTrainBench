from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from llm_flow.config import ConfigError, load_core_config, main

ROOT = Path(__file__).parents[1]
CORE_CONFIG = ROOT / "configs" / "core.yaml"


@pytest.fixture
def valid_data() -> dict:
    return {
        "schema_version": "1.0",
        "project": {"name": "llm-flow"},
        "model": {
            "id": "Qwen/Qwen2.5-0.5B",
            "revision": "060db6499f32faf8b98477b0a26969ef7d8b9987",
            "tokenizer_revision": "060db6499f32faf8b98477b0a26969ef7d8b9987",
            "eos_token_id": 151643,
        },
        "dataset": {
            "id": "HuggingFaceFW/fineweb-edu",
            "configuration": "sample-10BT",
            "split": "train",
            "revision": "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9",
        },
        "sequence_length": 1024,
        "training": {
            "subset_tokens": [9999360, 49999872, 99999744],
            "validation_input_tokens": 1024000,
            "seeds": [17, 42, 73],
        },
        "framework": {"name": "mlx", "mlx_lm_version": "0.32.0"},
        "evaluation": {"lm_eval_version": "0.4.13"},
        "hardware": {
            "class": "apple-silicon-m5-series",
            "unified_memory_gb": 48,
            "exact_identifier_required": True,
        },
    }


def write_yaml(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "core.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def test_loads_canonical_configuration() -> None:
    config = load_core_config(CORE_CONFIG)

    assert config.model.id == "Qwen/Qwen2.5-0.5B"
    assert config.model.eos_token_id == 151643
    assert config.dataset.configuration == "sample-10BT"
    assert config.sequence_length == 1024
    assert config.training.validation_input_tokens == 1024000
    assert config.training.seeds == (17, 42, 73)


def test_cli_validates_canonical_configuration(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(CORE_CONFIG)]) == 0
    assert "valid:" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda data: data["model"].pop("revision"), "model.revision"),
        (lambda data: data["model"].update(eos_token_id=1), "model.eos_token_id"),
        (lambda data: data.update(sequence_length=2048), "sequence_length"),
        (lambda data: data["model"].update(revision="0" * 40), "model.revision"),
        (lambda data: data["dataset"].update(revision="0" * 40), "dataset.revision"),
        (lambda data: data["training"].update(seeds=[]), "training.seeds"),
        (lambda data: data["training"].update(seeds=[17, 17]), "training.seeds"),
        (lambda data: data.update(unexpected=True), "unknown field"),
        (lambda data: data["model"].update(id="{{MODEL_ID}}"), "placeholder"),
    ],
)
def test_rejects_invalid_configuration(tmp_path, valid_data, mutation, message) -> None:
    data = deepcopy(valid_data)
    mutation(data)

    with pytest.raises(ConfigError, match=message):
        load_core_config(write_yaml(tmp_path, data))


def test_rejects_malformed_yaml(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("model: [unterminated", encoding="utf-8")

    with pytest.raises(ConfigError, match="invalid YAML"):
        load_core_config(path)

import json
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_flow.environment import (
    EnvironmentError,
    _packages,
    assert_binding,
    check_readiness,
    write_immutable_json,
)


def test_immutable_records_and_binding(tmp_path: Path) -> None:
    binding = tmp_path / "binding.json"
    identity = {
        "identity_sha256": "a" * 64,
        "model": "Mac17,8",
        "chip": "Apple M5 Pro",
        "memory_bytes": 48 * 1024**3,
    }
    assert_binding(binding, identity, register=True)
    assert_binding(binding, identity, register=False)
    with pytest.raises(EnvironmentError, match="identity"):
        assert_binding(binding, {**identity, "identity_sha256": "b" * 64}, register=False)
    with pytest.raises(EnvironmentError, match="exists"):
        write_immutable_json(binding, identity)
    with pytest.raises(EnvironmentError, match="unavailable"):
        assert_binding(tmp_path / "bad.json", {**identity, "identity_sha256": None}, register=True)
    assert not (tmp_path / "bad.json").exists()


def test_readiness_fails_closed_on_unknown_and_artifacts() -> None:
    observation = {
        "hardware": {
            "model": "Mac17,8",
            "chip": "Apple M5 Pro",
            "memory_bytes": 48 * 1024**3,
            "identity_sha256": "a" * 64,
            "cpu_cores": 18,
            "gpu_cores": 20,
        },
        "software": {
            "python": "3.12.13",
            "packages": {"mlx-lm": "0.32.0", "lm-eval": "0.4.13"},
            "locked_packages": {"mlx-lm": "0.32.0", "lm-eval": "0.4.13"},
            "macos_build": "25G83",
            "lock_sha256": "a" * 64,
        },
        "storage": {"same_volume": True, "local": True, "free_fraction": 0.2},
        "power": {"source": "AC", "low_power_mode": False},
        "thermal": {"start": "Nominal", "end": None},
        "binding_matches": True,
        "git": {"commit": "a" * 40, "clean": False},
        "artifacts": {"model": {"status": "unverified", "reason": "absent"}},
    }
    assert check_readiness(observation, require_artifacts=False)["ready"]
    result = check_readiness(observation, require_artifacts=True)
    assert not result["ready"]
    assert any("model" in reason for reason in result["reasons"])
    observation["artifacts"] = {
        "model": {"status": "verified", "revision": "060db6499f32faf8b98477b0a26969ef7d8b9987"},
        "tokenizer": {
            "status": "verified",
            "revision": "060db6499f32faf8b98477b0a26969ef7d8b9987",
            "eos_token_id": 151643,
        },
        "dataset": {"status": "verified", "revision": "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"},
    }
    assert check_readiness(observation, require_artifacts=True)["ready"]
    observation["artifacts"]["tokenizer"]["eos_token_id"] = 1
    assert not check_readiness(observation, require_artifacts=True)["ready"]
    observation["artifacts"]["tokenizer"]["eos_token_id"] = 151643
    observation["artifacts"]["dataset"]["revision"] = "0" * 40
    assert any(
        "dataset loaded revision mismatch" in reason
        for reason in check_readiness(observation, require_artifacts=True)["reasons"]
    )
    observation["power"]["source"] = None
    assert not check_readiness(observation, require_artifacts=False)["ready"]


@pytest.mark.parametrize(
    ("section", "field", "value", "message"),
    [
        ("hardware", "memory_bytes", 32 * 1024**3, "hardware"),
        ("storage", "free_fraction", 0.1999, "20%"),
        ("storage", "same_volume", False, "same local volume"),
        ("power", "low_power_mode", True, "Low Power Mode"),
        ("thermal", "start", None, "thermal"),
        ("software", "python", "3.11.0", "Python"),
    ],
)
def test_readiness_rejects_bad_observations(section, field, value, message) -> None:
    valid = {
        "hardware": {
            "model": "Mac17,8",
            "chip": "Apple M5 Pro",
            "memory_bytes": 48 * 1024**3,
            "cpu_cores": 18,
            "gpu_cores": 20,
        },
        "software": {
            "python": "3.12.13",
            "packages": {"mlx-lm": "0.32.0", "lm-eval": "0.4.13", "mlx": "0.32.3"},
            "locked_packages": {"mlx-lm": "0.32.0", "lm-eval": "0.4.13", "mlx": "0.32.3"},
            "macos_build": "25G83",
            "lock_sha256": "a" * 64,
        },
        "storage": {"same_volume": True, "local": True, "free_fraction": 0.2},
        "power": {"source": "AC", "low_power_mode": False},
        "thermal": {"start": "Nominal"},
        "git": {"commit": "a" * 40, "clean": False},
        "binding_matches": True,
    }
    observed = deepcopy(valid)
    observed[section][field] = value
    result = check_readiness(observed, require_artifacts=False)
    assert not result["ready"]
    assert any(message in reason for reason in result["reasons"])


def test_active_lock_package_inventory_includes_missing_transitive(monkeypatch) -> None:
    from llm_flow import environment

    monkeypatch.setattr(
        environment,
        "_run",
        lambda *args: (
            "mlx-lm==0.32.0\n"
            "mlx==0.32.3 ; sys_platform == 'darwin'\n"
            "tzdata==2026.5 ; sys_platform == 'win32'"
        ),
    )

    def version(name):
        if name == "mlx-lm":
            return "0.32.0"
        raise environment.importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(environment.importlib.metadata, "version", version)
    installed, locked = _packages()
    assert locked == {"mlx-lm": "0.32.0", "mlx": "0.32.3"}
    assert installed["mlx"] is None


def test_local_artifact_loader_requires_actual_load_and_pins(tmp_path, monkeypatch) -> None:
    from llm_flow import environment

    model = tmp_path / "060db6499f32faf8b98477b0a26969ef7d8b9987"
    dataset = tmp_path / "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
    model.mkdir()
    (model / "model.safetensors").write_bytes(b"weights")
    sample = dataset / "sample-10BT"
    sample.mkdir(parents=True)
    (sample / "part.parquet").write_bytes(b"parquet")

    def snapshot_download(name, **kwargs):
        assert kwargs["local_files_only"] is True
        return str(model if name.startswith("Qwen") else dataset)

    monkeypatch.setitem(
        sys.modules, "huggingface_hub", SimpleNamespace(snapshot_download=snapshot_download)
    )
    monkeypatch.setitem(
        sys.modules,
        "mlx_lm",
        SimpleNamespace(
            load=lambda *args, **kwargs: (
                object(),
                SimpleNamespace(eos_token_id=151643),
                {"model_type": "qwen2"},
            )
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "datasets",
        SimpleNamespace(load_dataset=lambda *args, **kwargs: [{"text": "abc", "id": "id-1"}]),
    )
    loaded = environment._artifact_metadata()
    assert {name: item["status"] for name, item in loaded.items()} == {
        "model": "verified",
        "tokenizer": "verified",
        "dataset": "verified",
    }
    monkeypatch.setitem(
        sys.modules,
        "mlx_lm",
        SimpleNamespace(
            load=lambda *args, **kwargs: (
                object(),
                SimpleNamespace(eos_token_id=1),
                {"model_type": "qwen2"},
            )
        ),
    )
    loaded = environment._artifact_metadata()
    assert loaded["tokenizer"]["status"] == "failed"
    monkeypatch.setitem(
        sys.modules,
        "mlx_lm",
        SimpleNamespace(
            load=lambda *args, **kwargs: (
                object(),
                SimpleNamespace(eos_token_id=151643),
                {"model_type": "gpt2"},
            )
        ),
    )
    assert environment._artifact_metadata()["model"]["status"] == "unverified"


def test_end_observation_is_separate_and_linked(tmp_path, monkeypatch) -> None:
    from llm_flow import environment

    start = tmp_path / "capture-start.json"
    write_immutable_json(start, {"capture_id": "capture-start"})
    monkeypatch.setattr(
        environment,
        "_thermal",
        lambda: {"state": "Nominal", "source": "ProcessInfo.thermalState", "reason": None},
    )
    end = environment.observe_end(start)
    assert end != start
    assert json.loads(end.read_text())["start_capture_id"] == "capture-start"
    assert json.loads(start.read_text()) == {"capture_id": "capture-start"}

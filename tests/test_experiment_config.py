import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from llm_flow.config import ConfigError
from llm_flow.experiment_config import load_all, load_document, resolve_row

ROOT = Path(__file__).parents[1]


def test_all_canonical_configs_load_and_cover_protocol() -> None:
    bundle = load_all(ROOT / "configs")
    assert set(bundle.pipeline.rows) == {
        "P00",
        "P01",
        "P02",
        "P03",
        "P04",
        "P05",
        "P10",
        "P11",
        "P12",
        "P13",
        "P20",
        "P21",
        "P22",
        "P30",
        "P31",
    }
    assert set(bundle.adaptation.rows) == {"A00", "A10", "A20", "A30"}
    assert set(bundle.scale.rows) == {"D10", "D50", "D100"}
    assert bundle.data["products"]["validation"]["scored_targets"] == 1_023_000


@pytest.mark.parametrize(
    ("name", "change", "message"),
    [
        ("data.yaml", lambda d: d["source"].update(revision="0" * 40), "source.revision"),
        ("data.yaml", lambda d: d["packing"].update(eos_token_id=1), "packing.eos_token_id"),
        (
            "training.yaml",
            lambda d: d["profiles"]["full"].update(peak_lr=1e-4),
            "profiles.full.peak_lr",
        ),
        (
            "evaluation.yaml",
            lambda d: d["validation"].update(scored_targets=1_024_000),
            "validation.scored_targets",
        ),
        ("pipeline_matrix.yaml", lambda d: d["rows"][1].update(control="P99"), "rows.P01.control"),
        ("pipeline_matrix.yaml", lambda d: d["rows"][1].update(extra=True), "unknown"),
        (
            "data.yaml",
            lambda d: d["products"]["train_10m"].update(tokens=9_999_361),
            "products.train_10m.tokens",
        ),
        (
            "data.yaml",
            lambda d: d["filters"].update(minimum_codepoints=True),
            "filters.minimum_codepoints",
        ),
        ("training.yaml", lambda d: d["shared"].pop("seeds"), "shared.seeds"),
        (
            "training.yaml",
            lambda d: d["shared"].update(accumulation_steps=7),
            "shared.accumulation_steps",
        ),
        (
            "evaluation.yaml",
            lambda d: d["benchmark"].update(num_fewshot=1),
            "benchmark.num_fewshot",
        ),
        (
            "adaptation_matrix.yaml",
            lambda d: d["rows"][0].update(tokens_per_seed=1),
            "rows.A00.tokens_per_seed",
        ),
        ("scale_matrix.yaml", lambda d: d["rows"][0].update(tokens=9_999_361), "rows.D10.tokens"),
        ("scale_matrix.yaml", lambda d: d["rows"][0].update(method="{{METHOD}}"), "placeholder"),
    ],
)
def test_frozen_and_schema_mutations_fail(tmp_path, name, change, message) -> None:
    data = yaml.safe_load((ROOT / "configs" / name).read_text())
    change(data)
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ConfigError, match=message):
        load_document(path)


def test_unresolved_winner_cannot_execute() -> None:
    bundle = load_all(ROOT / "configs")
    with pytest.raises(ConfigError, match="unresolved"):
        resolve_row(bundle, "pipeline", "P20")
    with pytest.raises(ConfigError, match="unresolved"):
        resolve_row(bundle, "pipeline", "P21")
    assert resolve_row(bundle, "pipeline", "P00")["id"] == "P00"
    assert resolve_row(bundle, "pipeline", "P13")["resolved_settings"]["workers"] == 8


def test_selection_requires_completed_checksums_and_eligible_worker(tmp_path: Path) -> None:
    bundle = load_all(ROOT / "configs")
    run_path = tmp_path / "P11-r1.json"
    run_content = json.dumps({"experiment_id": "P11", "status": "complete"}).encode()
    run_path.write_bytes(run_content)
    selection_path = tmp_path / "selection.json"
    selection = {
        "schema_version": "1.0",
        "name": "eligible_nonzero_worker",
        "value": "P11",
        "status": "complete",
        "run_records": [{"path": run_path.name, "sha256": hashlib.sha256(run_content).hexdigest()}],
    }
    selection_path.write_text(json.dumps(selection), encoding="utf-8")
    resolved = resolve_row(
        bundle, "pipeline", "P21", selections={"eligible_nonzero_worker": selection_path}
    )
    assert resolved["resolved_settings"]["workers"] == 2
    assert resolved["resolved_settings"]["prefetch_per_worker"] == 2
    run_path.write_bytes(json.dumps({"experiment_id": "P11", "status": "failed"}).encode())
    with pytest.raises(ConfigError, match="checksum"):
        resolve_row(
            bundle, "pipeline", "P20", selections={"eligible_nonzero_worker": selection_path}
        )
    run_path.write_bytes(run_content)
    selection["value"] = "P10"
    selection_path.write_text(json.dumps(selection), encoding="utf-8")
    with pytest.raises(ConfigError, match="ineligible"):
        resolve_row(
            bundle, "pipeline", "P20", selections={"eligible_nonzero_worker": selection_path}
        )


def test_d10_reuse_requires_exact_complete_seed42_run(tmp_path: Path) -> None:
    bundle = load_all(ROOT / "configs")
    selection_paths = {}
    for name, value, experiment in [
        ("production_pipeline", "P02", "P02"),
        ("training_method", "full", "A10"),
    ]:
        content = json.dumps({"experiment_id": experiment, "status": "complete"}).encode()
        run = tmp_path / f"{experiment}.json"
        run.write_bytes(content)
        selection = tmp_path / f"{name}.json"
        selection.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "name": name,
                    "value": value,
                    "status": "complete",
                    "run_records": [
                        {"path": run.name, "sha256": hashlib.sha256(content).hexdigest()}
                    ],
                }
            ),
            encoding="utf-8",
        )
        selection_paths[name] = selection
    scale = resolve_row(bundle, "scale", "D10", selections=selection_paths)
    adaptation = resolve_row(bundle, "adaptation", "A10", selections=selection_paths)
    assert scale["config_sha256"] == adaptation["config_sha256"]
    reuse = {
        "experiment_id": "A10",
        "status": "complete",
        "seed": 42,
        "dataset": "train_10m",
        "tokens": 9999360,
        "pipeline": "P02",
        "method": "full",
        "config_sha256": scale["config_sha256"],
    }
    assert resolve_row(bundle, "scale", "D10", selections=selection_paths, reuse_run=reuse)
    with pytest.raises(ConfigError, match="D10 reuse"):
        resolve_row(
            bundle, "scale", "D10", selections=selection_paths, reuse_run={**reuse, "seed": 17}
        )


def test_duplicate_matrix_id_rejected(tmp_path) -> None:
    data = yaml.safe_load((ROOT / "configs" / "scale_matrix.yaml").read_text())
    data["rows"].append(deepcopy(data["rows"][0]))
    path = tmp_path / "scale_matrix.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate"):
        load_document(path)

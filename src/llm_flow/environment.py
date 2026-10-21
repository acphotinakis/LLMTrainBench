from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement

from llm_flow.config import DATASET_REVISION, EOS_TOKEN_ID, MODEL_REVISION


class EnvironmentError(ValueError):
    pass


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "results" / "environment"


def _run(*command: str) -> str:
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=60, check=False, cwd=ROOT
    )
    if result.returncode:
        raise EnvironmentError(
            f"{' '.join(command)}: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def _probe(fn: Any) -> tuple[Any, str | None]:
    try:
        return fn(), None
    except (
        EnvironmentError,
        OSError,
        ValueError,
        KeyError,
        IndexError,
        subprocess.TimeoutExpired,
    ) as exc:
        return None, str(exc)


def _sysctl(name: str) -> str:
    return _run("sysctl", "-n", name)


def _identity() -> str:
    output = _run("ioreg", "-rd1", "-c", "IOPlatformExpertDevice")
    match = re.search(r'"IOPlatformUUID" = "([^"]+)"', output)
    if not match:
        raise EnvironmentError("IOPlatformUUID unavailable")
    return hashlib.sha256(match.group(1).encode()).hexdigest()


def _gpu_cores() -> int:
    data = json.loads(_run("system_profiler", "SPDisplaysDataType", "-json"))
    return int(data["SPDisplaysDataType"][0]["sppci_cores"])


def _volume(path: Path) -> dict[str, Any]:
    if not path.is_dir():
        raise EnvironmentError(f"volume path unavailable: {path}")
    mount = Path(os.path.realpath(path))
    df_lines = _run("df", "-P", str(mount)).splitlines()
    if len(df_lines) < 2:
        raise EnvironmentError(f"df volume probe failed for {mount}")
    device = df_lines[-1].split()[0]
    try:
        output = subprocess.run(
            ["diskutil", "info", "-plist", device], capture_output=True, check=True, timeout=20
        ).stdout
        data = plistlib.loads(output)
    except (subprocess.CalledProcessError, plistlib.InvalidFileException) as exc:
        raise EnvironmentError(f"diskutil volume probe failed: {exc}") from exc
    if data.get("Error"):
        raise EnvironmentError(str(data.get("ErrorMessage")))
    usage = shutil.disk_usage(mount)
    return {
        "path": str(path),
        "observed_at": str(path),
        "device": data.get("DeviceIdentifier"),
        "filesystem": data.get("FilesystemType"),
        "internal": data.get("Internal"),
        "free_bytes": usage.free,
        "total_bytes": usage.total,
        "free_fraction": usage.free / usage.total,
    }


def _power() -> dict[str, Any]:
    battery = _run("pmset", "-g", "batt")
    source_match = re.search(r"drawing from '([^']+)'", battery)
    source = (
        "AC"
        if source_match and source_match.group(1) == "AC Power"
        else "Battery"
        if source_match
        else None
    )
    settings = _run("pmset", "-g", "custom")
    section = "AC Power:" if source == "AC" else "Battery Power:" if source == "Battery" else None
    match = (
        re.search(r"^\s*powermode\s+(\d+)", settings.split(section, 1)[1], re.MULTILINE)
        if section and section in settings
        else None
    )
    mode = int(match.group(1)) if match else None
    return {
        "source": source,
        "low_power_mode": mode == 1 if mode in (0, 1, 2) else None,
        "power_mode": mode,
        "source_raw": source_match.group(1) if source_match else None,
    }


def _thermal() -> dict[str, Any]:
    raw = _run(
        "swift", "-e", "import Foundation; print(ProcessInfo.processInfo.thermalState.rawValue)"
    )
    states = {"0": "Nominal", "1": "Fair", "2": "Serious", "3": "Critical"}
    return {
        "state": states.get(raw),
        "source": "ProcessInfo.thermalState",
        "reason": None if raw in states else f"unknown thermal value {raw}",
    }


def _git() -> dict[str, Any]:
    return {
        "commit": _run("git", "rev-parse", "HEAD"),
        "clean": not bool(_run("git", "status", "--porcelain")),
    }


def _artifact_metadata() -> dict[str, dict[str, Any]]:
    os.environ["HF_HUB_OFFLINE"] = "1"
    result: dict[str, dict[str, Any]] = {}
    try:
        from huggingface_hub import snapshot_download
        from mlx_lm import load

        snapshot = Path(
            snapshot_download("Qwen/Qwen2.5-0.5B", revision=MODEL_REVISION, local_files_only=True)
        )
        if snapshot.name != MODEL_REVISION:
            raise EnvironmentError("local model resolver returned wrong revision")
        weights = sorted(snapshot.glob("*.safetensors"))
        if not weights:
            raise EnvironmentError("pinned model has no local weight files")
        loaded = load(
            str(snapshot),
            tokenizer_config={"local_files_only": True},
            lazy=False,
            return_config=True,
        )
        tokenizer = loaded[1]
        loaded_config = loaded[2]
        model_type = (
            loaded_config.get("model_type")
            if isinstance(loaded_config, dict)
            else getattr(loaded_config, "model_type", None)
        )
        if model_type != "qwen2":
            raise EnvironmentError(f"loaded model architecture is {model_type!r}, expected qwen2")
        result["model"] = {
            "status": "verified",
            "revision": MODEL_REVISION,
            "source": "pinned local Hub snapshot and loaded MLX weights",
            "weight_sha256": {path.name: _file_sha256(path) for path in weights},
        }
        result["tokenizer"] = {
            "status": "verified" if tokenizer.eos_token_id == EOS_TOKEN_ID else "failed",
            "revision": MODEL_REVISION,
            "eos_token_id": tokenizer.eos_token_id,
            "source": "tokenizer returned by local MLX model load",
        }
    except Exception as exc:
        result["model"] = {
            "status": "unverified",
            "reason": f"pinned local model load unavailable: {exc}",
        }
        result["tokenizer"] = {
            "status": "unverified",
            "reason": "pinned local tokenizer load unavailable",
        }
    try:
        from datasets import load_dataset
        from huggingface_hub import snapshot_download

        snapshot = Path(
            snapshot_download(
                "HuggingFaceFW/fineweb-edu",
                revision=DATASET_REVISION,
                repo_type="dataset",
                local_files_only=True,
            )
        )
        if snapshot.name != DATASET_REVISION:
            raise EnvironmentError("local dataset resolver returned wrong revision")
        files = sorted(path for path in snapshot.rglob("*.parquet") if "sample-10BT" in path.parts)
        if not files:
            raise EnvironmentError("pinned sample-10BT Parquet file unavailable")
        first = next(
            iter(load_dataset("parquet", data_files=str(files[0]), split="train", streaming=True))
        )
        if (
            not isinstance(first.get("text"), str)
            or not isinstance(first.get("id"), str)
            or not first["id"]
        ):
            raise EnvironmentError("loaded pinned dataset row lacks text or id")
        result["dataset"] = {
            "status": "verified",
            "revision": DATASET_REVISION,
            "source": "pinned local Hub snapshot and loaded sample-10BT Parquet row",
            "parquet_sha256": _file_sha256(files[0]),
        }
    except Exception as exc:
        result["dataset"] = {
            "status": "unverified",
            "reason": f"pinned local dataset load unavailable: {exc}",
        }
    return result


def _file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _packages() -> tuple[dict[str, str | None], dict[str, str]]:
    exported = _run("uv", "export", "--frozen", "--format", "requirements-txt", "--no-hashes")
    required: dict[str, str] = {}
    for line in exported.splitlines():
        if not line or line.startswith(("#", "-e", " ")):
            continue
        item = Requirement(line)
        if item.marker is not None and not item.marker.evaluate():
            continue
        pins = [specifier.version for specifier in item.specifier if specifier.operator == "=="]
        if len(pins) != 1:
            raise EnvironmentError(f"exported package {item.name} has no single locked version")
        required[item.name] = pins[0]
    installed: dict[str, str | None] = {}
    for name in required:
        try:
            installed[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            installed[name] = None
    return installed, required


def write_immutable_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True).encode() + b"\n"
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=".capture-", delete=False
    ) as temporary:
        temporary.write(payload)
        temporary.flush()
        os.fsync(temporary.fileno())
        temp_path = Path(temporary.name)
    try:
        os.link(temp_path, path)
    except FileExistsError as exc:
        raise EnvironmentError(f"record already exists: {path}") from exc
    finally:
        temp_path.unlink(missing_ok=True)


def assert_binding(path: Path, identity: dict[str, Any], *, register: bool) -> bool:
    if (
        not re.fullmatch(r"[0-9a-f]{64}", str(identity.get("identity_sha256", "")))
        or not re.fullmatch(r"Mac\d+,\d+", str(identity.get("model", "")))
        or not str(identity.get("chip", "")).startswith("Apple M5")
        or identity.get("memory_bytes") != 48 * 1024**3
    ):
        raise EnvironmentError("core Mac identity or hardware class unavailable")
    if not path.exists():
        if not register:
            raise EnvironmentError("core Mac identity binding absent")
        write_immutable_json(path, identity)
    bound = json.loads(path.read_text(encoding="utf-8"))
    if bound != identity:
        raise EnvironmentError("core Mac identity mismatch")
    return True


def capture(*, register: bool = False, output_dir: Path = OUTPUT) -> Path:
    model, model_error = _probe(lambda: _sysctl("hw.model"))
    chip, chip_error = _probe(lambda: _sysctl("machdep.cpu.brand_string"))
    cpu, cpu_error = _probe(lambda: int(_sysctl("hw.physicalcpu")))
    gpu, gpu_error = _probe(_gpu_cores)
    memory, memory_error = _probe(lambda: int(_sysctl("hw.memsize")))
    identity_hash, identity_error = _probe(_identity)
    identity = {
        "identity_sha256": identity_hash,
        "model": model,
        "chip": chip,
        "memory_bytes": memory,
    }
    binding_matches, binding_error = _probe(
        lambda: assert_binding(output_dir / "core-mac-binding.json", identity, register=register)
    )
    (ROOT / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    raw_volume, raw_error = _probe(lambda: _volume(ROOT / "data" / "raw"))
    processed_volume, processed_error = _probe(lambda: _volume(ROOT / "data" / "processed"))
    power, power_error = _probe(_power)
    thermal, thermal_error = _probe(_thermal)
    git, git_error = _probe(_git)
    os_build, os_error = _probe(lambda: _run("sw_vers", "-buildVersion"))
    package_inventory, packages_error = _probe(_packages)
    packages, locked_packages = package_inventory if package_inventory else ({}, {})
    record = {
        "schema_version": "1.0",
        "capture_id": (
            f"capture-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}-{uuid.uuid4().hex[:8]}"
        ),
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "hardware": {
            **identity,
            "cpu_cores": cpu,
            "gpu_cores": gpu,
            "errors": {
                "model": model_error,
                "chip": chip_error,
                "cpu": cpu_error,
                "gpu": gpu_error,
                "memory": memory_error,
                "identity": identity_error,
            },
        },
        "software": {
            "python": platform.python_version(),
            "packages": packages,
            "locked_packages": locked_packages,
            "packages_error": packages_error,
            "lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
            "macos_build": os_build,
            "error": os_error,
        },
        "storage": {
            "raw": raw_volume,
            "processed": processed_volume,
            "same_volume": bool(
                raw_volume
                and processed_volume
                and raw_volume["device"] == processed_volume["device"]
            ),
            "local": bool(
                raw_volume
                and processed_volume
                and raw_volume["filesystem"] in {"apfs", "hfs", "msdos", "exfat"}
                and processed_volume["filesystem"] in {"apfs", "hfs", "msdos", "exfat"}
            ),
            "free_fraction": min(raw_volume["free_fraction"], processed_volume["free_fraction"])
            if raw_volume and processed_volume
            else None,
            "errors": {"raw": raw_error, "processed": processed_error},
        },
        "power": power or {"source": None, "low_power_mode": None, "error": power_error},
        "thermal": {
            "start": thermal["state"] if thermal else None,
            "start_source": thermal["source"] if thermal else None,
            "start_reason": thermal["reason"] if thermal else thermal_error,
            "end": None,
            "end_reason": "a separate post-run observation is required",
        },
        "git": git or {"commit": None, "clean": None, "error": git_error},
        "binding_matches": binding_matches is True,
        "binding_error": binding_error,
        "revisions": {
            "model": MODEL_REVISION,
            "tokenizer": MODEL_REVISION,
            "dataset": DATASET_REVISION,
        },
        "artifacts": _artifact_metadata(),
    }
    path = output_dir / f"{record['capture_id']}.json"
    write_immutable_json(path, record)
    return path


def check_readiness(record: dict[str, Any], *, require_artifacts: bool) -> dict[str, Any]:
    reasons: list[str] = []
    hardware = record.get("hardware", {})
    software = record.get("software", {})
    storage = record.get("storage", {})
    power = record.get("power", {})
    thermal = record.get("thermal", {})
    if not record.get("binding_matches"):
        reasons.append("core Mac identity binding unavailable or mismatched")
    if not re.fullmatch(r"[0-9a-f]{64}", str(hardware.get("identity_sha256", ""))):
        reasons.append("machine identity digest unknown")
    if (
        not re.fullmatch(r"Mac\d+,\d+", str(hardware.get("model", "")))
        or not str(hardware.get("chip", "")).startswith("Apple M5")
        or hardware.get("memory_bytes") != 48 * 1024**3
    ):
        reasons.append("hardware class mismatch")
    if (
        type(hardware.get("cpu_cores")) is not int
        or hardware["cpu_cores"] <= 0
        or type(hardware.get("gpu_cores")) is not int
        or hardware["gpu_cores"] <= 0
    ):
        reasons.append("CPU/GPU core count unknown")
    if not re.match(r"^3\.12\.\d+$", str(software.get("python"))):
        reasons.append("Python 3.12 required")
    for package, expected in (("mlx-lm", "0.32.0"), ("lm-eval", "0.4.13")):
        if software.get("packages", {}).get(package) != expected:
            reasons.append(f"{package} installed version mismatch or unknown")
    locked_packages = software.get("locked_packages", {})
    if not locked_packages:
        reasons.append("locked package inventory unknown")
    for package, expected in locked_packages.items():
        if software.get("packages", {}).get(package) != expected:
            reasons.append(f"{package} differs from installed lock version")
    if not re.fullmatch(r"[0-9a-f]{64}", str(software.get("lock_sha256", ""))):
        reasons.append("lock digest unknown")
    if not software.get("macos_build"):
        reasons.append("macOS build unknown")
    if storage.get("same_volume") is not True or storage.get("local") is not True:
        reasons.append("raw and processed data require same local volume")
    if type(storage.get("free_fraction")) not in (int, float) or not (
        0.2 <= storage["free_fraction"] <= 1.0
    ):
        reasons.append("local volume below 20% free or unknown")
    if power.get("source") != "AC" or power.get("low_power_mode") is not False:
        reasons.append("AC power and Low Power Mode off required")
    if thermal.get("start") != "Nominal":
        reasons.append("start thermal state unknown or non-nominal")
    if (
        not record.get("git", {}).get("commit")
        or type(record.get("git", {}).get("clean")) is not bool
    ):
        reasons.append("Git commit or cleanliness observation unknown")
    if require_artifacts:
        for name in ("model", "tokenizer", "dataset"):
            artifact = record.get("artifacts", {}).get(name, {})
            if artifact.get("status") != "verified":
                reasons.append(f"{name} artifact unverified: {artifact.get('reason', 'unknown')}")
            elif artifact.get("revision") != (
                DATASET_REVISION if name == "dataset" else MODEL_REVISION
            ):
                reasons.append(f"{name} loaded revision mismatch")
        if record.get("artifacts", {}).get("tokenizer", {}).get("eos_token_id") != EOS_TOKEN_ID:
            reasons.append("tokenizer loaded EOS mismatch or unknown")
    return {"ready": not reasons, "reasons": reasons, "require_artifacts": require_artifacts}


def observe_end(capture_path: Path) -> Path:
    if not capture_path.is_file():
        raise EnvironmentError(f"capture not found: {capture_path}")
    start = json.loads(capture_path.read_text(encoding="utf-8"))
    thermal, error = _probe(_thermal)
    record = {
        "schema_version": "1.0",
        "start_capture_id": start["capture_id"],
        "observed_at_utc": datetime.now(UTC).isoformat(),
        "thermal_end": thermal or {"state": None, "reason": error},
    }
    path = capture_path.parent / f"end-{start['capture_id']}-{uuid.uuid4().hex[:8]}.json"
    write_immutable_json(path, record)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--register-core-mac", action="store_true")
    validate = sub.add_parser("validate")
    validate.add_argument("--capture", type=Path, required=True)
    validate.add_argument("--require-artifacts", action="store_true")
    end = sub.add_parser("observe-end")
    end.add_argument("--capture", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            print(capture(register=args.register_core_mac))
            return 0
        if args.command == "observe-end":
            print(observe_end(args.capture))
            return 0
        record = json.loads(args.capture.read_text(encoding="utf-8"))
        live_identity, identity_error = _probe(_identity)
        if live_identity != record.get("hardware", {}).get("identity_sha256"):
            record["binding_matches"] = False
            record["binding_error"] = identity_error or "capture belongs to another machine"
        else:
            bound, binding_error = _probe(
                lambda: assert_binding(
                    args.capture.parent / "core-mac-binding.json",
                    {
                        key: record["hardware"].get(key)
                        for key in ("identity_sha256", "model", "chip", "memory_bytes")
                    },
                    register=False,
                )
            )
            record["binding_matches"] = bound is True
            record["binding_error"] = binding_error
        result = check_readiness(record, require_artifacts=args.require_artifacts)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["ready"] else 2
    except (EnvironmentError, OSError, ValueError, KeyError) as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

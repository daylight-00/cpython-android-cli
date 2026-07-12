#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_PHASE4_INDEX = "878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce"
EXPECTED_PHASE4I_INDEX = "7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6"
EXPECTED_PORTABLE = "f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978"


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(cjson(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def actual_kind(path: Path) -> str:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return "absent"
    if stat.S_ISLNK(observed.st_mode):
        return "symlink"
    if stat.S_ISDIR(observed.st_mode):
        return "directory"
    if stat.S_ISREG(observed.st_mode):
        return "regular"
    return "special"


def snapshot(path: Path) -> dict[str, Any]:
    kind = actual_kind(path)
    result: dict[str, Any] = {"path": str(path), "type": kind}
    if kind == "absent":
        return result
    observed = path.lstat()
    result["mode"] = f"{stat.S_IMODE(observed.st_mode):04o}"
    if kind == "regular":
        result["size"] = observed.st_size
        result["sha256"] = sha256_file(path)
    elif kind == "symlink":
        result["target"] = os.readlink(path)
    return result


def manifest_record(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": entry["payload_path"],
        "type": entry["type"],
        "mode": entry["mode"],
        "size": entry.get("size"),
        "sha256": entry.get("sha256"),
        "symlink_target": entry.get("symlink_target"),
    }


def snapshot_matches(snapshot_value: dict[str, Any], record: dict[str, Any]) -> bool:
    if snapshot_value.get("type") != record.get("type"):
        return False
    if snapshot_value.get("mode") != record.get("mode"):
        return False
    if record.get("type") == "regular":
        return (
            snapshot_value.get("size") == record.get("size")
            and snapshot_value.get("sha256") == record.get("sha256")
        )
    if record.get("type") == "symlink":
        return snapshot_value.get("target") == record.get("symlink_target")
    return True


def registry_identity(root: Path) -> dict[str, Any]:
    path = root / ".cpython-android-cli/registry.json"
    data = path.read_bytes()
    value = json.loads(data)
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "artifact_count": len(value.get("artifacts", [])),
        "owned_path_count": len(value.get("owned_paths", [])),
    }


def transaction_inventory(root: Path) -> list[dict[str, Any]]:
    transactions = root / ".cpython-android-cli/transactions"
    if not transactions.is_dir():
        return []
    output: list[dict[str, Any]] = []
    for directory in sorted(path for path in transactions.iterdir() if path.is_dir()):
        journal_path = directory / "journal.json"
        row: dict[str, Any] = {"name": directory.name, "journal_exists": journal_path.is_file()}
        if journal_path.is_file():
            journal = read_json(journal_path)
            row.update(
                state=journal.get("state"),
                operation=journal.get("operation"),
                artifact=journal.get("artifact"),
                mutations=journal.get("mutations", []),
            )
        output.append(row)
    return output


def owned_digest(prefix: Path, entries: list[dict[str, Any]], *, exclude: str | None = None) -> str:
    records: list[dict[str, Any]] = []
    for entry in sorted(entries, key=lambda item: item["payload_path"]):
        relative = entry["payload_path"]
        if relative == exclude:
            continue
        observed = snapshot(prefix / relative)
        record = {"relative": relative, **{k: v for k, v in observed.items() if k != "path"}}
        records.append(record)
    return hashlib.sha256(cjson(records)).hexdigest()


def invoke_engine(
    *,
    local_runner: Path,
    engine: Path,
    contract_results: Path,
    root: Path,
    operation: str,
    output: Path,
    artifact: str | None = None,
) -> dict[str, Any]:
    command = [
        sys.executable,
        "-I",
        "-B",
        "-S",
        str(local_runner),
        str(engine),
        "--installation-root",
        str(root),
        "--operation",
        operation,
        "--output",
        str(output),
    ]
    if operation == "install":
        command.extend(("--contract-results", str(contract_results)))
    if artifact is not None:
        command.extend(("--artifact", artifact))
    completed = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    log_path = output.with_suffix(".log")
    log_path.write_text(completed.stdout, encoding="utf-8")
    result = read_json(output)
    process = {
        "returncode": completed.returncode,
        "result": result,
        "log": log_path.name,
    }
    write_json(output.with_name(output.stem + "-process.json"), process)
    return process


def invoke_fingerprint(
    *,
    script: Path,
    prefix: Path,
    output: Path,
    portable: bool,
) -> dict[str, Any]:
    command = [sys.executable, "-I", "-B", "-S", str(script)]
    if portable:
        command.extend(("--installed-prefix", str(prefix), "--output", str(output)))
    else:
        command.extend(("--runtime-prefix", str(prefix), "--output", str(output), "--expected-entry-count", "714"))
    completed = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    output.with_suffix(".log").write_text(completed.stdout, encoding="utf-8")
    result = read_json(output)
    return {"returncode": completed.returncode, "result": result}


def identity(
    *,
    root: Path,
    strict_script: Path,
    portable_script: Path,
    output_dir: Path,
    label: str,
) -> dict[str, Any]:
    prefix = root / "prefix"
    strict = invoke_fingerprint(
        script=strict_script,
        prefix=prefix,
        output=output_dir / f"{label}-strict.json",
        portable=False,
    )
    portable = invoke_fingerprint(
        script=portable_script,
        prefix=prefix,
        output=output_dir / f"{label}-portable.json",
        portable=True,
    )
    return {
        "strict": strict,
        "portable": portable,
        "registry": registry_identity(root),
        "transactions": transaction_inventory(root),
    }


def clone_seed(seed: Path, destination: Path, probe_relative: str) -> dict[str, Any]:
    shutil.copytree(seed, destination, symlinks=True, copy_function=shutil.copy2)
    seed_registry = seed / ".cpython-android-cli/registry.json"
    clone_registry = destination / ".cpython-android-cli/registry.json"
    seed_probe = seed / "prefix" / probe_relative
    clone_probe = destination / "prefix" / probe_relative
    return {
        "root_inode_separate": seed.stat().st_ino != destination.stat().st_ino,
        "registry_inode_separate": seed_registry.stat().st_ino != clone_registry.stat().st_ino,
        "probe_inode_separate": seed_probe.stat().st_ino != clone_probe.stat().st_ino,
    }


def mutate(path: Path, scenario: str, desired_mode: str) -> dict[str, Any]:
    before = snapshot(path)
    if scenario == "regular-bytes":
        path.write_bytes(b"stage3c-gate3a-product-acceptance-corruption\n")
        os.chmod(path, int(desired_mode, 8))
    elif scenario == "regular-mode":
        os.chmod(path, 0o644 if int(desired_mode, 8) != 0o644 else 0o600)
    elif scenario == "regular-wrong-type":
        path.unlink()
        path.mkdir(mode=0o755)
    elif scenario == "symlink-target":
        path.unlink()
        os.symlink("stage3c-gate3a-invalid-target", path)
    elif scenario in {"missing-regular", "missing-symlink"}:
        path.unlink()
    else:
        raise ValueError(scenario)
    return {"scenario": scenario, "before": before, "after": snapshot(path)}


def repair_cycle(
    *,
    scenario: str,
    root: Path,
    entry: dict[str, Any],
    owned_entries: list[dict[str, Any]],
    local_runner: Path,
    engine: Path,
    contract_results: Path,
    strict_script: Path,
    portable_script: Path,
    output_dir: Path,
) -> dict[str, Any]:
    relative = entry["payload_path"]
    path = root / "prefix" / relative
    before = identity(
        root=root,
        strict_script=strict_script,
        portable_script=portable_script,
        output_dir=output_dir,
        label="before",
    )
    unaffected_before = owned_digest(root / "prefix", owned_entries, exclude=relative)
    mutation = mutate(path, scenario, entry["mode"])
    corrupted = identity(
        root=root,
        strict_script=strict_script,
        portable_script=portable_script,
        output_dir=output_dir,
        label="corrupted",
    )
    pre_verify = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract_results,
        root=root,
        operation="verify",
        output=output_dir / "pre-verify.json",
    )
    install = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract_results,
        root=root,
        operation="install",
        artifact="runtime-base",
        output=output_dir / "install.json",
    )
    post_verify = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract_results,
        root=root,
        operation="verify",
        output=output_dir / "post-verify.json",
    )
    after = identity(
        root=root,
        strict_script=strict_script,
        portable_script=portable_script,
        output_dir=output_dir,
        label="after",
    )
    unaffected_after = owned_digest(root / "prefix", owned_entries, exclude=relative)
    final_path = snapshot(path)
    desired = manifest_record(entry)
    passed = (
        before["strict"]["returncode"] == 0
        and before["portable"]["returncode"] == 0
        and pre_verify["returncode"] == 44
        and pre_verify["result"].get("bad_paths") == [relative]
        and install["returncode"] == 0
        and install["result"].get("action_counts") == {"noop": 713, "repair": 1}
        and install["result"].get("mutation_count") == 2
        and post_verify["returncode"] == 0
        and post_verify["result"].get("bad_paths") == []
        and after["strict"]["returncode"] == 0
        and after["strict"]["result"].get("pass") is True
        and after["portable"]["returncode"] == 0
        and after["portable"]["result"].get("fingerprint") == EXPECTED_PORTABLE
        and after["registry"] == before["registry"]
        and after["transactions"] == []
        and unaffected_before == unaffected_after
        and snapshot_matches(final_path, desired)
    )
    result = {
        "schema_version": 1,
        "scenario": scenario,
        "candidate": desired,
        "before": before,
        "mutation": mutation,
        "corrupted": corrupted,
        "pre_verify": pre_verify,
        "install": install,
        "post_verify": post_verify,
        "after": after,
        "unaffected_before": unaffected_before,
        "unaffected_after": unaffected_after,
        "final_path": final_path,
        "pass": passed,
    }
    write_json(output_dir / "scenario.json", result)
    return result

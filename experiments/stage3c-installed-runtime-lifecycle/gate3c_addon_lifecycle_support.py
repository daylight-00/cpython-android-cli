#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import time
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

ARTIFACTS = ("runtime-base", "development-addon", "test-addon")
EXPECTED_GATE3B_ARCHIVE_SHA = "0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b"
EXPECTED_GATE3B_INDEX_SHA = "f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9"
EXPECTED_CONTRACT_INDEX_SHA = "79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3"
EXPECTED_MANIFEST_INDEX_SHA = "540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1"
EXPECTED_MATRIX_SHA = "52c622450e9664c6738a75fbc947b809cf1f4766e61b04a68a1a8dcc24b6c14a"
EXPECTED_ENGINE_SHA = "33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a"
EXPECTED_OPS_SHA = "61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021"
EXPECTED_ARTIFACTS = {
    "runtime-base": {
        "artifact_id": "cpython-android-cli-3.14.6-android24-aarch64-runtime-base",
        "archive_sha256": "2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743",
        "manifest_sha256": "ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a",
        "owned": 714,
    },
    "development-addon": {
        "artifact_id": "cpython-android-cli-3.14.6-android24-aarch64-development-addon",
        "archive_sha256": "f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea",
        "manifest_sha256": "9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a",
        "owned": 454,
    },
    "test-addon": {
        "artifact_id": "cpython-android-cli-3.14.6-android24-aarch64-test-addon",
        "archive_sha256": "02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1",
        "manifest_sha256": "47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f",
        "owned": 1788,
    },
}
EXPECTED_STATES = {
    "empty": ([], 0),
    "runtime": (["runtime-base"], 714),
    "runtime-development": (["runtime-base", "development-addon"], 1168),
    "runtime-test": (["runtime-base", "test-addon"], 2502),
    "composed": (["runtime-base", "development-addon", "test-addon"], 2956),
}


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(cjson(value))


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def kind(path: Path) -> str:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return "absent"
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISREG(mode):
        return "regular"
    if stat.S_ISDIR(mode):
        return "directory"
    return "special"


def path_snapshot(path: Path, *, recursive: bool = False) -> dict[str, Any]:
    observed = kind(path)
    result: dict[str, Any] = {"type": observed}
    if observed == "absent":
        return result
    st = path.lstat()
    result["mode"] = f"{stat.S_IMODE(st.st_mode):04o}"
    if observed == "regular":
        result.update(size=st.st_size, sha256=sha256_file(path))
    elif observed == "symlink":
        result["target"] = os.readlink(path)
    elif observed == "directory" and recursive:
        rows: list[dict[str, Any]] = []
        for child in sorted(path.rglob("*"), key=lambda p: p.relative_to(path).as_posix()):
            row = path_snapshot(child)
            row["path"] = child.relative_to(path).as_posix()
            rows.append(row)
        result["entries"] = rows
    return result


def tree_rows(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        row = path_snapshot(path)
        row["path"] = path.relative_to(root).as_posix()
        rows.append(row)
    return rows


def tree_digest(root: Path) -> str:
    return sha256_bytes(cjson(tree_rows(root)))


def transaction_inventory(root: Path) -> list[dict[str, Any]]:
    transactions_root = root / ".cpython-android-cli/transactions"
    if not transactions_root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for tx in sorted(p for p in transactions_root.iterdir() if p.is_dir()):
        journal = tx / "journal.json"
        rows.append(
            {
                "name": tx.name,
                "journal": read_json(journal) if journal.is_file() else None,
                "tree_digest": tree_digest(tx),
            }
        )
    return rows


def registry_value(root: Path) -> dict[str, Any]:
    path = root / ".cpython-android-cli/registry.json"
    if not path.is_file():
        return {
            "exists": False,
            "sha256": None,
            "artifact_names": [],
            "artifact_count": 0,
            "owned_path_count": 0,
            "value": None,
        }
    data = path.read_bytes()
    value = json.loads(data)
    return {
        "exists": True,
        "sha256": sha256_bytes(data),
        "artifact_names": [row["artifact"] for row in value.get("artifacts", [])],
        "artifact_count": len(value.get("artifacts", [])),
        "owned_path_count": len(value.get("owned_paths", [])),
        "value": value,
    }


def product_snapshot(root: Path) -> dict[str, Any]:
    """Snapshot mutation-sensitive product state, excluding lock infrastructure."""
    prefix_rows = tree_rows(root / "prefix")
    registry = registry_value(root)
    transactions = transaction_inventory(root)
    identity = {
        "prefix_entries": prefix_rows,
        "registry": registry,
        "transactions": transactions,
    }
    return {
        "prefix_entry_count": len(prefix_rows),
        "prefix_digest": sha256_bytes(cjson(prefix_rows)),
        "registry": registry,
        "transactions": transactions,
        "identity_sha256": sha256_bytes(cjson(identity)),
    }


def rows_from_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "path": entry["payload_path"],
            "type": entry["type"],
            "mode": entry["mode"],
            "size": entry.get("size"),
            "sha256": entry.get("sha256"),
            "target": entry.get("symlink_target"),
            "entry_class": entry["entry_class"],
        }
        for entry in manifest["entries"]
        if entry["entry_class"] == "OWNED_PAYLOAD"
    ]


def exact_match(path: Path, row: dict[str, Any]) -> bool:
    observed = path_snapshot(path)
    if observed.get("type") != row.get("type") or observed.get("mode") != row.get("mode"):
        return False
    if row["type"] == "regular":
        return observed.get("size") == row.get("size") and observed.get("sha256") == row.get("sha256")
    if row["type"] == "symlink":
        return observed.get("target") == row.get("target")
    return True


def owned_digest(root: Path, rows: Iterable[dict[str, Any]]) -> str:
    values: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda r: r["path"]):
        observed = path_snapshot(root / "prefix" / row["path"])
        observed["path"] = row["path"]
        values.append(observed)
    return sha256_bytes(cjson(values))


def choose_regular(rows: list[dict[str, Any]], *, preferred: str | None = None) -> dict[str, Any]:
    by_path = {row["path"]: row for row in rows}
    if preferred and preferred in by_path and by_path[preferred]["type"] == "regular":
        return by_path[preferred]
    candidates = [row for row in rows if row["type"] == "regular"]
    if not candidates:
        raise RuntimeError("manifest has no regular candidate")
    return candidates[0]


def clone_seed(seed: Path, destination: Path, probes: Iterable[str]) -> dict[str, bool]:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    copied = False
    cp = shutil.which("cp")
    if cp is not None:
        completed = subprocess.run(
            [cp, "-a", "--reflink=auto", str(seed), str(destination)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        copied = completed.returncode == 0
    if not copied:
        shutil.rmtree(destination, ignore_errors=True)
        shutil.copytree(seed, destination, symlinks=True, copy_function=shutil.copy2)
    checks = {
        "root_inode_separate": seed.stat().st_ino != destination.stat().st_ino,
    }
    source_registry = seed / ".cpython-android-cli/registry.json"
    target_registry = destination / ".cpython-android-cli/registry.json"
    if source_registry.is_file():
        checks["registry_inode_separate"] = source_registry.stat().st_ino != target_registry.stat().st_ino
    else:
        checks["registry_absent_in_empty_seed"] = not target_registry.exists()
    for relative in probes:
        source = seed / "prefix" / relative
        target = destination / "prefix" / relative
        if source.exists() or source.is_symlink():
            key = "probe_" + relative.replace("/", "_").replace(".", "_")
            checks[key] = source.lstat().st_ino != target.lstat().st_ino
    return checks


def invoke_engine(
    *,
    runner: Path,
    engine: Path,
    contract: Path,
    root: Path,
    operation: str,
    output: Path,
    artifact: str | None = None,
    crash_boundary: str | None = None,
    intent_ordinal: int | None = None,
    nonblocking: bool = False,
    fast_success: bool = False,
) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-I",
        "-B",
        "-S",
        str(runner),
        str(engine),
        "--installation-root",
        str(root),
        "--operation",
        operation,
        "--output",
        str(output),
    ]
    if operation == "install":
        command.extend(("--contract-results", str(contract)))
    if operation == "uninstall":
        command.extend(("--contract-results", str(contract)))
    if artifact:
        command.extend(("--artifact", artifact))
    if nonblocking:
        command.append("--nonblocking-lock")
    if os.environ.get("GATE3C_FAST_SUCCESS") == "1" and crash_boundary is None and operation in {"install", "uninstall"}:
        fast_success = True
    if fast_success:
        command.append("--fast-success")
    if crash_boundary == "PREPARED":
        command.append("--crash-after-prepared")
    elif crash_boundary == "LATE_APPLYING":
        command.extend(("--crash-after-intents", str(intent_ordinal)))
    elif crash_boundary == "COMMITTED":
        command.append("--crash-after-commit")
    elif crash_boundary is not None:
        raise ValueError(crash_boundary)

    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    stdout_path = output.with_name(output.stem + ".stdout.txt")
    stderr_path = output.with_name(output.stem + ".stderr.txt")
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    result = read_json(output) if output.is_file() else None
    process = {
        "command": command,
        "returncode": completed.returncode,
        "stdout_file": stdout_path.name,
        "stderr_file": stderr_path.name,
        "output_file": output.name,
        "output_exists": output.is_file(),
        "result": result,
    }
    write_json(output.with_name(output.stem + "-process.json"), process)
    return process


def start_lock_holder(
    *, runner: Path, engine: Path, root: Path, output: Path, ready: Path, seconds: float = 30.0
) -> subprocess.Popen[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-I",
        "-B",
        "-S",
        str(runner),
        str(engine),
        "--installation-root",
        str(root),
        "--operation",
        "hold-lock",
        "--hold-seconds",
        str(seconds),
        "--ready-file",
        str(ready),
        "--output",
        str(output),
    ]
    stdout = output.with_name(output.stem + ".stdout.txt").open("w", encoding="utf-8")
    stderr = output.with_name(output.stem + ".stderr.txt").open("w", encoding="utf-8")
    process = subprocess.Popen(command, stdout=stdout, stderr=stderr, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    process._gate3c_streams = (stdout, stderr)  # type: ignore[attr-defined]
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if ready.is_file():
            return process
        if process.poll() is not None:
            break
        time.sleep(0.05)
    process.terminate()
    process.wait(timeout=5)
    for stream in process._gate3c_streams:  # type: ignore[attr-defined]
        stream.close()
    raise RuntimeError("lock holder did not become ready")


def stop_lock_holder(process: subprocess.Popen[str]) -> int:
    process.terminate()
    try:
        rc = process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        rc = process.wait(timeout=5)
    for stream in process._gate3c_streams:  # type: ignore[attr-defined]
        stream.close()
    return rc


def run_command(command: list[str], *, output_prefix: Path, env: dict[str, str | None] | None = None) -> dict[str, Any]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    process_env = dict(os.environ)
    for key, value in (env or {}).items():
        if value is None:
            process_env.pop(key, None)
        else:
            process_env[key] = value
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=process_env,
            check=False,
        )
        returncode = completed.returncode
        stdout_text = completed.stdout
        stderr_text = completed.stderr
        error = None
    except OSError as exc:
        returncode = 127
        stdout_text = ""
        stderr_text = repr(exc) + "\n"
        error = repr(exc)
    stdout_path = output_prefix.with_suffix(".stdout.txt")
    stderr_path = output_prefix.with_suffix(".stderr.txt")
    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")
    result = {
        "command": command,
        "returncode": returncode,
        "stdout_file": stdout_path.name,
        "stderr_file": stderr_path.name,
        "error": error,
    }
    write_json(output_prefix.with_suffix(".process.json"), result)
    return result


def state_check(root: Path, state_name: str) -> dict[str, Any]:
    expected_artifacts, expected_owned = EXPECTED_STATES[state_name]
    registry = registry_value(root)
    check = {
        "state": state_name,
        "expected_artifacts": expected_artifacts,
        "expected_owned_path_count": expected_owned,
        "observed_artifacts": registry["artifact_names"],
        "observed_owned_path_count": registry["owned_path_count"],
        "pass": registry["artifact_names"] == expected_artifacts and registry["owned_path_count"] == expected_owned,
    }
    return check


def validate_archive_members(archive: Path) -> dict[str, Any]:
    regular = directories = symlinks = special = unsafe = 0
    with tarfile.open(archive, "r:gz") as container:
        members = container.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts:
                unsafe += 1
            if member.isdir():
                directories += 1
            elif member.isfile():
                regular += 1
            elif member.issym() or member.islnk():
                symlinks += 1
            else:
                special += 1
    return {
        "member_count": len(members),
        "regular": regular,
        "directories": directories,
        "symlinks": symlinks,
        "special": special,
        "unsafe": unsafe,
        "pass": unsafe == 0 and symlinks == 0 and special == 0,
    }


def verify_result_index(root: Path, index_path: Path) -> dict[str, Any]:
    index = read_json(index_path)
    failed: list[str] = []
    for row in index.get("files", []):
        path = root / row["path"]
        if row["type"] == "regular":
            if not path.is_file() or path.is_symlink() or path.stat().st_size != row["size"] or sha256_file(path) != row["sha256"]:
                failed.append(row["path"])
        elif row["type"] == "symlink":
            if not path.is_symlink() or os.readlink(path) != row["target"]:
                failed.append(row["path"])
        else:
            failed.append(row["path"])
    return {
        "indexed_count": index.get("file_count"),
        "checked_count": len(index.get("files", [])),
        "failed": failed,
        "pass": index.get("file_count") == len(index.get("files", [])) and not failed,
    }


def write_result_index(root: Path, output: Path, *, kind_name: str) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        if path == output or path.is_dir():
            continue
        rel = path.relative_to(root).as_posix()
        observed = path_snapshot(path)
        if observed["type"] not in {"regular", "symlink"}:
            raise RuntimeError(f"unsupported result entry: {path}")
        observed["path"] = rel
        files.append(observed)
    result = {"schema_version": 1, "index_kind": kind_name, "file_count": len(files), "files": files}
    write_json(output, result)
    return result

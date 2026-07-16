#!/usr/bin/env python3
"""Stable build/package/verify façade for the Epoch 2 standalone product."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def project_values() -> dict[str, str]:
    required = {
        "target_id": "TARGET_ID",
        "target_host": "TARGET_HOST",
        "build_profile": "BUILD_PROFILE",
        "python_version": "PYTHON_VERSION",
        "python_mm": "PYTHON_MM",
    }
    values: dict[str, str] = {}
    missing: list[str] = []
    for key, env_name in required.items():
        value = os.environ.get(env_name, "")
        if not value:
            missing.append(env_name)
        values[key] = value
    if missing:
        raise RuntimeError(f"missing project environment: {', '.join(missing)}")
    return values


def format_path(template: str, values: dict[str, str]) -> str:
    return template.format(**values)


def validate_contract(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    checks["schema_version"] = contract.get("schema_version") == 1
    checks["contract_version"] = contract.get("contract_version") == 1
    checks["facade_kind"] = contract.get("facade_kind") == "hw-t-standalone-build-package-verify-facade"
    checks["stable_command"] = contract.get("stable_command") == "components/standalone/bin/cpython-android-standalone"

    tracked = contract.get("tracked_inputs", [])
    steps = contract.get("operations", {}).get("build", {}).get("steps", [])
    rows = [*tracked, *steps]
    observed: list[dict[str, Any]] = []
    for row in rows:
        path = root / str(row.get("path", ""))
        expected = row.get("blob_sha")
        actual = None
        if path.is_file():
            proc = git(root, "hash-object", "--", str(path.relative_to(root)), check=False)
            if proc.returncode == 0:
                actual = proc.stdout.strip()
        observed.append({"path": str(row.get("path", "")), "expected_blob": expected, "actual_blob": actual})
    checks["tracked_paths_unique"] = len({item["path"] for item in observed}) == len(observed)
    checks["tracked_blobs_exact"] = bool(observed) and all(item["actual_blob"] == item["expected_blob"] for item in observed)

    operations = contract.get("operations", {})
    checks["operations_exact"] = set(operations) == {"build", "package", "verify"}
    checks["verify_scopes_exact"] = operations.get("verify", {}).get("scopes") == ["repository", "envelope"]
    checks["package_contract"] = (
        operations.get("package", {}).get("primary_flavor") == "install_only_stripped"
        and operations.get("package", {}).get("archive_root") == "python/"
        and operations.get("package", {}).get("payload_classes") == ["runtime", "development"]
    )
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "tracked_inputs": observed,
    }


def resolve_build_plan(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    values = project_values()
    operation = contract["operations"]["build"]
    steps = [
        {
            "id": row["id"],
            "command": ["bash", str(root / row["path"])],
            "path": row["path"],
            "expected_blob": row["blob_sha"],
            "expected_marker": row["marker"],
        }
        for row in operation["steps"]
    ]
    outputs = [format_path(item, values) for item in operation["outputs"]]
    return {
        "schema_version": 1,
        "operation": "build",
        "host_role": operation["host_role"],
        "steps": steps,
        "outputs": outputs,
        "receipt": operation["receipt"],
    }


def resolve_package_plan(root: Path, contract: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    values = project_values()
    operation = contract["operations"]["package"]
    source_prefix = args.source_prefix or root / format_path(operation["input_prefix"], values)
    launcher = args.launcher or root / format_path(operation["input_launcher"], values)
    output_dir = args.output_dir or root / format_path(operation["output_dir"], values)
    strip_tool = args.strip_tool or os.environ.get("ANDROID_STRIP", "")
    if not strip_tool:
        cc = os.environ.get("ANDROID_CC", "")
        if cc:
            candidate = Path(cc).with_name("llvm-strip")
            if candidate.is_file():
                strip_tool = str(candidate)
    command = [
        sys.executable,
        str(root / operation["implementation"]),
        "--root",
        str(root),
        "--source-prefix",
        str(source_prefix),
        "--launcher",
        str(launcher),
        "--output-dir",
        str(output_dir),
    ]
    if strip_tool:
        command.extend(["--strip-tool", strip_tool])
    return {
        "schema_version": 1,
        "operation": "package",
        "host_role": operation["host_role"],
        "source_prefix": str(source_prefix),
        "launcher": str(launcher),
        "output_dir": str(output_dir),
        "strip_tool": strip_tool or None,
        "command": command,
    }


def ensure_role(expected: str) -> None:
    actual = os.environ.get("PROJECT_ROLE", "")
    if actual != expected:
        raise RuntimeError(f"operation requires PROJECT_ROLE={expected}; observed {actual or '<unset>'}")


def output_identity(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if not path.is_file():
        raise FileNotFoundError(f"expected output is missing: {path}")
    return {
        "path": rel,
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def run_build(root: Path, contract: dict[str, Any], dry_run: bool) -> int:
    plan = resolve_build_plan(root, contract)
    validation = validate_contract(root, contract)
    if not validation["pass"]:
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 2
    if dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    ensure_role(plan["host_role"])

    receipt_path = root / plan["receipt"]
    log_dir = receipt_path.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    step_results: list[dict[str, Any]] = []
    for step in plan["steps"]:
        log_path = log_dir / f"{step['id']}.log"
        with log_path.open("wb") as log:
            proc = subprocess.run(step["command"], cwd=root, stdout=log, stderr=subprocess.STDOUT)
        text = log_path.read_text(encoding="utf-8", errors="replace")
        marker_present = step["expected_marker"] in text
        result = {
            "id": step["id"],
            "path": step["path"],
            "returncode": proc.returncode,
            "expected_marker": step["expected_marker"],
            "marker_present": marker_present,
            "log": str(log_path.relative_to(root)),
        }
        step_results.append(result)
        if proc.returncode != 0 or not marker_present:
            receipt = {
                "schema_version": 1,
                "receipt_kind": "hw-t-standalone-build-receipt",
                "status": "failed",
                "contract_version": contract["contract_version"],
                "steps": step_results,
                "outputs": [],
            }
            receipt_path.write_bytes(canonical_json_bytes(receipt))
            print(json.dumps(receipt, indent=2, sort_keys=True))
            return proc.returncode or 3

    outputs = [output_identity(root, rel) for rel in plan["outputs"]]
    receipt = {
        "schema_version": 1,
        "receipt_kind": "hw-t-standalone-build-receipt",
        "status": "passed",
        "contract_version": contract["contract_version"],
        "repository": {
            "commit": git(root, "rev-parse", "HEAD").stdout.strip(),
            "tree": git(root, "rev-parse", "HEAD^{tree}").stdout.strip(),
        },
        "steps": step_results,
        "outputs": outputs,
    }
    receipt_path.write_bytes(canonical_json_bytes(receipt))
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


def run_package(root: Path, contract: dict[str, Any], args: argparse.Namespace) -> int:
    plan = resolve_package_plan(root, contract, args)
    validation = validate_contract(root, contract)
    if not validation["pass"]:
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 2
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    ensure_role(plan["host_role"])
    if not plan["strip_tool"]:
        raise RuntimeError("ANDROID_STRIP is unset and llvm-strip could not be derived from ANDROID_CC")
    return subprocess.run(plan["command"], cwd=root).returncode


def run_verify(root: Path, contract: dict[str, Any], args: argparse.Namespace) -> int:
    operation = contract["operations"]["verify"]
    if args.scope == "repository":
        command = [sys.executable, str(root / operation["repository_implementation"]), "--root", str(root)]
    else:
        if args.release_dir is None:
            raise RuntimeError("--release-dir is required for --scope envelope")
        command = [
            sys.executable,
            str(root / operation["envelope_implementation"]),
            "--root",
            str(root),
            "--release-dir",
            str(args.release_dir),
        ]
    if args.dry_run:
        print(json.dumps({"schema_version": 1, "operation": "verify", "scope": args.scope, "command": command}, indent=2, sort_keys=True))
        return 0
    return subprocess.run(command, cwd=root).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cpython-android-standalone")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan")
    plan.add_argument("operation", choices=("build", "package", "verify"))
    plan.add_argument("--scope", choices=("repository", "envelope"), default="repository")
    plan.add_argument("--release-dir", type=Path)
    plan.add_argument("--source-prefix", type=Path)
    plan.add_argument("--launcher", type=Path)
    plan.add_argument("--output-dir", type=Path)
    plan.add_argument("--strip-tool")

    build = sub.add_parser("build")
    build.add_argument("--dry-run", action="store_true")

    package = sub.add_parser("package")
    package.add_argument("--dry-run", action="store_true")
    package.add_argument("--source-prefix", type=Path)
    package.add_argument("--launcher", type=Path)
    package.add_argument("--output-dir", type=Path)
    package.add_argument("--strip-tool")

    verify = sub.add_parser("verify")
    verify.add_argument("--scope", choices=("repository", "envelope"), default="repository")
    verify.add_argument("--release-dir", type=Path)
    verify.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.resolve()
    contract = read_json(args.contract.resolve())
    try:
        if args.command == "build":
            return run_build(root, contract, args.dry_run)
        if args.command == "package":
            return run_package(root, contract, args)
        if args.command == "verify":
            return run_verify(root, contract, args)
        if args.command == "plan":
            if args.operation == "build":
                result = resolve_build_plan(root, contract)
            elif args.operation == "package":
                result = resolve_package_plan(root, contract, args)
            else:
                operation = contract["operations"]["verify"]
                impl = operation["repository_implementation"] if args.scope == "repository" else operation["envelope_implementation"]
                result = {"schema_version": 1, "operation": "verify", "scope": args.scope, "implementation": impl}
            result["contract_validation"] = validate_contract(root, contract)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["contract_validation"]["pass"] else 2
        raise AssertionError(args.command)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

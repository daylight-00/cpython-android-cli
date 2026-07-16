#!/usr/bin/env python3
"""Independently verify the E2-P2 Gate 1 standalone façade authority."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

TARGET_BRANCH = "agent/epoch2-p2-standalone-build-facade"
E2P1_HEAD = "68828691fcae382cf49b9dbc2b5231f9e21f9282"
E2P1_TREE = "eea4b6e7c8ffb3b49f2b3c45e9ac0639055bb118"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path, errors: dict[str, str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors[str(path)] = f"{type(exc).__name__}: {exc}"
        return {}
    if not isinstance(value, dict):
        errors[str(path)] = "top-level value is not an object"
        return {}
    return value


def progress(label: str) -> None:
    print(f"E2P2_VERIFY_PHASE={label}", file=sys.stderr, flush=True)


def run(
    command: list[str],
    root: Path,
    env: dict[str, str] | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    # File-backed capture avoids pipe-EOF deadlocks when a regression child
    # launches compiler or compressor grandchildren that inherit stdio.
    with tempfile.TemporaryDirectory(prefix="e2p2-verify-capture-") as temp_name:
        stdout_path = Path(temp_name) / "stdout"
        stderr_path = Path(temp_name) / "stderr"
        with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
            try:
                proc = subprocess.run(
                    command,
                    cwd=root,
                    env=env,
                    text=True,
                    stdout=stdout,
                    stderr=stderr,
                    timeout=timeout,
                )
                returncode = proc.returncode
            except subprocess.TimeoutExpired:
                returncode = 124
                stderr.write(f"timeout after {timeout}s: {' '.join(command)}\n")
        return subprocess.CompletedProcess(
            command,
            returncode,
            stdout_path.read_text(encoding="utf-8", errors="replace"),
            stderr_path.read_text(encoding="utf-8", errors="replace"),
        )


def parse_json_stdout(proc: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        value = json.loads(proc.stdout)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def source_compiles(path: Path) -> bool:
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        return True
    except Exception:
        return False


def project_env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    defaults = root / "config/defaults.env"
    if defaults.is_file():
        for raw in defaults.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.replace("_", "").isalnum():
                env.setdefault(key, value.strip().strip('"').strip("'"))
    env.setdefault("PROJECT_ROLE", "termux")
    return env


def verify(root: Path) -> dict[str, Any]:
    root = root.resolve()
    experiment = root / "experiments/epoch2-standalone-build-facade"
    authority_path = experiment / "e2p2-gate1-authority.json"
    parse_errors: dict[str, str] = {}
    missing: list[str] = []
    required = [
        root / "components/standalone/bin/cpython-android-standalone",
        root / "components/standalone/contracts/facade-v1.json",
        root / "components/standalone/lib/facade.py",
        root / "components/standalone/lib/package_e2p1.py",
        root / "components/standalone/lib/verify_envelope.py",
        experiment / "README.md",
        experiment / "E2P2_GATE1_STANDALONE_FACADE.md",
        experiment / "test-e2p2-standalone-facade.py",
        experiment / "verify-e2p2-standalone-facade.py",
        experiment / "run-e2p2-standalone-facade.sh",
        authority_path,
        root / "docs/contracts/E2P2_STANDALONE_FACADE_CONTRACT.md",
        root / "docs/evidence/E2P2_GATE1_STANDALONE_FACADE_RESULT.md",
        root / "docs/handoff/2026-07-16-epoch2-p2-gate1-standalone-facade.md",
    ]
    for path in required:
        if not path.is_file():
            missing.append(str(path))

    contract_path = root / "components/standalone/contracts/facade-v1.json"
    contract = read_json(contract_path, parse_errors) if contract_path.is_file() else {}
    authority = read_json(authority_path, parse_errors) if authority_path.is_file() else {}
    checks: dict[str, bool] = {}

    branch = run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], root)
    checks["branch_active"] = branch.returncode == 0 and branch.stdout.strip() == TARGET_BRANCH
    checks["git_diff_check"] = run(["git", "diff", "--check", "HEAD"], root).returncode == 0
    checks["contract_identity"] = (
        contract.get("schema_version") == 1
        and contract.get("contract_version") == 1
        and contract.get("facade_kind") == "hw-t-standalone-build-package-verify-facade"
        and contract.get("stable_command") == "components/standalone/bin/cpython-android-standalone"
    )
    predecessor = contract.get("predecessor", {})
    checks["contract_predecessor"] = predecessor.get("e2p1_commit") == E2P1_HEAD and predecessor.get("e2p1_tree") == E2P1_TREE
    operations = contract.get("operations", {})
    checks["operations_exact"] = set(operations) == {"build", "package", "verify"}
    build = operations.get("build", {})
    package = operations.get("package", {})
    verify_op = operations.get("verify", {})
    checks["build_contract"] = (
        build.get("host_role") == "workstation"
        and [row.get("id") for row in build.get("steps", [])] == ["prepare-replay", "run-replay", "promote-product", "build-launcher"]
        and len(build.get("outputs", [])) == 5
        and build.get("receipt") == "results/workstation/epoch2-standalone/build-receipt.json"
    )
    checks["package_contract"] = (
        package.get("host_role") == "workstation"
        and package.get("primary_flavor") == "install_only_stripped"
        and package.get("archive_root") == "python/"
        and package.get("payload_classes") == ["runtime", "development"]
        and package.get("implementation") == "components/standalone/lib/package_e2p1.py"
    )
    checks["verify_contract"] = verify_op.get("scopes") == ["repository", "envelope"] and verify_op.get("envelope_implementation") == "components/standalone/lib/verify_envelope.py"

    tracked = [*contract.get("tracked_inputs", []), *build.get("steps", [])]
    observed: dict[str, str | None] = {}
    for row in tracked:
        rel = row.get("path")
        if not isinstance(rel, str):
            continue
        path = root / rel
        proc = run(["git", "hash-object", "--", rel], root) if path.is_file() else None
        observed[rel] = proc.stdout.strip() if proc and proc.returncode == 0 else None
    checks["tracked_paths_unique"] = len(observed) == len(tracked)
    checks["tracked_blobs_exact"] = bool(tracked) and all(observed.get(row.get("path")) == row.get("blob_sha") for row in tracked)

    shell_files = [root / "components/standalone/bin/cpython-android-standalone", experiment / "run-e2p2-standalone-facade.sh"]
    checks["shell_syntax"] = all(run(["bash", "-n", str(path)], root).returncode == 0 for path in shell_files if path.is_file()) and len(shell_files) == 2
    python_files = [
        root / "components/standalone/lib/facade.py",
        root / "components/standalone/lib/package_e2p1.py",
        root / "components/standalone/lib/verify_envelope.py",
        experiment / "test-e2p2-standalone-facade.py",
        experiment / "verify-e2p2-standalone-facade.py",
    ]
    checks["python_syntax"] = all(path.is_file() and source_compiles(path) for path in python_files)

    env = project_env(root)
    progress("facade-plans")
    facade = root / "components/standalone/lib/facade.py"
    plan_results = []
    if facade.is_file() and contract_path.is_file():
        for operation in ("build", "package", "verify"):
            command = [sys.executable, str(facade), "--root", str(root), "--contract", str(contract_path), "plan", operation]
            proc = run(command, root, env=env)
            plan_results.append((proc, parse_json_stdout(proc)))
    checks["facade_plans"] = len(plan_results) == 3 and all(proc.returncode == 0 and data.get("contract_validation", {}).get("pass") is True for proc, data in plan_results)

    progress("regression-tests")
    test_proc = run([sys.executable, str(experiment / "test-e2p2-standalone-facade.py")], root, env={**env, "PYTHONDONTWRITEBYTECODE": "1"}, timeout=180) if (experiment / "test-e2p2-standalone-facade.py").is_file() else None
    test_result = parse_json_stdout(test_proc) if test_proc else {}
    checks["regression_tests"] = bool(test_proc and test_proc.returncode == 0 and test_result.get("pass") is True and test_result.get("test_count") == 3 and test_result.get("pass_count") == 3)

    progress("e2p1-preservation")
    e2p1 = root / "experiments/epoch2-standalone-artifact-contract/verify-e2p1-standalone-artifact-contract.py"
    e2p1_proc = run([sys.executable, str(e2p1), "--root", str(root)], root, env={**env, "PYTHONDONTWRITEBYTECODE": "1"}) if e2p1.is_file() else None
    e2p1_result = parse_json_stdout(e2p1_proc) if e2p1_proc else {}
    checks["e2p1_preserved"] = bool(e2p1_proc and e2p1_proc.returncode == 0 and e2p1_result.get("pass") is True and e2p1_result.get("check_count") == 68 and e2p1_result.get("pass_count") == 68)

    progress("epoch1-control")
    predecessor_verifier = root / "scripts/verify-project-control-plane.py"
    predecessor_proc = run([sys.executable, str(predecessor_verifier), "--root", str(root)], root, env={**env, "PYTHONDONTWRITEBYTECODE": "1"}) if predecessor_verifier.is_file() else None
    predecessor_result = parse_json_stdout(predecessor_proc) if predecessor_proc else {}
    checks["epoch1_control_preserved"] = bool(
        predecessor_proc
        and predecessor_proc.returncode == 1
        and predecessor_result.get("check_count") == 129
        and predecessor_result.get("pass_count") == 128
        and predecessor_result.get("failed_checks") == ["branch_active"]
    )

    progress("epoch1-fixtures")
    fixture_suite = root / "scripts/test-verify-project-control-plane.py"
    fixture_proc = run([sys.executable, str(fixture_suite), "--root", str(root)], root, env={**env, "PYTHONDONTWRITEBYTECODE": "1"}) if fixture_suite.is_file() else None
    fixture_result = parse_json_stdout(fixture_proc) if fixture_proc else {}
    checks["epoch1_fixture_suite"] = bool(fixture_proc and fixture_proc.returncode == 0 and fixture_result.get("pass") is True)

    progress("authority-and-docs")
    file_identities = authority.get("file_identities", {})
    checks["authority_identity"] = (
        authority.get("schema_version") == 1
        and authority.get("authority_kind") == "epoch2-p2-gate1-standalone-build-package-verify-facade"
        and authority.get("status") == "gate1-frozen-repository-facade"
        and authority.get("repository_input") == {"branch": "agent/epoch2-p1-standalone-artifact-contract", "head": E2P1_HEAD, "tree": E2P1_TREE}
    )
    checks["authority_file_identities"] = isinstance(file_identities, dict) and bool(file_identities) and all((root / path).is_file() and sha256_file(root / path) == digest for path, digest in file_identities.items())
    checks["authority_verification"] = authority.get("verification") == {"independent_check_count": 23, "regression_test_count": 3, "regression_pass_count": 3}
    checks["authority_claim_boundary"] = authority.get("claim_boundary") == {
        "real_cpython_build": False,
        "real_release_envelope": False,
        "android_execution": False,
        "termux_qualification": False,
        "selectability": False,
        "publication": False,
        "installer_conversion": False,
    }

    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").is_file() else ""
    current = (root / "docs/CURRENT_CONTEXT.md").read_text(encoding="utf-8") if (root / "docs/CURRENT_CONTEXT.md").is_file() else ""
    roadmap = (root / "docs/roadmap/EPOCH2_ROADMAP.md").read_text(encoding="utf-8") if (root / "docs/roadmap/EPOCH2_ROADMAP.md").is_file() else ""
    checks["documentation_status"] = (
        "Epoch 2 P2 Gate 1 standalone façade" in readme
        and "E2-P2 Gate 1 frozen" in current
        and "> **Status:** ACTIVE — Gate 1 frozen; Gate 2 next" in roadmap
    )
    bytecode_roots = [
        root / "components/standalone",
        root / "experiments/epoch2-standalone-build-facade",
    ]
    checks["no_new_bytecode_residue"] = not any(
        path.is_file() and (path.suffix == ".pyc" or "__pycache__" in path.parts)
        for owned_root in bytecode_roots
        if owned_root.exists()
        for path in owned_root.rglob("*")
    )

    progress("complete")
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": 1,
        "verification_kind": "epoch2-p2-gate1-standalone-facade",
        "pass": not failed and not missing and not parse_errors,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "failed_checks": failed,
        "missing_files": sorted(set(missing)),
        "parse_errors": parse_errors,
        "checks": dict(sorted(checks.items())),
        "regression": test_result,
        "e2p1": {"pass": e2p1_result.get("pass"), "check_count": e2p1_result.get("check_count"), "pass_count": e2p1_result.get("pass_count")},
        "predecessor": {"pass": predecessor_result.get("pass"), "check_count": predecessor_result.get("check_count"), "pass_count": predecessor_result.get("pass_count"), "failed_checks": predecessor_result.get("failed_checks")},
        "claim_boundary": "Repository façade implementation and synthetic deterministic package verification only. A real CPython build, real release envelope, Android/Termux execution, qualification, selectability, publication, and installer conversion remain unclaimed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    result = verify(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

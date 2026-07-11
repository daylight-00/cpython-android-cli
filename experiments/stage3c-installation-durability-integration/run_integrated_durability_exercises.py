#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def run_engine(
    engine: Path,
    contract: Path,
    root: Path,
    operation: str,
    output: Path,
    *,
    artifact: str | None = None,
    extra: list[str] | None = None,
    expected_rc: int = 0,
) -> tuple[dict[str, Any], int]:
    command = [
        sys.executable,
        str(engine),
        "--installation-root",
        str(root),
        "--operation",
        operation,
        "--output",
        str(output),
    ]
    if operation in {"install", "uninstall"}:
        command.extend(["--contract-results", str(contract)])
    if artifact:
        command.extend(["--artifact", artifact])
    if extra:
        command.extend(extra)
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if output.exists():
        result = read_json(output)
    else:
        result = {
            "operation": operation,
            "artifact": artifact,
            "output_absent": True,
            "process_exit": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        output.write_bytes(canonical_json_bytes(result))
    result["expected_returncode_match"] = completed.returncode == expected_rc
    output.write_bytes(canonical_json_bytes(result))
    return result, completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-results", required=True, type=Path)
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    contract = args.contract_results.resolve()
    engine = args.engine.resolve()
    work = args.work_root.resolve()
    output = args.output_dir.resolve()
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    output.mkdir(parents=True, exist_ok=True)
    checks: dict[str, bool] = {}
    sequence = 0

    def check(name: str, value: bool) -> None:
        checks[name] = bool(value)

    def call(
        name: str,
        root: Path,
        operation: str,
        *,
        artifact: str | None = None,
        extra: list[str] | None = None,
        expected_rc: int = 0,
    ) -> tuple[dict[str, Any], int]:
        nonlocal sequence
        sequence += 1
        return run_engine(
            engine,
            contract,
            root,
            operation,
            output / f"{sequence:02d}-{name}.json",
            artifact=artifact,
            extra=extra,
            expected_rc=expected_rc,
        )

    lifecycle = work / "lifecycle"
    installed, returncode = call(
        "runtime-install",
        lifecycle,
        "install",
        artifact="runtime-base",
        extra=["--fast-success"],
    )
    verified, _ = call("runtime-verify", lifecycle, "verify")
    check(
        "runtime_install_714",
        returncode == 0 and installed.get("action_counts") == {"create": 714},
    )
    check(
        "runtime_verify_714",
        verified.get("pass") is True and verified.get("owned_path_count") == 714,
    )

    registry = read_json(lifecycle / ".cpython-android-cli/registry.json")
    directory_row = next(row for row in registry["owned_paths"] if row["type"] == "directory")
    directory_path = lifecycle / "prefix" / directory_row["path"]
    original_mode = int(directory_row["mode"], 8)
    changed_mode = 0o700 if original_mode != 0o700 else 0o755
    os.chmod(directory_path, changed_mode)
    repaired_directory, _ = call(
        "directory-mode-repair",
        lifecycle,
        "install",
        artifact="runtime-base",
    )
    repaired_directory_verify, _ = call("directory-mode-verify", lifecycle, "verify")
    check(
        "directory_mode_repair_exact",
        repaired_directory.get("pass") is True
        and repaired_directory.get("action_counts") == {"noop": 713, "repair-dir": 1},
    )
    check(
        "directory_mode_repair_verified",
        repaired_directory_verify.get("pass") is True,
    )

    registry = read_json(lifecycle / ".cpython-android-cli/registry.json")
    symlink_row = next(row for row in registry["owned_paths"] if row["type"] == "symlink")
    symlink_path = lifecycle / "prefix" / symlink_row["path"]
    symlink_path.unlink()
    os.symlink("incorrect-target", symlink_path)
    repaired_symlink, _ = call(
        "symlink-repair",
        lifecycle,
        "install",
        artifact="runtime-base",
    )
    repaired_symlink_verify, _ = call("symlink-repair-verify", lifecycle, "verify")
    check(
        "symlink_repair_exact",
        repaired_symlink.get("pass") is True
        and repaired_symlink.get("action_counts") == {"noop": 713, "repair": 1},
    )
    check("symlink_repair_verified", repaired_symlink_verify.get("pass") is True)

    development_install, _ = call(
        "development-install",
        lifecycle,
        "install",
        artifact="development-addon",
        extra=["--fast-success"],
    )
    development_verify, _ = call("development-verify", lifecycle, "verify")
    check(
        "development_install_454",
        development_install.get("action_counts") == {"create": 454},
    )
    check(
        "development_verify_1168",
        development_verify.get("owned_path_count") == 1168
        and development_verify.get("pass") is True,
    )

    development_uninstall, _ = call(
        "development-uninstall",
        lifecycle,
        "uninstall",
        artifact="development-addon",
        extra=["--fast-success"],
    )
    post_development_verify, _ = call(
        "post-development-uninstall-verify",
        lifecycle,
        "verify",
    )
    check("development_uninstall_pass", development_uninstall.get("pass") is True)
    check(
        "post_development_uninstall_714",
        post_development_verify.get("pass") is True
        and post_development_verify.get("owned_path_count") == 714,
    )

    abandoned = lifecycle / ".cpython-android-cli/transactions/abandoned-prepare/staging"
    abandoned.mkdir(parents=True)
    (abandoned / "sentinel").write_text("abandoned\n", encoding="utf-8")
    abandoned_recovery, _ = call("abandoned-prepare-recovery", lifecycle, "recover")
    check(
        "abandoned_prepare_discarded",
        abandoned_recovery.get("pass") is True
        and any(
            item.get("action") == "DISCARDED_PREPARE"
            for item in abandoned_recovery.get("actions", [])
        ),
    )
    check(
        "abandoned_prepare_removed",
        not (lifecycle / ".cpython-android-cli/transactions/abandoned-prepare").exists(),
    )

    runtime_uninstall, _ = call(
        "runtime-uninstall",
        lifecycle,
        "uninstall",
        artifact="runtime-base",
        extra=["--fast-success"],
    )
    empty_verify, _ = call("empty-verify", lifecycle, "verify")
    check("runtime_uninstall_pass", runtime_uninstall.get("pass") is True)
    check(
        "empty_registry_verified",
        empty_verify.get("pass") is True
        and empty_verify.get("artifact_count") == 0
        and empty_verify.get("owned_path_count") == 0,
    )

    registry_crash = work / "registry-precommit"
    crashed, returncode = call(
        "fresh-registry-precommit-crash",
        registry_crash,
        "install",
        artifact="runtime-base",
        extra=["--crash-after-mutations", "715"],
        expected_rc=91,
    )
    recovered, _ = call("fresh-registry-precommit-recovery", registry_crash, "recover")
    recovered_verify, _ = call("fresh-registry-precommit-verify", registry_crash, "verify")
    check(
        "fresh_registry_crash_exit_91",
        returncode == 91 and crashed.get("output_absent") is True,
    )
    check(
        "fresh_registry_crash_rolled_back",
        any(
            item.get("action") == "ROLLED_BACK"
            and item.get("restored_count") == 715
            for item in recovered.get("actions", [])
        ),
    )
    check(
        "fresh_registry_removed",
        recovered_verify.get("pass") is True
        and recovered_verify.get("artifact_count") == 0
        and recovered_verify.get("owned_path_count") == 0,
    )

    log_files = sorted(path.name for path in output.glob("[0-9][0-9]-*.json"))
    check("exercise_log_count_exact", len(log_files) == sequence)
    check(
        "exercise_logs_canonical",
        all(
            path.read_bytes() == canonical_json_bytes(read_json(path))
            for path in output.glob("[0-9][0-9]-*.json")
        ),
    )
    check(
        "work_root_set_exact",
        {path.name for path in work.iterdir()} == {"lifecycle", "registry-precommit"},
    )

    if len(checks) != 20:
        raise RuntimeError(f"unexpected check count: {len(checks)}")
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "observed": {
            "log_count": len(log_files),
            "directory_repair_path": directory_row["path"],
            "symlink_repair_path": symlink_row["path"],
        },
        "claim_boundary": {
            "proved": "Focused integrated exercises cover durable directory metadata repair, symlink repair, successful addon and runtime uninstall cleanup, unjournaled prepare cleanup, and a fresh registry-applied pre-commit rollback.",
            "not_proved": "These focused exercises supplement but do not replace the frozen full recovery and durability replays.",
        },
    }
    (output / "exercise.json").write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] or not args.require_pass else 56


if __name__ == "__main__":
    raise SystemExit(main())

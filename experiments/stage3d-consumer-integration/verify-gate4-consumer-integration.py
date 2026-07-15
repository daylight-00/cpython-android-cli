#!/usr/bin/env python3
"""Independently verify the accepted Stage 3-D Gate 4 result archive."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath

EXPECTED_ARCHIVE_SHA = "13ed73fdeaf5ea13339b2df70b69a4c79aa2920fb1d9207229fb64db828b283c"
EXPECTED_SIZE = 58525
EXPECTED_ROOT = "20260715-stage3d-gate4-consumer-integration-target-validation-v3"
EXPECTED_MEMBER_COUNT = 757
EXPECTED_INDEX_COUNT = 697
EXPECTED_INDEX_SHA = "4351a25986ebb9192542eafe79ad1d8a209d33931ea82a85bf908e5d2bf25acc"
EXPECTED_SUMMARY_SHA = "b1a7864d2144df44ee6cf65e33243592420c659d0069d198f87bc3727566c4a7"
EXPECTED_ROWS_SHA = "d6cd2fe5e751476a2935962f8c0ec88bbb6beb41bf56449e23526d0dd2544def"
EXPECTED_INDEPENDENT_SHA = "c9361f9c148c3d1a170b940a756b6f6b71d15ca957bb4d37e3ac3ea38664ebe5"
EXPECTED_SAFETY_SHA = "450e8b9c6198885509f0b520a002a3226ce0728f457c0565d792a09b02de969a"
EXPECTED_MATRIX_SHA = "9b99beb060573ac2557a16bd3ec7e758b34f0769f417c1967cefdf5cd05a7faa"
EXPECTED_CONTRACT_SHA = "c24f8af1d0af8cf2212a1e40ea0887cc7856fbd725e71759e9969ad8e07acb9e"
EXPECTED_REPOSITORY = {
    "branch": "agent/stage3d-consumer-integration",
    "head": "64a2066d464e437407bc84c85d21e3f04495d02a",
    "remote": "64a2066d464e437407bc84c85d21e3f04495d02a",
    "status": "",
    "tree": "2063517d5786ba179f71faa121e54c3e9b035239",
}
EXPECTED_GROUPS = Counter({
    "explicit-reconfirmation": 8,
    "pending-command-surface": 16,
    "bounded-discovery": 8,
    "transition-continuity": 4,
    "precedence-negative-invariant": 12,
})
EXPECTED_UV_COUNTS = Counter({"python-find": 33, "venv": 18, "run": 16, "sync": 16})


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} RESULT.tar.zst", file=sys.stderr)
        return 2

    archive = Path(sys.argv[1]).resolve()
    checks: dict[str, bool] = {}

    def check(name: str, value: object) -> None:
        checks[name] = bool(value)

    check("archive_exists", archive.is_file())
    if not archive.is_file():
        result = {"pass": False, "failed_checks": ["archive_exists"], "checks": checks}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    check("archive_sha256", sha256(archive) == EXPECTED_ARCHIVE_SHA)
    check("archive_size", archive.stat().st_size == EXPECTED_SIZE)

    with tempfile.TemporaryDirectory(prefix="stage3d-gate4-audit-") as temp_dir:
        temp = Path(temp_dir)
        tar_path = temp / "result.tar"
        with tar_path.open("wb") as output:
            decoded = subprocess.run(
                ["zstd", "-q", "-d", "-c", str(archive)],
                stdout=output,
                stderr=subprocess.PIPE,
                check=False,
            )
        check("zstd_decode", decoded.returncode == 0)
        if decoded.returncode != 0:
            failed = sorted(name for name, passed in checks.items() if not passed)
            print(json.dumps({"pass": False, "failed_checks": failed, "checks": checks}, indent=2, sort_keys=True))
            return 1

        with tarfile.open(tar_path, "r:") as tar:
            members = tar.getmembers()
            names = [member.name for member in members]
            roots = {PurePosixPath(name).parts[0] for name in names if PurePosixPath(name).parts}
            check("member_count", len(members) == EXPECTED_MEMBER_COUNT)
            check("unique_members", len(names) == len(set(names)))
            check("one_root", roots == {EXPECTED_ROOT})
            check("safe_member_types", all(member.isfile() or member.isdir() for member in members))
            check(
                "safe_paths",
                all(
                    not PurePosixPath(member.name).is_absolute()
                    and ".." not in PurePosixPath(member.name).parts
                    for member in members
                ),
            )
            tar.extractall(temp / "extracted", filter="data")

        root = temp / "extracted" / EXPECTED_ROOT
        index = root / "result-index.sha256"
        check("index_sha256", sha256(index) == EXPECTED_INDEX_SHA)
        expected_index: dict[str, str] = {}
        for line in index.read_text(encoding="utf-8").splitlines():
            if line.strip():
                digest, relative = line.split("  ", 1)
                expected_index[relative] = digest
        actual_index = {
            path.relative_to(root).as_posix(): sha256(path)
            for path in root.rglob("*")
            if path.is_file() and path != index
        }
        check("index_count", len(expected_index) == EXPECTED_INDEX_COUNT)
        check("index_exact", expected_index == actual_index)

        summary_file = root / "target-validation" / "validation-summary.json"
        rows_file = root / "target-validation" / "scenario-results.json"
        independent_file = root / "gate4-independent-verification.json"
        safety_file = root / "result-tree-safety.json"
        check("summary_sha256", sha256(summary_file) == EXPECTED_SUMMARY_SHA)
        check("rows_sha256", sha256(rows_file) == EXPECTED_ROWS_SHA)
        check("independent_sha256", sha256(independent_file) == EXPECTED_INDEPENDENT_SHA)
        check("safety_sha256", sha256(safety_file) == EXPECTED_SAFETY_SHA)

        summary = load(summary_file)
        rows = load(rows_file)["scenarios"]
        independent = load(independent_file)
        safety = load(safety_file)

        check("summary_pass", summary.get("pass") is True and not summary.get("failed_checks"))
        check("scenario_count", len(rows) == 48 and summary.get("scenario_count") == 48)
        check(
            "expectation_match",
            summary.get("expectation_match_count") == 48
            and all(row.get("expectation_match") is True for row in rows),
        )
        check("harness_complete", all(row.get("harness_complete") is True for row in rows))
        check("groups", Counter(row["group"] for row in rows) == EXPECTED_GROUPS)
        check("matrix_sha256", summary.get("matrix_sha256") == EXPECTED_MATRIX_SHA)
        check("contract_sha256", summary.get("contract_sha256") == EXPECTED_CONTRACT_SHA)
        check("repository_identity", summary.get("repository") == EXPECTED_REPOSITORY)
        check(
            "invariants",
            all(
                summary["checks"].get(name) is True
                for name in (
                    "authority_immutable",
                    "global_managed_install_dir_immutable",
                    "global_paths_immutable",
                    "repository_immutable",
                    "seed_products_immutable",
                )
            ),
        )
        check("transition_exact", summary["checks"].get("transition_all_exact") is True)
        check("pending_exact_product", summary.get("pending_surface_outcomes") == {"exact-product": 16})
        check("uv_operation_counts", Counter(summary.get("uv_operation_counts", {})) == EXPECTED_UV_COUNTS)
        check(
            "uv_identity",
            summary["uv"].get("version_stdout") == "uv 0.11.28 (aarch64-linux-android)"
            and summary["uv"].get("sha256") == "f624c48a72b2e2e307043f339eb3ff6dbdfa0207be2053d2e5bc071709289495",
        )
        check(
            "independent_27",
            independent.get("pass") is True
            and independent.get("pass_count") == 27
            and independent.get("check_count") == 27
            and not independent.get("failed_checks"),
        )
        check(
            "safety_report",
            safety == {
                "directory_count": 58,
                "entry_count": 754,
                "pass": True,
                "regular_count": 696,
                "root": EXPECTED_ROOT,
                "schema_version": 1,
                "unsafe": [],
            },
        )

        process_files = sorted((root / "target-validation" / "scenarios").rglob("*.process.json"))
        process_records = [load(path) for path in process_files]
        uv_commands = [record.get("command", []) for record in process_records if record.get("command")]
        uv_commands = [command for command in uv_commands if command[0].endswith("/uv")]
        check("process_record_count", len(process_records) == 150)
        check("no_timeouts", all(record.get("timed_out") is False for record in process_records))
        check(
            "raw_streams_present",
            all(
                (path.parent / record[stream]).is_file()
                for path, record in zip(process_files, process_records)
                for stream in ("stdout_file", "stderr_file")
            ),
        )
        check("download_disabled", all("--no-python-downloads" in command for command in uv_commands))
        check("offline_enforced", all("--offline" in command for command in uv_commands))
        check(
            "managed_fallback_disabled",
            all("--no-managed-python" in command for command in uv_commands),
        )
        check(
            "no_mutating_uv_commands",
            all(
                not (
                    len(command) >= 3
                    and command[1] == "python"
                    and command[2] in {"install", "uninstall", "upgrade"}
                )
                for command in uv_commands
            ),
        )

        x05 = next(row for row in rows if row["scenario_id"] == "X05")
        x05_process = x05["observations"]["selection"]["process"]
        check("x05_system_isolation", "--system" in x05_process["command"])
        check(
            "x05_expected_negative",
            x05_process.get("returncode") == 2
            and x05["observations"]["selection"].get("selected_path") is None
            and x05.get("expectation_match") is True,
        )

        before_after = ("repository", "authority", "global", "managed-global", "seed")
        check(
            "before_after_byte_identity",
            all(
                (root / "target-validation" / f"{name}-before.json").read_bytes()
                == (root / "target-validation" / f"{name}-after.json").read_bytes()
                for name in before_after
            ),
        )

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "verification_kind": "stage3d-gate4-accepted-archive-verification",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "observed": {
            "archive_sha256": sha256(archive),
            "archive_size": archive.stat().st_size,
            "member_count": EXPECTED_MEMBER_COUNT,
            "index_count": EXPECTED_INDEX_COUNT,
            "scenario_count": 48,
            "process_record_count": 150,
            "uv_operation_counts": dict(EXPECTED_UV_COUNTS),
        },
        "claim_boundary": (
            "Accepts the frozen system-Python consumer-integration surface for the exact two-product, "
            "four-topology authority. Managed-Python feasibility and third-product compatibility remain unaccepted."
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(
        f"STAGE3D_GATE4_ACCEPTED_ARCHIVE_VERIFICATION={result['pass_count']}/{result['check_count']} "
        f"{'PASS' if result['pass'] else 'FAIL'}"
    )
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

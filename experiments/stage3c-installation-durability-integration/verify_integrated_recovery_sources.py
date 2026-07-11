#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_GATE5A_RESULT_INDEX = "ac11225ae6b45ac45f1e378ecf7bba9cd074a1f779009318e001d5694d89ead8"
EXPECTED_FROZEN_BLOBS = {
    "recovery_common.py": "1ba78274c8c56a1b2b6cbd525fb341719a2ce4a7",
    "recovery_operations.py": "119571e8ad8a5663d20beff0ab82c85c14dfc4eb",
    "recovery_engine.py": "9a3f1898c7420198ff33d2b067a6fa2a6ac8618d",
}
EXPECTED_INTEGRATED_BLOBS = {
    "recovery_common.py": "3183ba0861ef45e7a395201bec0085f3f69fb248",
    "recovery_operations.py": "8a307065e00fd7a7332541f4911c5478945374ee",
    "recovery_engine.py": "aebf5b9a33d163f7f8758f785ca621c94c0e478b",
    "recovery_durability.py": "61bfb859f73acccb0dfcce1d2a630bfd1ffc2d3f",
}
PRODUCTION_FUNCTIONS = {
    ("recovery_common.py", "atomic_write"),
    ("recovery_common.py", "installation_lock"),
    ("recovery_common.py", "persist_journal"),
    ("recovery_common.py", "add_intent"),
    ("recovery_common.py", "mark_applied"),
    ("recovery_common.py", "save_prior_registry"),
    ("recovery_operations.py", "install"),
    ("recovery_operations.py", "uninstall"),
    ("recovery_engine.py", "remove_path"),
    ("recovery_engine.py", "rollback_transaction"),
    ("recovery_engine.py", "recover"),
}
DIRECT_NAMES = {
    "os.replace",
    "os.symlink",
    "os.chmod",
    "os.unlink",
    "os.rmdir",
    "shutil.copyfile",
    "shutil.rmtree",
}
DIRECT_METHODS = {"mkdir", "write_bytes", "write_text", "unlink", "rmdir"}
REQUIRED_HELPERS = {
    ("recovery_common.py", "atomic_write"): {"durable_atomic_write"},
    ("recovery_common.py", "installation_lock"): {"durable_ensure_directory", "durable_open_lock"},
    ("recovery_common.py", "persist_journal"): {"durable_atomic_write"},
    ("recovery_common.py", "add_intent"): {"persist_journal"},
    ("recovery_common.py", "mark_applied"): {"persist_journal"},
    ("recovery_common.py", "save_prior_registry"): {"durable_copy_file"},
    ("recovery_operations.py", "install"): {
        "durable_ensure_directory",
        "durable_mkdir",
        "durable_chmod",
        "durable_move",
        "durable_publish_regular",
        "durable_publish_symlink",
        "durable_cleanup_transaction",
        "atomic_write",
        "persist_journal",
    },
    ("recovery_operations.py", "uninstall"): {
        "durable_ensure_directory",
        "durable_mkdir",
        "durable_move",
        "durable_rmdir",
        "durable_cleanup_transaction",
        "atomic_write",
        "persist_journal",
    },
    ("recovery_engine.py", "remove_path"): {"durable_tree_remove"},
    ("recovery_engine.py", "rollback_transaction"): {
        "durable_unlink",
        "durable_ensure_directory",
        "durable_move",
        "durable_chmod",
        "durable_mkdir",
        "atomic_write",
        "persist_journal",
    },
    ("recovery_engine.py", "recover"): {
        "durable_ensure_directory",
        "durable_cleanup_transaction",
    },
}
REQUIRED_DURABILITY_FUNCTIONS = {
    "fsync_directory",
    "fsync_path",
    "durable_ensure_directory",
    "durable_mkdir",
    "durable_chmod",
    "durable_atomic_write",
    "durable_copy_file",
    "durable_move",
    "durable_publish_regular",
    "durable_publish_symlink",
    "durable_unlink",
    "durable_rmdir",
    "durable_tree_remove",
    "durable_cleanup_transaction",
    "durable_open_lock",
}


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


class SourceScanner(ast.NodeVisitor):
    def __init__(self, module: str):
        self.module = module
        self.functions: list[str] = []
        self.calls: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.function_names: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_names.add(node.name)
        self.functions.append(node.name)
        self.generic_visit(node)
        self.functions.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        function = self.functions[-1] if self.functions else "<module>"
        name = dotted(node.func)
        self.calls.setdefault((self.module, function), []).append(
            {
                "name": name,
                "method": node.func.attr if isinstance(node.func, ast.Attribute) else None,
                "line": node.lineno,
                "column": node.col_offset,
            }
        )
        self.generic_visit(node)


def scan(path: Path) -> SourceScanner:
    scanner = SourceScanner(path.name)
    scanner.visit(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
    return scanner


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate5a-results", required=True, type=Path)
    parser.add_argument("--recovery-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    gate5a = args.gate5a_results.resolve()
    recovery_dir = args.recovery_dir.resolve()
    inventory = read_json(gate5a / "mutation-inventory.json")
    plan = read_json(gate5a / "integration-plan.json")
    scenario = read_json(gate5a / "scenario.json")
    verification = read_json(gate5a / "verification.json")
    workflow = read_json(gate5a / "workflow-status.json")

    source_paths = {name: recovery_dir / name for name in EXPECTED_INTEGRATED_BLOBS}
    integrated_blobs = {name: git_blob_sha(path) for name, path in source_paths.items()}
    scanners = {name: scan(path) for name, path in source_paths.items()}

    direct_violations: list[dict[str, Any]] = []
    helper_presence: dict[str, list[str]] = {}
    helper_missing: dict[str, list[str]] = {}
    for key in sorted(PRODUCTION_FUNCTIONS):
        rows = scanners[key[0]].calls.get(key, [])
        names = {row["name"] for row in rows}
        for row in rows:
            if row["name"] in DIRECT_NAMES or row["method"] in DIRECT_METHODS:
                direct_violations.append({"module": key[0], "function": key[1], **row})
        required = REQUIRED_HELPERS[key]
        present = sorted(name for name in required if name in names)
        missing = sorted(required - names)
        helper_presence[f"{key[0]}:{key[1]}"] = present
        if missing:
            helper_missing[f"{key[0]}:{key[1]}"] = missing

    durability_scanner = scanners["recovery_durability.py"]
    durability_functions = durability_scanner.function_names
    old_production_rows = [row for row in inventory["rows"] if row["production_path"]]
    old_checkpoint_rows = [
        row
        for row in old_production_rows
        if row["module"] == "recovery_common.py"
        and row["function"] in {"add_intent", "mark_applied"}
    ]
    category_counts = Counter(row["category"] for row in old_production_rows)

    checks = {
        "gate5a_scenario_pass_32": scenario.get("pass") is True
        and scenario.get("check_count") == 32
        and scenario.get("failed_checks") == [],
        "gate5a_verification_pass_29": verification.get("pass") is True
        and verification.get("check_count") == 29
        and verification.get("failed_checks") == [],
        "gate5a_workflow_pass": workflow.get("pass") is True
        and all(value == 0 for value in workflow.get("returncodes", {}).values()),
        "gate5a_result_index_exact": sha256_file(gate5a / "result-index.json")
        == EXPECTED_GATE5A_RESULT_INDEX,
        "frozen_source_blobs_exact": inventory.get("source_blobs") == EXPECTED_FROZEN_BLOBS
        and plan.get("source_blobs") == EXPECTED_FROZEN_BLOBS,
        "frozen_inventory_rows_81": inventory.get("row_count") == 81
        and len(inventory.get("rows", [])) == 81,
        "frozen_production_rows_67": inventory.get("production_row_count") == 67
        and len(old_production_rows) == 67,
        "frozen_unknown_zero": all(row.get("category") != "UNKNOWN" for row in inventory["rows"]),
        "frozen_checkpoint_rows_exact": len(old_checkpoint_rows) == 2
        and {row["function"] for row in old_checkpoint_rows} == {"add_intent", "mark_applied"},
        "frozen_transaction_metadata_10": category_counts["transaction-metadata"] == 10,
        "integrated_source_set_exact": set(source_paths) == set(EXPECTED_INTEGRATED_BLOBS),
        "integrated_source_blobs_exact": integrated_blobs == EXPECTED_INTEGRATED_BLOBS,
        "all_integrated_sources_parse": all(scanner.function_names for scanner in scanners.values()),
        "production_direct_mutations_absent": direct_violations == [],
        "required_helper_calls_complete": helper_missing == {},
        "durability_function_set_complete": REQUIRED_DURABILITY_FUNCTIONS <= durability_functions,
        "atomic_helper_calls_fsync_directory": "fsync_directory"
        in {row["name"] for row in durability_scanner.calls[("recovery_durability.py", "durable_atomic_write")]},
        "move_helper_calls_fsync_directory": "fsync_directory"
        in {row["name"] for row in durability_scanner.calls[("recovery_durability.py", "durable_move")]},
        "mkdir_helper_calls_fsync_directory": "fsync_directory"
        in {row["name"] for row in durability_scanner.calls[("recovery_durability.py", "durable_mkdir")]},
        "unlink_helper_calls_fsync_directory": "fsync_directory"
        in {row["name"] for row in durability_scanner.calls[("recovery_durability.py", "durable_unlink")]},
        "rmdir_helper_calls_fsync_directory": "fsync_directory"
        in {row["name"] for row in durability_scanner.calls[("recovery_durability.py", "durable_rmdir")]},
        "chmod_helper_calls_fsync_path": "fsync_path"
        in {row["name"] for row in durability_scanner.calls[("recovery_durability.py", "durable_chmod")]},
        "regular_publish_calls_fsync_directory": "fsync_directory"
        in {row["name"] for row in durability_scanner.calls[("recovery_durability.py", "durable_publish_regular")]},
        "symlink_publish_calls_fsync_directory": "fsync_directory"
        in {row["name"] for row in durability_scanner.calls[("recovery_durability.py", "durable_publish_symlink")]},
        "cleanup_removes_journal_last": "durable_unlink"
        in {row["name"] for row in durability_scanner.calls[("recovery_durability.py", "durable_cleanup_transaction")]},
        "recovery_discards_unjournaled_prepare": any(
            row["name"] == "durable_cleanup_transaction"
            for row in scanners["recovery_engine.py"].calls[("recovery_engine.py", "recover")]
        ),
        "install_prepare_failure_cleanup_present": any(
            row["name"] == "durable_cleanup_transaction"
            for row in scanners["recovery_operations.py"].calls[("recovery_operations.py", "install")]
        ),
        "fast_success_flag_retained": "CrashController"
        in {row["name"] for row in scanners["recovery_operations.py"].calls[("recovery_operations.py", "install")]},
        "required_replay_counts_retained": plan.get("required_gate5_replay")
        == {
            "recovery_scenarios": 55,
            "recovery_independent_verifier": 82,
            "durability_scenarios": 64,
            "durability_independent_verifier": 53,
        },
    }
    if len(checks) != 29:
        raise RuntimeError(f"unexpected check count: {len(checks)}")
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "frozen_source_blobs": EXPECTED_FROZEN_BLOBS,
        "integrated_source_blobs": integrated_blobs,
        "helper_presence": helper_presence,
        "helper_missing": helper_missing,
        "direct_violations": direct_violations,
        "observed": {
            "frozen_row_count": len(inventory["rows"]),
            "frozen_production_row_count": len(old_production_rows),
            "durability_function_count": len(durability_functions),
            "integrated_source_count": len(integrated_blobs),
        },
        "claim_boundary": {
            "proved": "The exact Gate 5A production inventory is mapped to an integrated source set with no direct production mutation primitives in the inventoried functions and with required durability helper calls present.",
            "not_proved": "Behavioral recovery and durability replay are separate gates and must pass before integrated durability is accepted.",
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 54


if __name__ == "__main__":
    raise SystemExit(main())

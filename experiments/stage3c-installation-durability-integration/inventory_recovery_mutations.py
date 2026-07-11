#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_GATE4_RESULT_INDEX = "3cb7e83eb6dc6c186a36da512ed41cbba4566abfc4bd4f5f71766ea1fcf075c4"
EXPECTED_BLOBS = {
    "recovery_common.py": "1ba78274c8c56a1b2b6cbd525fb341719a2ce4a7",
    "recovery_operations.py": "119571e8ad8a5663d20beff0ab82c85c14dfc4eb",
    "recovery_engine.py": "9a3f1898c7420198ff33d2b067a6fa2a6ac8618d",
}
CATEGORY_BY_FUNCTION = {
    ("recovery_common.py", "atomic_write"): "transaction-metadata",
    ("recovery_common.py", "stage_archive"): "transient-staging",
    ("recovery_common.py", "installation_lock"): "lock-state",
    ("recovery_common.py", "persist_journal"): "transaction-metadata",
    ("recovery_common.py", "add_intent"): "transaction-metadata",
    ("recovery_common.py", "mark_applied"): "transaction-metadata",
    ("recovery_common.py", "save_prior_registry"): "transaction-backup",
    ("recovery_operations.py", "install"): "install-production",
    ("recovery_operations.py", "uninstall"): "uninstall-production",
    ("recovery_engine.py", "remove_path"): "rollback-cleanup",
    ("recovery_engine.py", "rollback_transaction"): "rollback-production",
    ("recovery_engine.py", "recover"): "recovery-cleanup",
    ("recovery_engine.py", "hold_lock"): "lock-probe",
    ("recovery_engine.py", "main"): "tool-output",
}
PRODUCTION_CATEGORIES = {
    "transaction-metadata",
    "transaction-backup",
    "install-production",
    "uninstall-production",
    "rollback-cleanup",
    "rollback-production",
    "recovery-cleanup",
}
DIRECT_OPERATIONS = {
    "os.replace": "namespace-replace",
    "os.symlink": "symlink-create",
    "os.chmod": "metadata-change",
    "os.unlink": "unlink",
    "os.rmdir": "rmdir",
    "os.fsync": "file-or-directory-fsync",
    "shutil.copyfile": "regular-copy",
    "shutil.copyfileobj": "regular-copy",
    "shutil.rmtree": "tree-remove",
    "atomic_write": "atomic-write-helper",
    "persist_journal": "journal-helper",
    "save_prior_registry": "registry-backup-helper",
}
METHOD_OPERATIONS = {
    "mkdir": "mkdir",
    "write_bytes": "direct-write",
    "write_text": "direct-write",
    "unlink": "unlink",
    "rmdir": "rmdir",
    "write": "stream-write",
    "flush": "stream-flush",
}
OBLIGATIONS = {
    "namespace-replace": "fsync source parent and destination parent after replace",
    "symlink-create": "fsync containing directory after symlink publication",
    "metadata-change": "fsync affected file or directory after metadata change",
    "unlink": "fsync parent directory after unlink",
    "rmdir": "fsync parent directory after rmdir",
    "regular-copy": "fsync completed regular file before namespace publication",
    "tree-remove": "fsync surviving parent after tree removal",
    "atomic-write-helper": "extend helper with target-parent directory fsync",
    "journal-helper": "inherit durable atomic journal replacement",
    "registry-backup-helper": "durably create backup before first payload mutation",
    "mkdir": "fsync new directory and parent directory",
    "direct-write": "fsync file and parent when the write creates a named object",
    "stream-write": "fsync stream before publication",
    "stream-flush": "flush is not a persistence boundary without fsync",
    "os-open-create": "fsync created file and parent when persistent state is introduced",
    "path-open-write": "fsync file and parent when the opened path becomes persistent",
    "file-or-directory-fsync": "retain and classify the fsync target",
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


def os_open_mutates(call: ast.Call) -> bool:
    if dotted(call.func) != "os.open" or len(call.args) < 2:
        return False
    flags = ast.dump(call.args[1], include_attributes=False)
    return any(token in flags for token in ("O_CREAT", "O_TRUNC", "O_WRONLY", "O_RDWR"))


def path_open_mutates(call: ast.Call) -> bool:
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "open":
        return False
    modes: list[str] = []
    if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
        modes.append(call.args[0].value)
    for keyword in call.keywords:
        if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
            if isinstance(keyword.value.value, str):
                modes.append(keyword.value.value)
    return any(any(marker in mode for marker in ("w", "a", "x", "+")) for mode in modes)


class InventoryVisitor(ast.NodeVisitor):
    def __init__(self, module: str, source: str):
        self.module = module
        self.source = source
        self.functions: list[str] = []
        self.rows: list[dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append(node.name)
        self.generic_visit(node)
        self.functions.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        function = self.functions[-1] if self.functions else "<module>"
        call = dotted(node.func)
        operation = DIRECT_OPERATIONS.get(call)
        if operation is None and isinstance(node.func, ast.Attribute):
            operation = METHOD_OPERATIONS.get(node.func.attr)
        if operation is None and os_open_mutates(node):
            operation = "os-open-create"
        if operation is None and path_open_mutates(node):
            operation = "path-open-write"
        if operation is not None:
            category = CATEGORY_BY_FUNCTION.get((self.module, function), "UNKNOWN")
            self.rows.append(
                {
                    "module": self.module,
                    "function": function,
                    "line": node.lineno,
                    "column": node.col_offset,
                    "call": call,
                    "source": ast.get_source_segment(self.source, node) or call,
                    "operation": operation,
                    "category": category,
                    "production_path": category in PRODUCTION_CATEGORIES,
                    "obligation": OBLIGATIONS[operation],
                }
            )
        self.generic_visit(node)


def scan(path: Path) -> list[dict[str, Any]]:
    source = path.read_text(encoding="utf-8")
    visitor = InventoryVisitor(path.name, source)
    visitor.visit(ast.parse(source, filename=str(path)))
    return visitor.rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate4-results", required=True, type=Path)
    parser.add_argument("--recovery-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    gate4 = args.gate4_results.resolve()
    recovery_dir = args.recovery_dir.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    gate4_scenario = read_json(gate4 / "scenario.json")
    gate4_verification = read_json(gate4 / "verification.json")
    gate4_workflow = read_json(gate4 / "workflow-status.json")
    source_paths = {name: recovery_dir / name for name in EXPECTED_BLOBS}
    source_blobs = {name: git_blob_sha(path) for name, path in source_paths.items()}
    rows = sorted(
        [row for path in source_paths.values() for row in scan(path)],
        key=lambda row: (row["module"], row["line"], row["column"], row["operation"]),
    )
    unknown = [row for row in rows if row["category"] == "UNKNOWN"]
    production = [row for row in rows if row["production_path"]]
    categories = Counter(row["category"] for row in rows)
    operations = Counter(row["operation"] for row in rows)

    inventory = {
        "schema_version": 1,
        "inventory_kind": "cpython-android-cli-recovery-filesystem-mutation-inventory",
        "source_blobs": source_blobs,
        "row_count": len(rows),
        "production_row_count": len(production),
        "categories": dict(sorted(categories.items())),
        "operations": dict(sorted(operations.items())),
        "rows": rows,
    }
    (output / "mutation-inventory.json").write_bytes(canonical_json_bytes(inventory))

    groups: dict[str, list[dict[str, Any]]] = {}
    for row in production:
        groups.setdefault(row["category"], []).append(
            {
                "module": row["module"],
                "function": row["function"],
                "line": row["line"],
                "operation": row["operation"],
                "obligation": row["obligation"],
            }
        )
    plan = {
        "schema_version": 1,
        "plan_kind": "cpython-android-cli-recovery-durability-integration-plan",
        "source_blobs": source_blobs,
        "production_row_count": len(production),
        "groups": {name: value for name, value in sorted(groups.items())},
        "required_gate5_replay": {
            "recovery_scenarios": 55,
            "recovery_independent_verifier": 82,
            "durability_scenarios": 64,
            "durability_independent_verifier": 53,
        },
        "claim_boundary": {
            "proved": "Every detected filesystem mutation and fsync call in the frozen Gate 3 recovery sources is anchored to an exact source blob, function, line, category, and integration obligation.",
            "not_proved": "No durability helper has yet been integrated into the recovery engine, and no production crash path has yet been replayed with the integrated implementation.",
        },
    }
    (output / "integration-plan.json").write_bytes(canonical_json_bytes(plan))

    checks = {
        "gate4_scenario_pass_64": gate4_scenario.get("pass") is True
        and gate4_scenario.get("check_count") == 64
        and gate4_scenario.get("failed_checks") == [],
        "gate4_verification_pass_53": gate4_verification.get("pass") is True
        and gate4_verification.get("check_count") == 53
        and gate4_verification.get("failed_checks") == [],
        "gate4_workflow_pass": gate4_workflow.get("pass") is True
        and all(value == 0 for value in gate4_workflow.get("returncodes", {}).values()),
        "gate4_result_index_exact": sha256_file(gate4 / "result-index.json")
        == EXPECTED_GATE4_RESULT_INDEX,
        "source_blob_set_exact": source_blobs == EXPECTED_BLOBS,
        "inventory_nonempty": len(rows) > 0,
        "production_inventory_nonempty": len(production) > 0,
        "unknown_categories_absent": unknown == [],
        "row_keys_complete": all(
            set(row)
            == {
                "module",
                "function",
                "line",
                "column",
                "call",
                "source",
                "operation",
                "category",
                "production_path",
                "obligation",
            }
            for row in rows
        ),
        "rows_sorted": rows
        == sorted(
            rows,
            key=lambda row: (
                row["module"],
                row["line"],
                row["column"],
                row["operation"],
            ),
        ),
        "row_anchors_unique": len(
            {
                (row["module"], row["line"], row["column"], row["operation"])
                for row in rows
            }
        )
        == len(rows),
        "production_obligations_nonempty": all(row["obligation"] for row in production),
        "install_category_present": categories["install-production"] > 0,
        "uninstall_category_present": categories["uninstall-production"] > 0,
        "rollback_category_present": categories["rollback-production"] > 0,
        "recovery_cleanup_present": categories["recovery-cleanup"] > 0,
        "transaction_metadata_present": categories["transaction-metadata"] > 0,
        "transaction_backup_present": categories["transaction-backup"] > 0,
        "transient_staging_present": categories["transient-staging"] > 0,
        "lock_state_present": categories["lock-state"] > 0,
        "namespace_replace_present": operations["namespace-replace"] > 0,
        "mkdir_present": operations["mkdir"] > 0,
        "unlink_or_rmdir_present": operations["unlink"] + operations["rmdir"] > 0,
        "tree_remove_present": operations["tree-remove"] > 0,
        "atomic_write_helper_present": operations["atomic-write-helper"] > 0,
        "fsync_present": operations["file-or-directory-fsync"] > 0,
        "inventory_canonical": (output / "mutation-inventory.json").read_bytes()
        == canonical_json_bytes(inventory),
        "plan_canonical": (output / "integration-plan.json").read_bytes()
        == canonical_json_bytes(plan),
        "plan_production_count_exact": plan["production_row_count"] == len(production),
        "plan_group_set_exact": set(plan["groups"])
        == {row["category"] for row in production},
        "gate5_replay_counts_exact": plan["required_gate5_replay"]
        == {
            "recovery_scenarios": 55,
            "recovery_independent_verifier": 82,
            "durability_scenarios": 64,
            "durability_independent_verifier": 53,
        },
        "claim_boundary_exact": "No durability helper has yet been integrated"
        in plan["claim_boundary"]["not_proved"],
    }
    if len(checks) != 32:
        raise RuntimeError(f"unexpected check count: {len(checks)}")
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "observed": {
            "row_count": len(rows),
            "production_row_count": len(production),
            "categories": dict(sorted(categories.items())),
            "operations": dict(sorted(operations.items())),
        },
        "claim_boundary": plan["claim_boundary"],
    }
    (output / "scenario.json").write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    print("\nSTAGE3C_PHASE4_DURABILITY_INTEGRATION_INVENTORY=" + ("PASS" if result["pass"] else "FAIL"))
    if args.require_pass and not result["pass"]:
        return 51
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

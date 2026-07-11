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
DIRECT = {
    "os.replace",
    "os.symlink",
    "os.chmod",
    "os.unlink",
    "os.rmdir",
    "os.fsync",
    "shutil.copyfile",
    "shutil.copyfileobj",
    "shutil.rmtree",
    "atomic_write",
    "persist_journal",
    "save_prior_registry",
}
METHODS = {"mkdir", "write_bytes", "write_text", "unlink", "rmdir", "write", "flush"}


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
    return (
        dotted(call.func) == "os.open"
        and len(call.args) >= 2
        and any(
            token in ast.dump(call.args[1], include_attributes=False)
            for token in ("O_CREAT", "O_TRUNC", "O_WRONLY", "O_RDWR")
        )
    )


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


class CallScanner(ast.NodeVisitor):
    def __init__(self, module: str):
        self.module = module
        self.functions: list[str] = []
        self.anchors: list[tuple[str, str, int, int]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append(node.name)
        self.generic_visit(node)
        self.functions.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        name = dotted(node.func)
        selected = name in DIRECT
        if isinstance(node.func, ast.Attribute) and node.func.attr in METHODS:
            selected = True
        if os_open_mutates(node) or path_open_mutates(node):
            selected = True
        if selected:
            self.anchors.append(
                (
                    self.module,
                    self.functions[-1] if self.functions else "<module>",
                    node.lineno,
                    node.col_offset,
                )
            )
        self.generic_visit(node)


def scan_anchors(path: Path) -> list[tuple[str, str, int, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    scanner = CallScanner(path.name)
    scanner.visit(tree)
    return scanner.anchors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate4-results", required=True, type=Path)
    parser.add_argument("--recovery-dir", required=True, type=Path)
    parser.add_argument("--inventory-results", required=True, type=Path)
    parser.add_argument("--input-before", required=True, type=Path)
    parser.add_argument("--input-after", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    gate4 = args.gate4_results.resolve()
    recovery_dir = args.recovery_dir.resolve()
    results = args.inventory_results.resolve()
    inventory = read_json(results / "mutation-inventory.json")
    plan = read_json(results / "integration-plan.json")
    scenario = read_json(results / "scenario.json")
    before = read_json(args.input_before.resolve())
    after = read_json(args.input_after.resolve())
    gate4_scenario = read_json(gate4 / "scenario.json")
    gate4_verification = read_json(gate4 / "verification.json")
    gate4_workflow = read_json(gate4 / "workflow-status.json")

    source_paths = {name: recovery_dir / name for name in EXPECTED_BLOBS}
    source_blobs = {name: git_blob_sha(path) for name, path in source_paths.items()}
    rescanned = sorted(
        [anchor for path in source_paths.values() for anchor in scan_anchors(path)]
    )
    inventory_anchors = sorted(
        (row["module"], row["function"], row["line"], row["column"])
        for row in inventory["rows"]
    )
    categories = Counter(row["category"] for row in inventory["rows"])
    operations = Counter(row["operation"] for row in inventory["rows"])
    production = [row for row in inventory["rows"] if row["production_path"]]
    plan_rows = [row for rows in plan["groups"].values() for row in rows]

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
        "input_tree_unchanged": before.get("pass") is True
        and after.get("pass") is True
        and before.get("entry_count") == after.get("entry_count")
        and before.get("fingerprint") == after.get("fingerprint"),
        "source_blobs_exact": source_blobs == EXPECTED_BLOBS,
        "inventory_source_blobs_exact": inventory.get("source_blobs") == source_blobs,
        "plan_source_blobs_exact": plan.get("source_blobs") == source_blobs,
        "scenario_pass_32": scenario.get("pass") is True
        and scenario.get("check_count") == 32
        and scenario.get("failed_checks") == [],
        "scenario_all_checks_true": len(scenario.get("checks", {})) == 32
        and all(scenario["checks"].values()),
        "inventory_kind_exact": inventory.get("inventory_kind")
        == "cpython-android-cli-recovery-filesystem-mutation-inventory",
        "plan_kind_exact": plan.get("plan_kind")
        == "cpython-android-cli-recovery-durability-integration-plan",
        "inventory_rows_nonempty": len(inventory["rows"]) > 0,
        "inventory_row_count_exact": inventory.get("row_count") == len(inventory["rows"]),
        "production_count_exact": inventory.get("production_row_count") == len(production),
        "rescanned_anchor_set_exact": rescanned == inventory_anchors,
        "anchors_unique": len(set(inventory_anchors)) == len(inventory_anchors),
        "unknown_categories_absent": all(row["category"] != "UNKNOWN" for row in inventory["rows"]),
        "production_obligations_nonempty": all(row["obligation"] for row in production),
        "category_summary_exact": inventory.get("categories")
        == dict(sorted(categories.items())),
        "operation_summary_exact": inventory.get("operations")
        == dict(sorted(operations.items())),
        "plan_group_set_exact": set(plan["groups"])
        == {row["category"] for row in production},
        "plan_row_count_exact": len(plan_rows) == len(production),
        "plan_anchor_set_exact": {
            (row["module"], row["function"], row["line"], row["operation"])
            for row in plan_rows
        }
        == {
            (row["module"], row["function"], row["line"], row["operation"])
            for row in production
        },
        "required_replay_counts_exact": plan.get("required_gate5_replay")
        == {
            "recovery_scenarios": 55,
            "recovery_independent_verifier": 82,
            "durability_scenarios": 64,
            "durability_independent_verifier": 53,
        },
        "inventory_canonical": (results / "mutation-inventory.json").read_bytes()
        == canonical_json_bytes(inventory),
        "plan_canonical": (results / "integration-plan.json").read_bytes()
        == canonical_json_bytes(plan),
        "scenario_canonical": (results / "scenario.json").read_bytes()
        == canonical_json_bytes(scenario),
        "claim_boundary_exact": "No durability helper has yet been integrated"
        in plan["claim_boundary"]["not_proved"],
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
        "observed": {
            "row_count": len(inventory["rows"]),
            "production_row_count": len(production),
            "category_count": len(categories),
            "operation_count": len(operations),
        },
        "claim_boundary": plan["claim_boundary"],
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 52


if __name__ == "__main__":
    raise SystemExit(main())

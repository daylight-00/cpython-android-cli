#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ALLOWED = {"adopt", "adopt-with-redesign", "exclude", "defer-to-epoch4"}
EXPECTED_IDS = {f"SEL-{index:02d}" for index in range(1, 19)}
EXPECTED_EXPERIMENTS = {f"E3-X{index}" for index in range(1, 10)}


def load(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha(path: str) -> str:
    digest = hashlib.sha256()
    with (ROOT / path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify() -> dict[str, Any]:
    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}
    selection = load("docs/epochs/EPOCH3_UPSTREAM_THIN_SELECTION_REGISTER.json")
    boundary = load("docs/contracts/EPOCH3_UPSTREAM_THIN_CLEAN_REPOSITORY_BOUNDARY.json")
    experiments = load("experiments/epoch3-upstream-thin-initialization/experiment-register.json")
    contract = load("components/upstream-thin/contracts/product-v1.json")
    lock = load("config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-v1.lock.json")

    rows = selection.get("selections", [])
    ids = [row.get("id") for row in rows]
    dispositions = [row.get("disposition") for row in rows]
    checks["selection_count_exact"] = len(rows) == 18 == selection.get("selection_count")
    checks["selection_ids_exact_unique"] = set(ids) == EXPECTED_IDS and len(ids) == len(set(ids))
    checks["selection_dispositions_valid"] = all(value in ALLOWED for value in dispositions)
    checks["selection_no_unresolved_disposition"] = all(row.get("decision") for row in rows)
    checks["astral_default_rule_frozen"] = "Adopt Astral-like" in selection.get("decision_rule", "")
    checks["artifact_order_full_first"] = selection.get("artifact_order") == ["full", "install_only", "install_only_stripped"] == contract.get("artifact_order")

    checks["clean_product_root"] = boundary.get("active_product_root") == "components/upstream-thin/"
    checks["single_main_rule"] = boundary.get("repository_flow", "").startswith("single append-only main")
    checks["experiment_import_forbidden"] = "experiments/** at product execution time" in boundary.get("forbidden_runtime_or_build_dependencies", [])
    checks["termux_native_dependency_forbidden"] = any("Termux native" in item for item in boundary.get("forbidden_runtime_or_build_dependencies", []))

    exp_ids = [row.get("id") for row in experiments.get("experiments", [])]
    checks["experiment_register_exact"] = set(exp_ids) == EXPECTED_EXPERIMENTS and len(exp_ids) == len(set(exp_ids))
    checks["parallel_rule_present"] = "alongside full assembly" in experiments.get("concurrency_rule", "")

    checks["official_input_exact"] = lock.get("archive", {}).get("sha256") == "38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5" and lock.get("archive", {}).get("size_bytes") == 22358404
    checks["native_rebuild_forbidden"] = lock.get("policy", {}).get("native_rebuild_forbidden") is True
    checks["full_contract_roots"] = contract.get("artifacts", {}).get("full", {}).get("required_members") == ["python/PYTHON.json", "python/build/", "python/install/"]
    checks["install_only_is_projection"] = "verified full" in contract.get("artifacts", {}).get("install_only", {}).get("derivation", "")
    checks["stripped_is_projection"] = "verified install_only" in contract.get("artifacts", {}).get("install_only_stripped", {}).get("derivation", "")
    checks["fake_producer_material_forbidden"] = contract.get("metadata", {}).get("fabricated_producer_objects_forbidden") is True and len(contract.get("build_area", {}).get("forbidden", [])) == 5
    checks["android_native_termux_independent"] = contract.get("native_boundary", {}).get("android_native") is True and contract.get("native_boundary", {}).get("termux_native_dependencies") == 0
    checks["publication_withheld"] = contract.get("publication") == {"selectable": False, "authorized": False}

    launcher = "components/upstream-thin/src/python.c"
    checks["launcher_exact_la2"] = sha(launcher) == "15b38b3acf1e3861fb036fe593de1e002e30bdb1be113c005330055bc6dbfbfd"
    required_code = [
        "components/upstream-thin/lib/archive.py",
        "components/upstream-thin/lib/elf.py",
        "components/upstream-thin/lib/metadata.py",
        "components/upstream-thin/lib/assemble_full.py",
        "components/upstream-thin/lib/verify_full.py",
        "components/upstream-thin/bin/build-launcher",
        "components/upstream-thin/bin/cpython-android-upstream-thin",
        "components/upstream-thin/tests/test_full_first.py",
    ]
    checks["full_scaffold_complete"] = all((ROOT / path).is_file() for path in required_code)
    checks["downstream_assemblers_not_started"] = not (ROOT / "components/upstream-thin/lib/assemble_install_only.py").exists() and not (ROOT / "components/upstream-thin/lib/assemble_stripped.py").exists()

    tests = subprocess.run(
        [str(ROOT / "components/upstream-thin/bin/cpython-android-upstream-thin"), "test"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    test_cases = sorted(
        line.strip()
        for line in tests.stdout.splitlines()
        if line.strip().endswith("... ok")
    )
    checks["full_scaffold_tests"] = tests.returncode == 0
    checks["full_scaffold_test_count"] = len(test_cases) == 7
    details["test_result"] = {
        "returncode": tests.returncode,
        "test_count": len(test_cases),
        "test_cases": test_cases,
    }

    failed = sorted(key for key, passed in checks.items() if not passed)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-upstream-thin-initialization-and-full-start",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": len(checks) - len(failed),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "details": details,
    }


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

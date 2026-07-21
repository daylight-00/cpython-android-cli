#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha(path: str) -> str:
    digest = hashlib.sha256()
    with (ROOT / path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit() -> dict[str, Any]:
    checks: dict[str, bool] = {}
    selection = load("docs/epochs/EPOCH3_UPSTREAM_THIN_SELECTION_REGISTER.json")
    contract = load("components/upstream-thin/contracts/product-v1.json")
    boundary = load("docs/contracts/EPOCH3_UPSTREAM_THIN_CLEAN_REPOSITORY_BOUNDARY.json")
    register = load("experiments/epoch3-upstream-thin-initialization/experiment-register.json")

    checks["every_selection_has_one_disposition"] = all(
        isinstance(row.get("disposition"), str) and row["disposition"] in {"adopt", "adopt-with-redesign", "exclude", "defer-to-epoch4"}
        for row in selection["selections"]
    ) and len(selection["selections"]) == 18
    checks["full_is_only_assembly_authority"] = contract["artifacts"]["full"]["role"] == "canonical assembly and derivation authority"
    checks["install_only_cannot_be_independent"] = "verified full" in contract["artifacts"]["install_only"]["derivation"]
    checks["stripped_cannot_be_independent"] = "verified install_only" in contract["artifacts"]["install_only_stripped"]["derivation"]
    checks["upstream_native_topology_inherited"] = contract["native_boundary"]["upstream_dependency_topology_inherited"] is True and contract["native_boundary"]["project_dependency_builds"] == 0
    checks["termux_native_dependency_zero"] = contract["native_boundary"]["termux_native_dependencies"] == 0
    checks["producer_surface_truthful"] = contract["metadata"]["fabricated_producer_objects_forbidden"] is True and all(item.startswith("fake ") for item in contract["build_area"]["forbidden"])
    checks["clean_root_matches_contract"] = boundary["active_product_contract"] == "components/upstream-thin/contracts/product-v1.json" and boundary["active_product_root"] == "components/upstream-thin/"
    checks["nine_experiments_bounded"] = len(register["experiments"]) == 9 and all(row.get("blocks") for row in register["experiments"])

    active_files = sorted((ROOT / "components/upstream-thin").rglob("*"))
    source_candidates = [path for path in active_files if path.is_file() and (path.suffix in {".py", ".sh", ".c", ".md"} or path.parent.name == "bin")]
    source_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in source_candidates)
    checks["active_code_does_not_import_experiments"] = "experiments." not in source_text and "experiments/" not in source_text
    dependency_sensitive = [
        ROOT / "components/upstream-thin/src/python.c",
        ROOT / "components/upstream-thin/bin/build-launcher",
        ROOT / "components/upstream-thin/bin/cpython-android-upstream-thin",
        ROOT / "components/upstream-thin/lib/archive.py",
        ROOT / "components/upstream-thin/lib/elf.py",
        ROOT / "components/upstream-thin/lib/assemble_full.py",
    ]
    dependency_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in dependency_sensitive)
    checks["active_code_has_no_termux_prefix"] = "/data/data/com.termux/" not in dependency_text
    checks["launcher_exact_accepted_source"] = sha("components/upstream-thin/src/python.c") == "15b38b3acf1e3861fb036fe593de1e002e30bdb1be113c005330055bc6dbfbfd"

    verifier = subprocess.run([sys.executable, str(ROOT / "experiments/epoch3-upstream-thin-initialization/verify_epoch3_initialization.py")], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    checks["primary_verifier_passes"] = verifier.returncode == 0 and json.loads(verifier.stdout)["pass"] is True
    compile_check = subprocess.run([sys.executable, "-m", "py_compile", *[str(path) for path in active_files if path.suffix == ".py"]], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    checks["active_python_compiles"] = compile_check.returncode == 0

    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": 1,
        "audit_kind": "epoch3-upstream-thin-initialization-independent-audit",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": len(checks) - len(failed),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "primary_verifier_output_sha256": hashlib.sha256(verifier.stdout.encode()).hexdigest(),
        "claim_boundary": {"selection_complete": True, "implementation_started": True, "full_release_complete": False, "selectable": False, "publication": False},
    }


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)

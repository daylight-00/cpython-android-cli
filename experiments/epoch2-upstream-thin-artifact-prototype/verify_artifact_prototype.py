#!/usr/bin/env python3
"""Focused semantic verifier for the frozen UT-1 artifact prototype."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

OUTPUT_REL = "experiments/epoch2-upstream-thin-artifact-prototype"
AUTHORITY_NAME = "artifact-prototype-authority.json"
NEXT_ACTION = "execute-e2-r1-ut2-loader-relocation-launcher-getpath"
FOLLOWING_ACTION = "execute-e2-r1-ut3-sysconfig-and-native-extension-sdk"
PRIMARY = [
    "PYTHON.json",
    "artifact-contract.json",
    "python-json-schema-mapping.json",
    "unavailable-field-policy.json",
    "deterministic-derivation-rules.json",
    "archive-root-and-path-contract.json",
    "full.manifest.json",
    "install_only.manifest.json",
    "install_only_stripped.manifest.json",
    "artifact-set.json",
    "artifact-flavor-decision-inputs.json",
    "consumer-extraction-contract.json",
    "strip-mutations.json",
    "official-extraction-verification.json",
    "independent-audit.json",
]
SCRIPTS = [
    "generate_artifact_prototype.py",
    "audit_artifact_prototype.py",
    "verify_artifact_prototype.py",
    "test_verify_artifact_prototype.py",
    "finalize_artifact_prototype.py",
    "run-ut1-astral-artifact-and-metadata-prototype.sh",
]
REQUIRED = ["README.md", *PRIMARY, *SCRIPTS, AUTHORITY_NAME, "evidence-freeze.md"]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def verify(root: Path, output_dir: Path | None = None, artifact_dir: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    out = (output_dir or (root / OUTPUT_REL)).resolve()
    checks: dict[str, bool] = {}
    errors: dict[str, Any] = {}
    missing = [name for name in REQUIRED if not (out / name).is_file()]
    checks["required_files"] = not missing
    if missing:
        errors["missing"] = missing

    parsed: dict[str, Any] = {}
    for name in [*PRIMARY, AUTHORITY_NAME]:
        p = out / name
        if not p.is_file():
            continue
        try:
            parsed[name] = load(p)
        except Exception as exc:
            errors.setdefault("parse", {})[name] = str(exc)
    checks["json_parse"] = "parse" not in errors

    audit = parsed.get("independent-audit.json", {})
    checks["independent_audit"] = audit.get("pass") is True and audit.get("pass_count") == audit.get("check_count")
    authority = parsed.get(AUTHORITY_NAME, {})
    checks["authority_identity"] = authority.get("schema_version") == 1 and authority.get("authority_kind") == "e2-r1-ut1-astral-artifact-and-metadata-prototype" and authority.get("status") == "frozen-pass-local-prototype-unselectable"
    expected_ids = {name: sha(out / name) for name in [*PRIMARY, *SCRIPTS] if (out / name).is_file()}
    checks["authority_file_set"] = set(authority.get("file_identities", {})) == set(expected_ids)
    checks["authority_file_identities"] = authority.get("file_identities") == expected_ids
    authority_sha = sha(out / AUTHORITY_NAME) if (out / AUTHORITY_NAME).is_file() else ""

    py = parsed.get("PYTHON.json", {})
    checks["python_json_identity"] = py.get("version") == 8 and py.get("target_triple") == "aarch64-linux-android" and py.get("python_version") == "3.14.6"
    checks["python_exe_unavailable"] = py.get("python_exe", "missing") is None and py.get("hw_t", {}).get("availability", {}).get("python_exe") == "unavailable-official-package"
    core = py.get("build_info", {}).get("core", {})
    ext = py.get("build_info", {}).get("extensions", {})
    checks["core_truthful"] = core.get("shared_lib") == "install/lib/libpython3.14.so" and not ({"objs", "static_lib", "inittab_object", "inittab_source", "inittab_cflags"} & set(core))
    checks["extensions_truthful"] = isinstance(ext, dict) and len(ext) == 67 and all(not ({"objs", "static_lib"} & set(c)) and isinstance(c.get("shared_lib"), str) for variants in ext.values() for c in variants)
    checks["claim_boundary"] = py.get("hw_t", {}).get("claim_boundary", {}).get("android_runtime") is False and py.get("hw_t", {}).get("claim_boundary", {}).get("selectable") is False

    contract = parsed.get("artifact-contract.json", {})
    checks["artifact_contract"] = contract.get("selectable") is False and set(contract.get("flavors", {})) == {"full", "install_only", "install_only_stripped"} and "interpreter executable" in contract.get("forbidden_fabrications", [])
    mapping = parsed.get("python-json-schema-mapping.json", {})
    checks["schema_mapping"] = mapping.get("astral_format_version") == 8 and mapping.get("python_exe", {}).get("availability") == "unavailable-official-package" and mapping.get("python_exe", {}).get("must_not_be_fabricated") is True
    policy = parsed.get("unavailable-field-policy.json", {})
    checks["unavailable_policy"] = policy.get("fields", {}).get("build_info.core.objs") == "omit" and policy.get("fields", {}).get("python_exe") == "null-with-hw_t-availability"
    consumer = parsed.get("consumer-extraction-contract.json", {})
    checks["consumer_contract"] = consumer.get("full", {}).get("direct_runtime_entry") is None and consumer.get("claim_boundary", {}).get("Android_execution") is False
    decisions = parsed.get("artifact-flavor-decision-inputs.json", {})
    checks["flavor_inputs"] = decisions.get("observations", {}).get("official_package_has_python_executable") is False and decisions.get("epoch3_selection") is False
    checks["extraction_binding"] = parsed.get("official-extraction-verification.json", {}).get("pass") is True

    aset = parsed.get("artifact-set.json", {})
    rows = aset.get("artifacts", []) if isinstance(aset, dict) else []
    checks["artifact_set"] = aset.get("selectable") is False and aset.get("publication") is False and {r.get("flavor") for r in rows if isinstance(r, dict)} == {"full", "install_only", "install_only_stripped"}
    if artifact_dir is not None:
        artifact_dir = artifact_dir.resolve()
        checks["artifact_bytes_present"] = all((artifact_dir / r["archive"]["filename"]).is_file() and sha(artifact_dir / r["archive"]["filename"]) == r["archive"]["sha256"] and (artifact_dir / r["archive"]["filename"]).stat().st_size == r["archive"]["size"] for r in rows)

    manifests: dict[str, Any] = {flavor: parsed.get(f"{flavor}.manifest.json", {}) for flavor in ("full", "install_only", "install_only_stripped")}
    full_paths = {r.get("path") for r in manifests["full"].get("members", []) if isinstance(r, dict)}
    install_paths = {r.get("path") for r in manifests["install_only"].get("members", []) if isinstance(r, dict)}
    stripped_paths = {r.get("path") for r in manifests["install_only_stripped"].get("members", []) if isinstance(r, dict)}
    checks["full_paths"] = {"python", "python/PYTHON.json", "python/build", "python/install"}.issubset(full_paths)
    checks["install_paths"] = "python" in install_paths and "python/PYTHON.json" not in install_paths and not any(p and p.startswith("python/build/") for p in install_paths)
    checks["stripped_paths"] = "python" in stripped_paths and "python/PYTHON.json" not in stripped_paths and not any(p and p.startswith("python/build/") for p in stripped_paths)
    checks["no_fabricated_bin"] = not any(p and (p.startswith("python/bin/") or p.startswith("python/install/bin/")) for p in full_paths | install_paths | stripped_paths)
    strip = parsed.get("strip-mutations.json", {})
    checks["strip_record"] = strip.get("elf_count") == len(strip.get("rows", [])) and strip.get("elf_count", 0) > 0
    checks["no_archives_committed"] = not any(p.is_file() and (p.name.endswith(".tar.gz") or p.name.endswith(".tar.zst")) for p in out.rglob("*"))

    state_path = root / "docs/current/STATE.json"
    task_path = root / "docs/current/AGENT_TASK.json"
    catalog_path = root / "docs/agent/TASK_CATALOG.json"
    registry_path = root / "docs/documentation/document-registry.json"
    state = load(state_path) if state_path.is_file() else {}
    task = load(task_path) if task_path.is_file() else {}
    catalog = load(catalog_path) if catalog_path.is_file() else {}
    registry = load(registry_path) if registry_path.is_file() else {}
    accepted = [a for a in state.get("accepted_authorities", []) if a.get("id") == "e2-r1-ut1-astral-artifact-and-metadata-prototype"]
    checks["state_binding"] = state.get("state_revision") == 8 and state.get("next_action_class") == NEXT_ACTION and state.get("program", {}).get("gate", {}).get("id") == "E2-R1/UT-2" and len(accepted) == 1 and accepted[0].get("sha256") == authority_sha
    checks["current_task"] = task.get("task", {}).get("id") == "E2-R1-UT-2" and task.get("task", {}).get("action_class") == NEXT_ACTION and task.get("program_gate", {}).get("status") == "ready"
    tasks = {t.get("task_id"): t for t in catalog.get("tasks", []) if isinstance(t, dict)}
    ut2 = tasks.get("E2-R1-UT-2", {})
    ut3 = tasks.get("E2-R1-UT-3", {})
    checks["ut2_activation"] = ut2.get("activation", {}).get("status") == "ready" and ut2.get("activation", {}).get("accepted_authority_sha256") == authority_sha and ut2.get("completion_contract", {}).get("pass", {}).get("successor_action_class") == FOLLOWING_ACTION
    checks["ut2_read_boundary"] = any(r.get("section_heading") == "## UT-2 — Loader, relocation, launcher, and getpath" and r.get("stop_before_heading") == "## UT-3 — Sysconfig and native-extension SDK" for r in ut2.get("required_reads", []))
    checks["ut3_cataloged"] = ut3.get("action_class") == FOLLOWING_ACTION and ut3.get("activation", {}).get("status") == "blocked-on-predecessor-authority"
    registry_paths = {d.get("path") for d in registry.get("documents", []) if isinstance(d, dict)}
    expected_registry = {f"{OUTPUT_REL}/{name}" for name in ["README.md", *PRIMARY, AUTHORITY_NAME, "evidence-freeze.md"]}
    checks["registry_coverage"] = expected_registry.issubset(registry_paths)
    checks["catalog_binding"] = state.get("task_catalog", {}).get("sha256") == sha(catalog_path)

    failed = sorted(k for k, v in checks.items() if not v)
    return {
        "schema_version": 1,
        "verification_kind": "e2-r1-ut1-astral-artifact-and-metadata-prototype",
        "pass": not failed and not errors,
        "check_count": len(checks),
        "pass_count": sum(1 for v in checks.values() if v),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "errors": errors,
        "authority_sha256": authority_sha,
        "claim_boundary": "Artifact representation only; no runtime, launcher, relocation, product selection, or publication claim.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--output-dir", type=Path)
    ap.add_argument("--artifact-dir", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = verify(args.root, args.output_dir, args.artifact_dir)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

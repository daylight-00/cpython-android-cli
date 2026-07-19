#!/usr/bin/env python3
"""Negative and positive fixtures for the document lifecycle verifier."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFY_PATH = HERE / "verify-document-registry.py"
spec = importlib.util.spec_from_file_location("doc_registry_verify", VERIFY_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SOURCE_ROOT = HERE.parents[1]
CONTROL_PATHS = [
    "docs/documentation/DOCUMENT_LIFECYCLE.md",
    "docs/documentation/document-registry.json",
    "docs/documentation/document-registry.schema.json",
    "docs/documentation/legacy-live-binding-baseline.json",
]


def run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def fixture() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="doc-lifecycle-fixture-"))
    run("git", "init", "-q", cwd=tmp)
    run("git", "config", "user.email", "fixture@example.invalid", cwd=tmp)
    run("git", "config", "user.name", "fixture", cwd=tmp)
    for rel in CONTROL_PATHS:
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_ROOT / rel, dst)
    # Minimal authority and a generated/live path with one grandfathered binding.
    (tmp / "README.md").write_text("# fixture\n", encoding="utf-8")
    (tmp / "authority.json").write_text(json.dumps({"file_identities": {"README.md": "a" * 64}}), encoding="utf-8")
    reg = json.loads((tmp / CONTROL_PATHS[1]).read_text(encoding="utf-8"))
    keep = {p for p in CONTROL_PATHS} | {"README.md", "authority.json"}
    reg["documents"] = [d for d in reg["documents"] if d["path"] in keep]
    reg["documents"].append({
        "path": "authority.json", "format": "json", "lifecycle_class": "FROZEN_AUTHORITY",
        "authority_domain": "fixture", "owner": "fixture", "mutability": "immutable",
        "update_trigger": "never", "supersession_rule": "new fixture",
        "onboarding_visibility": "machine", "machine_binding_policy": "allowed",
        "migration_action": "keep"
    })
    for d in reg["documents"]:
        if d["path"] == "README.md":
            d["machine_binding_policy"] = "LEGACY_CONFLICT—future-binding-forbidden"
    reg["basis"]["tracked_document_count"] = len(reg["documents"])
    (tmp / CONTROL_PATHS[1]).write_text(json.dumps(reg, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    base = json.loads((tmp / CONTROL_PATHS[3]).read_text(encoding="utf-8"))
    base["forbidden_live_targets"] = ["README.md"]
    base["expected_binding_count"] = 1
    base["bindings"] = [{"authority_path": "authority.json", "target_path": "README.md", "recorded_sha256": "a" * 64, "location": "file_identities"}]
    (tmp / CONTROL_PATHS[3]).write_text(json.dumps(base, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run("git", "add", ".", cwd=tmp)
    run("git", "commit", "-q", "-m", "fixture", cwd=tmp)
    return tmp


def expect(name: str, mutate, should_pass: bool) -> dict:
    root = fixture()
    try:
        mutate(root)
        result = mod.verify(root)
        ok = bool(result["pass"]) is should_pass
        return {"name": name, "pass": ok, "observed_pass": result["pass"], "failed_checks": result["failed_checks"]}
    finally:
        shutil.rmtree(root)


def edit_json(root: Path, rel: str, fn) -> None:
    p = root / rel
    obj = json.loads(p.read_text(encoding="utf-8"))
    fn(obj)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run("git", "add", rel, cwd=root)


cases = []
cases.append(expect("valid-fixture", lambda r: None, True))
cases.append(expect("unregistered-document", lambda r: ((r / "extra.md").write_text("x\n"), run("git", "add", "extra.md", cwd=r)), False))
cases.append(expect("registry-extra-path", lambda r: edit_json(r, CONTROL_PATHS[1], lambda o: o["documents"].append({**o["documents"][0], "path": "missing.md"})), False))
cases.append(expect("duplicate-path", lambda r: edit_json(r, CONTROL_PATHS[1], lambda o: o["documents"].append(dict(o["documents"][0]))), False))
cases.append(expect("invalid-lifecycle", lambda r: edit_json(r, CONTROL_PATHS[1], lambda o: o["documents"][0].__setitem__("lifecycle_class", "INVALID")), False))
cases.append(expect("missing-required-field", lambda r: edit_json(r, CONTROL_PATHS[1], lambda o: o["documents"][0].pop("owner")), False))
cases.append(expect("new-forbidden-binding", lambda r: edit_json(r, "authority.json", lambda o: o["file_identities"].__setitem__("README.md", "b" * 64)), False))
cases.append(expect("baseline-mismatch", lambda r: edit_json(r, CONTROL_PATHS[3], lambda o: o["bindings"][0].__setitem__("recorded_sha256", "c" * 64)), False))

failed = [c for c in cases if not c["pass"]]
result = {
    "schema_version": 1,
    "test_kind": "document-lifecycle-control-plane-negative-fixtures-v1",
    "pass": not failed,
    "check_count": len(cases),
    "pass_count": len(cases) - len(failed),
    "failed_checks": [c["name"] for c in failed],
    "checks": cases,
}
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result["pass"] else 1)

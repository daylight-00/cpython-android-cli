#!/usr/bin/env python3
"""Freeze UT-1 authority and activate UT-2 after independent audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ACTION = "execute-e2-r1-ut1-astral-artifact-and-metadata-prototype"
NEXT_ACTION = "execute-e2-r1-ut2-loader-relocation-launcher-getpath"
NEXT_TASK = "E2-R1-UT-2"
FOLLOWING_ACTION = "execute-e2-r1-ut3-sysconfig-and-native-extension-sdk"
FOLLOWING_TASK = "E2-R1-UT-3"
OUTPUT_REL = "experiments/epoch2-upstream-thin-artifact-prototype"
TRANSACTION_ID = "20260720-e2-r1-ut1-astral-artifact-and-metadata-prototype-v1"

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
NEW_DOCS = [
    "README.md",
    *PRIMARY,
    "artifact-prototype-authority.json",
    "evidence-freeze.md",
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def completion_contract(current: str, successor: str, successor_task: str) -> dict[str, Any]:
    return {
        "contract_version": 1,
        "always": {
            "all_required_verifiers_must_pass": True,
            "clean_main_and_bundle_export_ready_on_close": True,
            "forbidden_new_authority_bindings": ["docs/current/STATE.json", "docs/current/AGENT_TASK.json", "README.md", "docs/CURRENT_CONTEXT.md", "docs/INDEX.md"],
            "generated_views_must_be_regenerated": True,
            "new_markdown_or_json_requires_registry_update": True,
            "one_runner_and_complete_receipt_required": True,
        },
        "fail": {
            "allowed_action_policy": "retain-current-action-or-select-cataloged-bounded-correction",
            "complete_receipt_required": True,
            "correction_task_must_be_cataloged": True,
            "correction_task_must_resume_action_class": current,
            "required_failure_records": ["first-meaningful-failure", "failure-classification", "blocked-downstream", "claim-boundary"],
            "required_state_updates": ["state_revision", "predecessor", "active_work_package", "blockers", "unresolved_risks", "updated_by_transaction"],
        },
        "pass": {
            "required_catalog_updates": ["bind-accepted-authority-into-successor", "activate-successor-task", "define-successor-completion-contract-before-selection"],
            "required_output_namespace": "experiments/epoch2-upstream-thin-loader-relocation/",
            "required_output_roles": ["loader-variant-matrix", "launcher-variant-matrix", "executable-discovery-matrix", "native-loader-evidence", "relocation-results", "independent-audit", "machine-authority", "evidence-freeze"],
            "required_state_updates": ["state_revision", "predecessor", "accepted_authorities", "program.gate", "program.next_action_class", "next_action_class", "control_work.next_action_class", "control_work.resume_program_action_class", "unresolved_risks", "updated_by_transaction"],
            "successor_action_class": successor,
            "successor_must_exist": True,
            "successor_task_id": successor_task,
        },
    }


def registry_entry(path: str) -> dict[str, Any]:
    name = Path(path).name
    ext = Path(path).suffix.removeprefix(".")
    if name == "artifact-prototype-authority.json":
        domain = "machine_authority"
    elif name == "independent-audit.json":
        domain = "audit"
    elif ext == "md":
        domain = "claim_evidence"
    else:
        domain = "machine_evidence"
    return {
        "authority_domain": domain,
        "format": ext,
        "lifecycle_class": "FROZEN_AUTHORITY",
        "machine_binding_policy": "allowed",
        "migration_action": "e2-r1-ut1-astral-artifact-and-metadata-prototype",
        "mutability": "immutable",
        "onboarding_visibility": "secondary" if ext == "md" else "machine",
        "owner": "epoch2-research",
        "path": path,
        "planned_canonical_parent": "docs/authorities/experiments/INDEX.md" if ext == "md" else "docs/authorities/machine/INDEX.md",
        "rationale": "",
        "supersession_rule": "Explicit successor experiment or authority only.",
        "update_trigger": "Never edit after freeze; create successor authority.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--output-dir", default=OUTPUT_REL)
    ap.add_argument("--predecessor-head", required=True)
    ap.add_argument("--predecessor-tree", required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    out = root / args.output_dir
    audit = load(out / "independent-audit.json")
    if audit.get("pass") is not True:
        raise SystemExit("independent audit is not PASS")
    artifact_set = load(out / "artifact-set.json")
    py = load(out / "PYTHON.json")
    decisions = load(out / "artifact-flavor-decision-inputs.json")
    file_ids = {name: sha(out / name) for name in [*PRIMARY, *SCRIPTS]}

    readme = """# E2-R1/UT-1 — Astral artifact and metadata prototype

This experiment derives three deterministic local prototype artifacts from the exact official Python.org Android package frozen by UT-0:

- a full Astral-style `python/PYTHON.json + build/ + install/` audit artifact;
- `install_only`, preserving official install bytes while rewriting the archive root;
- `install_only_stripped`, with every ELF mutation recorded by before/after SHA-256.

The official package contains shared `libpython`, extensions, headers, pkg-config files, and the standard library, but no packaged Python interpreter executable. The prototype therefore marks `python_exe` unavailable, does not invent a launcher, object files, static libraries, extension object lists, or relinkable inittab material, and remains unselectable.

The accepted claim is deterministic artifact representation and consumer-readable limitations. Android execution, loader behavior, getpath, relocation, launcher selection, product selection, and publication remain outside this authority.
"""
    (out / "README.md").write_text(readme, encoding="utf-8")

    authority = {
        "schema_version": 1,
        "authority_kind": "e2-r1-ut1-astral-artifact-and-metadata-prototype",
        "status": "frozen-pass-local-prototype-unselectable",
        "predecessor": {"commit": args.predecessor_head, "tree": args.predecessor_tree},
        "upstream_control_authority": {"path": "experiments/epoch2-upstream-thin-control/upstream-control-authority.json", "sha256": "6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c"},
        "artifact_set": artifact_set,
        "python_json": {
            "format_version": py["version"],
            "target_triple": py["target_triple"],
            "python_version": py["python_version"],
            "python_exe": py["python_exe"],
            "extension_count": len(py["build_info"]["extensions"]),
            "unavailable": py["hw_t"]["availability"],
        },
        "flavor_decision_inputs": decisions["observations"],
        "file_identities": file_ids,
        "verification": {"independent_audit": f"{audit['pass_count']}/{audit['check_count']}", "focused_verifier": "required-after-finalization", "negative_fixtures": "required-before-transaction"},
        "claim_boundary": {
            "official_install_bytes": True,
            "deterministic_artifact_derivation": True,
            "consumer_readable_metadata_and_limitations": True,
            "python_executable": False,
            "android_runtime": False,
            "launcher": False,
            "relocation": False,
            "device_qualification": False,
            "epoch3_selection": False,
            "product_selectability": False,
            "publication": False,
        },
        "next_action_class": NEXT_ACTION,
    }
    dump(out / "artifact-prototype-authority.json", authority)
    authority_sha = sha(out / "artifact-prototype-authority.json")
    freeze = f"""# E2-R1/UT-1 Evidence Freeze

```text
authority       {OUTPUT_REL}/artifact-prototype-authority.json
authority sha   {authority_sha}
PYTHON format   8
python_exe      unavailable
flavors         full, install_only, install_only_stripped
selectable      false
audit           {audit['pass_count']}/{audit['check_count']} PASS
```

Accepted: deterministic Astral-style full root, exact install-only derivation, recorded stripped derivation, machine-readable target/runtime/ABI/path/provenance/limitation metadata, exact member manifests, and consumer extraction rules.

Not accepted: packaged interpreter executable, launcher, getpath behavior, Android runtime execution, relocation, device qualification, Epoch 3 selection, product selectability, or publication.
"""
    (out / "evidence-freeze.md").write_text(freeze, encoding="utf-8")

    catalog_path = root / "docs/agent/TASK_CATALOG.json"
    catalog = load(catalog_path)
    ut2 = next(t for t in catalog["tasks"] if t["task_id"] == NEXT_TASK)
    req = {"path": f"{OUTPUT_REL}/artifact-prototype-authority.json", "reason": "Frozen truthful Astral-style artifact and metadata prototype for the binary-derived official package.", "sha256": authority_sha}
    ut2["activation"] = {"prerequisites_satisfied": True, "accepted_authority_path": req["path"], "accepted_authority_sha256": authority_sha, "required_authority_role": "astral-artifact-and-metadata-prototype", "required_predecessor_action_class": ACTION, "status": "ready"}
    for read in ut2.get("required_reads", []):
        if read.get("section_heading") == "## UT-2 — Loader, relocation, launcher, and getpath":
            read["stop_before_heading"] = "## UT-3 — Sysconfig and native-extension SDK"
    if not any(x.get("path") == req["path"] for x in ut2["required_authorities"]):
        ut2["required_authorities"].append(req)
    ut2["completion_contract"] = completion_contract(NEXT_ACTION, FOLLOWING_ACTION, FOLLOWING_TASK)

    if not any(t.get("task_id") == FOLLOWING_TASK for t in catalog["tasks"]):
        catalog["tasks"].append({
            "action_class": FOLLOWING_ACTION,
            "activation": {"prerequisites_satisfied": False, "required_authority_role": "loader-relocation-launcher-getpath", "required_predecessor_action_class": NEXT_ACTION, "status": "blocked-on-predecessor-authority"},
            "claim_boundary": dict(ut2["claim_boundary"]),
            "default_exclusions": list(ut2["default_exclusions"]),
            "deliverable": dict(ut2["deliverable"]),
            "goal": "Normalize runtime and development metadata and prove a real Android native-extension wheel build, install, import, and supported relocation path.",
            "input_routing": dict(ut2["input_routing"]),
            "required_authorities": list(ut2["required_authorities"]),
            "required_reads": [{"path": "docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md", "reason": "Sysconfig, SDK normalization phases, native-extension probe, and exit condition.", "scope": "section", "section_heading": "## UT-3 — Sysconfig and native-extension SDK", "stop_before_heading": "## UT-4 — Android-mandatory data and writable-state policy"}],
            "task_id": FOLLOWING_TASK,
            "title": "Sysconfig and native-extension SDK",
            "work_class": "L",
        })
    dump(catalog_path, catalog)
    catalog_sha = sha(catalog_path)

    state_path = root / "docs/current/STATE.json"
    state = load(state_path)
    state["state_revision"] += 1
    state["predecessor"] = {"commit": args.predecessor_head, "tree": args.predecessor_tree}
    state["accepted_authorities"].append({"id": "e2-r1-ut1-astral-artifact-and-metadata-prototype", "path": f"{OUTPUT_REL}/artifact-prototype-authority.json", "role": "truthful Astral-style local artifact and metadata prototype for the official binary-derived package", "sha256": authority_sha})
    state["program"]["gate"] = {"id": "E2-R1/UT-2", "name": "Loader, relocation, launcher, and getpath", "status": "ready"}
    state["program"]["next_action_class"] = NEXT_ACTION
    state["next_action_class"] = NEXT_ACTION
    state["control_work"]["next_action_class"] = NEXT_ACTION
    state["control_work"]["resume_program_action_class"] = NEXT_ACTION
    state["blockers"] = []
    state["active_work_package"] = None
    state["unresolved_risks"] = ["The official package has no interpreter executable; UT-2 must select and qualify only evidenced launcher, loader, getpath, and relocation behavior before any artifact can become runnable or selectable."]
    state["updated_by_transaction"] = TRANSACTION_ID
    state["task_catalog"]["sha256"] = catalog_sha
    state["task_completion"]["current_action_class"] = NEXT_ACTION
    state["task_completion"]["pass_successor_action_class"] = FOLLOWING_ACTION
    dump(state_path, state)

    registry_path = root / "docs/documentation/document-registry.json"
    registry = load(registry_path)
    existing = {d["path"] for d in registry["documents"]}
    for name in NEW_DOCS:
        path = f"{OUTPUT_REL}/{name}"
        if path not in existing:
            registry["documents"].append(registry_entry(path))
            existing.add(path)
    registry["basis"]["next_action_class"] = NEXT_ACTION
    registry["basis"]["predecessor_head"] = args.predecessor_head
    registry["basis"]["predecessor_tree"] = args.predecessor_tree
    registry["basis"]["tracked_document_count"] = len(registry["documents"])
    registry["basis"]["task_catalog_schema_version"] = catalog["schema_version"]
    dump(registry_path, registry)

    proc = subprocess.run([sys.executable, str(root / "experiments/agent-task-completion/render-document-views.py"), "--root", str(root)])
    if proc.returncode:
        return proc.returncode
    print(json.dumps({"pass": True, "authority_sha256": authority_sha, "state_revision": state["state_revision"], "next_action_class": NEXT_ACTION, "registered_documents": len(NEW_DOCS)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

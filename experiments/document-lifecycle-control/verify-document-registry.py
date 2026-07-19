#!/usr/bin/env python3
"""Verify the Phase 1 document lifecycle registry and legacy-binding boundary."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REGISTRY = Path("docs/documentation/document-registry.json")
SCHEMA = Path("docs/documentation/document-registry.schema.json")
BASELINE = Path("docs/documentation/legacy-live-binding-baseline.json")
ALLOWED_CLASSES = {
    "STABLE", "STABLE_WITH_GENERATED_SECTION", "CURRENT_SOURCE", "CURRENT_REGISTRY",
    "CURRENT_INPUT_LOCK", "ACTIVE_PLAN", "APPEND_ONLY_LOG", "FROZEN_AUTHORITY",
    "HISTORICAL_SNAPSHOT", "GENERATED_VIEW", "REFERENCE", "RAW_REFERENCE",
}
ALLOWED_VISIBILITY = {"primary", "secondary", "contextual", "history", "hidden", "machine"}
FORBIDDEN_POLICIES = {
    "LEGACY_CONFLICT—future-binding-forbidden",
    "LEGACY_OR_SNAPSHOT_ONLY",
    "forbidden-live-view",
    "forbidden-live-plan",
}
REQUIRED_ENTRY_FIELDS = {
    "path", "format", "lifecycle_class", "authority_domain", "owner", "mutability",
    "update_trigger", "supersession_rule", "onboarding_visibility",
    "machine_binding_policy", "migration_action",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def tracked_documents(root: Path) -> set[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, stdout=subprocess.PIPE
    )
    paths = proc.stdout.decode("utf-8").split("\0")
    return {p for p in paths if p and Path(p).suffix in {".md", ".json"}}


def collect_file_identity_bindings(root: Path, json_paths: set[str]) -> set[tuple[str, str, str]]:
    found: set[tuple[str, str, str]] = set()

    def walk(obj: Any, authority_path: str) -> None:
        if isinstance(obj, dict):
            identities = obj.get("file_identities")
            if isinstance(identities, dict):
                for target, value in identities.items():
                    recorded = value.get("sha256") if isinstance(value, dict) else value
                    if isinstance(target, str) and isinstance(recorded, str):
                        found.add((authority_path, target, recorded))
            for value in obj.values():
                walk(value, authority_path)
        elif isinstance(obj, list):
            for value in obj:
                walk(value, authority_path)

    for path in sorted(json_paths):
        try:
            obj = load_json(root / path)
        except (OSError, json.JSONDecodeError):
            continue
        walk(obj, path)
    return found


def verify(root: Path) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    errors: dict[str, str] = {}

    def ck(name: str, value: bool, error: str = "") -> None:
        checks[name] = bool(value)
        if not value and error:
            errors[name] = error

    try:
        registry = load_json(root / REGISTRY)
        schema = load_json(root / SCHEMA)
        baseline = load_json(root / BASELINE)
        ck("control_files_parse", True)
    except Exception as exc:  # noqa: BLE001
        ck("control_files_parse", False, f"{type(exc).__name__}: {exc}")
        registry = {}; schema = {}; baseline = {}

    ck("registry_identity", registry.get("schema_version") == 1 and registry.get("registry_kind") == "document-lifecycle-registry")
    basis = registry.get("basis", {}) if isinstance(registry, dict) else {}
    ck("phase1_boundary", basis.get("migration_phase") == 1 and basis.get("current_source_present") is False and basis.get("physical_moves_allowed") is False)
    ck("schema_identity", schema.get("$id") == "urn:cpython-android-cli:document-registry:v1" and schema.get("type") == "object")
    ck("lifecycle_class_set", set(registry.get("lifecycle_classes", [])) == ALLOWED_CLASSES)

    docs = registry.get("documents", []) if isinstance(registry, dict) else []
    ck("documents_array", isinstance(docs, list) and bool(docs))
    paths = [d.get("path") for d in docs if isinstance(d, dict)]
    ck("registry_paths_unique", len(paths) == len(set(paths)))
    ck("registry_paths_safe", all(isinstance(p, str) and p and not p.startswith("/") and ".." not in Path(p).parts for p in paths))

    field_complete = True
    values_valid = True
    format_valid = True
    for d in docs:
        if not isinstance(d, dict) or not REQUIRED_ENTRY_FIELDS.issubset(d):
            field_complete = False
            continue
        if any(not isinstance(d.get(k), str) or not d.get(k) for k in REQUIRED_ENTRY_FIELDS):
            field_complete = False
        if d.get("lifecycle_class") not in ALLOWED_CLASSES or d.get("onboarding_visibility") not in ALLOWED_VISIBILITY:
            values_valid = False
        path = d.get("path", "")
        expected = Path(path).suffix.lstrip(".")
        if d.get("format") != expected or expected not in {"md", "json"}:
            format_valid = False
    ck("required_metadata_complete", field_complete)
    ck("metadata_values_valid", values_valid)
    ck("format_matches_path", format_valid)

    try:
        tracked = tracked_documents(root)
        ck("git_document_inventory", True)
    except Exception as exc:  # noqa: BLE001
        tracked = set()
        ck("git_document_inventory", False, f"{type(exc).__name__}: {exc}")
    registry_paths = {p for p in paths if isinstance(p, str)}
    ck("tracked_documents_exact", tracked == registry_paths, f"missing={sorted(tracked-registry_paths)} extra={sorted(registry_paths-tracked)}")
    ck("registry_count_exact", basis.get("tracked_document_count") == len(tracked) == len(registry_paths))
    ck("registered_paths_exist", all((root / p).is_file() for p in registry_paths))

    by_path = {d.get("path"): d for d in docs if isinstance(d, dict) and isinstance(d.get("path"), str)}
    current_successors_valid = True
    for d in docs:
        if not isinstance(d, dict):
            continue
        for target in d.get("current_successors", []) or []:
            if target not in by_path or not (root / target).is_file():
                current_successors_valid = False
    ck("current_supersession_targets_exist", current_successors_valid)

    frozen_mutability = all(
        d.get("mutability") in {"immutable", "immutable-versioned", "controlled-versioned"}
        for d in docs if isinstance(d, dict) and d.get("lifecycle_class") in {"FROZEN_AUTHORITY", "HISTORICAL_SNAPSHOT", "RAW_REFERENCE"}
    )
    ck("frozen_mutability_policy", frozen_mutability)
    generated_policy = all(
        "forbidden" in str(d.get("machine_binding_policy", "")).lower()
        for d in docs if isinstance(d, dict) and d.get("lifecycle_class") == "GENERATED_VIEW"
    )
    ck("generated_binding_policy", generated_policy)

    expected_baseline = {
        (b.get("authority_path"), b.get("target_path"), b.get("recorded_sha256"))
        for b in baseline.get("bindings", []) if isinstance(b, dict)
    }
    ck("legacy_baseline_identity", baseline.get("schema_version") == 1 and baseline.get("baseline_kind") == "legacy-live-document-file-identity-bindings")
    ck("legacy_baseline_unique", len(expected_baseline) == len(baseline.get("bindings", [])) == baseline.get("expected_binding_count"))
    forbidden_targets = {
        p for p, d in by_path.items()
        if d.get("machine_binding_policy") in FORBIDDEN_POLICIES
    }
    ck("forbidden_target_set", forbidden_targets == set(baseline.get("forbidden_live_targets", [])))

    observed = collect_file_identity_bindings(root, {p for p in tracked if p.endswith(".json")})
    observed_forbidden = {b for b in observed if b[1] in forbidden_targets}
    ck("legacy_bindings_exact", observed_forbidden == expected_baseline,
       f"missing={sorted(expected_baseline-observed_forbidden)} extra={sorted(observed_forbidden-expected_baseline)}")
    ck("no_new_forbidden_binding", not (observed_forbidden - expected_baseline))

    # Exact control-plane files must be classified in their intended classes.
    expected_classes = {
        "docs/documentation/DOCUMENT_LIFECYCLE.md": "STABLE",
        "docs/documentation/document-registry.json": "CURRENT_REGISTRY",
        "docs/documentation/document-registry.schema.json": "STABLE",
        "docs/documentation/legacy-live-binding-baseline.json": "FROZEN_AUTHORITY",
    }
    ck("control_plane_classification", all(by_path.get(p, {}).get("lifecycle_class") == c for p, c in expected_classes.items()))

    failed = [name for name, value in checks.items() if not value]
    return {
        "schema_version": 1,
        "verifier_kind": "document-lifecycle-control-plane-v1",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": len(checks) - len(failed),
        "failed_checks": failed,
        "checks": checks,
        "errors": errors,
        "metrics": {
            "tracked_document_count": len(tracked),
            "registry_document_count": len(registry_paths),
            "legacy_binding_count": len(expected_baseline),
            "observed_forbidden_binding_count": len(observed_forbidden),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    result = verify(Path(args.root).resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

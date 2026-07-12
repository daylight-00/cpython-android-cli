#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_PORTABLE_FINGERPRINT = (
    "f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978"
)
EXPECTED_PHASE4_RESULT_INDEX = (
    "878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce"
)


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def same_path(value: object, expected: Path) -> bool:
    return isinstance(value, str) and Path(value).resolve() == expected.resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--a-installation-root", required=True, type=Path)
    parser.add_argument("--b-installation-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    results = args.results_dir.resolve()
    a_root = args.a_installation_root.resolve()
    b_root = args.b_installation_root.resolve()
    a_prefix = a_root / "prefix"
    b_prefix = b_root / "prefix"

    paths = {
        "baseline_verification": results / "baseline/verification.json",
        "baseline_workflow": results / "baseline/workflow-status.json",
        "baseline_accepted": results / "baseline/accepted-inputs.json",
        "relocated_verification": results / "relocated-baseline-verification.json",
        "relocation_state": results / "relocation-state.json",
        "a_root": results / "a-installation-root.json",
        "b_root_move": results / "b-installation-root-after-move.json",
        "b_root_after": results / "b-installation-root-after-probes.json",
        "a_strict": results / "a-installed-strict.json",
        "b_strict_before": results / "b-installed-strict-before.json",
        "b_strict_after": results / "b-installed-strict-after.json",
        "a_portable": results / "a-installed-portable.json",
        "b_portable_before": results / "b-installed-portable-before.json",
        "b_portable_after": results / "b-installed-portable-after.json",
        "a_registry": results / "a-registry.json",
        "b_registry": results / "b-registry.json",
        "engine": results / "relocated/engine-verification.json",
        "stale": results / "stale-prefix-scan.json",
    }

    missing = sorted(str(path) for path in paths.values() if not path.is_file())
    parse_errors: dict[str, str] = {}
    values: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        if not path.is_file():
            continue
        try:
            values[name] = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            parse_errors[str(path)] = repr(exc)

    baseline = values.get("baseline_verification", {})
    baseline_workflow = values.get("baseline_workflow", {})
    baseline_accepted = values.get("baseline_accepted", {})
    relocated = values.get("relocated_verification", {})
    state = values.get("relocation_state", {})
    a_root_fp = values.get("a_root", {})
    b_root_move = values.get("b_root_move", {})
    b_root_after = values.get("b_root_after", {})
    a_strict = values.get("a_strict", {})
    b_strict_before = values.get("b_strict_before", {})
    b_strict_after = values.get("b_strict_after", {})
    a_portable = values.get("a_portable", {})
    b_portable_before = values.get("b_portable_before", {})
    b_portable_after = values.get("b_portable_after", {})
    a_registry = values.get("a_registry", {})
    b_registry = values.get("b_registry", {})
    engine = values.get("engine", {})
    stale = values.get("stale", {})

    baseline_rcs = baseline_workflow.get("returncodes", {})
    strict_fingerprints = {
        a_strict.get("fingerprint"),
        b_strict_before.get("fingerprint"),
        b_strict_after.get("fingerprint"),
    }
    portable_fingerprints = {
        a_portable.get("fingerprint"),
        b_portable_before.get("fingerprint"),
        b_portable_after.get("fingerprint"),
    }
    root_fingerprints = {
        a_root_fp.get("fingerprint"),
        b_root_move.get("fingerprint"),
        b_root_after.get("fingerprint"),
    }

    checks = {
        "all_required_outputs_present": not missing,
        "all_required_outputs_parse": not parse_errors,
        "baseline_gate1_pass": baseline.get("pass") is True,
        "baseline_gate1_check_count_80": baseline.get("check_count") == 80,
        "baseline_gate1_failed_empty": baseline.get("failed_checks") == [],
        "baseline_workflow_pass": baseline_workflow.get("pass") is True,
        "baseline_workflow_all_zero": bool(baseline_rcs)
        and all(value == 0 for value in baseline_rcs.values()),
        "baseline_accepted_phase4_pass": baseline_accepted.get("pass") is True,
        "baseline_accepted_phase4_exact": baseline_accepted.get(
            "observed_result_index_sha256"
        )
        == EXPECTED_PHASE4_RESULT_INDEX,
        "relocated_gate1_pass": relocated.get("pass") is True,
        "relocated_gate1_check_count_80": relocated.get("check_count") == 80,
        "relocated_gate1_failed_empty": relocated.get("failed_checks") == [],
        "relocation_state_pass": state.get("pass") is True,
        "relocation_a_root_matches": same_path(
            state.get("a_installation_root"), a_root
        ),
        "relocation_b_root_matches": same_path(
            state.get("b_installation_root"), b_root
        ),
        "relocation_a_absent": state.get("a_exists_after_move") is False
        and not a_root.exists(),
        "relocation_b_present": state.get("b_exists_after_move") is True
        and b_root.is_dir(),
        "relocation_b_python_executable": state.get(
            "b_python_executable_after_move"
        )
        is True
        and (b_prefix / "bin/python").is_file(),
        "relocation_same_filesystem": state.get("same_filesystem") is True,
        "relocation_inode_preserved": state.get("inode_preserved") is True,
        "installation_root_fingerprints_pass": a_root_fp.get("pass") is True
        and b_root_move.get("pass") is True
        and b_root_after.get("pass") is True,
        "installation_root_entry_count_717": a_root_fp.get("entry_count") == 717
        and b_root_move.get("entry_count") == 717
        and b_root_after.get("entry_count") == 717,
        "installation_root_no_special": a_root_fp.get("special_paths") == []
        and b_root_move.get("special_paths") == []
        and b_root_after.get("special_paths") == [],
        "installation_root_exact_across_move_and_probes": len(root_fingerprints) == 1
        and None not in root_fingerprints,
        "strict_fingerprints_pass": a_strict.get("pass") is True
        and b_strict_before.get("pass") is True
        and b_strict_after.get("pass") is True,
        "strict_entry_count_714": a_strict.get("entry_count") == 714
        and b_strict_before.get("entry_count") == 714
        and b_strict_after.get("entry_count") == 714,
        "strict_exact_across_move_and_probes": len(strict_fingerprints) == 1
        and None not in strict_fingerprints,
        "strict_pycache_zero": a_strict.get("pycache_paths") == []
        and b_strict_before.get("pycache_paths") == []
        and b_strict_after.get("pycache_paths") == [],
        "strict_special_zero": a_strict.get("special_paths") == []
        and b_strict_before.get("special_paths") == []
        and b_strict_after.get("special_paths") == [],
        "portable_fingerprints_pass": a_portable.get("pass") is True
        and b_portable_before.get("pass") is True
        and b_portable_after.get("pass") is True,
        "portable_entry_count_714": a_portable.get("entry_count") == 714
        and b_portable_before.get("entry_count") == 714
        and b_portable_after.get("entry_count") == 714,
        "portable_exact_expected": portable_fingerprints
        == {EXPECTED_PORTABLE_FINGERPRINT},
        "portable_a_root_matches": same_path(a_portable.get("root"), a_prefix),
        "portable_b_roots_match": same_path(
            b_portable_before.get("root"), b_prefix
        )
        and same_path(b_portable_after.get("root"), b_prefix),
        "registry_schema": a_registry.get("schema_version") == 1
        and b_registry.get("schema_version") == 1,
        "registry_owned_count_714": len(a_registry.get("owned_paths", [])) == 714
        and len(b_registry.get("owned_paths", [])) == 714,
        "registry_artifact_count_1": len(a_registry.get("artifacts", [])) == 1
        and len(b_registry.get("artifacts", [])) == 1,
        "registry_exact_across_move": a_registry == b_registry,
        "engine_verify_pass": engine.get("pass") is True,
        "engine_verify_counts": engine.get("artifact_count") == 1
        and engine.get("owned_path_count") == 714,
        "engine_verify_bad_paths_empty": engine.get("bad_paths") == [],
        "stale_scan_pass": stale.get("pass") is True,
        "stale_scan_a_absent": stale.get("a_root_absent") is True,
        "stale_scan_tree_clean": stale.get("regular_file_matches") == []
        and stale.get("symlink_matches") == [],
        "stale_scan_probes_clean": stale.get("probe_matches") == [],
        "machine_json_canonical": all(
            path.read_bytes() == canonical_json_bytes(values[name])
            for name, path in paths.items()
            if name in values
        ),
    }
    if len(checks) != 46:
        raise RuntimeError(f"unexpected check count: {len(checks)}")

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_outputs": missing,
        "parse_errors": parse_errors,
        "a_installation_root": str(a_root),
        "b_installation_root": str(b_root),
        "observed": {
            "installation_root_entry_count": a_root_fp.get("entry_count"),
            "installation_root_fingerprint": a_root_fp.get("fingerprint"),
            "installed_strict_fingerprint": a_strict.get("fingerprint"),
            "installed_portable_fingerprint": a_portable.get("fingerprint"),
            "registry_owned_count": len(b_registry.get("owned_paths", [])),
            "relocated_revalidation_check_count": relocated.get("check_count"),
        },
        "claim_boundary": {
            "proved": (
                "The runtime-base installed through the frozen Phase 4 engine was "
                "moved as a complete installation root on one filesystem, retained "
                "exact payload and registry identity, contained no stale location-A "
                "references, and passed the complete 80-check runtime, HTTPS, uv, "
                "native-closure, and extension-import validation at location B."
            ),
            "not_proved": (
                "Cross-filesystem copy relocation, same-version reinstall and repair, "
                "addon lifecycle, exact uninstall preservation, upgrade, downgrade, "
                "and physical power-loss persistence remain separate claims."
            ),
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 65


if __name__ == "__main__":
    raise SystemExit(main())

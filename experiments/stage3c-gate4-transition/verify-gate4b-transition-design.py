#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_GROUPS = {
    "preflight": 14,
    "happy": 8,
    "collision": 12,
    "recovery": 24,
    "locking": 2,
    "audit": 6,
}
EXPECTED_BLOBS = {
    "recovery_common.py": "3183ba0861ef45e7a395201bec0085f3f69fb248",
    "recovery_durability.py": "61bfb859f73acccb0dfcce1d2a630bfd1ffc2d3f",
    "recovery_engine.py": "aebf5b9a33d163f7f8758f785ca621c94c0e478b",
    "recovery_operations.py": "8a307065e00fd7a7332541f4911c5478945374ee",
}
EXPECTED_LOCKS = {
    "3.14.6": "83f6b1fd3b610c22606f8dd4108a86cf2454e5997d0d0ada4124a209bfb091b7",
    "3.14.5": "e8c189d4a7386f1c522cc1479515b266fff60fdffedb3b7e842d9730ec21faeb",
}
EXPECTED_TOPOLOGIES = {
    "runtime": ({"runtime-base"}, 714, 714, 60, 653, 656),
    "runtime-development": ({"runtime-base", "development-addon"}, 1168, 1161, 71, 1088, 1100),
    "runtime-test": ({"runtime-base", "test-addon"}, 2502, 2499, 205, 2293, 2299),
    "composed": ({"runtime-base", "development-addon", "test-addon"}, 2956, 2946, 216, 2728, 2743),
}


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(root: Path, relative: str) -> str:
    return subprocess.check_output(["git", "hash-object", relative], cwd=root, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--matrix", type=Path, default=Path(__file__).with_name("gate4b-transition-matrix.json"))
    parser.add_argument("--inventory", type=Path, default=Path(__file__).with_name("gate4b-cross-version-inventory.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    root = args.repository.resolve()
    matrix = json.loads(args.matrix.read_text())
    inventory = json.loads(args.inventory.read_text())
    checks: dict[str, bool] = {}

    def ck(name: str, condition: bool) -> None:
        if name in checks:
            raise RuntimeError(f"duplicate check: {name}")
        checks[name] = bool(condition)

    # Inventory identities and exact delta.
    ck("inventory_schema", inventory.get("schema_version") == 1)
    ck("inventory_kind", inventory.get("inventory_kind") == "stage3c-phase5-gate4b-cross-version-manifest-inventory")
    products = inventory.get("products", {})
    ck("product_versions", products.get("first", {}).get("python_version") == "3.14.6" and products.get("second", {}).get("python_version") == "3.14.5")
    ck("product_source_commits", products.get("first", {}).get("source_commit") == "c63aec69bd59c55314c06c23f4c22c03de76fe45" and products.get("second", {}).get("source_commit") == "5607950ef232dad16d75c0cf53101d9649d89115")
    ck("product_locks", products.get("first", {}).get("product_lock_sha256") == EXPECTED_LOCKS["3.14.6"] and products.get("second", {}).get("product_lock_sha256") == EXPECTED_LOCKS["3.14.5"])
    ck("first_authority_archive", products.get("first", {}).get("authority_archive_sha256") == "43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a")
    ck("second_authority_archive", products.get("second", {}).get("authority_archive_sha256") == "4565b69e78c618f58fda59f928c086bbcf1cd02cfb28252f419e42e8cbc266aa")
    global_delta = inventory.get("global", {})
    ck("global_first_count", global_delta.get("first_owned_paths") == 2956)
    ck("global_second_count", global_delta.get("second_owned_paths") == 2946)
    ck("global_union_count", global_delta.get("union_paths") == 2958)
    ck("global_shared_count", global_delta.get("shared_paths") == 2944)
    ck("global_same_count", global_delta.get("byte_identity_same") == 216)
    ck("global_replace_count", global_delta.get("replacement_required") == 2728)
    ck("global_one_sided", global_delta.get("first_only") == 12 and global_delta.get("second_only") == 2)
    ck("global_no_owner_transfer", global_delta.get("owner_transfer_count") == 0 and global_delta.get("owner_transfers") == [])
    ck("classification_digest", global_delta.get("classification_sha256") == "1daad3ef9c99eba060852962231e12e6361877709f15e0cb2f18952574f4310b")
    ck("first_only_paths_exact", set(global_delta.get("first_only_paths", [])) == {
        "lib/python3.14/ensurepip/_bundled/pip-26.1.2-py3-none-any.whl",
        "include/openssl/byteorder.h", "include/openssl/e_ostime.h", "include/openssl/hpke.h",
        "include/openssl/indicator.h", "include/openssl/ml_kem.h", "include/openssl/quic.h",
        "include/openssl/thread.h", "include/openssl/x509_acert.h",
        "lib/python3.14/test/test_capi/test_weakref.py",
        "lib/python3.14/test/test_free_threading/test_dict_watcher.py",
        "lib/python3.14/test/test_free_threading/test_pickle.py",
    })
    ck("second_only_paths_exact", set(global_delta.get("second_only_paths", [])) == {
        "lib/python3.14/ensurepip/_bundled/pip-26.1.1-py3-none-any.whl",
        "include/openssl/asn1_mac.h",
    })
    per = inventory.get("per_artifact", {})
    ck("runtime_delta", all(per.get("runtime-base", {}).get(k) == v for k, v in {
        "first_owned": 714, "second_owned": 714, "shared_paths": 713,
        "byte_identity_same": 60, "replacement_required": 653, "first_only": 1, "second_only": 1,
    }.items()))
    ck("development_delta", all(per.get("development-addon", {}).get(k) == v for k, v in {
        "first_owned": 454, "second_owned": 447, "shared_paths": 446,
        "byte_identity_same": 11, "replacement_required": 435, "first_only": 8, "second_only": 1,
    }.items()))
    ck("test_delta", all(per.get("test-addon", {}).get(k) == v for k, v in {
        "first_owned": 1788, "second_owned": 1785, "shared_paths": 1785,
        "byte_identity_same": 145, "replacement_required": 1640, "first_only": 3, "second_only": 0,
    }.items()))
    gaps = inventory.get("frozen_engine_gap_inventory", {})
    ck("gap_count", len(gaps.get("direct_cross_product_install", [])) == 4)
    ck("gap_source_only", any("remain on disk" in x for x in gaps.get("direct_cross_product_install", [])))
    ck("gap_mixed_addons", any("other product" in x for x in gaps.get("direct_cross_product_install", [])))
    ck("gap_product_atomicity", any("product-level rollback" in x for x in gaps.get("direct_cross_product_install", [])))
    ck("gap_decision", "dedicated whole-product transition" in gaps.get("decision", ""))

    # Matrix structure and authority.
    ck("matrix_schema", matrix.get("schema_version") == 1)
    ck("matrix_kind", matrix.get("matrix_kind") == "stage3c-phase5-gate4b-cross-version-transition-contract-design")
    ck("matrix_status", matrix.get("status") == "design-frozen-target-evidence-pending")
    scenarios = matrix.get("scenarios", [])
    ck("scenario_count", matrix.get("scenario_count") == 66 and len(scenarios) == 66)
    group_counts = Counter(s.get("group") for s in scenarios)
    ck("scenario_groups", dict(group_counts) == EXPECTED_GROUPS and matrix.get("scenario_group_counts") == EXPECTED_GROUPS)
    ids = [s.get("id") for s in scenarios]
    ck("scenario_ids_unique", len(ids) == len(set(ids)) == 66)
    ck("scenario_required_evidence", all(set(["process_output", "real_returncode", "before_registry", "after_registry", "owned_payload_inventory", "unowned_inventory", "transition_journal", "transaction_inventory"]).issubset(s.get("required_evidence", [])) for s in scenarios))
    authority = matrix.get("authority", {})
    ck("matrix_inventory_name", authority.get("manifest_inventory") == "gate4b-cross-version-inventory.json")
    ck("matrix_inventory_digest", authority.get("manifest_inventory_classification_sha256") == global_delta.get("classification_sha256"))
    ck("matrix_product_locks", all(authority.get("products", {}).get(v, {}).get("product_lock_sha256") == h for v, h in EXPECTED_LOCKS.items()))
    blobs = authority.get("frozen_engine_git_blobs", {})
    ck("matrix_blob_map", blobs == EXPECTED_BLOBS)
    observed_blobs = {name: git_blob(root, f"experiments/stage3c-installation-recovery/{name}") for name in EXPECTED_BLOBS}
    ck("engine_blobs_exact", observed_blobs == EXPECTED_BLOBS)
    topologies = authority.get("topologies", {})
    for name, (artifacts, first_count, second_count, same, replace, mutations) in EXPECTED_TOPOLOGIES.items():
        item = topologies.get(name, {})
        ck(f"topology_{name}", set(item.get("artifacts", [])) == artifacts and item.get("3.14.6") == first_count and item.get("3.14.5") == second_count and item.get("same") == same and item.get("replace") == replace and item.get("mutations") == mutations)

    # Policy: non-reopening whole-product transaction.
    policy = matrix.get("policy", {})
    ck("policy_dedicated_operation", "dedicated whole-product transition" in policy.get("operation", ""))
    ck("policy_exact_source", "exact recognized frozen product" in policy.get("source_precondition", ""))
    ck("policy_topology_preserved", policy.get("topology") == "preserve the installed artifact set across the transition")
    path_plan = policy.get("path_plan", {})
    ck("policy_path_plan", path_plan == {
        "shared_exact": "noop",
        "shared_changed": "replace transactionally",
        "source_only": "remove transactionally",
        "target_only": "create transactionally",
        "owner_transfer": "unsupported and absent in this authority pair",
    })
    ck("policy_modified_owned_reject", "reject before mutation" in policy.get("modified_owned", ""))
    ck("policy_unowned_preserve", "preserve unchanged" in policy.get("unowned_descendant", ""))
    ck("policy_collision_reject", policy.get("unowned_target_collision") == "reject before mutation")
    ck("policy_registry_v1", "schema version 1" in policy.get("registry", ""))
    ck("policy_product_derived", "runtime-base artifact ID" in policy.get("active_product_identity", "") and "do not install a separate mutable product lock" in policy.get("active_product_identity", ""))
    ck("policy_journal_compatible", "frozen schema-2 mutation vocabulary" in policy.get("journal", "") and "PREPARED/APPLYING/COMMITTED" in policy.get("journal", ""))
    ck("policy_lock_reused", "frozen exclusive installation lock" in policy.get("lock", ""))
    recovery_policy = policy.get("recovery", {})
    ck("policy_precommit_recovery", recovery_policy.get("precommit") == "restore exact source and retain one ROLLED_BACK tombstone" and recovery_policy.get("precommit_second") == "NOOP_ROLLED_BACK")
    ck("policy_committed_recovery", recovery_policy.get("committed") == "finalize exact target and clean transaction" and recovery_policy.get("committed_second") == "ZERO_TRANSACTIONS")
    ck("policy_non_reopening", all(term in policy.get("implementation_boundary", "") for term in ["must not modify", "frozen Phase 4 engine files", "registry schema", "artifact manifests", "archive bytes"]))

    # Scenario semantics.
    preflight = [s for s in scenarios if s.get("group") == "preflight"]
    ck("preflight_count", len(preflight) == 14)
    ck("preflight_zero_mutation", all(s.get("mutation_count") == 0 for s in preflight))
    ck("preflight_exact_classes", set(s.get("expected_result") for s in preflight) == {
        "REJECT_NO_ACTIVE_PRODUCT", "REJECT_UNKNOWN_PRODUCT", "REJECT_MIXED_PRODUCT", "REJECT_INVALID_TOPOLOGY",
        "REJECT_SOURCE_NOT_EXACT", "REJECT_TARGET_AUTHORITY", "REJECT_TOPOLOGY_CHANGE", "REJECT_RECOVERY_REQUIRED",
    })
    ck("preflight_modified_owned", {s.get("initial_state") for s in preflight if s.get("expected_result") == "REJECT_SOURCE_NOT_EXACT"} == {"modified-owned-regular", "modified-owned-symlink", "missing-owned-leaf", "wrong-owned-type"})
    ck("preflight_target_inputs", {s.get("initial_state") for s in preflight if s.get("expected_result") == "REJECT_TARGET_AUTHORITY"} == {"wrong-target-product-lock", "wrong-target-manifest", "wrong-target-archive"})
    happy = [s for s in scenarios if s.get("group") == "happy"]
    ck("happy_count", len(happy) == 8)
    ck("happy_direction_topology_cross_product", Counter((s.get("direction"), s.get("initial_state")) for s in happy) == Counter((d, t) for d in ["upgrade", "downgrade"] for t in EXPECTED_TOPOLOGIES))
    ck("happy_schema_v1", all(s.get("expected_registry_schema") == 1 for s in happy))
    ck("happy_plan_mutations", all(s.get("plan", {}).get("mutation_count") == EXPECTED_TOPOLOGIES[s.get("initial_state")][5] for s in happy))
    ck("happy_behavior_surface", all(set(["runtime_identity", "native_closure", "https_timezone", "subprocess", "venv_uv", "relocation", "installed_addons"]).issubset(s.get("post_behavior", [])) for s in happy))
    collision = [s for s in scenarios if s.get("group") == "collision"]
    ck("collision_count", len(collision) == 12)
    ck("collision_both_directions", Counter(s.get("direction") for s in collision) == Counter({"upgrade": 6, "downgrade": 6}))
    ck("collision_unowned_preserve", sum("unowned" in s.get("subject", "") and "preserve" in s.get("expected_result", "") for s in collision) == 6)
    ck("collision_target_reject", sum(s.get("subject") == "target-only-unowned-collision" and "reject" in s.get("expected_result", "") for s in collision) == 2)
    ck("collision_direct_install_reject", sum(s.get("subject") == "ordinary-install-cross-product" and "use transition" in s.get("expected_result", "") for s in collision) == 2)
    ck("collision_no_stale", sum(s.get("subject") == "source-only-exact-paths" and "no stale" in s.get("expected_result", "") for s in collision) == 2)
    recovery = [s for s in scenarios if s.get("group") == "recovery"]
    ck("recovery_count", len(recovery) == 24)
    ck("recovery_full_cross_product", Counter((s.get("direction"), s.get("initial_state"), s.get("crash_boundary")) for s in recovery) == Counter((d, t, b) for d in ["upgrade", "downgrade"] for t in EXPECTED_TOPOLOGIES for b in ["prepared", "applying-late", "committed"]))
    ck("recovery_returncodes", Counter(s.get("expected_crash_returncode") for s in recovery) == Counter({90: 8, 93: 8, 92: 8}))
    ck("recovery_actions", all((s.get("crash_boundary") == "committed" and s.get("expected_recovery_action") == "FINALIZED_COMMIT" and s.get("expected_second_recovery") == "ZERO_TRANSACTIONS" and s.get("expected_state") == "target-exact") or (s.get("crash_boundary") != "committed" and s.get("expected_recovery_action") == "ROLLED_BACK" and s.get("expected_second_recovery") == "NOOP_ROLLED_BACK" and s.get("expected_state") == "source-exact") for s in recovery))
    ck("recovery_mutation_totals", all(s.get("transition_mutation_count") == EXPECTED_TOPOLOGIES[s.get("initial_state")][5] for s in recovery))
    locking = [s for s in scenarios if s.get("group") == "locking"]
    ck("locking_count", len(locking) == 2 and {s.get("direction") for s in locking} == {"upgrade", "downgrade"})
    ck("locking_rc44", all(s.get("expected_returncode") == 44 and s.get("mutation_count") == 0 for s in locking))
    audit = [s for s in scenarios if s.get("group") == "audit"]
    ck("audit_count", len(audit) == 6)
    ck("audit_authority", "both product locks exact" in audit[0].get("assertions", []))
    ck("audit_delta", set(["union 2958", "shared 2944", "same 216", "replace 2728", "first-only 12", "second-only 2", "owner transfers 0"]).issubset(audit[1].get("assertions", [])))
    ck("audit_registry", "schema remains 1" in audit[2].get("assertions", []) and "no separate mutable product state" in audit[2].get("assertions", []))
    ck("audit_final_state", "source-only absent" in audit[3].get("assertions", []) and "unowned sentinels unchanged" in audit[3].get("assertions", []))
    ck("audit_recovery", "second recovery idempotent" in audit[4].get("assertions", []))
    ck("audit_evidence", set(["raw stdout/stderr", "real returncodes", "canonical JSON", "archive safety", "complete result index", "independent verifier", "explicit claim boundary"]).issubset(audit[5].get("assertions", [])))

    # Execution and claim boundaries.
    execution = matrix.get("execution_contract", {})
    ck("execution_single_wrapper", execution.get("single_termux_wrapper") is True)
    ck("execution_pass_fail_archive", execution.get("pass_or_fail_archive_required") is True)
    ck("execution_zstd", execution.get("new_archive_suffix") == ".tar.zst")
    ck("execution_historical_immutable", execution.get("historical_archives_immutable") is True)
    ck("execution_design_no_transition", execution.get("no_transition_execution_in_design_gate") is True)
    evidence = set(matrix.get("target_evidence_requirements", []))
    ck("evidence_contract", set([
        "fresh exact extraction of both product authorities", "inode-separated roots for every scenario",
        "synchronous raw stdout and stderr", "real process return codes", "before and after registry snapshots",
        "complete owned and unowned inventories", "transition journal and transaction snapshots",
        "first and second recovery evidence", "post-transition runtime/native/HTTPS/timezone/subprocess/venv/uv/relocation probes",
        "canonical machine JSON", "archive safety report", "complete root result-index recomputation",
        "independent verifier", "explicit claim boundary",
    ]).issubset(evidence))
    claim = matrix.get("claim_boundary", {})
    ck("claim_design_only", "sixty-six-scenario" in claim.get("proved_by_design", ""))
    ck("claim_no_implementation", "No transition implementation" in claim.get("not_proved_by_design", ""))
    ck("claim_close_sequence", "repository implementation gate" in claim.get("gate4b_close_requires", "") and "Termux result archive" in claim.get("gate4b_close_requires", ""))

    # Repository documentation state.
    docs = {
        "root": root / "README.md",
        "context": root / "docs/PROJECT_CONTEXT_STAGE3C.md",
        "scope": root / "docs/stages/STAGE3C_PHASE5_SCOPE.md",
        "lifecycle": root / "experiments/stage3c-installed-runtime-lifecycle/README.md",
        "gate4a": root / "experiments/stage3c-gate4-second-product-authority/README.md",
        "design": root / "experiments/stage3c-gate4-transition/GATE4B_TRANSITION_CONTRACT_DESIGN.md",
        "readme": root / "experiments/stage3c-gate4-transition/README.md",
    }
    texts = {name: path.read_text() for name, path in docs.items()}
    ck("docs_root_state", "Gate 4B design frozen; implementation pending" in texts["root"])
    ck("docs_context_state", "Gate 4B    cross-version transition contract            DESIGN FROZEN — 66 scenarios" in texts["context"])
    ck("docs_scope_state", "Gate 4B   cross-version transition contract                       DESIGN FROZEN — 66 scenarios" in texts["scope"])
    ck("docs_lifecycle_state", "Gate 4B transition design frozen" in texts["lifecycle"])
    ck("docs_gate4a_next", "experiments/stage3c-gate4-transition/GATE4B_TRANSITION_CONTRACT_DESIGN.md" in texts["gate4a"])
    ck("docs_design_status", "DESIGN FROZEN — implementation and target evidence pending" in texts["design"])
    ck("docs_design_inventory", all(term in texts["design"] for term in ["union owned paths       2958", "replacement required    2728", "cross-artifact transfers    0"]))
    ck("docs_design_non_reopening", "does not modify the frozen Phase 4 engine files" in texts["design"] and "registry remains schema version 1" in texts["design"])
    ck("docs_design_66", "exactly 66 scenarios" in texts["design"])
    ck("docs_design_claim", "does not prove a transition implementation" in texts["design"])
    ck("docs_readme_state", "Gate 4B  transition contract design               DESIGN FROZEN — 66 scenarios" in texts["readme"])

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "verification_kind": "stage3c-phase5-gate4b-transition-contract-design-verification",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "checks": checks,
        "failed_checks": failed,
        "matrix_sha256": sha256(args.matrix.resolve()),
        "inventory_sha256": sha256(args.inventory.resolve()),
        "observed": {
            "scenario_count": len(scenarios),
            "scenario_group_counts": dict(group_counts),
            "engine_git_blobs": observed_blobs,
        },
        "claim_boundary": claim,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(cjson(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"\nGATE4B_TRANSITION_DESIGN_VERIFICATION={result['pass_count']}/{result['check_count']} " + ("PASS" if result["pass"] else "FAIL"))
    return 0 if result["pass"] or not args.require_pass else 41


if __name__ == "__main__":
    raise SystemExit(main())

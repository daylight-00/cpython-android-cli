#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path
from typing import Any

P4_INDEX = "878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce"
PORTABLE = "f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978"
SUCCESS = {"exact-noop", "regular-bytes", "regular-mode", "regular-wrong-type", "symlink-target", "missing-regular", "missing-symlink"}
BOUNDARIES = {
    "prepared": (90, "PREPARED", [], 0, False),
    "intent-1": (93, "APPLYING", [("created", "INTENT")], 0, False),
    "mutation-1": (91, "APPLYING", [("created", "APPLIED")], 1, False),
    "intent-2": (93, "APPLYING", [("created", "APPLIED"), ("registry", "INTENT")], 2, False),
    "mutation-2": (91, "APPLYING", [("created", "APPLIED"), ("registry", "APPLIED")], 2, False),
    "committed": (92, "COMMITTED", [("created", "APPLIED"), ("registry", "APPLIED")], 0, True),
}
CRASH = {f"{kind}-{boundary}" for kind in ("regular", "symlink") for boundary in BOUNDARIES}


def cjson(v: Any) -> bytes: return (json.dumps(v, indent=2, sort_keys=True) + "\n").encode()
def readj(p: Path) -> dict[str, Any]:
    v = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v, dict): raise ValueError(p)
    return v
def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def final_matches(s: dict[str, Any], e: dict[str, Any]) -> bool:
    if s.get("type") != e.get("type") or s.get("mode") != e.get("mode"): return False
    if e.get("type") == "regular": return s.get("size") == e.get("size") and s.get("sha256") == e.get("sha256")
    if e.get("type") == "symlink": return s.get("target") == e.get("symlink_target")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--phase4-results", required=True, type=Path); ap.add_argument("--results-dir", required=True, type=Path); ap.add_argument("--output", required=True, type=Path); a = ap.parse_args()
    p4, root, output = a.phase4_results.resolve(), a.results_dir.resolve(), a.output.resolve()
    accepted = readj(root / "accepted-inputs.json"); summary = readj(root / "scenario-summary.json"); clones = readj(root / "clone-separation.json"); seed_install = readj(root / "seed/install.json"); seed_verify = readj(root / "seed/verify.json"); seed_id = readj(root / "seed/identity.json")
    success = {n: readj(root / "success" / n / "scenario.json") for n in SUCCESS}; crash = {n: readj(root / "crash" / n / "scenario.json") for n in CRASH}

    required = {root / "accepted-inputs.json", root / "scenario-summary.json", root / "clone-separation.json", root / "seed/install.json", root / "seed/install-process.json", root / "seed/install.log", root / "seed/verify.json", root / "seed/verify-process.json", root / "seed/verify.log", root / "seed/identity.json"}
    for n in SUCCESS:
        b = root / "success" / n; required.add(b / "scenario.json")
        stages = ("install", "verify") if n == "exact-noop" else ("pre-verify", "install", "post-verify")
        for st in stages: required |= {b / f"{st}.json", b / f"{st}-process.json", b / f"{st}.log"}
    for n in CRASH:
        b = root / "crash" / n; required.add(b / "scenario.json")
        required |= {b / "crash-install-process.json", b / "crash-install.log"}
        for st in ("recover-1", "recover-2", "verify"): required |= {b / f"{st}.json", b / f"{st}-process.json", b / f"{st}.log"}
    missing = sorted(str(p) for p in required if not p.is_file())
    canonical = [p for p in required if p.suffix == ".json"]

    noop = success["exact-noop"]
    repair_names = SUCCESS - {"exact-noop"}
    in_place = {n for n in repair_names if not n.startswith("missing-")}
    missing_success = {n for n in repair_names if n.startswith("missing-")}

    supported_rows = [success[n] for n in in_place]
    missing_rows = [success[n] for n in missing_success]
    precommit = [v for v in crash.values() if not v["expected"]["committed"]]
    committed = [v for v in crash.values() if v["expected"]["committed"]]

    crash_expectations = True
    for name, row in crash.items():
        kind, boundary = name.split("-", 1); rc, state, muts, restored, is_committed = BOUNDARIES[boundary]
        observed = [(m.get("kind"), m.get("status")) for m in row["transactions_before_recovery"][0].get("mutations", [])] if len(row["transactions_before_recovery"]) == 1 else []
        crash_expectations &= row["leaf_kind"] == kind and row["expected"] == {"returncode": rc, "journal_state": state, "mutations": [list(x) for x in muts], "restored_count": restored, "committed": is_committed} and row["crash_run"]["returncode"] == rc and row["crash_run"]["output_exists"] is False and len(row["transactions_before_recovery"]) == 1 and row["transactions_before_recovery"][0].get("state") == state and observed == muts

    checks = {
        "required_outputs_present": not missing,
        "accepted_phase4_file_exact": sha(p4 / "result-index.json") == P4_INDEX,
        "accepted_evidence_exact": accepted.get("pass") is True and accepted.get("observed_result_index_sha256") == P4_INDEX,
        "summary_check_count_39": summary.get("check_count") == 39,
        "summary_pass": summary.get("pass") is True and summary.get("failed_checks") == [],
        "summary_success_names_exact": set(summary.get("success_scenarios", [])) == SUCCESS,
        "summary_crash_names_exact": set(summary.get("crash_scenarios", [])) == CRASH,
        "clone_count_19": clones.get("scenario_count") == 19,
        "clone_names_exact": set(clones.get("scenarios", {})) == {"success/" + n for n in SUCCESS} | {"crash/" + n for n in CRASH},
        "clone_all_inode_separate": clones.get("pass") is True and all(all(v.values()) for v in clones.get("scenarios", {}).values()),
        "seed_install_exact": seed_install.get("pass") is True and seed_install.get("action_counts") == {"create": 714} and seed_install.get("mutation_count") == 715,
        "seed_verify_exact": seed_verify.get("pass") is True and seed_verify.get("artifact_count") == 1 and seed_verify.get("owned_path_count") == 714 and seed_verify.get("bad_paths") == [],
        "seed_portable_exact": seed_id.get("portable", {}).get("fingerprint") == PORTABLE,
        "seed_shape_exact": seed_id.get("portable", {}).get("entry_count") == 714 and seed_id.get("portable", {}).get("type_counts") == {"directory": 57, "regular": 654, "symlink": 3, "special": 0},
        "seed_registry_exact": seed_id.get("registry", {}).get("artifact_count") == 1 and seed_id.get("registry", {}).get("owned_path_count") == 714,
        "seed_transactions_empty": seed_id.get("transactions") == [],
        "success_names_exact": set(success) == SUCCESS,
        "success_all_scenario_pass": all(v.get("pass") is True for v in success.values()),
        "noop_classification_exact": noop.get("classification") == "exact-same-version-noop",
        "noop_operation_exact": noop["operation"]["result"].get("noop") is True and noop["operation"]["result"].get("action_counts") == {"noop": 714} and noop["operation"]["result"].get("mutation_count") == 0,
        "noop_verify_exact": noop["verify"]["result"].get("bad_paths") == [],
        "noop_identity_unchanged": noop.get("before") == noop.get("after"),
        "in_place_names_exact": in_place == {"regular-bytes", "regular-mode", "regular-wrong-type", "symlink-target"},
        "in_place_classification_exact": all(v.get("classification") == "in-place-registered-repair-regression" for v in supported_rows),
        "in_place_preverify_exact": all(v["pre_verify"]["returncode"] == 44 and v["pre_verify"]["result"]["bad_paths"] == [v["candidate"]["path"]] for v in supported_rows),
        "in_place_install_exact": all(v["operation"]["returncode"] == 0 and v["operation"]["result"].get("action_counts") == {"noop": 713, "repair": 1} and v["operation"]["result"].get("mutation_count") == 2 for v in supported_rows),
        "in_place_postverify_exact": all(v["post_verify"]["returncode"] == 0 and v["post_verify"]["result"]["bad_paths"] == [] for v in supported_rows),
        "in_place_final_exact": all(final_matches(v["final_path"], v["candidate"]) for v in supported_rows),
        "in_place_identity_exact": all(v["after"]["portable"]["fingerprint"] == PORTABLE and v["after"]["registry"] == v["before"]["registry"] and v["after"]["transactions"] == [] for v in supported_rows),
        "missing_success_names_exact": missing_success == {"missing-regular", "missing-symlink"},
        "missing_success_classification_exact": all(v.get("classification") == "missing-leaf-repair-supported" for v in missing_rows),
        "missing_success_preverify_exact": all(v["pre_verify"]["returncode"] == 44 and v["pre_verify"]["result"]["bad_paths"] == [v["candidate"]["path"]] for v in missing_rows),
        "missing_success_install_exact": all(v["operation"]["returncode"] == 0 and v["operation"]["result"].get("action_counts") == {"noop": 713, "repair": 1} and v["operation"]["result"].get("mutation_count") == 2 for v in missing_rows),
        "missing_success_postverify_exact": all(v["post_verify"]["returncode"] == 0 and v["post_verify"]["result"]["bad_paths"] == [] for v in missing_rows),
        "missing_success_final_exact": all(final_matches(v["final_path"], v["candidate"]) for v in missing_rows),
        "missing_success_identity_exact": all(v["after"]["portable"]["fingerprint"] == PORTABLE and v["after"]["registry"] == v["before"]["registry"] and v["after"]["transactions"] == [] for v in missing_rows),
        "crash_names_exact": set(crash) == CRASH,
        "crash_expected_metadata_exact": crash_expectations,
        "precommit_count_10": len(precommit) == 10,
        "precommit_recovery_exact": all(v["recover_1"]["result"]["actions"][0]["action"] == "ROLLED_BACK" and v["recover_1"]["result"]["actions"][0]["restored_count"] == v["expected"]["restored_count"] for v in precommit),
        "precommit_original_missing_state": all(v["final_path"]["type"] == "absent" and v["registry_before"] == v["registry_after"] for v in precommit),
        "precommit_verify_exact": all(v["verify"]["returncode"] == 44 and v["verify"]["result"]["bad_paths"] == [v["candidate"]["path"]] for v in precommit),
        "precommit_retained_rolledback": all(len(v["transactions_after_recovery_1"]) == 1 and v["transactions_after_recovery_1"][0]["state"] == "ROLLED_BACK" for v in precommit),
        "precommit_second_recover_noop": all(v["recover_2"]["result"]["actions"][0]["action"] == "NOOP_ROLLED_BACK" and v["transactions_after_recovery_2"] == v["transactions_after_recovery_1"] for v in precommit),
        "committed_count_two": len(committed) == 2,
        "committed_recovery_exact": all(v["recover_1"]["result"]["actions"][0]["action"] == "FINALIZED_COMMIT" for v in committed),
        "committed_final_exact": all(final_matches(v["final_path"], v["candidate"]) and v["registry_before"] == v["registry_after"] for v in committed),
        "committed_verify_and_cleanup": all(v["verify"]["returncode"] == 0 and v["verify"]["result"]["bad_paths"] == [] and v["transactions_after_recovery_1"] == [] and v["transactions_after_recovery_2"] == [] and v["recover_2"]["result"]["transaction_count"] == 0 for v in committed),
        "raw_process_outputs_match_embedded": all(readj(root / "success" / n / "install-process.json") == success[n]["operation"] for n in SUCCESS) and all(readj(root / "crash" / n / "crash-install-process.json") == crash[n]["crash_run"] for n in CRASH),
        "machine_json_canonical": not missing and all(p.read_bytes() == cjson(readj(p)) for p in canonical),
        "claim_boundary_not_product_acceptance": "product acceptance" in summary.get("claim_boundary", {}).get("not_proved", "").lower(),
    }
    if len(checks) != 51: raise RuntimeError(f"unexpected check count {len(checks)}")
    failed = sorted(k for k, v in checks.items() if not v)
    result = {"schema_version": 1, "pass": not failed, "check_count": 51, "checks": checks, "failed_checks": failed, "missing_files": missing, "observed": {"success_scenarios": len(success), "crash_scenarios": len(crash), "portable_fingerprint": seed_id.get("portable", {}).get("fingerprint")}, "claim_boundary": {"proved": "The candidate missing-leaf repair intervention succeeds for regular and symlink leaves and is recovery-safe at six crash boundaries per leaf type.", "not_proved": "Gate 3A product acceptance and downstream installed-runtime regressions remain unproved."}}
    output.parent.mkdir(parents=True, exist_ok=True); output.write_bytes(cjson(result)); print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["pass"] else 82


if __name__ == "__main__": raise SystemExit(main())

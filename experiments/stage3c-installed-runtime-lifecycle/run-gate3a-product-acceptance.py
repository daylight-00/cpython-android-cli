#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from gate3a_acceptance_support import (
    EXPECTED_PHASE4_INDEX,
    EXPECTED_PHASE4I_INDEX,
    EXPECTED_PORTABLE,
    clone_seed,
    identity,
    invoke_engine,
    manifest_record,
    read_json,
    repair_cycle,
    sha256_file,
    write_json,
)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase4-results", required=True, type=Path)
    parser.add_argument("--phase4i-results", required=True, type=Path)
    parser.add_argument("--contract-results", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--local-script-runner", required=True, type=Path)
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--strict-fingerprint", required=True, type=Path)
    parser.add_argument("--portable-fingerprint", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    phase4 = args.phase4_results.resolve()
    phase4i = args.phase4i_results.resolve()
    contract = args.contract_results.resolve()
    manifest_path = args.manifest.resolve()
    local_runner = args.local_script_runner.resolve()
    engine = args.engine.resolve()
    strict_script = args.strict_fingerprint.resolve()
    portable_script = args.portable_fingerprint.resolve()
    work = args.work_root.resolve()
    output = args.output_dir.resolve()

    shutil.rmtree(work, ignore_errors=True)
    shutil.rmtree(output, ignore_errors=True)
    work.mkdir(parents=True)
    output.mkdir(parents=True)

    accepted = {
        "schema_version": 1,
        "phase4_expected": EXPECTED_PHASE4_INDEX,
        "phase4_observed": sha256_file(phase4 / "result-index.json"),
        "phase4i_expected": EXPECTED_PHASE4I_INDEX,
        "phase4i_observed": sha256_file(phase4i / "result-index.json"),
    }
    accepted["pass"] = (
        accepted["phase4_observed"] == EXPECTED_PHASE4_INDEX
        and accepted["phase4i_observed"] == EXPECTED_PHASE4I_INDEX
    )
    write_json(output / "accepted-inputs.json", accepted)

    manifest = read_json(manifest_path)
    owned = [entry for entry in manifest["entries"] if entry["entry_class"] == "OWNED_PAYLOAD"]
    regular_candidates = sorted(
        (
            entry
            for entry in owned
            if entry["type"] == "regular" and entry.get("size", 0) > 0 and entry.get("elf") is not True
        ),
        key=lambda entry: entry["payload_path"],
    )
    symlink_candidates = sorted(
        (entry for entry in owned if entry["type"] == "symlink"),
        key=lambda entry: entry["payload_path"],
    )
    if not regular_candidates or not symlink_candidates:
        raise RuntimeError("missing deterministic repair candidates")
    candidates = {"regular": regular_candidates[0], "symlink": symlink_candidates[0]}

    seed = work / "seed"
    seed_output = output / "seed"
    seed_install = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract,
        root=seed,
        operation="install",
        artifact="runtime-base",
        output=seed_output / "install.json",
    )
    seed_verify = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract,
        root=seed,
        operation="verify",
        output=seed_output / "verify.json",
    )
    seed_identity = identity(
        root=seed,
        strict_script=strict_script,
        portable_script=portable_script,
        output_dir=seed_output,
        label="identity",
    )
    write_json(seed_output / "summary.json", {
        "schema_version": 1,
        "install": seed_install,
        "verify": seed_verify,
        "identity": seed_identity,
    })

    repair_specs = {
        "regular-bytes": candidates["regular"],
        "regular-mode": candidates["regular"],
        "regular-wrong-type": candidates["regular"],
        "symlink-target": candidates["symlink"],
        "missing-regular": candidates["regular"],
        "missing-symlink": candidates["symlink"],
    }

    clone_rows: dict[str, dict[str, Any]] = {}
    isolated_results: dict[str, dict[str, Any]] = {}

    noop_root = work / "isolated" / "exact-noop"
    clone_rows["exact-noop"] = clone_seed(seed, noop_root, candidates["regular"]["payload_path"])
    noop_before = identity(
        root=noop_root,
        strict_script=strict_script,
        portable_script=portable_script,
        output_dir=output / "isolated/exact-noop",
        label="before",
    )
    noop_install = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract,
        root=noop_root,
        operation="install",
        artifact="runtime-base",
        output=output / "isolated/exact-noop/install.json",
    )
    noop_verify = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract,
        root=noop_root,
        operation="verify",
        output=output / "isolated/exact-noop/verify.json",
    )
    noop_after = identity(
        root=noop_root,
        strict_script=strict_script,
        portable_script=portable_script,
        output_dir=output / "isolated/exact-noop",
        label="after",
    )
    noop_result = {
        "schema_version": 1,
        "scenario": "exact-noop",
        "before": noop_before,
        "install": noop_install,
        "verify": noop_verify,
        "after": noop_after,
        "pass": (
            noop_install["returncode"] == 0
            and noop_install["result"].get("noop") is True
            and noop_install["result"].get("action_counts") == {"noop": 714}
            and noop_install["result"].get("mutation_count") == 0
            and noop_verify["returncode"] == 0
            and noop_before == noop_after
        ),
    }
    write_json(output / "isolated/exact-noop/scenario.json", noop_result)
    isolated_results["exact-noop"] = noop_result

    for scenario, entry in repair_specs.items():
        root = work / "isolated" / scenario
        clone_rows[scenario] = clone_seed(seed, root, candidates["regular"]["payload_path"])
        isolated_results[scenario] = repair_cycle(
            scenario=scenario,
            root=root,
            entry=entry,
            owned_entries=owned,
            local_runner=local_runner,
            engine=engine,
            contract_results=contract,
            strict_script=strict_script,
            portable_script=portable_script,
            output_dir=output / "isolated" / scenario,
        )

    sequential_root = work / "sequential"
    sequential_output = output / "sequential"
    sequential_install = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract,
        root=sequential_root,
        operation="install",
        artifact="runtime-base",
        output=sequential_output / "install.json",
    )
    sequential_noop = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract,
        root=sequential_root,
        operation="install",
        artifact="runtime-base",
        output=sequential_output / "noop.json",
    )
    sequential_steps: dict[str, dict[str, Any]] = {}
    for index, scenario in enumerate(repair_specs, start=1):
        sequential_steps[scenario] = repair_cycle(
            scenario=scenario,
            root=sequential_root,
            entry=repair_specs[scenario],
            owned_entries=owned,
            local_runner=local_runner,
            engine=engine,
            contract_results=contract,
            strict_script=strict_script,
            portable_script=portable_script,
            output_dir=sequential_output / f"{index:02d}-{scenario}",
        )
    sequential_verify = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract,
        root=sequential_root,
        operation="verify",
        output=sequential_output / "final-verify.json",
    )
    sequential_identity = identity(
        root=sequential_root,
        strict_script=strict_script,
        portable_script=portable_script,
        output_dir=sequential_output,
        label="final",
    )
    sequential_summary = {
        "schema_version": 1,
        "root": str(sequential_root),
        "install": sequential_install,
        "noop": sequential_noop,
        "steps": {name: {"pass": row["pass"], "candidate": row["candidate"]} for name, row in sequential_steps.items()},
        "final_verify": sequential_verify,
        "final_identity": sequential_identity,
        "pass": (
            sequential_install["returncode"] == 0
            and sequential_install["result"].get("action_counts") == {"create": 714}
            and sequential_install["result"].get("mutation_count") == 715
            and sequential_noop["returncode"] == 0
            and sequential_noop["result"].get("action_counts") == {"noop": 714}
            and sequential_noop["result"].get("mutation_count") == 0
            and all(row["pass"] for row in sequential_steps.values())
            and sequential_verify["returncode"] == 0
            and sequential_verify["result"].get("bad_paths") == []
            and sequential_identity["strict"]["result"].get("pass") is True
            and sequential_identity["portable"]["result"].get("fingerprint") == EXPECTED_PORTABLE
            and sequential_identity["transactions"] == []
        ),
    }
    write_json(sequential_output / "summary.json", sequential_summary)

    sequential_probe = sequential_root / "prefix" / candidates["regular"]["payload_path"]
    clone_summary = {
        "schema_version": 1,
        "pass": all(all(row.values()) for row in clone_rows.values())
        and seed.stat().st_ino != sequential_root.stat().st_ino
        and (seed / ".cpython-android-cli/registry.json").stat().st_ino
        != (sequential_root / ".cpython-android-cli/registry.json").stat().st_ino
        and (seed / "prefix" / candidates["regular"]["payload_path"]).stat().st_ino
        != sequential_probe.stat().st_ino,
        "isolated": clone_rows,
        "sequential": {
            "root_inode_separate": seed.stat().st_ino != sequential_root.stat().st_ino,
            "registry_inode_separate": (seed / ".cpython-android-cli/registry.json").stat().st_ino
            != (sequential_root / ".cpython-android-cli/registry.json").stat().st_ino,
            "probe_inode_separate": (seed / "prefix" / candidates["regular"]["payload_path"]).stat().st_ino
            != sequential_probe.stat().st_ino,
        },
    }
    write_json(output / "clone-separation.json", clone_summary)

    checks = {
        "accepted_inputs_exact": accepted["pass"],
        "seed_install_exact": seed_install["returncode"] == 0
        and seed_install["result"].get("action_counts") == {"create": 714}
        and seed_install["result"].get("mutation_count") == 715,
        "seed_verify_exact": seed_verify["returncode"] == 0
        and seed_verify["result"].get("artifact_count") == 1
        and seed_verify["result"].get("owned_path_count") == 714
        and seed_verify["result"].get("bad_paths") == [],
        "seed_strict_shape_safe": seed_identity["strict"]["result"].get("pass") is True,
        "seed_portable_exact": seed_identity["portable"]["result"].get("fingerprint") == EXPECTED_PORTABLE,
        "seed_transactions_empty": seed_identity["transactions"] == [],
        "clone_separation": clone_summary["pass"],
        "isolated_names_exact": set(isolated_results) == {"exact-noop", *repair_specs.keys()},
        "isolated_all_pass": all(row["pass"] for row in isolated_results.values()),
        "isolated_noop_pass": isolated_results["exact-noop"]["pass"],
        "isolated_repairs_six": sum(row["pass"] for name, row in isolated_results.items() if name != "exact-noop") == 6,
        "isolated_existing_repairs_four": sum(
            isolated_results[name]["pass"]
            for name in ("regular-bytes", "regular-mode", "regular-wrong-type", "symlink-target")
        ) == 4,
        "isolated_missing_repairs_two": isolated_results["missing-regular"]["pass"]
        and isolated_results["missing-symlink"]["pass"],
        "isolated_registry_unchanged": all(
            row["after"]["registry"] == row["before"]["registry"]
            for name, row in isolated_results.items()
            if name != "exact-noop"
        ),
        "isolated_unaffected_exact": all(
            row["unaffected_before"] == row["unaffected_after"]
            for name, row in isolated_results.items()
            if name != "exact-noop"
        ),
        "isolated_transactions_empty": all(
            row["after"]["transactions"] == [] for row in isolated_results.values()
        ),
        "sequential_install_exact": sequential_install["returncode"] == 0
        and sequential_install["result"].get("action_counts") == {"create": 714}
        and sequential_install["result"].get("mutation_count") == 715,
        "sequential_noop_exact": sequential_noop["returncode"] == 0
        and sequential_noop["result"].get("action_counts") == {"noop": 714}
        and sequential_noop["result"].get("mutation_count") == 0,
        "sequential_steps_six": len(sequential_steps) == 6,
        "sequential_all_repairs_pass": all(row["pass"] for row in sequential_steps.values()),
        "sequential_registry_unchanged_each": all(
            row["after"]["registry"] == row["before"]["registry"] for row in sequential_steps.values()
        ),
        "sequential_unaffected_exact_each": all(
            row["unaffected_before"] == row["unaffected_after"] for row in sequential_steps.values()
        ),
        "sequential_final_verify": sequential_verify["returncode"] == 0
        and sequential_verify["result"].get("bad_paths") == [],
        "sequential_final_strict_shape_safe": sequential_identity["strict"]["result"].get("pass") is True,
        "sequential_final_portable": sequential_identity["portable"]["result"].get("fingerprint") == EXPECTED_PORTABLE,
        "sequential_transactions_empty": sequential_identity["transactions"] == [],
        "sequential_summary_pass": sequential_summary["pass"],
        "candidate_regular_exact": manifest_record(candidates["regular"])["path"] == "lib/python3.14/LICENSE.txt",
        "candidate_symlink_exact": manifest_record(candidates["symlink"])["path"] == "bin/python",
    }
    if len(checks) != 29:
        raise RuntimeError(f"unexpected scenario check count: {len(checks)}")
    failed = sorted(name for name, passed in checks.items() if not passed)
    summary = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "accepted_inputs": accepted,
        "candidates": {name: manifest_record(entry) for name, entry in candidates.items()},
        "isolated_scenarios": sorted(isolated_results),
        "sequential_order": list(repair_specs),
        "sequential_root": str(sequential_root),
        "claim_boundary": {
            "proved": "The corrected engine passed exact reinstall and all six registered repair classes in isolated and sequential roots.",
            "not_proved": "Full runtime behavior is verified by the outer Gate 3A workflow, not by this scenario runner alone.",
        },
    }
    write_json(output / "scenario-summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("\nSTAGE3C_PHASE5_GATE3A_REPAIR_SCENARIOS=" + ("PASS" if summary["pass"] else "FAIL"))
    return 91 if args.require_pass and not summary["pass"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

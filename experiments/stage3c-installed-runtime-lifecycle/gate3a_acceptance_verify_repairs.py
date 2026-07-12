#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from gate3a_acceptance_verify_support import PHASE4_INDEX, PHASE4I_INDEX, PORTABLE, REPAIRS, final_matches, sha256_file


def repair_checks(ctx: Any) -> dict[str, bool]:
    isolated = ctx.isolated
    noop = ctx.noop
    repair_rows = ctx.repair_rows
    sequential = ctx.sequential
    sequential_rows = ctx.sequential_rows
    return {
        "required_outputs_present": not ctx.missing_files,
        "phase4_result_index_exact": sha256_file(ctx.phase4 / "result-index.json") == PHASE4_INDEX,
        "phase4i_result_index_exact": sha256_file(ctx.phase4i / "result-index.json") == PHASE4I_INDEX,
        "accepted_inputs_exact": ctx.accepted.get("pass") is True
        and ctx.accepted.get("phase4_observed") == PHASE4_INDEX
        and ctx.accepted.get("phase4i_observed") == PHASE4I_INDEX,
        "scenario_summary_29": ctx.scenario_summary.get("pass") is True
        and ctx.scenario_summary.get("check_count") == 29
        and ctx.scenario_summary.get("failed_checks") == [],
        "clone_separation_pass": ctx.clones.get("pass") is True,
        "isolated_names_exact": set(isolated) == {"exact-noop", *REPAIRS},
        "isolated_all_pass": all(row.get("pass") is True for row in isolated.values()),
        "isolated_noop_exact": noop["install"]["returncode"] == 0
        and noop["install"]["result"].get("action_counts") == {"noop": 714}
        and noop["install"]["result"].get("mutation_count") == 0
        and noop["before"] == noop["after"],
        "isolated_repairs_six": len(repair_rows) == 6,
        "isolated_existing_repairs_four": all(isolated[name].get("pass") is True for name in REPAIRS[:4]),
        "isolated_missing_repairs_two": isolated["missing-regular"].get("pass") is True
        and isolated["missing-symlink"].get("pass") is True,
        "isolated_preverify_exact": all(
            row["pre_verify"]["returncode"] == 44
            and row["pre_verify"]["result"].get("bad_paths") == [row["candidate"]["path"]]
            for row in repair_rows
        ),
        "isolated_install_exact": all(
            row["install"]["returncode"] == 0
            and row["install"]["result"].get("action_counts") == {"noop": 713, "repair": 1}
            and row["install"]["result"].get("mutation_count") == 2
            for row in repair_rows
        ),
        "isolated_postverify_exact": all(
            row["post_verify"]["returncode"] == 0
            and row["post_verify"]["result"].get("bad_paths") == []
            for row in repair_rows
        ),
        "isolated_final_candidates_exact": all(final_matches(row) for row in repair_rows),
        "isolated_registry_unchanged": all(row["before"]["registry"] == row["after"]["registry"] for row in repair_rows),
        "isolated_unaffected_exact": all(row["unaffected_before"] == row["unaffected_after"] for row in repair_rows),
        "isolated_strict_shape_safe": all(row["after"]["strict"]["result"].get("pass") is True for row in repair_rows),
        "isolated_portable_exact": all(row["after"]["portable"]["result"].get("fingerprint") == PORTABLE for row in repair_rows),
        "isolated_transactions_empty": all(row["after"]["transactions"] == [] for row in isolated.values()),
        "sequential_summary_pass": sequential.get("pass") is True,
        "sequential_install_exact": sequential["install"]["returncode"] == 0
        and sequential["install"]["result"].get("action_counts") == {"create": 714}
        and sequential["install"]["result"].get("mutation_count") == 715,
        "sequential_noop_exact": sequential["noop"]["returncode"] == 0
        and sequential["noop"]["result"].get("action_counts") == {"noop": 714}
        and sequential["noop"]["result"].get("mutation_count") == 0,
        "sequential_order_exact": ctx.scenario_summary.get("sequential_order") == REPAIRS,
        "sequential_steps_six": len(sequential_rows) == 6,
        "sequential_all_pass": all(row.get("pass") is True for row in sequential_rows),
        "sequential_preverify_exact": all(
            row["pre_verify"]["returncode"] == 44
            and row["pre_verify"]["result"].get("bad_paths") == [row["candidate"]["path"]]
            for row in sequential_rows
        ),
        "sequential_install_repairs_exact": all(
            row["install"]["returncode"] == 0
            and row["install"]["result"].get("action_counts") == {"noop": 713, "repair": 1}
            and row["install"]["result"].get("mutation_count") == 2
            for row in sequential_rows
        ),
        "sequential_postverify_exact": all(
            row["post_verify"]["returncode"] == 0
            and row["post_verify"]["result"].get("bad_paths") == []
            for row in sequential_rows
        ),
        "sequential_final_candidates_exact": all(final_matches(row) for row in sequential_rows),
        "sequential_registry_unchanged_each": all(row["before"]["registry"] == row["after"]["registry"] for row in sequential_rows),
        "sequential_unaffected_exact_each": all(row["unaffected_before"] == row["unaffected_after"] for row in sequential_rows),
        "sequential_final_verify": sequential["final_verify"]["returncode"] == 0
        and sequential["final_verify"]["result"].get("bad_paths") == [],
        "sequential_final_strict_shape_safe": sequential["final_identity"]["strict"]["result"].get("pass") is True,
        "sequential_final_portable": sequential["final_identity"]["portable"]["result"].get("fingerprint") == PORTABLE,
        "sequential_transactions_empty": sequential["final_identity"]["transactions"] == [],
        "raw_process_outputs_match": ctx.raw_embedded_match,
    }

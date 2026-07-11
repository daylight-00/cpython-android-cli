from __future__ import annotations

from pathlib import Path

from recovery_scenario_context import ScenarioContext
from recovery_scenario_support import (
    clone_installation,
    fingerprint,
    first_regular,
    newest_journal,
    replace_with_bytes,
)


def run_applying_and_registry_recovery(
    ctx: ScenarioContext,
    runtime_seed: Path,
    runtime_development_seed: Path,
) -> dict[str, Path | str]:
    work = ctx.work

    applying_install = work / "applying-install"
    clone_installation(runtime_seed, applying_install)
    before = fingerprint(applying_install)
    crashed, process = ctx.run_engine(
        "applying-install-crash",
        applying_install,
        "install",
        artifact="development-addon",
        extra=["--crash-after-mutations", "5"],
        expect_rc=91,
    )
    _, journal = newest_journal(applying_install)
    ctx.save("applying-install-journal-before-recovery", journal)
    recovery, _ = ctx.run_engine("applying-install-recovery", applying_install, "recover")
    _, recovered_journal = newest_journal(applying_install)
    ctx.save("applying-install-journal-after-recovery", recovered_journal)
    verified, _ = ctx.run_engine("applying-install-verify", applying_install, "verify")
    ctx.check(
        "applying_install_crash_exit_91",
        process.returncode == 91 and crashed.get("output_absent") is True,
    )
    ctx.check(
        "applying_install_five_applied",
        journal.get("state") == "APPLYING"
        and len(journal.get("mutations", [])) == 5
        and all(item.get("status") == "APPLIED" for item in journal["mutations"]),
    )
    ctx.check(
        "applying_install_recovery_restored_5",
        recovery.get("actions", [{}])[0].get("restored_count") == 5,
    )
    ctx.check(
        "applying_install_recovered_state",
        recovered_journal.get("state") == "ROLLED_BACK",
    )
    ctx.check("applying_install_fingerprint_restored", fingerprint(applying_install) == before)
    ctx.check(
        "applying_install_registry_runtime_only",
        verified.get("pass") is True and verified.get("owned_path_count") == 714,
    )

    applying_uninstall = work / "applying-uninstall"
    clone_installation(runtime_development_seed, applying_uninstall)
    before = fingerprint(applying_uninstall)
    crashed, process = ctx.run_engine(
        "applying-uninstall-crash",
        applying_uninstall,
        "uninstall",
        artifact="development-addon",
        extra=["--crash-after-mutations", "5"],
        expect_rc=91,
    )
    _, journal = newest_journal(applying_uninstall)
    ctx.save("applying-uninstall-journal-before-recovery", journal)
    recovery, _ = ctx.run_engine("applying-uninstall-recovery", applying_uninstall, "recover")
    _, recovered_journal = newest_journal(applying_uninstall)
    ctx.save("applying-uninstall-journal-after-recovery", recovered_journal)
    verified, _ = ctx.run_engine("applying-uninstall-verify", applying_uninstall, "verify")
    ctx.check(
        "applying_uninstall_crash_exit_91",
        process.returncode == 91 and crashed.get("output_absent") is True,
    )
    ctx.check(
        "applying_uninstall_five_applied",
        journal.get("state") == "APPLYING"
        and len(journal.get("mutations", [])) == 5
        and all(item.get("status") == "APPLIED" for item in journal["mutations"]),
    )
    ctx.check(
        "applying_uninstall_recovery_restored_5",
        recovery.get("actions", [{}])[0].get("restored_count") == 5,
    )
    ctx.check(
        "applying_uninstall_recovered_state",
        recovered_journal.get("state") == "ROLLED_BACK",
    )
    ctx.check("applying_uninstall_fingerprint_restored", fingerprint(applying_uninstall) == before)
    ctx.check(
        "applying_uninstall_registry_1168",
        verified.get("pass") is True and verified.get("owned_path_count") == 1168,
    )

    registry_crash = work / "registry-crash"
    clone_installation(runtime_development_seed, registry_crash)
    regular = first_regular(registry_crash, "development-addon")
    leaf = registry_crash / "prefix" / regular
    replace_with_bytes(leaf, b"registry-crash-corruption\n")
    before = fingerprint(registry_crash)
    crashed, process = ctx.run_engine(
        "registry-crash-repair",
        registry_crash,
        "install",
        artifact="development-addon",
        extra=["--crash-after-mutations", "2"],
        expect_rc=91,
    )
    _, journal = newest_journal(registry_crash)
    ctx.save("registry-crash-journal-before-recovery", journal)
    recovery, _ = ctx.run_engine("registry-crash-recovery", registry_crash, "recover")
    _, recovered_journal = newest_journal(registry_crash)
    ctx.save("registry-crash-journal-after-recovery", recovered_journal)
    restored_corrupt, _ = ctx.run_engine(
        "registry-crash-verify-restored-corruption",
        registry_crash,
        "verify",
        expect_rc=44,
    )
    restored_corrupt_fingerprint = fingerprint(registry_crash)
    repaired, _ = ctx.run_engine(
        "registry-crash-normal-repair",
        registry_crash,
        "install",
        artifact="development-addon",
    )
    repaired_verify, _ = ctx.run_engine(
        "registry-crash-repaired-verify",
        registry_crash,
        "verify",
    )
    ctx.check(
        "registry_crash_exit_91",
        process.returncode == 91 and crashed.get("output_absent") is True,
    )
    ctx.check(
        "registry_crash_two_applied_including_registry",
        journal.get("state") == "APPLYING"
        and [item.get("kind") for item in journal.get("mutations", [])]
        == ["replaced", "registry"]
        and all(item.get("status") == "APPLIED" for item in journal["mutations"]),
    )
    ctx.check(
        "registry_crash_recovery_restored_two",
        recovery.get("actions", [{}])[0].get("restored_count") == 2,
    )
    ctx.check(
        "registry_crash_recovered_state",
        recovered_journal.get("state") == "ROLLED_BACK",
    )
    ctx.check(
        "registry_crash_fingerprint_restored_corrupt",
        restored_corrupt_fingerprint == before
        and restored_corrupt.get("bad_paths") == [regular],
    )
    ctx.check(
        "registry_crash_normal_repair_exact",
        repaired.get("pass") is True
        and repaired.get("action_counts") == {"noop": 453, "repair": 1},
    )
    ctx.check(
        "registry_crash_repaired_verify",
        repaired_verify.get("pass") is True
        and repaired_verify.get("owned_path_count") == 1168,
    )

    return {
        "applying_install": applying_install,
        "applying_uninstall": applying_uninstall,
        "registry_crash": registry_crash,
        "regular": regular,
    }

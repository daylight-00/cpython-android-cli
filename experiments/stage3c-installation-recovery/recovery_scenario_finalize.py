from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from recovery_scenario_context import ScenarioContext
from recovery_scenario_support import (
    canonical_json_bytes,
    fingerprint,
    first_regular,
    newest_journal,
    read_json,
    replace_with_bytes,
    write_registry_snapshot,
)


def run_commit_lock_and_finalize(
    ctx: ScenarioContext,
    prepared: Path,
    intent: Path,
    applying_install: Path,
    applying_uninstall: Path,
    registry_crash: Path,
    regular: str,
) -> dict[str, object]:
    work = ctx.work
    output = ctx.output

    committed = registry_crash
    regular = first_regular(committed, "development-addon")
    leaf = committed / "prefix" / regular
    replace_with_bytes(leaf, b"committed-crash-corruption\n")
    crashed, process = ctx.run_engine(
        "committed-repair-crash",
        committed,
        "install",
        artifact="development-addon",
        extra=["--crash-after-commit"],
        expect_rc=92,
    )
    transaction, journal = newest_journal(committed)
    ctx.save("committed-journal-before-recovery", journal)
    before_recovery = fingerprint(committed)
    recovery, _ = ctx.run_engine("committed-recovery", committed, "recover")
    verified, _ = ctx.run_engine("committed-verify", committed, "verify")
    ctx.check(
        "committed_crash_exit_92",
        process.returncode == 92 and crashed.get("output_absent") is True,
    )
    ctx.check(
        "committed_journal_state",
        journal.get("state") == "COMMITTED"
        and [item.get("kind") for item in journal.get("mutations", [])]
        == ["replaced", "registry"],
    )
    ctx.check(
        "committed_recovery_finalizes",
        any(item.get("action") == "FINALIZED_COMMIT" for item in recovery.get("actions", [])),
    )
    ctx.check("committed_transaction_removed", not transaction.exists())
    ctx.check(
        "committed_fingerprint_unchanged_by_recovery",
        fingerprint(committed) == before_recovery,
    )
    ctx.check(
        "committed_repaired_state_valid",
        verified.get("pass") is True and verified.get("owned_path_count") == 1168,
    )

    lock_root = applying_install
    before = fingerprint(lock_root)
    ready = work / "lock-ready.txt"
    holder_command = [
        sys.executable,
        str(ctx.engine),
        "--installation-root",
        str(lock_root),
        "--operation",
        "hold-lock",
        "--hold-seconds",
        "1.5",
        "--ready-file",
        str(ready),
    ]
    holder = subprocess.Popen(
        holder_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 5
    while not ready.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    contender, process = ctx.run_engine(
        "lock-contender",
        lock_root,
        "install",
        artifact="development-addon",
        extra=["--nonblocking-lock"],
        expect_rc=44,
    )
    holder_stdout, holder_stderr = holder.communicate(timeout=5)
    ctx.save(
        "lock-holder",
        {
            "pass": holder.returncode == 0,
            "returncode": holder.returncode,
            "ready_observed": ready.exists(),
            "stdout": holder_stdout,
            "stderr": holder_stderr,
        },
    )
    after_contention = fingerprint(lock_root)
    post_release, _ = ctx.run_engine(
        "lock-post-release-install",
        lock_root,
        "install",
        artifact="development-addon",
    )
    post_verify, _ = ctx.run_engine("lock-post-release-verify", lock_root, "verify")
    ctx.check("lock_holder_ready", ready.exists() and holder.returncode == 0)
    ctx.check(
        "lock_contender_rejected",
        process.returncode == 44
        and contender.get("pass") is False
        and "installation lock busy" in contender.get("error", ""),
    )
    ctx.check("lock_contention_no_mutation", before == after_contention)
    ctx.check(
        "lock_post_release_install_pass",
        post_release.get("pass") is True
        and post_release.get("action_counts") == {"create": 454},
    )
    ctx.check(
        "lock_post_release_registry_1168",
        post_verify.get("pass") is True and post_verify.get("owned_path_count") == 1168,
    )

    second_recovery, _ = ctx.run_engine(
        "idempotent-second-recovery",
        applying_install,
        "recover",
    )
    ctx.check(
        "rolled_back_recovery_idempotent",
        second_recovery.get("pass") is True
        and second_recovery.get("actions", [{}])[0].get("action") == "NOOP_ROLLED_BACK",
    )

    write_registry_snapshot(output, "prepared-final", prepared)
    write_registry_snapshot(output, "intent-final", intent)
    write_registry_snapshot(output, "applying-install-final", applying_install)
    write_registry_snapshot(output, "applying-uninstall-final", applying_uninstall)
    write_registry_snapshot(output, "registry-crash-final", registry_crash)

    logs = sorted(path.name for path in output.glob("[0-9][0-9]-*.json"))
    ctx.check("scenario_log_count_exact", len(logs) == ctx.sequence)
    ctx.check(
        "scenario_logs_canonical_json",
        all(
            path.read_bytes() == canonical_json_bytes(read_json(path))
            for path in output.glob("[0-9][0-9]-*.json")
        ),
    )
    ctx.check(
        "work_root_set_exact",
        {path.name for path in work.iterdir()}
        == {
            "runtime-seed",
            "runtime-development-seed",
            "prepared",
            "intent",
            "applying-install",
            "applying-uninstall",
            "registry-crash",
            "lock-ready.txt",
        },
    )

    return {
        "committed": committed,
        "lock_root": lock_root,
        "logs": logs,
        "regular": regular,
    }

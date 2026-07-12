#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_PHASE4_INDEX = "878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce"
EXPECTED_PHASE4I_INDEX = "7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6"
EXPECTED_PORTABLE = "f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978"
EXPECTED_STRICT = "9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796"


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(cjson(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def actual_kind(path: Path) -> str:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return "absent"
    if stat.S_ISLNK(observed.st_mode):
        return "symlink"
    if stat.S_ISDIR(observed.st_mode):
        return "directory"
    if stat.S_ISREG(observed.st_mode):
        return "regular"
    return "special"


def snapshot(path: Path) -> dict[str, Any]:
    kind = actual_kind(path)
    result: dict[str, Any] = {"path": str(path), "type": kind}
    if kind == "absent":
        return result
    observed = path.lstat()
    result["mode"] = f"{stat.S_IMODE(observed.st_mode):04o}"
    if kind == "regular":
        result["size"] = observed.st_size
        result["sha256"] = sha256_file(path)
    elif kind == "symlink":
        result["target"] = os.readlink(path)
    return result


def manifest_record(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": entry["payload_path"],
        "type": entry["type"],
        "mode": entry["mode"],
        "size": entry.get("size"),
        "sha256": entry.get("sha256"),
        "symlink_target": entry.get("symlink_target"),
    }


def snapshot_matches(snapshot_value: dict[str, Any], record: dict[str, Any]) -> bool:
    if snapshot_value.get("type") != record.get("type"):
        return False
    if snapshot_value.get("mode") != record.get("mode"):
        return False
    if record.get("type") == "regular":
        return (
            snapshot_value.get("size") == record.get("size")
            and snapshot_value.get("sha256") == record.get("sha256")
        )
    if record.get("type") == "symlink":
        return snapshot_value.get("target") == record.get("symlink_target")
    return True


def registry_identity(root: Path) -> dict[str, Any]:
    path = root / ".cpython-android-cli/registry.json"
    data = path.read_bytes()
    value = json.loads(data)
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "artifact_count": len(value.get("artifacts", [])),
        "owned_path_count": len(value.get("owned_paths", [])),
    }


def transaction_inventory(root: Path) -> list[dict[str, Any]]:
    transactions = root / ".cpython-android-cli/transactions"
    if not transactions.is_dir():
        return []
    output: list[dict[str, Any]] = []
    for directory in sorted(path for path in transactions.iterdir() if path.is_dir()):
        journal_path = directory / "journal.json"
        row: dict[str, Any] = {"name": directory.name, "journal_exists": journal_path.is_file()}
        if journal_path.is_file():
            journal = read_json(journal_path)
            row.update(
                state=journal.get("state"),
                operation=journal.get("operation"),
                artifact=journal.get("artifact"),
                mutations=journal.get("mutations", []),
            )
        output.append(row)
    return output


def owned_digest(prefix: Path, entries: list[dict[str, Any]], *, exclude: str | None = None) -> str:
    records: list[dict[str, Any]] = []
    for entry in sorted(entries, key=lambda item: item["payload_path"]):
        relative = entry["payload_path"]
        if relative == exclude:
            continue
        observed = snapshot(prefix / relative)
        record = {"relative": relative, **{key: value for key, value in observed.items() if key != "path"}}
        records.append(record)
    return hashlib.sha256(cjson(records)).hexdigest()


def invoke_engine(
    *,
    local_runner: Path,
    engine: Path,
    contract_results: Path,
    root: Path,
    operation: str,
    output: Path,
    artifact: str | None = None,
) -> dict[str, Any]:
    command = [
        sys.executable,
        "-I",
        "-B",
        "-S",
        str(local_runner),
        str(engine),
        "--installation-root",
        str(root),
        "--operation",
        operation,
        "--output",
        str(output),
    ]
    if operation == "install":
        command.extend(("--contract-results", str(contract_results)))
    if artifact is not None:
        command.extend(("--artifact", artifact))
    completed = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    log_path = output.with_suffix(".log")
    log_path.write_text(completed.stdout, encoding="utf-8")
    result = read_json(output)
    process = {
        "returncode": completed.returncode,
        "result": result,
        "log": log_path.name,
    }
    write_json(output.with_name(output.stem + "-process.json"), process)
    return process


def invoke_fingerprint(
    *,
    script: Path,
    prefix: Path,
    output: Path,
    portable: bool,
) -> dict[str, Any]:
    command = [sys.executable, "-I", "-B", "-S", str(script)]
    if portable:
        command.extend(("--installed-prefix", str(prefix), "--output", str(output)))
    else:
        command.extend(("--runtime-prefix", str(prefix), "--output", str(output), "--expected-entry-count", "714"))
    completed = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    output.with_suffix(".log").write_text(completed.stdout, encoding="utf-8")
    result = read_json(output)
    return {"returncode": completed.returncode, "result": result}


def identity(
    *,
    root: Path,
    strict_script: Path,
    portable_script: Path,
    output_dir: Path,
    label: str,
) -> dict[str, Any]:
    prefix = root / "prefix"
    strict = invoke_fingerprint(
        script=strict_script,
        prefix=prefix,
        output=output_dir / f"{label}-strict.json",
        portable=False,
    )
    portable = invoke_fingerprint(
        script=portable_script,
        prefix=prefix,
        output=output_dir / f"{label}-portable.json",
        portable=True,
    )
    return {
        "strict": strict,
        "portable": portable,
        "registry": registry_identity(root),
        "transactions": transaction_inventory(root),
    }


def clone_seed(seed: Path, destination: Path, probe_relative: str) -> dict[str, Any]:
    shutil.copytree(seed, destination, symlinks=True, copy_function=shutil.copy2)
    seed_registry = seed / ".cpython-android-cli/registry.json"
    clone_registry = destination / ".cpython-android-cli/registry.json"
    seed_probe = seed / "prefix" / probe_relative
    clone_probe = destination / "prefix" / probe_relative
    return {
        "root_inode_separate": seed.stat().st_ino != destination.stat().st_ino,
        "registry_inode_separate": seed_registry.stat().st_ino != clone_registry.stat().st_ino,
        "probe_inode_separate": seed_probe.stat().st_ino != clone_probe.stat().st_ino,
    }


def mutate(path: Path, scenario: str, desired_mode: str) -> dict[str, Any]:
    before = snapshot(path)
    if scenario == "regular-bytes":
        path.write_bytes(b"stage3c-gate3a-product-acceptance-corruption\n")
        os.chmod(path, int(desired_mode, 8))
    elif scenario == "regular-mode":
        os.chmod(path, 0o644 if int(desired_mode, 8) != 0o644 else 0o600)
    elif scenario == "regular-wrong-type":
        path.unlink()
        path.mkdir(mode=0o755)
    elif scenario == "symlink-target":
        path.unlink()
        os.symlink("stage3c-gate3a-invalid-target", path)
    elif scenario in {"missing-regular", "missing-symlink"}:
        path.unlink()
    else:
        raise ValueError(scenario)
    return {"scenario": scenario, "before": before, "after": snapshot(path)}


def repair_cycle(
    *,
    scenario: str,
    root: Path,
    entry: dict[str, Any],
    owned_entries: list[dict[str, Any]],
    local_runner: Path,
    engine: Path,
    contract_results: Path,
    strict_script: Path,
    portable_script: Path,
    output_dir: Path,
) -> dict[str, Any]:
    relative = entry["payload_path"]
    path = root / "prefix" / relative
    before = identity(
        root=root,
        strict_script=strict_script,
        portable_script=portable_script,
        output_dir=output_dir,
        label="before",
    )
    unaffected_before = owned_digest(root / "prefix", owned_entries, exclude=relative)
    mutation = mutate(path, scenario, entry["mode"])
    corrupted = identity(
        root=root,
        strict_script=strict_script,
        portable_script=portable_script,
        output_dir=output_dir,
        label="corrupted",
    )
    pre_verify = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract_results,
        root=root,
        operation="verify",
        output=output_dir / "pre-verify.json",
    )
    install = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract_results,
        root=root,
        operation="install",
        artifact="runtime-base",
        output=output_dir / "install.json",
    )
    post_verify = invoke_engine(
        local_runner=local_runner,
        engine=engine,
        contract_results=contract_results,
        root=root,
        operation="verify",
        output=output_dir / "post-verify.json",
    )
    after = identity(
        root=root,
        strict_script=strict_script,
        portable_script=portable_script,
        output_dir=output_dir,
        label="after",
    )
    unaffected_after = owned_digest(root / "prefix", owned_entries, exclude=relative)
    final_path = snapshot(path)
    desired = manifest_record(entry)
    passed = (
        before["strict"]["returncode"] == 0
        and before["portable"]["returncode"] == 0
        and pre_verify["returncode"] == 44
        and pre_verify["result"].get("bad_paths") == [relative]
        and install["returncode"] == 0
        and install["result"].get("action_counts") == {"noop": 713, "repair": 1}
        and install["result"].get("mutation_count") == 2
        and post_verify["returncode"] == 0
        and post_verify["result"].get("bad_paths") == []
        and after["strict"]["returncode"] == 0
        and after["strict"]["result"].get("fingerprint") == EXPECTED_STRICT
        and after["portable"]["returncode"] == 0
        and after["portable"]["result"].get("fingerprint") == EXPECTED_PORTABLE
        and after["registry"] == before["registry"]
        and after["transactions"] == []
        and unaffected_before == unaffected_after
        and snapshot_matches(final_path, desired)
    )
    result = {
        "schema_version": 1,
        "scenario": scenario,
        "candidate": desired,
        "before": before,
        "mutation": mutation,
        "corrupted": corrupted,
        "pre_verify": pre_verify,
        "install": install,
        "post_verify": post_verify,
        "after": after,
        "unaffected_before": unaffected_before,
        "unaffected_after": unaffected_after,
        "final_path": final_path,
        "pass": passed,
    }
    write_json(output_dir / "scenario.json", result)
    return result


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
            and sequential_identity["strict"]["result"].get("fingerprint") == EXPECTED_STRICT
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
        "seed_strict_exact": seed_identity["strict"]["result"].get("fingerprint") == EXPECTED_STRICT,
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
        "sequential_final_strict": sequential_identity["strict"]["result"].get("fingerprint") == EXPECTED_STRICT,
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

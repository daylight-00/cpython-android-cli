#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

PHASE4_INDEX = "878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce"
PHASE4I_INDEX = "7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6"
PORTABLE = "f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978"
REPAIRS = [
    "regular-bytes",
    "regular-mode",
    "regular-wrong-type",
    "symlink-target",
    "missing-regular",
    "missing-symlink",
]


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def same_path(value: object, expected: Path) -> bool:
    return isinstance(value, str) and Path(value).resolve() == expected.resolve()


def path_within(value: object, root: Path) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        Path(value).resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def final_matches(row: dict[str, Any]) -> bool:
    final = row.get("final_path", {})
    candidate = row.get("candidate", {})
    if final.get("type") != candidate.get("type") or final.get("mode") != candidate.get("mode"):
        return False
    if candidate.get("type") == "regular":
        return final.get("size") == candidate.get("size") and final.get("sha256") == candidate.get("sha256")
    if candidate.get("type") == "symlink":
        return final.get("target") == candidate.get("symlink_target")
    return True


def load_context(args: Any) -> SimpleNamespace:
    phase4 = args.phase4_results.resolve()
    phase4i = args.phase4i_results.resolve()
    scenarios_root = args.scenario_results.resolve()
    runtime_root = args.runtime_results.resolve()

    scenario_summary = read_json(scenarios_root / "scenario-summary.json")
    accepted = read_json(scenarios_root / "accepted-inputs.json")
    clones = read_json(scenarios_root / "clone-separation.json")
    sequential = read_json(scenarios_root / "sequential/summary.json")
    gate1 = read_json(args.gate1_verification.resolve())
    engine = read_json(runtime_root / "engine-verification.json")
    registry = read_json(runtime_root / "registry.json")
    strict_before = read_json(runtime_root / "installed-before.json")
    strict_after = read_json(runtime_root / "installed-after.json")
    portable_before = read_json(runtime_root / "installed-portable-before.json")
    portable_after = read_json(runtime_root / "installed-portable-after.json")
    base = read_json(runtime_root / "base-probe.json")
    venv = read_json(runtime_root / "smoke/venv-probe.json")
    uv_run = read_json(runtime_root / "smoke/uv-run-probe.json")
    closure_workflow = read_json(runtime_root / "closure/workflow-status.json")
    inventory = read_json(runtime_root / "closure/summary.json")
    closure = read_json(runtime_root / "closure/closure-analysis-summary.json")
    system_probe = read_json(runtime_root / "closure/system-soname-probe-summary.json")
    extension_probe = read_json(runtime_root / "closure/extension-import-probe-summary.json")
    input_before = read_json(args.input_before.resolve())
    input_after = read_json(args.input_after.resolve())
    smoke_text = (runtime_root / "smoke.log").read_text(encoding="utf-8")

    sequential_root = Path(scenario_summary["sequential_root"]).resolve()
    prefix = sequential_root / "prefix"
    isolated: dict[str, dict[str, Any]] = {
        "exact-noop": read_json(scenarios_root / "isolated/exact-noop/scenario.json")
    }
    for name in REPAIRS:
        isolated[name] = read_json(scenarios_root / "isolated" / name / "scenario.json")
    sequential_steps = {
        name: read_json(scenarios_root / "sequential" / f"{index:02d}-{name}" / "scenario.json")
        for index, name in enumerate(REPAIRS, start=1)
    }

    required = {
        scenarios_root / "scenario-summary.json",
        scenarios_root / "accepted-inputs.json",
        scenarios_root / "clone-separation.json",
        scenarios_root / "sequential/install.json",
        scenarios_root / "sequential/install-process.json",
        scenarios_root / "sequential/noop.json",
        scenarios_root / "sequential/noop-process.json",
        scenarios_root / "sequential/final-verify.json",
        scenarios_root / "sequential/final-verify-process.json",
        scenarios_root / "sequential/summary.json",
        runtime_root / "engine-verification.json",
        runtime_root / "registry.json",
        runtime_root / "installed-before.json",
        runtime_root / "installed-after.json",
        runtime_root / "installed-portable-before.json",
        runtime_root / "installed-portable-after.json",
        runtime_root / "base-probe.json",
        runtime_root / "smoke/venv-probe.json",
        runtime_root / "smoke/uv-run-probe.json",
        runtime_root / "closure/workflow-status.json",
        runtime_root / "closure/summary.json",
        runtime_root / "closure/closure-analysis-summary.json",
        runtime_root / "closure/system-soname-probe-summary.json",
        runtime_root / "closure/extension-import-probe-summary.json",
        args.gate1_verification.resolve(),
        args.input_before.resolve(),
        args.input_after.resolve(),
    }
    for name in isolated:
        base_dir = scenarios_root / "isolated" / name
        required.add(base_dir / "scenario.json")
        stages = ("install", "verify") if name == "exact-noop" else ("pre-verify", "install", "post-verify")
        for stage in stages:
            required.add(base_dir / f"{stage}.json")
            required.add(base_dir / f"{stage}-process.json")
    for index, name in enumerate(REPAIRS, start=1):
        base_dir = scenarios_root / "sequential" / f"{index:02d}-{name}"
        required.add(base_dir / "scenario.json")
        for stage in ("pre-verify", "install", "post-verify"):
            required.add(base_dir / f"{stage}.json")
            required.add(base_dir / f"{stage}-process.json")

    raw_embedded_match = True
    noop = isolated["exact-noop"]
    raw_embedded_match &= read_json(scenarios_root / "isolated/exact-noop/install-process.json") == noop["install"]
    raw_embedded_match &= read_json(scenarios_root / "isolated/exact-noop/verify-process.json") == noop["verify"]
    for name in REPAIRS:
        row = isolated[name]
        directory = scenarios_root / "isolated" / name
        raw_embedded_match &= read_json(directory / "pre-verify-process.json") == row["pre_verify"]
        raw_embedded_match &= read_json(directory / "install-process.json") == row["install"]
        raw_embedded_match &= read_json(directory / "post-verify-process.json") == row["post_verify"]
    for index, name in enumerate(REPAIRS, start=1):
        row = sequential_steps[name]
        directory = scenarios_root / "sequential" / f"{index:02d}-{name}"
        raw_embedded_match &= read_json(directory / "pre-verify-process.json") == row["pre_verify"]
        raw_embedded_match &= read_json(directory / "install-process.json") == row["install"]
        raw_embedded_match &= read_json(directory / "post-verify-process.json") == row["post_verify"]

    return SimpleNamespace(
        phase4=phase4,
        phase4i=phase4i,
        scenarios_root=scenarios_root,
        runtime_root=runtime_root,
        scenario_summary=scenario_summary,
        accepted=accepted,
        clones=clones,
        sequential=sequential,
        gate1=gate1,
        engine=engine,
        registry=registry,
        strict_before=strict_before,
        strict_after=strict_after,
        portable_before=portable_before,
        portable_after=portable_after,
        base=base,
        venv=venv,
        uv_run=uv_run,
        closure_workflow=closure_workflow,
        inventory=inventory,
        closure=closure,
        system_probe=system_probe,
        extension_probe=extension_probe,
        input_before=input_before,
        input_after=input_after,
        smoke_text=smoke_text,
        sequential_root=sequential_root,
        prefix=prefix,
        isolated=isolated,
        sequential_steps=sequential_steps,
        repair_rows=[isolated[name] for name in REPAIRS],
        sequential_rows=[sequential_steps[name] for name in REPAIRS],
        required=required,
        missing_files=sorted(str(path) for path in required if not path.is_file()),
        generated_jsons=[path for path in required if path.suffix == ".json"],
        raw_embedded_match=raw_embedded_match,
        noop=noop,
    )

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Callable

RAW_SHA = "bebc4dc1fcd793775eb2a8a50c9d0b58e738f1e2f83282c597255aae196500ea"
RAW_SIZE = 41858

PATHS = {
    "adr6": "docs/decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md",
    "adr7": "docs/decisions/ADR-0007-EPOCH2-EVIDENCE-AND-EPOCH3-SELECTION-GATES.md",
    "e2": "docs/epochs/EPOCH2_CHARTER.md",
    "e3": "docs/epochs/EPOCH3_CHARTER.md",
    "roadmap": "docs/roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md",
    "plan": "docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md",
    "context": "docs/CURRENT_CONTEXT.md",
    "index": "docs/INDEX.md",
    "ownership": "docs/architecture/COMPONENT_OWNERSHIP.md",
    "freeze": "docs/evidence/E2_UPSTREAM_THIN_PLAN_AUTHORITY_FREEZE.md",
    "intake": "docs/references/UPSTREAM_THIN_PLAN_INTAKE_20260719.md",
    "raw": "docs/references/raw/2026-07-19-upstream-thin-plan/UPSTREAM_THIN_RESEARCH_AND_DESIGN_PLAN.md",
    "raw_readme": "docs/references/raw/2026-07-19-upstream-thin-plan/README.md",
    "authority": "experiments/epoch2-upstream-thin-plan/plan-authority.json",
    "recal": "experiments/epoch2-recalibration/recalibration-authority.json",
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--json-out")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    checks: list[dict[str, object]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        checks.append({"name": name, "pass": bool(condition), "detail": detail})

    def text(key: str) -> str:
        p = root / PATHS[key]
        check(f"file-present:{key}", p.is_file(), str(p))
        if not p.is_file():
            return ""
        try:
            return p.read_text(encoding="utf-8")
        except Exception as e:
            check(f"utf8:{key}", False, repr(e))
            return ""

    docs = {key: text(key) for key in PATHS if key not in {"authority", "recal", "raw"}}

    raw_path = root / PATHS["raw"]
    check("file-present:raw", raw_path.is_file(), str(raw_path))
    if raw_path.is_file():
        check("raw-size", raw_path.stat().st_size == RAW_SIZE, str(raw_path.stat().st_size))
        check("raw-sha256", sha256(raw_path) == RAW_SHA, sha256(raw_path))
        try:
            raw_text = raw_path.read_text(encoding="utf-8")
            check("raw-title", raw_text.startswith("# Upstream-Thin Research and Design Plan"))
            check("raw-ut7", "## UT-7 — Update Portability" in raw_text)
            check("raw-completion-20", "20. Is the Python 3.15 delta understood" in raw_text)
        except Exception as e:
            check("raw-utf8", False, repr(e))

    try:
        authority = json.loads((root / PATHS["authority"]).read_text())
        check("authority-schema", authority.get("schema_version") == 1)
        check("authority-name", authority.get("authority") == "epoch2-remaining-work-and-epoch3-completion-gates")
        d = authority.get("decisions", {})
        check("api36-required", d.get("api36_epoch2_required") is True)
        check("api36-not-auto-adopt", d.get("api36_epoch3_auto_adopt") is False)
        check("success-not-inclusion", d.get("experiment_success_implies_epoch3_inclusion") is False)
        check("epoch4-source-producer", d.get("epoch4_owns_full_source_producer") is True)
        check("e2-dispositions", d.get("epoch2_evidence_dispositions") == ["pass", "bounded-pass", "fail", "unavailable"])
        check("e3-dispositions", d.get("epoch3_selection_dispositions") == ["adopt", "adopt-with-redesign", "exclude", "defer-to-epoch4"])
        check("work-program", authority.get("work_program") == ["UT-0","UT-1","UT-2","UT-3","UT-4","UT-5","UT-6","UT-7","API36-A-B-C"])
        check("e2-gates", authority.get("epoch2_closure_gates") == [f"E2-G{i}" for i in range(1,9)])
        check("e3-init-gates", authority.get("epoch3_initialization_gates") == [f"E3-I{i}" for i in range(1,5)])
        check("e3-completion-gates", authority.get("epoch3_completion_gates") == [f"E3-G{i}" for i in range(1,11)])
        minimum = authority.get("selectable_minimum", [])
        for item in ["base-pip","ca-policy","timezone-policy","sdk-modes","multiprocessing","uv-integration","api36-input"]:
            check(f"selectable:{item}", item in minimum)
        raw = authority.get("raw_input", {})
        check("authority-raw-path", raw.get("path") == PATHS["raw"])
        check("authority-raw-sha", raw.get("sha256") == RAW_SHA)
        check("authority-raw-size", raw.get("size") == RAW_SIZE)
        check("next-action", authority.get("next_action_class") == "execute-e2-r1-ut0-exact-official-upstream-control")
    except Exception as e:
        check("authority-json", False, repr(e))

    try:
        recal = json.loads((root / PATHS["recal"]).read_text())
        check("recal-schema", recal.get("schema_version") == 2)
        rd = recal.get("decisions", {})
        check("recal-api36", rd.get("epoch2_api36_comparison_required") is True)
        check("recal-api36-upstream-material", rd.get("epoch2_api36_uses_upstream_sources_patches_recipes") is True)
        check("recal-success-not-inclusion", rd.get("experiment_success_implies_epoch3_inclusion") is False)
        check("recal-plan-link", recal.get("detailed_plan_authority") == PATHS["authority"])
        check("recal-next-action", recal.get("next_action_class") == "execute-e2-r1-ut0-exact-official-upstream-control")
        check("recal-note9", rd.get("note9") == "optional-deferred-evidence")
        check("recal-emulator", rd.get("emulator") == "waived-unclaimed")
    except Exception as e:
        check("recal-json", False, repr(e))

    plan = docs.get("plan", "")
    adr7 = docs.get("adr7", "")
    e2 = docs.get("e2", "")
    e3 = docs.get("e3", "")
    roadmap = docs.get("roadmap", "")
    context = docs.get("context", "")
    ownership = docs.get("ownership", "")
    index = docs.get("index", "")
    intake = docs.get("intake", "")
    freeze = docs.get("freeze", "")

    for n in range(8):
        check(f"plan-ut-{n}", f"## UT-{n} " in plan)
    for n in range(1,9):
        check(f"plan-e2-g{n}", f"### E2-G{n} " in plan)
    for n in range(1,5):
        check(f"plan-e3-i{n}", f"### E3-I{n} " in plan)
    for n in range(1,11):
        check(f"plan-e3-g{n}", f"### E3-G{n} " in plan)

    required_plan_terms = [
        "A successful Epoch 2 experiment is not an automatic Epoch 3 feature",
        "PIP-X  omit base pip from the Epoch 3 product",
        "API-36 controlled source-equivalent comparison track",
        "same upstream CPython and BeeWare dependency source revisions",
        "project-required LD_LIBRARY_PATH = absent",
        "loader-bootstrap self-reexec     = absent",
        "E2-G8 — Producer-independent evidence export",
        "E3-G10 — Epoch 4 substitution boundary",
    ]
    for term in required_plan_terms:
        check("plan-term:" + term[:35], term in plan, term)

    check("adr7-status", "- **Status:** Accepted" in adr7)
    check("adr7-api36", "API 36 is mandatory Epoch 2 research" in adr7)
    check("adr7-not-auto", "does not automatically become an Epoch 3 product feature" in adr7)
    check("adr7-pip-example", "external pip payload may work" in adr7)
    check("adr7-e3-dispositions", "adopt-with-redesign" in adr7 and "defer-to-epoch4" in adr7)
    check("adr7-epoch4", "Full CPython/dependency source production remains Epoch 4" in adr7 or "source production or deeper architecture work" in adr7)

    check("e2-link-plan", "EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md" in e2)
    check("e2-success-not-inclusion", "does not automatically select the Epoch 3 feature set" in e2)
    check("e2-api36-same-material", "same-source and same-recipe API 36" in e2)
    check("e2-pip-example", "External pip may pass" in e2)
    check("e2-note9-optional", "optional deferred evidence" in e2)
    check("e2-no-note9-closure", "does not require the optional Note9 run" in e2)

    check("e3-selection-register", "## Selection register" in e3)
    check("e3-passing-not-inclusion", "A passing experiment is not an inclusion decision" in e3)
    check("e3-api36-default", "official upstream API-floor product remains the default input" in e3)
    check("e3-no-source-producer", "CPython source patch production" in e3 and "BeeWare dependency recipe production" in e3)
    check("e3-gates", "E3-G1 through E3-G10" in e3)

    check("roadmap-ut", "UT-0 exact upstream control" in roadmap and "UT-7" in roadmap)
    check("roadmap-api36-required", "API 36 is mandatory Epoch 2 research" in roadmap)
    check("roadmap-not-auto", "passed experiment is not automatic product inclusion" in roadmap)
    check("roadmap-e2-r6", "E2-R6" in roadmap)

    check("context-next", "E2-R1 / UT-0 exact official upstream control" in context)
    check("context-selection", "adopt / adopt-with-redesign / exclude / defer-to-epoch4" in context)
    check("context-api36-evidence", "not automatic Epoch 3 inputs" in context)
    check("context-note9", "optional additional evidence" in context)

    check("ownership-evidence", "does not automatically authorize Epoch 3 inclusion" in ownership)
    check("ownership-selection", "complete selection register" in ownership)
    check("ownership-source-e4", "Epoch 4 source producer" in ownership)

    for target in [
        "ADR-0007-EPOCH2-EVIDENCE-AND-EPOCH3-SELECTION-GATES.md",
        "EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md",
        "UPSTREAM_THIN_PLAN_INTAKE_20260719.md",
        "2026-07-19-upstream-thin-plan",
        "epoch2-upstream-thin-plan",
    ]:
        check("index:" + target, target in index)

    check("intake-sha", RAW_SHA in intake)
    check("intake-size", str(RAW_SIZE) in intake)
    check("freeze-api36", "API 36 remains mandatory Epoch 2 research" in freeze)
    check("freeze-success-selection", "Successful experiments do not automatically become product features" in freeze)

    # Contradiction scans in canonical new documents.
    canonical = "\n".join([adr7, e2, e3, roadmap, plan, context, ownership])
    forbidden = [
        "API-36 compile-time CPython behavior\n  defer",
        "every passed experiment is included",
        "Note9 is required for Epoch 2 closure",
        "emulator qualification is accepted",
        "Epoch 3 owns the full CPython/dependency source producer",
        "base pip is mandatory",
    ]
    for term in forbidden:
        check("forbidden:" + term[:35], term not in canonical, term)

    failed = [c for c in checks if not c["pass"]]
    result = {
        "schema_version": 1,
        "check_count": len(checks),
        "failed_checks": [c["name"] for c in failed],
        "checks": checks,
        "pass": not failed,
    }
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ["schema_version","check_count","failed_checks","pass"]}, sort_keys=True))
    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(main())

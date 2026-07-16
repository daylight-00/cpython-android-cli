#!/usr/bin/env python3
"""Verify the Stage 3-F Gate 5 documentation-integrity correction."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable

BRANCH = "agent/stage3f-publication-acquisition"
BAD_HEAD = "71ded3869f38ed59118435f119a35591aee29f75"
BAD_TREE = "78459cd8a561a72f6d5f41e0c46dc327da715d35"
BAD_RESULT = "a338b903d78f3cfa34ae8cddae45b1cb83cb3a89953c0804994e4110691cb5e1"
PARENT_HEAD = "1e7797218473463bc85f6413c49080301eda2ad7"
PARENT_TREE = "a3a1cb90f12b20ab47203b4f6b47d8a9694b0e04"
RETAINED_SNAPSHOT = "dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233"
FAILED_CORRECTION_RESULT = "69bfe223c5fb4f0dec42cf5b99ac35d346be9aaddb7438b82ce59e1d38af494a"

MIN_LINES = {
    "README.md": 480,
    "docs/GITHUB_COLLABORATION_WORKFLOW.md": 280,
    "docs/PROJECT_CONTEXT_STAGE3F.md": 95,
    "docs/PROJECT_ORIENTATION.md": 40,
    "docs/handoff/README.md": 50,
    "docs/stages/STAGE3F_SCOPE.md": 125,
}

SENTINELS = {
    "README.md": [
        "## Frozen runtime architecture",
        "## Stage 3-B frozen result",
        "## Repository map",
        "## Stage 3-F frozen publication and acquisition authority",
    ],
    "docs/GITHUB_COLLABORATION_WORKFLOW.md": [
        "## Git execution model",
        "## Authorship policy",
        "## Drive exchange rule",
        "## Sandbox boundary",
    ],
    "docs/PROJECT_CONTEXT_STAGE3F.md": [
        "## Frozen foundation",
        "## Gate 5 freeze and documentation correction",
        "## Deferred boundary",
    ],
    "docs/PROJECT_ORIENTATION.md": [
        "## Governing method",
        "## Current boundary",
        "## Current reading path",
    ],
    "docs/handoff/README.md": [
        "# Successor Session Handoff",
        "Stage 3-F Gate 5 independent publication freeze",
    ],
    "docs/stages/STAGE3F_SCOPE.md": [
        "## Stage question",
        "## Frozen authority separation",
        "## Gate 5 frozen result and integrity correction",
        "## Explicitly not proved",
    ],
}

REQUIRED = sorted(set(MIN_LINES) | {
    "docs/evidence/STAGE3F_FINAL_SUMMARY.md",
    "docs/evidence/STAGE3F_GATE5_INDEPENDENT_FREEZE.md",
    "docs/evidence/STAGE3F_GATE5_DOCUMENTATION_INTEGRITY_CORRECTION.md",
    "docs/handoff/2026-07-16-stage3f-independent-freeze.md",
    "docs/handoff/2026-07-16-stage3f-gate5-documentation-integrity-correction.md",
    "experiments/stage3f-publication-acquisition/GATE5_INDEPENDENT_PUBLICATION_ACQUISITION_FREEZE.md",
    "experiments/stage3f-publication-acquisition/GATE5_DOCUMENTATION_INTEGRITY_CORRECTION.md",
    "experiments/stage3f-publication-acquisition/gate5-independent-publication-acquisition-freeze.json",
    "experiments/stage3f-publication-acquisition/gate5-documentation-integrity-correction-authority.json",
    "experiments/stage3f-publication-acquisition/run-gate5-documentation-integrity-correction.sh",
    "experiments/stage3f-publication-acquisition/test-verify-gate5-documentation-integrity-correction.py",
    "experiments/stage3f-publication-acquisition/verify-gate5-documentation-integrity-correction.py",
})


def dig(value: Any, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def bytecode_inventory(root: Path) -> set[str]:
    entries: set[str] = set()
    for path in root.rglob("__pycache__"):
        if ".git" not in path.parts:
            entries.add(str(path.relative_to(root)) + "/")
    for path in root.rglob("*.pyc"):
        if ".git" not in path.parts:
            entries.add(str(path.relative_to(root)))
    return entries


def load_bytecode_baseline(path: Path) -> set[str]:
    raw = path.read_text(encoding="utf-8")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {line.strip() for line in raw.splitlines() if line.strip()}
    if isinstance(value, dict):
        value = value.get("entries", [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("bytecode baseline must be a string list or {'entries': [...]} object")
    return set(value)


def tracked_bytecode(root: Path) -> set[str]:
    proc = subprocess.run(
        ["git", "ls-files"], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if proc.returncode != 0:
        return set()
    result: set[str] = set()
    for rel in proc.stdout.splitlines():
        parts = Path(rel).parts
        if "__pycache__" in parts or rel.endswith(".pyc"):
            result.add(rel)
    return result


def verify(root: Path, bytecode_baseline: Iterable[str] | None = None) -> dict[str, Any]:
    root = root.resolve()
    missing: list[str] = []
    parse_errors: dict[str, str] = {}

    def text(rel: str) -> str:
        path = root / rel
        if not path.is_file():
            missing.append(rel)
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except Exception as exc:
            parse_errors[rel] = f"{type(exc).__name__}: {exc}"
            return ""

    def data(rel: str) -> dict[str, Any]:
        raw = text(rel)
        if not raw:
            return {}
        try:
            value = json.loads(raw)
        except Exception as exc:
            parse_errors[rel] = f"{type(exc).__name__}: {exc}"
            return {}
        if not isinstance(value, dict):
            parse_errors[rel] = "top-level JSON is not an object"
            return {}
        return value

    docs = {rel: text(rel) for rel in MIN_LINES}
    final_summary = text("docs/evidence/STAGE3F_FINAL_SUMMARY.md")
    freeze_evidence = text("docs/evidence/STAGE3F_GATE5_INDEPENDENT_FREEZE.md")
    correction_evidence = text("docs/evidence/STAGE3F_GATE5_DOCUMENTATION_INTEGRITY_CORRECTION.md")
    correction_handoff = text("docs/handoff/2026-07-16-stage3f-gate5-documentation-integrity-correction.md")
    correction_doc = text("experiments/stage3f-publication-acquisition/GATE5_DOCUMENTATION_INTEGRITY_CORRECTION.md")
    correction_run = text("experiments/stage3f-publication-acquisition/run-gate5-documentation-integrity-correction.sh")
    correction_test = text("experiments/stage3f-publication-acquisition/test-verify-gate5-documentation-integrity-correction.py")
    freeze = data("experiments/stage3f-publication-acquisition/gate5-independent-publication-acquisition-freeze.json")
    correction = data("experiments/stage3f-publication-acquisition/gate5-documentation-integrity-correction-authority.json")

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    branch = git("symbolic-ref", "--quiet", "--short", "HEAD")
    diff = git("diff", "--check", "HEAD")
    current_bytecode = bytecode_inventory(root)
    baseline_path = os.environ.get("STAGE3F_BYTECODE_BASELINE", "")
    baseline_mode = "explicit-delta" if bytecode_baseline is not None or baseline_path else "tracked-only"
    try:
        if bytecode_baseline is not None:
            baseline = set(bytecode_baseline)
        elif baseline_path:
            baseline = load_bytecode_baseline(Path(baseline_path))
        else:
            baseline = set()
    except Exception as exc:
        parse_errors["STAGE3F_BYTECODE_BASELINE"] = f"{type(exc).__name__}: {exc}"
        baseline = set()
    new_bytecode = sorted(current_bytecode - baseline) if baseline_mode == "explicit-delta" else sorted(tracked_bytecode(root))

    checks: dict[str, bool] = {
        "required_files": all((root / rel).is_file() for rel in REQUIRED),
        "parse_clean": not parse_errors,
        "branch": branch.returncode == 0 and branch.stdout.strip() == BRANCH,
        "correction_status": correction.get("status") == "correction-v2-defined-and-locally-verified",
        "correction_class": correction.get("class") == "R-repository-corrective-fast-forward",
        "correction_precondition": dig(correction, "repository_precondition", "head") == BAD_HEAD and dig(correction, "repository_precondition", "tree") == BAD_TREE,
        "failed_result_identity": dig(correction, "failed_gate5_transaction", "result_archive_sha256") == BAD_RESULT and dig(correction, "failed_gate5_transaction", "acceptance") is False,
        "failed_correction_attempt": dig(correction, "failed_correction_attempt", "result_archive_sha256") == FAILED_CORRECTION_RESULT and dig(correction, "failed_correction_attempt", "repository_mutation") is False,
        "restoration_source": dig(correction, "restoration_source", "commit") == PARENT_HEAD and dig(correction, "restoration_source", "tree") == PARENT_TREE,
        "affected_paths": sorted(dig(correction, "restored_paths", default=[])) == sorted(MIN_LINES),
        "no_history_rewrite": dig(correction, "protected_state", "history_rewrite") is False,
        "bounded_protected_state": all(dig(correction, "protected_state", key) is False for key in ("target_execution", "uv_invocation", "network_publication", "external_network", "cache_mutation", "installation_mutation")),
        "bytecode_policy": dig(correction, "integrity_contract", "bytecode_residue", "policy") == "no-new-relative-to-preflight-baseline" and dig(correction, "integrity_contract", "bytecode_residue", "standalone_fallback") == "no-tracked-bytecode",
        "bytecode_baseline_mode": baseline_mode in {"explicit-delta", "tracked-only"},
        "readme_minimum_lines": len(docs["README.md"].splitlines()) >= MIN_LINES["README.md"],
        "collaboration_minimum_lines": len(docs["docs/GITHUB_COLLABORATION_WORKFLOW.md"].splitlines()) >= MIN_LINES["docs/GITHUB_COLLABORATION_WORKFLOW.md"],
        "context_minimum_lines": len(docs["docs/PROJECT_CONTEXT_STAGE3F.md"].splitlines()) >= MIN_LINES["docs/PROJECT_CONTEXT_STAGE3F.md"],
        "orientation_minimum_lines": len(docs["docs/PROJECT_ORIENTATION.md"].splitlines()) >= MIN_LINES["docs/PROJECT_ORIENTATION.md"],
        "handoff_minimum_lines": len(docs["docs/handoff/README.md"].splitlines()) >= MIN_LINES["docs/handoff/README.md"],
        "scope_minimum_lines": len(docs["docs/stages/STAGE3F_SCOPE.md"].splitlines()) >= MIN_LINES["docs/stages/STAGE3F_SCOPE.md"],
        "readme_sentinels": all(marker in docs["README.md"] for marker in SENTINELS["README.md"]),
        "collaboration_sentinels": all(marker in docs["docs/GITHUB_COLLABORATION_WORKFLOW.md"] for marker in SENTINELS["docs/GITHUB_COLLABORATION_WORKFLOW.md"]),
        "context_sentinels": all(marker in docs["docs/PROJECT_CONTEXT_STAGE3F.md"] for marker in SENTINELS["docs/PROJECT_CONTEXT_STAGE3F.md"]),
        "orientation_sentinels": all(marker in docs["docs/PROJECT_ORIENTATION.md"] for marker in SENTINELS["docs/PROJECT_ORIENTATION.md"]),
        "handoff_sentinels": all(marker in docs["docs/handoff/README.md"] for marker in SENTINELS["docs/handoff/README.md"]),
        "scope_sentinels": all(marker in docs["docs/stages/STAGE3F_SCOPE.md"] for marker in SENTINELS["docs/stages/STAGE3F_SCOPE.md"]),
        "readme_final_status": "frozen — Gate 5 independent freeze complete; documentation integrity corrected" in docs["README.md"],
        "context_no_active_gate": "> **Active boundary:** none" in docs["docs/PROJECT_CONTEXT_STAGE3F.md"],
        "scope_frozen": "> **Status:** FROZEN" in docs["docs/stages/STAGE3F_SCOPE.md"],
        "retained_snapshot_preserved": RETAINED_SNAPSHOT in docs["README.md"] and RETAINED_SNAPSHOT in docs["docs/PROJECT_CONTEXT_STAGE3F.md"],
        "initial_failure_documented": BAD_HEAD in correction_evidence and BAD_RESULT in correction_evidence and "1,017" in correction_evidence,
        "correction_v1_false_negative_documented": FAILED_CORRECTION_RESULT in correction_evidence and "pre-existing ignored bytecode" in correction_evidence,
        "final_summary_corrected": "documentation-integrity correction" in final_summary and BAD_HEAD in final_summary,
        "freeze_evidence_corrected": "documentation-integrity correction" in freeze_evidence and BAD_HEAD in freeze_evidence,
        "correction_handoff": BAD_HEAD in correction_handoff and "fast-forward" in correction_handoff,
        "correction_doc": "> **Status:** CORRECTION V2 DEFINED" in correction_doc and "1,017" in correction_doc,
        "freeze_authority_corrected": freeze.get("status") == "independent-freeze-complete-with-documentation-integrity-correction" and dig(freeze, "documentation_integrity_correction", "initial_commit") == BAD_HEAD,
        "correction_run_bounded": "PYTHONDONTWRITEBYTECODE=1" in correction_run and "STAGE3F_BYTECODE_BASELINE" in correction_run and "verify-gate5-documentation-integrity-correction.py" in correction_run,
        "correction_fixture_negative": "shortened_document" in correction_test and "bytecode_delta" in correction_test and "expected_negative" in correction_test and "incomplete" in correction_test,
        "no_new_bytecode_residue": not new_bytecode,
        "git_diff_check": diff.returncode == 0,
    }

    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": 2,
        "verification_kind": "stage3f-gate5-documentation-integrity-correction",
        "pass": not failed and not missing and not parse_errors,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "failed_checks": failed,
        "missing_files": sorted(set(missing)),
        "parse_errors": parse_errors,
        "bytecode": {
            "mode": baseline_mode,
            "baseline_count": len(baseline),
            "current_count": len(current_bytecode),
            "new_entries": new_bytecode,
        },
        "checks": dict(sorted(checks.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--bytecode-baseline", type=Path)
    args = parser.parse_args()
    baseline = load_bytecode_baseline(args.bytecode_baseline) if args.bytecode_baseline else None
    result = verify(Path(args.root), baseline)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

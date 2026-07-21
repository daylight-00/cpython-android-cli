#!/usr/bin/env python3
"""Independently audit a returned canonical install-only candidate."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))

from archive import sha256_file, write_json  # noqa: E402
from verify_install_only import verify  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--full-archive", required=True)
    parser.add_argument("--zstd", required=True)
    args = parser.parse_args()

    result = Path(args.result_dir).resolve()
    full = Path(args.full_archive).resolve()
    receipts = result / "receipts"
    summary = load(receipts / "gate-diagnostics.json")
    verification = load(receipts / "install-only-verification.json")
    qualification = load(receipts / "install-only-target-qualification.json")
    reproducibility = load(receipts / "install-only-reproducibility.json")
    authority = load(receipts / "full-authority-verification.json")
    artifacts = sorted((result / "artifacts").glob("*-install_only.tar.gz"))

    checks: dict[str, bool] = {
        "one_install_only_artifact": len(artifacts) == 1,
        "no_stripped_artifact": not list((result / "artifacts").glob("*stripped*")),
        "summary_pass": summary.get("pass") is True,
        "full_authority_pass": authority.get("pass") is True,
        "verification_pass": verification.get("pass") is True,
        "target_qualification_pass": qualification.get("pass") is True,
        "reproducibility_pass": reproducibility.get("pass") is True and reproducibility.get("first") == reproducibility.get("second"),
        "claims_withheld": all(
            summary.get("claim_boundary", {}).get(key) is False
            for key in (
                "install_only_authority_frozen",
                "stripped_implementation_started",
                "selectable",
                "publication",
                "api24_runtime_claim",
                "actual_16k_runtime_claim",
                "non_termux_context_claim",
            )
        ),
    }
    rerun: dict[str, Any] = {"pass": False}
    if artifacts:
        artifact = artifacts[0]
        checks["artifact_identity_matches_summary"] = (
            summary.get("artifact", {}).get("sha256") == sha256_file(artifact)
            and summary.get("artifact", {}).get("size_bytes") == artifact.stat().st_size
        )
        rerun = verify(artifact, full, zstd=args.zstd, fixture_mode=False)
        checks["independent_projection_rerun"] = (
            rerun.get("pass") is True
            and rerun.get("artifact", {}).get("sha256") == verification.get("artifact", {}).get("sha256")
            and rerun.get("source_full", {}).get("sha256") == summary.get("source_full", {}).get("sha256")
        )
    else:
        checks["artifact_identity_matches_summary"] = False
        checks["independent_projection_rerun"] = False

    failed = sorted(name for name, value in checks.items() if value is not True)
    audit = {
        "schema_version": 1,
        "audit_kind": "epoch3-first-real-install-only-independent-return-audit",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "independent_projection_rerun": rerun,
        "claim_boundary": {
            "install_only_authority_frozen": False,
            "stripped_implementation_started": False,
            "selectable": False,
            "publication": False,
        },
    }
    write_json(receipts / "independent-audit.json", audit)
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

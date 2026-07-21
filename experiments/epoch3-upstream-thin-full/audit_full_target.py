#!/usr/bin/env python3
"""Independent audit of returned first-real-full candidate evidence."""
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
from verify_full import verify  # noqa: E402


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--readelf", required=True)
    parser.add_argument("--zstd", required=True)
    args = parser.parse_args()
    result = Path(args.result_dir).resolve()
    receipts = result / "receipts"
    gate = load(receipts / "gate-diagnostics.json")
    static = load(receipts / "full-static-verification.json")
    target = load(receipts / "full-target-qualification.json")
    golden = load(receipts / "astral-golden-observation.json")
    conformance = load(receipts / "astral-conformance-decision-input.json")
    reproducibility = load(receipts / "full-reproducibility.json")
    artifacts = sorted((result / "artifacts").glob("*-full.tar.zst"))
    checks: dict[str, bool] = {
        "one_full_artifact": len(artifacts) == 1,
        "no_downstream_flavors": not list((result / "artifacts").glob("*install_only*")) and not list((result / "artifacts").glob("*stripped*")),
        "gate_pass": gate.get("pass") is True,
        "static_pass": static.get("pass") is True,
        "target_pass": target.get("pass") is True,
        "golden_pass": golden.get("pass") is True,
        "conformance_pass": conformance.get("pass") is True,
        "reproducibility_pass": reproducibility.get("pass") is True and reproducibility.get("first") == reproducibility.get("second"),
        "claims_withheld": all(gate.get("claim_boundary", {}).get(key) is False for key in ("full_authority_frozen", "install_only_implementation_started", "selectable", "publication", "api24_runtime_claim", "actual_16k_runtime_claim", "non_termux_context_claim")),
    }
    rerun: dict[str, Any] = {"pass": False}
    if artifacts:
        artifact = artifacts[0]
        checks["artifact_identity_matches_gate"] = gate.get("artifact", {}).get("sha256") == sha256_file(artifact) and gate.get("artifact", {}).get("size_bytes") == artifact.stat().st_size
        rerun = verify(artifact, zstd=args.zstd, readelf=args.readelf, fixture_mode=False)
        checks["independent_static_rerun"] = rerun.get("pass") is True and rerun.get("archive", {}).get("sha256") == static.get("archive", {}).get("sha256")
    else:
        checks["artifact_identity_matches_gate"] = False
        checks["independent_static_rerun"] = False
    failed = sorted(key for key, value in checks.items() if value is not True)
    audit = {
        "schema_version": 1,
        "audit_kind": "epoch3-first-real-full-independent-return-audit",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "independent_static_rerun": rerun,
        "claim_boundary": {"full_authority_frozen": False, "selectable": False, "publication": False},
    }
    write_json(receipts / "independent-audit.json", audit)
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

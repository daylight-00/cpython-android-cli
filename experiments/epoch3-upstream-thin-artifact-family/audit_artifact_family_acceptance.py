#!/usr/bin/env python3
"""Independent repository audit before freezing artifact-family authority."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    verifier = ROOT / "experiments/epoch3-upstream-thin-artifact-family/verify_artifact_family_acceptance.py"
    proc = subprocess.run([sys.executable, str(verifier), "--root", str(ROOT)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        primary = json.loads(proc.stdout)
    except json.JSONDecodeError:
        primary = {}
    bound = [
        "components/upstream-thin/lib/release_family.py",
        "components/upstream-thin/tests/test_release_family.py",
        "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-artifact-family-r1.lock.json",
        "experiments/epoch3-upstream-thin-artifact-family/accepted-r1-return.json",
        "experiments/epoch3-upstream-thin-artifact-family/run_artifact_family.py",
        "experiments/epoch3-upstream-thin-artifact-family/audit_artifact_family.py",
        "experiments/epoch3-upstream-thin-artifact-family/verify_artifact_family_acceptance.py",
    ]
    checks = {
        "primary_pass": proc.returncode == 0 and primary.get("pass") is True,
        "all_primary_checks_pass": bool(primary.get("checks")) and all(primary.get("checks", {}).values()),
        "family_identity_exact": primary.get("release_family", {}).get("fingerprint_sha256") == "87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302" and primary.get("release_family", {}).get("file_count") == 23,
        "three_artifacts_exact": set(primary.get("artifacts", {})) == {"full", "install_only", "install_only_stripped"},
        "claims_bounded": primary.get("claim_boundary", {}).get("selectable") is False and primary.get("claim_boundary", {}).get("publication") is False and primary.get("claim_boundary", {}).get("component_license_mapping_complete") is False,
        "bound_files_present": all((ROOT / rel).is_file() for rel in bound),
    }
    failed = sorted(key for key, value in checks.items() if value is not True)
    result = {
        "schema_version": 1,
        "audit_kind": "epoch3-artifact-family-acceptance-independent-audit",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "primary_verification_sha256": hashlib.sha256((proc.stdout.rstrip() + "\n").encode()).hexdigest() if proc.stdout else None,
        "bound_file_identities": {rel: sha(ROOT / rel) for rel in bound if (ROOT / rel).is_file()},
        "stderr": proc.stderr,
        "claim_boundary": {
            "artifact_family_complete": not failed,
            "release_blocker_work_authorized": not failed,
            "component_license_mapping_complete": False,
            "selectable": False,
            "publication": False,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

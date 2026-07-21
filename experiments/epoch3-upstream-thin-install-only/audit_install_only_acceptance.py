#!/usr/bin/env python3
"""Independent repository audit before freezing install-only authority."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    proc = subprocess.run([sys.executable, str(ROOT / "experiments/epoch3-upstream-thin-install-only/verify_install_only_acceptance.py"), "--root", str(ROOT)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        primary = json.loads(proc.stdout)
    except json.JSONDecodeError:
        primary = {}
    bound = [
        "experiments/epoch3-upstream-thin-install-only/accepted-r1-return.json",
        "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-install-only-r1.lock.json",
        "components/upstream-thin/lib/assemble_install_only.py",
        "components/upstream-thin/lib/verify_install_only.py",
        "components/upstream-thin/lib/qualify_install_only.py",
        "experiments/epoch3-upstream-thin-install-only/run_install_only_target.py",
        "experiments/epoch3-upstream-thin-install-only/audit_install_only_target.py",
    ]
    checks = {
        "primary_pass": proc.returncode == 0 and primary.get("pass") is True,
        "all_primary_checks_pass": bool(primary.get("checks")) and all(primary.get("checks", {}).values()),
        "artifact_exact": primary.get("artifact", {}).get("sha256") == "84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76",
        "source_full_exact": primary.get("source_full", {}).get("sha256") == "20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12",
        "claims_bounded": primary.get("claim_boundary", {}).get("selectable") is False and primary.get("claim_boundary", {}).get("publication") is False,
        "bound_files_present": all((ROOT / rel).is_file() for rel in bound),
    }
    failed = sorted(k for k, v in checks.items() if v is not True)
    result = {
        "schema_version": 1,
        "audit_kind": "epoch3-canonical-install-only-acceptance-independent-audit",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "primary_verification_sha256": hashlib.sha256((proc.stdout.rstrip() + "\n").encode()).hexdigest() if proc.stdout else None,
        "bound_file_identities": {rel: sha(ROOT / rel) for rel in bound if (ROOT / rel).is_file()},
        "stderr": proc.stderr,
        "claim_boundary": {"install_only_complete": not failed, "stripped_authorized_to_start": not failed, "selectable": False, "publication": False},
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

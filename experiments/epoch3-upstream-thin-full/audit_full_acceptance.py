#!/usr/bin/env python3
"""Independent repository audit before freezing the canonical full authority."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def main() -> int:
    primary = subprocess.run(
        [sys.executable, str(ROOT / "experiments/epoch3-upstream-thin-full/verify_full_acceptance.py")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        verification = json.loads(primary.stdout)
    except Exception:  # noqa: BLE001
        verification = {}
    accepted = load(ROOT / "experiments/epoch3-upstream-thin-full/accepted-r4-return.json")
    gate = load(ROOT / "experiments/epoch3-upstream-thin-full/authority-evidence/gate-diagnostics.json")
    target = load(ROOT / "experiments/epoch3-upstream-thin-full/authority-evidence/full-target-qualification.json")
    audit = load(ROOT / "experiments/epoch3-upstream-thin-full/authority-evidence/independent-audit.json")
    checks = {
        "primary_verifier_passes": primary.returncode == 0 and verification.get("pass") is True,
        "accepted_artifact_matches_gate": accepted["artifact"]["sha256"] == gate["artifact"]["sha256"] == "20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12",
        "accepted_size_matches_target": accepted["artifact"]["size_bytes"] == target["archive"]["size_bytes"] == 39408292,
        "independent_return_audit_passes": audit.get("pass") is True and all(audit.get("checks", {}).values()),
        "full_has_exact_inventory": accepted["artifact"]["archive_member_count"] == 3752 and accepted["artifact"]["elf_count"] == 81 and accepted["artifact"]["python_extension_count"] == 67,
        "full_is_only_artifact": gate.get("gates", {}).get("only_full_artifact") is True and gate.get("claim_boundary", {}).get("install_only_implementation_started") is False,
        "android_claim_is_bounded": target.get("claim_boundary", {}).get("qualified_context") == "current owner Termux app process on Android/Bionic" and target.get("claim_boundary", {}).get("non_termux_context_claim") is False,
        "publication_withheld": all(source.get("claim_boundary", {}).get("publication") is False for source in (gate, target, audit)),
        "selectability_withheld": all(source.get("claim_boundary", {}).get("selectable") is False for source in (gate, target, audit)),
        "full_code_identity_recorded": len(verification.get("claim_code_identities", {})) == 6,
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    result = {
        "schema_version": 1,
        "audit_kind": "epoch3-canonical-full-authority-independent-audit",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": len(checks) - len(failed),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "primary_output_sha256": hashlib.sha256(primary.stdout.encode()).hexdigest(),
        "accepted_return_sha256": sha(ROOT / "experiments/epoch3-upstream-thin-full/accepted-r4-return.json"),
        "claim_boundary": {
            "canonical_full_complete": not failed,
            "install_only_may_start": not failed,
            "selectable": False,
            "publication": False,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

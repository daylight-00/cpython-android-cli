#!/usr/bin/env python3
"""Verify the frozen canonical full authority and its immutable bindings."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def verify(*, root: Path = ROOT, authority_path: Path | None = None) -> dict[str, Any]:
    path = authority_path or root / "experiments/epoch3-upstream-thin-full/full-authority.json"
    checks: dict[str, bool] = {}
    errors: dict[str, str] = {}
    try:
        authority = load(path)
        checks["authority_parse"] = True
    except Exception as exc:  # noqa: BLE001
        authority = {}
        checks["authority_parse"] = False
        errors["authority_parse"] = f"{type(exc).__name__}: {exc}"

    checks["authority_kind"] = authority.get("authority_kind") == "epoch3-upstream-thin-canonical-full"
    checks["status_frozen_pass"] = authority.get("status") == "frozen-pass-full-complete-install-only-authorized"
    artifact = authority.get("artifact", {})
    checks["artifact_exact"] = artifact == {
        "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-full.tar.zst",
        "sha256": "20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12",
        "size_bytes": 39408292,
        "member_count": 3752,
        "elf_count": 81,
        "python_extension_count": 67,
    }
    completion = authority.get("completion", {})
    checks["required_gates_complete"] = all(completion.get(key) is True for key in ("E3-G1", "E3-G2", "E3-G3", "E3-G4-full"))
    checks["next_action_exact"] = authority.get("next_action_class") == "derive-epoch3-install-only-from-full"
    claims = authority.get("claim_boundary", {})
    checks["claim_boundary"] = (
        claims.get("canonical_full_complete") is True
        and claims.get("install_only_implementation_authorized") is True
        and claims.get("selectable") is False
        and claims.get("publication") is False
        and claims.get("api24_runtime") is False
        and claims.get("actual_16k_runtime") is False
        and claims.get("non_termux_context") is False
    )
    identities = authority.get("file_identities", {})
    forbidden = {"docs/current/STATE.json", "docs/current/AGENT_TASK.json", "README.md", "docs/CURRENT_CONTEXT.md", "docs/INDEX.md"}
    checks["no_live_view_binding"] = not (set(identities) & forbidden)
    identity_ok = True
    for rel, expected in identities.items():
        target = root / rel
        if not target.is_file() or sha(target) != expected:
            identity_ok = False
    checks["file_identities_exact"] = len(identities) >= 13 and identity_ok
    full_lock = root / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-full-r4.lock.json"
    checks["full_lock_bound"] = identities.get(full_lock.relative_to(root).as_posix()) == sha(full_lock) if full_lock.is_file() else False
    accepted = root / "experiments/epoch3-upstream-thin-full/accepted-r4-return.json"
    checks["accepted_return_bound"] = identities.get(accepted.relative_to(root).as_posix()) == sha(accepted) if accepted.is_file() else False
    primary = load(root / "experiments/epoch3-upstream-thin-full/full-verification.json") if (root / "experiments/epoch3-upstream-thin-full/full-verification.json").is_file() else {}
    audit = load(root / "experiments/epoch3-upstream-thin-full/full-independent-audit.json") if (root / "experiments/epoch3-upstream-thin-full/full-independent-audit.json").is_file() else {}
    checks["primary_and_audit_pass"] = primary.get("pass") is True and audit.get("pass") is True

    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-canonical-full-authority",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": len(checks) - len(failed),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--authority")
    args = parser.parse_args()
    result = verify(root=Path(args.root).resolve(), authority_path=Path(args.authority).resolve() if args.authority else None)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

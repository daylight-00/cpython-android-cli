#!/usr/bin/env python3
"""Verify the frozen canonical install-only authority and all bound identities."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "experiments/epoch3-upstream-thin-install-only/install-only-authority.json"
EXPECTED_ARTIFACT = {
    "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only.tar.gz",
    "sha256": "84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76",
    "size_bytes": 23841726,
    "member_count": 3699,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path = ROOT, authority_path: Path | None = None) -> dict:
    path = authority_path or root / AUTHORITY.relative_to(ROOT)
    checks = {}
    errors = []
    try:
        authority = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        authority = {}
        errors.append(f"{type(exc).__name__}: {exc}")
    checks["authority_parse"] = bool(authority)
    checks["authority_kind"] = authority.get("authority_kind") == "epoch3-upstream-thin-canonical-install-only"
    checks["status"] = authority.get("status") == "frozen-pass-install-only-complete-stripped-authorized"
    checks["artifact_exact"] = authority.get("artifact") == EXPECTED_ARTIFACT
    checks["source_full_exact"] = authority.get("source_full", {}).get("sha256") == "20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12"
    checks["projection_exact"] = authority.get("projection_invariant") == {
        "source": "python/install/**",
        "target": "python/**",
        "filtering": "none-preserve-all-install-members",
        "payload_bytes_unchanged": True,
        "full_metadata_excluded": ["python/PYTHON.json", "python/build/**"],
    }
    claims = authority.get("claim_boundary", {})
    checks["claims_bounded"] = claims.get("install_only_complete") is True and claims.get("stripped_implementation_authorized") is True and claims.get("selectable") is False and claims.get("publication") is False and claims.get("api24_runtime") is False and claims.get("actual_16k_runtime") is False and claims.get("non_termux_context") is False
    completion = authority.get("completion", {})
    checks["completion_gates"] = all(completion.get(k) is True for k in ("E3-G2", "E3-G4-install-only", "E3-G6-install-only", "E3-G7"))
    ids = authority.get("file_identities", {})
    identity_ok = bool(ids)
    for rel, expected in ids.items():
        p = root / rel
        if not p.is_file() or sha(p) != expected:
            identity_ok = False
    checks["file_identities"] = identity_ok
    checks["next_action"] = authority.get("next_action_class") == "derive-epoch3-stripped-from-install-only"
    failed = sorted(k for k, v in checks.items() if v is not True)
    return {"schema_version": 1, "verifier_kind": "epoch3-canonical-install-only-authority", "pass": not failed and not errors, "checks": dict(sorted(checks.items())), "failed_checks": failed, "errors": errors, "authority_sha256": sha(path) if path.is_file() else None}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--authority")
    args = parser.parse_args()
    result = verify(Path(args.root).resolve(), Path(args.authority).resolve() if args.authority else None)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

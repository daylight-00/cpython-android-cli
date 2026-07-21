#!/usr/bin/env python3
"""Verify the frozen canonical artifact-family authority."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "experiments/epoch3-upstream-thin-artifact-family/artifact-family-authority.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("authority must be an object")
    return value


def verify(root: Path, authority_path: Path | None = None) -> dict[str, Any]:
    path = authority_path or (root / DEFAULT.relative_to(ROOT))
    checks: dict[str, bool] = {}
    errors: list[str] = []
    try:
        authority = load(path)
        checks["authority_parse"] = True
    except Exception as exc:  # noqa: BLE001
        authority = {}
        checks["authority_parse"] = False
        errors.append(f"{type(exc).__name__}: {exc}")

    checks["authority_kind"] = authority.get("authority_kind") == "epoch3-upstream-thin-canonical-artifact-family"
    checks["status"] = authority.get("status") == "frozen-pass-artifact-family-complete-release-blockers-authorized"
    family = authority.get("release_family", {})
    checks["family_identity"] = family.get("release_id") == "cpython-3.14.6+e3-r1-aarch64-linux-android" and family.get("file_count") == 23 and family.get("fingerprint_sha256") == "87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302" and family.get("release_index", {}).get("sha256") == "b60274ac64b40c43fc174e4ea4a238743216452b5dfe8af300adde37c4fd7389" and family.get("release_sha256") == "81bd66f5cd1978485eb50991d5a6e773b55b51defb52483db6db5215c1a91a9e" and family.get("sha256sums", {}).get("sha256") == "b47f399a48526e75aad98499aff841126986f8436702a7cd5c9cd25784ac6082"
    artifacts = authority.get("artifacts", {})
    checks["three_artifacts"] = set(artifacts) == {"full", "install_only", "install_only_stripped"} and artifacts.get("full", {}).get("sha256") == "20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12" and artifacts.get("install_only", {}).get("sha256") == "84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76" and artifacts.get("install_only_stripped", {}).get("sha256") == "40951002c5880b223fa78c7b956dfcf2929e3ebf8e8beb9420c4179b98231134"
    checks["input_authorities"] = authority.get("inputs", {}).get("full_authority_sha256") == "a29064602ad2fa612eba516cc09ab49334f7d8ec4aec04f3c9e2e0827afec9d0" and authority.get("inputs", {}).get("install_only_authority_sha256") == "7f27a85ce283e0283bb7e7cf0e4aace8282d7cfd0d37c732b23188c8b318018d" and authority.get("inputs", {}).get("stripped_authority_sha256") == "bf985a2cfc5446f7deab36d853f27ac439c30ba2b85b761546d919fe411a2d25" and authority.get("inputs", {}).get("result_archive_sha256") == "1fc50a26840cd33d15ef53cd85674fd3cc4a46c96ea00657eef9f6f3fdb93ade"
    checks["completion_gates"] = all(authority.get("completion", {}).get(key) is True for key in ("E3-G4-family", "E3-G6-family", "E3-G7-family"))
    checks["next_action"] = authority.get("next_action_class") == "resolve-epoch3-release-blocking-experiments"
    claims = authority.get("claim_boundary", {})
    checks["claims_bounded"] = claims.get("artifact_family_complete") is True and claims.get("artifact_family_authority_frozen") is True and claims.get("release_blocker_work_authorized") is True and claims.get("component_license_mapping_complete") is False and claims.get("api24_runtime") is False and claims.get("actual_16k_runtime") is False and claims.get("non_termux_context") is False and claims.get("selectable") is False and claims.get("publication") is False
    identities = authority.get("file_identities", {})
    identity_ok = bool(identities)
    for rel, expected in identities.items():
        file_path = root / rel
        if not file_path.is_file() or sha(file_path) != expected:
            identity_ok = False
            errors.append(f"file identity mismatch: {rel}")
    checks["file_identities"] = identity_ok
    checks["verification"] = authority.get("verification") == {"primary": "26/26", "independent_audit": "6/6", "verifier_fixtures": "3/3"}

    failed = sorted(key for key, value in checks.items() if value is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-canonical-artifact-family-authority",
        "pass": not failed and not errors,
        "authority_sha256": sha(path) if path.is_file() else None,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
    }


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

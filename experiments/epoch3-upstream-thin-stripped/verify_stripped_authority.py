#!/usr/bin/env python3
"""Verify the frozen canonical install_only_stripped authority and bound identities."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "experiments/epoch3-upstream-thin-stripped/stripped-authority.json"
EXPECTED_ARTIFACT = {
    "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only_stripped.tar.gz",
    "sha256": "40951002c5880b223fa78c7b956dfcf2929e3ebf8e8beb9420c4179b98231134",
    "size_bytes": 23841241,
    "member_count": 3699,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path = ROOT, authority_path: Path | None = None) -> dict:
    path = authority_path or root / AUTHORITY.relative_to(ROOT)
    checks: dict[str, bool] = {}
    errors: list[str] = []
    try:
        authority = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        authority = {}
        errors.append(f"{type(exc).__name__}: {exc}")
    checks["authority_parse"] = bool(authority)
    checks["authority_kind"] = authority.get("authority_kind") == "epoch3-upstream-thin-canonical-install-only-stripped"
    checks["status"] = authority.get("status") == "frozen-pass-stripped-complete-artifact-family-authorized"
    checks["artifact_exact"] = authority.get("artifact") == EXPECTED_ARTIFACT
    checks["source_install_only_exact"] = authority.get("source_install_only") == {
        "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only.tar.gz",
        "sha256": "84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76",
        "size_bytes": 23841726,
    }
    checks["strip_surface_exact"] = authority.get("strip_surface") == {
        "decision": "distinct-archive",
        "operation": "--strip-unneeded",
        "regular_elf_count": 81,
        "eligible_elf_count": 1,
        "changed_elf_count": 1,
        "eligible_paths": ["bin/python3.14"],
        "changed_paths": ["bin/python3.14"],
        "non_elf_payload_unchanged": True,
        "dynamic_and_alignment_surface_preserved": True,
    }
    tool = authority.get("tool_identity", {})
    checks["tool_identity"] = (
        tool.get("alias_invocation_semantics_preserved") is True
        and tool.get("llvm_version") == "21.1.8"
        and tool.get("readelf_invocation") == "/data/data/com.termux/files/usr/bin/readelf"
        and tool.get("readelf_canonical") == "/data/data/com.termux/files/usr/bin/llvm-readobj"
        and tool.get("readelf_sha256") == "f409f88b053ede038c37d2cc844a6c065a9d623cdebdf3f63d544beb8b55630e"
        and tool.get("strip_invocation") == "/data/data/com.termux/files/usr/bin/llvm-strip"
        and tool.get("strip_canonical") == "/data/data/com.termux/files/usr/bin/llvm-objcopy"
        and tool.get("strip_sha256") == "b1196f21e347a912662b0bea76ad97c60f758e68c612b58006d505182a679392"
    )
    claims = authority.get("claim_boundary", {})
    checks["claims_bounded"] = (
        claims.get("stripped_complete") is True
        and claims.get("artifact_family_implementation_authorized") is True
        and claims.get("selectable") is False
        and claims.get("publication") is False
        and claims.get("api24_runtime") is False
        and claims.get("actual_16k_runtime") is False
        and claims.get("non_termux_context") is False
    )
    completion = authority.get("completion", {})
    checks["completion_gates"] = all(completion.get(key) is True for key in ("E3-X4", "E3-G2", "E3-G4-stripped", "E3-G6-stripped", "E3-G7"))
    checks["input_authorities"] = authority.get("inputs") == {
        "install_only_authority_sha256": "7f27a85ce283e0283bb7e7cf0e4aace8282d7cfd0d37c732b23188c8b318018d",
        "result_archive_sha256": "f23fcbaed9cdaad1da8ca355500e8181297f0c70b96618f5f5a802b607b08a93",
    }
    ids = authority.get("file_identities", {})
    identity_ok = bool(ids)
    for rel, expected in ids.items():
        candidate = root / rel
        if not candidate.is_file() or sha(candidate) != expected:
            identity_ok = False
    checks["file_identities"] = identity_ok
    checks["next_action"] = authority.get("next_action_class") == "finalize-epoch3-artifact-family"
    failed = sorted(key for key, value in checks.items() if value is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-canonical-install-only-stripped-authority",
        "pass": not failed and not errors,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "authority_sha256": sha(path) if path.is_file() else None,
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

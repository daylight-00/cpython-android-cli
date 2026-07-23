#!/usr/bin/env python3
"""Qualify RB-1 technical-legal and RB-2 data/runtime rebinding for profile M."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))

from archive import safe_extract_tar, sha256_file, write_json  # noqa: E402
from data_products import activate_data_release, install_data_product, verify_data_product  # noqa: E402

LEGAL_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-successor-legal-family-r3.lock.json"
RB1_AUTHORITY = ROOT / "experiments/epoch3-upstream-thin-release-blockers/rb1-legal-integration-authority.json"
RB2_AUTHORITY = ROOT / "experiments/epoch3-upstream-thin-release-blockers/rb2-data-product-authority.json"

RELEASE_ID = "cpython-3.14.6+e3-r3-aarch64-linux-android"
RELEASE_FINGERPRINT = "c8d76b6dcb934c12098efb2de985c5ab4799e4b5db5ae1c2b7c0f5a68438a82a"
RELEASE_SHA = "2c31578f95a11291eee1693db80048568a7b533e77877f36a8b1570241ce1e1c"
NOTICE_SHA = "80cf82a6b6957fd830701e2559755d1eecdf01c61cbcb4f8f8843b9735eaf613"
COMPONENT_MAP_SHA = "4da6f405f18ff827452f33aea0886f993ab9dab362b515350ab8f92c87b0f7b2"
RB1_AUTHORITY_SHA = "23717b5b69b52f76f37240f008e1cf1718158adc0419fcf05dd0729cf492f8ba"
RB2_AUTHORITY_SHA = "48ae38370afcd3cf095566307e6859ee2bf88a6ee0c45ad7f07dea7401e77098"
INSTALL_ONLY = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android-install_only.tar.gz",
    "sha256": "c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56",
    "size_bytes": 23843355,
}
DATA_PRODUCTS = {
    "rollback": {
        "filename": "android-data-ca-2026.5.20-tzdata-2026.2-r1.tar.zst",
        "sha256": "144d96b8f301309fc2269cc73c9f888a37b663afc0ae3e485966834b635d750d",
        "size_bytes": 229141,
        "release_id": "android-data-ca-2026.5.20-tzdata-2026.2-r1",
    },
    "current": {
        "filename": "android-data-ca-2026.6.17-tzdata-2026.3-r1.tar.zst",
        "sha256": "e7dcdfa84f093d8bbdea50c80f25b9f20bddd8619199610405c4ba344790268d",
        "size_bytes": 227318,
        "release_id": "android-data-ca-2026.6.17-tzdata-2026.3-r1",
    },
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def identity(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def snapshot(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append({"path": rel, "type": "symlink", "target": os.readlink(path)})
        elif path.is_file():
            rows.append({"path": rel, "type": "file", "sha256": sha256_file(path), "size_bytes": path.stat().st_size, "mode": stat.S_IMODE(path.stat().st_mode)})
        elif path.is_dir():
            rows.append({"path": rel, "type": "directory", "mode": stat.S_IMODE(path.stat().st_mode)})
    return rows


def fingerprint(rows: list[dict[str, Any]]) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def content_snapshot(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return path/content identity while intentionally excluding permission modes."""
    return [{key: value for key, value in row.items() if key != "mode"} for row in rows]


def read_only_modes_enforced(rows: list[dict[str, Any]]) -> bool:
    """True when every non-symlink file and directory has no write bits."""
    relevant = [row for row in rows if row.get("type") in {"file", "directory"}]
    return bool(relevant) and all(isinstance(row.get("mode"), int) and row["mode"] & 0o222 == 0 for row in relevant)


def candidate_claim_boundary() -> dict[str, bool]:
    return {
        "successor_legal_family_accepted": True,
        "successor_legal_data_rebinding_started": True,
        "successor_legal_data_rebinding_candidate": True,
        "successor_legal_data_rebinding_accepted": False,
        "rb1_technical_legal_evidence_complete": True,
        "rb2_data_runtime_evidence_complete": True,
        "rb1_rebound": False,
        "rb2_rebound": False,
        "owner_approved": False,
        "predecessor_family_superseded": False,
        "rb3_closed": False,
        "selectable": False,
        "publication": False,
    }


def verify_exact_successor_family(family: Path) -> dict[str, Any]:
    lock = load(LEGAL_LOCK)
    expected = {row["path"]: {"sha256": row["sha256"], "size_bytes": row["size_bytes"]} for row in lock["files"]}
    actual_paths = {path.relative_to(family).as_posix() for path in family.rglob("*") if path.is_file() and not path.is_symlink()}
    checks: dict[str, bool] = {"exact_file_set": actual_paths == set(expected)}
    mismatches: list[dict[str, Any]] = []
    for rel, wanted in sorted(expected.items()):
        path = family / rel
        actual = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size} if path.is_file() else None
        if actual != wanted:
            mismatches.append({"path": rel, "actual": actual, "expected": wanted})
    checks["all_file_identities"] = not mismatches
    index_path = family / "release-index.json"
    index = load(index_path) if index_path.is_file() else {}
    checks["release_index_present"] = bool(index)
    checks["release_identity"] = (
        index.get("file_count") == 128
        and index.get("family_fingerprint_sha256") == RELEASE_FINGERPRINT
        and index.get("release_sha256") == RELEASE_SHA
        and index.get("release", {}).get("release_id") == RELEASE_ID
    )
    checks["accepted_lock_boundary"] = lock.get("claim_boundary", {}).get("successor_legal_family_accepted") is True
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-rb3-successor-legal-family-r3-exact-input",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "mismatches": mismatches,
        "release": {"release_id": RELEASE_ID, "file_count": len(actual_paths), "family_fingerprint_sha256": index.get("family_fingerprint_sha256"), "release_sha256": index.get("release_sha256")},
    }


def qualify_rb1(family: Path) -> dict[str, Any]:
    index = load(family / "release-index.json")
    release = index["release"]
    legal = release["legal"]
    binding = legal["binding"]
    rebinding = binding["license_rebinding"]
    component_map = load(family / "legal/component-license-map.json")
    technical = load(family / "legal/technical-obligation-review.json")
    gaps = load(family / "legal/updated-gap-register.json")
    integration = load(family / "legal/legal-integration.json")
    checks = {
        "source_authority_exact": sha256_file(RB1_AUTHORITY) == RB1_AUTHORITY_SHA and binding.get("source_authority", {}).get("sha256") == RB1_AUTHORITY_SHA,
        "legal_payload_byte_exact": binding.get("legal_payload_byte_identical") is True and binding.get("legal_payload_file_count") == 102,
        "component_map_exact": sha256_file(family / "legal/component-license-map.json") == COMPONENT_MAP_SHA,
        "component_mapping_complete": component_map.get("mapping_complete") is True and component_map.get("componentization_complete") is True and component_map.get("top_level_component_count") == 13,
        "technical_review_complete": technical.get("technical_review_complete") is True and technical.get("review_unit_count") == 31 and technical.get("pip_vendored_component_count") == 18,
        "successor_flavors_rebound": rebinding.get("pass") is True and all(row.get("pass") is True and row.get("license_file_count") == 42 and row.get("license_inventory_byte_semantics_equal") is True for row in rebinding.get("flavors", {}).values()) and set(rebinding.get("flavors", {})) == {"full", "install_only", "install_only_stripped"},
        "notice_exact": sha256_file(family / "legal/THIRD-PARTY-NOTICES.candidate.txt") == NOTICE_SHA and legal.get("third_party_notices_candidate_sha256") == NOTICE_SHA,
        "single_owner_gap": gaps.get("blocking_gap_count") == 1 and gaps.get("remaining_gaps") == [{"code": "final-notice-set-not-owner-approved"}] and gaps.get("closure_status") == "owner-approval-pending",
        "owner_approval_pending": component_map.get("owner_approved") is False and binding.get("owner_approved") is False and integration.get("owner_approved") is False and integration.get("rb1_closed") is False,
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "result_kind": "epoch3-rb3-successor-rb1-technical-legal-rebinding-candidate",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "release_id": release.get("release_id"),
        "metrics": {"top_level_component_count": component_map.get("top_level_component_count"), "pip_vendored_component_count": technical.get("pip_vendored_component_count"), "review_unit_count": technical.get("review_unit_count"), "legal_payload_file_count": binding.get("legal_payload_file_count"), "license_files_per_flavor": {key: value.get("license_file_count") for key, value in sorted(rebinding.get("flavors", {}).items())}, "remaining_gap_count": gaps.get("blocking_gap_count")},
        "owner_approved": False,
        "rb1_closed": False,
        "claim_boundary": {"technical_legal_evidence_complete": not failed, "owner_approved": False, "rb1_rebound": False, "rb1_closed": False, "selectable": False, "publication": False},
    }


def exact_data_artifact(rb2_result: Path, name: str, *, zstd: str) -> tuple[Path, dict[str, Any]]:
    expected = DATA_PRODUCTS[name]
    path = rb2_result / "target/artifacts" / expected["filename"]
    actual = identity(path) if path.is_file() else None
    wanted = {key: expected[key] for key in ("filename", "sha256", "size_bytes")}
    if actual != wanted:
        raise ValueError(f"{name} data product identity mismatch: actual={actual!r} expected={wanted!r}")
    verification = verify_data_product(path, zstd=zstd)
    if verification.get("pass") is not True or verification.get("metrics", {}).get("release_id") != expected["release_id"]:
        raise ValueError(f"{name} data product verification failed: {verification}")
    return path, verification


def _make_read_only(root: Path) -> dict[Path, int]:
    modes: dict[Path, int] = {}
    paths = [root, *sorted(root.rglob("*"), reverse=True)]
    for path in paths:
        if path.is_symlink():
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        modes[path] = mode
        os.chmod(path, mode & ~0o222)
    return modes


def _restore_modes(modes: dict[Path, int]) -> None:
    for path, mode in sorted(modes.items(), key=lambda item: len(item[0].parts)):
        if path.exists() and not path.is_symlink():
            os.chmod(path, mode)


def qualify_runtime(python: Path, data_root: Path, install_root: Path) -> dict[str, Any]:
    metadata = load(data_root / "DATA.json")
    ca = data_root / metadata["layout"]["ca_bundle"]
    zoneinfo = data_root / metadata["layout"]["zoneinfo_root"]
    script = r'''
import json, os, ssl, sys, sysconfig, zoneinfo
ctx = ssl.create_default_context(cafile=os.environ["SSL_CERT_FILE"])
zoneinfo.reset_tzpath([os.environ["PYTHONTZPATH"]])
keys = ["UTC", "Asia/Seoul", "America/New_York"]
print(json.dumps({
  "ca_count": len(ctx.get_ca_certs()),
  "zones": {key: str(zoneinfo.ZoneInfo(key)) for key in keys},
  "version": sys.version.split()[0],
  "executable": sys.executable,
  "prefix": sys.prefix,
  "base_prefix": sys.base_prefix,
  "soabi": sysconfig.get_config_var("SOABI"),
  "multiarch": sysconfig.get_config_var("MULTIARCH"),
  "platform": sysconfig.get_platform(),
}, sort_keys=True))
'''
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("PYTHON") or key in {"SSL_CERT_FILE", "SSL_CERT_DIR", "LD_LIBRARY_PATH", "LD_PRELOAD"}:
            env.pop(key, None)
    env.update({"SSL_CERT_FILE": str(ca), "PYTHONTZPATH": str(zoneinfo)})
    proc = subprocess.run([str(python), "-I", "-c", script], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    details: dict[str, Any] = {}
    if proc.returncode == 0:
        details = json.loads(proc.stdout)
    checks = {
        "process_success": proc.returncode == 0,
        "ca_loaded": details.get("ca_count", 0) > 0,
        "zones_loaded": set(details.get("zones", {})) == {"UTC", "Asia/Seoul", "America/New_York"},
        "python_version": details.get("version") == "3.14.6",
        "android_identity": details.get("soabi") == "cpython-314-aarch64-linux-android" and details.get("multiarch") == "aarch64-linux-android" and details.get("platform") == "android-24-arm64_v8a",
        "exact_extracted_prefix": details.get("prefix") == str(install_root / "python") and details.get("base_prefix") == str(install_root / "python"),
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {"schema_version": 1, "qualifier_kind": "epoch3-rb3-successor-rb2-data-runtime", "pass": not failed, "checks": dict(sorted(checks.items())), "failed_checks": failed, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "details": details, "data_root": str(data_root), "python": str(python)}


def qualify_rb2(family: Path, rb2_result: Path, output: Path, *, zstd: str) -> dict[str, Any]:
    if sha256_file(RB2_AUTHORITY) != RB2_AUTHORITY_SHA:
        raise ValueError("RB-2 source authority identity mismatch")
    rollback_archive, rollback_verification = exact_data_artifact(rb2_result, "rollback", zstd=zstd)
    current_archive, current_verification = exact_data_artifact(rb2_result, "current", zstd=zstd)
    family_before = snapshot(family)
    install_archive = family / INSTALL_ONLY["filename"]
    if identity(install_archive) != INSTALL_ONLY:
        raise ValueError(f"successor install-only identity mismatch: {identity(install_archive)}")

    with tempfile.TemporaryDirectory(prefix="e3-rb3-rebind-") as raw:
        temp = Path(raw)
        data_home = temp / "data-home"
        events = [
            {"event": "install-rollback", "result": install_data_product(rollback_archive, data_home, zstd=zstd)},
            {"event": "install-current", "result": install_data_product(current_archive, data_home, zstd=zstd)},
            {"event": "rollback", "result": activate_data_release(data_home, DATA_PRODUCTS["rollback"]["release_id"])},
            {"event": "reactivate-current", "result": activate_data_release(data_home, DATA_PRODUCTS["current"]["release_id"])},
        ]
        current_link = os.readlink(data_home / "current")
        lifecycle = {
            "schema_version": 1,
            "check_kind": "epoch3-rb3-successor-data-update-rollback-reactivation",
            "pass": current_link == f"releases/{DATA_PRODUCTS['current']['release_id']}",
            "events": events,
            "final_current_link": current_link,
            "release_directories": sorted(path.name for path in (data_home / "releases").iterdir() if path.is_dir()),
            "python_install_root_written": False,
        }

        runtime_root = temp / "runtime"
        safe_extract_tar(install_archive, runtime_root, "r:gz")
        python = runtime_root / "python/bin/python3.14"
        if not python.is_file() or not os.access(python, os.X_OK):
            raise ValueError("successor interpreter missing after extraction")
        install_before = snapshot(runtime_root / "python")
        modes = _make_read_only(runtime_root / "python")
        try:
            qualification = qualify_runtime(python, data_home / "current", runtime_root)
            install_after_read_only = snapshot(runtime_root / "python")
        finally:
            _restore_modes(modes)
        install_after = snapshot(runtime_root / "python")

    family_after = snapshot(family)
    content_before = content_snapshot(install_before)
    content_after_read_only = content_snapshot(install_after_read_only)
    content_after_restore = content_snapshot(install_after)
    content_unchanged = content_before == content_after_read_only == content_after_restore
    read_only_enforced = read_only_modes_enforced(install_after_read_only)
    modes_restored = install_before == install_after
    checks = {
        "source_authority_exact": sha256_file(RB2_AUTHORITY) == RB2_AUTHORITY_SHA,
        "accepted_data_products_exact": rollback_verification.get("pass") is True and current_verification.get("pass") is True,
        "update_rollback_reactivation": lifecycle["pass"],
        "successor_runtime_qualified": qualification.get("pass") is True,
        "read_only_install_root_content_unchanged": content_unchanged,
        "read_only_install_root_mode_enforced": read_only_enforced,
        "install_root_modes_restored": modes_restored,
        "accepted_family_unchanged": family_before == family_after,
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    result = {
        "schema_version": 1,
        "result_kind": "epoch3-rb3-successor-rb2-data-runtime-rebinding-candidate",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "successor_install_only": INSTALL_ONLY,
        "data_products": {"rollback": identity(rollback_archive), "current": identity(current_archive)},
        "data_product_verification": {"rollback": rollback_verification, "current": current_verification},
        "lifecycle": lifecycle,
        "runtime_qualification": qualification,
        "install_root_invariance": {
            "pass": content_unchanged and read_only_enforced and modes_restored,
            "content_identity_unchanged": content_unchanged,
            "read_only_modes_enforced": read_only_enforced,
            "original_modes_restored": modes_restored,
            "before_full_fingerprint_sha256": fingerprint(install_before),
            "read_only_full_fingerprint_sha256": fingerprint(install_after_read_only),
            "restored_full_fingerprint_sha256": fingerprint(install_after),
            "before_content_fingerprint_sha256": fingerprint(content_before),
            "read_only_content_fingerprint_sha256": fingerprint(content_after_read_only),
            "restored_content_fingerprint_sha256": fingerprint(content_after_restore),
            "file_count": len([row for row in install_before if row["type"] == "file"]),
        },
        "family_invariance": {"pass": family_before == family_after, "before_fingerprint_sha256": fingerprint(family_before), "after_fingerprint_sha256": fingerprint(family_after), "file_count": len([row for row in family_before if row["type"] == "file"])},
        "claim_boundary": {"data_runtime_evidence_complete": not failed, "rb2_closed_source_authority": True, "rb2_rebound": False, "predecessor_family_superseded": False, "selectable": False, "publication": False},
    }
    write_json(output / "rb2-data-runtime-rebinding.json", result)
    return result


def run(family: Path, rb2_result: Path, output: Path, *, zstd: str = "zstd") -> dict[str, Any]:
    family = family.resolve(); rb2_result = rb2_result.resolve(); output = output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    family_verification = verify_exact_successor_family(family)
    write_json(output / "successor-family-verification.json", family_verification)
    if family_verification.get("pass") is not True:
        raise ValueError(f"invalid successor family: {family_verification}")
    rb1 = qualify_rb1(family)
    write_json(output / "rb1-technical-legal-rebinding.json", rb1)
    if rb1.get("pass") is not True:
        raise ValueError(f"RB-1 technical legal rebinding failed: {rb1}")
    rb2 = qualify_rb2(family, rb2_result, output, zstd=zstd)
    if rb2.get("pass") is not True:
        raise ValueError(f"RB-2 data runtime rebinding failed: {rb2}")
    checks = {"exact_successor_family": family_verification["pass"], "rb1_technical_legal_evidence": rb1["pass"], "rb2_data_runtime_evidence": rb2["pass"], "owner_approval_still_pending": rb1["owner_approved"] is False, "predecessor_not_superseded": True}
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    result = {"schema_version": 1, "result_kind": "epoch3-rb3-profile-M-successor-legal-data-rebinding-owner-candidate", "pass": not failed, "checks": dict(sorted(checks.items())), "failed_checks": failed, "successor_family": family_verification["release"], "rb1": {"result": "rb1-technical-legal-rebinding.json", "pass": rb1["pass"], "owner_approved": False}, "rb2": {"result": "rb2-data-runtime-rebinding.json", "pass": rb2["pass"], "successor_install_only": INSTALL_ONLY}, "claim_boundary": candidate_claim_boundary()}
    write_json(output / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--successor-family-dir", type=Path, required=True)
    parser.add_argument("--rb2-result-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zstd", default="zstd")
    args = parser.parse_args()
    try:
        result = run(args.successor_family_dir, args.rb2_result_dir, args.output_dir, zstd=args.zstd)
    except Exception as exc:  # noqa: BLE001
        result = {"schema_version": 1, "result_kind": "epoch3-rb3-profile-M-successor-legal-data-rebinding-owner-candidate", "pass": False, "error": f"{type(exc).__name__}: {exc}", "claim_boundary": {**candidate_claim_boundary(), "successor_legal_data_rebinding_candidate": False, "rb1_technical_legal_evidence_complete": False, "rb2_data_runtime_evidence_complete": False}}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic profile-M successor legal-family integration.

The selected successor technical family is preserved byte-for-byte. The
accepted predecessor legal payload and project LICENSE are also preserved
byte-for-byte. Only the top-level release envelope is regenerated to bind the
accepted legal evidence to the successor technical manifests.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from archive import canonical_json_bytes, sha256_file, write_json
from successor_release_family import verify_successor_release_family

ROOT = Path(__file__).resolve().parents[3]
TECHNICAL_RELEASE_ID = "cpython-3.14.6+e3-r2-aarch64-linux-android"
LEGAL_RELEASE_ID = "cpython-3.14.6+e3-r3-aarch64-linux-android"
TECHNICAL_AUTHORITY = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-technical-family-m-authority.json"
TECHNICAL_AUTHORITY_SHA256 = "ce6a80b5505afec7c99a74e0a7c12001848ba2e1892e3592fc1066e299b091e2"
LEGAL_AUTHORITY = "experiments/epoch3-upstream-thin-release-blockers/rb1-legal-integration-authority.json"
LEGAL_AUTHORITY_SHA256 = "23717b5b69b52f76f37240f008e1cf1718158adc0419fcf05dd0729cf492f8ba"
CONTRACT = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-family-m-contract.json"
PREDECESSOR_LEGAL_FINGERPRINT = "b71a0123d9d135b3ab378b59d2227ec312c95b49dc15c6ec40fce91a916f348d"
PREDECESSOR_LEGAL_RELEASE_SHA256 = "b2d93c0f13b60e7404a948a54abfa4c7adffdb318194b291a6ec6b668b49c1fb"
NOTICE_SHA256 = "80cf82a6b6957fd830701e2559755d1eecdf01c61cbcb4f8f8843b9735eaf613"
EXPECTED_FILE_COUNT = 128
EXPECTED_LEGAL_FILE_COUNT = 102


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def identity(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def relative_identity(path: Path, base: Path) -> dict[str, Any]:
    return {"path": path.relative_to(base).as_posix(), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def inventory(root: Path, *, exclude: set[str] | None = None) -> list[dict[str, Any]]:
    exclude = exclude or set()
    return [
        relative_identity(path, root)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.relative_to(root).as_posix() not in exclude
    ]


def fingerprint(rows: list[dict[str, Any]]) -> str:
    return hashlib.sha256(canonical_json_bytes({"schema_version": 1, "files": rows})).hexdigest()


def exact_tree_equal(left: Path, right: Path) -> bool:
    return inventory(left) == inventory(right)


def safe_copy_tree(source: Path, destination: Path) -> None:
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source)
        target = destination / rel
        if path.is_symlink():
            raise ValueError(f"symlink forbidden in legal payload: {rel}")
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        else:
            raise ValueError(f"special member forbidden in legal payload: {rel}")


def _license_sidecars(directory: Path) -> dict[str, Path]:
    rows: dict[str, Path] = {}
    patterns = {
        "full": "*-full.tar.zst.licenses.json",
        "install_only": "*-install_only.tar.gz.licenses.json",
        "install_only_stripped": "*-install_only_stripped.tar.gz.licenses.json",
    }
    for flavor, pattern in patterns.items():
        matches = sorted(directory.glob(pattern))
        if len(matches) != 1:
            raise ValueError(f"expected exactly one {flavor} license sidecar in {directory}")
        rows[flavor] = matches[0]
    return rows


def verify_predecessor_legal_family(directory: Path, *, root: Path = ROOT) -> dict[str, Any]:
    directory = directory.resolve()
    checks: dict[str, bool] = {}
    errors: list[str] = []
    try:
        index = load_json(directory / "release-index.json")
        release = index["release"]
        checks["index_parse"] = True
    except Exception as exc:  # noqa: BLE001
        index, release = {}, {}
        checks["index_parse"] = False
        errors.append(f"{type(exc).__name__}: {exc}")
    checks["authority_identity"] = sha256_file(root / LEGAL_AUTHORITY) == LEGAL_AUTHORITY_SHA256
    checks["release_identity"] = release.get("release_id") == TECHNICAL_RELEASE_ID
    checks["family_identity"] = (
        index.get("family_fingerprint_sha256") == PREDECESSOR_LEGAL_FINGERPRINT
        and index.get("release_sha256") == PREDECESSOR_LEGAL_RELEASE_SHA256
        and index.get("file_count") == EXPECTED_FILE_COUNT
    )
    legal = directory / "legal"
    checks["legal_file_count"] = legal.is_dir() and len([p for p in legal.rglob("*") if p.is_file()]) == EXPECTED_LEGAL_FILE_COUNT
    checks["project_license"] = (
        (directory / "LICENSE").is_file()
        and sha256_file(directory / "LICENSE") == sha256_file(root / "LICENSE")
    )
    checks["notice_identity"] = (
        (legal / "THIRD-PARTY-NOTICES.candidate.txt").is_file()
        and sha256_file(legal / "THIRD-PARTY-NOTICES.candidate.txt") == NOTICE_SHA256
    )
    try:
        component_map = load_json(legal / "component-license-map.json")
        pip_review = load_json(legal / "pip-vendored-component-review.json")
        technical_review = load_json(legal / "technical-obligation-review.json")
        gaps = load_json(legal / "updated-gap-register.json")
        checks["legal_metrics"] = (
            component_map.get("mapping_complete") is True
            and component_map.get("review_unit_count") == 31
            and pip_review.get("vendor_component_count") == 18
            and technical_review.get("review_unit_count") == 31
            and gaps.get("blocking_gap_count") == 1
        )
    except Exception as exc:  # noqa: BLE001
        checks["legal_metrics"] = False
        errors.append(f"legal:{type(exc).__name__}: {exc}")
    expected_sums = "".join(
        f"{sha256_file(path)}  {path.relative_to(directory).as_posix()}\n"
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.relative_to(directory).as_posix() not in {"SHA256SUMS", "release-index.json"}
    )
    checks["sha256sums_exact"] = (directory / "SHA256SUMS").is_file() and (directory / "SHA256SUMS").read_text(encoding="utf-8") == expected_sums
    rows = inventory(directory, exclude={"release-index.json"})
    checks["fingerprint_exact"] = index.get("family_fingerprint_sha256") == fingerprint(rows) and index.get("file_count") == len(rows) + 1
    checks["regular_files_only"] = all(not path.is_symlink() for path in directory.rglob("*"))
    failed = sorted(key for key, value in checks.items() if value is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-rb1-accepted-legal-family-input",
        "pass": not failed and not errors,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "release_id": release.get("release_id"),
        "family_fingerprint_sha256": index.get("family_fingerprint_sha256"),
        "release_sha256": index.get("release_sha256"),
        "file_count": index.get("file_count"),
    }


def license_rebinding(technical_family: Path, predecessor_legal_family: Path) -> dict[str, Any]:
    technical = _license_sidecars(technical_family)
    predecessor = _license_sidecars(predecessor_legal_family)
    rows: dict[str, Any] = {}
    passed = True
    for flavor in ("full", "install_only", "install_only_stripped"):
        current = load_json(technical[flavor])
        previous = load_json(predecessor[flavor])
        exact = current.get("license_files") == previous.get("license_files")
        primary = current.get("primary_python_license") == previous.get("primary_python_license") == "PSF-2.0"
        rows[flavor] = {
            "pass": exact and primary,
            "successor_sidecar": relative_identity(technical[flavor], technical_family),
            "predecessor_sidecar": relative_identity(predecessor[flavor], predecessor_legal_family),
            "license_file_count": len(current.get("license_files", [])),
            "license_inventory_byte_semantics_equal": exact,
            "primary_python_license_equal": primary,
        }
        passed = passed and rows[flavor]["pass"]
    return {
        "schema_version": 1,
        "receipt_kind": "epoch3-rb3-successor-legal-family-license-rebinding",
        "pass": passed,
        "flavors": rows,
        "component_license_mapping_complete": passed,
        "owner_approved": False,
    }


def candidate_claim_boundary() -> dict[str, Any]:
    return {
        "successor_technical_family_accepted": True,
        "successor_legal_family_integration_started": True,
        "successor_legal_family_candidate": True,
        "successor_legal_family_accepted": False,
        "rb1_rebound": False,
        "rb2_rebound": False,
        "predecessor_family_superseded": False,
        "rb3_closed": False,
        "selectable": False,
        "publication": False,
        "api24_runtime": False,
        "actual_16k_runtime": False,
        "non_termux_context": False,
    }


def assemble_successor_legal_family(
    technical_family: Path,
    predecessor_legal_family: Path,
    output: Path,
    *,
    root: Path = ROOT,
    zstd: str = "zstd",
) -> dict[str, Any]:
    technical_family = technical_family.resolve()
    predecessor_legal_family = predecessor_legal_family.resolve()
    output = output.resolve()
    technical_verification = verify_successor_release_family(technical_family, root=root, zstd=zstd)
    if technical_verification.get("pass") is not True:
        raise ValueError(f"technical family verification failed: {technical_verification.get('failed_checks')}")
    legal_verification = verify_predecessor_legal_family(predecessor_legal_family, root=root)
    if legal_verification.get("pass") is not True:
        raise ValueError(f"legal family verification failed: {legal_verification.get('failed_checks')}")
    if sha256_file(root / TECHNICAL_AUTHORITY) != TECHNICAL_AUTHORITY_SHA256:
        raise ValueError("technical authority identity mismatch")
    rebinding = license_rebinding(technical_family, predecessor_legal_family)
    if rebinding.get("pass") is not True:
        raise ValueError("successor license inventories differ from accepted legal evidence")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    # Preserve all 23 technical-family bytes. The two technical envelope files
    # move under lineage/r2; the remaining 21 files retain their top-level names.
    lineage = output / "lineage/r2"
    lineage.mkdir(parents=True)
    for path in sorted(technical_family.iterdir(), key=lambda item: item.name):
        if not path.is_file():
            raise ValueError(f"unexpected technical family member: {path.name}")
        destination = lineage / path.name if path.name in {"release-index.json", "SHA256SUMS"} else output / path.name
        shutil.copyfile(path, destination)

    # Preserve accepted legal evidence and project license byte-identically.
    safe_copy_tree(predecessor_legal_family / "legal", output / "legal")
    shutil.copyfile(predecessor_legal_family / "LICENSE", output / "LICENSE")

    technical_index = load_json(technical_family / "release-index.json")
    predecessor_index = load_json(predecessor_legal_family / "release-index.json")
    legal = output / "legal"
    legal_binding = {
        "source_release_id": predecessor_index["release"]["release_id"],
        "source_family_fingerprint_sha256": predecessor_index["family_fingerprint_sha256"],
        "source_release_sha256": predecessor_index["release_sha256"],
        "source_authority": {"path": LEGAL_AUTHORITY, "sha256": LEGAL_AUTHORITY_SHA256},
        "technical_authority": {"path": TECHNICAL_AUTHORITY, "sha256": TECHNICAL_AUTHORITY_SHA256},
        "contract": {"path": CONTRACT, "sha256": sha256_file(root / CONTRACT)},
        "legal_payload_file_count": EXPECTED_LEGAL_FILE_COUNT,
        "legal_payload_byte_identical": exact_tree_equal(predecessor_legal_family / "legal", legal),
        "project_license": identity(output / "LICENSE"),
        "notice": identity(legal / "THIRD-PARTY-NOTICES.candidate.txt"),
        "license_rebinding": rebinding,
        "remaining_gap_count": 1,
        "remaining_gap": "final-notice-set-not-owner-approved",
        "owner_approved": False,
    }
    release = {
        "release_id": LEGAL_RELEASE_ID,
        "technical_predecessor_release_id": TECHNICAL_RELEASE_ID,
        "legal_evidence_predecessor_release_id": predecessor_index["release"]["release_id"],
        "python_version": "3.14.6",
        "target_triple": "aarch64-linux-android",
        "status": "successor-legal-family-candidate-owner-approval-and-rb2-rebinding-pending",
        "assets": technical_index["release"]["assets"],
        "family_invariants": technical_index["release"]["family_invariants"],
        "lineage": {
            "technical_release_index": "lineage/r2/release-index.json",
            "technical_sha256sums": "lineage/r2/SHA256SUMS",
            "technical_release_index_sha256": sha256_file(lineage / "release-index.json"),
            "technical_sha256sums_sha256": sha256_file(lineage / "SHA256SUMS"),
        },
        "legal": {
            "directory": "legal/",
            "component_license_map_sha256": sha256_file(legal / "component-license-map.json"),
            "pip_vendored_review_sha256": sha256_file(legal / "pip-vendored-component-review.json"),
            "technical_obligation_review_sha256": sha256_file(legal / "technical-obligation-review.json"),
            "third_party_notices_candidate_sha256": sha256_file(legal / "THIRD-PARTY-NOTICES.candidate.txt"),
            "updated_gap_register_sha256": sha256_file(legal / "updated-gap-register.json"),
            "project_license_sha256": sha256_file(output / "LICENSE"),
            "binding": legal_binding,
        },
        "claim_boundary": candidate_claim_boundary(),
    }
    targets = [
        path
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.relative_to(output).as_posix() not in {"SHA256SUMS", "release-index.json"}
    ]
    (output / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.relative_to(output).as_posix()}\n" for path in targets),
        encoding="utf-8",
    )
    rows = inventory(output, exclude={"release-index.json"})
    index = {
        "schema_version": 1,
        "index_kind": "epoch3-rb3-successor-legally-integrated-release-family-candidate",
        "release": release,
        "release_sha256": hashlib.sha256(canonical_json_bytes(release)).hexdigest(),
        "family_fingerprint_sha256": fingerprint(rows),
        "file_count": len(rows) + 1,
        "checksums": {"filename": "SHA256SUMS", "sha256": sha256_file(output / "SHA256SUMS")},
    }
    write_json(output / "release-index.json", index)
    return verify_successor_legal_family(
        output,
        technical_family=technical_family,
        predecessor_legal_family=predecessor_legal_family,
        root=root,
        zstd=zstd,
    )


def verify_successor_legal_family(
    directory: Path,
    *,
    technical_family: Path,
    predecessor_legal_family: Path,
    root: Path = ROOT,
    zstd: str = "zstd",
) -> dict[str, Any]:
    directory = directory.resolve()
    technical_family = technical_family.resolve()
    predecessor_legal_family = predecessor_legal_family.resolve()
    checks: dict[str, bool] = {}
    errors: list[str] = []
    try:
        index = load_json(directory / "release-index.json")
        release = index["release"]
        checks["index_parse"] = True
    except Exception as exc:  # noqa: BLE001
        index, release = {}, {}
        checks["index_parse"] = False
        errors.append(f"{type(exc).__name__}: {exc}")
    checks["technical_input"] = verify_successor_release_family(technical_family, root=root, zstd=zstd).get("pass") is True
    checks["legal_input"] = verify_predecessor_legal_family(predecessor_legal_family, root=root).get("pass") is True
    checks["release_identity"] = (
        release.get("release_id") == LEGAL_RELEASE_ID
        and release.get("technical_predecessor_release_id") == TECHNICAL_RELEASE_ID
        and release.get("status") == "successor-legal-family-candidate-owner-approval-and-rb2-rebinding-pending"
    )
    checks["release_digest"] = bool(release) and index.get("release_sha256") == hashlib.sha256(canonical_json_bytes(release)).hexdigest()
    checks["claims_bounded"] = release.get("claim_boundary") == candidate_claim_boundary()

    technical_exact = True
    for path in technical_family.iterdir():
        if not path.is_file():
            technical_exact = False
            continue
        target = directory / "lineage/r2" / path.name if path.name in {"release-index.json", "SHA256SUMS"} else directory / path.name
        if not target.is_file() or sha256_file(target) != sha256_file(path) or target.stat().st_size != path.stat().st_size:
            technical_exact = False
    checks["technical_23_files_exact"] = technical_exact and len([p for p in technical_family.iterdir() if p.is_file()]) == 23
    checks["legal_payload_exact"] = exact_tree_equal(directory / "legal", predecessor_legal_family / "legal")
    checks["project_license_exact"] = (
        (directory / "LICENSE").is_file()
        and sha256_file(directory / "LICENSE") == sha256_file(predecessor_legal_family / "LICENSE")
        and sha256_file(directory / "LICENSE") == sha256_file(root / "LICENSE")
    )
    rebinding = license_rebinding(technical_family, predecessor_legal_family)
    checks["license_rebinding"] = rebinding.get("pass") is True
    try:
        legal = directory / "legal"
        component_map = load_json(legal / "component-license-map.json")
        pip_review = load_json(legal / "pip-vendored-component-review.json")
        technical_review = load_json(legal / "technical-obligation-review.json")
        gaps = load_json(legal / "updated-gap-register.json")
        checks["legal_metrics"] = (
            component_map.get("mapping_complete") is True
            and component_map.get("review_unit_count") == 31
            and pip_review.get("vendor_component_count") == 18
            and technical_review.get("review_unit_count") == 31
            and gaps.get("blocking_gap_count") == 1
        )
        checks["notice_identity"] = sha256_file(legal / "THIRD-PARTY-NOTICES.candidate.txt") == NOTICE_SHA256
    except Exception as exc:  # noqa: BLE001
        checks["legal_metrics"] = False
        checks["notice_identity"] = False
        errors.append(f"legal:{type(exc).__name__}: {exc}")
    expected_sums = "".join(
        f"{sha256_file(path)}  {path.relative_to(directory).as_posix()}\n"
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.relative_to(directory).as_posix() not in {"SHA256SUMS", "release-index.json"}
    )
    checks["sha256sums_exact"] = (directory / "SHA256SUMS").is_file() and (directory / "SHA256SUMS").read_text(encoding="utf-8") == expected_sums
    rows = inventory(directory, exclude={"release-index.json"})
    checks["family_fingerprint"] = index.get("family_fingerprint_sha256") == fingerprint(rows)
    checks["file_count"] = index.get("file_count") == len(rows) + 1 == EXPECTED_FILE_COUNT
    checks["regular_files_only"] = all(not path.is_symlink() for path in directory.rglob("*"))
    failed = sorted(key for key, value in checks.items() if value is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-rb3-successor-legally-integrated-release-family-candidate",
        "pass": not failed and not errors,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "release_id": release.get("release_id"),
        "file_count": index.get("file_count"),
        "family_fingerprint_sha256": index.get("family_fingerprint_sha256"),
        "release_sha256": index.get("release_sha256"),
        "notice_sha256": NOTICE_SHA256,
        "claim_boundary": release.get("claim_boundary", {}),
        "license_rebinding": rebinding,
    }

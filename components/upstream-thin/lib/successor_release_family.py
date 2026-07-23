#!/usr/bin/env python3
"""Deterministic candidate release-family envelope for accepted RB-3 successor artifacts."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from archive import canonical_json_bytes, sha256_file, write_json
from release_family import archive_manifest, artifact_identity, license_inventory

ROOT = Path(__file__).resolve().parents[3]
RELEASE_ID = "cpython-3.14.6+e3-r2-aarch64-linux-android"
FLAVORS = ("full", "install_only", "install_only_stripped")
SIDECAR_KINDS = ("artifact", "manifest", "provenance", "qualification", "licenses", "attestation")
AUTHORITY_PATHS = {
    "full": "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-authority.json",
    "install_only": "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-authority.json",
    "install_only_stripped": "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-stripped-m-authority.json",
}
AUTHORIZATION_CONTRACT = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-technical-family-m-contract.json"
EXECUTION_CONTRACT = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-technical-family-m-r1-execution-contract.json"
PREDECESSOR_AUTHORITY = "experiments/epoch3-upstream-thin-artifact-family/artifact-family-authority.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def expected_family(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    contract = load_json(root / AUTHORIZATION_CONTRACT)
    accepted = contract.get("accepted_inputs", {})
    expected: dict[str, dict[str, Any]] = {}
    for flavor in FLAVORS:
        row = accepted.get(flavor)
        if not isinstance(row, dict):
            raise ValueError(f"missing accepted input: {flavor}")
        expected[flavor] = {key: row[key] for key in ("filename", "sha256", "size_bytes", "member_count")}
    return expected


def relationship(flavor: str) -> dict[str, Any]:
    if flavor == "full":
        return {
            "kind": "accepted-profile-M-successor-full",
            "source": "official-python.org-android-prebuilt",
            "accepted_product_bytes_unchanged": True,
        }
    if flavor == "install_only":
        return {
            "kind": "accepted-exact-projection",
            "source_flavor": "full",
            "source_prefix": "python/install/**",
            "target_prefix": "python/**",
            "payload_bytes_unchanged": True,
        }
    return {
        "kind": "accepted-bounded-strip-derivation",
        "source_flavor": "install_only",
        "operation": "llvm-strip --strip-unneeded",
        "changed_paths": ["bin/python3.14"],
        "non_elf_payload_unchanged": True,
        "dynamic_and_16k_alignment_preserved": True,
    }


def authority_binding(flavor: str, root: Path = ROOT) -> dict[str, Any]:
    rel = AUTHORITY_PATHS[flavor]
    path = root / rel
    authority = load_json(path)
    evidence = authority.get("accepted_evidence", {})
    return {
        "path": rel,
        "sha256": sha256_file(path),
        "authority_kind": authority.get("authority_kind"),
        "status": authority.get("status"),
        "owner_result_archive": {
            "filename": evidence.get("result_archive_filename"),
            "sha256": evidence.get("result_archive_sha256"),
            "size_bytes": evidence.get("result_archive_size"),
        },
    }


def family_bindings(root: Path = ROOT) -> dict[str, Any]:
    def binding(rel: str) -> dict[str, Any]:
        path = root / rel
        return {"path": rel, "sha256": sha256_file(path)}

    return {
        "authorization_contract": binding(AUTHORIZATION_CONTRACT),
        "execution_contract": binding(EXECUTION_CONTRACT),
        "predecessor_family_authority": binding(PREDECESSOR_AUTHORITY),
        "successor_artifact_authorities": {flavor: authority_binding(flavor, root) for flavor in FLAVORS},
    }


def candidate_claim_boundary() -> dict[str, Any]:
    return {
        "successor_technical_family_candidate": True,
        "successor_technical_family_accepted": False,
        "legal_family_integration_started": False,
        "predecessor_family_superseded": False,
        "rb1_rebound": False,
        "rb2_rebound": False,
        "rb3_closed": False,
        "selectable": False,
        "publication": False,
        "portable_user_built_wheel_claim": False,
        "user_built_wheel_repair": False,
        "user_built_wheel_postprocessing": "out-of-scope-external-tool-responsibility",
    }


def build_sidecars(
    flavor: str,
    archive: Path,
    manifest: list[dict[str, Any]],
    *,
    root: Path = ROOT,
) -> dict[str, dict[str, Any]]:
    identity = artifact_identity(archive)
    authority = authority_binding(flavor, root)
    claims = candidate_claim_boundary()
    manifest_document = {"schema_version": 1, "members": manifest}
    manifest_sha = hashlib.sha256(canonical_json_bytes(manifest_document)).hexdigest()
    artifact = {
        "schema_version": 1,
        "metadata_kind": "epoch3-rb3-successor-technical-family-artifact",
        "python_implementation": "cpython",
        "python_version": "3.14.6",
        "target_triple": "aarch64-linux-android",
        "android_abi": "arm64-v8a",
        "upstream_declared_api_floor": 24,
        "libc": "bionic",
        "profile": "M",
        "flavor": flavor,
        "archive": {**identity, "member_count": len(manifest)},
        "archive_root": "python/",
        "relationship": relationship(flavor),
        "accepted_authority": authority,
        "claim_boundary": claims,
    }
    provenance = {
        "schema_version": 1,
        "metadata_kind": "epoch3-rb3-successor-technical-family-provenance",
        "subject": identity,
        "native_producer": "Python.org CPython Android release with inherited BeeWare dependency products",
        "official_input": {
            "filename": "python-3.14.6-aarch64-linux-android.tar.gz",
            "sha256": "38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5",
            "size_bytes": 22358404,
        },
        "project_model": "upstream-thin",
        "selected_profile": "M",
        "relationship": relationship(flavor),
        "accepted_authority": authority,
        "producer_object_graph_available": False,
        "dependency_build_recipes_owned_by_project": False,
    }
    qualification = {
        "schema_version": 1,
        "metadata_kind": "epoch3-rb3-successor-technical-family-qualification",
        "subject": identity,
        "status": "accepted-profile-M-owner-termux-app-context",
        "accepted_authority": authority,
        "qualified": {
            "android_bionic_runtime": True,
            "fresh_extraction": True,
            "whole_prefix_relocation": True,
            "read_only_install": True,
            "subprocess_reentry": True,
            "pip_surface": True,
            "fresh_venv": True,
            "on_device_sdk_metadata": True,
            "uv_system_consumer": True,
            "uv_managed_consumer": True,
            "direct_native_extension_build_install_import": True,
            "managed_native_extension_build_install_import": True,
            "baseline_native_extension_load_alignment_16k": True,
        },
        "withheld": {
            "technical_family_acceptance": True,
            "legal_family_integration": True,
            "predecessor_supersession": True,
            "selectable": True,
            "publication": True,
            "api24_runtime": True,
            "actual_16k_runtime": True,
            "non_termux_context": True,
            "other_abis": True,
            "portable_user_built_wheel": True,
        },
    }
    licenses = {
        "schema_version": 1,
        "metadata_kind": "epoch3-rb3-successor-technical-family-archive-license-file-inventory",
        "subject": identity,
        "license_files": license_inventory(manifest),
        "archive_license_file_inventory_complete": True,
        "component_to_license_mapping_integrated_into_candidate": False,
        "legal_family_integration_started": False,
        "publication_blocked_pending_successor_legal_integration": True,
        "primary_python_license": "PSF-2.0",
    }
    attestation = {
        "schema_version": 1,
        "statement_kind": "epoch3-rb3-successor-technical-family-artifact-identity-attestation",
        "subject": [
            {
                "name": identity["filename"],
                "digest": {"sha256": identity["sha256"]},
                "size_bytes": identity["size_bytes"],
            }
        ],
        "predicate": {
            "accepted_authority": authority,
            "relationship": relationship(flavor),
            "manifest_sha256": manifest_sha,
            "claims": claims,
        },
    }
    return {
        "artifact": artifact,
        "manifest": {
            "schema_version": 1,
            "metadata_kind": "epoch3-rb3-successor-technical-family-archive-manifest",
            "subject": identity,
            "members": manifest,
        },
        "provenance": provenance,
        "qualification": qualification,
        "licenses": licenses,
        "attestation": attestation,
    }


def assemble_successor_release_family(
    full: Path,
    install_only: Path,
    stripped: Path,
    output_dir: Path,
    *,
    root: Path = ROOT,
    expected: dict[str, dict[str, Any]] | None = None,
    zstd: str = "zstd",
) -> dict[str, Any]:
    expected = expected or expected_family(root)
    inputs = {
        "full": full.resolve(),
        "install_only": install_only.resolve(),
        "install_only_stripped": stripped.resolve(),
    }
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    assets: list[dict[str, Any]] = []
    checksum_paths: list[Path] = []
    for flavor in FLAVORS:
        source = inputs[flavor]
        observed = artifact_identity(source)
        locked = expected[flavor]
        for key in ("filename", "sha256", "size_bytes"):
            if observed[key] != locked[key]:
                raise ValueError(f"{flavor} identity mismatch for {key}: {observed[key]} != {locked[key]}")
        destination = output_dir / source.name
        shutil.copyfile(source, destination)
        checksum_paths.append(destination)
        manifest = archive_manifest(destination, zstd=zstd)
        if len(manifest) != locked["member_count"]:
            raise ValueError(f"{flavor} member count mismatch: {len(manifest)} != {locked['member_count']}")
        sidecars = build_sidecars(flavor, destination, manifest, root=root)
        sidecar_rows: list[dict[str, Any]] = []
        for kind in SIDECAR_KINDS:
            path = output_dir / f"{source.name}.{kind}.json"
            write_json(path, sidecars[kind])
            checksum_paths.append(path)
            sidecar_rows.append({"kind": kind, **artifact_identity(path)})
        assets.append(
            {
                "flavor": flavor,
                "artifact": {**artifact_identity(destination), "member_count": len(manifest)},
                "relationship": relationship(flavor),
                "accepted_authority": authority_binding(flavor, root),
                "sidecars": sidecar_rows,
            }
        )
    sums = "".join(
        f"{sha256_file(path)}  {path.name}\n" for path in sorted(checksum_paths, key=lambda item: item.name)
    )
    (output_dir / "SHA256SUMS").write_text(sums, encoding="utf-8")
    release = {
        "release_id": RELEASE_ID,
        "python_version": "3.14.6",
        "target_triple": "aarch64-linux-android",
        "status": "successor-technical-family-candidate-unaccepted",
        "assets": assets,
        "family_invariants": {
            "full_first": True,
            "install_only_exact_full_projection": True,
            "stripped_exact_install_only_derivation": True,
            "accepted_product_bytes_reused_without_rewrite": True,
            "astral_archive_flavors": ["full", "install_only", "install_only_stripped"],
        },
        "bindings": family_bindings(root),
        "claim_boundary": candidate_claim_boundary(),
    }
    index = {
        "schema_version": 1,
        "index_kind": "epoch3-rb3-successor-technical-release-family",
        "release": release,
        "release_sha256": hashlib.sha256(canonical_json_bytes(release)).hexdigest(),
        "checksums": {"filename": "SHA256SUMS", "sha256": sha256_file(output_dir / "SHA256SUMS")},
    }
    write_json(output_dir / "release-index.json", index)
    inventory = [
        {"path": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        for path in sorted(output_dir.iterdir(), key=lambda item: item.name)
        if path.is_file()
    ]
    return {
        "schema_version": 1,
        "assembler_kind": "epoch3-rb3-successor-technical-release-family",
        "pass": True,
        "output_dir": str(output_dir),
        "release_id": RELEASE_ID,
        "release_index": artifact_identity(output_dir / "release-index.json"),
        "checksums": artifact_identity(output_dir / "SHA256SUMS"),
        "asset_count": len(assets),
        "file_count": len(inventory),
        "fingerprint_sha256": hashlib.sha256(canonical_json_bytes(inventory)).hexdigest(),
        "release_sha256": index["release_sha256"],
        "claim_boundary": release["claim_boundary"],
    }


def verify_successor_release_family(
    directory: Path,
    *,
    root: Path = ROOT,
    expected: dict[str, dict[str, Any]] | None = None,
    zstd: str = "zstd",
) -> dict[str, Any]:
    expected = expected or expected_family(root)
    checks: dict[str, bool] = {}
    errors: list[str] = []
    directory = directory.resolve()
    try:
        index = load_json(directory / "release-index.json")
        checks["release_index_parse"] = True
    except Exception as exc:  # noqa: BLE001
        index = {}
        checks["release_index_parse"] = False
        errors.append(f"{type(exc).__name__}: {exc}")
    release = index.get("release", {})
    checks["index_kind"] = index.get("index_kind") == "epoch3-rb3-successor-technical-release-family"
    checks["release_digest"] = bool(release) and index.get("release_sha256") == hashlib.sha256(canonical_json_bytes(release)).hexdigest()
    checks["release_identity"] = (
        release.get("release_id") == RELEASE_ID
        and release.get("target_triple") == "aarch64-linux-android"
        and release.get("python_version") == "3.14.6"
        and release.get("status") == "successor-technical-family-candidate-unaccepted"
    )
    checks["claims_bounded"] = release.get("claim_boundary") == candidate_claim_boundary()
    checks["bindings_exact"] = release.get("bindings") == family_bindings(root)
    assets = release.get("assets", [])
    checks["three_flavors"] = [row.get("flavor") for row in assets] == list(FLAVORS)
    expected_files = {"release-index.json", "SHA256SUMS"}
    checksum_targets: list[Path] = []
    asset_checks = True
    manifest_checks = True
    authority_checks = True
    relationship_checks = True
    claim_checks = True
    for row in assets:
        flavor = row.get("flavor")
        if flavor not in FLAVORS:
            asset_checks = False
            continue
        artifact = row.get("artifact", {})
        path = directory / artifact.get("filename", "")
        expected_files.add(path.name)
        if not path.is_file() or artifact_identity(path) != {
            key: artifact.get(key) for key in ("filename", "sha256", "size_bytes")
        }:
            asset_checks = False
        locked = expected[flavor]
        if any(artifact.get(key) != locked.get(key) for key in ("filename", "sha256", "size_bytes", "member_count")):
            asset_checks = False
        checksum_targets.append(path)
        if row.get("relationship") != relationship(flavor):
            relationship_checks = False
        binding = authority_binding(flavor, root)
        if row.get("accepted_authority") != binding:
            authority_checks = False
        sidecar_map = {entry.get("kind"): entry for entry in row.get("sidecars", [])}
        if set(sidecar_map) != set(SIDECAR_KINDS):
            asset_checks = False
            continue
        for kind in SIDECAR_KINDS:
            side = sidecar_map[kind]
            side_path = directory / side.get("filename", "")
            expected_files.add(side_path.name)
            checksum_targets.append(side_path)
            if not side_path.is_file() or artifact_identity(side_path) != {
                key: side.get(key) for key in ("filename", "sha256", "size_bytes")
            }:
                asset_checks = False
        try:
            manifest_doc = load_json(directory / sidecar_map["manifest"]["filename"])
            observed_manifest = archive_manifest(path, zstd=zstd)
            if manifest_doc.get("members") != observed_manifest or artifact.get("member_count") != len(observed_manifest):
                manifest_checks = False
            artifact_doc = load_json(directory / sidecar_map["artifact"]["filename"])
            provenance_doc = load_json(directory / sidecar_map["provenance"]["filename"])
            qualification_doc = load_json(directory / sidecar_map["qualification"]["filename"])
            licenses_doc = load_json(directory / sidecar_map["licenses"]["filename"])
            attestation_doc = load_json(directory / sidecar_map["attestation"]["filename"])
            if artifact_doc.get("relationship") != relationship(flavor) or provenance_doc.get("relationship") != relationship(flavor):
                relationship_checks = False
            if any(doc.get("accepted_authority") != binding for doc in (artifact_doc, provenance_doc, qualification_doc)):
                authority_checks = False
            if attestation_doc.get("predicate", {}).get("accepted_authority") != binding:
                authority_checks = False
            if artifact_doc.get("claim_boundary") != candidate_claim_boundary() or attestation_doc.get("predicate", {}).get("claims") != candidate_claim_boundary():
                claim_checks = False
            if qualification_doc.get("status") != "accepted-profile-M-owner-termux-app-context" or qualification_doc.get("withheld", {}).get("technical_family_acceptance") is not True:
                claim_checks = False
            expected_licenses = license_inventory(observed_manifest)
            if (
                licenses_doc.get("archive_license_file_inventory_complete") is not True
                or licenses_doc.get("component_to_license_mapping_integrated_into_candidate") is not False
                or licenses_doc.get("legal_family_integration_started") is not False
                or licenses_doc.get("license_files") != expected_licenses
            ):
                manifest_checks = False
            expected_manifest_digest = hashlib.sha256(
                canonical_json_bytes({"schema_version": 1, "members": observed_manifest})
            ).hexdigest()
            if attestation_doc.get("predicate", {}).get("manifest_sha256") != expected_manifest_digest:
                manifest_checks = False
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{flavor}: {type(exc).__name__}: {exc}")
            manifest_checks = authority_checks = relationship_checks = claim_checks = False
    checks["asset_identities"] = asset_checks
    checks["manifests_and_license_inventories"] = manifest_checks
    checks["successor_authority_bindings"] = authority_checks
    checks["relationships"] = relationship_checks
    checks["sidecar_claim_boundaries"] = claim_checks
    actual_files = {path.name for path in directory.iterdir() if path.is_file()} if directory.is_dir() else set()
    checks["exact_file_set"] = actual_files == expected_files and len(actual_files) == 23
    expected_sums = "".join(
        f"{sha256_file(path)}  {path.name}\n" for path in sorted(checksum_targets, key=lambda item: item.name)
    )
    sums_path = directory / "SHA256SUMS"
    checks["sha256sums_exact"] = sums_path.is_file() and sums_path.read_text(encoding="utf-8") == expected_sums
    checks["checksum_binding"] = sums_path.is_file() and index.get("checksums") == {
        "filename": "SHA256SUMS",
        "sha256": sha256_file(sums_path),
    }
    checks["accepted_artifact_bytes_present"] = all(
        (directory / row["filename"]).is_file()
        and sha256_file(directory / row["filename"]) == row["sha256"]
        and (directory / row["filename"]).stat().st_size == row["size_bytes"]
        for row in expected.values()
    )
    checks["predecessor_artifacts_absent"] = not any("full-r4" in name for name in actual_files)
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    inventory = [
        {"path": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        for path in sorted(directory.iterdir(), key=lambda item: item.name)
        if path.is_file()
    ] if directory.is_dir() else []
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-rb3-successor-technical-release-family",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "release_id": release.get("release_id"),
        "release_sha256": index.get("release_sha256"),
        "release_index": artifact_identity(directory / "release-index.json") if (directory / "release-index.json").is_file() else None,
        "checksums": artifact_identity(sums_path) if sums_path.is_file() else None,
        "file_count": len(inventory),
        "fingerprint_sha256": hashlib.sha256(canonical_json_bytes(inventory)).hexdigest() if inventory else None,
        "claim_boundary": release.get("claim_boundary"),
    }

#!/usr/bin/env python3
"""Deterministic release-family envelope for frozen upstream-thin artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any, BinaryIO

from archive import canonical_json_bytes, normalize_member_name, safe_link_target, sha256_file, write_json

ROOT = Path(__file__).resolve().parents[3]
FULL_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-full-r4.lock.json"
INSTALL_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-install-only-r1.lock.json"
STRIPPED_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-install-only-stripped-r2.lock.json"
FLAVORS = ("full", "install_only", "install_only_stripped")
SIDECAR_KINDS = ("artifact", "manifest", "provenance", "qualification", "licenses", "attestation")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def expected_family(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    full = load_json(root / FULL_LOCK.relative_to(ROOT))["artifact"]
    install = load_json(root / INSTALL_LOCK.relative_to(ROOT))["artifact"]
    stripped = load_json(root / STRIPPED_LOCK.relative_to(ROOT))["artifact"]
    return {"full": full, "install_only": install, "install_only_stripped": stripped}


def _sha_stream(stream: BinaryIO) -> str:
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def _open_tar(archive: Path, zstd: str = "zstd"):
    if archive.name.endswith(".tar.zst"):
        tmp = tempfile.NamedTemporaryFile(prefix="release-family-", suffix=".tar", delete=False)
        tmp_path = Path(tmp.name)
        tmp.close()
        with tmp_path.open("wb") as output_stream:
            proc = subprocess.run([zstd, "-q", "-d", "-c", str(archive)], stdout=output_stream, stderr=subprocess.PIPE)
        if proc.returncode:
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError(f"zstd decompression failed: {proc.stderr.decode(errors='replace').strip()}")
        tf = tarfile.open(tmp_path, "r:")
        return tf, tmp_path
    return tarfile.open(archive, "r:gz"), None


def archive_manifest(archive: Path, *, zstd: str = "zstd") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    tf, temporary = _open_tar(archive, zstd)
    try:
        for member in tf.getmembers():
            name = normalize_member_name(member.name)
            if name in seen:
                raise ValueError(f"duplicate member: {name}")
            seen.add(name)
            if member.islnk() or member.isdev() or member.isfifo() or not (member.isdir() or member.isfile() or member.issym()):
                raise ValueError(f"forbidden member type: {name}")
            if member.issym() and not safe_link_target(name, member.linkname):
                raise ValueError(f"unsafe symlink: {name} -> {member.linkname}")
            row = {
                "path": name,
                "type": "directory" if member.isdir() else "file" if member.isfile() else "symlink",
                "mode": f"{stat.S_IMODE(member.mode):04o}",
                "size_bytes": member.size if member.isfile() else 0,
                "sha256": None,
                "linkname": member.linkname if member.issym() else None,
            }
            if member.isfile():
                stream = tf.extractfile(member)
                if stream is None:
                    raise ValueError(f"cannot read member: {name}")
                row["sha256"] = _sha_stream(stream)
            rows.append(row)
    finally:
        tf.close()
        if temporary:
            temporary.unlink(missing_ok=True)
    return rows


def artifact_identity(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def license_inventory(manifest: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in manifest:
        if row["type"] != "file":
            continue
        base = Path(row["path"]).name.casefold()
        if base.startswith("license") or base.startswith("copying") or base.startswith("notice"):
            selected.append({key: row[key] for key in ("path", "size_bytes", "sha256")})
    return selected


def relationship(flavor: str) -> dict[str, Any]:
    if flavor == "full":
        return {"kind": "canonical-upstream-derived-full", "source": "official-python.org-android-prebuilt"}
    if flavor == "install_only":
        return {"kind": "exact-projection", "source_flavor": "full", "source_prefix": "python/install/**", "target_prefix": "python/**", "payload_bytes_unchanged": True}
    return {"kind": "bounded-strip-derivation", "source_flavor": "install_only", "operation": "--strip-unneeded", "changed_paths": ["bin/python3.14"], "non_elf_payload_unchanged": True}


def authority_binding(flavor: str, root: Path = ROOT) -> dict[str, Any]:
    mapping = {
        "full": "experiments/epoch3-upstream-thin-full/full-authority.json",
        "install_only": "experiments/epoch3-upstream-thin-install-only/install-only-authority.json",
        "install_only_stripped": "experiments/epoch3-upstream-thin-stripped/stripped-authority.json",
    }
    rel = mapping[flavor]
    path = root / rel
    return {"path": rel, "sha256": sha256_file(path)}


def build_sidecars(flavor: str, archive: Path, manifest: list[dict[str, Any]], *, root: Path = ROOT) -> dict[str, dict[str, Any]]:
    identity = artifact_identity(archive)
    authority = authority_binding(flavor, root)
    common_claims = {
        "artifact_qualified": True,
        "selectable": False,
        "publication": False,
        "api24_runtime": False,
        "actual_16k_runtime": False,
        "non_termux_context": False,
    }
    artifact = {
        "schema_version": 1,
        "metadata_kind": "epoch3-upstream-thin-artifact",
        "python_implementation": "cpython",
        "python_version": "3.14.6",
        "target_triple": "aarch64-linux-android",
        "android_abi": "arm64-v8a",
        "upstream_declared_api_floor": 24,
        "libc": "bionic",
        "flavor": flavor,
        "archive": {**identity, "member_count": len(manifest)},
        "archive_root": "python/",
        "relationship": relationship(flavor),
        "authority": authority,
        "claim_boundary": common_claims,
    }
    provenance = {
        "schema_version": 1,
        "metadata_kind": "epoch3-upstream-thin-provenance",
        "subject": identity,
        "native_producer": "Python.org CPython Android release with inherited BeeWare dependency products",
        "official_input": {
            "filename": "python-3.14.6-aarch64-linux-android.tar.gz",
            "sha256": "38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5",
            "size_bytes": 22358404,
        },
        "project_model": "upstream-thin",
        "relationship": relationship(flavor),
        "authority": authority,
        "producer_object_graph_available": False,
        "dependency_build_recipes_owned_by_project": False,
    }
    qualification = {
        "schema_version": 1,
        "metadata_kind": "epoch3-upstream-thin-qualification",
        "subject": identity,
        "status": "passed-bounded-current-owner-termux-app-context",
        "authority": authority,
        "qualified": {
            "android_bionic_runtime": True,
            "fresh_extraction": True,
            "whole_prefix_relocation": True,
            "read_only_install": True,
            "native_extension_count": 67,
            "subprocess_reentry": True,
            "pip_surface": True,
            "fresh_venv": True,
            "on_device_sdk_metadata": True,
        },
        "withheld": {
            "selectable": True,
            "publication": True,
            "api24_runtime": True,
            "actual_16k_runtime": True,
            "non_termux_context": True,
            "other_abis": True,
        },
    }
    licenses = {
        "schema_version": 1,
        "metadata_kind": "epoch3-upstream-thin-archive-license-file-inventory",
        "subject": identity,
        "license_files": license_inventory(manifest),
        "archive_license_file_inventory_complete": True,
        "component_to_license_mapping_complete": False,
        "publication_blocked_pending_component_mapping": True,
        "primary_python_license": "PSF-2.0",
    }
    attestation = {
        "schema_version": 1,
        "statement_kind": "epoch3-upstream-thin-artifact-identity-attestation",
        "subject": [{"name": identity["filename"], "digest": {"sha256": identity["sha256"]}, "size_bytes": identity["size_bytes"]}],
        "predicate": {
            "authority": authority,
            "relationship": relationship(flavor),
            "manifest_sha256": hashlib.sha256(canonical_json_bytes({"schema_version": 1, "members": manifest})).hexdigest(),
            "claims": common_claims,
        },
    }
    return {
        "artifact": artifact,
        "manifest": {"schema_version": 1, "metadata_kind": "epoch3-upstream-thin-archive-manifest", "subject": identity, "members": manifest},
        "provenance": provenance,
        "qualification": qualification,
        "licenses": licenses,
        "attestation": attestation,
    }


def assemble_release_family(
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
    inputs = {"full": full.resolve(), "install_only": install_only.resolve(), "install_only_stripped": stripped.resolve()}
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
        if "member_count" in locked and len(manifest) != locked["member_count"]:
            raise ValueError(f"{flavor} member count mismatch")
        sidecars = build_sidecars(flavor, destination, manifest, root=root)
        sidecar_rows = []
        prefix = source.name
        for kind in SIDECAR_KINDS:
            path = output_dir / f"{prefix}.{kind}.json"
            write_json(path, sidecars[kind])
            checksum_paths.append(path)
            sidecar_rows.append({"kind": kind, **artifact_identity(path)})
        assets.append({
            "flavor": flavor,
            "artifact": {**artifact_identity(destination), "member_count": len(manifest)},
            "relationship": relationship(flavor),
            "sidecars": sidecar_rows,
        })
    sums = "".join(f"{sha256_file(path)}  {path.name}\n" for path in sorted(checksum_paths, key=lambda p: p.name))
    (output_dir / "SHA256SUMS").write_text(sums, encoding="utf-8")
    release = {
        "release_id": "cpython-3.14.6+e3-r1-aarch64-linux-android",
        "python_version": "3.14.6",
        "target_triple": "aarch64-linux-android",
        "status": "qualified-unselectable-unpublished",
        "assets": assets,
        "family_invariants": {
            "full_first": True,
            "install_only_exact_full_projection": True,
            "stripped_exact_install_only_derivation": True,
            "astral_archive_flavors": ["full", "install_only", "install_only_stripped"],
        },
        "claim_boundary": {
            "artifact_family_complete": True,
            "selectable": False,
            "publication": False,
            "component_license_mapping_complete": False,
            "api24_runtime": False,
            "actual_16k_runtime": False,
            "non_termux_context": False,
        },
    }
    index = {
        "schema_version": 1,
        "index_kind": "epoch3-upstream-thin-release-family",
        "release": release,
        "release_sha256": hashlib.sha256(canonical_json_bytes(release)).hexdigest(),
        "checksums": {"filename": "SHA256SUMS", "sha256": sha256_file(output_dir / "SHA256SUMS")},
    }
    write_json(output_dir / "release-index.json", index)
    return {
        "schema_version": 1,
        "assembler_kind": "epoch3-upstream-thin-release-family",
        "pass": True,
        "output_dir": str(output_dir),
        "release_index": artifact_identity(output_dir / "release-index.json"),
        "checksums": artifact_identity(output_dir / "SHA256SUMS"),
        "asset_count": len(assets),
        "file_count": len([p for p in output_dir.iterdir() if p.is_file()]),
        "release_sha256": index["release_sha256"],
        "claim_boundary": release["claim_boundary"],
    }


def verify_release_family(
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
    checks["release_digest"] = index.get("release_sha256") == hashlib.sha256(canonical_json_bytes(release)).hexdigest() if release else False
    checks["release_identity"] = release.get("release_id") == "cpython-3.14.6+e3-r1-aarch64-linux-android" and release.get("target_triple") == "aarch64-linux-android" and release.get("python_version") == "3.14.6"
    checks["claims_bounded"] = release.get("status") == "qualified-unselectable-unpublished" and release.get("claim_boundary", {}).get("artifact_family_complete") is True and release.get("claim_boundary", {}).get("selectable") is False and release.get("claim_boundary", {}).get("publication") is False and release.get("claim_boundary", {}).get("component_license_mapping_complete") is False
    assets = release.get("assets", [])
    checks["three_flavors"] = [row.get("flavor") for row in assets] == list(FLAVORS)
    expected_files = {"release-index.json", "SHA256SUMS"}
    checksum_targets: list[Path] = []
    asset_checks = True
    manifest_checks = True
    authority_checks = True
    relationship_checks = True
    for row in assets:
        flavor = row.get("flavor")
        if flavor not in FLAVORS:
            asset_checks = False
            continue
        artifact = row.get("artifact", {})
        path = directory / artifact.get("filename", "")
        expected_files.add(path.name)
        if not path.is_file() or artifact_identity(path) != {key: artifact.get(key) for key in ("filename", "sha256", "size_bytes")}:
            asset_checks = False
        locked = expected[flavor]
        if any(artifact.get(key) != locked.get(key) for key in ("filename", "sha256", "size_bytes", "member_count")):
            asset_checks = False
        checksum_targets.append(path)
        if row.get("relationship") != relationship(flavor):
            relationship_checks = False
        sidecar_map = {entry.get("kind"): entry for entry in row.get("sidecars", [])}
        if set(sidecar_map) != set(SIDECAR_KINDS):
            asset_checks = False
            continue
        for kind in SIDECAR_KINDS:
            side = sidecar_map[kind]
            side_path = directory / side.get("filename", "")
            expected_files.add(side_path.name)
            checksum_targets.append(side_path)
            if not side_path.is_file() or artifact_identity(side_path) != {key: side.get(key) for key in ("filename", "sha256", "size_bytes")}:
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
            if artifact_doc.get("relationship") != relationship(flavor) or artifact_doc.get("claim_boundary", {}).get("selectable") is not False:
                relationship_checks = False
            binding = authority_binding(flavor, root)
            if any(doc.get("authority") != binding for doc in (artifact_doc, provenance_doc, qualification_doc)) or attestation_doc.get("predicate", {}).get("authority") != binding:
                authority_checks = False
            expected_licenses = license_inventory(observed_manifest)
            if licenses_doc.get("archive_license_file_inventory_complete") is not True or licenses_doc.get("component_to_license_mapping_complete") is not False or licenses_doc.get("license_files") != expected_licenses:
                manifest_checks = False
            expected_manifest_digest = hashlib.sha256(canonical_json_bytes({"schema_version": 1, "members": observed_manifest})).hexdigest()
            if attestation_doc.get("predicate", {}).get("manifest_sha256") != expected_manifest_digest:
                manifest_checks = False
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{flavor}: {type(exc).__name__}: {exc}")
            manifest_checks = False
    checks["asset_identities"] = asset_checks
    checks["manifest_exact"] = manifest_checks
    checks["authority_bindings"] = authority_checks
    checks["flavor_relationships"] = relationship_checks
    actual_files = {p.name for p in directory.iterdir() if p.is_file()}
    checks["exact_file_set"] = actual_files == expected_files
    checksum_targets_exist = all(path.is_file() for path in checksum_targets)
    expected_sums = "".join(f"{sha256_file(path)}  {path.name}\n" for path in sorted(checksum_targets, key=lambda p: p.name)) if checksum_targets_exist else ""
    checks["sha256sums_exact"] = checksum_targets_exist and (directory / "SHA256SUMS").is_file() and (directory / "SHA256SUMS").read_text(encoding="utf-8") == expected_sums
    checks["checksum_binding"] = index.get("checksums") == {"filename": "SHA256SUMS", "sha256": sha256_file(directory / "SHA256SUMS")} if (directory / "SHA256SUMS").is_file() else False
    failed = sorted(key for key, value in checks.items() if value is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-upstream-thin-release-family",
        "pass": not failed and not errors,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "release_index": artifact_identity(directory / "release-index.json") if (directory / "release-index.json").is_file() else None,
        "release_sha256": index.get("release_sha256"),
        "claim_boundary": release.get("claim_boundary", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    assemble = sub.add_parser("assemble")
    assemble.add_argument("--full", required=True)
    assemble.add_argument("--install-only", required=True)
    assemble.add_argument("--stripped", required=True)
    assemble.add_argument("--output-dir", required=True)
    assemble.add_argument("--zstd", default="zstd")
    verify = sub.add_parser("verify")
    verify.add_argument("directory")
    verify.add_argument("--zstd", default="zstd")
    args = parser.parse_args()
    if args.command == "assemble":
        result = assemble_release_family(Path(args.full), Path(args.install_only), Path(args.stripped), Path(args.output_dir), zstd=args.zstd)
    else:
        result = verify_release_family(Path(args.directory), zstd=args.zstd)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Evidence-only component and license census for a frozen release family.

This module intentionally does not turn upstream knowledge into a legal claim.
Only evidence present in the frozen artifact family or the repository license is
recorded as authoritative. Missing component license payloads remain gaps.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from archive import sha256_file, write_json
from release_family import _open_tar, expected_family, verify_release_family

ROOT = Path(__file__).resolve().parents[3]
FAMILY_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-artifact-family-r1.lock.json"
EXPECTED_CLASSES = (
    "cpython", "project-launcher", "pip", "openssl", "sqlite", "bzip2",
    "xz-liblzma", "zstd", "expat", "libmpdec", "libffi", "android-system-providers",
)
TARGET_MEMBERS = {
    "python/PYTHON.json",
    "python/install/lib/python3.14/build-details.json",
    "python/install/lib/pkgconfig/openssl.pc",
    "python/install/lib/pkgconfig/sqlite3.pc",
    "python/install/include/openssl/opensslv.h",
    "python/install/include/sqlite3.h",
    "python/install/lib/python3.14/site-packages/pip-26.1.2.dist-info/METADATA",
    "python/install/lib/python3.14/lib-dynload/_bz2.cpython-314-aarch64-linux-android.so",
    "python/install/lib/python3.14/lib-dynload/_lzma.cpython-314-aarch64-linux-android.so",
    "python/install/lib/python3.14/lib-dynload/_zstd.cpython-314-aarch64-linux-android.so",
    "python/install/lib/python3.14/lib-dynload/pyexpat.cpython-314-aarch64-linux-android.so",
    "python/install/lib/python3.14/lib-dynload/_decimal.cpython-314-aarch64-linux-android.so",
    "python/install/lib/python3.14/lib-dynload/_ctypes.cpython-314-aarch64-linux-android.so",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _license_like(path: str) -> bool:
    name = Path(path).name.casefold()
    return name.startswith(("license", "copying", "notice", "authors"))


def _evidence(path: str, data: bytes, kind: str, detail: str) -> dict[str, Any]:
    return {
        "path": path,
        "kind": kind,
        "detail": detail,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
    }


def _text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _match(pattern: str, data: bytes, *, flags: int = 0) -> str | None:
    found = re.search(pattern.encode(), data, flags)
    return found.group(1).decode(errors="replace") if found else None


def _version_from_pc(data: bytes) -> str | None:
    return _match(r"(?m)^Version:\s*([^\r\n]+)", data)


def _system_links(python_json: dict[str, Any]) -> list[str]:
    names: set[str] = set()
    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("system") is True and isinstance(value.get("name"), str):
                names.add(value["name"])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(python_json)
    return sorted(names)


def collect_archive_evidence(full_archive: Path, *, zstd: str = "zstd") -> tuple[dict[str, bytes], list[dict[str, Any]]]:
    selected: dict[str, bytes] = {}
    licenses: list[dict[str, Any]] = []
    tf, temporary = _open_tar(full_archive, zstd)
    try:
        for member in tf.getmembers():
            path = member.name.rstrip("/")
            if not member.isfile() or (path not in TARGET_MEMBERS and not _license_like(path)):
                continue
            stream = tf.extractfile(member)
            if stream is None:
                raise ValueError(f"cannot read member: {path}")
            data = stream.read()
            if path in TARGET_MEMBERS:
                selected[path] = data
            if _license_like(path):
                licenses.append({
                    "path": path,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "size_bytes": len(data),
                })
    finally:
        tf.close()
        if temporary:
            temporary.unlink(missing_ok=True)
    missing = sorted(TARGET_MEMBERS - selected.keys())
    if missing:
        raise ValueError(f"required evidence members missing: {missing}")
    return selected, sorted(licenses, key=lambda row: row["path"])


def analyze_evidence(members: dict[str, bytes], archive_licenses: list[dict[str, Any]], repository_license: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pyjson_path = "python/PYTHON.json"
    pyjson = json.loads(_text(members[pyjson_path]))
    pip_meta_path = "python/install/lib/python3.14/site-packages/pip-26.1.2.dist-info/METADATA"
    pip_meta = members[pip_meta_path]
    pip_version = _match(r"(?m)^Version:\s*([^\r\n]+)", pip_meta)
    pip_expression = _match(r"(?m)^License-Expression:\s*([^\r\n]+)", pip_meta)
    openssl_pc_path = "python/install/lib/pkgconfig/openssl.pc"
    sqlite_pc_path = "python/install/lib/pkgconfig/sqlite3.pc"
    openssl_header_path = "python/install/include/openssl/opensslv.h"
    sqlite_header_path = "python/install/include/sqlite3.h"
    binary_paths = {
        "bzip2": "python/install/lib/python3.14/lib-dynload/_bz2.cpython-314-aarch64-linux-android.so",
        "xz-liblzma": "python/install/lib/python3.14/lib-dynload/_lzma.cpython-314-aarch64-linux-android.so",
        "zstd": "python/install/lib/python3.14/lib-dynload/_zstd.cpython-314-aarch64-linux-android.so",
        "expat": "python/install/lib/python3.14/lib-dynload/pyexpat.cpython-314-aarch64-linux-android.so",
        "libmpdec": "python/install/lib/python3.14/lib-dynload/_decimal.cpython-314-aarch64-linux-android.so",
        "libffi": "python/install/lib/python3.14/lib-dynload/_ctypes.cpython-314-aarch64-linux-android.so",
    }
    version_patterns = {
        "bzip2": rb"\b(1\.0\.8)\b",
        "xz-liblzma": rb"\b(5\.4\.6)\b",
        "zstd": rb"\b(1\.5\.7)\b",
        "expat": rb"expat_(2\.8\.1)",
        "libmpdec": rb"\b(2\.5\.1)\b",
    }
    license_paths = {row["path"] for row in archive_licenses}
    cpython_license = "python/install/lib/python3.14/LICENSE.txt"
    pip_license_prefix = "python/install/lib/python3.14/site-packages/pip-26.1.2.dist-info/licenses/"
    repo_license_data = repository_license.read_bytes()
    components: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    def component(cid: str, *, distribution: str, version: str | None, version_status: str, evidence: list[dict[str, Any]], license_status: str, expressions: list[str], license_evidence: list[str], gap_codes: list[str]) -> None:
        row = {
            "component_class": cid,
            "distribution": distribution,
            "version": version,
            "version_status": version_status,
            "evidence": evidence,
            "license_mapping": {
                "status": license_status,
                "expressions": expressions,
                "evidence_paths": sorted(license_evidence),
                "gap_codes": gap_codes,
            },
        }
        components.append(row)
        for code in gap_codes:
            gaps.append({"component_class": cid, "code": code, "blocking": True})

    build_path = "python/install/lib/python3.14/build-details.json"
    component("cpython", distribution="distributed", version="3.14.6", version_status="exact",
              evidence=[_evidence(pyjson_path, members[pyjson_path], "machine-metadata", "Astral-format product metadata"), _evidence(build_path, members[build_path], "machine-metadata", "runtime build details")],
              license_status="partial", expressions=["PSF-2.0"], license_evidence=[cpython_license] if cpython_license in license_paths else [],
              gap_codes=["cpython-bundled-third-party-license-sections-not-componentized"])
    component("project-launcher", distribution="distributed", version="LA-2", version_status="exact",
              evidence=[{"path":"python/install/bin/python3.14","kind":"project-owned-binary","detail":"standalone Py_BytesMain launcher; identity frozen by full authority"}],
              license_status="missing-from-release-family", expressions=["MIT"],
              license_evidence=[{"path":"LICENSE","sha256":hashlib.sha256(repo_license_data).hexdigest(),"size_bytes":len(repo_license_data),"scope":"repository-not-release-family"}],
              gap_codes=["project-license-not-in-release-family"])
    pip_license_paths = sorted(p for p in license_paths if p.startswith(pip_license_prefix))
    component("pip", distribution="distributed", version=pip_version, version_status="exact" if pip_version else "unresolved",
              evidence=[_evidence(pip_meta_path, pip_meta, "core-metadata", "pip package metadata and declared license files")],
              license_status="complete-package-metadata-candidate" if pip_expression and pip_license_paths else "partial",
              expressions=[pip_expression] if pip_expression else [], license_evidence=pip_license_paths,
              gap_codes=[] if pip_expression and pip_license_paths else ["pip-license-metadata-incomplete"])
    openssl_header = members[openssl_header_path]
    openssl_expression = "Apache-2.0" if b"Apache License 2.0" in openssl_header else None
    component("openssl", distribution="distributed-inherited-beeware-product", version=_version_from_pc(members[openssl_pc_path]), version_status="exact",
              evidence=[_evidence(openssl_pc_path, members[openssl_pc_path], "pkg-config", "OpenSSL version"), _evidence(openssl_header_path, openssl_header, "header", "upstream copyright and license reference")],
              license_status="inline-reference-only", expressions=[openssl_expression] if openssl_expression else [], license_evidence=[],
              gap_codes=["openssl-license-text-not-packaged"])
    sqlite_header = members[sqlite_header_path]
    sqlite_statement = "public-domain-dedication" if b"author disclaims copyright" in sqlite_header else None
    component("sqlite", distribution="distributed-inherited-beeware-product", version=_version_from_pc(members[sqlite_pc_path]), version_status="exact",
              evidence=[_evidence(sqlite_pc_path, members[sqlite_pc_path], "pkg-config", "SQLite version"), _evidence(sqlite_header_path, sqlite_header, "header", "public-domain dedication text")],
              license_status="inline-statement-candidate", expressions=[sqlite_statement] if sqlite_statement else [], license_evidence=[sqlite_header_path] if sqlite_statement else [],
              gap_codes=["sqlite-notice-policy-not-frozen"])
    for cid in ("bzip2", "xz-liblzma", "zstd", "expat", "libmpdec"):
        path = binary_paths[cid]; data = members[path]
        found = re.search(version_patterns[cid], data)
        version = found.group(1).decode() if found else None
        component(cid, distribution="embedded-in-cpython-extension", version=version, version_status="exact-binary-string" if version else "unresolved",
                  evidence=[_evidence(path, data, "embedded-binary-string", "component version marker in extension binary")],
                  license_status="unmapped", expressions=[], license_evidence=[], gap_codes=[f"{cid}-license-evidence-not-packaged"])
    ffi_path = binary_paths["libffi"]
    component("libffi", distribution="embedded-in-cpython-extension", version=None, version_status="unresolved",
              evidence=[_evidence(ffi_path, members[ffi_path], "extension-binary", "libffi-backed ctypes extension; no reliable libffi version marker established")],
              license_status="unmapped", expressions=[], license_evidence=[], gap_codes=["libffi-version-unresolved", "libffi-license-evidence-not-packaged"])
    system_links = _system_links(pyjson)
    component("android-system-providers", distribution="external-not-distributed", version=None, version_status="platform-provided",
              evidence=[{"path":pyjson_path,"kind":"machine-metadata","detail":"system=true link providers","providers":system_links}],
              license_status="external-provider-boundary", expressions=[], license_evidence=[], gap_codes=["android-system-provider-notice-boundary-not-frozen"])
    components.sort(key=lambda row: EXPECTED_CLASSES.index(row["component_class"]))
    gaps.sort(key=lambda row:(EXPECTED_CLASSES.index(row["component_class"]),row["code"]))
    return components, gaps


def census_release_family(family_dir: Path, output_dir: Path, *, root: Path = ROOT, zstd: str = "zstd") -> dict[str, Any]:
    lock = load_json(root / FAMILY_LOCK.relative_to(ROOT))
    verification = verify_release_family(family_dir, root=root, zstd=zstd)
    if not verification.get("pass"):
        raise ValueError(f"release family verification failed: {verification.get('errors')}")
    full_expected = expected_family(root)["full"]
    full_archive = family_dir / full_expected["filename"]
    before = {"sha256": sha256_file(full_archive), "size_bytes": full_archive.stat().st_size}
    members, license_files = collect_archive_evidence(full_archive, zstd=zstd)
    components, gaps = analyze_evidence(members, license_files, root / "LICENSE")
    after = {"sha256": sha256_file(full_archive), "size_bytes": full_archive.stat().st_size}
    if before != after:
        raise RuntimeError("frozen full artifact changed during census")
    observed_classes = [row["component_class"] for row in components]
    if observed_classes != list(EXPECTED_CLASSES):
        raise ValueError(f"component class mismatch: {observed_classes}")
    output_dir.mkdir(parents=True, exist_ok=True)
    census = {
        "schema_version": 1,
        "census_kind": "epoch3-frozen-artifact-family-component-license-baseline",
        "family": {
            "release_id": lock["release_family"]["release_id"],
            "fingerprint_sha256": lock["release_family"]["fingerprint_sha256"],
            "file_count": lock["release_family"]["file_count"],
        },
        "subject": {"filename": full_archive.name, **before},
        "components": components,
        "archive_license_files": license_files,
        "summary": {
            "component_count": len(components),
            "exact_version_count": sum(row["version_status"].startswith("exact") for row in components),
            "unresolved_version_components": [row["component_class"] for row in components if row["version_status"] == "unresolved"],
            "components_with_blocking_gaps": sorted({row["component_class"] for row in gaps}, key=EXPECTED_CLASSES.index),
            "blocking_gap_count": len(gaps),
            "component_to_license_mapping_complete": False,
        },
        "claim_boundary": {"artifact_bytes_mutated": False, "component_license_mapping_complete": False, "selectable": False, "publication": False},
    }
    gap_register = {
        "schema_version": 1,
        "register_kind": "epoch3-component-license-gap-register",
        "family_fingerprint_sha256": lock["release_family"]["fingerprint_sha256"],
        "gaps": gaps,
        "blocking_gap_count": len(gaps),
        "closure_status": "incomplete",
        "next_actions": [
            "acquire-versioned-license-texts-from-authoritative-upstream-sources",
            "resolve-libffi-version-from-beeware-producer-provenance-or-binary-equivalent-evidence",
            "add-project-license-and-required-notices-to-release-family-metadata-layer",
            "freeze-component-to-license-and-notice-mapping-before-selectability",
        ],
        "claim_boundary": {"component_license_mapping_complete": False, "selectable": False, "publication": False},
    }
    write_json(output_dir / "component-census.json", census)
    write_json(output_dir / "license-gap-register.json", gap_register)
    result = {
        "schema_version": 1,
        "runner_kind": "epoch3-release-blocker-component-license-baseline",
        "pass": True,
        "outputs": {
            "component_census": "component-census.json",
            "license_gap_register": "license-gap-register.json",
        },
        "metrics": census["summary"],
        "full_artifact_identity_preserved": before == after,
        "claim_boundary": census["claim_boundary"],
    }
    write_json(output_dir / "baseline-result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--root", default=ROOT, type=Path)
    parser.add_argument("--zstd", default="zstd")
    args = parser.parse_args()
    try:
        result = census_release_family(args.family_dir.resolve(), args.output_dir.resolve(), root=args.root.resolve(), zstd=args.zstd)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"schema_version":1,"runner_kind":"epoch3-release-blocker-component-license-baseline","pass":False,"error":f"{type(exc).__name__}: {exc}"}, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

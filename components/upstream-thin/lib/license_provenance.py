#!/usr/bin/env python3
"""Resolve RB-1 source provenance without changing frozen artifact bytes."""
from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import stat
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from archive import normalize_member_name, safe_link_target, sha256_file, write_json
from release_family import _open_tar, expected_family, verify_release_family

ROOT = Path(__file__).resolve().parents[3]
FAMILY_FINGERPRINT = "87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302"
FULL_SHA256 = "20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12"
OFFICIAL_ANDROID = {
    "filename": "python-3.14.6-aarch64-linux-android.tar.gz",
    "sha256": "38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5",
    "size_bytes": 22358404,
}
CPYTHON_SOURCE = {
    "filename": "Python-3.14.6.tgz",
    "sha256": "74d0d71d0600e477651a077101d6e62d1e2e69b8e992ba18c993dd643b7ba222",
    "size_bytes": 31234628,
    "url": "https://www.python.org/ftp/python/3.14.6/Python-3.14.6.tgz",
}
DEPENDENCY_NAMES = ("bzip2", "libffi", "openssl", "sqlite", "xz", "zstd")
BASELINE_GAP_SHA256 = "9ac84e6c625d1bdeadd1cbe2a87f1947af4e05aebdabb5a64ed2c11b348c7f01"


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_full_members(full: Path, wanted: set[str], *, zstd: str) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    tf, temporary = _open_tar(full, zstd)
    try:
        seen: set[str] = set()
        for member in tf.getmembers():
            name = normalize_member_name(member.name)
            if name in seen:
                raise ValueError(f"duplicate full member: {name}")
            seen.add(name)
            if name not in wanted:
                continue
            if not member.isfile():
                raise ValueError(f"required full member is not regular: {name}")
            stream = tf.extractfile(member)
            if stream is None:
                raise ValueError(f"cannot read full member: {name}")
            result[name] = stream.read()
    finally:
        tf.close()
        if temporary:
            temporary.unlink(missing_ok=True)
    missing = sorted(wanted - set(result))
    if missing:
        raise ValueError(f"missing full members: {missing}")
    return result


def _safe_tar_rows(tf: tarfile.TarFile) -> list[tarfile.TarInfo]:
    rows: list[tarfile.TarInfo] = []
    seen: set[str] = set()
    for member in tf.getmembers():
        name = normalize_member_name(member.name)
        if name in seen:
            raise ValueError(f"duplicate source member: {name}")
        seen.add(name)
        if member.islnk() or member.isdev() or member.isfifo() or not (member.isdir() or member.isfile() or member.issym()):
            raise ValueError(f"forbidden source member type: {name}")
        if member.issym() and not safe_link_target(name, member.linkname):
            raise ValueError(f"unsafe source symlink: {name} -> {member.linkname}")
        rows.append(member)
    return rows


def _read_nested_android(package: bytes) -> bytes:
    if _sha_bytes(package) != OFFICIAL_ANDROID["sha256"] or len(package) != OFFICIAL_ANDROID["size_bytes"]:
        raise ValueError("nested official Android package identity mismatch")
    with tarfile.open(fileobj=io.BytesIO(package), mode="r:gz") as tf:
        _safe_tar_rows(tf)
        matches = [m for m in tf.getmembers() if normalize_member_name(m.name) == "android.py"]
        if len(matches) != 1 or not matches[0].isfile():
            raise ValueError("nested official Android android.py missing or ambiguous")
        stream = tf.extractfile(matches[0])
        if stream is None:
            raise ValueError("cannot read nested android.py")
        return stream.read()


def parse_dependency_pins(android_py: bytes) -> dict[str, dict[str, Any]]:
    text = android_py.decode("utf-8")
    found = re.findall(r'"((?:bzip2|libffi|openssl|sqlite|xz|zstd)-[^"\n]+-\d+)"', text)
    if len(found) != len(DEPENDENCY_NAMES) or len(set(found)) != len(found):
        raise ValueError(f"unexpected dependency pin set: {found}")
    result: dict[str, dict[str, Any]] = {}
    for tag in found:
        match = re.fullmatch(r"(bzip2|libffi|openssl|sqlite|xz|zstd)-(.+)-(\d+)", tag)
        if not match:
            raise ValueError(f"cannot parse dependency tag: {tag}")
        name, version, build = match.groups()
        if name in result:
            raise ValueError(f"duplicate dependency component: {name}")
        result[name] = {
            "component": name,
            "version": version,
            "build_revision": int(build),
            "release_tag": tag,
            "aarch64_asset": f"{tag}-aarch64-linux-android.tar.gz",
            "release_url": f"https://github.com/beeware/cpython-android-source-deps/releases/download/{tag}/{tag}-aarch64-linux-android.tar.gz",
        }
    if set(result) != set(DEPENDENCY_NAMES):
        raise ValueError(f"dependency names mismatch: {sorted(result)}")
    return dict(sorted(result.items()))


def _spdx_checksum(package: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in package.get("checksums", []) or []:
        if isinstance(item, dict) and isinstance(item.get("algorithm"), str) and isinstance(item.get("checksumValue"), str):
            result[item["algorithm"].upper()] = item["checksumValue"]
    return dict(sorted(result.items()))


def _spdx_packages(document: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for package in document.get("packages", []) or []:
        if not isinstance(package, dict):
            continue
        rows.append({
            "name": package.get("name"),
            "version": package.get("versionInfo"),
            "download_location": package.get("downloadLocation"),
            "checksums": _spdx_checksum(package),
            "license_concluded": package.get("licenseConcluded"),
            "license_declared": package.get("licenseDeclared"),
            "copyright_text": package.get("copyrightText"),
            "spdx_id": package.get("SPDXID"),
        })
    rows.sort(key=lambda row: (str(row.get("name", "")).casefold(), str(row.get("version", ""))))
    return rows


def _selected_source_license(name: str) -> bool:
    parts = Path(name).parts
    base = Path(name).name.casefold()
    if not (base.startswith("license") or base.startswith("copying") or base.startswith("notice") or base.startswith("copyright")):
        return False
    if len(parts) == 2 and parts[1] == "LICENSE":
        return True
    lowered = "/".join(parts).casefold()
    return any(token in lowered for token in (
        "/modules/expat/", "/modules/_decimal/", "/modules/_ctypes/", "/modules/_sqlite/",
        "/modules/_bz2/", "/modules/_lzma/", "/modules/_zstd/", "/misc/",
    ))


def inspect_cpython_source(source: Path, evidence_dir: Path, *, expected: dict[str, Any] = CPYTHON_SOURCE) -> dict[str, Any]:
    identity = {"filename": source.name, "sha256": sha256_file(source), "size_bytes": source.stat().st_size, "url": expected["url"]}
    for key in ("filename", "sha256", "size_bytes"):
        if identity[key] != expected[key]:
            raise ValueError(f"CPython source {key} mismatch: {identity[key]} != {expected[key]}")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(source, "r:gz") as tf:
        rows = _safe_tar_rows(tf)
        names = {normalize_member_name(m.name): m for m in rows}
        root = "Python-3.14.6"
        spdx_name = f"{root}/Misc/externals.spdx.json"
        license_name = f"{root}/LICENSE"
        for required in (spdx_name, license_name):
            if required not in names or not names[required].isfile():
                raise ValueError(f"required CPython source evidence missing: {required}")
        evidence: list[dict[str, Any]] = []
        selected = [name for name, member in names.items() if member.isfile() and (name in {spdx_name, license_name} or _selected_source_license(name))]
        for name in sorted(set(selected)):
            stream = tf.extractfile(names[name])
            if stream is None:
                raise ValueError(f"cannot read source evidence: {name}")
            data = stream.read()
            relative = name.removeprefix(root + "/")
            destination = evidence_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            evidence.append({"source_path": name, "evidence_path": relative, "sha256": _sha_bytes(data), "size_bytes": len(data)})
    spdx = json.loads((evidence_dir / "Misc/externals.spdx.json").read_text(encoding="utf-8"))
    return {"identity": identity, "spdx_document_sha256": _sha_bytes((evidence_dir / "Misc/externals.spdx.json").read_bytes()), "spdx_packages": _spdx_packages(spdx), "license_evidence": evidence}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def resolve_source_provenance(family_dir: Path, source: Path, output_dir: Path, *, root: Path = ROOT, zstd: str = "zstd") -> dict[str, Any]:
    verification = verify_release_family(family_dir, root=root, zstd=zstd)
    family_lock = _load(root / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-artifact-family-r1.lock.json")
    if not verification.get("pass") or family_lock.get("release_family", {}).get("fingerprint_sha256") != FAMILY_FINGERPRINT:
        raise ValueError("frozen release family verification failed")
    full_expected = expected_family(root)["full"]
    full = family_dir / full_expected["filename"]
    before = {"sha256": sha256_file(full), "size_bytes": full.stat().st_size}
    if before["sha256"] != FULL_SHA256:
        raise ValueError("frozen full identity mismatch")
    wanted = {
        "python/build/upstream/extracted-metadata/android.py",
        "python/build/upstream/package/python-3.14.6-aarch64-linux-android.tar.gz",
    }
    full_members = _read_full_members(full, wanted, zstd=zstd)
    metadata_android = full_members["python/build/upstream/extracted-metadata/android.py"]
    package = full_members["python/build/upstream/package/python-3.14.6-aarch64-linux-android.tar.gz"]
    nested_android = _read_nested_android(package)
    if metadata_android != nested_android:
        raise ValueError("preserved android.py does not match nested official package")
    pins = parse_dependency_pins(metadata_android)
    baseline_authority = root / "experiments/epoch3-upstream-thin-release-blockers/rb1-baseline-authority.json"
    baseline_gaps_path = root / "experiments/epoch3-upstream-thin-release-blockers/rb1-baseline-authority-evidence/license-gap-register.json"
    baseline = _load(baseline_authority)
    if baseline.get("baseline", {}).get("license_gap_register_sha256") != BASELINE_GAP_SHA256 or sha256_file(baseline_gaps_path) != BASELINE_GAP_SHA256:
        raise ValueError("RB-1 baseline gap authority mismatch")
    baseline_gaps = _load(baseline_gaps_path)
    evidence_dir = output_dir / "source-evidence"
    if evidence_dir.exists():
        shutil.rmtree(evidence_dir)
    source_info = inspect_cpython_source(source, evidence_dir)
    after = {"sha256": sha256_file(full), "size_bytes": full.stat().st_size}
    if before != after:
        raise RuntimeError("frozen full changed during provenance resolution")
    source_plan: list[dict[str, Any]] = []
    pin_map = {"bzip2":"bzip2","libffi":"libffi","openssl":"openssl","sqlite":"sqlite","xz-liblzma":"xz","zstd":"zstd"}
    for component in ("cpython","project-launcher","pip","openssl","sqlite","bzip2","xz-liblzma","zstd","expat","libmpdec","libffi","android-system-providers"):
        row: dict[str, Any] = {"component_class": component, "payload_packaged": False, "mapping_complete": False}
        if component == "cpython":
            row.update({"source_coordinate":{"filename":CPYTHON_SOURCE["filename"],"sha256":CPYTHON_SOURCE["sha256"],"url":CPYTHON_SOURCE["url"]},"license_candidates":["LICENSE","Misc/externals.spdx.json"],"source_coordinate_resolved":True})
        elif component == "project-launcher":
            repo_license = root / "LICENSE"
            row.update({"source_coordinate":{"path":"LICENSE","sha256":sha256_file(repo_license)},"license_candidates":["LICENSE"],"source_coordinate_resolved":True})
        elif component == "pip":
            row.update({"source_coordinate":{"kind":"already-packaged-pip-dist-info-and-vendored-license-files"},"source_coordinate_resolved":True,"payload_packaged":True})
        elif component in pin_map:
            pin = pins[pin_map[component]]
            row.update({"source_coordinate":{"provider":"BeeWare cpython-android-source-deps","release_tag":pin["release_tag"],"asset":pin["aarch64_asset"],"release_url":pin["release_url"]},"resolved_version":pin["version"],"source_coordinate_resolved":True})
        elif component in {"expat","libmpdec"}:
            token = "expat" if component == "expat" else "decimal"
            candidates = [r["evidence_path"] for r in source_info["license_evidence"] if token in r["evidence_path"].casefold()]
            row.update({"source_coordinate":{"provider":"CPython 3.14.6 bundled source tree"},"license_candidates":candidates,"source_coordinate_resolved":bool(candidates)})
        else:
            row.update({"source_coordinate":{"kind":"external-Android-system-provider-policy"},"source_coordinate_resolved":False})
        source_plan.append(row)
    remaining = [g for g in baseline_gaps.get("gaps", []) if g.get("code") != "libffi-version-unresolved"]
    if len(remaining) != 11 or any(g.get("code") == "libffi-version-unresolved" for g in remaining):
        raise ValueError("unexpected resolved gap transition")
    output_dir.mkdir(parents=True, exist_ok=True)
    provenance = {
        "schema_version":1,"provenance_kind":"epoch3-rb1-source-provenance-resolution",
        "family":{"fingerprint_sha256":FAMILY_FINGERPRINT,"full":{**before,"filename":full.name}},
        "official_android_package":{**OFFICIAL_ANDROID,"embedded_path":"python/build/upstream/package/python-3.14.6-aarch64-linux-android.tar.gz"},
        "android_py":{"embedded_metadata_sha256":_sha_bytes(metadata_android),"nested_package_sha256":_sha_bytes(nested_android),"byte_identical":True},
        "beeware_dependency_releases":pins,
        "cpython_source":source_info,
        "resolved":{"libffi":{"version":pins["libffi"]["version"],"build_revision":pins["libffi"]["build_revision"],"release_tag":pins["libffi"]["release_tag"]}},
        "claim_boundary":{"artifact_bytes_mutated":False,"license_payloads_complete":False,"component_license_mapping_complete":False,"rb1_closed":False,"selectable":False,"publication":False},
    }
    plan = {
        "schema_version":1,"plan_kind":"epoch3-rb1-authoritative-license-source-plan",
        "family_fingerprint_sha256":FAMILY_FINGERPRINT,"components":source_plan,
        "next_action":"acquire-and-package-exact-license-and-notice-payloads",
        "claim_boundary":{"plan_is_not_license_payload":True,"component_license_mapping_complete":False,"rb1_closed":False,"selectable":False,"publication":False},
    }
    gap_register = {
        "schema_version":1,"register_kind":"epoch3-rb1-resolved-source-provenance-gap-register",
        "baseline_gap_count":12,"resolved_gaps":[{"code":"libffi-version-unresolved","resolution":{"version":pins["libffi"]["version"],"build_revision":pins["libffi"]["build_revision"],"release_tag":pins["libffi"]["release_tag"],"evidence":"byte-identical android.py in frozen full and nested official Android package"}}],
        "remaining_gaps":remaining,"blocking_gap_count":len(remaining),"closure_status":"incomplete",
        "claim_boundary":{"component_license_mapping_complete":False,"rb1_closed":False,"selectable":False,"publication":False},
    }
    write_json(output_dir / "source-provenance.json", provenance)
    write_json(output_dir / "license-source-plan.json", plan)
    write_json(output_dir / "resolved-gap-register.json", gap_register)
    result = {
        "schema_version":1,"runner_kind":"epoch3-rb1-source-provenance-resolution","pass":True,
        "metrics":{"component_count":12,"resolved_dependency_pin_count":len(pins),"resolved_version_components":["libffi"],"baseline_gap_count":12,"remaining_gap_count":11},
        "outputs":{"source_provenance":"source-provenance.json","license_source_plan":"license-source-plan.json","resolved_gap_register":"resolved-gap-register.json","source_evidence_dir":"source-evidence"},
        "full_artifact_identity_preserved":before==after,
        "claim_boundary":{"artifact_bytes_mutated":False,"component_license_mapping_complete":False,"rb1_closed":False,"selectable":False,"publication":False},
    }
    write_json(output_dir / "provenance-result.json", result)
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--family-dir", required=True, type=Path)
    parser.add_argument("--cpython-source", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--root", default=ROOT, type=Path)
    parser.add_argument("--zstd", default="zstd")
    args = parser.parse_args()
    try:
        result = resolve_source_provenance(args.family_dir.resolve(), args.cpython_source.resolve(), args.output_dir.resolve(), root=args.root.resolve(), zstd=args.zstd)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"schema_version":1,"runner_kind":"epoch3-rb1-source-provenance-resolution","pass":False,"error":f"{type(exc).__name__}: {exc}"}, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

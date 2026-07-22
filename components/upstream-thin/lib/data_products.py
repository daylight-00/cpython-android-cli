#!/usr/bin/env python3
"""Assemble, verify, install, activate, and qualify Epoch 3 Android data products."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from archive import normalize_member_name, safe_extract_tar, sha256_file, tree_manifest, write_json, write_tar_zst

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "config/products/cpython-android-cli-e3-rb2-data-products-r1.lock.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _check_identity(path: Path, expected: dict[str, Any]) -> None:
    actual = {"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
    wanted = {key: expected[key] for key in actual}
    if actual != wanted:
        raise ValueError(f"input identity mismatch: actual={actual!r} expected={wanted!r}")


def _zip_mode(info: zipfile.ZipInfo) -> int:
    return (info.external_attr >> 16) & 0xFFFF


def _safe_wheel_files(path: Path) -> dict[str, zipfile.ZipInfo]:
    files: dict[str, zipfile.ZipInfo] = {}
    with zipfile.ZipFile(path) as wheel:
        for info in wheel.infolist():
            raw = info.filename
            if raw.endswith("/"):
                raw = raw.rstrip("/")
                if not raw:
                    continue
            name = normalize_member_name(raw)
            if name in files:
                raise ValueError(f"duplicate wheel member: {name}")
            mode = _zip_mode(info)
            if mode and stat.S_ISLNK(mode):
                raise ValueError(f"wheel symlink forbidden: {name}")
            if info.is_dir():
                continue
            files[name] = info
    return files


def _read_wheel_member(path: Path, member: str, files: dict[str, zipfile.ZipInfo]) -> bytes:
    with zipfile.ZipFile(path) as wheel:
        return wheel.read(files[member])


def _license_members(files: dict[str, zipfile.ZipInfo], distribution: str) -> list[str]:
    candidates = [
        name
        for name in files
        if ".dist-info/" in name
        and PurePosixPath(name).name.lower().startswith(("license", "copying"))
        and name.lower().split(".dist-info/", 1)[0].startswith(distribution.lower().replace("-", "_"))
    ]
    if not candidates:
        candidates = [
            name for name in files
            if ".dist-info/" in name and PurePosixPath(name).name.lower().startswith(("license", "copying"))
        ]
    if not candidates:
        raise ValueError(f"no license member found in {distribution} wheel")
    return sorted(candidates, key=lambda item: (item.count("/"), item))


def _write_payload(path: Path, data: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(mode)


def _parse_iana_version(tzdata_zi: bytes) -> str:
    for line in tzdata_zi.decode("utf-8", errors="strict").splitlines()[:8]:
        if line.startswith("# version "):
            return line.removeprefix("# version ").strip()
    raise ValueError("tzdata.zi does not declare an IANA version")


def _release_id(ca_version: str, tzdata_version: str, revision: str) -> str:
    return f"android-data-ca-{ca_version}-tzdata-{tzdata_version}-{revision}"


def assemble_data_product(
    certifi_wheel: Path,
    tzdata_wheel: Path,
    output_dir: Path,
    *,
    ca_version: str,
    tzdata_version: str,
    revision: str = "r1",
    expected_certifi: dict[str, Any] | None = None,
    expected_tzdata: dict[str, Any] | None = None,
    zstd: str = "zstd",
) -> dict[str, Any]:
    certifi_wheel = certifi_wheel.resolve()
    tzdata_wheel = tzdata_wheel.resolve()
    if expected_certifi is not None:
        _check_identity(certifi_wheel, expected_certifi)
        if expected_certifi.get("version") != ca_version:
            raise ValueError("certifi version argument does not match the locked input")
    if expected_tzdata is not None:
        _check_identity(tzdata_wheel, expected_tzdata)
        if expected_tzdata.get("version") != tzdata_version:
            raise ValueError("tzdata version argument does not match the locked input")

    certifi_files = _safe_wheel_files(certifi_wheel)
    tzdata_files = _safe_wheel_files(tzdata_wheel)
    cert_member = "certifi/cacert.pem"
    if cert_member not in certifi_files:
        raise ValueError(f"missing {cert_member}")
    ca_bytes = _read_wheel_member(certifi_wheel, cert_member, certifi_files)
    cert_count = ca_bytes.count(b"-----BEGIN CERTIFICATE-----")
    if cert_count < 1 or ca_bytes.count(b"-----END CERTIFICATE-----") != cert_count:
        raise ValueError("invalid certifi CA bundle framing")

    zone_prefix = "tzdata/zoneinfo/"
    zone_members = sorted(
        name for name in tzdata_files
        if name.startswith(zone_prefix)
        and not name.endswith((".py", ".pyc"))
        and "/__pycache__/" not in name
    )
    if not zone_members:
        raise ValueError("tzdata wheel contains no zoneinfo payload")
    tzdata_zi_member = zone_prefix + "tzdata.zi"
    if tzdata_zi_member not in zone_members:
        raise ValueError("tzdata wheel is missing zoneinfo/tzdata.zi")
    tzdata_zi = _read_wheel_member(tzdata_wheel, tzdata_zi_member, tzdata_files)
    iana_version = _parse_iana_version(tzdata_zi)
    if expected_tzdata is not None:
        expected_iana = expected_tzdata.get("expected_iana_version")
        if isinstance(expected_iana, str) and not expected_iana.startswith("verify-from-") and iana_version != expected_iana:
            raise ValueError(f"IANA version mismatch: actual={iana_version!r} expected={expected_iana!r}")

    cert_licenses = _license_members(certifi_files, "certifi")
    tz_licenses = _license_members(tzdata_files, "tzdata")
    release_id = _release_id(ca_version, tzdata_version, revision)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="e3-data-product-") as tmp:
        staging = Path(tmp)
        data_root = staging / "data"
        _write_payload(data_root / "ca/ca-bundle.pem", ca_bytes)
        for member in zone_members:
            relative = member.removeprefix(zone_prefix)
            if not relative:
                continue
            _write_payload(data_root / "zoneinfo" / relative, _read_wheel_member(tzdata_wheel, member, tzdata_files))
        for member in cert_licenses:
            _write_payload(data_root / "licenses/certifi" / PurePosixPath(member).name, _read_wheel_member(certifi_wheel, member, certifi_files))
        for member in tz_licenses:
            _write_payload(data_root / "licenses/tzdata" / PurePosixPath(member).name, _read_wheel_member(tzdata_wheel, member, tzdata_files))

        sources = {
            "certifi": {
                "version": ca_version,
                "filename": certifi_wheel.name,
                "sha256": sha256_file(certifi_wheel),
                "size_bytes": certifi_wheel.stat().st_size,
                "payload_member": cert_member,
                "license_members": cert_licenses,
            },
            "tzdata": {
                "version": tzdata_version,
                "iana_version": iana_version,
                "filename": tzdata_wheel.name,
                "sha256": sha256_file(tzdata_wheel),
                "size_bytes": tzdata_wheel.stat().st_size,
                "payload_prefix": zone_prefix,
                "license_members": tz_licenses,
            },
        }
        metadata = {
            "schema_version": 1,
            "data_product_kind": "epoch3-android-ca-timezone-data",
            "release_id": release_id,
            "target": {"platform": "android", "libc": "bionic", "python_family": "cpython-upstream-thin"},
            "layout": {
                "ca_bundle": "ca/ca-bundle.pem",
                "zoneinfo_root": "zoneinfo",
                "license_root": "licenses",
            },
            "runtime_environment": {
                "SSL_CERT_FILE": "ca/ca-bundle.pem",
                "PYTHONTZPATH": "zoneinfo",
                "values_are_relative_to_data_root": True,
                "caller_override_allowed": True,
            },
            "update_model": {
                "python_artifacts_unchanged": True,
                "install_root_unchanged": True,
                "release_directory_immutable": True,
                "activation": "atomic-relative-current-symlink",
                "rollback": "activate-an-already-verified-release",
            },
            "sources": sources,
            "metrics": {"ca_certificate_count": cert_count, "zoneinfo_file_count": len(zone_members)},
            "claim_boundary": {
                "data_product_candidate": True,
                "runtime_qualified": False,
                "rb2_closed": False,
                "selectable": False,
                "publication": False,
            },
        }
        write_json(data_root / "DATA.json", metadata)
        write_json(data_root / "provenance/certifi.json", sources["certifi"])
        write_json(data_root / "provenance/tzdata.json", sources["tzdata"])
        excluded = ["data/DATA-MANIFEST.json"]
        manifest = {
            "schema_version": 1,
            "index_kind": "epoch3-android-data-product-self-excluding-member-manifest",
            "excluded_paths": excluded,
            "members": tree_manifest(data_root, exclude=excluded),
        }
        write_json(data_root / "DATA-MANIFEST.json", manifest)
        artifact = output_dir / f"{release_id}.tar.zst"
        write_tar_zst(data_root, artifact, zstd=zstd)

    verification = verify_data_product(artifact, zstd=zstd)
    if not verification["pass"]:
        raise ValueError(f"assembled data product failed verification: {verification}")
    return {
        "schema_version": 1,
        "operation": "assemble-epoch3-android-data-product",
        "pass": True,
        "artifact": {"filename": artifact.name, "sha256": sha256_file(artifact), "size_bytes": artifact.stat().st_size},
        "release_id": release_id,
        "sources": sources,
        "verification": verification,
    }


def _decompress_zst(archive: Path, output: Path, zstd: str) -> None:
    proc = subprocess.run([zstd, "-q", "-d", "-f", str(archive), "-o", str(output)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise ValueError(f"zstd decompression failed: {proc.stderr.strip()}")


def verify_data_product(archive: Path, *, zstd: str = "zstd") -> dict[str, Any]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    metrics: dict[str, Any] = {}
    try:
        with tempfile.TemporaryDirectory(prefix="verify-e3-data-") as tmp:
            root = Path(tmp)
            tar_path = root / "artifact.tar"
            _decompress_zst(archive, tar_path, zstd)
            rows = safe_extract_tar(tar_path, root / "tree", "r:")
            paths = {row["path"] for row in rows}
            checks["one_data_root"] = bool(paths) and all(path == "data" or path.startswith("data/") for path in paths)
            required = {
                "data", "data/DATA.json", "data/DATA-MANIFEST.json", "data/ca", "data/ca/ca-bundle.pem",
                "data/zoneinfo", "data/zoneinfo/tzdata.zi", "data/licenses", "data/licenses/certifi/LICENSE", "data/licenses/tzdata/LICENSE",
            }
            checks["required_layout"] = required.issubset(paths)
            checks["no_duplicate_members"] = len(paths) == len(rows)
            data_root = root / "tree/data"
            metadata = _load(data_root / "DATA.json")
            checks["metadata_schema"] = metadata.get("schema_version") == 1 and metadata.get("data_product_kind") == "epoch3-android-ca-timezone-data"
            checks["runtime_paths_relative"] = all(
                value and not value.startswith("/") and ".." not in PurePosixPath(value).parts
                for key, value in metadata.get("runtime_environment", {}).items()
                if key in {"SSL_CERT_FILE", "PYTHONTZPATH"}
            )
            checks["immutable_update_model"] = metadata.get("update_model", {}).get("python_artifacts_unchanged") is True and metadata.get("update_model", {}).get("install_root_unchanged") is True
            checks["claims_bounded"] = metadata.get("claim_boundary") == {
                "data_product_candidate": True, "publication": False, "rb2_closed": False, "runtime_qualified": False, "selectable": False
            }
            ca_bytes = (data_root / "ca/ca-bundle.pem").read_bytes()
            begin = ca_bytes.count(b"-----BEGIN CERTIFICATE-----")
            checks["ca_bundle_framing"] = begin >= 1 and ca_bytes.count(b"-----END CERTIFICATE-----") == begin
            iana_version = _parse_iana_version((data_root / "zoneinfo/tzdata.zi").read_bytes())
            checks["iana_version_bound"] = metadata.get("sources", {}).get("tzdata", {}).get("iana_version") == iana_version
            checks["source_wheel_hashes_bound"] = all(
                isinstance(metadata.get("sources", {}).get(name, {}).get("sha256"), str)
                and len(metadata["sources"][name]["sha256"]) == 64
                for name in ("certifi", "tzdata")
            )
            payload_files = [path for path in data_root.rglob("*") if path.is_file()]
            checks["pure_data_only"] = all(
                path.suffix not in {".py", ".pyc", ".pyo", ".so", ".a", ".o"}
                and not path.read_bytes().startswith(b"\x7fELF")
                for path in payload_files
            )
            manifest = _load(data_root / "DATA-MANIFEST.json")
            actual = tree_manifest(data_root, exclude=manifest.get("excluded_paths", []))
            checks["self_excluding_manifest_exact"] = manifest.get("members") == actual
            metrics.update({
                "archive_member_count": len(rows),
                "release_id": metadata.get("release_id"),
                "ca_certificate_count": begin,
                "zoneinfo_file_count": len([path for path in (data_root / "zoneinfo").rglob("*") if path.is_file()]),
                "iana_version": iana_version,
            })
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{type(exc).__name__}: {exc}")
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-android-ca-timezone-data-product",
        "pass": not failed and not errors,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "metrics": metrics,
        "subject": {"filename": archive.name, "sha256": sha256_file(archive), "size_bytes": archive.stat().st_size} if archive.is_file() else None,
        "claim_boundary": {"runtime_qualified": False, "rb2_closed": False, "selectable": False, "publication": False},
    }



def _relative_tree(root: Path) -> list[dict[str, Any]]:
    rows = tree_manifest(root)
    prefix = root.name
    normalized: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        path = item["path"]
        item["path"] = "." if path == prefix else path.removeprefix(prefix + "/")
        normalized.append(item)
    return normalized

def _atomic_activate(data_home: Path, release_id: str) -> dict[str, Any]:
    releases = data_home / "releases"
    target = releases / release_id
    if not target.is_dir() or not (target / "DATA.json").is_file():
        raise ValueError(f"unknown or incomplete data release: {release_id}")
    data_home.mkdir(parents=True, exist_ok=True)
    temporary = data_home / f".current.{os.getpid()}"
    if temporary.exists() or temporary.is_symlink():
        temporary.unlink()
    os.symlink(f"releases/{release_id}", temporary)
    os.replace(temporary, data_home / "current")
    current = data_home / "current"
    return {"release_id": release_id, "current_link": os.readlink(current), "data_root": str(current)}


def install_data_product(archive: Path, data_home: Path, *, activate: bool = True, zstd: str = "zstd") -> dict[str, Any]:
    verification = verify_data_product(archive, zstd=zstd)
    if not verification["pass"]:
        raise ValueError(f"invalid data product: {verification}")
    release_id = str(verification["metrics"]["release_id"])
    releases = data_home / "releases"
    final = releases / release_id
    data_home.mkdir(parents=True, exist_ok=True)
    releases.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="install-e3-data-", dir=data_home) as tmp:
        tmp_root = Path(tmp)
        tar_path = tmp_root / "artifact.tar"
        _decompress_zst(archive, tar_path, zstd)
        safe_extract_tar(tar_path, tmp_root / "tree", "r:")
        candidate = tmp_root / "tree/data"
        if final.exists():
            existing = _relative_tree(final)
            incoming = _relative_tree(candidate)
            if existing != incoming:
                raise ValueError(f"immutable release collision: {release_id}")
        else:
            staging = releases / f".{release_id}.{os.getpid()}"
            if staging.exists():
                shutil.rmtree(staging)
            shutil.copytree(candidate, staging)
            os.replace(staging, final)
    activation = _atomic_activate(data_home, release_id) if activate else None
    return {
        "schema_version": 1,
        "operation": "install-epoch3-android-data-product",
        "pass": True,
        "release_id": release_id,
        "installed_root": str(final),
        "activation": activation,
    }


def activate_data_release(data_home: Path, release_id: str) -> dict[str, Any]:
    return {"schema_version": 1, "operation": "activate-epoch3-android-data-release", "pass": True, **_atomic_activate(data_home, release_id)}


def qualify_data_product(python: Path, data_root: Path) -> dict[str, Any]:
    metadata = _load(data_root / "DATA.json")
    ca = data_root / metadata["layout"]["ca_bundle"]
    zoneinfo = data_root / metadata["layout"]["zoneinfo_root"]
    script = r'''
import json, os, ssl, sys, zoneinfo
ca = os.environ["SSL_CERT_FILE"]
tz = os.environ["PYTHONTZPATH"]
ctx = ssl.create_default_context(cafile=ca)
zoneinfo.reset_tzpath([tz])
keys = ["UTC", "Asia/Seoul", "America/New_York"]
loaded = {key: str(zoneinfo.ZoneInfo(key)) for key in keys}
print(json.dumps({"ca_count": len(ctx.get_ca_certs()), "zones": loaded, "python": sys.version, "executable": sys.executable}, sort_keys=True))
'''
    env = os.environ.copy()
    env["SSL_CERT_FILE"] = str(ca)
    env["PYTHONTZPATH"] = str(zoneinfo)
    proc = subprocess.run([str(python), "-I", "-c", script], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    details: dict[str, Any] = {}
    if proc.returncode == 0:
        details = json.loads(proc.stdout)
    passed = proc.returncode == 0 and details.get("ca_count", 0) > 0 and set(details.get("zones", {})) == {"UTC", "Asia/Seoul", "America/New_York"}
    return {
        "schema_version": 1,
        "qualifier_kind": "epoch3-android-ca-timezone-data-runtime",
        "pass": passed,
        "python": str(python),
        "data_root": str(data_root),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "details": details,
        "claim_boundary": {"exact_runtime_context_only": True, "rb2_closed": False, "selectable": False, "publication": False},
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    assemble = sub.add_parser("assemble")
    assemble.add_argument("--certifi-wheel", type=Path, required=True)
    assemble.add_argument("--tzdata-wheel", type=Path, required=True)
    assemble.add_argument("--output-dir", type=Path, required=True)
    assemble.add_argument("--ca-version", required=True)
    assemble.add_argument("--tzdata-version", required=True)
    assemble.add_argument("--revision", default="r1")
    assemble.add_argument("--lock-entry", choices=("current", "rollback"))
    assemble.add_argument("--zstd", default="zstd")
    verify = sub.add_parser("verify")
    verify.add_argument("archive", type=Path)
    verify.add_argument("--zstd", default="zstd")
    install = sub.add_parser("install")
    install.add_argument("archive", type=Path)
    install.add_argument("--data-home", type=Path, required=True)
    install.add_argument("--no-activate", action="store_true")
    install.add_argument("--zstd", default="zstd")
    activate = sub.add_parser("activate")
    activate.add_argument("--data-home", type=Path, required=True)
    activate.add_argument("--release-id", required=True)
    qualify = sub.add_parser("qualify")
    qualify.add_argument("--python", type=Path, required=True)
    qualify.add_argument("--data-root", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "assemble":
            expected_ca = expected_tz = None
            if args.lock_entry:
                entry = _load(LOCK_PATH)["releases"][args.lock_entry]
                expected_ca, expected_tz = entry["certifi"], entry["tzdata"]
            result = assemble_data_product(args.certifi_wheel, args.tzdata_wheel, args.output_dir, ca_version=args.ca_version, tzdata_version=args.tzdata_version, revision=args.revision, expected_certifi=expected_ca, expected_tzdata=expected_tz, zstd=args.zstd)
        elif args.command == "verify":
            result = verify_data_product(args.archive, zstd=args.zstd)
        elif args.command == "install":
            result = install_data_product(args.archive, args.data_home, activate=not args.no_activate, zstd=args.zstd)
        elif args.command == "activate":
            result = activate_data_release(args.data_home, args.release_id)
        else:
            result = qualify_data_product(args.python, args.data_root)
    except Exception as exc:  # noqa: BLE001
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build an unqualified E2-P1 release envelope from the frozen promoted prefix."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

SIDECAR_KINDS = ("artifact", "manifest", "provenance", "qualification", "licenses")
EXCLUDED_ROOTS = (
    "lib/python3.14/test",
    "lib/python3.14/__phello__",
    "lib/python3.14/tkinter",
    "lib/python3.14/idlelib",
    "lib/python3.14/turtledemo",
)
EXCLUDED_PATHS = {
    "lib/python3.14/turtle.py",
    "lib/python3.14/turtle.cfg",
}


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def safe_relative(path: str) -> bool:
    if not path or path.startswith("/") or "\\" in path or "\x00" in path:
        return False
    return all(part not in {"", ".", ".."} for part in PurePosixPath(path).parts)


def safe_symlink_target(member_path: str, target: str) -> bool:
    if not target or target.startswith("/") or "\\" in target:
        return False
    resolved = list(PurePosixPath(member_path).parent.parts)
    for part in PurePosixPath(target).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not resolved:
                return False
            resolved.pop()
        else:
            resolved.append(part)
    return bool(resolved) and resolved[0] == "python"


def is_excluded(rel: str) -> bool:
    path = PurePosixPath(rel)
    if any(part == "__pycache__" for part in path.parts):
        return True
    if path.suffix in {".pyc", ".pyo"}:
        return True
    if rel in EXCLUDED_PATHS:
        return True
    return any(rel == root or rel.startswith(root + "/") for root in EXCLUDED_ROOTS)


def copy_prefix(source: Path, destination: Path) -> dict[str, int]:
    counts = {"directory": 0, "regular": 0, "symlink": 0, "excluded": 0}

    def visit(src: Path, dst: Path, rel: str) -> None:
        if rel and is_excluded(rel):
            counts["excluded"] += 1
            return
        observed = src.lstat()
        mode = stat.S_IMODE(observed.st_mode)
        if stat.S_ISDIR(observed.st_mode):
            dst.mkdir(mode=mode, exist_ok=True)
            counts["directory"] += 1
            for child in sorted(src.iterdir(), key=lambda item: item.name):
                child_rel = child.name if not rel else f"{rel}/{child.name}"
                visit(child, dst / child.name, child_rel)
            os.chmod(dst, mode, follow_symlinks=False)
        elif stat.S_ISREG(observed.st_mode):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst, follow_symlinks=False)
            os.chmod(dst, mode, follow_symlinks=False)
            counts["regular"] += 1
        elif stat.S_ISLNK(observed.st_mode):
            target = os.readlink(src)
            member = f"python/{rel}"
            if not safe_symlink_target(member, target):
                raise ValueError(f"unsafe source symlink: {rel} -> {target}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(target, dst)
            counts["symlink"] += 1
        else:
            raise ValueError(f"unsupported source entry type: {src}")

    visit(source, destination, "")
    return counts


def overlay_launcher(prefix: Path, launcher: Path, python_mm: str) -> None:
    bin_dir = prefix / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name in (f"python{python_mm}", "python3", "python"):
        target = bin_dir / name
        if target.is_symlink() or target.exists():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
    destination = bin_dir / f"python{python_mm}"
    shutil.copyfile(launcher, destination)
    os.chmod(destination, 0o755)
    os.symlink(f"python{python_mm}", bin_dir / "python3")
    os.symlink("python3", bin_dir / "python")


def is_elf(path: Path) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    with path.open("rb") as stream:
        return stream.read(4) == b"\x7fELF"


def strip_elf_files(prefix: Path, strip_tool: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(prefix.rglob("*"), key=lambda item: item.as_posix()):
        if not is_elf(path):
            continue
        before = sha256_file(path)
        proc = subprocess.run(
            [strip_tool, "--strip-unneeded", str(path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"strip failed for {path}: {proc.stderr.strip()}")
        rows.append(
            {
                "path": f"python/{path.relative_to(prefix).as_posix()}",
                "before_sha256": before,
                "after_sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        )
    if not rows:
        raise RuntimeError("no ELF files were found for install_only_stripped")
    return rows


def payload_class(path: str) -> str:
    rel = path.removeprefix("python/")
    development_prefixes = (
        "include",
        "lib/pkgconfig",
        "lib/python3.14/config-3.14-",
    )
    if rel == "include" or rel.startswith("include/"):
        return "development"
    if rel == "lib/pkgconfig" or rel.startswith("lib/pkgconfig/"):
        return "development"
    if rel.startswith("lib/python3.14/config-3.14-"):
        return "development"
    if rel in {"bin/python3.14-config", "bin/python3-config", "bin/python-config"}:
        return "development"
    if rel.startswith("lib/") and rel.endswith(".a"):
        return "development"
    return "runtime"


def manifest_entries(prefix: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    paths = [prefix, *prefix.rglob("*")]
    for path in sorted(paths, key=lambda item: ("python" if item == prefix else f"python/{item.relative_to(prefix).as_posix()}")):
        member = "python" if path == prefix else f"python/{path.relative_to(prefix).as_posix()}"
        if not safe_relative(member):
            raise ValueError(f"unsafe member path: {member}")
        observed = path.lstat()
        row: dict[str, Any] = {
            "path": member,
            "mode": f"{stat.S_IMODE(observed.st_mode):04o}",
            "payload_class": payload_class(member),
        }
        if stat.S_ISDIR(observed.st_mode):
            row["type"] = "directory"
        elif stat.S_ISREG(observed.st_mode):
            row.update(type="regular", size=observed.st_size, sha256=sha256_file(path))
        elif stat.S_ISLNK(observed.st_mode):
            target = os.readlink(path)
            if not safe_symlink_target(member, target):
                raise ValueError(f"unsafe staged symlink: {member} -> {target}")
            row.update(type="symlink", symlink_target=target)
        else:
            raise ValueError(f"unsupported staged entry type: {path}")
        entries.append(row)
    if [row["path"] for row in entries] != sorted(row["path"] for row in entries):
        raise AssertionError("manifest entries are not lexicographically ordered")
    return entries


def tar_info(row: dict[str, Any]) -> tarfile.TarInfo:
    info = tarfile.TarInfo(row["path"])
    info.mode = int(row["mode"], 8)
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    info.pax_headers = {}
    if row["type"] == "directory":
        info.type = tarfile.DIRTYPE
        info.size = 0
    elif row["type"] == "regular":
        info.type = tarfile.REGTYPE
        info.size = row["size"]
    elif row["type"] == "symlink":
        info.type = tarfile.SYMTYPE
        info.size = 0
        info.linkname = row["symlink_target"]
    else:
        raise ValueError(f"unsupported manifest type: {row['type']}")
    return info


def build_tar(prefix: Path, entries: list[dict[str, Any]], destination: Path) -> None:
    with destination.open("wb") as raw:
        with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for row in entries:
                info = tar_info(row)
                if row["type"] == "regular":
                    source = prefix if row["path"] == "python" else prefix / row["path"].removeprefix("python/")
                    with source.open("rb") as stream:
                        archive.addfile(info, stream)
                else:
                    archive.addfile(info)


def zstd_version(zstd: str) -> str:
    proc = subprocess.run([zstd, "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    match = re.search(r"v?(\d+\.\d+\.\d+)", proc.stdout)
    return f"zstd-cli-{match.group(1)}" if match else proc.stdout.strip().splitlines()[0]


def compress_zstd(zstd: str, source: Path, destination: Path, level: int) -> None:
    subprocess.run(
        [zstd, "-q", "-f", f"-{level}", "-T1", "--check", "-o", str(destination), str(source)],
        check=True,
    )


def file_ref(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "sha256": sha256_file(path), "size": path.stat().st_size}


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_json_bytes(value))


def git_value(root: Path, expression: str) -> str:
    proc = subprocess.run(["git", "rev-parse", expression], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return proc.stdout.strip()


def tool_version(tool: str) -> str:
    proc = subprocess.run([tool, "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    return proc.stdout.splitlines()[0].strip()


def create_release(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    source_prefix = args.source_prefix.resolve()
    launcher = args.launcher.resolve()
    output = args.output_dir.resolve()
    if not source_prefix.is_dir():
        raise FileNotFoundError(f"source prefix not found: {source_prefix}")
    if not launcher.is_file():
        raise FileNotFoundError(f"launcher not found: {launcher}")
    if not args.strip_tool:
        raise RuntimeError("--strip-tool is required")
    strip_tool = shutil.which(args.strip_tool) or (args.strip_tool if Path(args.strip_tool).is_file() else None)
    if not strip_tool:
        raise FileNotFoundError(f"strip tool not found: {args.strip_tool}")
    zstd = shutil.which(args.zstd)
    if not zstd:
        raise FileNotFoundError(f"zstd tool not found: {args.zstd}")

    lock = read_json(root / "config/products/cpython-3.14.6-aarch64-linux-android.lock.json")
    version = lock["python_version"]
    python_mm = ".".join(version.split(".")[:2])
    api = int(lock["android_api"])
    artifact_id = f"cpython-{version}-aarch64-linux-android{api}-install_only_stripped"
    archive_name = f"{artifact_id}.tar.zst"
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="e2p2-package-", dir=output.parent) as temp_name:
        temp = Path(temp_name)
        staged = temp / "python"
        copy_counts = copy_prefix(source_prefix, staged)
        overlay_launcher(staged, launcher, python_mm)
        strip_rows = strip_elf_files(staged, str(strip_tool))
        entries = manifest_entries(staged)

        license_path = f"python/lib/python{python_mm}/LICENSE.txt"
        license_row = next((row for row in entries if row["path"] == license_path and row["type"] == "regular"), None)
        if license_row is None:
            raise RuntimeError(f"CPython license is missing from staged payload: {license_path}")
        executable = next((row for row in entries if row["path"] == f"python/bin/python{python_mm}" and row["type"] == "regular"), None)
        if executable is None or executable["mode"] != "0755":
            raise RuntimeError("canonical launcher is missing or not executable")
        classes = {row["payload_class"] for row in entries}
        if classes != {"runtime", "development"}:
            raise RuntimeError(f"payload class coverage mismatch: {sorted(classes)}")

        tar_a = temp / "a.tar"
        tar_b = temp / "b.tar"
        zst_a = temp / "a.tar.zst"
        zst_b = temp / "b.tar.zst"
        build_tar(staged, entries, tar_a)
        build_tar(staged, entries, tar_b)
        compress_zstd(zstd, tar_a, zst_a, args.zstd_level)
        compress_zstd(zstd, tar_b, zst_b, args.zstd_level)
        if sha256_file(zst_a) != sha256_file(zst_b) or zst_a.read_bytes() != zst_b.read_bytes():
            raise RuntimeError("release archive is not byte-reproducible across two serializations")
        archive_path = output / archive_name
        shutil.copyfile(zst_a, archive_path)

    archive_ref = file_ref(archive_path)
    build_options = ["development", "install_only_stripped", "runtime", "strip_unneeded"]
    artifact = {
        "schema_version": 1,
        "metadata_kind": "hw-t-standalone-artifact",
        "artifact_id": artifact_id,
        "distribution": {
            "implementation": "cpython",
            "python_version": version,
            "python_major_minor": python_mm,
            "python_tag": f"cp{python_mm.replace('.', '')}",
            "python_abi_tag": f"cp{python_mm.replace('.', '')}",
            "soabi": f"cpython-{python_mm.replace('.', '')}-aarch64-linux-android",
            "multiarch": "aarch64-linux-android",
        },
        "target": {
            "os": "android",
            "kernel": "linux",
            "libc": "bionic",
            "architecture": "aarch64",
            "target_triple": "aarch64-linux-android",
            "android_abi": "arm64-v8a",
            "android_api_min": api,
            "wheel_platform_tag": f"android_{api}_arm64_v8a",
            "sysconfig_platform": f"android-{api}-arm64_v8a",
        },
        "artifact": {
            "flavor": "install_only_stripped",
            "archive_filename": archive_name,
            "archive_format": "pax-tar+zstd",
            "archive_sha256": archive_ref["sha256"],
            "archive_size": archive_ref["size"],
            "build_options": build_options,
            "native_debug": "stripped",
            "payload_classes": ["runtime", "development"],
            "excluded_payload_classes": ["tests", "build", "debug_symbols"],
        },
        "layout": {
            "archive_root": "python/",
            "install_root": "python/",
            "python_executable": f"python/bin/python{python_mm}",
            "direct_extract_runnable": True,
            "prefix_model": "whole-prefix-relocatable",
        },
        "profiles": {
            "primary": "termux-cli",
            "qualified": [],
            "binary_identity_requires_termux": False,
        },
        "compatibility": {
            "android_api_rule": "host-api-greater-than-or-equal-to-minimum",
            "required_os": "android",
            "required_libc": "bionic",
            "required_abi": "arm64-v8a",
            "consumer_mappings": {
                "uv_catalog_key": f"cpython-{version}-linux-aarch64-none",
                "uv_catalog_key_is_canonical_identity": False,
            },
        },
        "extensions": {
            "e2p2": {
                "excluded_policy_classes": ["optional_test_demo", "optional_test_suite", "unsupported_gui_source"],
                "qualification_required": True,
            }
        },
    }
    manifest = {
        "schema_version": 1,
        "metadata_kind": "hw-t-standalone-manifest",
        "artifact_id": artifact_id,
        "archive": {"filename": archive_name, "sha256": archive_ref["sha256"], "size": archive_ref["size"], "root": "python/"},
        "serialization": {
            "format": "pax-tar+zstd",
            "member_order": "lexicographic-posix-path",
            "mtime": 0,
            "uid": 0,
            "gid": 0,
            "uname": "",
            "gname": "",
            "hardlinks": "forbidden",
            "special_entries": "forbidden",
            "symlink_policy": "relative-non-escaping",
            "pax_headers": "path-and-linkpath-only-when-required",
            "compression_profile_recorded_in_provenance": True,
        },
        "ownership": {
            "unit": "exact-manifest-path",
            "unowned_descendant_policy": "preserve",
            "directory_removal_rule": "remove-owned-directory-only-when-empty",
            "installer_repacking": "forbidden",
        },
        "entries": entries,
        "extensions": {},
    }
    provenance = {
        "schema_version": 1,
        "metadata_kind": "hw-t-standalone-provenance",
        "artifact_id": artifact_id,
        "source": {"implementation": "cpython", "version": version, "tag": f"v{version}", "commit": lock["source_head"]},
        "toolchain": {"ndk_version": lock["ndk_version"], "target_compiler": Path(os.environ.get("ANDROID_CC", f"aarch64-linux-android{api}-clang")).name, "android_api": api},
        "build": {
            "repository": "daylight-00/cpython-android-cli",
            "commit": git_value(root, "HEAD"),
            "tree": git_value(root, "HEAD^{tree}"),
            "build_options": build_options,
            "fixture_only": False,
        },
        "archive_serialization": {
            "tar_format": "pax",
            "zstd_tool": zstd_version(zstd),
            "zstd_level": args.zstd_level,
            "zstd_threads": 1,
            "frame_checksum": True,
        },
        "predecessor_authority": {
            "epoch1_commit": "e1de252740a96c40f3d587269136235a2c84ea16",
            "epoch1_tree": "66c976f3fc182496d2843771b46faaf98fc267da",
            "stage3c_archive_contract": "pax-tar+gzip-schema-v1",
            "stage3f_publication_snapshot": "dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233",
        },
        "extensions": {
            "e2p2": {
                "copy_counts": copy_counts,
                "producer_authority": lock.get("producer_authority", {}),
                "standalone_artifacts": lock.get("standalone_artifacts", {}),
                "strip_tool": tool_version(str(strip_tool)),
                "stripped_elf_count": len(strip_rows),
                "stripped_elf": strip_rows,
                "serialization_replay": "2/2-byte-identical",
            }
        },
    }
    qualification = {
        "schema_version": 1,
        "metadata_kind": "hw-t-standalone-qualification",
        "artifact_id": artifact_id,
        "status": "not-qualified",
        "selectable": False,
        "profiles": ["termux-cli"],
        "checks": {"static": "passed", "emulator": "not-run", "termux": "not-run"},
        "claim_boundary": [
            "E2-P2 verifies deterministic assembly and E2-P1 envelope integrity only.",
            "The product remains unselectable until E2-P3 archive-only target qualification passes.",
        ],
        "extensions": {"e2p2": {"envelope_static_verification": "pending-sidecar-finalization"}},
    }
    licenses = {
        "schema_version": 1,
        "metadata_kind": "hw-t-standalone-licenses",
        "artifact_id": artifact_id,
        "entries": [
            {
                "component": "CPython",
                "license_id": "PSF-2.0",
                "archive_path": license_path,
                "sha256": license_row["sha256"],
                "size": license_row["size"],
            }
        ],
        "complete_for_published_payload": False,
        "extensions": {"e2p2": {"status": "dependency-license-expansion-required-before-publication"}},
    }

    sidecars = {
        "artifact": artifact,
        "manifest": manifest,
        "provenance": provenance,
        "qualification": qualification,
        "licenses": licenses,
    }
    sidecar_paths: dict[str, Path] = {}
    for kind in SIDECAR_KINDS:
        path = output / f"{artifact_id}.{kind}.json"
        write_json(path, sidecars[kind])
        sidecar_paths[kind] = path

    checksum_rows = [(sha256_file(archive_path), archive_path.name)] + [(sha256_file(sidecar_paths[kind]), sidecar_paths[kind].name) for kind in SIDECAR_KINDS]
    checksums = output / "SHA256SUMS"
    checksums.write_text("".join(f"{digest}  {name}\n" for digest, name in sorted(checksum_rows, key=lambda item: item[1])), encoding="utf-8")

    release = {
        "format": "hw-t-standalone-release-v1",
        "contract_version": 1,
        "channel": "prerelease",
        "selectable": False,
        "products": [
            {
                "artifact_id": artifact_id,
                "archive": file_ref(archive_path),
                "metadata": {kind: file_ref(sidecar_paths[kind]) for kind in SIDECAR_KINDS},
                "selectable": False,
            }
        ],
        "checksums": file_ref(checksums),
        "extensions": {"e2p2": {"qualification_required": True, "publication_allowed": False}},
    }
    release_index = {"schema_version": 1, "release": release, "release_sha256": sha256_bytes(canonical_json_bytes(release))}
    release_path = output / "release-index.json"
    write_json(release_path, release_index)

    verifier = root / "components/standalone/lib/verify_envelope.py"
    proc = subprocess.run([sys.executable, str(verifier), "--root", str(root), "--release-dir", str(output)], cwd=root)
    if proc.returncode != 0:
        raise RuntimeError("generated release envelope failed independent verification")

    qualification["extensions"]["e2p2"]["envelope_static_verification"] = "passed"
    write_json(sidecar_paths["qualification"], qualification)
    checksum_rows = [(sha256_file(archive_path), archive_path.name)] + [(sha256_file(sidecar_paths[kind]), sidecar_paths[kind].name) for kind in SIDECAR_KINDS]
    checksums.write_text("".join(f"{digest}  {name}\n" for digest, name in sorted(checksum_rows, key=lambda item: item[1])), encoding="utf-8")
    release["products"][0]["metadata"] = {kind: file_ref(sidecar_paths[kind]) for kind in SIDECAR_KINDS}
    release["checksums"] = file_ref(checksums)
    release_index = {"schema_version": 1, "release": release, "release_sha256": sha256_bytes(canonical_json_bytes(release))}
    write_json(release_path, release_index)
    proc = subprocess.run([sys.executable, str(verifier), "--root", str(root), "--release-dir", str(output)], cwd=root)
    if proc.returncode != 0:
        raise RuntimeError("finalized release envelope failed independent verification")

    result = {
        "schema_version": 1,
        "result_kind": "hw-t-e2p2-package-result",
        "status": "passed-unqualified",
        "artifact_id": artifact_id,
        "release_dir": str(output),
        "archive": file_ref(archive_path),
        "manifest_entry_count": len(entries),
        "payload_classes": sorted(classes),
        "stripped_elf_count": len(strip_rows),
        "selectable": False,
        "release_index": file_ref(release_path),
    }
    write_json(output.parent / f"{artifact_id}.package-result.json", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-prefix", type=Path, required=True)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--strip-tool", required=True)
    parser.add_argument("--zstd", default="zstd")
    parser.add_argument("--zstd-level", type=int, default=19)
    return parser


def main() -> int:
    try:
        result = create_release(build_parser().parse_args())
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

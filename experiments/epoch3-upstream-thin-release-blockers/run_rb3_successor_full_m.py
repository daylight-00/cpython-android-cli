#!/usr/bin/env python3
"""Qualify an RB-3 profile-M successor full candidate on Android/AArch64.

This runner does not promote or supersede the frozen predecessor family.  It
proves that one exact successor full candidate is structurally valid, works as
an Android runtime, and can be consumed by uv through a temporary exact
install-only projection.  Raw native-wheel ELF policy remains a separately
recorded boundary.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(LIB))
sys.path.insert(0, str(HERE))

from archive import copy_entry, safe_extract_tar, sha256_file, write_json, write_tar_gz  # noqa: E402
from qualify_full import qualify  # noqa: E402
from run_rb3_sysconfig_boundary_probe import (  # noqa: E402
    android_identity,
    clean_env,
    parse_json_stdout,
    run_capture,
    snapshot,
    wheel_probe,
)
from verify_full import verify  # noqa: E402

KEY = "cpython-3.14.6-linux-aarch64-none"
EXPECTED_PROFILE = "upstream-preserved-minimal-consumer-overlay"
EXPECTED_HEADER = "# system configuration generated and used by the sysconfig module"
EXPECTED_PREDECESSOR = {
    "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-full.tar.zst",
    "sha256": "20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12",
    "size_bytes": 39408292,
}


def exact_identity(path: Path) -> dict[str, Any]:
    return {
        "filename": path.name,
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def extract_zst(archive: Path, destination: Path, zstd: str) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rb3-successor-full-zst-") as td:
        tar_path = Path(td) / "artifact.tar"
        proc = subprocess.run(
            [zstd, "-q", "-d", "-f", str(archive), "-o", str(tar_path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"zstd extraction failed: {proc.stderr.strip()}")
        safe_extract_tar(tar_path, destination, "r:")


def identity_code() -> str:
    return (
        "import json,os,platform,sys,sysconfig;"
        "print(json.dumps({"
        "'executable':sys.executable,'real_executable':os.path.realpath(sys.executable),"
        "'version':platform.python_version(),'implementation':platform.python_implementation(),"
        "'soabi':sysconfig.get_config_var('SOABI'),'multiarch':sysconfig.get_config_var('MULTIARCH'),"
        "'platform':sysconfig.get_platform(),'prefix':sys.prefix,'base_prefix':sys.base_prefix,"
        "'cc':sysconfig.get_config_var('CC'),'cxx':sysconfig.get_config_var('CXX'),"
        "'ar':sysconfig.get_config_var('AR'),'build_gnu_type':sysconfig.get_config_var('BUILD_GNU_TYPE'),"
        "'host_gnu_type':sysconfig.get_config_var('HOST_GNU_TYPE'),"
        "'config_args':sysconfig.get_config_var('CONFIG_ARGS'),"
        "'ldshared':sysconfig.get_config_var('LDSHARED'),'cflags':sysconfig.get_config_var('CFLAGS'),"
        "'ldflags':sysconfig.get_config_var('LDFLAGS'),"
        "'metadata_profile':sysconfig.get_config_var('HW_T_METADATA_PROFILE')},sort_keys=True))"
    )


def profile_m_identity(row: dict[str, Any], *, managed: bool = False) -> bool:
    if not android_identity(row):
        return False
    value = parse_json_stdout(row)
    if not value:
        return False
    expected_tools = (
        ({"cc", "clang"}, {"c++", "clang++"}, {"ar", "llvm-ar"})
        if managed
        else ({"clang"}, {"clang++"}, {"llvm-ar"})
    )
    linker_policy = " ".join(str(value.get(key, "")) for key in ("ldshared", "ldflags"))
    return (
        value.get("metadata_profile") == EXPECTED_PROFILE
        and value.get("cc") in expected_tools[0]
        and value.get("cxx") in expected_tools[1]
        and value.get("ar") in expected_tools[2]
        and value.get("host_gnu_type") == "aarch64-unknown-linux-android"
        and value.get("build_gnu_type") != "aarch64-unknown-linux-android"
        and "consumer-normalized-binary-derived" not in str(value.get("config_args", ""))
        and "-D__BIONIC_NO_PAGE_SIZE_MACRO" in str(value.get("cflags", ""))
        and "max-page-size=16384" in linker_policy
        and "common-page-size=16384" in linker_policy
    )


def identity_base_ok(row: dict[str, Any], base: Path, *, managed: bool = False) -> bool:
    value = parse_json_stdout(row)
    return bool(profile_m_identity(row, managed=managed) and Path(str(value.get("base_prefix", ""))).resolve() == base.resolve())


def managed_find_observed(row: dict[str, Any], python_path: Path) -> bool:
    """Snapshot managed-find success before a later uninstall removes the path."""
    return row.get("returncode") == 0 and python_path.is_file()


def catalog_row(archive: Path) -> dict[str, Any]:
    return {
        "name": "cpython",
        "arch": {"family": "aarch64", "variant": None},
        "os": "linux",
        "libc": "none",
        "major": 3,
        "minor": 14,
        "patch": 6,
        "prerelease": "",
        "url": archive.resolve().as_uri(),
        "sha256": sha256_file(archive),
        "variant": None,
        "build": "hw-t-rb3-successor-full-profile-m",
    }


def project_install_only(install: Path, output: Path, staging: Path) -> dict[str, Any]:
    product = staging / "python"
    if product.exists():
        shutil.rmtree(product)
    product.mkdir(parents=True)
    for child in sorted(install.iterdir(), key=lambda p: p.name):
        copy_entry(child, product / child.name)
    rows = write_tar_gz(product, output)
    return {
        "archive": exact_identity(output),
        "member_count": len(rows),
        "projection_root": "python",
        "source": "successor-full/python/install",
        "claim": "temporary exact install-only projection for RB-3 qualification only",
    }


def run(
    full_archive: Path,
    output_dir: Path,
    uv: Path,
    *,
    zstd: str = "zstd",
    readelf: str = "readelf",
    pkg_config: str = "pkg-config",
    predecessor_full: Path | None = None,
) -> dict[str, Any]:
    full_archive = full_archive.resolve()
    output_dir = output_dir.resolve()
    uv = uv.resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "process").mkdir(parents=True)
    (output_dir / "artifacts").mkdir()
    (output_dir / "research").mkdir()

    before_candidate = exact_identity(full_archive)
    predecessor_before = exact_identity(predecessor_full.resolve()) if predecessor_full else None
    real_managed = Path(
        os.environ.get("UV_PYTHON_INSTALL_DIR", str(Path.home() / ".local/share/uv/python"))
    ).resolve()
    real_managed_before = snapshot(real_managed)

    structural = verify(full_archive, zstd=zstd, readelf=readelf)
    write_json(output_dir / "full-structural-verification.json", structural)
    qualification = qualify(
        full_archive,
        output=output_dir / "full-android-qualification.json",
        zstd=zstd,
        pkg_config=pkg_config,
    )

    uv_version = subprocess.run(
        [str(uv), "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    uv_identity = {
        "path": str(uv),
        "returncode": uv_version.returncode,
        "version": uv_version.stdout.strip(),
        "stderr": uv_version.stderr,
        "sha256": sha256_file(uv) if uv.is_file() else None,
        "size_bytes": uv.stat().st_size if uv.is_file() else None,
    }
    write_json(output_dir / "research/uv.json", uv_identity)

    process: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="rb3-successor-full-m-") as td:
        root = Path(td)
        extracted = root / "full"
        extract_zst(full_archive, extracted, zstd)
        python_root = extracted / "python"
        install = python_root / "install"
        python = install / "bin/python3.14"
        sysdata = install / "lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py"
        if not python.is_file() or not os.access(python, os.X_OK):
            raise ValueError("successor full lacks executable python/install/bin/python3.14")
        if not sysdata.is_file():
            raise ValueError("successor full lacks expected sysconfigdata")

        projected = output_dir / "artifacts/successor-install-only-projection.tar.gz"
        projection = project_install_only(install, projected, root / "projection")
        write_json(output_dir / "artifacts/install-only-projection.json", projection)

        system_env = clean_env(root / "system-session")
        direct = run_capture("system-identity", [str(python), "-c", identity_code()], root, system_env, output_dir / "process")
        process.append(direct)
        find = run_capture(
            "system-find",
            [str(uv), "python", "find", str(python), "--resolve-links", "--no-python-downloads", "--offline", "--no-managed-python", "--system", "--no-config", "--color", "never"],
            root, system_env, output_dir / "process",
        )
        process.append(find)
        system_venv = root / "system-venv"
        venv = run_capture(
            "system-venv",
            [str(uv), "venv", str(system_venv), "--python", str(python), "--no-python-downloads", "--offline", "--no-managed-python", "--no-cache", "--no-config", "--color", "never"],
            root, system_env, output_dir / "process",
        )
        process.append(venv)
        venv_id = run_capture("system-venv-identity", [str(system_venv / "bin/python"), "-c", identity_code()], root, system_env, output_dir / "process") if venv["returncode"] == 0 else {"name": "system-venv-identity", "returncode": 125}
        process.append(venv_id)
        run_row = run_capture(
            "system-run",
            [str(uv), "run", "--python", str(python), "--no-python-downloads", "--offline", "--no-managed-python", "--no-project", "--no-sync", "--no-config", "--color", "never", "--", "python", "-c", identity_code()],
            root, system_env, output_dir / "process",
        )
        process.append(run_row)
        project = root / "sync-project"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            "[project]\nname='rb3-successor-probe'\nversion='0.0.0'\nrequires-python='>=3.14,<3.15'\ndependencies=[]\n\n[tool.uv]\npackage=false\n",
            encoding="utf-8",
        )
        sync_venv = root / "sync-venv"
        sync_env = dict(system_env)
        sync_env["UV_PROJECT_ENVIRONMENT"] = str(sync_venv)
        sync = run_capture(
            "system-sync",
            [str(uv), "sync", "--project", str(project), "--python", str(python), "--no-python-downloads", "--offline", "--no-managed-python", "--no-cache", "--no-config", "--color", "never"],
            project, sync_env, output_dir / "process",
        )
        process.append(sync)
        sync_id = run_capture("system-sync-identity", [str(sync_venv / "bin/python"), "-c", identity_code()], project, sync_env, output_dir / "process") if sync["returncode"] == 0 else {"name": "system-sync-identity", "returncode": 125}
        process.append(sync_id)

        catalog = root / "custom-downloads.json"
        write_json(catalog, {KEY: catalog_row(projected)})
        shutil.copyfile(catalog, output_dir / "artifacts/custom-downloads.json")
        managed = root / "managed-root"
        managed_env = clean_env(root / "managed-session", managed, "manual", catalog)
        catalog_list = run_capture(
            "managed-catalog",
            [str(uv), "python", "list", "3.14", "--python-downloads-json-url", catalog.resolve().as_uri(), "--output-format", "json", "--show-urls", "--offline", "--no-config", "--color", "never"],
            root, managed_env, output_dir / "process",
        )
        process.append(catalog_list)
        install_row = run_capture(
            "managed-install",
            [str(uv), "python", "install", KEY, "--install-dir", str(managed), "--no-bin", "--python-downloads-json-url", catalog.resolve().as_uri(), "--offline", "--no-config", "--color", "never"],
            root, managed_env, output_dir / "process", timeout=900,
        )
        process.append(install_row)
        find_env = clean_env(root / "managed-find-session", managed, "never", catalog)
        managed_find = run_capture(
            "managed-find",
            [str(uv), "python", "find", "3.14.6", "--managed-python", "--no-python-downloads", "--offline", "--python-downloads-json-url", catalog.resolve().as_uri(), "--no-config", "--color", "never"],
            root, find_env, output_dir / "process",
        )
        process.append(managed_find)
        managed_python = Path(managed_find.get("stdout", "").strip()) if managed_find["returncode"] == 0 else managed / "missing"
        managed_find_ok = managed_find_observed(managed_find, managed_python)
        managed_id = run_capture("managed-identity", [str(managed_python), "-c", identity_code()], root, find_env, output_dir / "process") if managed_find_ok else {"name": "managed-identity", "returncode": 125}
        process.append(managed_id)
        managed_venv = root / "managed-venv"
        mvenv = run_capture(
            "managed-venv",
            [str(uv), "venv", str(managed_venv), "--python", "3.14.6", "--managed-python", "--no-python-downloads", "--offline", "--no-cache", "--no-config", "--color", "never"],
            root, find_env, output_dir / "process",
        )
        process.append(mvenv)
        mvenv_id = run_capture("managed-venv-identity", [str(managed_venv / "bin/python"), "-c", identity_code()], root, find_env, output_dir / "process") if mvenv["returncode"] == 0 else {"name": "managed-venv-identity", "returncode": 125}
        process.append(mvenv_id)
        managed_wheel = (
            wheel_probe(
                "successor-M-managed", managed_python, managed_python.parent.parent,
                root / "managed-wheel", find_env, output_dir / "process", readelf, None,
                perform_explicit_normalization=False,
            )
            if managed_find_ok and profile_m_identity(managed_id, managed=True)
            else {"pass": False, "skipped": "managed profile M identity unavailable"}
        )
        write_json(output_dir / "native-managed-wheel-elf-boundary.json", managed_wheel)
        managed_before_reinstall = snapshot(managed)
        reinstall = run_capture(
            "managed-reinstall",
            [str(uv), "python", "install", KEY, "--install-dir", str(managed), "--no-bin", "--python-downloads-json-url", catalog.resolve().as_uri(), "--offline", "--no-config", "--color", "never"],
            root, managed_env, output_dir / "process", timeout=900,
        )
        process.append(reinstall)
        managed_after_reinstall = snapshot(managed)
        uninstall = run_capture(
            "managed-uninstall",
            [str(uv), "python", "uninstall", "3.14.6", "--install-dir", str(managed), "--offline", "--no-config", "--color", "never"],
            root, find_env, output_dir / "process",
        )
        process.append(uninstall)
        find_empty = run_capture(
            "managed-find-empty",
            [str(uv), "python", "find", "3.14.6", "--managed-python", "--no-python-downloads", "--offline", "--python-downloads-json-url", catalog.resolve().as_uri(), "--no-config", "--color", "never"],
            root, find_env, output_dir / "process",
        )
        process.append(find_empty)

        wheel = wheel_probe(
            "successor-M", python, install, root / "wheel", system_env,
            output_dir / "process", readelf, None,
            perform_explicit_normalization=False,
        )
        write_json(output_dir / "native-wheel-elf-boundary.json", wheel)

        checks = {
            "full_structural_verification": structural.get("pass") is True,
            "full_android_qualification": qualification.get("pass") is True,
            "canonical_sysconfig_header": sysdata.read_text(encoding="utf-8").splitlines()[0] == EXPECTED_HEADER,
            "system_profile_m_identity": profile_m_identity(direct),
            "system_find": find["returncode"] == 0 and Path(find.get("stdout", "").strip()).resolve() == python.resolve(),
            "system_venv": venv["returncode"] == 0 and identity_base_ok(venv_id, install),
            "system_run": identity_base_ok(run_row, install),
            "system_sync": sync["returncode"] == 0 and identity_base_ok(sync_id, install),
            "managed_catalog": catalog_list["returncode"] == 0 and KEY in catalog_list.get("stdout", ""),
            "managed_install": install_row["returncode"] == 0,
            "managed_find": managed_find_ok,
            "managed_profile_m_identity": profile_m_identity(managed_id, managed=True),
            "managed_venv": mvenv["returncode"] == 0 and identity_base_ok(mvenv_id, managed_python.parent.parent, managed=True),
            "managed_reinstall_noop": reinstall["returncode"] == 0 and managed_before_reinstall == managed_after_reinstall,
            "managed_uninstall": uninstall["returncode"] == 0 and find_empty["returncode"] != 0,
            "native_wheel_build_and_import": wheel.get("pass") is True and wheel.get("wheel_import_returncode") == 0,
            "native_wheel_elf_recorded": isinstance(wheel.get("raw_extension"), dict),
            "native_wheel_16k_alignment": wheel.get("raw_extension", {}).get("all_load_alignments_16k") is True,
            "managed_native_wheel_build_and_import": managed_wheel.get("pass") is True and managed_wheel.get("wheel_import_returncode") == 0,
            "managed_native_wheel_elf_recorded": isinstance(managed_wheel.get("raw_extension"), dict),
            "managed_native_wheel_16k_alignment": managed_wheel.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        }

    after_candidate = exact_identity(full_archive)
    predecessor_after = exact_identity(predecessor_full.resolve()) if predecessor_full else None
    real_managed_after = snapshot(real_managed)
    checks.update({
        "candidate_full_unchanged": before_candidate == after_candidate,
        "predecessor_full_unchanged": predecessor_before == predecessor_after,
        "real_managed_root_unchanged": real_managed_before == real_managed_after,
    })
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    result = {
        "schema_version": 1,
        "result_kind": "epoch3-rb3-profile-M-successor-full-owner-qualification",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "candidate_full": before_candidate,
        "predecessor_full": predecessor_before,
        "temporary_install_only_projection": projection,
        "uv": uv_identity,
        "profile": {"id": "M", "name": EXPECTED_PROFILE},
        "native_wheel_elf_boundary": wheel,
        "managed_native_wheel_elf_boundary": managed_wheel,
        "claim_boundary": {
            "successor_full_candidate_built": True,
            "successor_full_accepted": False,
            "successor_install_only_started": False,
            "predecessor_family_superseded": False,
            "portable_raw_wheel_claim": False,
            "user_built_wheel_postprocessing": "out-of-scope-external-tool-responsibility",
            "native_wheel_16k_alignment_qualified": wheel.get("raw_extension", {}).get("all_load_alignments_16k") is True,
            "managed_native_wheel_16k_alignment_qualified": managed_wheel.get("raw_extension", {}).get("all_load_alignments_16k") is True,
            "rb3_closed": False,
            "selectable": False,
            "publication": False,
        },
    }
    write_json(output_dir / "rb3-successor-full-m-result.json", result)
    write_json(output_dir / "protected-state.json", {
        "candidate_full_unchanged": before_candidate == after_candidate,
        "predecessor_full_unchanged": predecessor_before == predecessor_after,
        "real_managed_root": str(real_managed),
        "real_managed_root_unchanged": real_managed_before == real_managed_after,
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--uv", type=Path, default=Path(shutil.which("uv") or "uv"))
    parser.add_argument("--zstd", default="zstd")
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--pkg-config", default="pkg-config")
    parser.add_argument("--predecessor-full", type=Path)
    args = parser.parse_args()
    try:
        result = run(
            args.full_archive,
            args.output_dir,
            args.uv,
            zstd=args.zstd,
            readelf=args.readelf,
            pkg_config=args.pkg_config,
            predecessor_full=args.predecessor_full,
        )
    except Exception as exc:  # noqa: BLE001
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "rb3-successor-full-m-result.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Derive and qualify the profile-M successor install-only candidate on Android."""
from __future__ import annotations

import argparse
import filecmp
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

from archive import safe_extract_tar, sha256_file, write_json  # noqa: E402
from qualify_install_only import qualify  # noqa: E402
from run_rb3_successor_full_m import (  # noqa: E402
    KEY,
    clean_env,
    exact_identity,
    identity_base_ok,
    identity_code,
    managed_find_observed,
    profile_m_identity,
    run_capture,
    snapshot,
    wheel_probe,
)

FULL_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-full-r5.lock.json"
FULL_AUTHORITY_VERIFIER = HERE / "verify_rb3_successor_full_m_acceptance.py"
CLI = ROOT / "components/upstream-thin/bin/cpython-android-upstream-thin"
EXPECTED_FULL = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android-full.tar.zst",
    "sha256": "b13206f67d900c1954ee6720c1b3d9337c467c9008b93a0384c16fb6127260d2",
    "size_bytes": 39414556,
}
EXPECTED_INSTALL = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android-install_only.tar.gz",
    "sha256": "c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56",
    "size_bytes": 23843355,
    "member_count": 3699,
}


def command(command: list[str], *, cwd: Path = ROOT, timeout: int = 3600) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": command, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "timed_out": True}
    except OSError as exc:
        return {"command": command, "returncode": 127, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}", "timed_out": False}


def parse_json(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("returncode") != 0:
        return {}
    try:
        value = json.loads(row.get("stdout", ""))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def extract_install(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    safe_extract_tar(archive, destination, "r:gz")
    roots = sorted(item.name for item in destination.iterdir())
    if roots != ["python"]:
        raise ValueError(f"install-only root mismatch: {roots}")
    return destination / "python"


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
        "build": "hw-t-rb3-successor-install-only-profile-m",
    }


def run(
    full_archive: Path,
    output_dir: Path,
    uv: Path,
    *,
    zstd: str = "zstd",
    readelf: str = "readelf",
    pkg_config: str = "pkg-config",
    predecessor_install_only: Path | None = None,
) -> dict[str, Any]:
    full_archive = full_archive.resolve()
    output_dir = output_dir.resolve()
    uv = uv.resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "artifacts").mkdir(parents=True)
    (output_dir / "process").mkdir()
    (output_dir / "receipts").mkdir()
    (output_dir / "research").mkdir()

    full_before = exact_identity(full_archive)
    predecessor_before = exact_identity(predecessor_install_only.resolve()) if predecessor_install_only else None
    real_managed = Path(os.environ.get("UV_PYTHON_INSTALL_DIR", str(Path.home() / ".local/share/uv/python"))).resolve()
    real_managed_before = snapshot(real_managed)

    full_identity = full_before == EXPECTED_FULL
    write_json(output_dir / "receipts/full-input-identity.json", {"schema_version": 1, "pass": full_identity, "expected": EXPECTED_FULL, "observed": full_before})

    authority_row = command([sys.executable, str(FULL_AUTHORITY_VERIFIER), "--root", str(ROOT)])
    authority = parse_json(authority_row)
    write_json(output_dir / "receipts/full-authority-command.json", authority_row)
    write_json(output_dir / "receipts/full-authority-verification.json", authority)
    if not full_identity or authority_row["returncode"] != 0 or authority.get("pass") is not True:
        raise ValueError("accepted full r5 identity or authority verification failed")

    assemblies: list[Path] = []
    assembly_receipts: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="rb3-successor-install-only-assembly-") as assembly_td:
        assembly_root = Path(assembly_td)
        for index in (1, 2):
            destination = assembly_root / f"assembly-{index}"
            row = command([
                str(CLI), "assemble-install-only", "--full-archive", str(full_archive),
                "--output-dir", str(destination), "--full-lock", str(FULL_LOCK),
                "--release-id", "e3-full-r5", "--zstd", zstd,
            ])
            write_json(output_dir / f"receipts/assembly-{index}-command.json", row)
            parsed = parse_json(row)
            write_json(output_dir / f"receipts/assembly-{index}-receipt.json", parsed)
            matches = sorted(destination.glob("*-install_only.tar.gz"))
            if row["returncode"] != 0 or len(matches) != 1:
                raise RuntimeError(f"assembly {index} failed")
            assemblies.append(matches[0])
            assembly_receipts.append(parsed)

        reproducibility = {
            "schema_version": 1,
            "pass": filecmp.cmp(assemblies[0], assemblies[1], shallow=False),
            "first": exact_identity(assemblies[0]),
            "second": exact_identity(assemblies[1]),
            "byte_identical": assemblies[0].read_bytes() == assemblies[1].read_bytes(),
        }
        write_json(output_dir / "receipts/install-only-reproducibility.json", reproducibility)
        expected_identity = {key: EXPECTED_INSTALL[key] for key in ("filename", "sha256", "size_bytes")}
        if not reproducibility["pass"] or not reproducibility["byte_identical"] or reproducibility["first"] != expected_identity or reproducibility["second"] != expected_identity:
            raise ValueError("successor install-only reproducibility or identity mismatch")

        final_artifact = output_dir / "artifacts" / EXPECTED_INSTALL["filename"]
        shutil.copyfile(assemblies[0], final_artifact)

    verify_row = command([
        str(CLI), "verify-install-only", str(final_artifact), "--full-archive", str(full_archive),
        "--full-lock", str(FULL_LOCK), "--zstd", zstd,
    ])
    verification = parse_json(verify_row)
    write_json(output_dir / "receipts/install-only-verification-command.json", verify_row)
    write_json(output_dir / "receipts/install-only-verification.json", verification)

    qualification = qualify(final_artifact, output=output_dir / "receipts/install-only-android-qualification.json", pkg_config=pkg_config)

    process: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="rb3-successor-install-only-m-") as td:
        root = Path(td)
        install = extract_install(final_artifact, root / "install")
        python = install / "bin/python3.14"
        if not python.is_file() or not os.access(python, os.X_OK):
            raise ValueError("install-only lacks executable python3.14")

        system_env = clean_env(root / "system-session")
        direct = run_capture("system-identity", [str(python), "-c", identity_code()], root, system_env, output_dir / "process")
        process.append(direct)
        find = run_capture("system-find", [str(uv), "python", "find", str(python), "--resolve-links", "--no-python-downloads", "--offline", "--no-managed-python", "--system", "--no-config", "--color", "never"], root, system_env, output_dir / "process")
        process.append(find)
        system_venv = root / "system-venv"
        venv = run_capture("system-venv", [str(uv), "venv", str(system_venv), "--python", str(python), "--no-python-downloads", "--offline", "--no-managed-python", "--no-cache", "--no-config", "--color", "never"], root, system_env, output_dir / "process")
        process.append(venv)
        venv_id = run_capture("system-venv-identity", [str(system_venv / "bin/python"), "-c", identity_code()], root, system_env, output_dir / "process") if venv["returncode"] == 0 else {"name": "system-venv-identity", "returncode": 125}
        process.append(venv_id)
        run_row = run_capture("system-run", [str(uv), "run", "--python", str(python), "--no-python-downloads", "--offline", "--no-managed-python", "--no-project", "--no-sync", "--no-config", "--color", "never", "--", "python", "-c", identity_code()], root, system_env, output_dir / "process")
        process.append(run_row)
        project = root / "sync-project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='rb3-successor-install-only-probe'\nversion='0.0.0'\nrequires-python='>=3.14,<3.15'\ndependencies=[]\n\n[tool.uv]\npackage=false\n", encoding="utf-8")
        sync_venv = root / "sync-venv"
        sync_env = dict(system_env)
        sync_env["UV_PROJECT_ENVIRONMENT"] = str(sync_venv)
        sync = run_capture("system-sync", [str(uv), "sync", "--project", str(project), "--python", str(python), "--no-python-downloads", "--offline", "--no-managed-python", "--no-cache", "--no-config", "--color", "never"], project, sync_env, output_dir / "process")
        process.append(sync)
        sync_id = run_capture("system-sync-identity", [str(sync_venv / "bin/python"), "-c", identity_code()], project, sync_env, output_dir / "process") if sync["returncode"] == 0 else {"name": "system-sync-identity", "returncode": 125}
        process.append(sync_id)

        catalog = root / "custom-downloads.json"
        write_json(catalog, {KEY: catalog_row(final_artifact)})
        shutil.copyfile(catalog, output_dir / "artifacts/custom-downloads.json")
        managed = root / "managed-root"
        managed_env = clean_env(root / "managed-session", managed, "manual", catalog)
        catalog_list = run_capture("managed-catalog", [str(uv), "python", "list", "3.14", "--python-downloads-json-url", catalog.resolve().as_uri(), "--output-format", "json", "--show-urls", "--offline", "--no-config", "--color", "never"], root, managed_env, output_dir / "process")
        process.append(catalog_list)
        install_row = run_capture("managed-install", [str(uv), "python", "install", KEY, "--install-dir", str(managed), "--no-bin", "--python-downloads-json-url", catalog.resolve().as_uri(), "--offline", "--no-config", "--color", "never"], root, managed_env, output_dir / "process", timeout=900)
        process.append(install_row)
        find_env = clean_env(root / "managed-find-session", managed, "never", catalog)
        managed_find = run_capture("managed-find", [str(uv), "python", "find", "3.14.6", "--managed-python", "--no-python-downloads", "--offline", "--python-downloads-json-url", catalog.resolve().as_uri(), "--no-config", "--color", "never"], root, find_env, output_dir / "process")
        process.append(managed_find)
        managed_python = Path(managed_find.get("stdout", "").strip()) if managed_find["returncode"] == 0 else managed / "missing"
        managed_find_ok = managed_find_observed(managed_find, managed_python)
        managed_id = run_capture("managed-identity", [str(managed_python), "-c", identity_code()], root, find_env, output_dir / "process") if managed_find_ok else {"name": "managed-identity", "returncode": 125}
        process.append(managed_id)
        managed_venv = root / "managed-venv"
        mvenv = run_capture("managed-venv", [str(uv), "venv", str(managed_venv), "--python", "3.14.6", "--managed-python", "--no-python-downloads", "--offline", "--no-cache", "--no-config", "--color", "never"], root, find_env, output_dir / "process")
        process.append(mvenv)
        mvenv_id = run_capture("managed-venv-identity", [str(managed_venv / "bin/python"), "-c", identity_code()], root, find_env, output_dir / "process") if mvenv["returncode"] == 0 else {"name": "managed-venv-identity", "returncode": 125}
        process.append(mvenv_id)
        managed_wheel = wheel_probe("successor-install-only-M-managed", managed_python, managed_python.parent.parent, root / "managed-wheel", find_env, output_dir / "process", readelf, None, perform_explicit_normalization=False) if managed_find_ok and profile_m_identity(managed_id, managed=True) else {"pass": False, "skipped": "managed profile M identity unavailable"}
        write_json(output_dir / "receipts/native-managed-wheel-elf-boundary.json", managed_wheel)
        managed_before_reinstall = snapshot(managed)
        reinstall = run_capture("managed-reinstall", [str(uv), "python", "install", KEY, "--install-dir", str(managed), "--no-bin", "--python-downloads-json-url", catalog.resolve().as_uri(), "--offline", "--no-config", "--color", "never"], root, managed_env, output_dir / "process", timeout=900)
        process.append(reinstall)
        managed_after_reinstall = snapshot(managed)
        uninstall = run_capture("managed-uninstall", [str(uv), "python", "uninstall", "3.14.6", "--install-dir", str(managed), "--offline", "--no-config", "--color", "never"], root, find_env, output_dir / "process")
        process.append(uninstall)
        find_empty = run_capture("managed-find-empty", [str(uv), "python", "find", "3.14.6", "--managed-python", "--no-python-downloads", "--offline", "--python-downloads-json-url", catalog.resolve().as_uri(), "--no-config", "--color", "never"], root, find_env, output_dir / "process")
        process.append(find_empty)

        wheel = wheel_probe("successor-install-only-M", python, install, root / "wheel", system_env, output_dir / "process", readelf, None, perform_explicit_normalization=False)
        write_json(output_dir / "receipts/native-wheel-elf-boundary.json", wheel)

        checks = {
            "accepted_full_identity": full_identity,
            "accepted_full_authority": authority.get("pass") is True,
            "assembly_1": assembly_receipts[0].get("artifact", {}).get("sha256") == EXPECTED_INSTALL["sha256"],
            "assembly_2": assembly_receipts[1].get("artifact", {}).get("sha256") == EXPECTED_INSTALL["sha256"],
            "byte_reproducible": reproducibility["pass"] is True and reproducibility["byte_identical"] is True,
            "candidate_identity": exact_identity(final_artifact) == {key: EXPECTED_INSTALL[key] for key in ("filename", "sha256", "size_bytes")},
            "candidate_member_count": verification.get("artifact", {}).get("member_count") == EXPECTED_INSTALL["member_count"],
            "exact_full_projection": verify_row["returncode"] == 0 and verification.get("pass") is True,
            "android_target_qualification": qualification.get("pass") is True,
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
            "native_wheel_16k_alignment": wheel.get("raw_extension", {}).get("all_load_alignments_16k") is True,
            "managed_native_wheel_build_and_import": managed_wheel.get("pass") is True and managed_wheel.get("wheel_import_returncode") == 0,
            "managed_native_wheel_16k_alignment": managed_wheel.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        }

    full_after = exact_identity(full_archive)
    predecessor_after = exact_identity(predecessor_install_only.resolve()) if predecessor_install_only else None
    real_managed_after = snapshot(real_managed)
    checks.update({
        "accepted_full_unchanged": full_before == full_after,
        "predecessor_install_only_unchanged": predecessor_before == predecessor_after,
        "real_managed_root_unchanged": real_managed_before == real_managed_after,
        "stripped_not_started": not any("stripped" in path.name for path in (output_dir / "artifacts").iterdir()),
    })
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    result = {
        "schema_version": 1,
        "result_kind": "epoch3-rb3-profile-M-successor-install-only-owner-qualification",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "source_full": full_before,
        "artifact": {**exact_identity(final_artifact), "member_count": verification.get("artifact", {}).get("member_count")},
        "reproducibility": reproducibility,
        "projection": {"source": "accepted-full-r5/python/install", "target": "python", "filtering": "none-preserve-all-install-members", "payload_bytes_changed": False},
        "native_wheel_elf_boundary": wheel,
        "managed_native_wheel_elf_boundary": managed_wheel,
        "claim_boundary": {
            "successor_full_accepted": True,
            "successor_install_only_started": True,
            "successor_install_only_candidate": not failed,
            "successor_install_only_accepted": False,
            "successor_stripped_started": False,
            "predecessor_family_superseded": False,
            "portable_raw_wheel_claim": False,
            "user_built_wheel_postprocessing": "out-of-scope-external-tool-responsibility",
            "rb3_closed": False,
            "selectable": False,
            "publication": False,
        },
    }
    write_json(output_dir / "rb3-successor-install-only-m-result.json", result)
    write_json(output_dir / "protected-state.json", {
        "accepted_full_unchanged": full_before == full_after,
        "predecessor_install_only_unchanged": predecessor_before == predecessor_after,
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
    parser.add_argument("--predecessor-install-only", type=Path)
    args = parser.parse_args()
    try:
        result = run(args.full_archive, args.output_dir, args.uv, zstd=args.zstd, readelf=args.readelf, pkg_config=args.pkg_config, predecessor_install_only=args.predecessor_install_only)
    except Exception as exc:  # noqa: BLE001
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "rb3-successor-install-only-m-result.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())

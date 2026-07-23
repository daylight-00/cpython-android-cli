#!/usr/bin/env python3
"""Derive and qualify the profile-M successor stripped candidate on Android."""
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

INSTALL_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-successor-install-only-r5.lock.json"
INSTALL_AUTHORITY_VERIFIER = HERE / "verify_rb3_successor_install_only_m_acceptance.py"
INSTALL_AUTHORITY = HERE / "rb3-successor-install-only-m-authority.json"
FULL_AUTHORITY = HERE / "rb3-successor-full-m-authority.json"
PREDECESSOR_FAMILY_AUTHORITY = ROOT / "experiments/epoch3-upstream-thin-artifact-family/artifact-family-authority.json"
CLI = ROOT / "components/upstream-thin/bin/cpython-android-upstream-thin"
EXPECTED_INSTALL = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android-install_only.tar.gz",
    "sha256": "c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56",
    "size_bytes": 23843355,
    "member_count": 3699,
}
EXPECTED_FULL = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android-full.tar.zst",
    "sha256": "b13206f67d900c1954ee6720c1b3d9337c467c9008b93a0384c16fb6127260d2",
    "size_bytes": 39414556,
}
EXPECTED_PREDECESSOR_STRIPPED = {
    "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only_stripped.tar.gz",
    "sha256": "40951002c5880b223fa78c7b956dfcf2929e3ebf8e8beb9420c4179b98231134",
    "size_bytes": 23841241,
}
EXPECTED_CHANGED_PATHS = ["bin/python3.14"]
EXPECTED_REGULAR_ELF_COUNT = 81


def command(argv: list[str], *, cwd: Path = ROOT, timeout: int = 3600) -> dict[str, Any]:
    try:
        proc = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": argv, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"command": argv, "returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "timed_out": True}
    except OSError as exc:
        return {"command": argv, "returncode": 127, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}", "timed_out": False}


def parse_json(row: dict[str, Any]) -> dict[str, Any]:
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
        raise ValueError(f"stripped archive root mismatch: {roots}")
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
        "build": "hw-t-rb3-successor-stripped-profile-m",
    }


def authority_snapshot() -> dict[str, str]:
    return {
        "accepted_full_authority_sha256": sha256_file(FULL_AUTHORITY),
        "accepted_install_only_authority_sha256": sha256_file(INSTALL_AUTHORITY),
        "predecessor_family_authority_sha256": sha256_file(PREDECESSOR_FAMILY_AUTHORITY),
    }


def qualify_candidate(archive: Path, output: Path, pkg_config: str) -> dict[str, Any]:
    try:
        result = qualify(archive, output=output, pkg_config=pkg_config)
    except Exception as exc:  # noqa: BLE001
        result = {
            "schema_version": 1,
            "qualification_kind": "epoch3-rb3-profile-M-successor-stripped-android-target",
            "pass": False,
            "checks": {"qualification_completed_without_exception": False},
            "failed_checks": ["qualification_completed_without_exception"],
            "error": f"{type(exc).__name__}: {exc}",
            "claim_boundary": {},
        }
    result["qualification_kind"] = "epoch3-rb3-profile-M-successor-stripped-android-target"
    result.setdefault("claim_boundary", {}).update({
        "install_only_authority_frozen": True,
        "stripped_started": True,
        "stripped_authority_frozen": False,
    })
    write_json(output, result)
    return result


def run(
    install_only_archive: Path,
    output_dir: Path,
    uv: Path,
    *,
    strip_tool: str,
    readelf: str = "readelf",
    pkg_config: str = "pkg-config",
    accepted_full: Path | None = None,
    predecessor_stripped: Path | None = None,
) -> dict[str, Any]:
    install_only_archive = install_only_archive.resolve()
    output_dir = output_dir.resolve()
    uv = uv.resolve()
    if accepted_full is None or predecessor_stripped is None:
        raise ValueError("accepted full and predecessor stripped artifacts are required protected inputs")
    accepted_full = accepted_full.resolve()
    predecessor_stripped = predecessor_stripped.resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "artifacts").mkdir(parents=True)
    (output_dir / "process").mkdir()
    (output_dir / "receipts").mkdir()
    (output_dir / "research").mkdir()

    install_before = exact_identity(install_only_archive)
    full_before = exact_identity(accepted_full) if accepted_full else None
    predecessor_before = exact_identity(predecessor_stripped) if predecessor_stripped else None
    authority_before = authority_snapshot()
    real_managed = Path(os.environ.get("UV_PYTHON_INSTALL_DIR", str(Path.home() / ".local/share/uv/python"))).resolve()
    real_managed_before = snapshot(real_managed)

    expected_install_identity = {key: EXPECTED_INSTALL[key] for key in ("filename", "sha256", "size_bytes")}
    install_identity = install_before == expected_install_identity
    write_json(output_dir / "receipts/install-only-input-identity.json", {
        "schema_version": 1,
        "pass": install_identity,
        "expected": expected_install_identity,
        "observed": install_before,
    })
    if accepted_full and full_before != EXPECTED_FULL:
        raise ValueError("accepted full r5 identity mismatch")
    if predecessor_stripped and predecessor_before != EXPECTED_PREDECESSOR_STRIPPED:
        raise ValueError("predecessor stripped identity mismatch")

    authority_row = command([sys.executable, str(INSTALL_AUTHORITY_VERIFIER), "--root", str(ROOT)])
    authority = parse_json(authority_row)
    write_json(output_dir / "receipts/install-only-authority-command.json", authority_row)
    write_json(output_dir / "receipts/install-only-authority-verification.json", authority)
    if not install_identity or authority_row["returncode"] != 0 or authority.get("pass") is not True:
        raise ValueError("accepted install-only r5 identity or authority verification failed")

    assemblies: list[Path] = []
    assembly_receipts: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="rb3-successor-stripped-assembly-") as assembly_td:
        assembly_root = Path(assembly_td)
        for index in (1, 2):
            destination = assembly_root / f"assembly-{index}"
            row = command([
                str(CLI), "assemble-stripped",
                "--install-only-archive", str(install_only_archive),
                "--output-dir", str(destination),
                "--strip-tool", strip_tool,
                "--readelf", readelf,
                "--install-only-lock", str(INSTALL_LOCK),
            ])
            write_json(output_dir / f"receipts/assembly-{index}-command.json", row)
            parsed = parse_json(row)
            write_json(output_dir / f"receipts/assembly-{index}-receipt.json", parsed)
            matches = sorted(destination.glob("*-install_only_stripped.tar.gz"))
            if row["returncode"] != 0 or len(matches) != 1 or parsed.get("decision") != "distinct-archive":
                raise RuntimeError(f"stripped assembly {index} failed or did not produce a distinct archive")
            assemblies.append(matches[0])
            assembly_receipts.append(parsed)

        reproducibility = {
            "schema_version": 1,
            "pass": filecmp.cmp(assemblies[0], assemblies[1], shallow=False),
            "first": exact_identity(assemblies[0]),
            "second": exact_identity(assemblies[1]),
            "byte_identical": assemblies[0].read_bytes() == assemblies[1].read_bytes(),
            "first_changed_paths": assembly_receipts[0].get("changed_paths"),
            "second_changed_paths": assembly_receipts[1].get("changed_paths"),
        }
        write_json(output_dir / "receipts/stripped-reproducibility.json", reproducibility)
        if not reproducibility["pass"] or not reproducibility["byte_identical"] or reproducibility["first"] != reproducibility["second"]:
            raise ValueError("successor stripped A/B reproducibility mismatch")

        final_artifact = output_dir / "artifacts" / assemblies[0].name
        shutil.copyfile(assemblies[0], final_artifact)

    mutation_receipt = output_dir / "receipts/stripped-mutation-receipt.json"
    write_json(mutation_receipt, assembly_receipts[0])
    verify_row = command([
        str(CLI), "verify-stripped", str(final_artifact),
        "--install-only-archive", str(install_only_archive),
        "--mutation-receipt", str(mutation_receipt),
        "--readelf", readelf,
        "--install-only-lock", str(INSTALL_LOCK),
    ])
    verification = parse_json(verify_row)
    write_json(output_dir / "receipts/stripped-verification-command.json", verify_row)
    write_json(output_dir / "receipts/stripped-verification.json", verification)

    qualification = qualify_candidate(
        final_artifact,
        output_dir / "receipts/stripped-android-qualification.json",
        pkg_config,
    )

    receipt = assembly_receipts[0]
    if qualification.get("pass") is not True:
        install_after = exact_identity(install_only_archive)
        full_after = exact_identity(accepted_full)
        predecessor_after = exact_identity(predecessor_stripped)
        authority_after = authority_snapshot()
        real_managed_after = snapshot(real_managed)
        candidate_identity = exact_identity(final_artifact)
        checks = {
            "accepted_install_only_identity": install_identity,
            "accepted_install_only_authority": authority.get("pass") is True,
            "assembly_1_distinct": assembly_receipts[0].get("decision") == "distinct-archive",
            "assembly_2_distinct": assembly_receipts[1].get("decision") == "distinct-archive",
            "byte_reproducible": reproducibility["pass"] is True and reproducibility["byte_identical"] is True,
            "candidate_identity_consistent": candidate_identity == reproducibility["first"] == reproducibility["second"],
            "candidate_member_count": verification.get("artifact", {}).get("member_count") == EXPECTED_INSTALL["member_count"],
            "regular_elf_count_81": receipt.get("regular_elf_count") == EXPECTED_REGULAR_ELF_COUNT,
            "eligible_elf_count_1": receipt.get("eligible_elf_count") == 1,
            "changed_elf_count_1": receipt.get("changed_elf_count") == 1,
            "only_project_launcher_changed": receipt.get("eligible_paths") == EXPECTED_CHANGED_PATHS and receipt.get("changed_paths") == EXPECTED_CHANGED_PATHS,
            "exact_stripped_derivation": verify_row["returncode"] == 0 and verification.get("pass") is True,
            "non_elf_bytes_unchanged": verification.get("checks", {}).get("non_elf_bytes_unchanged") is True,
            "elf_dynamic_alignment_preserved": verification.get("checks", {}).get("elf_dynamic_alignment_preserved") is True,
            "android_target_qualification": False,
            "accepted_install_only_unchanged": install_before == install_after,
            "accepted_full_unchanged": full_before == full_after,
            "predecessor_stripped_unchanged": predecessor_before == predecessor_after,
            "frozen_authorities_unchanged": authority_before == authority_after,
            "real_managed_root_unchanged": real_managed_before == real_managed_after,
            "technical_family_not_started": not any(path.name in {"release-index.json", "SHA256SUMS"} for path in (output_dir / "artifacts").iterdir()),
        }
        failed = sorted(name for name, passed in checks.items() if passed is not True)
        result = {
            "schema_version": 1,
            "result_kind": "epoch3-rb3-profile-M-successor-stripped-owner-qualification",
            "pass": False,
            "checks": dict(sorted(checks.items())),
            "failed_checks": failed,
            "source_install_only": install_before,
            "artifact": {**candidate_identity, "member_count": verification.get("artifact", {}).get("member_count")},
            "reproducibility": reproducibility,
            "strip_surface": {
                "operation": "llvm-strip --strip-unneeded",
                "regular_elf_count": receipt.get("regular_elf_count"),
                "eligible_elf_count": receipt.get("eligible_elf_count"),
                "changed_elf_count": receipt.get("changed_elf_count"),
                "eligible_paths": receipt.get("eligible_paths"),
                "changed_paths": receipt.get("changed_paths"),
                "strip_tool": receipt.get("strip_tool"),
                "readelf_tool": receipt.get("readelf_tool"),
            },
            "qualification_error": qualification.get("error"),
            "claim_boundary": {
                "successor_full_accepted": True,
                "successor_install_only_accepted": True,
                "successor_stripped_started": True,
                "successor_stripped_candidate": False,
                "successor_stripped_accepted": False,
                "successor_technical_family_started": False,
                "successor_technical_family_accepted": False,
                "predecessor_family_superseded": False,
                "portable_raw_wheel_claim": False,
                "user_built_wheel_postprocessing": "out-of-scope-external-tool-responsibility",
                "rb3_closed": False,
                "selectable": False,
                "publication": False,
            },
        }
        write_json(output_dir / "rb3-successor-stripped-m-result.json", result)
        write_json(output_dir / "protected-state.json", {
            "accepted_install_only_unchanged": install_before == install_after,
            "accepted_full": full_before,
            "accepted_full_unchanged": full_before == full_after,
            "predecessor_stripped": predecessor_before,
            "predecessor_stripped_unchanged": predecessor_before == predecessor_after,
            "authority_before": authority_before,
            "authority_after": authority_after,
            "frozen_authorities_unchanged": authority_before == authority_after,
            "real_managed_root": str(real_managed),
            "real_managed_root_unchanged": real_managed_before == real_managed_after,
        })
        return result

    process: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="rb3-successor-stripped-m-") as td:
        root = Path(td)
        install = extract_install(final_artifact, root / "install")
        python = install / "bin/python3.14"
        if not python.is_file() or not os.access(python, os.X_OK):
            raise ValueError("stripped candidate lacks executable python3.14")

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
        (project / "pyproject.toml").write_text("[project]\nname='rb3-successor-stripped-probe'\nversion='0.0.0'\nrequires-python='>=3.14,<3.15'\ndependencies=[]\n\n[tool.uv]\npackage=false\n", encoding="utf-8")
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
        managed_wheel = wheel_probe("successor-stripped-M-managed", managed_python, managed_python.parent.parent, root / "managed-wheel", find_env, output_dir / "process", readelf, None, perform_explicit_normalization=False) if managed_find_ok and profile_m_identity(managed_id, managed=True) else {"pass": False, "skipped": "managed profile M identity unavailable"}
        write_json(output_dir / "receipts/native-managed-wheel-elf-boundary.json", managed_wheel)
        managed_before_reinstall = snapshot(managed)
        reinstall = run_capture("managed-reinstall", [str(uv), "python", "install", KEY, "--install-dir", str(managed), "--no-bin", "--python-downloads-json-url", catalog.resolve().as_uri(), "--offline", "--no-config", "--color", "never"], root, managed_env, output_dir / "process", timeout=900)
        process.append(reinstall)
        managed_after_reinstall = snapshot(managed)
        uninstall = run_capture("managed-uninstall", [str(uv), "python", "uninstall", "3.14.6", "--install-dir", str(managed), "--offline", "--no-config", "--color", "never"], root, find_env, output_dir / "process")
        process.append(uninstall)
        find_empty = run_capture("managed-find-empty", [str(uv), "python", "find", "3.14.6", "--managed-python", "--no-python-downloads", "--offline", "--python-downloads-json-url", catalog.resolve().as_uri(), "--no-config", "--color", "never"], root, find_env, output_dir / "process")
        process.append(find_empty)

        wheel = wheel_probe("successor-stripped-M", python, install, root / "wheel", system_env, output_dir / "process", readelf, None, perform_explicit_normalization=False)
        write_json(output_dir / "receipts/native-wheel-elf-boundary.json", wheel)

        candidate_identity = exact_identity(final_artifact)
        checks = {
            "accepted_install_only_identity": install_identity,
            "accepted_install_only_authority": authority.get("pass") is True,
            "assembly_1_distinct": assembly_receipts[0].get("decision") == "distinct-archive",
            "assembly_2_distinct": assembly_receipts[1].get("decision") == "distinct-archive",
            "byte_reproducible": reproducibility["pass"] is True and reproducibility["byte_identical"] is True,
            "candidate_identity_consistent": candidate_identity == reproducibility["first"] == reproducibility["second"],
            "candidate_member_count": verification.get("artifact", {}).get("member_count") == EXPECTED_INSTALL["member_count"],
            "regular_elf_count_81": receipt.get("regular_elf_count") == EXPECTED_REGULAR_ELF_COUNT,
            "eligible_elf_count_1": receipt.get("eligible_elf_count") == 1,
            "changed_elf_count_1": receipt.get("changed_elf_count") == 1,
            "only_project_launcher_changed": receipt.get("eligible_paths") == EXPECTED_CHANGED_PATHS and receipt.get("changed_paths") == EXPECTED_CHANGED_PATHS,
            "exact_stripped_derivation": verify_row["returncode"] == 0 and verification.get("pass") is True,
            "non_elf_bytes_unchanged": verification.get("checks", {}).get("non_elf_bytes_unchanged") is True,
            "elf_dynamic_alignment_preserved": verification.get("checks", {}).get("elf_dynamic_alignment_preserved") is True,
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

    install_after = exact_identity(install_only_archive)
    full_after = exact_identity(accepted_full) if accepted_full else None
    predecessor_after = exact_identity(predecessor_stripped) if predecessor_stripped else None
    authority_after = authority_snapshot()
    real_managed_after = snapshot(real_managed)
    checks.update({
        "accepted_install_only_unchanged": install_before == install_after,
        "accepted_full_unchanged": full_before == full_after,
        "predecessor_stripped_unchanged": predecessor_before == predecessor_after,
        "frozen_authorities_unchanged": authority_before == authority_after,
        "real_managed_root_unchanged": real_managed_before == real_managed_after,
        "technical_family_not_started": not any(path.name in {"release-index.json", "SHA256SUMS"} for path in (output_dir / "artifacts").iterdir()),
    })
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    result = {
        "schema_version": 1,
        "result_kind": "epoch3-rb3-profile-M-successor-stripped-owner-qualification",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "source_install_only": install_before,
        "artifact": {**exact_identity(final_artifact), "member_count": verification.get("artifact", {}).get("member_count")},
        "reproducibility": reproducibility,
        "strip_surface": {
            "operation": "llvm-strip --strip-unneeded",
            "regular_elf_count": receipt.get("regular_elf_count"),
            "eligible_elf_count": receipt.get("eligible_elf_count"),
            "changed_elf_count": receipt.get("changed_elf_count"),
            "eligible_paths": receipt.get("eligible_paths"),
            "changed_paths": receipt.get("changed_paths"),
            "strip_tool": receipt.get("strip_tool"),
            "readelf_tool": receipt.get("readelf_tool"),
        },
        "native_wheel_elf_boundary": wheel,
        "managed_native_wheel_elf_boundary": managed_wheel,
        "claim_boundary": {
            "successor_full_accepted": True,
            "successor_install_only_accepted": True,
            "successor_stripped_started": True,
            "successor_stripped_candidate": not failed,
            "successor_stripped_accepted": False,
            "successor_technical_family_started": False,
            "successor_technical_family_accepted": False,
            "predecessor_family_superseded": False,
            "portable_raw_wheel_claim": False,
            "user_built_wheel_postprocessing": "out-of-scope-external-tool-responsibility",
            "rb3_closed": False,
            "selectable": False,
            "publication": False,
        },
    }
    write_json(output_dir / "rb3-successor-stripped-m-result.json", result)
    write_json(output_dir / "protected-state.json", {
        "accepted_install_only_unchanged": install_before == install_after,
        "accepted_full": full_before,
        "accepted_full_unchanged": full_before == full_after,
        "predecessor_stripped": predecessor_before,
        "predecessor_stripped_unchanged": predecessor_before == predecessor_after,
        "authority_before": authority_before,
        "authority_after": authority_after,
        "frozen_authorities_unchanged": authority_before == authority_after,
        "real_managed_root": str(real_managed),
        "real_managed_root_unchanged": real_managed_before == real_managed_after,
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-only-archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--uv", type=Path, default=Path(shutil.which("uv") or "uv"))
    parser.add_argument("--strip-tool", required=True)
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--pkg-config", default="pkg-config")
    parser.add_argument("--accepted-full", type=Path, required=True)
    parser.add_argument("--predecessor-stripped", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(
            args.install_only_archive,
            args.output_dir,
            args.uv,
            strip_tool=args.strip_tool,
            readelf=args.readelf,
            pkg_config=args.pkg_config,
            accepted_full=args.accepted_full,
            predecessor_stripped=args.predecessor_stripped,
        )
    except Exception as exc:  # noqa: BLE001
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "rb3-successor-stripped-m-result.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())

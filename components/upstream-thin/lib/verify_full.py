#!/usr/bin/env python3
"""Verify the canonical full archive without broadening target claims."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from archive import safe_extract_tar, sha256_file, tree_manifest
from elf import elf_surface, is_elf, relative_runpath

FORBIDDEN_ACTIVE_BYTES = (
    b"/data/data/com.termux/files/usr",
    b"/data/data/com.termux/files/home",
    b"/Users/runner/",
    b"/home/runner/",
    b"LD_LIBRARY_PATH",
)
SYSTEM_LIBRARIES = {
    "libc.so", "libdl.so", "liblog.so", "libm.so", "libz.so",
}
FORBIDDEN_BUILD_INFO_KEYS = {"objs", "static_lib", "inittab_object", "inittab_source", "inittab_cflags"}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(checks: dict[str, bool], errors: list[str], name: str, condition: bool, detail: str = "") -> None:
    checks[name] = bool(condition)
    if not condition and detail:
        errors.append(f"{name}: {detail}")


def _forbidden_build_info(value: Any, path: str = "build_info") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in FORBIDDEN_BUILD_INFO_KEYS:
                hits.append(child)
            hits.extend(_forbidden_build_info(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(_forbidden_build_info(item, f"{path}[{index}]"))
    return hits


def _providers(install: Path, readelf: str) -> tuple[dict[str, str], list[Path]]:
    providers: dict[str, str] = {}
    objects = [path for path in sorted(install.rglob("*")) if is_elf(path)]
    for path in objects:
        surface = elf_surface(path, readelf)
        rel = path.relative_to(install).as_posix()
        providers[path.name] = rel
        for soname in surface["soname"]:
            providers[soname] = rel
    return providers, objects


def verify(archive: Path, *, zstd: str = "zstd", readelf: str = "readelf", fixture_mode: bool = False) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    metrics: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="verify-full-") as tmp:
        root = Path(tmp)
        tar_path = root / "artifact.tar"
        proc = subprocess.run([zstd, "-q", "-d", "-f", str(archive), "-o", str(tar_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _check(checks, errors, "zstd_decompress", proc.returncode == 0, proc.stderr.strip())
        if proc.returncode:
            return {"schema_version": 2, "pass": False, "checks": checks, "errors": errors}
        extracted = root / "tree"
        try:
            rows = safe_extract_tar(tar_path, extracted, "r:")
        except Exception as exc:  # noqa: BLE001
            return {"schema_version": 2, "pass": False, "checks": checks, "errors": [*errors, f"safe extraction: {type(exc).__name__}: {exc}"]}
        paths = {row["path"] for row in rows}
        _check(checks, errors, "one_python_root", bool(paths) and all(path == "python" or path.startswith("python/") for path in paths))
        _check(checks, errors, "required_roots", {"python", "python/build", "python/install", "python/PYTHON.json"}.issubset(paths))
        _check(checks, errors, "no_duplicate_members", len(paths) == len(rows))
        metrics["archive_member_count"] = len(rows)

        python_root = extracted / "python"
        install = python_root / "install"
        py_path = python_root / "PYTHON.json"
        manifest_path = python_root / "build/hw-t/full-member-manifest.json"
        input_path = python_root / "build/hw-t/input.json"
        mutation_path = python_root / "build/hw-t/mutations.json"
        launcher_record_path = python_root / "build/hw-t/launcher.json"

        try:
            py = _load(py_path)
            required_keys = {
                "version", "target_triple", "build_options", "python_tag", "python_abi_tag", "python_platform_tag",
                "python_implementation_cache_tag", "python_implementation_hex_version", "python_implementation_name",
                "python_implementation_version", "python_version", "python_major_minor_version", "python_paths",
                "python_paths_abstract", "python_config_vars", "python_exe", "python_suffixes", "libpython_link_mode",
                "python_extension_module_loading", "build_info", "licenses", "license_path",
            }
            _check(checks, errors, "python_json_format_8", py.get("version") == 8)
            _check(checks, errors, "python_json_target", py.get("target_triple") == "aarch64-linux-android")
            _check(checks, errors, "python_json_executable", py.get("python_exe") == "install/bin/python3.14")
            _check(checks, errors, "python_json_standard_key_floor", required_keys.issubset(py))
            _check(checks, errors, "python_json_no_project_extension", "hw_t" not in py)
            _check(checks, errors, "python_json_paths_exist", all((python_root / value).exists() for value in py.get("python_paths", {}).values()))
            _check(checks, errors, "python_json_license_exists", (python_root / py.get("license_path", "missing")).is_file())
            forbidden_info = _forbidden_build_info(py.get("build_info", {}))
            _check(checks, errors, "truthful_partial_build_info", not forbidden_info, str(forbidden_info))
            metrics["python_json_top_level_keys"] = sorted(py)
            metrics["python_json_extension_count"] = len(py.get("build_info", {}).get("extensions", {}))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"PYTHON.json: {type(exc).__name__}: {exc}")
            for key in ("python_json_format_8", "python_json_target", "python_json_executable", "python_json_standard_key_floor", "python_json_no_project_extension", "python_json_paths_exist", "python_json_license_exists", "truthful_partial_build_info"):
                checks[key] = False
            py = {}

        launcher = install / "bin/python3.14"
        _check(checks, errors, "launcher_present_executable", launcher.is_file() and bool(launcher.stat().st_mode & 0o111))
        alias_ok = all((install / f"bin/{name}").is_symlink() and os.readlink(install / f"bin/{name}") == "python3.14" for name in ("python", "python3"))
        _check(checks, errors, "launcher_aliases", alias_ok)
        pip_ok = all((install / f"bin/{name}").is_file() and bool((install / f"bin/{name}").stat().st_mode & 0o111) for name in ("pip", "pip3", "pip3.14")) if not fixture_mode else True
        _check(checks, errors, "pip_wrappers_present", pip_ok)

        try:
            manifest = _load(manifest_path)
            expected = manifest.get("members", [])
            actual = tree_manifest(python_root, exclude=manifest.get("excluded_paths", []))
            _check(checks, errors, "self_excluding_member_manifest_exact", expected == actual, f"expected={len(expected)} actual={len(actual)}")
        except Exception as exc:  # noqa: BLE001
            _check(checks, errors, "self_excluding_member_manifest_exact", False, f"{type(exc).__name__}: {exc}")

        try:
            input_record = _load(input_path)
            official = input_record.get("official_input", {})
            _check(checks, errors, "official_input_identity", fixture_mode or (official.get("filename") == "python-3.14.6-aarch64-linux-android.tar.gz" and official.get("size_bytes") == 22358404 and official.get("sha256") == "38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5"))
        except Exception as exc:  # noqa: BLE001
            _check(checks, errors, "official_input_identity", False, f"{type(exc).__name__}: {exc}")

        active_files = [path for path in install.rglob("*") if path.is_file() and not path.is_symlink()]
        active_files.append(py_path)
        residue: list[str] = []
        for path in active_files:
            data = path.read_bytes()
            for marker in FORBIDDEN_ACTIVE_BYTES:
                if marker in data:
                    residue.append(f"{path.relative_to(python_root).as_posix()}:{marker.decode(errors='replace')}")
        _check(checks, errors, "active_tree_host_neutral", not residue, str(residue[:20]))
        metrics["active_host_residue_count"] = len(residue)

        if fixture_mode:
            _check(checks, errors, "release_elf_inventory", True)
            _check(checks, errors, "release_lr3_exact", True)
            _check(checks, errors, "release_needed_closure", True)
            _check(checks, errors, "release_mutation_manifest_exact", True)
            metrics["elf_count"] = 0
        else:
            try:
                mutations = _load(mutation_path)
                mutation_rows = mutations.get("elf_objects", [])
                providers, objects = _providers(install, readelf)
                by_path = {row.get("path"): row for row in mutation_rows}
                object_paths = {path.relative_to(install).as_posix() for path in objects}
                _check(checks, errors, "release_elf_inventory", bool(objects) and set(by_path) == object_paths, f"objects={len(objects)} rows={len(by_path)}")
                lr3_errors: list[str] = []
                closure_errors: list[str] = []
                mutation_errors: list[str] = []
                for path in objects:
                    rel = path.relative_to(install).as_posix()
                    surface = elf_surface(path, readelf)
                    expected_runpath = relative_runpath(path, install / "lib")
                    if surface["machine"] != "AArch64" or surface["rpath"] or surface["runpath"] != [expected_runpath] or not surface["load_alignments"] or any(value != 0x4000 for value in surface["load_alignments"]):
                        lr3_errors.append(rel)
                    for needed in surface["needed"]:
                        if needed not in providers and needed not in SYSTEM_LIBRARIES:
                            closure_errors.append(f"{rel}:{needed}")
                    row = by_path.get(rel, {})
                    after = row.get("after", {})
                    if row.get("exact_mutation_check") is not True or row.get("expected_runpath") != expected_runpath or after.get("sha256") != surface["sha256"] or after.get("needed") != surface["needed"] or after.get("runpath") != surface["runpath"]:
                        mutation_errors.append(rel)
                _check(checks, errors, "release_lr3_exact", not lr3_errors, str(lr3_errors[:20]))
                _check(checks, errors, "release_needed_closure", not closure_errors, str(closure_errors[:20]))
                _check(checks, errors, "release_mutation_manifest_exact", not mutation_errors, str(mutation_errors[:20]))
                metrics["elf_count"] = len(objects)
                metrics["packaged_provider_count"] = len(providers)
                metrics["system_libraries"] = sorted(SYSTEM_LIBRARIES)
                normalization = mutations.get("runtime_metadata", {})
                _check(checks, errors, "runtime_metadata_normalized", normalization.get("normalization_kind") == "relocation-aware-runtime-and-on-device-sdk")
                pip_surface = mutations.get("pip_surface", {})
                _check(checks, errors, "pip_from_upstream_wheel", pip_surface.get("installation_kind") == "package-only-from-exact-upstream-ensurepip-wheel" and pip_surface.get("network_acquisition") is False)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"release ELF verification: {type(exc).__name__}: {exc}")
                for key in ("release_elf_inventory", "release_lr3_exact", "release_needed_closure", "release_mutation_manifest_exact", "runtime_metadata_normalized", "pip_from_upstream_wheel"):
                    checks[key] = False

        _check(checks, errors, "truthful_build_area", input_path.is_file() and mutation_path.is_file() and launcher_record_path.is_file())

    failed = sorted(key for key, passed in checks.items() if not passed)
    return {
        "schema_version": 2,
        "verifier_kind": "epoch3-upstream-thin-full-static-and-structural",
        "fixture_mode": fixture_mode,
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "metrics": metrics,
        "archive": {"path": str(archive), "sha256": sha256_file(archive), "size_bytes": archive.stat().st_size},
        "claim_boundary": {"target_runtime_qualified": False, "selectable": False, "publication": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("--zstd", default="zstd")
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = verify(Path(args.archive).resolve(), zstd=args.zstd, readelf=args.readelf, fixture_mode=args.fixture_mode)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify the canonical full archive without broadening target claims."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from archive import safe_extract_tar, sha256_file, tree_manifest
from elf import elf_surface, is_elf, relative_runpath

FORBIDDEN_OPERATIONAL_BYTES = (
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


def _parse_makefile(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(?::=|=)\s*(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def inspect_consumer_metadata(install: Path) -> dict[str, Any]:
    stdlib = install / "lib/python3.14"
    sysdata_files = sorted(stdlib.glob("_sysconfigdata_*.py"))
    sysvars_files = sorted(stdlib.glob("_sysconfig_vars_*.json"))
    if len(sysdata_files) != 1 or len(sysvars_files) != 1:
        return {"pass": False, "errors": ["expected exactly one sysconfigdata and sysconfig-vars file"]}
    sysdata = sysdata_files[0]
    namespace: dict[str, Any] = {"__file__": str(sysdata)}
    try:
        exec(compile(sysdata.read_text(encoding="utf-8"), str(sysdata), "exec"), namespace)  # noqa: S102
    except Exception as exc:  # noqa: BLE001
        return {"pass": False, "errors": [f"sysconfigdata execution: {type(exc).__name__}: {exc}"]}
    values = namespace.get("build_time_vars")
    if not isinstance(values, dict):
        return {"pass": False, "errors": ["build_time_vars missing"]}

    expected_paths = {
        "BINDIR": install / "bin",
        "LIBDIR": install / "lib",
        "LIBDEST": install / "lib/python3.14",
        "INCLUDEPY": install / "include/python3.14",
        "LIBPL": install / "lib/python3.14/config-3.14-aarch64-linux-android",
        "DESTSHARED": install / "lib/python3.14/lib-dynload",
    }
    errors: list[str] = []
    for key, expected in expected_paths.items():
        if values.get(key) != str(expected):
            errors.append(f"{key}={values.get(key)!r} expected={str(expected)!r}")
    expected_values = {
        "CC": "clang",
        "CXX": "clang++",
        "AR": "llvm-ar",
        "SOABI": "cpython-314-aarch64-linux-android",
        "MULTIARCH": "aarch64-linux-android",
        "EXT_SUFFIX": ".cpython-314-aarch64-linux-android.so",
        "HOST_GNU_TYPE": "aarch64-linux-android",
        "HW_T_METADATA_PROFILE": "upstream-preserved-minimal-consumer-overlay",
    }
    for key, expected in expected_values.items():
        if values.get(key) != expected:
            errors.append(f"{key}={values.get(key)!r} expected={expected!r}")
    if "consumer-normalized-binary-derived" in str(values.get("CONFIG_ARGS", "")):
        errors.append("CONFIG_ARGS synthetic provenance replacement remains")
    if values.get("BUILD_GNU_TYPE") == "aarch64-linux-android":
        errors.append("BUILD_GNU_TYPE was replaced by consumer target")
    header = sysdata.read_text(encoding="utf-8").splitlines()[0]
    if header != "# system configuration generated and used by the sysconfig module":
        errors.append(f"noncanonical sysconfig header: {header!r}")

    makefile_path = stdlib / "config-3.14-aarch64-linux-android/Makefile"
    makefile = _parse_makefile(makefile_path)
    expected_make = {
        "CC": "clang", "CXX": "clang++", "AR": "llvm-ar",
        "CFLAGS": "-fno-strict-overflow -Wsign-compare -Wunreachable-code -DNDEBUG -O2 -Wall -D__BIONIC_NO_PAGE_SIZE_MACRO",
        "LDFLAGS": "-Wl,--build-id=sha1 -Wl,--no-rosegment -Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384",
    }
    for key, expected in expected_make.items():
        if makefile.get(key) != expected:
            errors.append(f"Makefile {key}={makefile.get(key)!r} expected={expected!r}")
    if "lastword $(MAKEFILE_LIST)" not in makefile.get("prefix", ""):
        errors.append("Makefile prefix is not location-relative")
    if "consumer-normalized-binary-derived" in makefile.get("CONFIG_ARGS", ""):
        errors.append("Makefile CONFIG_ARGS synthetic provenance replacement remains")

    pkg_rows: list[dict[str, str]] = []
    for path in sorted((install / "lib/pkgconfig").glob("*.pc")):
        if path.is_symlink():
            continue
        text = path.read_text(encoding="utf-8")
        prefix = next((line.split("=", 1)[1] for line in text.splitlines() if line.startswith("prefix=")), "")
        pkg_rows.append({"path": path.name, "prefix": prefix})
        if prefix != "${pcfiledir}/../..":
            errors.append(f"pkg-config prefix not relative: {path.name}={prefix!r}")
        if any(marker.decode() in text for marker in FORBIDDEN_OPERATIONAL_BYTES):
            errors.append(f"pkg-config contains forbidden operational path: {path.name}")

    config_entry = install / "bin/python3.14-config"
    if not config_entry.is_file() or not bool(config_entry.stat().st_mode & 0o111):
        errors.append("dynamic python3.14-config entry missing")
    elif any(marker.decode() in config_entry.read_text(encoding="utf-8") for marker in FORBIDDEN_OPERATIONAL_BYTES):
        errors.append("python3.14-config contains forbidden operational path")

    build_details = _load(stdlib / "build-details.json")
    if build_details.get("base_interpreter") != "bin/python3.14" or build_details.get("base_prefix") != ".":
        errors.append("build-details runtime paths are not relative")

    return {
        "pass": not errors,
        "errors": errors,
        "header": header,
        "effective": {key: values.get(key) for key in (*expected_paths, *expected_values)},
        "preserved_producer": {
            "BUILD_GNU_TYPE": values.get("BUILD_GNU_TYPE"),
            "CONFIG_ARGS": values.get("CONFIG_ARGS"),
        },
        "sysconfig_vars_sha256": sha256_file(sysvars_files[0]),
        "pkgconfig": pkg_rows,
    }


def classify_host_residue(python_root: Path, install: Path) -> dict[str, list[str]]:
    """Separate executable consumer surfaces from preserved producer records.

    `_sysconfigdata_`, `_sysconfig_vars_`, and the Makefile deliberately retain
    producer facts. Their effective consumer values are verified semantically by
    `inspect_consumer_metadata`; raw byte scanning would incorrectly reject the
    selected upstream-preserving profile M.
    """
    operational: set[Path] = set()
    operational.update(
        path for path in (install / "bin").glob("*")
        if path.is_file() and not path.is_symlink() and not is_elf(path)
    )
    stdlib = install / "lib/python3.14"
    for pattern in ("build-details.json", "config-*/python-config.py", "config-*/pybuilddir.txt"):
        operational.update(path for path in stdlib.glob(pattern) if path.is_file())
    operational.update(path for path in (install / "lib/pkgconfig").glob("*.pc") if path.is_file())

    provenance: set[Path] = {python_root / "PYTHON.json"}
    for pattern in ("_sysconfigdata_*.py", "_sysconfig_vars_*.json", "config-*/Makefile"):
        provenance.update(path for path in stdlib.glob(pattern) if path.is_file())

    operational_hits: list[str] = []
    informational_hits: list[str] = []
    for path in sorted(path for path in python_root.rglob("*") if path.is_file() and not path.is_symlink()):
        data = path.read_bytes()
        for marker in FORBIDDEN_OPERATIONAL_BYTES:
            if marker not in data:
                continue
            row = f"{path.relative_to(python_root).as_posix()}:{marker.decode(errors='replace')}"
            if path in operational:
                operational_hits.append(row)
            else:
                informational_hits.append(row)
    return {
        "operational": operational_hits,
        "informational_upstream_provenance": informational_hits,
    }

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

        residue = classify_host_residue(python_root, install)
        operational_residue = residue["operational"]
        informational_residue = residue["informational_upstream_provenance"]
        _check(
            checks,
            errors,
            "active_tree_host_neutral",
            not operational_residue,
            str(operational_residue[:20]),
        )
        metrics["active_host_residue_count"] = len(operational_residue)
        metrics["informational_upstream_provenance_residue_count"] = len(informational_residue)
        metrics["informational_upstream_provenance_residue"] = informational_residue[:40]

        if fixture_mode:
            _check(checks, errors, "effective_consumer_metadata", True)
        else:
            consumer_metadata = inspect_consumer_metadata(install)
            _check(checks, errors, "effective_consumer_metadata", consumer_metadata.get("pass") is True, str(consumer_metadata.get("errors", [])))
            metrics["consumer_metadata"] = consumer_metadata

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
                _check(checks, errors, "runtime_metadata_normalized", normalization.get("normalization_kind") == "upstream-preserved-minimal-consumer-overlay" and normalization.get("selected_profile") == "M" and normalization.get("producer_provenance_preserved") is True and normalization.get("sysconfig_vars_json", {}).get("mutation") == "preserved-upstream-byte-exact")
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

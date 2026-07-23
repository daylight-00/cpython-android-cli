#!/usr/bin/env python3
"""Run bounded Android qualification against an install-only archive."""
from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from archive import safe_extract_tar, sha256_file
from qualify_full import _chmod_read_only, _clean_env, _has_external_termux_prefix, _json_probe, _restore_owner_write, _run, _runtime_code


def extension_modules(prefix: Path) -> list[str]:
    directory = prefix / "lib/python3.14/lib-dynload"
    suffix = ".cpython-314-aarch64-linux-android.so"
    modules = []
    for path in sorted(directory.glob(f"*{suffix}")):
        modules.append(path.name[:-len(suffix)])
    return modules


def qualify(archive: Path, *, output: Path | None = None, pkg_config: str = "pkg-config") -> dict[str, Any]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    evidence: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="qualify-install-only-") as tmp:
        root = Path(tmp)
        tar_path = root / "install-only.tar"
        try:
            with gzip.open(archive, "rb") as source, tar_path.open("wb") as target:
                shutil.copyfileobj(source, target)
            checks["decompress"] = True
        except Exception as exc:  # noqa: BLE001
            checks["decompress"] = False
            errors.append(f"{type(exc).__name__}: {exc}")
        if checks["decompress"]:
            extracted = root / "extracted"
            safe_extract_tar(tar_path, extracted, "r:")
            source_prefix = extracted / "python"
            checks["direct_archive_root"] = source_prefix.is_dir() and sorted(path.name for path in extracted.iterdir()) == ["python"]
            modules = extension_modules(source_prefix)
            runtime_a = root / "runtime-a/prefix"
            runtime_a.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_prefix), runtime_a)
            python_a = runtime_a / "bin/python3.14"
            env_a = _clean_env(runtime_a, root / "state-a")
            probe_a = _json_probe(python_a, _runtime_code(modules), env_a, 420)
            evidence["runtime_location_a"] = probe_a
            checks["runtime_location_a"] = probe_a["pass"]

            runtime_b = root / "relocated/deep/path/prefix"
            runtime_b.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(runtime_a), runtime_b)
            python_b = runtime_b / "bin/python3.14"
            env_b = _clean_env(runtime_b, root / "state-b")
            probe_b = _json_probe(python_b, _runtime_code(modules), env_b, 420)
            evidence["runtime_location_b"] = probe_b
            checks["whole_prefix_relocation"] = probe_b["pass"]

            command_rows = {name: _run([str(runtime_b / "bin" / name), "-c", "import json,sys;print(json.dumps({'pass':True,'executable':sys.executable}))"], env=env_b) for name in ("python", "python3", "python3.14")}
            checks["python_alias_commands"] = all(row["returncode"] == 0 for row in command_rows.values())
            evidence["python_alias_commands"] = command_rows

            pip_rows = {}
            for name in ("module", "pip", "pip3", "pip3.14"):
                command = [str(python_b), "-m", "pip", "--version"] if name == "module" else [str(runtime_b / "bin" / name), "--version"]
                pip_rows[name] = _run(command, env=env_b)
            checks["pip_surface"] = all(row["returncode"] == 0 and "pip " in row["stdout"] for row in pip_rows.values())
            evidence["pip_surface"] = pip_rows

            config_rows = {option: _run([str(runtime_b / "bin/python3.14-config"), option], env=env_b) for option in ("--prefix", "--exec-prefix", "--includes", "--cflags", "--libs", "--ldflags", "--extension-suffix", "--configdir")}
            checks["python_config_surface"] = all(row["returncode"] == 0 and not _has_external_termux_prefix(row["stdout"] + row["stderr"], runtime_b) for row in config_rows.values())
            evidence["python_config_surface"] = config_rows

            pc_env = dict(env_b)
            pc_env["PKG_CONFIG_PATH"] = pc_env["PKG_CONFIG_LIBDIR"] = str(runtime_b / "lib/pkgconfig")
            pkg_rows = {package: _run([pkg_config, "--cflags", "--libs", package], env=pc_env) for package in ("python-3.14", "python-3.14-embed")}
            checks["pkg_config_surface"] = all(row["returncode"] == 0 and str(runtime_b) in row["stdout"] and not _has_external_termux_prefix(row["stdout"] + row["stderr"], runtime_b) for row in pkg_rows.values())
            evidence["pkg_config_surface"] = pkg_rows

            venv = root / "state-b/venvs/fresh"
            create = _run([str(python_b), "-m", "venv", "--without-pip", "--symlinks", str(venv)], env=env_b, timeout=300)
            probe = _json_probe(venv / "bin/python", "import json,sys;print(json.dumps({'pass':sys.prefix!=sys.base_prefix}))", env_b)
            checks["fresh_venv"] = create["returncode"] == 0 and probe["pass"]
            evidence["fresh_venv"] = {"create": create, "probe": probe}

            _chmod_read_only(runtime_b)
            read_only = _json_probe(python_b, _runtime_code(modules), _clean_env(runtime_b, root / "state-read-only"), 420)
            checks["read_only_install"] = read_only["pass"]
            evidence["read_only_install"] = read_only
            _restore_owner_write(runtime_b)

            checks["all_67_extensions"] = (
                len(modules) == 67
                and (probe_a.get("data") or {}).get("extension_count") == 67
                and (probe_b.get("data") or {}).get("extension_count") == 67
            )
            evidence["device"] = {
                "uname": _run(["uname", "-a"], env=env_b),
                "getprop_sdk": _run(["getprop", "ro.build.version.sdk"], env=env_b),
                "getprop_release": _run(["getprop", "ro.build.version.release"], env=env_b),
                "python_sysconf_pagesize": _run([str(python_b), "-c", "import os;print(os.sysconf('SC_PAGE_SIZE'))"], env=env_b),
                "id": _run(["id"], env=env_b),
                "execution_context": "Termux app process used only as an Android/Bionic qualification context",
            }
    failed = sorted(key for key, value in checks.items() if value is not True)
    result = {
        "schema_version": 1,
        "qualification_kind": "epoch3-canonical-install-only-android-target",
        "pass": not failed and not errors,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "evidence": evidence,
        "archive": {"path": str(archive), "sha256": sha256_file(archive), "size_bytes": archive.stat().st_size},
        "claim_boundary": {"qualified_context": "current owner Termux app process on Android/Bionic", "install_only_authority_frozen": False, "stripped_started": False, "selectable": False, "publication": False, "api24_runtime_claim": False, "actual_16k_runtime_claim": False, "non_termux_context_claim": False},
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("--output")
    parser.add_argument("--pkg-config", default="pkg-config")
    args = parser.parse_args()
    result = qualify(Path(args.archive).resolve(), output=Path(args.output).resolve() if args.output else None, pkg_config=args.pkg_config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

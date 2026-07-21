#!/usr/bin/env python3
"""Verify canonical full archive structure without making target claims."""
from __future__ import annotations

import argparse
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from archive import safe_extract_tar, sha256_file

FORBIDDEN_TEXT = ("/data/data/com.termux/", "/Users/runner/", "/home/runner/", "LD_LIBRARY_PATH")


def verify(archive: Path, zstd: str = "zstd") -> dict[str, Any]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="verify-full-") as tmp:
        root = Path(tmp)
        tar_path = root / "artifact.tar"
        proc = subprocess.run([zstd, "-q", "-d", "-f", str(archive), "-o", str(tar_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        checks["zstd_decompress"] = proc.returncode == 0
        if proc.returncode:
            errors.append(proc.stderr.strip())
            return {"schema_version": 1, "pass": False, "checks": checks, "errors": errors}
        extracted = root / "tree"
        rows = safe_extract_tar(tar_path, extracted, "r:")
        paths = {row["path"] for row in rows}
        checks["one_python_root"] = bool(paths) and all(path == "python" or path.startswith("python/") for path in paths)
        checks["required_roots"] = {"python", "python/build", "python/install", "python/PYTHON.json"}.issubset(paths)
        checks["no_duplicate_members"] = len(paths) == len(rows)
        py_path = extracted / "python/PYTHON.json"
        try:
            py = json.loads(py_path.read_text(encoding="utf-8"))
            checks["python_json_format_8"] = py.get("version") == 8
            checks["python_json_target"] = py.get("target_triple") == "aarch64-linux-android"
            checks["python_json_executable"] = py.get("python_exe") == "install/bin/python3.14"
            checks["python_json_no_project_extension"] = "hw_t" not in py
            text = py_path.read_text(encoding="utf-8")
            checks["python_json_host_neutral"] = not any(marker in text for marker in FORBIDDEN_TEXT)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"PYTHON.json: {type(exc).__name__}: {exc}")
            for key in ("python_json_format_8", "python_json_target", "python_json_executable", "python_json_no_project_extension", "python_json_host_neutral"):
                checks[key] = False
        launcher = extracted / "python/install/bin/python3.14"
        checks["launcher_present_executable"] = launcher.is_file() and bool(launcher.stat().st_mode & 0o111)
        checks["launcher_aliases"] = all((extracted / f"python/install/bin/{name}").is_symlink() for name in ("python", "python3"))
        checks["truthful_build_area"] = (extracted / "python/build/hw-t/input.json").is_file() and (extracted / "python/build/hw-t/mutations.json").is_file()
    failed = sorted(key for key, passed in checks.items() if not passed)
    return {"schema_version": 1, "verifier_kind": "epoch3-upstream-thin-full-structural", "pass": not failed, "checks": dict(sorted(checks.items())), "failed_checks": failed, "errors": errors, "archive": {"sha256": sha256_file(archive), "size_bytes": archive.stat().st_size}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("--zstd", default="zstd")
    args = parser.parse_args()
    result = verify(Path(args.archive).resolve(), args.zstd)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

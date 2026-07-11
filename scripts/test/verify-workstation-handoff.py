#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_kv(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True, type=Path)
    parser.add_argument("--promoted-prefix", required=True, type=Path)
    parser.add_argument("--product-lock", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--readelf", default="readelf")
    args = parser.parse_args()

    lock = json.loads(args.product_lock.read_text())
    filename = lock["archive"]["filename"]
    archive = args.out_root / "cpython" / filename
    checksums = args.out_root / "cpython" / "SHA256SUMS"
    launcher = args.out_root / "bin" / "python3.14"
    build_info_path = args.out_root / "metadata" / "build-info.txt"
    product_path = args.out_root / "metadata" / "cpython-product.json"

    for path in [
        archive, checksums, launcher, build_info_path, product_path,
    ]:
        if not path.is_file():
            raise SystemExit(f"missing handoff file: {path}")

    build_info = parse_kv(build_info_path)
    product = json.loads(product_path.read_text())
    archive_hash = sha256(archive)
    launcher_hash = sha256(launcher)

    checksum_line = checksums.read_text().strip()
    expected_checksum_line = (
        f"{lock['archive']['sha256']}  {lock['archive']['filename']}"
    )

    dynamic = subprocess.run(
        [args.readelf, "-dW", str(launcher)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    needed = sorted(re.findall(r"\(NEEDED\).*?\[(.*?)\]", dynamic))
    runpath = re.findall(r"\(RUNPATH\).*?\[(.*?)\]", dynamic)

    checks = {
        "archive_size": archive.stat().st_size == lock["archive"]["size_bytes"],
        "archive_sha256": archive_hash == lock["archive"]["sha256"],
        "checksum_sidecar": checksum_line == expected_checksum_line,
        "product_pass": product.get("pass") is True,
        "product_source_head": (
            product.get("source_head") == lock["source_head"]
        ),
        "product_archive_sha256": (
            product.get("canonical_archive_sha256")
            == lock["archive"]["sha256"]
        ),
        "launcher_hash_recorded": build_info.get("sha256") == launcher_hash,
        "launcher_promoted_prefix": (
            build_info.get("cpython_dev_prefix")
            == str(args.promoted_prefix.resolve())
        ),
        "launcher_contract_python_h": (
            build_info.get("python_h_sha256")
            == lock["launcher_development_contract"][
                "include/python3.14/Python.h"
            ]["sha256"]
        ),
        "launcher_contract_pyconfig_h": (
            build_info.get("pyconfig_h_sha256")
            == lock["launcher_development_contract"][
                "include/python3.14/pyconfig.h"
            ]["sha256"]
        ),
        "launcher_contract_libpython": (
            build_info.get("libpython_sha256")
            == lock["launcher_development_contract"][
                "lib/libpython3.14.so"
            ]["sha256"]
        ),
        "launcher_needed": needed == sorted([
            "libc.so",
            "libdl.so",
            "liblog.so",
            "libm.so",
            "libpython3.14.so",
        ]),
        "launcher_runpath": runpath == ["$ORIGIN/../lib"],
    }

    result = {
        "schema_version": 1,
        "out_root": str(args.out_root.resolve()),
        "archive": {
            "path": str(archive.resolve()),
            "size_bytes": archive.stat().st_size,
            "sha256": archive_hash,
        },
        "launcher": {
            "path": str(launcher.resolve()),
            "size_bytes": launcher.stat().st_size,
            "sha256": launcher_hash,
            "needed": needed,
            "runpath": runpath,
        },
        "checks": checks,
        "pass": all(checks.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Result: {args.output}")
    print(
        "STAGE3B_WORKSTATION_HANDOFF="
        + ("PASS" if result["pass"] else "FAIL")
    )
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Install the exact upstream-carried pip wheel and Android-safe command wrappers."""
from __future__ import annotations

import os
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from archive import sha256_file


def _safe_wheel_path(name: str) -> str:
    if not name or name.startswith("/") or "\\" in name or "\x00" in name:
        raise ValueError(f"unsafe wheel member: {name!r}")
    parts = PurePosixPath(name).parts
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"unsafe wheel member: {name!r}")
    return PurePosixPath(*parts).as_posix()


def install_upstream_pip(install: Path) -> dict[str, Any]:
    bundled = install / "lib/python3.14/ensurepip/_bundled"
    wheels = sorted(bundled.glob("pip-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected exactly one upstream-carried pip wheel, got {[path.name for path in wheels]}")
    wheel = wheels[0]
    match = re.fullmatch(r"pip-([0-9][A-Za-z0-9_.-]*)-py3-none-any\.whl", wheel.name)
    if not match:
        raise RuntimeError(f"unexpected upstream pip wheel name: {wheel.name}")
    site = install / "lib/python3.14/site-packages"
    site.mkdir(parents=True, exist_ok=True)
    extracted: list[dict[str, Any]] = []
    seen: set[str] = set()
    with zipfile.ZipFile(wheel) as archive:
        for info in sorted(archive.infolist(), key=lambda row: row.filename):
            name = _safe_wheel_path(info.filename.rstrip("/")) if info.filename.rstrip("/") else ""
            if not name:
                continue
            if name in seen:
                raise RuntimeError(f"duplicate pip wheel member: {name}")
            seen.add(name)
            target = site / name
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            data = archive.read(info)
            target.write_bytes(data)
            mode = (info.external_attr >> 16) & 0o7777
            os.chmod(target, mode or 0o644)
            extracted.append({"path": target.relative_to(install).as_posix(), "sha256": sha256_file(target), "size_bytes": len(data)})
    wrappers: list[dict[str, Any]] = []
    (install / "bin").mkdir(parents=True, exist_ok=True)
    wrapper_text = (
        "#!/system/bin/sh\n"
        "case \"$0\" in /*) _hw_script=\"$0\" ;; *) _hw_script=\"$(pwd)/$0\" ;; esac\n"
        "_hw_bindir=${_hw_script%/*}\n"
        "exec \"$_hw_bindir/python3.14\" -m pip \"$@\"\n"
    )
    for name in ("pip", "pip3", "pip3.14"):
        path = install / "bin" / name
        path.write_text(wrapper_text, encoding="utf-8")
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        wrappers.append({"path": path.relative_to(install).as_posix(), "sha256": sha256_file(path), "launcher": "relative-bin/python3.14 -m pip"})
    return {
        "schema_version": 1,
        "installation_kind": "package-only-from-exact-upstream-ensurepip-wheel",
        "wheel": {"path": wheel.relative_to(install).as_posix(), "filename": wheel.name, "version": match.group(1), "sha256": sha256_file(wheel), "size_bytes": wheel.stat().st_size},
        "extracted_file_count": len(extracted),
        "extracted_files": extracted,
        "wrappers": wrappers,
        "network_acquisition": False,
    }

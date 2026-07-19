#!/usr/bin/env python3
"""Independent audit for the UT-1 Astral artifact prototype."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

PACKAGE_NAME = "python-3.14.6-aarch64-linux-android.tar.gz"
PACKAGE_SHA256 = "38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5"
REQUIRED = [
    "PYTHON.json",
    "artifact-contract.json",
    "python-json-schema-mapping.json",
    "unavailable-field-policy.json",
    "deterministic-derivation-rules.json",
    "archive-root-and-path-contract.json",
    "artifact-flavor-decision-inputs.json",
    "consumer-extraction-contract.json",
    "artifact-set.json",
    "full.manifest.json",
    "install_only.manifest.json",
    "install_only_stripped.manifest.json",
    "strip-mutations.json",
    "official-extraction-verification.json",
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def safe_path(path: str) -> bool:
    if not path or path.startswith("/") or "\\" in path or "\x00" in path:
        return False
    return all(p not in {"", ".", ".."} for p in PurePosixPath(path).parts)


def safe_link(path: str, target: str) -> bool:
    if not target or target.startswith("/") or "\\" in target:
        return False
    parts = list(PurePosixPath(path).parent.parts)
    for p in PurePosixPath(target).parts:
        if p in {"", "."}:
            continue
        if p == "..":
            if not parts:
                return False
            parts.pop()
        else:
            parts.append(p)
    return bool(parts) and parts[0] == "python"


def open_archive(path: Path, temp: Path) -> tuple[tarfile.TarFile, Path | None]:
    if path.name.endswith(".tar.gz"):
        return tarfile.open(path, "r:gz"), None
    if path.name.endswith(".tar.zst"):
        raw = temp / (path.stem + ".tar")
        with raw.open("wb") as f:
            subprocess.run(["zstd", "-q", "-d", "-c", str(path)], stdout=f, check=True)
        return tarfile.open(raw, "r:"), raw
    raise ValueError(f"unsupported archive: {path}")


def archive_rows(path: Path, temp: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    tf, raw = open_archive(path, temp)
    try:
        for m in tf.getmembers():
            row: dict[str, Any] = {"path": m.name, "mode": f"{m.mode & 0o7777:04o}"}
            if not safe_path(m.name):
                errors.append(f"unsafe-path:{m.name}")
            if not (m.isdir() or m.isfile() or m.issym()) or m.islnk() or m.isdev() or m.isfifo():
                errors.append(f"unsafe-type:{m.name}")
            if any((m.mtime != 0, m.uid != 0, m.gid != 0, m.uname != "", m.gname != "")):
                errors.append(f"unnormalized-header:{m.name}")
            if m.isdir():
                row["type"] = "directory"
            elif m.isfile():
                src = tf.extractfile(m)
                if src is None:
                    errors.append(f"missing-bytes:{m.name}")
                    continue
                h = hashlib.sha256(); size = 0
                for block in iter(lambda: src.read(1024 * 1024), b""):
                    size += len(block); h.update(block)
                row.update(type="file", size=size, sha256=h.hexdigest())
            elif m.issym():
                if not safe_link(m.name, m.linkname):
                    errors.append(f"unsafe-link:{m.name}")
                row.update(type="symlink", linkname=m.linkname)
            rows.append(row)
    finally:
        tf.close()
        if raw is not None:
            raw.unlink(missing_ok=True)
    return rows, errors


def normalize_mode(value: str) -> str:
    return f"{int(value, 8):04o}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--artifact-dir", type=Path, required=True)
    ap.add_argument("--audit-output", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    out = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    artifacts = args.artifact_dir.resolve()
    checks: dict[str, bool] = {}
    errors: dict[str, Any] = {}

    missing = [name for name in REQUIRED if not (out / name).is_file()]
    checks["required_outputs"] = not missing
    if missing:
        errors["missing"] = missing

    parsed: dict[str, Any] = {}
    for name in REQUIRED:
        p = out / name
        if not p.is_file():
            continue
        try:
            parsed[name] = load(p)
        except Exception as exc:
            errors.setdefault("parse", {})[name] = str(exc)
    checks["json_parse"] = "parse" not in errors

    artifact_set = parsed.get("artifact-set.json", {})
    rows = artifact_set.get("artifacts", []) if isinstance(artifact_set, dict) else []
    checks["artifact_set_shape"] = isinstance(rows, list) and {r.get("flavor") for r in rows if isinstance(r, dict)} == {"full", "install_only", "install_only_stripped"}
    refs = {r.get("flavor"): r for r in rows if isinstance(r, dict)}
    for flavor, row in refs.items():
        ref = row.get("archive", {})
        p = artifacts / ref.get("filename", "")
        checks[f"{flavor}_archive_ref"] = p.is_file() and sha(p) == ref.get("sha256") and p.stat().st_size == ref.get("size")

    expected = load(root / "experiments/epoch2-upstream-thin-control/package-and-file-hashes.json")
    prefix_expected = {r["path"]: r for r in expected["members"] if r["path"] == "prefix" or r["path"].startswith("prefix/")}
    strip = parsed.get("strip-mutations.json", {})
    strip_by_path = {r["path"]: r for r in strip.get("rows", []) if isinstance(r, dict)} if isinstance(strip, dict) else {}

    observed_by_flavor: dict[str, dict[str, dict[str, Any]]] = {}
    with tempfile.TemporaryDirectory(prefix="ut1-audit-") as td:
        temp = Path(td)
        for flavor, row in refs.items():
            p = artifacts / row["archive"]["filename"]
            if not p.is_file():
                continue
            try:
                observed, archive_errors = archive_rows(p, temp)
            except Exception as exc:
                errors.setdefault("archive_open", {})[flavor] = str(exc)
                continue
            observed_by_flavor[flavor] = {r["path"]: r for r in observed}
            checks[f"{flavor}_archive_safety"] = not archive_errors
            if archive_errors:
                errors.setdefault("archive_safety", {})[flavor] = archive_errors[:50]
            manifest = parsed.get(f"{flavor}.manifest.json", {})
            manifest_rows = manifest.get("members", []) if isinstance(manifest, dict) else []
            checks[f"{flavor}_manifest_exact"] = observed == manifest_rows and manifest.get("member_count") == len(observed)

    full = observed_by_flavor.get("full", {})
    install = observed_by_flavor.get("install_only", {})
    stripped = observed_by_flavor.get("install_only_stripped", {})
    checks["full_root_contract"] = all(p in full for p in ("python", "python/PYTHON.json", "python/build", "python/install"))
    checks["install_only_root_contract"] = "python" in install and not any(p == "python/PYTHON.json" or p.startswith("python/build/") for p in install)
    checks["stripped_root_contract"] = "python" in stripped and not any(p == "python/PYTHON.json" or p.startswith("python/build/") for p in stripped)
    checks["no_interpreter_executable"] = not any(p.startswith("python/bin/") for p in install) and not any(p.startswith("python/install/bin/") for p in full)

    exact_errors: list[str] = []
    for src_path, want in prefix_expected.items():
        suffix = src_path.removeprefix("prefix")
        full_path = "python/install" + suffix
        install_path = "python" + suffix
        for flavor, path, observed in (("full", full_path, full), ("install_only", install_path, install)):
            got = observed.get(path)
            if not got:
                exact_errors.append(f"missing:{flavor}:{path}")
                continue
            kind_map = {"file": "file", "directory": "directory", "symlink": "symlink"}
            if got.get("type") != kind_map[want["type"]]:
                exact_errors.append(f"type:{flavor}:{path}")
            if normalize_mode(want["mode"]) != got.get("mode"):
                exact_errors.append(f"mode:{flavor}:{path}")
            if want["type"] == "file" and (got.get("sha256") != want.get("sha256") or got.get("size") != want.get("size")):
                exact_errors.append(f"bytes:{flavor}:{path}")
            if want["type"] == "symlink" and got.get("linkname") != want.get("linkname"):
                exact_errors.append(f"link:{flavor}:{path}")
    checks["official_install_bytes_exact"] = not exact_errors
    if exact_errors:
        errors["official_exact"] = exact_errors[:100]

    strip_errors: list[str] = []
    for path, got in stripped.items():
        base = install.get(path)
        if base is None:
            strip_errors.append(f"extra:{path}")
            continue
        if got["type"] != base["type"] or got.get("mode") != base.get("mode") or got.get("linkname") != base.get("linkname"):
            strip_errors.append(f"shape:{path}")
            continue
        if got["type"] == "file":
            mutation = strip_by_path.get(path)
            if mutation:
                if base.get("sha256") != mutation.get("before_sha256") or got.get("sha256") != mutation.get("after_sha256"):
                    strip_errors.append(f"mutation:{path}")
            elif got.get("sha256") != base.get("sha256") or got.get("size") != base.get("size"):
                strip_errors.append(f"non-elf-changed:{path}")
    checks["stripped_mutations_bounded"] = not strip_errors and len(strip_by_path) == strip.get("elf_count") and len(strip_by_path) > 0
    if strip_errors:
        errors["stripped"] = strip_errors[:100]

    original_member = full.get(f"python/build/upstream/package/{PACKAGE_NAME}", {})
    checks["full_retains_official_archive"] = original_member.get("sha256") == PACKAGE_SHA256

    py = parsed.get("PYTHON.json", {})
    checks["python_json_v8"] = py.get("version") == 8 and py.get("target_triple") == "aarch64-linux-android" and py.get("python_version") == "3.14.6"
    checks["python_exe_explicitly_unavailable"] = py.get("python_exe", "sentinel") is None and py.get("hw_t", {}).get("availability", {}).get("python_exe") == "unavailable-official-package"
    core = py.get("build_info", {}).get("core", {})
    ext = py.get("build_info", {}).get("extensions", {})
    forbidden_core = {"objs", "static_lib", "inittab_object", "inittab_source", "inittab_cflags"}
    checks["no_fabricated_core_surfaces"] = not (forbidden_core & set(core)) and core.get("shared_lib") == "install/lib/libpython3.14.so"
    checks["no_fabricated_extension_surfaces"] = isinstance(ext, dict) and all(not ({"objs", "static_lib"} & set(candidate)) for variants in ext.values() for candidate in variants)
    checks["extensions_mapped"] = isinstance(ext, dict) and len(ext) == 67

    policy = parsed.get("unavailable-field-policy.json", {})
    checks["unavailable_policy"] = policy.get("fields", {}).get("python_exe") == "null-with-hw_t-availability"
    contract = parsed.get("artifact-contract.json", {})
    consumer = parsed.get("consumer-extraction-contract.json", {})
    decisions = parsed.get("artifact-flavor-decision-inputs.json", {})
    checks["unselectable_contract"] = contract.get("selectable") is False and consumer.get("full", {}).get("direct_runtime_entry") is None and decisions.get("epoch3_selection") is False
    checks["extraction_verification"] = parsed.get("official-extraction-verification.json", {}).get("pass") is True

    failed = sorted(k for k, v in checks.items() if not v)
    result = {
        "schema_version": 1,
        "audit_kind": "e2-r1-ut1-independent-audit",
        "pass": not failed and not errors,
        "check_count": len(checks),
        "pass_count": sum(1 for v in checks.values() if v),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "errors": errors,
        "blockers": [] if not failed and not errors else ["artifact-prototype-audit-failed"],
        "claim_boundary": "Artifact structure and deterministic derivation only; no Android runtime, launcher, relocation, selection, or publication claim.",
    }
    target = args.audit_output or (out / "independent-audit.json")
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

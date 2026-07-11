#!/usr/bin/env python3
from __future__ import annotations

import argparse, ast, hashlib, json
from pathlib import Path

KEYS = [
    "CONFIG_ARGS", "AR", "CC", "CXX", "CFLAGS", "LDFLAGS",
    "CONFIGURE_CFLAGS", "CONFIGURE_LDFLAGS", "PYTHON_FOR_BUILD",
    "PYTHON_FOR_FREEZE", "BUILD_GNU_TYPE", "HOST_GNU_TYPE", "prefix",
    "exec_prefix", "LIBDIR", "INCLUDEPY", "DESTSHARED", "TZPATH",
    "SOABI", "EXT_SUFFIX", "MULTIARCH",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_sysconfig(path: Path) -> dict:
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "build_time_vars"
            for t in node.targets
        ):
            values = ast.literal_eval(node.value)
            return {key: values.get(key) for key in KEYS if key in values}
    raise RuntimeError(f"build_time_vars not found: {path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text())
    prefix = Path(plan["expected_prefix"]).resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    if not prefix.is_dir():
        raise SystemExit(f"missing replay prefix: {prefix}")

    file_count = 0
    symlink_count = 0
    elf_count = 0
    total_bytes = 0
    for path in prefix.rglob("*"):
        if path.is_symlink():
            symlink_count += 1
        elif path.is_file():
            file_count += 1
            total_bytes += path.stat().st_size
            try:
                with path.open("rb") as f:
                    if f.read(4) == b"\x7fELF":
                        elf_count += 1
            except OSError:
                pass

    sysconfigs = []
    for path in sorted(prefix.glob("lib/python*/_sysconfigdata__android_*.py")):
        sysconfigs.append({
            "path": str(path),
            "relative_path": str(path.relative_to(prefix)),
            "sha256": sha256(path),
            "selected_build_time_vars": parse_sysconfig(path),
        })

    key_candidates = []
    for pattern in [
        "include/python*/Python.h",
        "include/python*/pyconfig.h",
        "lib/libpython*.so",
    ]:
        key_candidates.extend(sorted(prefix.glob(pattern)))

    key_artifacts = [
        {
            "path": str(path),
            "relative_path": str(path.relative_to(prefix)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in key_candidates
        if path.is_file()
    ]

    result = {
        "schema_version": 1,
        "source_head": plan["source_head"],
        "target_host": plan["target_host"],
        "prefix": str(prefix),
        "inventory": {
            "file_count": file_count,
            "symlink_count": symlink_count,
            "elf_count": elf_count,
            "total_file_bytes": total_bytes,
        },
        "sysconfigdata": sysconfigs,
        "key_artifacts": key_artifacts,
    }

    output = out / "replay-output-summary.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Result: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

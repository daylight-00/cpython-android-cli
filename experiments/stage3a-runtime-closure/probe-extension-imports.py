#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.machinery
import json
from pathlib import Path
import subprocess
import sys
import sysconfig


def module_name_from_filename(name: str, suffixes: list[str]) -> str | None:
    for suffix in sorted(suffixes, key=len, reverse=True):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return None


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-bin", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    python_bin = args.python_bin.resolve()
    output_dir = args.output_dir.resolve()

    if not python_bin.is_file():
        parser.error(f"runtime Python not found: {python_bin}")

    output_dir.mkdir(parents=True, exist_ok=True)

    destshared_raw = sysconfig.get_config_var("DESTSHARED")
    if not destshared_raw:
        raise SystemExit("DESTSHARED is empty")

    destshared = Path(destshared_raw)
    if not destshared.is_dir():
        raise SystemExit(f"DESTSHARED is not a directory: {destshared}")

    suffixes = list(importlib.machinery.EXTENSION_SUFFIXES)
    candidates: list[tuple[str, Path]] = []

    for path in sorted(destshared.iterdir(), key=lambda p: p.name):
        if not path.is_file():
            continue
        module_name = module_name_from_filename(path.name, suffixes)
        if module_name:
            candidates.append((module_name, path))

    probe_code = r'''
import importlib
import sys

name = sys.argv[1]
module = importlib.import_module(name)
print(name)
print(getattr(module, "__file__", "<built-in>"))
'''

    rows: list[list[str]] = []
    pass_count = 0
    fail_count = 0

    for module_name, path in candidates:
        proc = subprocess.run(
            [
                str(python_bin),
                "-I",
                "-S",
                "-c",
                probe_code,
                module_name,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        result = "PASS" if proc.returncode == 0 else "FAIL"
        if result == "PASS":
            pass_count += 1
        else:
            fail_count += 1

        rows.append(
            [
                module_name,
                str(path),
                result,
                str(proc.returncode),
                proc.stdout.strip().replace("\t", "\\t").replace("\n", "\\n"),
                proc.stderr.strip().replace("\t", "\\t").replace("\n", "\\n"),
            ]
        )

    write_tsv(
        output_dir / "extension-import-probe.tsv",
        [
            "module",
            "path",
            "result",
            "returncode",
            "stdout",
            "stderr",
        ],
        rows,
    )

    summary = {
        "destshared": str(destshared),
        "extension_candidate_count": len(candidates),
        "import_pass_count": pass_count,
        "import_fail_count": fail_count,
    }

    with (output_dir / "extension-import-probe-summary.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if fail_count == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())

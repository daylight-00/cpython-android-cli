#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess


def read_system_sonames(path: Path) -> list[str]:
    names: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["classification"] == "ANDROID_SYSTEM":
                names.add(row["needed"])
    return sorted(names)


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--classification-tsv", required=True, type=Path)
    parser.add_argument("--python-bin", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    classification_tsv = args.classification_tsv.resolve()
    python_bin = args.python_bin.resolve()
    output_dir = args.output_dir.resolve()

    if not classification_tsv.is_file():
        parser.error(f"missing classification TSV: {classification_tsv}")
    if not python_bin.is_file():
        parser.error(f"missing runtime Python: {python_bin}")

    output_dir.mkdir(parents=True, exist_ok=True)
    sonames = read_system_sonames(classification_tsv)

    probe_code = r'''
import ctypes
import os
import sys

name = sys.argv[1]
mode = getattr(os, "RTLD_NOW", 2) | getattr(os, "RTLD_LOCAL", 0)
ctypes.CDLL(name, mode=mode)
print("DLOPEN_OK", name)
'''

    rows: list[list[str]] = []
    pass_count = 0
    fail_count = 0

    for soname in sonames:
        proc = subprocess.run(
            [
                str(python_bin),
                "-I",
                "-B",
                "-S",
                "-c",
                probe_code,
                soname,
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
                soname,
                result,
                str(proc.returncode),
                proc.stdout.strip().replace("\t", "\\t").replace("\n", "\\n"),
                proc.stderr.strip().replace("\t", "\\t").replace("\n", "\\n"),
            ]
        )

    write_tsv(
        output_dir / "system-soname-probe.tsv",
        ["needed", "result", "returncode", "stdout", "stderr"],
        rows,
    )

    summary = {
        "unique_android_system_soname_count": len(sonames),
        "dlopen_pass_count": pass_count,
        "dlopen_fail_count": fail_count,
    }

    with (output_dir / "system-soname-probe-summary.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if fail_count == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())

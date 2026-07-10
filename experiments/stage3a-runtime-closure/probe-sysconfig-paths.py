#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import re
import sys
import sysconfig
from collections import Counter

# Absolute paths may appear as standalone tokens or inside common compiler/linker
# flag forms. The generic pattern deliberately refuses a slash preceded by '.'
# so relative paths such as ../Include are not misclassified as absolute paths.
GENERIC_ABS_PATH_RE = re.compile(
    r"(?:^|[\s=,:\"'\(\[])(/[A-Za-z0-9_@%+=./$~\-]+)"
)
FLAG_ABS_PATH_RE = re.compile(
    r"(?:-I|-L|-B|-isystem|--sysroot=)(/[A-Za-z0-9_@%+=:,./$~\-]+)"
)


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def normalize_candidate(raw: str) -> str:
    return raw.rstrip(".,;:)]}")


def classify_path(path: str, runtime_prefix: Path, termux_prefix: Path) -> str:
    try:
        p = Path(path)
        rp = Path(os.path.realpath(path)) if p.exists() else p
    except OSError:
        rp = Path(path)

    runtime_s = str(runtime_prefix)
    termux_s = str(termux_prefix)
    rp_s = str(rp)

    if rp_s == runtime_s or rp_s.startswith(runtime_s + "/"):
        return "RUNTIME_PREFIX"

    if rp_s == termux_s or rp_s.startswith(termux_s + "/"):
        return "TERMUX_PREFIX"

    if any(
        rp_s == root or rp_s.startswith(root + "/")
        for root in ["/system", "/apex", "/vendor", "/product", "/odm"]
    ):
        return "ANDROID_SYSTEM"

    if rp_s == "/usr/local" or rp_s.startswith("/usr/local/"):
        return "BUILD_PREFIX_RESIDUE"

    return "OTHER_ABSOLUTE"


def extract_paths(value: object) -> list[str]:
    if not isinstance(value, str):
        return []

    result: list[str] = []
    seen: set[str] = set()

    for pattern in (GENERIC_ABS_PATH_RE, FLAG_ABS_PATH_RE):
        for match in pattern.finditer(value):
            candidate = normalize_candidate(match.group(1))
            if candidate and candidate not in seen:
                seen.add(candidate)
                result.append(candidate)

    return result


def self_check_extractor() -> None:
    cases = [
        ("../..", []),
        ("../Include/internal", []),
        ("/usr/local/lib/python3.14", ["/usr/local/lib/python3.14"]),
        ("cc -I/abs/include -L/abs/lib", ["/abs/include", "/abs/lib"]),
        ("--sysroot=/ndk/sysroot", ["/ndk/sysroot"]),
        ("-Wl,-rpath,/runtime/lib", ["/runtime/lib"]),
    ]

    for raw, expected in cases:
        actual = extract_paths(raw)
        if actual != expected:
            raise RuntimeError(
                f"absolute-path extractor self-check failed: raw={raw!r} "
                f"expected={expected!r} actual={actual!r}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--termux-prefix", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    self_check_extractor()

    runtime_prefix = args.runtime_prefix.resolve()
    termux_prefix = args.termux_prefix.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[list[str]] = []
    counts: Counter[str] = Counter()

    config_vars = sysconfig.get_config_vars()
    for key in sorted(config_vars):
        raw_value = config_vars[key]
        for candidate in extract_paths(raw_value):
            classification = classify_path(candidate, runtime_prefix, termux_prefix)
            counts[classification] += 1
            rows.append(
                [
                    "config_var",
                    key,
                    str(raw_value),
                    candidate,
                    classification,
                    "yes" if Path(candidate).exists() else "no",
                ]
            )

    scheme_names = sorted(sysconfig.get_scheme_names())
    scheme_paths: dict[str, dict[str, str]] = {}

    for scheme in scheme_names:
        try:
            paths = sysconfig.get_paths(scheme=scheme)
        except Exception as exc:  # noqa: BLE001
            scheme_paths[scheme] = {"__error__": repr(exc)}
            continue

        scheme_paths[scheme] = dict(sorted(paths.items()))
        for key, value in sorted(paths.items()):
            for candidate in extract_paths(value):
                classification = classify_path(candidate, runtime_prefix, termux_prefix)
                counts[classification] += 1
                rows.append(
                    [
                        "scheme_path",
                        f"{scheme}:{key}",
                        value,
                        candidate,
                        classification,
                        "yes" if Path(candidate).exists() else "no",
                    ]
                )

    rows.sort(key=lambda row: (row[4], row[0], row[1], row[3]))

    write_tsv(
        output_dir / "sysconfig-absolute-paths.tsv",
        [
            "source_type",
            "key",
            "raw_value",
            "path_candidate",
            "classification",
            "exists",
        ],
        rows,
    )

    residue_rows = [row for row in rows if row[4] == "BUILD_PREFIX_RESIDUE"]
    write_tsv(
        output_dir / "sysconfig-build-prefix-residue.tsv",
        [
            "source_type",
            "key",
            "raw_value",
            "path_candidate",
            "classification",
            "exists",
        ],
        residue_rows,
    )

    current = {
        "sys_prefix": sys.prefix,
        "sys_base_prefix": sys.base_prefix,
        "sys_exec_prefix": sys.exec_prefix,
        "sys_base_exec_prefix": sys.base_exec_prefix,
        "sys_path": list(sys.path),
        "default_scheme": sysconfig.get_default_scheme(),
        "preferred_schemes": {
            name: sysconfig.get_preferred_scheme(name)
            for name in ("prefix", "home", "user")
        },
        "current_paths": sysconfig.get_paths(),
        "config_vars": {
            key: value
            for key, value in sorted(config_vars.items())
            if isinstance(value, (str, int, float, bool)) or value is None
        },
        "scheme_paths": scheme_paths,
    }

    with (output_dir / "sysconfig-current.json").open("w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, sort_keys=True)
        f.write("\n")

    summary = {
        "absolute_path_record_count": len(rows),
        "classification_counts": dict(sorted(counts.items())),
        "build_prefix_residue_record_count": len(residue_rows),
        "build_prefix_residue_unique_path_count": len({row[3] for row in residue_rows}),
        "default_scheme": sysconfig.get_default_scheme(),
        "runtime_prefix": str(runtime_prefix),
        "termux_prefix": str(termux_prefix),
        "extractor_version": 2,
        "extractor_self_check": "PASS",
    }

    with (output_dir / "sysconfig-path-summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
import tarfile
from collections import Counter
from pathlib import Path

PATHS = {
    "sysconfig_vars": (
        "lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json"
    ),
    "sysconfigdata": (
        "lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py"
    ),
    "build_details": "lib/python3.14/build-details.json",
    "makefile": (
        "lib/python3.14/config-3.14-aarch64-linux-android/Makefile"
    ),
    "config_c": (
        "lib/python3.14/config-3.14-aarch64-linux-android/config.c"
    ),
}


def read_package_files(package: Path) -> dict[str, str]:
    wanted = {f"prefix/{path}": name for name, path in PATHS.items()}
    result = {}
    with tarfile.open(package, "r:*") as archive:
        members = {
            member.name.lstrip("./").rstrip("/"): member
            for member in archive.getmembers()
        }
        for member_name, logical_name in wanted.items():
            member = members.get(member_name)
            if member is None or not member.isfile():
                raise ValueError(f"missing package metadata: {member_name}")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"cannot read package metadata: {member_name}")
            with stream:
                result[logical_name] = stream.read().decode(
                    "utf-8", "surrogateescape"
                )
    return result


def parse_sysconfigdata(text: str) -> dict:
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name)
            and target.id == "build_time_vars"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError("build_time_vars assignment not found")


def parse_makefile(text: str) -> dict[str, str]:
    logical = []
    buffer = ""
    for line in text.splitlines():
        if buffer:
            buffer += line
        else:
            buffer = line
        if buffer.endswith("\\"):
            buffer = buffer[:-1]
            continue
        logical.append(buffer)
        buffer = ""
    if buffer:
        logical.append(buffer)

    variables = {}
    pattern = re.compile(r"^([A-Za-z0-9_]+)\s*(?::=|\?=|\+=|=)\s*(.*)$")
    for line in logical:
        match = pattern.match(line)
        if match:
            variables[match.group(1)] = match.group(2)
    return variables


def flatten(value, prefix="") -> dict[str, object]:
    if isinstance(value, dict):
        result = {}
        for key in sorted(value):
            child = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten(value[key], child))
        return result
    if isinstance(value, list):
        result = {}
        for index, item in enumerate(value):
            child = f"{prefix}[{index}]"
            result.update(flatten(item, child))
        return result
    return {prefix: value}


def compare_mapping(old: dict, new: dict) -> dict:
    old_flat = flatten(old)
    new_flat = flatten(new)
    old_keys = set(old_flat)
    new_keys = set(new_flat)
    common = old_keys & new_keys
    differing = {
        key: {
            "historical": old_flat[key],
            "package": new_flat[key],
        }
        for key in sorted(common)
        if old_flat[key] != new_flat[key]
    }
    return {
        "historical_key_count": len(old_keys),
        "package_key_count": len(new_keys),
        "common_equal_key_count": sum(
            old_flat[key] == new_flat[key] for key in common
        ),
        "differing_key_count": len(differing),
        "only_historical_keys": sorted(old_keys - new_keys),
        "only_package_keys": sorted(new_keys - old_keys),
        "differing": differing,
    }


def token_summary(comparisons: dict) -> dict:
    tokens = Counter()
    patterns = {
        "historical_macos_workspace": r"/Users/runner/work/",
        "replay_linux_workspace": r"/home/[^\s'\"]+",
        "darwin_ndk_prebuilt": r"prebuilt/darwin-x86_64",
        "linux_ndk_prebuilt": r"prebuilt/linux-x86_64",
        "macos_host_identity": r"(?:apple-darwin|MACOS)",
        "linux_host_identity": r"(?:linux-gnu|LINUX)",
        "usr_local_prefix": r"/usr/local",
    }
    text = json.dumps(comparisons, sort_keys=True)
    for name, pattern in patterns.items():
        tokens[name] = len(re.findall(pattern, text))
    return dict(sorted(tokens.items()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-prefix", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    historical = {
        name: (args.historical_prefix / path).read_text(
            encoding="utf-8", errors="surrogateescape"
        )
        for name, path in PATHS.items()
    }
    package = read_package_files(args.package)

    comparisons = {
        "sysconfig_vars": compare_mapping(
            json.loads(historical["sysconfig_vars"]),
            json.loads(package["sysconfig_vars"]),
        ),
        "sysconfigdata": compare_mapping(
            parse_sysconfigdata(historical["sysconfigdata"]),
            parse_sysconfigdata(package["sysconfigdata"]),
        ),
        "build_details": compare_mapping(
            json.loads(historical["build_details"]),
            json.loads(package["build_details"]),
        ),
        "makefile": compare_mapping(
            parse_makefile(historical["makefile"]),
            parse_makefile(package["makefile"]),
        ),
    }

    config_diff = list(difflib.unified_diff(
        historical["config_c"].splitlines(),
        package["config_c"].splitlines(),
        fromfile="historical/config.c",
        tofile="package/config.c",
        lineterm="",
    ))
    comparisons["config_c"] = {
        "historical_line_count": len(historical["config_c"].splitlines()),
        "package_line_count": len(package["config_c"].splitlines()),
        "unified_diff_line_count": len(config_diff),
        "unified_diff": config_diff,
    }

    result = {
        "schema_version": 1,
        "files": PATHS,
        "comparisons": comparisons,
        "producer_token_counts": token_summary(comparisons),
        "all_five_files_parsed": len(comparisons) == 5,
        "pass": len(comparisons) == 5,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "non-elf-metadata-delta.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Result: {output}")
    print(
        "STAGE3B_METADATA_DELTA_CAPTURE="
        + ("PASS" if result["pass"] else "FAIL")
    )
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

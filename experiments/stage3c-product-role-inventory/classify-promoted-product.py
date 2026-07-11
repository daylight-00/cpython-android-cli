#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import stat
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

ROLES = (
    "RUNTIME",
    "DEVELOPMENT",
    "METADATA",
    "LICENSE",
    "DEBUG_OR_OPTIONAL",
    "UNKNOWN",
)
ROLE_PRECEDENCE = {role: index for index, role in enumerate(ROLES)}
ELF_MAGIC = b"\x7fELF"

RULES: tuple[dict[str, str], ...] = (
    {
        "rule_id": "legal-surface",
        "role": "LICENSE",
        "reason": "license, copying, copyright, or notice material",
    },
    {
        "rule_id": "debug-surface",
        "role": "DEBUG_OR_OPTIONAL",
        "reason": "known debug, symbol, or map surface",
    },
    {
        "rule_id": "elf-runtime",
        "role": "RUNTIME",
        "reason": "ELF object in the promoted target product",
    },
    {
        "rule_id": "bin-runtime",
        "role": "RUNTIME",
        "reason": "runtime entry point under bin/",
    },
    {
        "rule_id": "include-development",
        "role": "DEVELOPMENT",
        "reason": "header/development surface under include/",
    },
    {
        "rule_id": "static-development-library",
        "role": "DEVELOPMENT",
        "reason": "static or libtool development library",
    },
    {
        "rule_id": "pkgconfig-development",
        "role": "DEVELOPMENT",
        "reason": "pkg-config consumer metadata",
    },
    {
        "rule_id": "sysconfig-metadata",
        "role": "METADATA",
        "reason": "installed Python build/runtime metadata surface",
    },
    {
        "rule_id": "config-metadata",
        "role": "METADATA",
        "reason": "installed config/build metadata file",
    },
    {
        "rule_id": "config-development",
        "role": "DEVELOPMENT",
        "reason": "installed config development surface",
    },
    {
        "rule_id": "python-optional-surface",
        "role": "DEBUG_OR_OPTIONAL",
        "reason": "installed test, demo, GUI, or other optional stdlib surface",
    },
    {
        "rule_id": "python-tree-runtime",
        "role": "RUNTIME",
        "reason": "Python stdlib, extension, or required runtime data tree",
    },
    {
        "rule_id": "shared-library-runtime",
        "role": "RUNTIME",
        "reason": "runtime shared-library path",
    },
    {
        "rule_id": "share-metadata",
        "role": "METADATA",
        "reason": "descriptive shared metadata/documentation surface",
    },
    {
        "rule_id": "root-metadata",
        "role": "METADATA",
        "reason": "top-level descriptive metadata file",
    },
    {
        "rule_id": "symlink-target-role",
        "role": "dynamic",
        "reason": "role inherited from an in-tree symlink target",
    },
    {
        "rule_id": "directory-descendant-owner",
        "role": "dynamic",
        "reason": "minimum owner role selected from descendant roles",
    },
    {
        "rule_id": "unknown",
        "role": "UNKNOWN",
        "reason": "no selected rule matched",
    },
)

INVENTORY_FIELDS = (
    "path",
    "type",
    "mode",
    "size",
    "mtime_ns",
    "sha256",
    "symlink_target",
    "elf",
    "role",
    "rule_id",
    "reason",
    "descendant_roles",
    "mixed_directory",
)

LEGAL_NAMES = {
    "license",
    "license.txt",
    "license.md",
    "copying",
    "copying.txt",
    "copyright",
    "notice",
    "notice.txt",
    "third-party-notices",
    "third-party-notices.txt",
}
DEBUG_SUFFIXES = (
    ".debug",
    ".dbg",
    ".pdb",
    ".dwp",
    ".dwo",
    ".map",
    ".sym",
    ".symbols",
)
ROOT_METADATA_NAMES = {
    "readme",
    "readme.txt",
    "readme.md",
    "version",
    "version.txt",
    "build-details.json",
}
CONFIG_METADATA_NAMES = {
    "makefile",
    "config.c",
    "setup",
    "setup.local",
    "setup.bootstrap.in",
    "build-details.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_type(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "REGULAR"
    if stat.S_ISDIR(mode):
        return "DIRECTORY"
    if stat.S_ISLNK(mode):
        return "SYMLINK"
    if stat.S_ISCHR(mode):
        return "CHAR"
    if stat.S_ISBLK(mode):
        return "BLOCK"
    if stat.S_ISFIFO(mode):
        return "FIFO"
    if stat.S_ISSOCK(mode):
        return "SOCKET"
    return "OTHER"


def is_elf(path: Path) -> bool:
    try:
        with path.open("rb") as stream:
            return stream.read(4) == ELF_MAGIC
    except OSError:
        return False


def walk_entries(root: Path) -> list[Path]:
    entries: list[Path] = []
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        dirs.sort()
        files.sort()
        current_path = Path(current)
        entries.extend(current_path / name for name in dirs)
        entries.extend(current_path / name for name in files)
    return sorted(entries, key=lambda path: path.relative_to(root).as_posix())


def collect_entries(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in walk_entries(root):
        st = path.lstat()
        relative = path.relative_to(root).as_posix()
        kind = file_type(st.st_mode)
        digest = ""
        target = ""
        elf = False
        if kind == "REGULAR":
            digest = sha256_file(path)
            elf = is_elf(path)
        elif kind == "SYMLINK":
            target = os.readlink(path)
        result[relative] = {
            "path": relative,
            "type": kind,
            "mode": f"{stat.S_IMODE(st.st_mode):04o}",
            "size": st.st_size,
            "mtime_ns": st.st_mtime_ns,
            "sha256": digest,
            "symlink_target": target,
            "elf": elf,
            "role": "",
            "rule_id": "",
            "reason": "",
            "descendant_roles": "",
            "mixed_directory": False,
        }
    return result


def same_tree_fingerprint(entries: dict[str, dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    keys = (
        "path",
        "type",
        "mode",
        "size",
        "mtime_ns",
        "sha256",
        "symlink_target",
    )
    for path in sorted(entries):
        row = [str(entries[path][key]) for key in keys]
        digest.update("\t".join(row).encode("utf-8", "surrogateescape"))
        digest.update(b"\n")
    return digest.hexdigest()


def normalized_parts(path: str) -> tuple[str, ...]:
    return tuple(part.lower() for part in PurePosixPath(path).parts)


def is_legal_path(path: str) -> bool:
    parts = normalized_parts(path)
    name = parts[-1] if parts else ""
    return (
        name in LEGAL_NAMES
        or name.startswith("license.")
        or "licenses" in parts
        or "license" in parts
        or "legal" in parts
    )


def is_debug_path(path: str) -> bool:
    parts = normalized_parts(path)
    lower = path.lower()
    return (
        any(part in {"debug", "symbols", ".debug"} for part in parts)
        or lower.endswith(DEBUG_SUFFIXES)
        or ".dsym/" in lower
        or lower.endswith(".dsym")
    )


def is_python_tree(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return (
        len(parts) >= 2
        and parts[0] == "lib"
        and parts[1].startswith("python3.")
    )


def is_config_tree(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return (
        len(parts) >= 3
        and parts[0] == "lib"
        and parts[1].startswith("python3.")
        and parts[2].startswith("config-")
    )


def is_optional_python_surface(path: str) -> bool:
    parts = normalized_parts(path)
    if (
        len(parts) < 3
        or parts[0] != "lib"
        or not parts[1].startswith("python3.")
    ):
        return False
    optional_roots = {
        "test",
        "tests",
        "idlelib",
        "turtledemo",
        "tkinter",
        "__phello__",
    }
    return any(part in optional_roots for part in parts[2:])


def assign(
    entry: dict[str, Any],
    role: str,
    rule_id: str,
    reason: str,
) -> None:
    entry["role"] = role
    entry["rule_id"] = rule_id
    entry["reason"] = reason


def classify_non_directory(entry: dict[str, Any]) -> None:
    path = entry["path"]
    pure = PurePosixPath(path)
    parts = pure.parts
    lower_name = pure.name.lower()
    lower_path = path.lower()

    if entry["type"] not in {"REGULAR", "SYMLINK"}:
        assign(entry, "UNKNOWN", "unknown", "unsupported special-file type")
        return
    if is_legal_path(path):
        assign(entry, "LICENSE", "legal-surface", "license or legal-notice path")
        return
    if is_debug_path(path):
        assign(
            entry,
            "DEBUG_OR_OPTIONAL",
            "debug-surface",
            "debug/symbol path",
        )
        return
    if entry["elf"]:
        assign(
            entry,
            "RUNTIME",
            "elf-runtime",
            "ELF object in promoted target product",
        )
        return
    if parts and parts[0] == "bin":
        assign(entry, "RUNTIME", "bin-runtime", "runtime entry point under bin/")
        return
    if parts and parts[0] == "include":
        assign(
            entry,
            "DEVELOPMENT",
            "include-development",
            "header/development surface",
        )
        return
    if lower_name.endswith((".a", ".la")):
        assign(
            entry,
            "DEVELOPMENT",
            "static-development-library",
            "static/libtool library",
        )
        return
    if len(parts) >= 2 and parts[0] == "lib" and parts[1] == "pkgconfig":
        assign(
            entry,
            "DEVELOPMENT",
            "pkgconfig-development",
            "pkg-config metadata",
        )
        return
    if lower_name.startswith("_sysconfigdata_") or lower_name.startswith(
        "_sysconfig_vars_"
    ):
        assign(
            entry,
            "METADATA",
            "sysconfig-metadata",
            "installed sysconfig data",
        )
        return
    if lower_name == "build-details.json":
        assign(
            entry,
            "METADATA",
            "sysconfig-metadata",
            "installed build-details metadata",
        )
        return
    if is_config_tree(path):
        if lower_name in CONFIG_METADATA_NAMES or lower_name.endswith(
            (".json", ".py")
        ):
            assign(
                entry,
                "METADATA",
                "config-metadata",
                "installed config metadata",
            )
        else:
            assign(
                entry,
                "DEVELOPMENT",
                "config-development",
                "installed config development surface",
            )
        return
    if is_optional_python_surface(path):
        assign(
            entry,
            "DEBUG_OR_OPTIONAL",
            "python-optional-surface",
            "optional stdlib test/demo/GUI surface",
        )
        return
    if is_python_tree(path):
        assign(entry, "RUNTIME", "python-tree-runtime", "Python runtime tree")
        return
    if parts and parts[0] == "lib" and (
        ".so" in lower_name or lower_name.endswith(".dylib")
    ):
        assign(
            entry,
            "RUNTIME",
            "shared-library-runtime",
            "runtime shared-library path",
        )
        return
    if parts and parts[0] == "share":
        assign(
            entry,
            "METADATA",
            "share-metadata",
            "shared descriptive metadata",
        )
        return
    if len(parts) == 1 and lower_name in ROOT_METADATA_NAMES:
        assign(
            entry,
            "METADATA",
            "root-metadata",
            "top-level descriptive metadata",
        )
        return
    if entry["type"] == "SYMLINK":
        return
    assign(
        entry,
        "UNKNOWN",
        "unknown",
        f"no selected rule matched: {lower_path}",
    )


def resolve_symlink_target(
    path: str,
    target: str,
    entries: dict[str, dict[str, Any]],
) -> str | None:
    if not target:
        return None
    target_path = PurePosixPath(target)
    if target_path.is_absolute():
        return None
    combined = PurePosixPath(path).parent / target_path
    normalized: list[str] = []
    for part in combined.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not normalized:
                return None
            normalized.pop()
        else:
            normalized.append(part)
    relative = "/".join(normalized)
    return relative if relative in entries else None


def classify_symlink_fallbacks(
    entries: dict[str, dict[str, Any]],
) -> None:
    pending = {
        path
        for path, entry in entries.items()
        if entry["type"] == "SYMLINK" and not entry["role"]
    }
    for _ in range(len(pending) + 1):
        progress = False
        for path in sorted(tuple(pending)):
            entry = entries[path]
            target_path = resolve_symlink_target(
                path,
                entry["symlink_target"],
                entries,
            )
            if not target_path:
                continue
            target = entries[target_path]
            if target["role"]:
                assign(
                    entry,
                    target["role"],
                    "symlink-target-role",
                    f"inherits role from in-tree target {target_path}",
                )
                pending.remove(path)
                progress = True
        if not progress:
            break
    for path in sorted(pending):
        assign(
            entries[path],
            "UNKNOWN",
            "unknown",
            "unclassified symlink target",
        )


def direct_empty_directory_role(path: str) -> tuple[str, str, str]:
    pure = PurePosixPath(path)
    parts = pure.parts
    if is_legal_path(path):
        return "LICENSE", "legal-surface", "empty legal/license directory"
    if is_debug_path(path):
        return (
            "DEBUG_OR_OPTIONAL",
            "debug-surface",
            "empty debug/symbol directory",
        )
    if parts and parts[0] == "bin":
        return "RUNTIME", "bin-runtime", "empty runtime entry-point directory"
    if parts and parts[0] == "include":
        return (
            "DEVELOPMENT",
            "include-development",
            "empty development include directory",
        )
    if len(parts) >= 2 and parts[0] == "lib" and parts[1] == "pkgconfig":
        return (
            "DEVELOPMENT",
            "pkgconfig-development",
            "empty pkg-config directory",
        )
    if is_config_tree(path):
        return (
            "DEVELOPMENT",
            "config-development",
            "empty installed config directory",
        )
    if is_optional_python_surface(path):
        return (
            "DEBUG_OR_OPTIONAL",
            "python-optional-surface",
            "empty optional stdlib directory",
        )
    if is_python_tree(path):
        return "RUNTIME", "python-tree-runtime", "empty Python runtime directory"
    if parts and parts[0] == "share":
        return (
            "METADATA",
            "share-metadata",
            "empty shared metadata directory",
        )
    return "UNKNOWN", "unknown", "empty directory has no selected path rule"


def choose_directory_owner(roles: Iterable[str]) -> str:
    return min(set(roles), key=lambda role: ROLE_PRECEDENCE[role])


def classify_directories(entries: dict[str, dict[str, Any]]) -> None:
    children: dict[str, list[str]] = defaultdict(list)
    for path in entries:
        parent = PurePosixPath(path).parent.as_posix()
        if parent != ".":
            children[parent].append(path)

    descendant_roles: dict[str, set[str]] = {}
    directories = sorted(
        (
            path
            for path, entry in entries.items()
            if entry["type"] == "DIRECTORY"
        ),
        key=lambda path: (len(PurePosixPath(path).parts), path),
        reverse=True,
    )
    for path in directories:
        roles: set[str] = set()
        for child_path in children.get(path, []):
            child = entries[child_path]
            if child["type"] == "DIRECTORY":
                roles.update(descendant_roles.get(child_path, set()))
            elif child["role"]:
                roles.add(child["role"])
        if not roles:
            role, rule_id, reason = direct_empty_directory_role(path)
            roles = {role}
            assign(entries[path], role, rule_id, reason)
        else:
            owner = choose_directory_owner(roles)
            assign(
                entries[path],
                owner,
                "directory-descendant-owner",
                "minimum archive-owner role selected from descendant roles",
            )
        descendant_roles[path] = roles
        entries[path]["descendant_roles"] = ",".join(
            sorted(roles, key=lambda role: ROLE_PRECEDENCE[role])
        )
        entries[path]["mixed_directory"] = len(roles) > 1


def classify(entries: dict[str, dict[str, Any]]) -> None:
    for entry in entries.values():
        if entry["type"] != "DIRECTORY":
            classify_non_directory(entry)
    classify_symlink_fallbacks(entries)
    classify_directories(entries)


def normalized_manifest_hash(
    entries: dict[str, dict[str, Any]],
) -> str:
    digest = hashlib.sha256()
    for path in sorted(entries):
        row = entries[path]
        values = [
            str(row[field]).lower()
            if field in {"elf", "mixed_directory"}
            else str(row[field])
            for field in INVENTORY_FIELDS
        ]
        digest.update("\t".join(values).encode("utf-8", "surrogateescape"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_tsv(
    path: Path,
    fields: Iterable[str],
    rows: Iterable[dict[str, Any]],
) -> None:
    field_list = list(fields)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=field_list,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            output = dict(row)
            for key in ("elf", "mixed_directory"):
                if key in output:
                    output[key] = str(bool(output[key])).lower()
            writer.writerow(output)


def write_rules(path: Path) -> None:
    write_tsv(path, ("rule_id", "role", "reason"), RULES)


def summarize(
    entries: dict[str, dict[str, Any]],
    expected_count: int,
    before: str,
    after: str,
) -> dict[str, Any]:
    role_counts = Counter(entry["role"] for entry in entries.values())
    type_counts = Counter(entry["type"] for entry in entries.values())
    file_bytes_by_role: Counter[str] = Counter()
    for entry in entries.values():
        if entry["type"] == "REGULAR":
            file_bytes_by_role[entry["role"]] += int(entry["size"])

    unknown_paths = sorted(
        path
        for path, entry in entries.items()
        if entry["role"] == "UNKNOWN"
    )
    special_paths = sorted(
        path
        for path, entry in entries.items()
        if entry["type"] not in {"REGULAR", "DIRECTORY", "SYMLINK"}
    )
    pycache_paths = sorted(
        path
        for path in entries
        if path.endswith(".pyc")
        or "/__pycache__/" in f"/{path}/"
        or path.endswith("/__pycache__")
    )
    elf_role_counts = Counter(
        entry["role"] for entry in entries.values() if entry["elf"]
    )
    mixed_directories = sorted(
        path
        for path, entry in entries.items()
        if entry["mixed_directory"]
    )
    empty_directories = sorted(
        path
        for path, entry in entries.items()
        if entry["type"] == "DIRECTORY"
        and entry["reason"].startswith("empty ")
    )

    passed = (
        len(entries) == expected_count
        and not unknown_paths
        and not special_paths
        and not pycache_paths
        and set(elf_role_counts) <= {"RUNTIME"}
        and before == after
    )

    return {
        "schema_version": 1,
        "runtime_prefix": "",
        "expected_entry_count": expected_count,
        "entry_count": len(entries),
        "role_counts": dict(sorted(role_counts.items())),
        "type_counts": dict(sorted(type_counts.items())),
        "file_bytes_by_role": dict(sorted(file_bytes_by_role.items())),
        "unknown_count": len(unknown_paths),
        "unknown_paths": unknown_paths,
        "special_file_count": len(special_paths),
        "special_file_paths": special_paths,
        "pycache_path_count": len(pycache_paths),
        "pycache_paths": pycache_paths,
        "elf_count": sum(elf_role_counts.values()),
        "elf_role_counts": dict(sorted(elf_role_counts.items())),
        "mixed_directory_count": len(mixed_directories),
        "mixed_directories": mixed_directories,
        "empty_directory_count": len(empty_directories),
        "empty_directories": empty_directories,
        "manifest_sha256": normalized_manifest_hash(entries),
        "before_tree_sha256": before,
        "after_tree_sha256": after,
        "mutation_pass": before == after,
        "pass": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expected-entry-count", required=True, type=int)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    runtime_prefix = args.runtime_prefix.resolve()
    output_dir = args.output_dir.resolve()
    if not runtime_prefix.is_dir():
        parser.error(f"runtime prefix is not a directory: {runtime_prefix}")
    output_dir.mkdir(parents=True, exist_ok=True)

    before_entries = collect_entries(runtime_prefix)
    before_fingerprint = same_tree_fingerprint(before_entries)

    classify(before_entries)

    after_entries = collect_entries(runtime_prefix)
    after_fingerprint = same_tree_fingerprint(after_entries)

    summary = summarize(
        before_entries,
        args.expected_entry_count,
        before_fingerprint,
        after_fingerprint,
    )
    summary["runtime_prefix"] = str(runtime_prefix)

    rows = [before_entries[path] for path in sorted(before_entries)]
    unknown_rows = [row for row in rows if row["role"] == "UNKNOWN"]
    mixed_rows = [row for row in rows if row["mixed_directory"]]

    write_tsv(
        output_dir / "product-role-inventory.tsv",
        INVENTORY_FIELDS,
        rows,
    )
    write_tsv(output_dir / "unknown.tsv", INVENTORY_FIELDS, unknown_rows)
    write_tsv(
        output_dir / "mixed-directories.tsv",
        INVENTORY_FIELDS,
        mixed_rows,
    )
    write_rules(output_dir / "rules.tsv")

    with (output_dir / "role-summary.json").open(
        "w",
        encoding="utf-8",
    ) as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write("\n")

    with (output_dir / "mutation-check.txt").open(
        "w",
        encoding="utf-8",
    ) as stream:
        stream.write(f"runtime_prefix={runtime_prefix}\n")
        stream.write(f"before={before_fingerprint}\n")
        stream.write(f"after={after_fingerprint}\n")
        stream.write(
            f"pass={str(before_fingerprint == after_fingerprint).lower()}\n"
        )

    print(json.dumps(summary, indent=2, sort_keys=True))
    print()
    print(f"Inventory:         {output_dir / 'product-role-inventory.tsv'}")
    print(f"Unknown paths:     {output_dir / 'unknown.tsv'}")
    print(f"Mixed directories: {output_dir / 'mixed-directories.tsv'}")
    print(f"Rules:             {output_dir / 'rules.tsv'}")
    print(f"Summary:           {output_dir / 'role-summary.json'}")
    print(f"Mutation check:    {output_dir / 'mutation-check.txt'}")
    print()
    print(
        "STAGE3C_PRODUCT_ROLE_CLASSIFIER="
        + ("PASS" if summary["pass"] else "FAIL")
    )

    if args.require_pass and not summary["pass"]:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

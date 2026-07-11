#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tarfile
from pathlib import Path

CONTRACT_PATHS = [
    "include/python3.14/Python.h",
    "include/python3.14/pyconfig.h",
    "lib/libpython3.14.so",
]


def digest_stream(stream) -> tuple[str, bool]:
    digest = hashlib.sha256()
    first = True
    elf = False
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        if first:
            elf = chunk[:4] == b"\x7fELF"
            first = False
        digest.update(chunk)
    return digest.hexdigest(), elf


def metadata_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        filenames.sort()
        for name in [*dirnames, *filenames]:
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            stat = path.lstat()
            target = os.readlink(path) if path.is_symlink() else ""
            digest.update(
                (json.dumps(
                    (rel, stat.st_mode, stat.st_size, stat.st_mtime_ns, target)
                ) + "\n").encode()
            )
    return digest.hexdigest()


def filesystem_inventory(root: Path) -> dict[str, dict]:
    entries = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        filenames.sort()
        for name in [*dirnames, *filenames]:
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            stat = path.lstat()
            if path.is_symlink():
                entry = {
                    "kind": "symlink",
                    "size_bytes": stat.st_size,
                    "sha256": "",
                    "elf": False,
                    "target": os.readlink(path),
                }
            elif path.is_dir():
                entry = {
                    "kind": "directory",
                    "size_bytes": 0,
                    "sha256": "",
                    "elf": False,
                    "target": "",
                }
            elif path.is_file():
                with path.open("rb") as stream:
                    file_hash, elf = digest_stream(stream)
                entry = {
                    "kind": "file",
                    "size_bytes": stat.st_size,
                    "sha256": file_hash,
                    "elf": elf,
                    "target": "",
                }
            else:
                entry = {
                    "kind": "other",
                    "size_bytes": stat.st_size,
                    "sha256": "",
                    "elf": False,
                    "target": "",
                }
            entries[rel] = entry
    return entries


def package_prefix_inventory(package: Path) -> dict[str, dict]:
    entries = {}
    with tarfile.open(package, "r:*") as archive:
        for member in archive.getmembers():
            normalized = member.name.lstrip("./").rstrip("/")
            if normalized == "prefix":
                continue
            if not normalized.startswith("prefix/"):
                continue
            rel = normalized.removeprefix("prefix/")
            if not rel:
                continue
            if rel in entries:
                raise ValueError(f"duplicate package prefix member: {rel}")

            if member.isfile():
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f"cannot read package member: {member.name}")
                with stream:
                    file_hash, elf = digest_stream(stream)
                entry = {
                    "kind": "file",
                    "size_bytes": member.size,
                    "sha256": file_hash,
                    "elf": elf,
                    "target": "",
                }
            elif member.isdir():
                entry = {
                    "kind": "directory",
                    "size_bytes": 0,
                    "sha256": "",
                    "elf": False,
                    "target": "",
                }
            elif member.issym():
                entry = {
                    "kind": "symlink",
                    "size_bytes": member.size,
                    "sha256": "",
                    "elf": False,
                    "target": member.linkname,
                }
            elif member.islnk():
                entry = {
                    "kind": "hardlink",
                    "size_bytes": member.size,
                    "sha256": "",
                    "elf": False,
                    "target": member.linkname,
                }
            else:
                entry = {
                    "kind": "other",
                    "size_bytes": member.size,
                    "sha256": "",
                    "elf": False,
                    "target": member.linkname,
                }
            entries[rel] = entry
    return entries


def summarize(entries: dict[str, dict]) -> dict:
    kinds = {}
    file_bytes = 0
    elf_count = 0
    for entry in entries.values():
        kinds[entry["kind"]] = kinds.get(entry["kind"], 0) + 1
        if entry["kind"] == "file":
            file_bytes += entry["size_bytes"]
            elf_count += int(entry["elf"])
    return {
        "entry_count": len(entries),
        "kind_counts": dict(sorted(kinds.items())),
        "elf_count": elf_count,
        "total_file_bytes": file_bytes,
    }


def identity(entry: dict) -> tuple:
    if entry["kind"] == "file":
        return ("file", entry["sha256"])
    if entry["kind"] in {"symlink", "hardlink"}:
        return (entry["kind"], entry["target"])
    return (entry["kind"],)


def write_inventory(path: Path, entries: dict[str, dict]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(
            ["relative_path", "kind", "size_bytes", "sha256", "elf", "target"]
        )
        for rel, entry in sorted(entries.items()):
            writer.writerow([
                rel, entry["kind"], entry["size_bytes"], entry["sha256"],
                str(entry["elf"]).lower(), entry["target"],
            ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-prefix", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    historical = args.historical_prefix.resolve()
    package = args.package.resolve()
    if not historical.is_dir():
        raise SystemExit(f"missing historical prefix: {historical}")
    if not package.is_file():
        raise SystemExit(f"missing replay package: {package}")

    before = metadata_fingerprint(historical)
    historical_entries = filesystem_inventory(historical)
    package_entries = package_prefix_inventory(package)
    after = metadata_fingerprint(historical)

    counts = {
        "only_historical": 0,
        "only_package": 0,
        "common_exact": 0,
        "common_different": 0,
    }
    rows = []
    for rel in sorted(set(historical_entries) | set(package_entries)):
        old = historical_entries.get(rel)
        new = package_entries.get(rel)
        if old is None:
            status = "only_package"
        elif new is None:
            status = "only_historical"
        elif identity(old) == identity(new):
            status = "common_exact"
        else:
            status = "common_different"
        counts[status] += 1
        rows.append({
            "relative_path": rel,
            "status": status,
            "historical_kind": old["kind"] if old else "",
            "package_kind": new["kind"] if new else "",
            "historical_sha256": old["sha256"] if old else "",
            "package_sha256": new["sha256"] if new else "",
            "historical_target": old["target"] if old else "",
            "package_target": new["target"] if new else "",
        })

    contract = {}
    for rel in CONTRACT_PATHS:
        old = historical_entries.get(rel)
        new = package_entries.get(rel)
        contract[rel] = {
            "historical_present": old is not None,
            "package_present": new is not None,
            "historical_sha256": old["sha256"] if old else None,
            "package_sha256": new["sha256"] if new else None,
            "exact_identity_match": (
                old is not None
                and new is not None
                and identity(old) == identity(new)
            ),
        }

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    write_inventory(
        output / "historical-prefix-inventory.tsv", historical_entries
    )
    write_inventory(
        output / "replay-package-prefix-inventory.tsv", package_entries
    )
    with (output / "historical-package-prefix-diff.tsv").open(
        "w", newline=""
    ) as stream:
        fields = list(rows[0])
        writer = csv.DictWriter(
            stream, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "schema_version": 1,
        "inputs": {
            "historical_prefix": str(historical),
            "replay_package": str(package),
        },
        "historical_prefix": summarize(historical_entries),
        "replay_package_prefix": summarize(package_entries),
        "comparison": counts,
        "launcher_contract": contract,
        "mutation_check": before == after,
    }
    result["pass"] = (
        result["mutation_check"]
        and all(
            item["historical_present"] and item["package_present"]
            for item in contract.values()
        )
    )

    summary = output / "historical-package-prefix-summary.json"
    summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Result: {summary}")
    print(
        "STAGE3B_PACKAGE_PREFIX_COMPARISON="
        + ("PASS" if result["pass"] else "FAIL")
    )
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

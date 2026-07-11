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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
            row = (
                rel, stat.st_mode, stat.st_size, stat.st_mtime_ns, target
            )
            digest.update((json.dumps(row) + "\n").encode())
    return digest.hexdigest()


def inventory(root: Path) -> dict[str, dict]:
    result = {}
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
                    "target": os.readlink(path),
                    "sha256": "",
                    "elf": False,
                }
            elif path.is_dir():
                entry = {
                    "kind": "directory",
                    "size_bytes": 0,
                    "target": "",
                    "sha256": "",
                    "elf": False,
                }
            elif path.is_file():
                with path.open("rb") as stream:
                    elf = stream.read(4) == b"\x7fELF"
                entry = {
                    "kind": "file",
                    "size_bytes": stat.st_size,
                    "target": "",
                    "sha256": sha256(path),
                    "elf": elf,
                }
            else:
                entry = {
                    "kind": "other",
                    "size_bytes": stat.st_size,
                    "target": "",
                    "sha256": "",
                    "elf": False,
                }
            result[rel] = entry
    return result


def summarize(entries: dict[str, dict]) -> dict:
    kinds = {}
    total_file_bytes = 0
    elf_count = 0
    for entry in entries.values():
        kinds[entry["kind"]] = kinds.get(entry["kind"], 0) + 1
        if entry["kind"] == "file":
            total_file_bytes += entry["size_bytes"]
            elf_count += int(entry["elf"])
    return {
        "entry_count": len(entries),
        "kind_counts": dict(sorted(kinds.items())),
        "elf_count": elf_count,
        "total_file_bytes": total_file_bytes,
    }


def identity(entry: dict) -> tuple:
    if entry["kind"] == "file":
        return ("file", entry["sha256"])
    if entry["kind"] == "symlink":
        return ("symlink", entry["target"])
    return (entry["kind"],)


def write_inventory(path: Path, entries: dict[str, dict]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(
            ["relative_path", "kind", "size_bytes", "sha256", "elf", "target"]
        )
        for rel, entry in sorted(entries.items()):
            writer.writerow([
                rel,
                entry["kind"],
                entry["size_bytes"],
                entry["sha256"],
                str(entry["elf"]).lower(),
                entry["target"],
            ])


def package_inventory(path: Path) -> tuple[list[dict], dict]:
    rows = []
    with tarfile.open(path, "r:*") as archive:
        for member in archive.getmembers():
            if member.isfile():
                kind = "file"
            elif member.isdir():
                kind = "directory"
            elif member.issym():
                kind = "symlink"
            elif member.islnk():
                kind = "hardlink"
            else:
                kind = "other"
            rows.append({
                "path": member.name,
                "kind": kind,
                "size_bytes": member.size,
                "linkname": member.linkname,
            })

    kinds = {}
    total_file_bytes = 0
    top_level = set()
    normalized_paths = set()
    for row in rows:
        kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
        if row["kind"] == "file":
            total_file_bytes += row["size_bytes"]
        normalized = row["path"].lstrip("./")
        if normalized:
            normalized_paths.add(normalized.rstrip("/"))
            top_level.add(normalized.split("/", 1)[0])

    summary = {
        "member_count": len(rows),
        "kind_counts": dict(sorted(kinds.items())),
        "declared_file_bytes": total_file_bytes,
        "top_level_paths": sorted(top_level),
        "contract_members": {
            rel: f"aarch64-linux-android/{rel}" in normalized_paths
            for rel in CONTRACT_PATHS
        },
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--build-result", required=True, type=Path)
    parser.add_argument("--historical-dev-prefix", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text())
    build_result = json.loads(args.build_result.read_text())
    historical = args.historical_dev_prefix.resolve()
    replay = Path(plan["expected_prefix"]).resolve()
    package = Path(build_result["package_archive"]).resolve()

    for label, root in [
        ("historical development prefix", historical),
        ("replay development prefix", replay),
    ]:
        if not root.is_dir():
            raise SystemExit(f"missing {label}: {root}")
    if not package.is_file():
        raise SystemExit(f"missing replay package: {package}")

    before = {
        "historical": metadata_fingerprint(historical),
        "replay": metadata_fingerprint(replay),
    }
    historical_entries = inventory(historical)
    replay_entries = inventory(replay)
    after = {
        "historical": metadata_fingerprint(historical),
        "replay": metadata_fingerprint(replay),
    }

    all_paths = sorted(set(historical_entries) | set(replay_entries))
    diff_rows = []
    counts = {
        "only_historical": 0,
        "only_replay": 0,
        "common_exact": 0,
        "common_different": 0,
    }
    for rel in all_paths:
        left = historical_entries.get(rel)
        right = replay_entries.get(rel)
        if left is None:
            status = "only_replay"
        elif right is None:
            status = "only_historical"
        elif identity(left) == identity(right):
            status = "common_exact"
        else:
            status = "common_different"
        counts[status] += 1
        diff_rows.append({
            "relative_path": rel,
            "status": status,
            "historical_kind": left["kind"] if left else "",
            "replay_kind": right["kind"] if right else "",
            "historical_sha256": left["sha256"] if left else "",
            "replay_sha256": right["sha256"] if right else "",
            "historical_target": left["target"] if left else "",
            "replay_target": right["target"] if right else "",
        })

    contract = {}
    for rel in CONTRACT_PATHS:
        left = historical_entries.get(rel)
        right = replay_entries.get(rel)
        contract[rel] = {
            "historical_present": left is not None,
            "replay_present": right is not None,
            "historical_sha256": left["sha256"] if left else None,
            "replay_sha256": right["sha256"] if right else None,
            "exact_identity_match": (
                left is not None
                and right is not None
                and identity(left) == identity(right)
            ),
        }

    package_rows, package_summary = package_inventory(package)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    write_inventory(output / "historical-dev-inventory.tsv", historical_entries)
    write_inventory(output / "replay-dev-inventory.tsv", replay_entries)

    with (output / "development-prefix-diff.tsv").open(
        "w", newline=""
    ) as stream:
        fields = list(diff_rows[0])
        writer = csv.DictWriter(
            stream, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(diff_rows)

    with (output / "replay-package-members.tsv").open(
        "w", newline=""
    ) as stream:
        fields = ["path", "kind", "size_bytes", "linkname"]
        writer = csv.DictWriter(
            stream, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(package_rows)

    mutation_checks = {
        name: before[name] == after[name] for name in before
    }
    result = {
        "schema_version": 1,
        "inputs": {
            "source_head": plan["source_head"],
            "historical_dev_prefix": str(historical),
            "replay_dev_prefix": str(replay),
            "replay_package": str(package),
            "replay_package_sha256": build_result[
                "package_archive_sha256"
            ],
        },
        "development_prefixes": {
            "historical": summarize(historical_entries),
            "replay": summarize(replay_entries),
            "comparison": counts,
            "launcher_contract": contract,
        },
        "replay_package": package_summary,
        "mutation_checks": mutation_checks,
        "pass": (
            all(mutation_checks.values())
            and all(
                item["historical_present"] and item["replay_present"]
                for item in contract.values()
            )
            and all(package_summary["contract_members"].values())
        ),
    }
    summary = output / "product-boundary-summary.json"
    summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Result: {summary}")
    print(
        "STAGE3B_PRODUCT_BOUNDARY_ANALYSIS="
        + ("PASS" if result["pass"] else "FAIL")
    )
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

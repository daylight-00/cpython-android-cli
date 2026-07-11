#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

BASE_URL = (
    "https://github.com/beeware/cpython-android-source-deps/releases/download"
)
DEPENDENCIES = [
    ("bzip2", "1.0.8", "3"),
    ("libffi", "3.4.4", "3"),
    ("openssl", "3.5.7", "0"),
    ("sqlite", "3.50.4", "0"),
    ("xz", "5.4.6", "1"),
    ("zstd", "1.5.7", "2"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_archive(path: Path) -> dict:
    with tarfile.open(path, "r:*") as archive:
        members = archive.getmembers()

    top_level = sorted({
        member.name.lstrip("./").split("/", 1)[0]
        for member in members
        if member.name.lstrip("./")
    })
    return {
        "member_count": len(members),
        "regular_file_count": sum(member.isfile() for member in members),
        "directory_count": sum(member.isdir() for member in members),
        "symlink_count": sum(member.issym() for member in members),
        "hardlink_count": sum(member.islnk() for member in members),
        "declared_regular_file_bytes": sum(
            member.size for member in members if member.isfile()
        ),
        "top_level_paths": top_level,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text())
    cache_dir = Path(plan["cache_dir"]).resolve()
    target = plan["target_host"]

    products = []
    for name, version, revision in DEPENDENCIES:
        release_tag = f"{name}-{version}-{revision}"
        filename = f"{release_tag}-{target}.tar.gz"
        path = cache_dir / filename
        if not path.is_file():
            raise SystemExit(f"missing dependency archive: {path}")

        try:
            archive = inspect_archive(path)
        except (tarfile.TarError, OSError) as exc:
            raise SystemExit(f"invalid dependency archive {path}: {exc}") from exc

        products.append({
            "name": name,
            "version": version,
            "recipe_revision": revision,
            "release_tag": release_tag,
            "target_host": target,
            "filename": filename,
            "source_url": f"{BASE_URL}/{release_tag}/{filename}",
            "cache_path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "archive": archive,
        })

    result = {
        "schema_version": 1,
        "source_head": plan["source_head"],
        "target_host": target,
        "producer_files": plan["producer_files"],
        "cache_dir": str(cache_dir),
        "product_count": len(products),
        "all_expected_products_present": len(products) == len(DEPENDENCIES),
        "products": products,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "dependency-input-manifest.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Result: {output}")
    print("STAGE3B_DEPENDENCY_INPUT_CAPTURE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

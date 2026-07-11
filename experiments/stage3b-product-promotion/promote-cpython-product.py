#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--source-archive", required=True, type=Path)
    parser.add_argument("--canonical-archive-dir", required=True, type=Path)
    parser.add_argument("--derived-product-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    lock = json.loads(args.lock.read_text())
    expected = lock["archive"]
    source = args.source_archive.resolve()

    if not source.is_file():
        raise SystemExit(f"missing replay package: {source}")
    observed_size = source.stat().st_size
    observed_hash = sha256(source)
    if observed_size != expected["size_bytes"]:
        raise SystemExit(
            f"package size mismatch: {observed_size} != {expected['size_bytes']}"
        )
    if observed_hash != expected["sha256"]:
        raise SystemExit(
            f"package SHA-256 mismatch: {observed_hash} != {expected['sha256']}"
        )

    args.canonical_archive_dir.mkdir(parents=True, exist_ok=True)
    canonical_archive = (
        args.canonical_archive_dir / expected["filename"]
    )
    shutil.copy2(source, canonical_archive)
    if sha256(canonical_archive) != expected["sha256"]:
        raise SystemExit("canonical archive copy verification failed")
    checksum_file = args.canonical_archive_dir / "SHA256SUMS"
    checksum_file.write_text(
        f"{expected['sha256']}  {expected['filename']}\n"
    )

    product_root = args.derived_product_root.resolve()
    product_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="stage3b-product-", dir=product_root.parent
    ) as temp_name:
        temp_root = Path(temp_name)
        with tarfile.open(canonical_archive, "r:*") as archive:
            prefix = lock["package_prefix_root"].rstrip("/") + "/"
            members = [
                member for member in archive.getmembers()
                if member.name.lstrip("./").rstrip("/") == prefix.rstrip("/")
                or member.name.lstrip("./").startswith(prefix)
            ]
            archive.extractall(temp_root, members=members, filter="data")

        extracted = temp_root / lock["package_prefix_root"]
        if not extracted.is_dir():
            raise SystemExit(
                f"package prefix root was not extracted: {extracted}"
            )

        contract_results = {}
        for rel, contract in lock[
            "launcher_development_contract"
        ].items():
            path = extracted / rel
            if not path.is_file():
                raise SystemExit(f"missing launcher contract file: {rel}")
            actual = sha256(path)
            expected_hash = contract["sha256"]
            contract_results[rel] = {
                "sha256": actual,
                "match": actual == expected_hash,
            }
            if actual != expected_hash:
                raise SystemExit(
                    f"launcher contract hash mismatch for {rel}: "
                    f"{actual} != {expected_hash}"
                )

        if product_root.exists():
            shutil.rmtree(product_root)
        shutil.move(str(extracted), product_root)

    result = {
        "schema_version": 1,
        "product_kind": lock["product_kind"],
        "source_head": lock["source_head"],
        "target_host": lock["target_host"],
        "canonical_archive": str(canonical_archive.resolve()),
        "canonical_archive_size_bytes": canonical_archive.stat().st_size,
        "canonical_archive_sha256": sha256(canonical_archive),
        "checksum_file": str(checksum_file.resolve()),
        "derived_development_prefix": str(product_root),
        "launcher_development_contract": contract_results,
        "pass": True,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Manifest: {args.manifest}")
    print("STAGE3B_CPYTHON_PRODUCT_PROMOTION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

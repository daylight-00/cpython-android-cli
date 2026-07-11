#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

OWNED_FIELDS = (
    "artifact", "entry_class", "path", "type", "mode", "size", "mtime_ns",
    "sha256", "symlink_target", "elf", "role", "rule_id", "reason",
    "descendant_roles", "mixed_directory", "component", "policy_rule",
    "policy_reason",
)
STRUCTURAL_FIELDS = (
    "artifact", "path", "entry_class", "owner_artifact", "owner_component",
    "required_by_owned_descendant_count", "participant_artifacts", "participant_count",
)
SOURCE_FIELDS = OWNED_FIELDS[2:]
ARTIFACTS = ("runtime-base", "development-addon", "test-addon")
ARTIFACT_COMPONENTS = {
    "runtime-base": ["RUNTIME_BASE", "RUNTIME_METADATA", "LICENSE"],
    "development-addon": ["DEVELOPMENT", "DEVELOPMENT_METADATA"],
    "test-addon": ["OPTIONAL_TEST_SUITE", "OPTIONAL_TEST_DEMO"],
}
EXPECTED_COUNTS = {
    "runtime-base": {"owned": 714, "structural": 0, "total": 714},
    "development-addon": {"owned": 454, "structural": 2, "total": 456},
    "test-addon": {"owned": 1788, "structural": 2, "total": 1790},
}
LICENSE_PATH = "lib/python3.14/LICENSE.txt"
PRODUCT = {
    "product_kind": "upstream-cpython-android-package",
    "python_version": "3.14.6",
    "source_head": "c63aec69bd59c55314c06c23f4c22c03de76fe45",
    "target_host": "aarch64-linux-android",
    "android_api": 24,
    "ndk_version": "27.3.13750724",
    "architecture": "aarch64",
    "platform": "android",
    "multiarch": "aarch64-linux-android",
    "soabi": "cpython-314-aarch64-linux-android",
    "source_archive": {
        "filename": "python-3.14.6-aarch64-linux-android.tar.gz",
        "size_bytes": 22346066,
        "sha256": "a16e0433b6f7e69c4634b52ce582d4d387447fbcfed797425f669ac224631f4f",
    },
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def read_json_safe(path: Path, missing: list[str], errors: dict[str, str]) -> dict[str, Any]:
    if not path.is_file():
        missing.append(str(path))
        return {}
    try:
        return read_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors[str(path)] = repr(exc)
        return {}


def read_tsv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"TSV schema mismatch: {path}")
        return list(reader)


def read_tsv_safe(
    path: Path,
    fields: tuple[str, ...],
    missing: list[str],
    errors: dict[str, str],
) -> list[dict[str, str]]:
    if not path.is_file():
        missing.append(str(path))
        return []
    try:
        return read_tsv(path, fields)
    except (OSError, ValueError) as exc:
        errors[str(path)] = repr(exc)
        return []


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def artifact_id(name: str) -> str:
    return f"cpython-android-cli-3.14.6-android24-aarch64-{name}"


def safe_relative(path: object) -> bool:
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
        return False
    return all(part not in {"", ".", ".."} for part in PurePosixPath(path).parts)

#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

ARTIFACTS = ("runtime-base", "development-addon", "test-addon")
EXPECTED_MANIFEST_HASHES = {
    "runtime-base": "ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a",
    "development-addon": "9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a",
    "test-addon": "47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f",
}
EXPECTED_MANIFEST_INDEX = "540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1"
EXPECTED_PRODUCT_LOCK = "83f6b1fd3b610c22606f8dd4108a86cf2454e5997d0d0ada4124a209bfb091b7"
EXPECTED_CANONICAL_FINGERPRINT = "5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c"
EXPECTED_RUNTIME_FINGERPRINT = "9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796"
NORMALIZED_MTIME = 0
NORMALIZED_UID = 0
NORMALIZED_GID = 0
ENVELOPE_DIRECTORY_MODE = 0o755
METADATA_FILE_MODE = 0o644
GZIP_LEVEL = 9
LICENSE_PATH = "lib/python3.14/LICENSE.txt"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(path: object) -> bool:
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
        return False
    return all(part not in {"", ".", ".."} for part in PurePosixPath(path).parts)


def parse_mode(value: str) -> int:
    return int(value, 8)


def archive_filename(manifest: dict[str, Any]) -> str:
    return manifest["artifact"]["artifact_id"] + ".tar.gz"


def envelope_members(artifact_id: str) -> list[str]:
    root = artifact_id
    return [
        root,
        f"{root}/metadata",
        f"{root}/metadata/licenses",
        f"{root}/payload",
        f"{root}/metadata/manifest.json",
        f"{root}/metadata/manifest-index.json",
        f"{root}/metadata/product-lock.json",
        f"{root}/metadata/licenses/CPython-LICENSE.txt",
    ]


def payload_member_name(artifact_id: str, archive_path: str) -> str:
    return f"{artifact_id}/{archive_path}"

from __future__ import annotations

import csv
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
EXPECTED_ARCHIVES = {
    "runtime-base": {
        "sha256": "2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743",
        "size": 13684443,
        "members": 722,
    },
    "development-addon": {
        "sha256": "f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea",
        "size": 1037544,
        "members": 464,
    },
    "test-addon": {
        "sha256": "02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1",
        "size": 7135813,
        "members": 1798,
    },
}
EXPECTED_COUNTS = {
    "runtime-base": {"owned": 714, "structural": 0, "manifest": 714},
    "development-addon": {"owned": 454, "structural": 2, "manifest": 456},
    "test-addon": {"owned": 1788, "structural": 2, "manifest": 1790},
}
EXPECTED_MANIFEST_INDEX = "540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1"
EXPECTED_PRODUCT_LOCK = "83f6b1fd3b610c22606f8dd4108a86cf2454e5997d0d0ada4124a209bfb091b7"
EXPECTED_SHARED_NAMESPACE = ("lib", "lib/python3.14")

OWNED_FIELDS = (
    "path", "owner_artifact", "artifact_id", "component", "type", "mode",
    "size", "sha256", "symlink_target", "elf", "install_action",
    "uninstall_action",
)
STRUCTURAL_FIELDS = (
    "path", "consumer_artifact", "owner_artifact", "type", "mode",
    "install_action", "uninstall_action",
)
POLICY_FIELDS = (
    "operation", "path_class", "observed_state", "action", "allowed", "reason",
)
ORDER_FIELDS = ("operation", "sequence", "step", "mutation", "rollback_required")
SUMMARY_FIELDS = (
    "artifact", "owned_entry_count", "structural_parent_count",
    "regular_count", "directory_count", "symlink_count", "elf_count",
    "regular_bytes", "archive_size", "archive_sha256", "manifest_sha256",
)

COLLISION_POLICY = [
    ("fresh-install", "OWNED_PAYLOAD", "ABSENT", "CREATE_TYPE_APPROPRIATE", "true", "create exact regular file, symlink, or directory"),
    ("fresh-install", "OWNED_REGULAR_OR_SYMLINK", "EXISTING_UNOWNED", "CONFLICT", "false", "never adopt or overwrite unowned leaf content"),
    ("fresh-install", "OWNED_DIRECTORY", "EXISTING_DIRECTORY", "REUSE_AND_REGISTER_DIRECTORY", "true", "exact directory ownership preserves all descendant ownership boundaries"),
    ("fresh-install", "OWNED_OR_STRUCTURAL_DIRECTORY", "EXISTING_NON_DIRECTORY", "CONFLICT", "false", "directory namespace type mismatch"),
    ("fresh-install", "STRUCTURAL_PARENT", "ABSENT_OR_EXISTING_DIRECTORY", "CREATE_OR_REUSE_DIRECTORY", "true", "maintain a compatible non-owning namespace directory"),
    ("same-version-reinstall", "OWNED_PAYLOAD", "REGISTERED_SAME_ARTIFACT_MATCH", "NOOP", "true", "exact content and metadata already installed"),
    ("same-version-reinstall", "OWNED_PAYLOAD", "REGISTERED_SAME_ARTIFACT_MISMATCH", "REPLACE_WITH_BACKUP", "true", "repair only registered ownership with rollback backup"),
    ("same-version-reinstall", "OWNED_PAYLOAD", "REGISTERED_OTHER_ARTIFACT", "CONFLICT", "false", "cross-artifact ownership conflict"),
    ("same-version-reinstall", "OWNED_PAYLOAD", "UNREGISTERED_EXISTING", "CONFLICT", "false", "never adopt unregistered content"),
    ("uninstall", "OWNED_REGULAR_OR_SYMLINK", "REGISTERED_MATCH", "REMOVE_EXACT", "true", "remove exact registered leaf path"),
    ("uninstall", "OWNED_REGULAR_OR_SYMLINK", "REGISTERED_MISMATCH", "PRESERVE_AND_REPORT", "true", "do not delete locally modified content"),
    ("uninstall", "OWNED_DIRECTORY", "EMPTY_AFTER_CHILD_REMOVAL", "REMOVE_DIRECTORY", "true", "remove exact owned directory only when empty"),
    ("uninstall", "OWNED_DIRECTORY", "NONEMPTY", "PRESERVE_DIRECTORY", "true", "preserve unowned or other-artifact descendants"),
    ("uninstall", "STRUCTURAL_PARENT", "ANY", "PRESERVE_NAMESPACE", "true", "structural parent is non-owning"),
    ("uninstall", "UNOWNED_DESCENDANT", "ANY", "PRESERVE", "true", "never delete unowned sentinel content"),
    ("transaction", "ANY", "PREFLIGHT_FAILURE", "NO_MUTATION", "true", "fail before changing target or registry"),
    ("transaction", "ANY", "FAILURE_AFTER_MUTATION", "ROLLBACK", "true", "restore backups and prior registry"),
]

OPERATION_ORDER = [
    ("install", 1, "verify trusted archive and manifest identities", "false", "false"),
    ("install", 2, "acquire exclusive installation lock", "false", "false"),
    ("install", 3, "load and validate prior registry", "false", "false"),
    ("install", 4, "verify artifact prerequisites", "false", "false"),
    ("install", 5, "scan complete collision plan", "false", "false"),
    ("install", 6, "stage all replacement bytes and symlinks", "false", "false"),
    ("install", 7, "write PREPARED journal and backup plan", "true", "true"),
    ("install", 8, "create required directories shallow-to-deep", "true", "true"),
    ("install", 9, "replace exact regular and symlink paths", "true", "true"),
    ("install", 10, "write registry atomically", "true", "true"),
    ("install", 11, "mark transaction COMMITTED", "true", "true"),
    ("install", 12, "remove transaction backups and staging", "true", "false"),
    ("uninstall", 1, "verify registry and requested artifact identity", "false", "false"),
    ("uninstall", 2, "acquire exclusive installation lock", "false", "false"),
    ("uninstall", 3, "classify registered paths and local modifications", "false", "false"),
    ("uninstall", 4, "write PREPARED journal and backup plan", "true", "true"),
    ("uninstall", 5, "remove matching registered files and symlinks", "true", "true"),
    ("uninstall", 6, "remove owned directories deepest-first only when empty", "true", "true"),
    ("uninstall", 7, "preserve structural parents and unowned descendants", "false", "false"),
    ("uninstall", 8, "write registry atomically", "true", "true"),
    ("uninstall", 9, "mark transaction COMMITTED", "true", "true"),
    ("uninstall", 10, "remove transaction backups", "true", "false"),
]


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_relative(path: object) -> bool:
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
        return False
    return all(part not in {"", ".", ".."} for part in PurePosixPath(path).parts)


def write_tsv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_tsv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"TSV schema mismatch: {path}")
        return list(reader)

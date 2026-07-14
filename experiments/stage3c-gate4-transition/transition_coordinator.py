#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
FROZEN_ENGINE_DIR = SCRIPT_DIR.parent / "stage3c-installation-recovery"
sys.path.insert(0, str(FROZEN_ENGINE_DIR))

from recovery_common import (  # noqa: E402
    ARTIFACTS,
    REGISTRY_KIND,
    CrashController,
    actual_kind,
    add_intent,
    atomic_write,
    canonical_json_bytes,
    ensure_no_symlink_parent,
    installation_lock,
    load_registry,
    mark_applied,
    matches,
    persist_journal,
    record_from_entry,
    save_prior_registry,
)
from recovery_durability import (  # noqa: E402
    durable_cleanup_transaction,
    durable_ensure_directory,
    durable_mkdir,
    durable_move,
    durable_publish_regular,
    durable_publish_symlink,
)

DEFAULT_AUTHORITY_SPEC = SCRIPT_DIR / "gate4c-transition-authorities.json"
AUTHORITY_MAP_KIND = "stage3c-phase5-gate4-transition-authority-map"
SUPPORTED_TOPOLOGIES = {
    ("runtime-base",),
    ("runtime-base", "development-addon"),
    ("runtime-base", "test-addon"),
    ("runtime-base", "development-addon", "test-addon"),
}
RECORD_IDENTITY_FIELDS = ("type", "mode", "size", "sha256", "symlink_target")


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


def resolve_map_path(base: Path, text: str) -> Path:
    candidate = Path(text)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise RuntimeError(f"authority map path must be relative: {text}")
    resolved = (base / candidate).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as exc:
        raise RuntimeError(f"authority map path escapes root: {text}") from exc
    return resolved


def owned_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [entry for entry in manifest["entries"] if entry["entry_class"] == "OWNED_PAYLOAD"]


def structural_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [entry for entry in manifest["entries"] if entry["entry_class"] == "STRUCTURAL_PARENT"]


def record_identity(record: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(record.get(field) for field in RECORD_IDENTITY_FIELDS)


def artifact_metadata_from_expected(
    manifest: dict[str, Any], archive: Path, expected: dict[str, Any]
) -> dict[str, Any]:
    return {
        "artifact": manifest["artifact"]["name"],
        "artifact_id": manifest["artifact"]["artifact_id"],
        "archive_filename": archive.name,
        "archive_sha256": expected["archive_sha256"],
        "archive_size": expected["archive_size"],
        "manifest_sha256": expected["manifest_sha256"],
    }


@dataclass(frozen=True)
class ArtifactAuthority:
    name: str
    manifest_path: Path
    archive_path: Path
    manifest: dict[str, Any]
    expected: dict[str, Any]

    @property
    def metadata(self) -> dict[str, Any]:
        return artifact_metadata_from_expected(self.manifest, self.archive_path, self.expected)

    @property
    def records(self) -> dict[str, dict[str, Any]]:
        return {
            entry["payload_path"]: record_from_entry(entry, self.name)
            for entry in owned_entries(self.manifest)
        }

    @property
    def entries(self) -> dict[str, dict[str, Any]]:
        return {entry["payload_path"]: entry for entry in owned_entries(self.manifest)}


@dataclass(frozen=True)
class ProductAuthority:
    version: str
    product_lock_path: Path
    product_lock: dict[str, Any]
    expected: dict[str, Any]
    artifacts: dict[str, ArtifactAuthority]

    def expected_registry(self, topology: Sequence[str]) -> dict[str, Any]:
        selected = tuple(name for name in ARTIFACTS if name in topology)
        path_map: dict[str, dict[str, Any]] = {}
        for name in selected:
            for relative, record in self.artifacts[name].records.items():
                if relative in path_map:
                    raise RuntimeError(f"authority has duplicate owned path: {relative}")
                path_map[relative] = record
        return {
            "schema_version": 1,
            "registry_kind": REGISTRY_KIND,
            "artifacts": [self.artifacts[name].metadata for name in selected],
            "owned_paths": [path_map[path] for path in sorted(path_map)],
        }


def validate_product_files(
    version: str,
    product_map: dict[str, Any],
    expected: dict[str, Any],
    base: Path,
    *,
    role: str,
) -> ProductAuthority:
    product_lock_path = resolve_map_path(base, product_map["product_lock"])
    if not product_lock_path.is_file():
        raise RuntimeError(f"{role} product lock mismatch: missing file")
    if (
        sha256_file(product_lock_path) != expected["product_lock_sha256"]
        or product_lock_path.stat().st_size != expected["product_lock_size"]
    ):
        raise RuntimeError(f"{role} product lock mismatch")
    product_lock = read_json(product_lock_path)
    if (
        product_lock.get("python_version") != version
        or product_lock.get("source_head") != expected["source_head"]
    ):
        raise RuntimeError(f"{role} product lock mismatch")

    mapped_artifacts = product_map.get("artifacts")
    if not isinstance(mapped_artifacts, dict) or set(mapped_artifacts) != set(ARTIFACTS):
        raise RuntimeError(f"{role} authority artifact map mismatch")

    artifacts: dict[str, ArtifactAuthority] = {}
    for name in ARTIFACTS:
        row = mapped_artifacts[name]
        if not isinstance(row, dict):
            raise RuntimeError(f"{role} authority artifact map mismatch")
        manifest_path = resolve_map_path(base, row["manifest"])
        archive_path = resolve_map_path(base, row["archive"])
        artifact_expected = expected["artifacts"][name]
        if not manifest_path.is_file() or sha256_file(manifest_path) != artifact_expected["manifest_sha256"]:
            raise RuntimeError(f"{role} manifest mismatch: {name}")
        if (
            not archive_path.is_file()
            or archive_path.name != artifact_expected["archive_filename"]
            or archive_path.stat().st_size != artifact_expected["archive_size"]
            or sha256_file(archive_path) != artifact_expected["archive_sha256"]
        ):
            raise RuntimeError(f"{role} archive mismatch: {name}")
        manifest = read_json(manifest_path)
        entries = owned_entries(manifest)
        if (
            manifest.get("schema_version") != 1
            or manifest.get("artifact", {}).get("name") != name
            or manifest.get("artifact", {}).get("artifact_id") != artifact_expected["artifact_id"]
            or manifest.get("product", {}).get("python_version") != version
            or len(entries) != artifact_expected["owned_paths"]
        ):
            raise RuntimeError(f"{role} manifest mismatch: {name}")
        artifacts[name] = ArtifactAuthority(
            name=name,
            manifest_path=manifest_path,
            archive_path=archive_path,
            manifest=manifest,
            expected=artifact_expected,
        )
    return ProductAuthority(
        version=version,
        product_lock_path=product_lock_path,
        product_lock=product_lock,
        expected=expected,
        artifacts=artifacts,
    )


def load_authority_map(
    map_path: Path,
    spec_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    authority_map = read_json(map_path)
    spec = read_json(spec_path)
    if authority_map.get("schema_version") != 1 or authority_map.get("authority_map_kind") != AUTHORITY_MAP_KIND:
        raise RuntimeError("invalid transition authority map")
    spec_products = spec.get("products")
    if spec.get("schema_version") != 1 or not isinstance(spec_products, dict) or len(spec_products) != 2:
        raise RuntimeError("invalid transition authority specification")
    products = authority_map.get("products")
    if not isinstance(products, dict) or set(products) != set(spec["products"]):
        raise RuntimeError("transition authority map product set mismatch")
    return authority_map, spec, map_path.resolve().parent


def detect_source_product(
    registry: dict[str, Any],
    spec: dict[str, Any],
) -> tuple[str, tuple[str, ...]]:
    artifacts = registry.get("artifacts")
    owned = registry.get("owned_paths")
    if not isinstance(artifacts, list) or not isinstance(owned, list):
        raise RuntimeError("source artifact tuple is not a frozen authority")
    artifact_map = {row.get("artifact"): row for row in artifacts if isinstance(row, dict)}
    if not artifacts and not owned:
        raise RuntimeError("no exact runtime-base authority installed")
    if "runtime-base" not in artifact_map:
        raise RuntimeError("runtime-base is required")
    topology = tuple(name for name in ARTIFACTS if name in artifact_map)
    if topology not in SUPPORTED_TOPOLOGIES or len(artifact_map) != len(topology):
        raise RuntimeError("source artifact tuple is not a frozen authority")

    runtime_id = artifact_map["runtime-base"].get("artifact_id")
    source: str | None = None
    for version, product in spec["products"].items():
        if runtime_id == product["artifacts"]["runtime-base"]["artifact_id"]:
            source = version
            break
    if source is None:
        raise RuntimeError("source artifact tuple is not a frozen authority")

    for name in topology:
        observed_id = artifact_map[name].get("artifact_id")
        expected_id = spec["products"][source]["artifacts"][name]["artifact_id"]
        if observed_id == expected_id:
            continue
        other_ids = {
            product["artifacts"][name]["artifact_id"]
            for version, product in spec["products"].items()
            if version != source
        }
        if observed_id in other_ids:
            raise RuntimeError("registry combines artifact IDs from different products")
        raise RuntimeError("source artifact tuple is not a frozen authority")
    return source, topology


def compare_registry_exact(
    current: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    if current != expected:
        raise RuntimeError("source artifact tuple is not a frozen authority")


def verify_source_payload(prefix: Path, registry: dict[str, Any]) -> None:
    for row in registry["owned_paths"]:
        relative = row["path"]
        ensure_no_symlink_parent(prefix, relative)
        path = prefix / relative
        kind = actual_kind(path)
        expected_kind = row["type"]
        if kind == "absent":
            raise RuntimeError(f"source-owned path is absent: {relative}")
        if kind != expected_kind:
            raise RuntimeError(f"source-owned path type differs: {relative}")
        if matches(path, row):
            continue
        if expected_kind == "regular":
            raise RuntimeError(f"source-owned regular file differs: {relative}")
        if expected_kind == "symlink":
            raise RuntimeError(f"source-owned symlink differs: {relative}")
        raise RuntimeError(f"source-owned directory differs: {relative}")


def transaction_directories(state: Path) -> list[Path]:
    root = state / "transactions"
    if not root.is_dir():
        return []
    return sorted(path for path in root.iterdir() if path.is_dir())


def build_plan(
    prefix: Path,
    source_registry: dict[str, Any],
    target_registry: dict[str, Any],
) -> list[dict[str, Any]]:
    source = {row["path"]: row for row in source_registry["owned_paths"]}
    target = {row["path"]: row for row in target_registry["owned_paths"]}
    plan: list[dict[str, Any]] = []
    for relative in sorted(source.keys() | target.keys()):
        source_row = source.get(relative)
        target_row = target.get(relative)
        if source_row is not None and target_row is not None:
            if source_row["owner_artifact"] != target_row["owner_artifact"]:
                raise RuntimeError(f"cross-artifact owner transfer is unsupported: {relative}")
            action = "noop" if record_identity(source_row) == record_identity(target_row) else "replace"
        elif source_row is not None:
            action = "remove"
        else:
            assert target_row is not None
            ensure_no_symlink_parent(prefix, relative)
            if actual_kind(prefix / relative) != "absent":
                raise RuntimeError(f"unowned target-path collision: {relative}")
            action = "create"
        plan.append(
            {
                "action": action,
                "path": relative,
                "source": source_row,
                "target": target_row,
            }
        )
    return plan


@contextlib.contextmanager
def open_tar(archive: Path, temporary_root: Path) -> Iterator[tarfile.TarFile]:
    name = archive.name
    if name.endswith(".tar.gz"):
        with tarfile.open(archive, "r:gz") as container:
            yield container
        return
    if name.endswith(".tar.zst"):
        durable_ensure_directory(temporary_root, label="transition-zstd-temporary-root")
        temporary = temporary_root / f"{archive.stem}-{uuid.uuid4().hex}.tar"
        with temporary.open("wb") as output:
            completed = subprocess.run(
                ["zstd", "-q", "-d", "-c", str(archive)],
                stdout=output,
                stderr=subprocess.PIPE,
                check=False,
            )
        if completed.returncode != 0:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"zstd archive decode failed: {archive.name}")
        try:
            with tarfile.open(temporary, "r:") as container:
                yield container
        finally:
            temporary.unlink(missing_ok=True)
        return
    raise RuntimeError(f"unsupported artifact archive: {archive.name}")


def safe_member_name(name: str) -> bool:
    value = PurePosixPath(name)
    return bool(value.parts) and not value.is_absolute() and ".." not in value.parts


def stage_target_payload(
    transaction: Path,
    target: ProductAuthority,
    topology: Sequence[str],
    plan: Sequence[dict[str, Any]],
) -> Path:
    needed = {
        row["path"]
        for row in plan
        if row["action"] in {"replace", "create"}
    }
    staging = transaction / "staging/payload"
    durable_ensure_directory(staging, label="transition-staging-payload")
    temporary_root = transaction / "staging/tar"
    staged: set[str] = set()
    for artifact_name in topology:
        artifact = target.artifacts[artifact_name]
        selected = {
            relative: entry
            for relative, entry in artifact.entries.items()
            if relative in needed
        }
        if not selected:
            continue
        root = artifact.manifest["artifact"]["artifact_id"]
        expected_members = {
            f"{root}/{entry['archive_path']}": (relative, entry)
            for relative, entry in selected.items()
        }
        with open_tar(artifact.archive_path, temporary_root) as container:
            member_list = container.getmembers()
            member_names = [member.name for member in member_list]
            if len(member_names) != len(set(member_names)):
                raise RuntimeError(f"duplicate artifact member: {artifact.archive_path.name}")
            if any(not safe_member_name(name) for name in member_names):
                raise RuntimeError(f"unsafe artifact member: {artifact.archive_path.name}")
            if any(
                not (member.isfile() or member.isdir() or member.issym())
                for member in member_list
            ):
                raise RuntimeError(f"unsupported artifact member type: {artifact.archive_path.name}")
            members = {member.name: member for member in member_list}
            for member_name, (relative, entry) in expected_members.items():
                member = members.get(member_name)
                if member is None:
                    raise RuntimeError(f"target archive missing member: {relative}")
                destination = staging / relative
                durable_ensure_directory(destination.parent, label="transition-staging-parent")
                if entry["type"] == "regular":
                    if not member.isfile():
                        raise RuntimeError(f"target archive member type mismatch: {relative}")
                    stream = container.extractfile(member)
                    if stream is None:
                        raise RuntimeError(f"target archive member bytes missing: {relative}")
                    with destination.open("wb") as output:
                        shutil.copyfileobj(stream, output)
                    os.chmod(destination, int(entry["mode"], 8))
                elif entry["type"] == "symlink":
                    if not member.issym() or member.linkname != entry["symlink_target"]:
                        raise RuntimeError(f"target archive symlink mismatch: {relative}")
                    os.symlink(entry["symlink_target"], destination)
                else:
                    raise RuntimeError(f"transition leaf staging does not support {entry['type']}: {relative}")
                record = record_from_entry(entry, artifact_name)
                if not matches(destination, record):
                    raise RuntimeError(f"staged target payload mismatch: {relative}")
                staged.add(relative)
    if staged != needed:
        missing = sorted(needed - staged)
        raise RuntimeError(f"target staging incomplete: {missing[:3]}")
    return staging


def transition(
    authority_map_path: Path,
    authority_spec_path: Path,
    root: Path,
    target_product: str,
    requested_artifacts: Sequence[str] | None,
    *,
    nonblocking_lock: bool = False,
    crash_after_prepared: bool = False,
    crash_after_intents: int | None = None,
    crash_after_mutations: int | None = None,
    crash_after_commit: bool = False,
    fast_success: bool = False,
) -> dict[str, Any]:
    authority_map, spec, map_base = load_authority_map(authority_map_path, authority_spec_path)
    if target_product not in spec["products"]:
        raise RuntimeError("unknown target product")
    crash = CrashController(
        after_prepared=crash_after_prepared,
        after_intents=crash_after_intents,
        after_mutations=crash_after_mutations,
        after_commit=crash_after_commit,
        persist_each_checkpoint=not fast_success,
    )
    prefix = root / "prefix"
    with installation_lock(root, nonblocking=nonblocking_lock) as state:
        if transaction_directories(state):
            raise RuntimeError("recover existing transaction before transition")
        registry_path = state / "registry.json"
        current_registry = load_registry(registry_path)
        source_product, topology = detect_source_product(current_registry, spec)
        if source_product == target_product:
            raise RuntimeError("target product is already active")
        if requested_artifacts is not None:
            requested = tuple(name for name in ARTIFACTS if name in requested_artifacts)
            if requested != topology or len(set(requested_artifacts)) != len(requested_artifacts):
                raise RuntimeError("transition preserves the installed artifact set")

        source = validate_product_files(
            source_product,
            authority_map["products"][source_product],
            spec["products"][source_product],
            map_base,
            role="source",
        )
        target = validate_product_files(
            target_product,
            authority_map["products"][target_product],
            spec["products"][target_product],
            map_base,
            role="target",
        )
        expected_source_registry = source.expected_registry(topology)
        compare_registry_exact(current_registry, expected_source_registry)
        verify_source_payload(prefix, current_registry)
        target_registry = target.expected_registry(topology)
        plan = build_plan(prefix, current_registry, target_registry)
        counts = Counter(row["action"] for row in plan)

        transaction_id = f"transition-{source_product}-to-{target_product}-{uuid.uuid4().hex}"
        transaction = state / "transactions" / transaction_id
        durable_mkdir(transaction, parents=True, label="transition-transaction")
        try:
            staging = stage_target_payload(transaction, target, topology, plan)
            durable_mkdir(transaction / "backup", label="transition-backup")
            prior_registry_exists = save_prior_registry(transaction, registry_path)
        except Exception:
            durable_cleanup_transaction(transaction, label="transition-prepare-failure")
            raise

        journal: dict[str, Any] = {
            "schema_version": 2,
            "journal_kind": "cpython-android-cli-crash-recoverable-transaction",
            "id": transaction_id,
            "operation": "transition",
            "source_product": source_product,
            "target_product": target_product,
            "artifact_topology": list(topology),
            "state": "PREPARED",
            "prior_registry_exists": prior_registry_exists,
            "plan": [
                {"action": row["action"], "path": row["path"]}
                for row in plan
            ],
            "mutations": [],
        }
        persist_journal(transaction, journal)
        crash.crash_prepared()
        journal["state"] = "APPLYING"
        persist_journal(transaction, journal)

        for row in plan:
            action = row["action"]
            if action == "noop":
                continue
            relative = row["path"]
            path = prefix / relative
            if action in {"replace", "remove"}:
                backup_path = transaction / "backup" / relative
                durable_ensure_directory(backup_path.parent, label="transition-backup-parent")
                kind = "replaced" if action == "replace" else "removed"
                intent = {
                    "kind": kind,
                    "path": relative,
                    "backup": str(backup_path.relative_to(transaction)),
                }
                index = add_intent(transaction, journal, intent, crash)
                durable_move(path, backup_path, label=f"transition-{action}-backup")
                if action == "replace":
                    target_row = row["target"]
                    source_path = staging / relative
                    if target_row["type"] == "regular":
                        durable_publish_regular(
                            source_path,
                            path,
                            int(target_row["mode"], 8),
                            label="transition-regular-replace",
                        )
                    elif target_row["type"] == "symlink":
                        durable_publish_symlink(
                            os.readlink(source_path),
                            path,
                            label="transition-symlink-replace",
                        )
                    else:
                        raise RuntimeError(f"unsupported replacement type: {relative}")
                mark_applied(transaction, journal, index, crash)
            elif action == "create":
                target_row = row["target"]
                source_path = staging / relative
                durable_ensure_directory(path.parent, label="transition-create-parent")
                index = add_intent(
                    transaction,
                    journal,
                    {"kind": "created", "path": relative},
                    crash,
                )
                if target_row["type"] == "regular":
                    durable_publish_regular(
                        source_path,
                        path,
                        int(target_row["mode"], 8),
                        label="transition-regular-create",
                    )
                elif target_row["type"] == "symlink":
                    durable_publish_symlink(
                        os.readlink(source_path),
                        path,
                        label="transition-symlink-create",
                    )
                else:
                    raise RuntimeError(f"unsupported creation type: {relative}")
                mark_applied(transaction, journal, index, crash)
            else:
                raise RuntimeError(f"unknown transition plan action: {action}")

        index = add_intent(
            transaction,
            journal,
            {"kind": "registry", "prior_exists": prior_registry_exists},
            crash,
        )
        atomic_write(registry_path, canonical_json_bytes(target_registry))
        mark_applied(transaction, journal, index, crash)
        journal["state"] = "COMMITTED"
        persist_journal(transaction, journal)
        crash.crash_committed()
        durable_cleanup_transaction(transaction, label="transition-committed-cleanup")
        return {
            "operation": "transition",
            "pass": True,
            "source_product": source_product,
            "target_product": target_product,
            "artifact_topology": list(topology),
            "action_counts": dict(sorted(counts.items())),
            "mutation_count": crash.applied_mutations,
            "target_owned_paths": len(target_registry["owned_paths"]),
            "registry_schema": target_registry["schema_version"],
        }


def guard_install(
    authority_map_path: Path,
    authority_spec_path: Path,
    root: Path,
    requested_product: str,
    artifact: str,
    *,
    nonblocking_lock: bool = False,
) -> dict[str, Any]:
    del artifact
    authority_map, spec, map_base = load_authority_map(authority_map_path, authority_spec_path)
    with installation_lock(root, nonblocking=nonblocking_lock) as state:
        current_registry = load_registry(state / "registry.json")
        source_product, topology = detect_source_product(current_registry, spec)
        source = validate_product_files(
            source_product,
            authority_map["products"][source_product],
            spec["products"][source_product],
            map_base,
            role="source",
        )
        compare_registry_exact(current_registry, source.expected_registry(topology))
        if requested_product != source_product:
            raise RuntimeError("cross-product artifact install requires transition")
        return {
            "operation": "guard-install",
            "pass": True,
            "active_product": source_product,
            "artifact_topology": list(topology),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-map", required=True, type=Path)
    parser.add_argument("--authority-spec", default=DEFAULT_AUTHORITY_SPEC, type=Path)
    parser.add_argument("--installation-root", required=True, type=Path)
    parser.add_argument("--operation", required=True, choices=("transition", "guard-install"))
    parser.add_argument("--target-product")
    parser.add_argument("--requested-product")
    parser.add_argument("--artifact", action="append", choices=ARTIFACTS)
    parser.add_argument("--nonblocking-lock", action="store_true")
    parser.add_argument("--crash-after-prepared", action="store_true")
    parser.add_argument("--crash-after-intents", type=int)
    parser.add_argument("--crash-after-mutations", type=int)
    parser.add_argument("--crash-after-commit", action="store_true")
    parser.add_argument("--fast-success", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.fast_success and (
        args.crash_after_prepared
        or args.crash_after_intents is not None
        or args.crash_after_mutations is not None
        or args.crash_after_commit
    ):
        parser.error("--fast-success cannot be combined with crash injection")

    try:
        if args.operation == "transition":
            if args.target_product is None:
                raise RuntimeError("transition requires target product")
            result = transition(
                args.authority_map.resolve(),
                args.authority_spec.resolve(),
                args.installation_root.resolve(),
                args.target_product,
                args.artifact,
                nonblocking_lock=args.nonblocking_lock,
                crash_after_prepared=args.crash_after_prepared,
                crash_after_intents=args.crash_after_intents,
                crash_after_mutations=args.crash_after_mutations,
                crash_after_commit=args.crash_after_commit,
                fast_success=args.fast_success,
            )
        else:
            if args.requested_product is None or not args.artifact or len(args.artifact) != 1:
                raise RuntimeError("guard-install requires requested product and one artifact")
            result = guard_install(
                args.authority_map.resolve(),
                args.authority_spec.resolve(),
                args.installation_root.resolve(),
                args.requested_product,
                args.artifact[0],
                nonblocking_lock=args.nonblocking_lock,
            )
    except Exception as exc:
        result = {
            "operation": args.operation,
            "pass": False,
            "error": str(exc),
            "error_repr": repr(exc),
        }

    if args.output is not None:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") else 44


if __name__ == "__main__":
    raise SystemExit(main())

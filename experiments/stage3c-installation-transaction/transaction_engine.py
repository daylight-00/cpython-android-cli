#!/usr/bin/env python3
from __future__ import annotations
import argparse, contextlib, fcntl, hashlib, json, os, shutil, stat, tarfile, uuid
from pathlib import Path, PurePosixPath

ARTIFACTS = ("runtime-base", "development-addon", "test-addon")
REGISTRY_KIND = "cpython-android-cli-installed-ownership-registry"


def cbytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def readj(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rec_from_entry(entry, artifact):
    return {
        "path": entry["payload_path"],
        "owner_artifact": artifact,
        "type": entry["type"],
        "mode": entry["mode"],
        "size": entry.get("size"),
        "sha256": entry.get("sha256"),
        "symlink_target": entry.get("symlink_target"),
        "component": entry.get("component", ""),
        "elf": entry.get("elf") is True,
    }


def empty_registry():
    return {
        "schema_version": 1,
        "registry_kind": REGISTRY_KIND,
        "artifacts": [],
        "owned_paths": [],
    }


def load_registry(path):
    if not path.exists():
        return empty_registry()
    value = readj(path)
    if value.get("schema_version") != 1 or value.get("registry_kind") != REGISTRY_KIND:
        raise RuntimeError("invalid registry")
    return value


def actual_kind(path):
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return "absent"
    if stat.S_ISLNK(observed.st_mode):
        return "symlink"
    if stat.S_ISDIR(observed.st_mode):
        return "directory"
    if stat.S_ISREG(observed.st_mode):
        return "regular"
    return "special"


def matches(path, record):
    kind = actual_kind(path)
    if kind != record["type"]:
        return False
    if f"{stat.S_IMODE(path.lstat().st_mode):04o}" != record["mode"]:
        return False
    if kind == "regular":
        return path.stat().st_size == record["size"] and sha(path) == record["sha256"]
    if kind == "symlink":
        return os.readlink(path) == record["symlink_target"]
    return True


def ensure_no_symlink_parent(prefix: Path, relative: str):
    current = prefix
    for part in PurePosixPath(relative).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(f"symlink parent: {current}")
        if current.exists() and not current.is_dir():
            raise RuntimeError(f"non-directory parent: {current}")


def atomic_write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def load_inputs(contract_results: Path, artifact: str):
    phase3 = contract_results / "input/phase3"
    manifest_path = phase3 / "input/manifest-schema/manifests" / f"{artifact}.manifest.json"
    manifest = readj(manifest_path)
    archive_info = readj(contract_results / "installation-contract.json")["input"]["archives"][artifact]
    archive = next((phase3 / "archives").glob(f"*{artifact}.tar.gz"))
    if sha(archive) != archive_info["sha256"] or archive.stat().st_size != archive_info["size"]:
        raise RuntimeError("archive identity mismatch")
    with tarfile.open(archive, "r:gz") as container:
        root = manifest["artifact"]["artifact_id"]
        member = container.getmember(f"{root}/metadata/manifest.json")
        stream = container.extractfile(member)
        if stream is None or stream.read() != manifest_path.read_bytes():
            raise RuntimeError("embedded manifest mismatch")
    return phase3, manifest, archive, archive_info


def stage_archive(archive, manifest, staging: Path):
    root = manifest["artifact"]["artifact_id"]
    payload = staging / "payload"
    payload.mkdir(parents=True)
    expected = {
        f"{root}/{entry['archive_path']}": entry
        for entry in manifest["entries"]
        if entry["entry_class"] == "OWNED_PAYLOAD"
    }
    with tarfile.open(archive, "r:gz") as container:
        members = {member.name: member for member in container.getmembers()}
        for name, entry in expected.items():
            member = members.get(name)
            if member is None:
                raise RuntimeError("missing member " + name)
            destination = payload / entry["payload_path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            if entry["type"] == "directory":
                destination.mkdir(exist_ok=True)
                os.chmod(destination, int(entry["mode"], 8))
            elif entry["type"] == "regular":
                source = container.extractfile(member)
                if source is None:
                    raise RuntimeError("missing member bytes " + name)
                with destination.open("wb") as output:
                    shutil.copyfileobj(source, output)
                os.chmod(destination, int(entry["mode"], 8))
                if not matches(destination, rec_from_entry(entry, manifest["artifact"]["name"])):
                    raise RuntimeError("staged mismatch " + entry["payload_path"])
            elif entry["type"] == "symlink":
                if member.linkname != entry["symlink_target"]:
                    raise RuntimeError("staged symlink target mismatch " + entry["payload_path"])
                os.symlink(entry["symlink_target"], destination)
                if not matches(destination, rec_from_entry(entry, manifest["artifact"]["name"])):
                    raise RuntimeError("staged symlink mismatch " + entry["payload_path"])
            else:
                raise RuntimeError("unsupported entry type")
    return payload


@contextlib.contextmanager
def lock_state(root: Path):
    state = root / ".cpython-android-cli"
    state.mkdir(parents=True, exist_ok=True)
    lock_path = state / "lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield state
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def artifact_meta(manifest, archive, info):
    return {
        "artifact": manifest["artifact"]["name"],
        "artifact_id": manifest["artifact"]["artifact_id"],
        "archive_filename": archive.name,
        "archive_sha256": info["sha256"],
        "archive_size": info["size"],
        "manifest_sha256": hashlib.sha256(cbytes(manifest)).hexdigest(),
    }


def install(contract_results: Path, root: Path, artifact: str, fail_after: int | None):
    _, manifest, archive, info = load_inputs(contract_results, artifact)
    prefix = root / "prefix"
    prefix.mkdir(parents=True, exist_ok=True)
    with lock_state(root) as state:
        registry_path = state / "registry.json"
        prior_registry = registry_path.read_bytes() if registry_path.exists() else None
        current_registry = load_registry(registry_path)
        path_map = {item["path"]: item for item in current_registry["owned_paths"]}
        artifact_map = {item["artifact"]: item for item in current_registry["artifacts"]}
        prerequisite = manifest["compatibility"]["prerequisite"]
        if prerequisite and (
            prerequisite["artifact"] not in artifact_map
            or artifact_map[prerequisite["artifact"]]["artifact_id"] != prerequisite["artifact_id"]
        ):
            raise RuntimeError("prerequisite not installed")

        owned = [entry for entry in manifest["entries"] if entry["entry_class"] == "OWNED_PAYLOAD"]
        structural = [entry for entry in manifest["entries"] if entry["entry_class"] == "STRUCTURAL_PARENT"]
        plan = []
        for entry in structural:
            relative = entry["payload_path"]
            ensure_no_symlink_parent(prefix, relative)
            path = prefix / relative
            kind = actual_kind(path)
            if kind not in ("absent", "directory"):
                raise RuntimeError("structural collision " + relative)
            if kind == "directory" and f"{stat.S_IMODE(path.lstat().st_mode):04o}" != entry["mode"]:
                raise RuntimeError("structural mode mismatch " + relative)
            if kind == "absent":
                plan.append(("mkdir-structural", entry))

        for entry in owned:
            relative = entry["payload_path"]
            ensure_no_symlink_parent(prefix, relative)
            path = prefix / relative
            kind = actual_kind(path)
            old = path_map.get(relative)
            desired = rec_from_entry(entry, artifact)
            if old and old["owner_artifact"] != artifact:
                raise RuntimeError("other owner " + relative)
            if old:
                if matches(path, desired):
                    plan.append(("noop", entry))
                elif entry["type"] == "directory":
                    plan.append(("repair-dir", entry))
                else:
                    plan.append(("repair", entry))
            elif kind == "absent":
                plan.append(("create", entry))
            elif (
                entry["type"] == "directory"
                and kind == "directory"
                and f"{stat.S_IMODE(path.lstat().st_mode):04o}" == entry["mode"]
            ):
                plan.append(("reuse-dir", entry))
            else:
                raise RuntimeError("unowned collision " + relative)

        actionable = [item for item in plan if item[0] not in ("noop", "reuse-dir")]
        if not actionable and artifact in artifact_map:
            from collections import Counter

            return {
                "operation": "install",
                "artifact": artifact,
                "pass": True,
                "noop": True,
                "action_counts": dict(Counter(action for action, _ in plan)),
                "mutation_count": 0,
            }

        transaction_id = "install-" + artifact + "-" + uuid.uuid4().hex
        transaction = state / "transactions" / transaction_id
        transaction.mkdir(parents=True)
        staging = stage_archive(archive, manifest, transaction / "staging")
        backup = transaction / "backup"
        backup.mkdir()
        journal = {
            "schema_version": 1,
            "id": transaction_id,
            "operation": "install",
            "artifact": artifact,
            "state": "PREPARED",
            "plan": [{"action": action, "path": entry["payload_path"]} for action, entry in plan],
            "mutations": [],
        }
        atomic_write(transaction / "journal.json", cbytes(journal))
        mutations = []
        mutation_count = 0

        def tick():
            nonlocal mutation_count
            mutation_count += 1
            if fail_after is not None and mutation_count >= fail_after:
                raise RuntimeError(f"injected failure after {mutation_count}")

        try:
            journal["state"] = "APPLYING"
            atomic_write(transaction / "journal.json", cbytes(journal))
            directories = [
                (action, entry)
                for action, entry in plan
                if entry["type"] == "directory"
                and action in ("mkdir-structural", "create", "repair-dir")
            ]
            directories.sort(key=lambda item: len(PurePosixPath(item[1]["payload_path"]).parts))
            for action, entry in directories:
                relative = entry["payload_path"]
                path = prefix / relative
                if action in ("mkdir-structural", "create"):
                    path.mkdir(parents=True, exist_ok=False)
                    os.chmod(path, int(entry["mode"], 8))
                    mutations.append({"kind": "created", "path": relative})
                    tick()
                else:
                    kind = actual_kind(path)
                    if kind == "absent":
                        path.mkdir(parents=True, exist_ok=False)
                        os.chmod(path, int(entry["mode"], 8))
                        mutations.append({"kind": "created", "path": relative})
                        tick()
                    elif kind == "directory":
                        old_mode = f"{stat.S_IMODE(path.lstat().st_mode):04o}"
                        os.chmod(path, int(entry["mode"], 8))
                        mutations.append({"kind": "chmod", "path": relative, "old_mode": old_mode})
                        tick()
                    else:
                        backup_path = backup / relative
                        backup_path.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(path, backup_path)
                        path.mkdir(parents=True, exist_ok=False)
                        os.chmod(path, int(entry["mode"], 8))
                        mutations.append(
                            {
                                "kind": "replaced",
                                "path": relative,
                                "backup": str(backup_path.relative_to(transaction)),
                            }
                        )
                        tick()

            for action, entry in plan:
                if entry["type"] == "directory" or action in ("noop", "reuse-dir"):
                    continue
                relative = entry["payload_path"]
                path = prefix / relative
                source = staging / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if action == "repair":
                    backup_path = backup / relative
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(path, backup_path)
                    mutations.append(
                        {
                            "kind": "replaced",
                            "path": relative,
                            "backup": str(backup_path.relative_to(transaction)),
                        }
                    )
                else:
                    mutations.append({"kind": "created", "path": relative})
                temporary = path.with_name(path.name + ".new-" + uuid.uuid4().hex)
                if entry["type"] == "regular":
                    shutil.copyfile(source, temporary, follow_symlinks=False)
                    os.chmod(temporary, int(entry["mode"], 8))
                else:
                    os.symlink(os.readlink(source), temporary)
                os.replace(temporary, path)
                tick()

            new_paths = {key: value for key, value in path_map.items() if value["owner_artifact"] != artifact}
            for entry in owned:
                new_paths[entry["payload_path"]] = rec_from_entry(entry, artifact)
            new_artifacts = {key: value for key, value in artifact_map.items() if key != artifact}
            new_artifacts[artifact] = artifact_meta(manifest, archive, info)
            new_registry = {
                "schema_version": 1,
                "registry_kind": REGISTRY_KIND,
                "artifacts": [new_artifacts[name] for name in ARTIFACTS if name in new_artifacts],
                "owned_paths": [new_paths[name] for name in sorted(new_paths)],
            }
            atomic_write(registry_path, cbytes(new_registry))
            mutations.append({"kind": "registry", "prior_exists": prior_registry is not None})
            tick()
            journal["mutations"] = mutations
            journal["state"] = "COMMITTED"
            atomic_write(transaction / "journal.json", cbytes(journal))
            shutil.rmtree(transaction)
            from collections import Counter

            return {
                "operation": "install",
                "artifact": artifact,
                "pass": True,
                "noop": False,
                "action_counts": dict(Counter(action for action, _ in plan)),
                "mutation_count": mutation_count,
            }
        except Exception as exc:
            journal["state"] = "ROLLING_BACK"
            journal["error"] = repr(exc)
            journal["mutations"] = mutations
            atomic_write(transaction / "journal.json", cbytes(journal))
            for mutation in reversed(mutations):
                if mutation["kind"] == "registry":
                    if prior_registry is None:
                        registry_path.unlink(missing_ok=True)
                    else:
                        atomic_write(registry_path, prior_registry)
                elif mutation["kind"] == "created":
                    path = prefix / mutation["path"]
                    if path.is_symlink() or path.is_file():
                        path.unlink(missing_ok=True)
                    elif path.is_dir():
                        try:
                            path.rmdir()
                        except OSError:
                            pass
                elif mutation["kind"] == "replaced":
                    path = prefix / mutation["path"]
                    backup_path = transaction / mutation["backup"]
                    if path.is_symlink() or path.is_file():
                        path.unlink(missing_ok=True)
                    elif path.is_dir():
                        shutil.rmtree(path)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(backup_path, path)
                elif mutation["kind"] == "chmod":
                    path = prefix / mutation["path"]
                    if path.is_dir() and not path.is_symlink():
                        os.chmod(path, int(mutation["old_mode"], 8))
            journal["state"] = "ROLLED_BACK"
            atomic_write(transaction / "journal.json", cbytes(journal))
            return {
                "operation": "install",
                "artifact": artifact,
                "pass": False,
                "rolled_back": True,
                "error": repr(exc),
                "mutation_count": mutation_count,
                "transaction": str(transaction),
            }


def uninstall(contract_results: Path, root: Path, artifact: str, fail_after: int | None):
    prefix = root / "prefix"
    with lock_state(root) as state:
        registry_path = state / "registry.json"
        prior_registry = registry_path.read_bytes() if registry_path.exists() else None
        current_registry = load_registry(registry_path)
        artifact_map = {item["artifact"]: item for item in current_registry["artifacts"]}
        rows = [item for item in current_registry["owned_paths"] if item["owner_artifact"] == artifact]
        if artifact not in artifact_map:
            raise RuntimeError("artifact not installed")
        dependents = [item["artifact"] for item in current_registry["artifacts"] if item["artifact"] != artifact]
        if artifact == "runtime-base" and dependents:
            raise RuntimeError("dependent addons installed")

        transaction_id = "uninstall-" + artifact + "-" + uuid.uuid4().hex
        transaction = state / "transactions" / transaction_id
        transaction.mkdir(parents=True)
        backup = transaction / "backup"
        backup.mkdir()
        journal = {
            "schema_version": 1,
            "id": transaction_id,
            "operation": "uninstall",
            "artifact": artifact,
            "state": "PREPARED",
            "mutations": [],
        }
        atomic_write(transaction / "journal.json", cbytes(journal))
        mutations = []
        preserved = []
        mutation_count = 0

        def tick():
            nonlocal mutation_count
            mutation_count += 1
            if fail_after is not None and mutation_count >= fail_after:
                raise RuntimeError(f"injected failure after {mutation_count}")

        try:
            journal["state"] = "APPLYING"
            atomic_write(transaction / "journal.json", cbytes(journal))
            leaves = [row for row in rows if row["type"] != "directory"]
            leaves.sort(key=lambda row: row["path"], reverse=True)
            for row in leaves:
                path = prefix / row["path"]
                if matches(path, row):
                    backup_path = backup / row["path"]
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(path, backup_path)
                    mutations.append(
                        {
                            "kind": "removed",
                            "path": row["path"],
                            "backup": str(backup_path.relative_to(transaction)),
                        }
                    )
                    tick()
                else:
                    preserved.append(row["path"])

            directories = [row for row in rows if row["type"] == "directory"]
            directories.sort(
                key=lambda row: (len(PurePosixPath(row["path"]).parts), row["path"]),
                reverse=True,
            )
            for row in directories:
                path = prefix / row["path"]
                if path.is_dir() and not path.is_symlink():
                    try:
                        path.rmdir()
                        mutations.append({"kind": "removed-dir", "path": row["path"], "mode": row["mode"]})
                        tick()
                    except OSError:
                        preserved.append(row["path"])
                elif actual_kind(path) != "absent":
                    preserved.append(row["path"])

            new_paths = [row for row in current_registry["owned_paths"] if row["owner_artifact"] != artifact]
            new_artifacts = [item for item in current_registry["artifacts"] if item["artifact"] != artifact]
            new_registry = {
                "schema_version": 1,
                "registry_kind": REGISTRY_KIND,
                "artifacts": new_artifacts,
                "owned_paths": new_paths,
            }
            atomic_write(registry_path, cbytes(new_registry))
            mutations.append({"kind": "registry", "prior_exists": prior_registry is not None})
            tick()
            journal["mutations"] = mutations
            journal["preserved"] = preserved
            journal["state"] = "COMMITTED"
            atomic_write(transaction / "journal.json", cbytes(journal))
            shutil.rmtree(transaction)
            return {
                "operation": "uninstall",
                "artifact": artifact,
                "pass": True,
                "preserved": sorted(set(preserved)),
                "mutation_count": mutation_count,
            }
        except Exception as exc:
            journal["state"] = "ROLLING_BACK"
            journal["error"] = repr(exc)
            journal["mutations"] = mutations
            atomic_write(transaction / "journal.json", cbytes(journal))
            for mutation in reversed(mutations):
                if mutation["kind"] == "registry":
                    if prior_registry is None:
                        registry_path.unlink(missing_ok=True)
                    else:
                        atomic_write(registry_path, prior_registry)
                elif mutation["kind"] == "removed":
                    path = prefix / mutation["path"]
                    backup_path = transaction / mutation["backup"]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(backup_path, path)
                elif mutation["kind"] == "removed-dir":
                    path = prefix / mutation["path"]
                    path.mkdir(parents=True, exist_ok=True)
                    os.chmod(path, int(mutation["mode"], 8))
            journal["state"] = "ROLLED_BACK"
            atomic_write(transaction / "journal.json", cbytes(journal))
            return {
                "operation": "uninstall",
                "artifact": artifact,
                "pass": False,
                "rolled_back": True,
                "error": repr(exc),
                "mutation_count": mutation_count,
                "transaction": str(transaction),
            }


def verify(root: Path):
    registry_path = root / ".cpython-android-cli/registry.json"
    current_registry = load_registry(registry_path)
    prefix = root / "prefix"
    bad_paths = [
        row["path"]
        for row in current_registry["owned_paths"]
        if not matches(prefix / row["path"], row)
    ]
    return {
        "pass": not bad_paths,
        "artifact_count": len(current_registry["artifacts"]),
        "owned_path_count": len(current_registry["owned_paths"]),
        "bad_paths": bad_paths,
        "registry_sha256": sha(registry_path) if registry_path.exists() else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-results", required=True, type=Path)
    parser.add_argument("--installation-root", required=True, type=Path)
    parser.add_argument("--operation", required=True, choices=("install", "uninstall", "verify"))
    parser.add_argument("--artifact", choices=ARTIFACTS)
    parser.add_argument("--fail-after-mutations", type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "install":
            result = install(
                args.contract_results.resolve(),
                args.installation_root.resolve(),
                args.artifact,
                args.fail_after_mutations,
            )
        elif args.operation == "uninstall":
            result = uninstall(
                args.contract_results.resolve(),
                args.installation_root.resolve(),
                args.artifact,
                args.fail_after_mutations,
            )
        else:
            result = verify(args.installation_root.resolve())
    except Exception as exc:
        result = {
            "operation": args.operation,
            "artifact": args.artifact,
            "pass": False,
            "preflight_failure": True,
            "error": repr(exc),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(cbytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") else 40


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
COORDINATOR = SCRIPT_DIR / "transition_coordinator.py"
PRODUCTION_SPEC = SCRIPT_DIR / "gate4c-transition-authorities.json"
RECOVERY_ENGINE = REPO_ROOT / "experiments/stage3c-installation-recovery/recovery_engine.py"
FROZEN_ENGINE = REPO_ROOT / "experiments/stage3c-installation-recovery"
ARTIFACTS = ("runtime-base", "development-addon", "test-addon")
TOPOLOGIES = (
    ("runtime-base",),
    ("runtime-base", "development-addon"),
    ("runtime-base", "test-addon"),
    ("runtime-base", "development-addon", "test-addon"),
)
EXPECTED_ENGINE_BLOBS = {
    "recovery_common.py": "3183ba0861ef45e7a395201bec0085f3f69fb248",
    "recovery_durability.py": "61bfb859f73acccb0dfcce1d2a630bfd1ffc2d3f",
    "recovery_engine.py": "aebf5b9a33d163f7f8758f785ca621c94c0e478b",
    "recovery_operations.py": "8a307065e00fd7a7332541f4911c5478945374ee",
}


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(cjson(value))


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def entry_regular(path: str, data: bytes, component: str) -> dict[str, Any]:
    return {
        "archive_path": f"payload/{path}",
        "component": component,
        "elf": False,
        "entry_class": "OWNED_PAYLOAD",
        "mode": "0644",
        "payload_path": path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "type": "regular",
    }


def entry_directory(path: str, component: str) -> dict[str, Any]:
    return {
        "archive_path": f"payload/{path}",
        "component": component,
        "elf": False,
        "entry_class": "OWNED_PAYLOAD",
        "mode": "0755",
        "payload_path": path,
        "type": "directory",
    }


def entry_symlink(path: str, target: str, component: str) -> dict[str, Any]:
    return {
        "archive_path": f"payload/{path}",
        "component": component,
        "elf": False,
        "entry_class": "OWNED_PAYLOAD",
        "mode": "0777",
        "payload_path": path,
        "symlink_target": target,
        "type": "symlink",
    }


def fixture_artifact(version: str, artifact: str) -> tuple[dict[str, Any], dict[str, bytes | tuple[str, str]]]:
    suffix = version.replace(".", "-")
    component = artifact.upper().replace("-", "_")
    payload: dict[str, bytes | tuple[str, str]] = {}
    if artifact == "runtime-base":
        payload = {
            "bin/python": f"python-{version}\n".encode(),
            "lib/common.txt": b"common\n",
            "bin/python-link": ("symlink", "python"),
            f"lib/{'old' if version == '1.0.0' else 'new'}-only.txt": f"only-{version}\n".encode(),
        }
        entries = [entry_directory("bin", component), entry_directory("lib", component)]
        entries += [
            entry_regular("bin/python", payload["bin/python"], component),  # type: ignore[arg-type]
            entry_symlink("bin/python-link", "python", component),
            entry_regular("lib/common.txt", payload["lib/common.txt"], component),  # type: ignore[arg-type]
            entry_regular(
                f"lib/{'old' if version == '1.0.0' else 'new'}-only.txt",
                payload[f"lib/{'old' if version == '1.0.0' else 'new'}-only.txt"],  # type: ignore[arg-type]
                component,
            ),
        ]
    elif artifact == "development-addon":
        payload = {
            "include/header.h": f"header-{version}\n".encode(),
            f"include/{'old' if version == '1.0.0' else 'new'}-dev.h": f"dev-{version}\n".encode(),
        }
        entries = [entry_directory("include", component)]
        entries += [
            entry_regular("include/header.h", payload["include/header.h"], component),  # type: ignore[arg-type]
            entry_regular(
                f"include/{'old' if version == '1.0.0' else 'new'}-dev.h",
                payload[f"include/{'old' if version == '1.0.0' else 'new'}-dev.h"],  # type: ignore[arg-type]
                component,
            ),
        ]
    else:
        payload = {"tests/test_runtime.py": f"test-{version}\n".encode()}
        entries = [entry_directory("tests", component)]
        entries += [entry_regular("tests/test_runtime.py", payload["tests/test_runtime.py"], component)]  # type: ignore[arg-type]
    artifact_id = f"fixture-{suffix}-{artifact}"
    manifest = {
        "artifact": {"artifact_id": artifact_id, "name": artifact},
        "compatibility": {
            "prerequisite": None
            if artifact == "runtime-base"
            else {"artifact": "runtime-base", "artifact_id": f"fixture-{suffix}-runtime-base"}
        },
        "entries": entries,
        "manifest_kind": "fixture-transition-artifact-manifest",
        "product": {"python_version": version},
        "schema_version": 1,
    }
    return manifest, payload


def add_tar_member(container: tarfile.TarFile, name: str, entry: dict[str, Any], data: bytes | None) -> None:
    info = tarfile.TarInfo(name)
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mtime = 0
    info.mode = int(entry["mode"], 8)
    if entry["type"] == "directory":
        info.type = tarfile.DIRTYPE
        info.size = 0
        container.addfile(info)
    elif entry["type"] == "symlink":
        info.type = tarfile.SYMTYPE
        info.linkname = entry["symlink_target"]
        info.size = 0
        container.addfile(info)
    else:
        assert data is not None
        info.type = tarfile.REGTYPE
        info.size = len(data)
        container.addfile(info, io.BytesIO(data))


def build_archive(path: Path, manifest: dict[str, Any], payload: dict[str, bytes | tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    artifact_id = manifest["artifact"]["artifact_id"]
    raw_tar = path.with_suffix("") if path.name.endswith(".zst") else path
    if path.name.endswith(".tar.gz"):
        mode = "w:gz"
        destination = path
    else:
        mode = "w:"
        destination = path.with_name(path.name.removesuffix(".zst"))
    with tarfile.open(destination, mode) as container:
        metadata = tarfile.TarInfo(f"{artifact_id}/metadata/manifest.json")
        manifest_bytes = cjson(manifest)
        metadata.uid = metadata.gid = 0
        metadata.uname = metadata.gname = ""
        metadata.mtime = 0
        metadata.mode = 0o644
        metadata.size = len(manifest_bytes)
        container.addfile(metadata, io.BytesIO(manifest_bytes))
        for entry in manifest["entries"]:
            value = payload.get(entry["payload_path"])
            data = value if isinstance(value, bytes) else None
            add_tar_member(container, f"{artifact_id}/{entry['archive_path']}", entry, data)
    if path.name.endswith(".tar.zst"):
        completed = subprocess.run(
            ["zstd", "-q", "-f", "-19", str(destination), "-o", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        destination.unlink(missing_ok=True)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.decode(errors="replace"))


def build_fixture(root: Path) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    authority_root = root / "authority"
    spec: dict[str, Any] = {
        "authority_kind": "fixture-transition-authorities",
        "products": {},
        "schema_version": 1,
    }
    authority_map: dict[str, Any] = {
        "authority_map_kind": "stage3c-phase5-gate4-transition-authority-map",
        "products": {},
        "schema_version": 1,
    }
    payloads: dict[str, Any] = {}
    for version, role, extension in (("1.0.0", "first", ".tar.gz"), ("1.0.1", "second", ".tar.zst")):
        product_dir = authority_root / version
        product_lock = {
            "product_kind": "fixture-product",
            "python_version": version,
            "schema_version": 1,
            "source_head": hashlib.sha1(version.encode()).hexdigest(),
        }
        product_lock_path = product_dir / "product-lock.json"
        write_json(product_lock_path, product_lock)
        product_spec = {
            "artifacts": {},
            "product_lock_sha256": sha256_file(product_lock_path),
            "product_lock_size": product_lock_path.stat().st_size,
            "role": role,
            "source_head": product_lock["source_head"],
        }
        product_map: dict[str, Any] = {
            "artifacts": {},
            "product_lock": f"{version}/product-lock.json",
        }
        payloads[version] = {}
        for artifact in ARTIFACTS:
            manifest, payload = fixture_artifact(version, artifact)
            payloads[version][artifact] = payload
            manifest_path = product_dir / "manifests" / f"{artifact}.manifest.json"
            write_json(manifest_path, manifest)
            archive_name = f"{manifest['artifact']['artifact_id']}{extension}"
            archive_path = product_dir / "artifacts" / archive_name
            build_archive(archive_path, manifest, payload)
            product_spec["artifacts"][artifact] = {
                "archive_filename": archive_name,
                "archive_sha256": sha256_file(archive_path),
                "archive_size": archive_path.stat().st_size,
                "artifact_id": manifest["artifact"]["artifact_id"],
                "manifest_sha256": sha256_file(manifest_path),
                "owned_paths": len(manifest["entries"]),
            }
            product_map["artifacts"][artifact] = {
                "archive": f"{version}/artifacts/{archive_name}",
                "manifest": f"{version}/manifests/{artifact}.manifest.json",
            }
        spec["products"][version] = product_spec
        authority_map["products"][version] = product_map
    spec_path = authority_root / "spec.json"
    map_path = authority_root / "authority-map.json"
    write_json(spec_path, spec)
    write_json(map_path, authority_map)
    return map_path, spec_path, spec, payloads


def record_from_entry(entry: dict[str, Any], artifact: str) -> dict[str, Any]:
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


def expected_registry(authority_root: Path, version: str, topology: Iterable[str], spec: dict[str, Any]) -> dict[str, Any]:
    artifacts = []
    rows: dict[str, dict[str, Any]] = {}
    for artifact in ARTIFACTS:
        if artifact not in topology:
            continue
        manifest_path = authority_root / version / "manifests" / f"{artifact}.manifest.json"
        manifest = read_json(manifest_path)
        archive_expected = spec["products"][version]["artifacts"][artifact]
        artifacts.append(
            {
                "artifact": artifact,
                "artifact_id": archive_expected["artifact_id"],
                "archive_filename": archive_expected["archive_filename"],
                "archive_sha256": archive_expected["archive_sha256"],
                "archive_size": archive_expected["archive_size"],
                "manifest_sha256": archive_expected["manifest_sha256"],
            }
        )
        for entry in manifest["entries"]:
            rows[entry["payload_path"]] = record_from_entry(entry, artifact)
    return {
        "schema_version": 1,
        "registry_kind": "cpython-android-cli-installed-ownership-registry",
        "artifacts": artifacts,
        "owned_paths": [rows[path] for path in sorted(rows)],
    }


def seed_installation(
    root: Path,
    authority_root: Path,
    version: str,
    topology: tuple[str, ...],
    spec: dict[str, Any],
    payloads: dict[str, Any],
) -> None:
    if root.exists():
        shutil.rmtree(root)
    prefix = root / "prefix"
    prefix.mkdir(parents=True)
    registry = expected_registry(authority_root, version, topology, spec)
    for row in registry["owned_paths"]:
        path = prefix / row["path"]
        if row["type"] == "directory":
            path.mkdir(parents=True, exist_ok=True)
            os.chmod(path, int(row["mode"], 8))
        elif row["type"] == "symlink":
            path.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(row["symlink_target"], path)
        else:
            value = payloads[version][row["owner_artifact"]][row["path"]]
            assert isinstance(value, bytes)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
            os.chmod(path, int(row["mode"], 8))
    write_json(root / ".cpython-android-cli/registry.json", registry)


def file_matches(path: Path, row: dict[str, Any]) -> bool:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return False
    if row["type"] == "directory":
        return stat.S_ISDIR(mode) and not stat.S_ISLNK(mode) and f"{stat.S_IMODE(mode):04o}" == row["mode"]
    if row["type"] == "symlink":
        return stat.S_ISLNK(mode) and os.readlink(path) == row["symlink_target"]
    return (
        stat.S_ISREG(mode)
        and f"{stat.S_IMODE(mode):04o}" == row["mode"]
        and path.stat().st_size == row["size"]
        and sha256_file(path) == row["sha256"]
    )


def installation_exact(root: Path, expected: dict[str, Any]) -> bool:
    registry_path = root / ".cpython-android-cli/registry.json"
    if not registry_path.is_file() or read_json(registry_path) != expected:
        return False
    return all(file_matches(root / "prefix" / row["path"], row) for row in expected["owned_paths"])


def tx_inventory(root: Path) -> list[dict[str, Any]]:
    tx_root = root / ".cpython-android-cli/transactions"
    if not tx_root.is_dir():
        return []
    values = []
    for path in sorted(p for p in tx_root.iterdir() if p.is_dir()):
        journal = path / "journal.json"
        values.append(read_json(journal) if journal.is_file() else {"state": None})
    return values


def invoke(
    root: Path,
    map_path: Path,
    spec_path: Path,
    operation: str,
    *,
    target: str | None = None,
    requested: str | None = None,
    artifacts: Iterable[str] = (),
    extra: Iterable[str] = (),
) -> tuple[int, dict[str, Any], str, str]:
    output = root.parent / f"{root.name}-{operation}-{time.time_ns()}.json"
    command = [
        sys.executable,
        "-B",
        str(COORDINATOR),
        "--authority-map",
        str(map_path),
        "--authority-spec",
        str(spec_path),
        "--installation-root",
        str(root),
        "--operation",
        operation,
        "--output",
        str(output),
    ]
    if target is not None:
        command += ["--target-product", target]
    if requested is not None:
        command += ["--requested-product", requested]
    for artifact in artifacts:
        command += ["--artifact", artifact]
    command += list(extra)
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    value = read_json(output) if output.is_file() else {}
    return completed.returncode, value, completed.stdout, completed.stderr


def recover(root: Path) -> tuple[int, dict[str, Any]]:
    output = root.parent / f"{root.name}-recover-{time.time_ns()}.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(RECOVERY_ENGINE),
            "--installation-root",
            str(root),
            "--operation",
            "recover",
            "--output",
            str(output),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.returncode, read_json(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    checks: dict[str, bool] = {}

    def check(name: str, value: bool) -> None:
        checks[name] = bool(value)

    production = read_json(PRODUCTION_SPEC)
    check("production_spec_schema", production.get("schema_version") == 1)
    check("production_versions", set(production.get("products", {})) == {"3.14.5", "3.14.6"})
    check(
        "production_lock_hashes",
        production["products"]["3.14.5"]["product_lock_sha256"]
        == "e8c189d4a7386f1c522cc1479515b266fff60fdffedb3b7e842d9730ec21faeb"
        and production["products"]["3.14.6"]["product_lock_sha256"]
        == "83f6b1fd3b610c22606f8dd4108a86cf2454e5997d0d0ada4124a209bfb091b7",
    )
    for name, expected in EXPECTED_ENGINE_BLOBS.items():
        check(f"frozen_blob_{name}", git_blob_sha(FROZEN_ENGINE / name) == expected)
    source_text = COORDINATOR.read_text(encoding="utf-8")
    check("imports_frozen_common", "from recovery_common import" in source_text)
    check("imports_frozen_durability", "from recovery_durability import" in source_text)
    check("schema1_registry", '"schema_version": 1' in source_text and "REGISTRY_KIND" in source_text)
    check("schema2_journal", '"schema_version": 2' in source_text and '"operation": "transition"' in source_text)
    check("dedicated_operation", 'choices=("transition", "guard-install")' in source_text)
    check(
        "implementation_boundary_and_archive_safety",
        "recovery_operations.py" not in source_text
        and "recovery_engine.py" not in source_text
        and "duplicate artifact member" in source_text
        and "unsupported artifact member type" in source_text,
    )

    with tempfile.TemporaryDirectory(prefix="gate4c-implementation-") as temporary:
        work = Path(temporary)
        map_path, spec_path, spec, payloads = build_fixture(work)
        authority_root = map_path.parent

        happy_cases = (
            ("1.0.0", "1.0.1", TOPOLOGIES[-1], "upgrade_composed"),
            ("1.0.1", "1.0.0", TOPOLOGIES[0], "downgrade_runtime"),
        )
        for source, target, topology, label in happy_cases:
            root = work / f"happy-{label}"
            seed_installation(root, authority_root, source, topology, spec, payloads)
            sentinel = root / "prefix/user-data/sentinel.txt"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text("preserve\n", encoding="utf-8")
            rc, result, _, _ = invoke(
                root,
                map_path,
                spec_path,
                "transition",
                target=target,
                extra=("--fast-success",),
            )
            expected = expected_registry(authority_root, target, topology, spec)
            check(label + "_rc", rc == 0 and result.get("pass") is True)
            check(label + "_exact", installation_exact(root, expected))
            check(label + "_topology", result.get("artifact_topology") == list(topology))
            check(label + "_transactions", tx_inventory(root) == [])
            check(label + "_unowned", sentinel.read_text(encoding="utf-8") == "preserve\n")

        # Exact source preflight rejection classes.
        cases = (
            ("modified-regular", "bin/python", lambda p: p.write_text("modified\n"), "source-owned regular file differs"),
            ("modified-symlink", "bin/python-link", lambda p: (p.unlink(), os.symlink("wrong", p)), "source-owned symlink differs"),
            ("missing", "bin/python", lambda p: p.unlink(), "source-owned path is absent"),
            ("wrong-type", "bin/python", lambda p: (p.unlink(), p.mkdir()), "source-owned path type differs"),
        )
        for name, relative, mutation, error in cases:
            root = work / "preflight" / name
            seed_installation(root, authority_root, "1.0.0", TOPOLOGIES[-1], spec, payloads)
            before = (root / ".cpython-android-cli/registry.json").read_bytes()
            mutation(root / "prefix" / relative)
            rc, result, _, _ = invoke(root, map_path, spec_path, "transition", target="1.0.1")
            check(f"preflight_{name}_rc", rc == 44 and error in result.get("error", ""))
            check(f"preflight_{name}_registry", (root / ".cpython-android-cli/registry.json").read_bytes() == before)
            check(f"preflight_{name}_no_tx", tx_inventory(root) == [])

        root = work / "target-collision"
        seed_installation(root, authority_root, "1.0.0", TOPOLOGIES[-1], spec, payloads)
        collision = root / "prefix/lib/new-only.txt"
        collision.write_text("unowned\n", encoding="utf-8")
        rc, result, _, _ = invoke(root, map_path, spec_path, "transition", target="1.0.1")
        check("target_collision_rc", rc == 44 and "unowned target-path collision" in result.get("error", ""))
        check("target_collision_preserved", collision.read_text() == "unowned\n" and tx_inventory(root) == [])

        root = work / "topology-change"
        seed_installation(root, authority_root, "1.0.0", ("runtime-base",), spec, payloads)
        rc, result, _, _ = invoke(
            root,
            map_path,
            spec_path,
            "transition",
            target="1.0.1",
            artifacts=("runtime-base", "development-addon"),
        )
        check("topology_change_rc", rc == 44 and "transition preserves the installed artifact set" in result.get("error", ""))

        root = work / "transaction-residue"
        seed_installation(root, authority_root, "1.0.0", ("runtime-base",), spec, payloads)
        (root / ".cpython-android-cli/transactions/residue").mkdir(parents=True)
        rc, result, _, _ = invoke(root, map_path, spec_path, "transition", target="1.0.1")
        check("transaction_residue_rc", rc == 44 and "recover existing transaction" in result.get("error", ""))

        root = work / "empty"
        root.mkdir()
        rc, result, _, _ = invoke(root, map_path, spec_path, "transition", target="1.0.1")
        check("empty_reject", rc == 44 and "no exact runtime-base authority installed" in result.get("error", ""))

        root = work / "addon-no-runtime"
        seed_installation(root, authority_root, "1.0.0", ("runtime-base", "development-addon"), spec, payloads)
        registry = read_json(root / ".cpython-android-cli/registry.json")
        registry["artifacts"] = [x for x in registry["artifacts"] if x["artifact"] != "runtime-base"]
        registry["owned_paths"] = [x for x in registry["owned_paths"] if x["owner_artifact"] != "runtime-base"]
        write_json(root / ".cpython-android-cli/registry.json", registry)
        rc, result, _, _ = invoke(root, map_path, spec_path, "transition", target="1.0.1")
        check("addon_without_runtime", rc == 44 and "runtime-base is required" in result.get("error", ""))

        root = work / "unknown"
        seed_installation(root, authority_root, "1.0.0", ("runtime-base",), spec, payloads)
        registry = read_json(root / ".cpython-android-cli/registry.json")
        registry["artifacts"][0]["artifact_id"] = "unknown-runtime"
        write_json(root / ".cpython-android-cli/registry.json", registry)
        rc, result, _, _ = invoke(root, map_path, spec_path, "transition", target="1.0.1")
        check("unknown_product", rc == 44 and "source artifact tuple is not a frozen authority" in result.get("error", ""))

        root = work / "mixed"
        seed_installation(root, authority_root, "1.0.0", ("runtime-base", "development-addon"), spec, payloads)
        registry = read_json(root / ".cpython-android-cli/registry.json")
        for row in registry["artifacts"]:
            if row["artifact"] == "development-addon":
                row["artifact_id"] = spec["products"]["1.0.1"]["artifacts"]["development-addon"]["artifact_id"]
        write_json(root / ".cpython-android-cli/registry.json", registry)
        rc, result, _, _ = invoke(root, map_path, spec_path, "transition", target="1.0.1")
        check("mixed_product", rc == 44 and "registry combines artifact IDs" in result.get("error", ""))

        root = work / "guard"
        seed_installation(root, authority_root, "1.0.0", ("runtime-base",), spec, payloads)
        rc, result, _, _ = invoke(
            root,
            map_path,
            spec_path,
            "guard-install",
            requested="1.0.1",
            artifacts=("runtime-base",),
        )
        check("cross_product_install_guard", rc == 44 and "requires transition" in result.get("error", ""))
        rc, result, _, _ = invoke(
            root,
            map_path,
            spec_path,
            "guard-install",
            requested="1.0.0",
            artifacts=("runtime-base",),
        )
        check("same_product_install_guard", rc == 0 and result.get("active_product") == "1.0.0")

        # Target authority corruption classes use isolated copies of the authority root.
        for name, mutate, error in (
            ("lock", lambda p: (p / "1.0.1/product-lock.json").write_text("{}\n"), "target product lock mismatch"),
            ("manifest", lambda p: (p / "1.0.1/manifests/runtime-base.manifest.json").write_text("{}\n"), "target manifest mismatch"),
            ("archive", lambda p: (p / "1.0.1/artifacts/fixture-1-0-1-runtime-base.tar.zst").write_bytes(b"broken"), "target archive mismatch"),
        ):
            copied = work / f"corrupt-{name}"
            shutil.copytree(authority_root, copied)
            mutate(copied)
            root = work / f"corrupt-{name}-root"
            seed_installation(root, authority_root, "1.0.0", ("runtime-base",), spec, payloads)
            rc, result, _, _ = invoke(root, copied / "authority-map.json", copied / "spec.json", "transition", target="1.0.1")
            check(f"target_{name}_corrupt", rc == 44 and error in result.get("error", ""))
            check(f"target_{name}_no_tx", tx_inventory(root) == [])

        # Determine the fixture runtime mutation count from a successful plan.
        probe = work / "recovery-probe"
        seed_installation(probe, authority_root, "1.0.0", ("runtime-base",), spec, payloads)
        rc, probe_result, _, _ = invoke(
            probe,
            map_path,
            spec_path,
            "transition",
            target="1.0.1",
            extra=("--fast-success",),
        )
        mutation_count = int(probe_result.get("mutation_count", -1))
        check("fixture_mutation_count_positive", rc == 0 and mutation_count > 1)

        source_expected = expected_registry(authority_root, "1.0.0", ("runtime-base",), spec)
        target_expected = expected_registry(authority_root, "1.0.1", ("runtime-base",), spec)
        for boundary, extra, expected_rc in (
            ("prepared", ("--crash-after-prepared",), 90),
            ("applying", ("--crash-after-intents", str(mutation_count)), 93),
            ("committed", ("--crash-after-commit",), 92),
        ):
            root = work / f"recovery-{boundary}"
            seed_installation(root, authority_root, "1.0.0", ("runtime-base",), spec, payloads)
            rc, _, _, _ = invoke(root, map_path, spec_path, "transition", target="1.0.1", extra=extra)
            recover1_rc, recover1 = recover(root)
            recover2_rc, recover2 = recover(root)
            check(f"recovery_{boundary}_crash_rc", rc == expected_rc)
            check(f"recovery_{boundary}_recover_rc", recover1_rc == 0 and recover2_rc == 0)
            if boundary == "committed":
                check(f"recovery_{boundary}_target", installation_exact(root, target_expected))
                check(f"recovery_{boundary}_action", recover1["actions"][0]["action"] == "FINALIZED_COMMIT")
                check(f"recovery_{boundary}_second", recover2.get("transaction_count") == 0 and tx_inventory(root) == [])
            else:
                check(f"recovery_{boundary}_source", installation_exact(root, source_expected))
                check(f"recovery_{boundary}_action", recover1["actions"][0]["action"] == "ROLLED_BACK")
                check(
                    f"recovery_{boundary}_second",
                    recover2["actions"][0]["action"] == "NOOP_ROLLED_BACK"
                    and len(tx_inventory(root)) == 1
                    and tx_inventory(root)[0].get("state") == "ROLLED_BACK",
                )

        # Lock compatibility with the frozen engine.
        root = work / "locking"
        seed_installation(root, authority_root, "1.0.0", ("runtime-base",), spec, payloads)
        ready = work / "lock.ready"
        holder = subprocess.Popen(
            [
                sys.executable,
                "-B",
                str(RECOVERY_ENGINE),
                "--installation-root",
                str(root),
                "--operation",
                "hold-lock",
                "--hold-seconds",
                "10",
                "--ready-file",
                str(ready),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            for _ in range(100):
                if ready.is_file():
                    break
                time.sleep(0.02)
            rc, result, _, _ = invoke(
                root,
                map_path,
                spec_path,
                "transition",
                target="1.0.1",
                extra=("--nonblocking-lock",),
            )
            check("locking_ready", ready.is_file())
            check("locking_reject", rc == 44 and "installation lock busy" in result.get("error", ""))
        finally:
            holder.terminate()
            try:
                holder.wait(timeout=2)
            except subprocess.TimeoutExpired:
                holder.kill()
                holder.wait()

    failed = sorted(name for name, value in checks.items() if not value)
    result = {
        "schema_version": 1,
        "verification_kind": "stage3c-phase5-gate4c-transition-coordinator-implementation-verification",
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "pass_count": len(checks) - len(failed),
        "pass": not failed,
        "claim_boundary": "Repository implementation and synthetic transaction semantics only. No CPython 3.14.5/3.14.6 target transition, runtime behavior, or Gate 4D acceptance is proved.",
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_bytes(cjson(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Self-contained semantic and archive-safety regression tests for E2-P3 Gate 1."""
from __future__ import annotations

import copy
import importlib.util
import io
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT_PATH = ROOT / "components/standalone/contracts/qualification-v1.json"
QUALIFY_PATH = ROOT / "components/standalone/lib/qualify_archive.py"
VERIFY_PATH = ROOT / "components/standalone/lib/verify_qualification_result.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


QUALIFY = load("e2p3_qualify", QUALIFY_PATH)
VERIFY = load("e2p3_verify", VERIFY_PATH)
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(VERIFY.canonical_json_bytes(value))


def make_result(root: Path, profile: str = "static") -> Path:
    result_dir = root / profile
    evidence_dir = result_dir / "evidence"
    evidence_dir.mkdir(parents=True)
    evidence: dict[str, Any] = {}
    for name in CONTRACT["profile_evidence"][profile]:
        path = evidence_dir / name
        write_json(path, {"schema_version": 1, "name": name, "pass": True})
        evidence[name] = {"filename": name, "sha256": QUALIFY.sha256_file(path), "size": path.stat().st_size}
    checks = {name: True for name in sorted(CONTRACT["profile_checks"][profile])}
    profile_contract = CONTRACT["profiles"][profile]
    if profile == "static":
        host = {"host_role": "host-independent", "target_execution": False, "device_kind": "not-applicable"}
    else:
        host = {"host_role": "termux", "project_role": "termux", "target_execution": True, "device_kind": "real" if profile == "termux-real" else "emulator"}
    result = {
        "schema_version": 1,
        "qualification_kind": "hw-t-standalone-archive-qualification-result",
        "contract_version": 1,
        "profile": profile,
        "artifact_id": CONTRACT["artifact"]["artifact_id"],
        "input": {
            "archive_sha256": CONTRACT["artifact"]["archive_sha256"],
            "execution_authority": CONTRACT["input_authority"]["execution_authority"],
            "private_authority_index_sha256": CONTRACT["input_authority"]["private_authority_index_sha256"],
            "release_index_sha256": CONTRACT["artifact"]["release_index_sha256"],
        },
        "host": host,
        "checks": checks,
        "check_count": len(checks),
        "pass_count": len(checks),
        "failed_checks": [],
        "pass": True,
        "status": "passed-individual-profile",
        "selectable": False,
        "observations": {},
        "evidence": evidence,
        "claim_boundary": copy.deepcopy(VERIFY.CLAIM_BOUNDARY),
    }
    write_json(result_dir / VERIFY.RESULT_NAME, result)
    return result_dir


def mutate_result(result_dir: Path, fn: Callable[[dict[str, Any]], None], canonical: bool = True) -> None:
    path = result_dir / VERIFY.RESULT_NAME
    value = json.loads(path.read_text(encoding="utf-8"))
    fn(value)
    if canonical:
        write_json(path, value)
    else:
        path.write_text(json.dumps(value), encoding="utf-8")


def verify(result_dir: Path) -> dict[str, Any]:
    return VERIFY.verify_result(ROOT, CONTRACT_PATH, result_dir)


def archive_fixture(root: Path, members: list[tuple[str, str, bytes | str | None]], manifest_order: list[str] | None = None) -> tuple[Path, list[dict[str, Any]]]:
    tar_path = root / "fixture.tar"
    zst_path = root / "fixture.tar.zst"
    rows: list[dict[str, Any]] = []
    with tarfile.open(tar_path, "w", format=tarfile.PAX_FORMAT) as archive:
        for name, kind, payload in members:
            info = tarfile.TarInfo(name)
            info.mode = 0o755 if name.endswith("python3.14") else 0o644
            if kind == "directory":
                info.type = tarfile.DIRTYPE
                archive.addfile(info)
                rows.append({"path": name, "type": "directory", "mode": f"{info.mode:04o}"})
            elif kind == "regular":
                data = bytes(payload or b"")
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
                rows.append({"path": name, "type": "regular", "mode": f"{info.mode:04o}", "size": len(data), "sha256": QUALIFY.hashlib.sha256(data).hexdigest()})
            elif kind == "symlink":
                info.type = tarfile.SYMTYPE
                info.linkname = str(payload)
                archive.addfile(info)
                rows.append({"path": name, "type": "symlink", "mode": f"{info.mode:04o}", "symlink_target": str(payload)})
            elif kind == "hardlink":
                info.type = tarfile.LNKTYPE
                info.linkname = str(payload)
                archive.addfile(info)
            else:
                raise ValueError(kind)
    subprocess.run(["zstd", "-q", "-f", "-T1", "--check", "-o", str(zst_path), str(tar_path)], check=True)
    tar_path.unlink()
    if manifest_order:
        by_name = {row["path"]: row for row in rows}
        rows = [by_name[name] for name in manifest_order]
    return zst_path, rows


def rejected(fn: Callable[[], Any]) -> bool:
    try:
        fn()
    except (ValueError, RuntimeError):
        return True
    return False


def main() -> int:
    outcomes: list[dict[str, Any]] = []
    def record(name: str, passed: bool, detail: Any = None) -> None:
        outcomes.append({"name": name, "pass": bool(passed), "detail": detail})

    with tempfile.TemporaryDirectory(prefix="e2p3-contract-tests-") as td:
        temp = Path(td)
        baseline = make_result(temp / "baseline")
        base_verify = verify(baseline)
        record("baseline-static-result", base_verify["pass"], base_verify.get("failed_checks"))

        mutations: list[tuple[str, str, Callable[[dict[str, Any]], None], bool]] = [
            ("archive-sha", "input_identity", lambda v: v["input"].__setitem__("archive_sha256", "0" * 64), True),
            ("private-index", "input_identity", lambda v: v["input"].__setitem__("private_authority_index_sha256", "1" * 64), True),
            ("missing-check", "check_names_exact", lambda v: v["checks"].pop(next(iter(v["checks"]))), True),
            ("pass-accounting", "pass_semantics", lambda v: v["checks"].__setitem__(next(iter(v["checks"])), False), True),
            ("selectable", "never_selectable", lambda v: v.__setitem__("selectable", True), True),
            ("profile", "profile_known", lambda v: v.__setitem__("profile", "unknown"), True),
            ("artifact", "artifact_identity", lambda v: v.__setitem__("artifact_id", "wrong"), True),
            ("evidence-hash", "evidence_refs", lambda v: v["evidence"][next(iter(v["evidence"]))].__setitem__("sha256", "f" * 64), True),
            ("evidence-missing", "evidence_names_exact", lambda v: v["evidence"].pop(next(iter(v["evidence"]))), True),
            ("claim-boundary", "claim_boundary", lambda v: v["claim_boundary"].__setitem__("combined_target_qualification", True), True),
            ("host-role", "host_object", lambda v: v["host"].__setitem__("host_role", "termux"), True),
            ("noncanonical-json", "result_present", lambda v: None, False),
        ]
        for name, expected, mutator, canonical in mutations:
            case_root = temp / f"case-{name}"
            result_dir = make_result(case_root)
            mutate_result(result_dir, mutator, canonical=canonical)
            observed = verify(result_dir)
            passed = not observed["pass"] and (expected in observed["failed_checks"] or bool(observed.get("parse_errors")))
            record(name, passed, observed.get("failed_checks"))

        valid_root = temp / "archive-valid"
        valid_root.mkdir()
        valid_members = [("python", "directory", None), ("python/bin", "directory", None), ("python/bin/python3.14", "regular", b"python"), ("python/bin/python", "symlink", "python3.14")]
        valid_archive, valid_manifest = archive_fixture(valid_root, valid_members)
        record("archive-valid", QUALIFY.inspect_archive(valid_archive, valid_manifest)["pass"])

        escape_root = temp / "archive-escape"; escape_root.mkdir()
        escape_archive, escape_manifest = archive_fixture(escape_root, [("../escape", "regular", b"x")])
        record("archive-path-escape", rejected(lambda: QUALIFY.inspect_archive(escape_archive, escape_manifest)))

        hard_root = temp / "archive-hardlink"; hard_root.mkdir()
        hard_archive, hard_manifest = archive_fixture(hard_root, [("python", "directory", None), ("python/a", "regular", b"x"), ("python/b", "hardlink", "python/a")])
        record("archive-hardlink", rejected(lambda: QUALIFY.inspect_archive(hard_archive, hard_manifest)))

        symlink_root = temp / "archive-symlink"; symlink_root.mkdir()
        symlink_archive, symlink_manifest = archive_fixture(symlink_root, [("python", "directory", None), ("python/bin", "directory", None), ("python/bin/python", "symlink", "../../../escape")])
        record("archive-symlink-escape", rejected(lambda: QUALIFY.inspect_archive(symlink_archive, symlink_manifest)))

        order_root = temp / "archive-order"; order_root.mkdir()
        order_archive, order_manifest = archive_fixture(order_root, valid_members, manifest_order=["python", "python/bin/python3.14", "python/bin", "python/bin/python"])
        record("archive-order-mismatch", rejected(lambda: QUALIFY.inspect_archive(order_archive, order_manifest)))

        counts = {name: len(CONTRACT["profile_checks"][name]) for name in CONTRACT["profile_checks"]}
        sorted_checks = all(CONTRACT["profile_checks"][name] == sorted(CONTRACT["profile_checks"][name]) for name in CONTRACT["profile_checks"])
        record("profile-matrix", counts == {"static": 9, "termux-real": 35, "termux-emulator": 35} and sorted_checks, counts)

    failed = [row["name"] for row in outcomes if not row["pass"]]
    result = {
        "schema_version": 1,
        "test_kind": "e2p3-archive-qualification-contract-regression",
        "pass": not failed,
        "test_count": len(outcomes),
        "pass_count": sum(row["pass"] for row in outcomes),
        "failed_tests": failed,
        "tests": outcomes,
        "claim_boundary": "Contract, result-verifier, and archive-safety regression only; no Android target execution or qualification claim.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independently audit a Gate 4A A2a remote-input capture result archive.

This verifier intentionally preserves the original collector's FAIL record.  It
recomputes the intended evidence contract using a field projection for reused
first-product dependency identities, because the captured archive inventory
adds safety diagnostics that are not present in the older lock schema.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tarfile
import tempfile
from typing import Any

EXPECTED_ARCHIVE_SHA256 = "e9c9ed69098017017b3cbf70e8237c040ede26d378f6530043cc5ff4e7469caf"
EXPECTED_ARCHIVE_SIZE = 26218
EXPECTED_PACKAGE_SHA256 = "1b95da93389c9586d80db8501caa92bb4f213105bcc33febaf33fefb8215c187"
EXPECTED_RESULT_ROOT = "20260713-gate4a-a2a-remote-input-capture-20260713T132628Z"
EXPECTED_REPOSITORY = {
    "branch": "agent/phase5-gate4-second-product-authority",
    "head": "b807c2964b408adc954a7f5a2155030e7442ed05",
    "tree": "2f0106dc6f19ab2190dcb9c15454f6e041e44fa7",
}
EXPECTED_ORIGINAL_FAILED = {
    "reused_first_lock_exact_bzip2",
    "reused_first_lock_exact_libffi",
    "reused_first_lock_exact_sqlite",
    "reused_first_lock_exact_xz",
    "reused_first_lock_exact_zstd",
}
CORE_ARCHIVE_FIELDS = (
    "member_count",
    "regular_file_count",
    "directory_count",
    "symlink_count",
    "hardlink_count",
    "declared_regular_file_bytes",
    "top_level_paths",
)
STABLE_DEPENDENCY_FIELDS = (
    "version",
    "recipe_revision",
    "release_tag",
    "target_host",
    "filename",
    "source_url",
    "size_bytes",
    "sha256",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def safe_member_name(name: str) -> bool:
    p = PurePosixPath(name)
    return not p.is_absolute() and ".." not in p.parts


def extract_archive(archive: Path, destination: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if shutil.which("zstd") is None:
        raise RuntimeError("zstd command is required")
    tar_path = destination / "archive.tar"
    with tar_path.open("wb") as out:
        subprocess.run(["zstd", "-q", "-dc", "--", str(archive)], check=True, stdout=out)

    members: list[dict[str, Any]] = []
    problems: list[str] = []
    names: set[str] = set()
    with tarfile.open(tar_path, "r:") as tf:
        for member in tf.getmembers():
            kind = (
                "regular" if member.isfile() else
                "directory" if member.isdir() else
                "symlink" if member.issym() else
                "hardlink" if member.islnk() else
                "special"
            )
            members.append({
                "name": member.name,
                "kind": kind,
                "size": member.size,
                "linkname": member.linkname,
            })
            if member.name in names:
                problems.append(f"duplicate member: {member.name}")
            names.add(member.name)
            if not safe_member_name(member.name):
                problems.append(f"unsafe member path: {member.name}")
            if kind not in {"regular", "directory"}:
                problems.append(f"non-regular archive entry: {member.name} ({kind})")

        if problems:
            return members, problems

        extract_root = destination / "extract"
        extract_root.mkdir()
        for member in tf.getmembers():
            target = extract_root / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = tf.extractfile(member)
            if source is None:
                problems.append(f"could not read regular member: {member.name}")
                continue
            with source, target.open("wb") as out:
                shutil.copyfileobj(source, out)
            os.chmod(target, stat.S_IMODE(member.mode))
    return members, problems


def parse_writeout(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-archive-sha256", default=EXPECTED_ARCHIVE_SHA256)
    args = parser.parse_args()

    repo = args.repo.resolve()
    archive = args.archive.resolve()
    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}

    def check(name: str, value: bool, detail: Any | None = None) -> None:
        checks[name] = bool(value)
        if detail is not None:
            details[name] = detail

    archive_sha = sha256_file(archive)
    archive_size = archive.stat().st_size
    check("archive_sha256_exact", archive_sha == args.expected_archive_sha256,
          {"expected": args.expected_archive_sha256, "observed": archive_sha})
    check("archive_size_exact", archive_size == EXPECTED_ARCHIVE_SIZE,
          {"expected": EXPECTED_ARCHIVE_SIZE, "observed": archive_size})

    with tempfile.TemporaryDirectory(prefix="gate4a-a2a-audit-") as td:
        temp = Path(td)
        try:
            members, archive_problems = extract_archive(archive, temp)
        except Exception as exc:  # fail closed with a machine-readable result
            members, archive_problems = [], [f"archive extraction error: {exc}"]
        details["archive_members"] = {
            "count": len(members),
            "regular": sum(m["kind"] == "regular" for m in members),
            "directory": sum(m["kind"] == "directory" for m in members),
            "problems": archive_problems,
        }
        check("archive_readable_and_safe", not archive_problems)
        roots = sorted({PurePosixPath(m["name"]).parts[0] for m in members if PurePosixPath(m["name"]).parts})
        check("archive_single_expected_root", roots == [EXPECTED_RESULT_ROOT], {"roots": roots})

        root = temp / "extract" / EXPECTED_RESULT_ROOT
        check("expected_result_root_present", root.is_dir())
        if not root.is_dir():
            result = {
                "schema_version": 1,
                "verification_kind": "external-gate4a-a2a-remote-input-capture-audit",
                "archive_sha256": archive_sha,
                "archive_size": archive_size,
                "package_sha256": EXPECTED_PACKAGE_SHA256,
                "checks": checks,
                "details": details,
                "failed_checks": sorted(k for k, v in checks.items() if not v),
            }
            result["check_count"] = len(checks)
            result["pass_count"] = sum(checks.values())
            result["pass"] = all(checks.values())
            if args.output:
                args.output.write_bytes(canonical_json_bytes(result))
            else:
                print(canonical_json_bytes(result).decode(), end="")
            return 1

        index_path = root / "result-index.json"
        capture_path = root / "evidence/gate4a-a2a-remote-input-capture.json"
        original_verification_path = root / "evidence/gate4a-a2a-verification.json"
        run_log_path = root / "run.log"
        required = [index_path, capture_path, original_verification_path, run_log_path]
        check("required_control_files_present", all(p.is_file() for p in required),
              {"missing": [str(p.relative_to(root)) for p in required if not p.is_file()]})

        index = load_json(index_path)
        capture = load_json(capture_path)
        original = load_json(original_verification_path)
        run_log = run_log_path.read_text()

        check("result_index_canonical", index_path.read_bytes() == canonical_json_bytes(index))
        check("capture_json_canonical", capture_path.read_bytes() == canonical_json_bytes(capture))
        check("original_verification_json_canonical",
              original_verification_path.read_bytes() == canonical_json_bytes(original))
        check("result_index_schema_exact",
              index.get("schema_version") == 1 and
              index.get("verification_kind") == "gate4a-a2a-result-index")

        indexed: dict[str, dict[str, Any]] = {}
        index_problems: list[Any] = []
        for entry in index.get("files", []):
            rel = entry.get("path")
            if not isinstance(rel, str) or rel in indexed or not safe_member_name(rel):
                index_problems.append(["bad_or_duplicate_path", rel])
                continue
            indexed[rel] = entry
            path = root / rel
            if not path.is_file() or path.is_symlink():
                index_problems.append(["missing_or_not_regular", rel])
                continue
            data = path.read_bytes()
            observed_mode = f"{stat.S_IMODE(path.stat().st_mode):04o}"
            if entry.get("type") != "regular":
                index_problems.append(["type", rel, entry.get("type")])
            if entry.get("size") != len(data):
                index_problems.append(["size", rel, entry.get("size"), len(data)])
            if entry.get("sha256") != sha256_bytes(data):
                index_problems.append(["sha256", rel])
            if entry.get("mode") != observed_mode:
                index_problems.append(["mode", rel, entry.get("mode"), observed_mode])

        actual = {
            p.relative_to(root).as_posix()
            for p in root.rglob("*")
            if p.is_file() and not p.is_symlink() and p.name != "result-index.json"
        }
        check("result_index_file_count_exact",
              index.get("file_count") == len(index.get("files", [])) == len(actual),
              {"declared": index.get("file_count"), "entries": len(index.get("files", [])), "actual": len(actual)})
        check("result_index_membership_exact", set(indexed) == actual,
              {"missing": sorted(actual - set(indexed)), "extra": sorted(set(indexed) - actual)})
        check("result_index_identities_exact", not index_problems, index_problems)

        original_failed = set(original.get("failed_checks", []))
        check("original_verifier_failure_preserved",
              original.get("pass") is False and original_failed == EXPECTED_ORIGINAL_FAILED,
              {"pass": original.get("pass"), "failed_checks": sorted(original_failed)})
        check("original_verifier_44_of_49_exact",
              original.get("pass_count") == 44 and original.get("check_count") == 49)
        check("run_log_failure_markers_exact",
              "GATE4A_A2A_REMOTE_INPUT_CAPTURE=FAIL" in run_log and
              "CHECKS=44/49" in run_log and
              "TOOLCHAIN_WITNESS_STATUS=pending-linux-workstation-witness" in run_log)

        lock = load_json(repo / "config/dependencies/android-source-deps-aarch64-linux-android.lock.json")
        selected = load_json(repo / "experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-input.json")
        lock_by_name = {item["name"]: item for item in lock["products"]}
        selected_by_name = {item["name"]: item for item in selected["dependency_selection"]["products"]}
        captured_by_name = {item["name"]: item for item in capture["dependencies"]}

        check("repository_binding_exact", capture.get("repository_binding") == EXPECTED_REPOSITORY,
              capture.get("repository_binding"))
        check("repository_sidecars_exact",
              (root / "evidence/repository-head.txt").read_text().strip() == EXPECTED_REPOSITORY["head"] and
              (root / "evidence/repository-tree.txt").read_text().strip() == EXPECTED_REPOSITORY["tree"] and
              (root / "evidence/repository-branch.txt").read_text().strip() == EXPECTED_REPOSITORY["branch"])
        for name in ("repository_branch_exact", "repository_head_exact", "repository_tree_exact", "repository_clean"):
            check(f"original_{name}", original.get("checks", {}).get(name) is True)

        source_expected = selected["second_product_selection"]
        source = capture["source"]
        check("source_tag_commit_exact",
              source.get("tag") == source_expected["source_tag"] and
              source.get("commit") == source_expected["source_head"])
        check("source_tag_object_present", original["checks"].get("source_tag_object_present") is True)
        for producer_path, producer_expected in source_expected["source_native_producer"].items():
            observed = source["producer_files"][producer_path]
            evidence_path = root / "evidence" / observed["evidence_file"]
            check(f"producer_blob_{Path(producer_path).name}_exact",
                  observed["git_blob_sha"] == producer_expected["git_blob_sha"])
            check(f"producer_sha256_{Path(producer_path).name}_exact",
                  observed["sha256"] == sha256_file(evidence_path) and
                  observed["size_bytes"] == evidence_path.stat().st_size)
            check(f"source_tar_match_{Path(producer_path).name}",
                  original["checks"].get(f"source_tar_matches_git_{Path(producer_path).name}") is True)

        official_expected = source_expected["official_references"]
        official_observed = {item["kind"]: item for item in capture["official_references"]}
        official_mapping = {
            "source_tar_xz": "source-tar-xz",
            "android_aarch64_package": "official-android-reference",
        }
        for expected_key, observed_key in official_mapping.items():
            expected = official_expected[expected_key]
            observed = official_observed[observed_key]
            check(f"official_{observed_key}_identity_exact",
                  observed["filename"] == expected["filename"] and
                  observed["requested_url"] == expected["url"] and
                  observed["sha256"] == expected["sha256"] and
                  observed["expected_sha256"] == expected["sha256"] and
                  observed["sha256_matches_expected"] is True and
                  observed["http_code"] == 200)
            check(f"official_{observed_key}_archive_safe",
                  not observed["archive"]["unsafe_member_names"] and
                  not observed["archive"]["unsafe_link_targets"] and
                  observed["archive"]["other_count"] == 0)

        expected_names = set(selected_by_name)
        check("dependency_name_set_exact", set(captured_by_name) == expected_names,
              {"expected": sorted(expected_names), "observed": sorted(captured_by_name)})
        check("dependency_count_exact", len(captured_by_name) == 6)

        projection_details: dict[str, Any] = {}
        for name in sorted(expected_names):
            observed = captured_by_name[name]
            selected_dep = selected_by_name[name]
            check(f"dependency_release_tag_{name}_exact",
                  observed["release_tag"] == selected_dep["release_tag"] and
                  observed["filename"] == selected_dep["filename"])

            release_file = root / "evidence" / f"github-release-{observed['release_tag']}.json"
            release = load_json(release_file)
            assets = [asset for asset in release.get("assets", []) if asset.get("name") == observed["filename"]]
            check(f"release_asset_unique_{name}", len(assets) == 1)
            if assets:
                asset = assets[0]
                digest = asset.get("digest")
                check(f"release_asset_identity_{name}",
                      asset.get("browser_download_url") == observed["source_url"] and
                      asset.get("size") == observed["size_bytes"] and
                      (digest is None or digest == f"sha256:{observed['sha256']}") and
                      observed["github_release"]["asset_id"] == asset.get("id") and
                      observed["github_release"]["asset_size"] == asset.get("size"))

            writeout = parse_writeout(root / "evidence" / observed["http_observation"]["writeout_file"])
            check(f"http_observation_{name}_exact",
                  observed["http_observation"]["http_code"] == 200 and
                  writeout.get("http_code") == "200" and
                  int(writeout.get("size_download", "-1")) == observed["size_bytes"])
            inv = observed["archive"]
            check(f"dependency_archive_safe_{name}",
                  inv.get("other_count") == 0 and
                  inv.get("unsafe_member_names") == [] and
                  inv.get("unsafe_link_targets") == [])

            if name != "openssl":
                prior = lock_by_name[name]
                stable_diff = {
                    key: {"expected": prior.get(key), "observed": observed.get(key)}
                    for key in STABLE_DEPENDENCY_FIELDS
                    if prior.get(key) != observed.get(key)
                }
                archive_diff = {
                    key: {"expected": prior["archive"].get(key), "observed": inv.get(key)}
                    for key in CORE_ARCHIVE_FIELDS
                    if prior["archive"].get(key) != inv.get(key)
                }
                added_safety = {
                    key: inv.get(key)
                    for key in ("other_count", "unsafe_member_names", "unsafe_link_targets")
                }
                projection_details[name] = {
                    "stable_diff": stable_diff,
                    "core_archive_diff": archive_diff,
                    "added_safety_fields": added_safety,
                }
                check(f"reused_first_lock_projected_exact_{name}", not stable_diff and not archive_diff)
                check(f"reused_first_lock_safety_extension_valid_{name}",
                      added_safety == {
                          "other_count": 0,
                          "unsafe_member_names": [],
                          "unsafe_link_targets": [],
                      })
            else:
                prior = lock_by_name[name]
                check("openssl_3020_exact", observed["release_tag"] == "openssl-3.0.20-0")
                check("openssl_differs_from_first_product",
                      prior["release_tag"] != observed["release_tag"] and
                      prior["sha256"] != observed["sha256"])
        details["reused_dependency_projection"] = projection_details

        declared = capture["declared_toolchain"]
        check("declared_api_ndk_exact",
              declared["android_api"] == source_expected["android_api"] == 24 and
              declared["ndk_version"] == source_expected["ndk_version"] == "27.3.13750724")
        local_witness = capture["local_toolchain_witness"]
        check("toolchain_witness_pending_exact",
              local_witness["status"] == "pending-linux-workstation-witness" and
              (root / "evidence/toolchain-witness-status.txt").read_text().strip() == "pending-linux-workstation-witness")
        check("capture_claim_boundary_preserved",
              "immutable remote inputs" in capture["claim_boundary"]["proved"].lower() and
              "linux workstation ndk" in capture["claim_boundary"]["not_proved"].lower())

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "verification_kind": "external-gate4a-a2a-remote-input-capture-audit",
        "archive_sha256": archive_sha,
        "archive_size": archive_size,
        "package_sha256": EXPECTED_PACKAGE_SHA256,
        "repository_binding": EXPECTED_REPOSITORY,
        "original_collector_result": {
            "status": "fail",
            "checks": "44/49",
            "failed_checks": sorted(EXPECTED_ORIGINAL_FAILED),
            "classification": "false-negative-schema-comparison",
        },
        "acceptance": {
            "a2a_remote_inputs": "accepted" if not failed else "not-accepted",
            "a2b_linux_workstation_toolchain_witness": "pending",
            "a2_overall": "open",
            "a3_through_a6": "pending",
        },
        "checks": checks,
        "details": details,
        "failed_checks": failed,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "pass": not failed,
    }
    payload = canonical_json_bytes(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
    else:
        print(payload.decode(), end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

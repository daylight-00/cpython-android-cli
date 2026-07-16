#!/usr/bin/env python3
"""Regression tests for the E2-P2 build/package/verify façade."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    expect: int = 0,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    # File-backed capture prevents pipe-EOF waits when compiler or compressor
    # grandchildren inherit the command's stdout/stderr descriptors.
    with tempfile.TemporaryDirectory(prefix="e2p2-test-capture-") as temp_name:
        stdout_path = Path(temp_name) / "stdout"
        stderr_path = Path(temp_name) / "stderr"
        with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
            try:
                proc = subprocess.run(
                    command,
                    cwd=cwd,
                    env=env,
                    text=True,
                    stdout=stdout,
                    stderr=stderr,
                    timeout=timeout,
                )
                returncode = proc.returncode
            except subprocess.TimeoutExpired:
                returncode = 124
                stderr.write(f"timeout after {timeout}s: {' '.join(command)}\n")
        result = subprocess.CompletedProcess(
            command,
            returncode,
            stdout_path.read_text(encoding="utf-8", errors="replace"),
            stderr_path.read_text(encoding="utf-8", errors="replace"),
        )
    if result.returncode != expect:
        raise AssertionError(
            f"command rc {result.returncode} != {expect}: {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def init_git(root: Path) -> None:
    run(["git", "init", "-q"], root)
    run(["git", "config", "user.name", "E2P2 Test"], root)
    run(["git", "config", "user.email", "e2p2@example.invalid"], root)
    run(["git", "add", "."], root)
    run(["git", "commit", "-qm", "fixture"], root)


def write_product_lock(root: Path) -> None:
    path = root / "config/products/cpython-3.14.6-aarch64-linux-android.lock.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes({
        "schema_version": 1,
        "product_kind": "upstream-cpython-android-package",
        "python_version": "3.14.6",
        "source_head": "c63aec69bd59c55314c06c23f4c22c03de76fe45",
        "target_host": "aarch64-linux-android",
        "android_api": 24,
        "ndk_version": "27.3.13750724",
        "archive": {"filename": "python-3.14.6-aarch64-linux-android.tar.gz", "size_bytes": 1, "sha256": "0" * 64},
        "package_prefix_root": "prefix",
        "launcher_development_contract": {},
    }))


def make_package_fixture(root: Path, source_repo: Path) -> tuple[Path, Path, Path]:
    lib = root / "components/standalone/lib"
    lib.mkdir(parents=True, exist_ok=True)
    for name in ("package_e2p1.py", "verify_envelope.py"):
        shutil.copy2(source_repo / "components/standalone/lib" / name, lib / name)
    write_product_lock(root)
    init_git(root)

    prefix = root / "fixture-prefix"
    for rel in (
        "bin",
        "include/python3.14",
        "lib/pkgconfig",
        "lib/python3.14/config-3.14-aarch64-linux-android",
        "lib/python3.14/test",
        "lib/python3.14/tkinter",
        "lib/python3.14/__phello__",
    ):
        (prefix / rel).mkdir(parents=True, exist_ok=True)
    (prefix / "include/python3.14/Python.h").write_text("/* fixture */\n")
    (prefix / "lib/pkgconfig/python-3.14.pc").write_text("prefix=/fixture\n")
    (prefix / "lib/python3.14/config-3.14-aarch64-linux-android/Makefile").write_text("VERSION=3.14\n")
    (prefix / "lib/python3.14/os.py").write_text("name = 'posix'\n")
    (prefix / "lib/python3.14/LICENSE.txt").write_text("Python Software Foundation License fixture\n")
    (prefix / "lib/python3.14/test/test_fixture.py").write_text("raise AssertionError\n")
    (prefix / "lib/python3.14/tkinter/__init__.py").write_text("raise ImportError\n")
    (prefix / "lib/python3.14/__phello__/spam.py").write_text("print('test')\n")
    (prefix / "lib/python3.14/turtle.py").write_text("raise RuntimeError\n")
    source = root / "tiny.c"
    source.write_text("int fixture(void) { return 42; }\n")
    run(["cc", "-shared", "-fPIC", "-o", str(prefix / "lib/libpython3.14.so"), str(source)], root)
    os.symlink("libpython3.14.so", prefix / "lib/libpython3.14.so.1")

    launcher = root / "python3.14"
    launcher.write_text("#!/bin/sh\nexec /bin/true \"$@\"\n")
    launcher.chmod(0o755)
    strip_tool = root / "fake-llvm-strip"
    strip_tool.write_text(f"#!{sys.executable}\nimport sys\nif '--version' in sys.argv: print('fake llvm-strip 1.0')\nraise SystemExit(0)\n")
    strip_tool.chmod(0o755)
    return prefix, launcher, strip_tool


def package_twice(source_repo: Path, temp: Path) -> tuple[Path, Path]:
    fake = temp / "package-root"
    fake.mkdir()
    prefix, launcher, strip_tool = make_package_fixture(fake, source_repo)
    env = os.environ.copy()
    env["ANDROID_CC"] = "/opt/android/aarch64-linux-android24-clang"
    package = fake / "components/standalone/lib/package_e2p1.py"
    outputs = []
    for name in ("release-a", "release-b"):
        out = fake / name
        run([
            sys.executable, str(package), "--root", str(fake), "--source-prefix", str(prefix),
            "--launcher", str(launcher), "--output-dir", str(out), "--strip-tool", str(strip_tool),
        ], fake, env=env)
        outputs.append(out)
    names_a = sorted(path.name for path in outputs[0].iterdir() if path.is_file())
    names_b = sorted(path.name for path in outputs[1].iterdir() if path.is_file())
    if names_a != names_b or len(names_a) != 8:
        raise AssertionError(f"release asset set mismatch: {names_a} {names_b}")
    for name in names_a:
        if (outputs[0] / name).read_bytes() != (outputs[1] / name).read_bytes():
            raise AssertionError(f"non-deterministic release asset: {name}")
    manifest = json.loads(next(outputs[0].glob("*.manifest.json")).read_text())
    paths = {row["path"] for row in manifest["entries"]}
    forbidden = {"python/lib/python3.14/test", "python/lib/python3.14/tkinter", "python/lib/python3.14/__phello__", "python/lib/python3.14/turtle.py"}
    if any(path in paths or any(item.startswith(path + "/") for item in paths) for path in forbidden):
        raise AssertionError("excluded payload paths leaked into release")
    if {row["payload_class"] for row in manifest["entries"]} != {"runtime", "development"}:
        raise AssertionError("payload class coverage mismatch")
    return fake, outputs[0]


def mutate_and_require_failure(fake: Path, release: Path) -> None:
    verifier = fake / "components/standalone/lib/verify_envelope.py"
    archive = next(release.glob("*.tar.zst"))
    original = archive.read_bytes()
    archive.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
    proc = run([sys.executable, str(verifier), "--root", str(fake), "--release-dir", str(release)], fake, expect=1)
    result = json.loads(proc.stdout)
    if result.get("pass") is not False or not result.get("failed_checks"):
        raise AssertionError("mutated archive was not rejected")
    archive.write_bytes(original)


def make_facade_fixture(source_repo: Path, temp: Path) -> tuple[Path, Path]:
    root = temp / "facade-root"
    root.mkdir()
    steps_dir = root / "steps"
    steps_dir.mkdir()
    values = {
        "TARGET_ID": "aarch64-linux-android24",
        "TARGET_HOST": "aarch64-linux-android",
        "BUILD_PROFILE": "release",
        "PYTHON_VERSION": "3.14.6",
        "PYTHON_MM": "3.14",
        "PROJECT_ROLE": "workstation",
    }
    output_paths = [
        "out/aarch64-linux-android24/release/cpython/python-3.14.6-aarch64-linux-android.tar.gz",
        "out/aarch64-linux-android24/release/cpython/SHA256SUMS",
        "out/aarch64-linux-android24/release/metadata/cpython-product.json",
        "out/aarch64-linux-android24/release/bin/python3.14",
        "out/aarch64-linux-android24/release/metadata/build-info.txt",
    ]
    markers = ["PREPARE=PASS", "BUILD=PASS", "PROMOTE=PASS", "LAUNCHER=PASS"]
    for index, marker in enumerate(markers):
        path = steps_dir / f"step-{index}.sh"
        body = ["#!/bin/sh", "set -eu"]
        if index == len(markers) - 1:
            for rel in output_paths:
                body.extend([f"mkdir -p \"$(dirname '{rel}')\"", f"printf '%s\\n' '{rel}' > '{rel}'"])
        body.append(f"echo '{marker}'")
        path.write_text("\n".join(body) + "\n")
        path.chmod(0o755)
    init_git(root)
    step_rows = []
    for index, marker in enumerate(markers):
        rel = f"steps/step-{index}.sh"
        blob = run(["git", "hash-object", rel], root).stdout.strip()
        step_rows.append({"id": f"step-{index}", "path": rel, "blob_sha": blob, "marker": marker})
    contract = {
        "schema_version": 1,
        "contract_version": 1,
        "facade_kind": "hw-t-standalone-build-package-verify-facade",
        "stable_command": "components/standalone/bin/cpython-android-standalone",
        "predecessor": {},
        "tracked_inputs": [],
        "operations": {
            "build": {
                "host_role": "workstation",
                "steps": step_rows,
                "outputs": [
                    "out/{target_id}/{build_profile}/cpython/python-{python_version}-{target_host}.tar.gz",
                    "out/{target_id}/{build_profile}/cpython/SHA256SUMS",
                    "out/{target_id}/{build_profile}/metadata/cpython-product.json",
                    "out/{target_id}/{build_profile}/bin/python3.14",
                    "out/{target_id}/{build_profile}/metadata/build-info.txt",
                ],
                "receipt": "results/workstation/epoch2-standalone/build-receipt.json",
            },
            "package": {"host_role": "workstation", "primary_flavor": "install_only_stripped", "archive_root": "python/", "payload_classes": ["runtime", "development"], "implementation": "package.py", "input_prefix": "prefix", "input_launcher": "launcher", "output_dir": "dist"},
            "verify": {"scopes": ["repository", "envelope"], "repository_implementation": "verify-repo.py", "envelope_implementation": "verify-envelope.py"},
        },
    }
    contract_path = root / "facade.json"
    contract_path.write_bytes(canonical_json_bytes(contract))
    env_file = root / "env.json"
    env_file.write_bytes(canonical_json_bytes(values))
    return root, contract_path


def test_facade_execution(source_repo: Path, temp: Path) -> None:
    root, contract = make_facade_fixture(source_repo, temp)
    facade = source_repo / "components/standalone/lib/facade.py"
    env = os.environ.copy()
    env.update(json.loads((root / "env.json").read_text()))
    plan = run([sys.executable, str(facade), "--root", str(root), "--contract", str(contract), "build", "--dry-run"], root, env=env)
    if json.loads(plan.stdout).get("operation") != "build":
        raise AssertionError("build dry-run plan missing")
    run([sys.executable, str(facade), "--root", str(root), "--contract", str(contract), "build"], root, env=env)
    receipt = json.loads((root / "results/workstation/epoch2-standalone/build-receipt.json").read_text())
    if receipt.get("status") != "passed" or len(receipt.get("outputs", [])) != 5:
        raise AssertionError("build receipt mismatch")
    first = root / "steps/step-0.sh"
    first.write_text(first.read_text() + "# drift\n")
    proc = run([sys.executable, str(facade), "--root", str(root), "--contract", str(contract), "build", "--dry-run"], root, env=env, expect=2)
    if "tracked_blobs_exact" not in proc.stdout:
        raise AssertionError("entrypoint drift was not rejected")


def main() -> int:
    parser_root = Path(__file__).resolve().parents[2]
    tests: list[tuple[str, bool, str]] = []
    with tempfile.TemporaryDirectory(prefix="e2p2-tests-") as temp_name:
        temp = Path(temp_name)
        cases = [
            ("package_reproducibility", lambda: package_twice(parser_root, temp)),
            ("facade_execution_and_drift", lambda: test_facade_execution(parser_root, temp)),
        ]
        package_state: tuple[Path, Path] | None = None
        for name, case in cases:
            try:
                value = case()
                if name == "package_reproducibility":
                    package_state = value
                tests.append((name, True, ""))
            except Exception as exc:
                tests.append((name, False, f"{type(exc).__name__}: {exc}"))
        if package_state:
            try:
                mutate_and_require_failure(*package_state)
                tests.append(("archive_mutation_rejected", True, ""))
            except Exception as exc:
                tests.append(("archive_mutation_rejected", False, f"{type(exc).__name__}: {exc}"))

    failed = [name for name, passed, _ in tests if not passed]
    result = {
        "schema_version": 1,
        "test_kind": "e2p2-standalone-facade-regression",
        "pass": not failed,
        "test_count": len(tests),
        "pass_count": sum(passed for _, passed, _ in tests),
        "failed_tests": failed,
        "tests": [{"name": name, "pass": passed, "error": error or None} for name, passed, error in tests],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

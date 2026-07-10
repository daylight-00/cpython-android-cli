#!/usr/bin/env python3
from __future__ import annotations

import argparse, ast, hashlib, json, os, platform, re, shlex, shutil, subprocess, sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> dict:
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=20)
        return {"command": shlex.join(cmd), "returncode": p.returncode,
                "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as e:
        return {"command": shlex.join(cmd), "returncode": None,
                "stdout": "", "stderr": repr(e)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pinfo(path: Path | None, hash_file: bool = False) -> dict:
    if path is None:
        return {"path": None, "exists": False}
    d = {"path": str(path), "exists": path.exists()}
    if path.exists():
        d["realpath"] = str(path.resolve())
        d["type"] = "file" if path.is_file() else "directory" if path.is_dir() else "other"
        if path.is_file():
            d["size_bytes"] = path.stat().st_size
            if hash_file:
                d["sha256"] = sha256(path)
    return d


def git_id(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {"path": str(path) if path else None, "is_git_worktree": False}
    top = run(["git", "-C", str(path), "rev-parse", "--show-toplevel"])
    if top["returncode"] != 0:
        return {"path": str(path), "is_git_worktree": False}
    root = Path(top["stdout"])

    def q(*args: str) -> str | None:
        r = run(["git", "-C", str(root), *args])
        return r["stdout"] if r["returncode"] == 0 else None

    status = q("status", "--porcelain=v1") or ""
    return {"path": str(path), "is_git_worktree": True, "toplevel": str(root),
            "head": q("rev-parse", "HEAD"), "describe": q("describe", "--tags", "--always", "--dirty"),
            "branch": q("branch", "--show-current"), "origin": q("remote", "get-url", "origin"),
            "dirty_path_count": len([x for x in status.splitlines() if x.strip()])}


def defaults(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k] = v.strip().strip("\"'")
    return out


def sysconfig_vars(path: Path) -> dict:
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "build_time_vars" for t in node.targets):
            values = ast.literal_eval(node.value)
            keys = ["CONFIG_ARGS", "AR", "CC", "CXX", "CFLAGS", "LDFLAGS", "CONFIGURE_CFLAGS",
                    "CONFIGURE_LDFLAGS", "PYTHON_FOR_BUILD", "PYTHON_FOR_FREEZE", "BUILD_GNU_TYPE",
                    "HOST_GNU_TYPE", "prefix", "exec_prefix", "LIBDIR", "INCLUDEPY", "DESTSHARED",
                    "TZPATH", "SOABI", "EXT_SUFFIX", "MULTIARCH"]
            return {k: values.get(k) for k in keys if k in values}
    return {"error": "build_time_vars not found"}


def tool(name: str, args: list[str]) -> dict:
    exe = shutil.which(name)
    return {"found": False} if not exe else {"found": True, "path": exe, "probe": run([exe, *args])}


def write_tsv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w") as f:
        f.write("\t".join(fields) + "\n")
        for row in rows:
            f.write("\t".join(str(row.get(k, "")).replace("\t", " ").replace("\n", "\\n") for k in fields) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--android-cc")
    ap.add_argument("--cpython-dev-prefix")
    ap.add_argument("--cpython-src")
    ap.add_argument("--runtime-archive")
    a = ap.parse_args()

    root, out = Path(a.project_root).resolve(), Path(a.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cfg = defaults(root / "config/defaults.env")
    ver = cfg.get("PYTHON_VERSION", "3.14.6")
    mm = cfg.get("PYTHON_MM", "3.14")
    target = cfg.get("TARGET_ID", "aarch64-linux-android24")
    host = re.sub(r"\d+$", "", target)
    snap = root / "experiments/bootstrap-android-build/android-python-work"
    android_py, android_env = snap / "android.py", snap / "android-env.sh"
    dev = Path(a.cpython_dev_prefix).resolve() if a.cpython_dev_prefix else None
    cc = Path(a.android_cc).resolve() if a.android_cc else None
    archive = Path(a.runtime_archive).expanduser().resolve() if a.runtime_archive else None

    candidates = []
    if a.cpython_src:
        candidates.append(Path(a.cpython_src).expanduser())
    if os.environ.get("CPYTHON_SRC"):
        candidates.append(Path(os.environ["CPYTHON_SRC"]).expanduser())
    candidates += [root / "tools" / f"cpython-{ver}", root / "tools/cpython", Path.home() / "tmp/tools" / f"cpython-{ver}"]
    src = next((p for p in candidates if p.exists()), None)

    toolchain = {"defaults": {"target_id": target, "android_api": cfg.get("ANDROID_API"), "python_version": ver}}
    if cc:
        toolchain.update({"compiler_path": str(cc), "exists": cc.exists(),
                          "version_probe": run([str(cc), "--version"]),
                          "dumpmachine_probe": run([str(cc), "-dumpmachine"])})
        m = re.search(r"^(.+)/ndk/([^/]+)/toolchains/llvm/prebuilt/([^/]+)/bin/([^/]+)$", str(cc))
        if m:
            toolchain.update({"android_sdk_root_derived": m.group(1), "ndk_version_derived": m.group(2),
                              "toolchain_prebuilt_host": m.group(3), "compiler_driver": m.group(4)})
        if cc.is_file():
            toolchain["sha256"] = sha256(cc)
    if android_env.is_file():
        m = re.search(r"^ndk_version=(.+)$", android_env.read_text(), re.M)
        toolchain["ndk_version_from_android_env"] = m.group(1).strip() if m else None
    toolchain["host"] = {"platform": platform.platform(), "system": platform.system(), "release": platform.release(),
                         "machine": platform.machine(), "python_executable": sys.executable, "python_version": sys.version,
                         "tools": {"make": tool("make", ["--version"]), "pkg-config": tool("pkg-config", ["--version"]),
                                   "curl": tool("curl", ["--version"]), "java": tool("java", ["-version"]),
                                   "git": tool("git", ["--version"])}}

    deps, base_url = [], ""
    if android_py.is_file():
        text = android_py.read_text()
        m = re.search(r"deps_url\s*=\s*[\"']([^\"']+)", text)
        base_url = m.group(1) if m else ""
        for token in re.findall(r"[\"']([A-Za-z0-9_+.-]+-\d+)[\"']", text):
            m = re.fullmatch(r"([A-Za-z0-9_+]+)-(.+)-(\d+)", token)
            if m and m.group(1) in {"bzip2", "libffi", "openssl", "sqlite", "xz", "zstd"} and not any(x["release_tag"] == token for x in deps):
                deps.append({"name": m.group(1), "version": m.group(2), "recipe_revision": m.group(3),
                             "release_tag": token, "source_base_url": base_url,
                             "expected_archive_name": f"{token}-{host}.tar.gz", "source_script": str(android_py)})

    sc = []
    if dev and dev.is_dir():
        for p in sorted(dev.glob("lib/python*/_sysconfigdata__android_*.py")):
            try:
                selected = sysconfig_vars(p)
            except Exception as e:
                selected = {"error": repr(e)}
            sc.append({"path": str(p), "sha256": sha256(p), "selected_build_time_vars": selected})

    key_paths = [root / "src/launcher/python.c", root / "scripts/build/build-launcher.sh",
                 root / "scripts/termux/prepare-runtime.sh", root / "config/defaults.env", android_py,
                 android_env, snap / "README.md", root / "config/legacy/env.sh", root / "config/legacy/env-260704.sh"]
    if dev:
        key_paths += [dev / f"include/python{mm}/Python.h", dev / f"include/python{mm}/pyconfig.h",
                      dev / f"lib/libpython{mm}.so"]
    if archive:
        key_paths.append(archive)

    evidence = []
    boot = root / "experiments/bootstrap-android-build"
    if boot.is_dir():
        for p in boot.rglob("*"):
            if p.is_file() and (p.name in {"config.log", "config.status", "Makefile", "pybuilddir.txt", "Setup.local"} or p.suffix == ".log"):
                evidence.append({"relative_path": str(p.relative_to(boot)), "size_bytes": p.stat().st_size,
                                 "sha256": sha256(p), "path": str(p)})

    inputs = {"schema_version": 1, "stage": "3-B-phase1-current-provenance", "project_root": str(root),
              "project_git": git_id(root), "defaults": cfg,
              "target": {"target_id": target, "target_host": host, "android_api": cfg.get("ANDROID_API"),
                         "python_version": ver, "python_mm": mm},
              "current_paths": {"android_snapshot": pinfo(snap), "cpython_dev_prefix": pinfo(dev),
                                "cpython_source": pinfo(src), "runtime_archive": pinfo(archive),
                                "android_cc": pinfo(cc, True)},
              "cpython_source_git": git_id(src), "source_candidates_checked": [str(p) for p in candidates],
              "sysconfigdata": sc, "key_artifacts": [pinfo(p, True) for p in key_paths],
              "historical_build_evidence_file_count": len(evidence)}

    (out / "current-build-inputs.json").write_text(json.dumps(inputs, indent=2, sort_keys=True) + "\n")
    (out / "current-toolchain-identity.json").write_text(json.dumps(toolchain, indent=2, sort_keys=True) + "\n")
    write_tsv(out / "current-dependency-provenance.tsv", deps,
              ["name", "version", "recipe_revision", "release_tag", "source_base_url", "expected_archive_name", "source_script"])
    write_tsv(out / "current-build-evidence-files.tsv", evidence,
              ["relative_path", "size_bytes", "sha256", "path"])

    launcher = (root / "scripts/build/build-launcher.sh").read_text().splitlines()
    block, active = [], False
    for line in launcher:
        if line.startswith('"$ANDROID_CC"'):
            active = True
        if active:
            block.append(line)
        if active and '-o "$OUTPUT"' in line:
            break
    assembly = [line for line in (root / "scripts/termux/prepare-runtime.sh").read_text().splitlines()
                if re.search(r"\btar -xzf\b|\binstall -m 0755\b|\bln -sfn\b", line)]
    config_args = [str(x["selected_build_time_vars"].get("CONFIG_ARGS")) for x in sc
                   if x["selected_build_time_vars"].get("CONFIG_ARGS")]
    md = ["# Current Build Command Map", "", "> Generated by the Stage 3-B Phase 1 read-only provenance probe.", "",
          "## Evidence levels", "", "```text", "OBSERVED_CURRENT   current files, binaries, or generated metadata",
          "SNAPSHOT_PRODUCER  command path available in preserved Android tooling",
          "HISTORICAL_HINT    preserved legacy configuration",
          "NOT_YET_PROVEN     exact historical invocation not yet established", "```", "",
          "## Preserved Android producer flow", "", "Evidence level: `SNAPSHOT_PRODUCER`.", "", "```sh",
          "python android.py configure-build", "python android.py make-build",
          f"python android.py configure-host {host}", f"python android.py make-host {host}", "",
          "# Equivalent one-shot producer path:", f"python android.py build {host}", "```", "",
          "These are available producer paths, not proof of the exact historical invocation that produced the current prefix.", "",
          "## CONFIG_ARGS recovered from current sysconfigdata", ""]
    if config_args:
        for value in config_args:
            md += ["```text", value, "```", ""]
    else:
        md += ["`CONFIG_ARGS` was not recovered from the inspected development prefix.", ""]
    md += ["## Current launcher build command block", "", "Evidence level: `OBSERVED_CURRENT`.", "", "```sh",
           *(block or ["# not found"]), "```", "", "## Current Termux runtime assembly operations", "",
           "Evidence level: `OBSERVED_CURRENT`.", "", "```sh", *(assembly or ["# not found"]), "```", "",
           "## Phase 1 gap", "",
           "The exact historical command transcript remains `NOT_YET_PROVEN` unless recovered config logs, shell transcripts, or equivalent immutable producer evidence establishes it.", ""]
    (out / "current-build-command-map.md").write_text("\n".join(md))

    summary = {"schema_version": 1, "dependency_count": len(deps), "sysconfigdata_file_count": len(sc),
               "historical_build_evidence_file_count": len(evidence), "cpython_source_detected": src is not None,
               "cpython_source_git_identity_available": bool(inputs["cpython_source_git"].get("is_git_worktree")),
               "android_cc_exists": bool(cc and cc.exists()), "dev_prefix_exists": bool(dev and dev.exists()),
               "ndk_version_from_snapshot": toolchain.get("ndk_version_from_android_env"),
               "ndk_version_from_compiler_path": toolchain.get("ndk_version_derived"),
               "outputs": ["current-build-inputs.json", "current-toolchain-identity.json",
                           "current-dependency-provenance.tsv", "current-build-command-map.md",
                           "current-build-evidence-files.tsv"]}
    (out / "provenance-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import posixpath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

EXPECTED_ARCHIVE_SHA = "38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5"
EXPECTED_ARCHIVE_SIZE = 22358404
EXPECTED_CONTROL_SHA = "6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c"
EXPECTED_ARTIFACT_SHA = "387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306"
PYTHON_MM = "3.14"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(cmd: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None, timeout: int = 300, check: bool = False) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\nstdout:\n{p.stdout}\nstderr:\n{p.stderr}")
    return p


def normalize_member(name: str) -> str:
    if name.startswith("/"):
        raise ValueError(f"absolute archive member: {name}")
    n = posixpath.normpath(name)
    while n.startswith("./"):
        n = n[2:]
    if n in ("", "."):
        return "."
    if n == ".." or n.startswith("../"):
        raise ValueError(f"escaping archive member: {name}")
    return n


def safe_extract(archive: Path, dest: Path) -> dict[str, Any]:
    dest.mkdir(parents=True, exist_ok=True)
    pending_links: list[tuple[Path, str, bool]] = []
    seen: set[str] = set()
    material = 0
    with tarfile.open(archive, "r:gz") as tf:
        for m in tf:
            n = normalize_member(m.name)
            if n == ".":
                if not m.isdir():
                    raise ValueError("archive root marker is not a directory")
                continue
            if n in seen:
                raise ValueError(f"duplicate normalized member: {n}")
            seen.add(n)
            material += 1
            out = dest / n
            out.parent.mkdir(parents=True, exist_ok=True)
            if m.isdir():
                out.mkdir(parents=True, exist_ok=True)
                os.chmod(out, m.mode & 0o7777)
            elif m.isfile():
                src = tf.extractfile(m)
                if src is None:
                    raise ValueError(f"missing file body: {n}")
                with out.open("wb") as f:
                    shutil.copyfileobj(src, f)
                os.chmod(out, m.mode & 0o7777)
            elif m.issym() or m.islnk():
                target = m.linkname
                if os.path.isabs(target):
                    raise ValueError(f"absolute link target: {n} -> {target}")
                resolved = (out.parent / target).resolve(strict=False)
                root = dest.resolve()
                if resolved != root and root not in resolved.parents:
                    raise ValueError(f"escaping link target: {n} -> {target}")
                pending_links.append((out, target, m.islnk()))
            else:
                raise ValueError(f"unsupported archive member type: {n}")
    for out, target, hard in pending_links:
        if out.exists() or out.is_symlink():
            out.unlink()
        if hard:
            source = (out.parent / target).resolve()
            os.link(source, out)
        else:
            os.symlink(target, out)
    return {"material_member_count": material, "normalized_unique_count": len(seen)}


def verify_official_prefix(root: Path, control_dir: Path) -> dict[str, Any]:
    evidence = load(control_dir / "package-and-file-hashes.json")
    expected = {x["path"]: x for x in evidence["members"] if x["path"] == "prefix" or x["path"].startswith("prefix/")}
    errors: list[str] = []
    checked = 0
    for rel, row in expected.items():
        p = root / rel
        kind = row["type"]
        checked += 1
        if kind == "directory":
            if not p.is_dir() or p.is_symlink(): errors.append(f"type:{rel}")
        elif kind == "file":
            if not p.is_file() or p.is_symlink(): errors.append(f"type:{rel}")
            elif sha256(p) != row["sha256"]: errors.append(f"sha256:{rel}")
        elif kind == "symlink":
            if not p.is_symlink(): errors.append(f"type:{rel}")
            elif os.readlink(p) != row["linkname"]: errors.append(f"link:{rel}")
        else:
            errors.append(f"unexpected-authority-type:{rel}:{kind}")
    return {"pass": not errors, "checked": checked, "expected": len(expected), "errors": errors[:100]}


DYNAMIC_RE = re.compile(r"\((NEEDED|SONAME|RPATH|RUNPATH)\).*?\[(.*?)\]")


def elf_surface(path: Path, readelf: str) -> dict[str, Any]:
    h = run([readelf, "-hW", str(path)], timeout=60)
    l = run([readelf, "-lW", str(path)], timeout=60)
    d = run([readelf, "-dW", str(path)], timeout=60)
    if h.returncode or l.returncode or d.returncode:
        raise RuntimeError(f"readelf failed for {path}: {h.stderr}{l.stderr}{d.stderr}")
    typ = None; machine = None
    for line in h.stdout.splitlines():
        if line.strip().startswith("Type:"): typ = line.split(":",1)[1].strip()
        if line.strip().startswith("Machine:"): machine = line.split(":",1)[1].strip()
    tags: dict[str, list[str]] = {k: [] for k in ("NEEDED","SONAME","RPATH","RUNPATH")}
    for line in d.stdout.splitlines():
        m = DYNAMIC_RE.search(line)
        if m: tags[m.group(1)].append(m.group(2))
    aligns: list[int] = []
    for line in l.stdout.splitlines():
        s = line.strip()
        if s.startswith("LOAD "):
            tok = s.split()[-1]
            try: aligns.append(int(tok, 0))
            except ValueError: pass
    return {
        "sha256": sha256(path), "size": path.stat().st_size,
        "type": typ, "machine": machine, "needed": tags["NEEDED"],
        "soname": tags["SONAME"], "rpath": tags["RPATH"], "runpath": tags["RUNPATH"],
        "load_alignments": aligns,
    }


def is_elf(path: Path) -> bool:
    if not path.is_file() or path.is_symlink(): return False
    try:
        with path.open("rb") as f: return f.read(4) == b"\x7fELF"
    except OSError:
        return False


def relative_runpath(obj: Path, libdir: Path) -> str:
    rel = os.path.relpath(libdir, obj.parent)
    return "$ORIGIN" if rel == "." else "$ORIGIN/" + rel.replace(os.sep, "/")


def alignment_policy(before: list[int], after: list[int]) -> dict[str, Any]:
    """Accept added LOAD segments only when the 16 KiB contract is preserved.

    patchelf may add a PT_LOAD segment when the dynamic string table must grow.
    UT-2 requires preservation of the Android 16 KiB alignment contract, not an
    identical program-header count. Existing LOAD segments may not disappear,
    and every pre/post LOAD alignment must remain exactly 0x4000.
    """
    before_ok = bool(before) and all(x == 0x4000 for x in before)
    after_ok = bool(after) and all(x == 0x4000 for x in after)
    count_preserved = len(after) >= len(before)
    return {
        "before_load_count": len(before),
        "after_load_count": len(after),
        "before_all_16k": before_ok,
        "after_all_16k": after_ok,
        "load_count_not_reduced": count_preserved,
        "preserved": before_ok and after_ok and count_preserved,
    }


def patchelf_capabilities(patchelf: str) -> dict[str, Any]:
    p = run([patchelf, "--help"], timeout=60)
    text = (p.stdout or "") + "\n" + (p.stderr or "")
    return {
        "command": patchelf,
        "help_returncode": p.returncode,
        "page_size_supported": "--page-size" in text,
        "help_excerpt": [line for line in text.splitlines() if "page-size" in line][:5],
    }


def patchelf_set_runpath_command(patchelf: str, expected: str, path: Path) -> list[str]:
    return [patchelf, "--page-size", "16384", "--set-rpath", expected, str(path)]


def patch_objects(prefix: Path, mode: str, patchelf: str, readelf: str, native_extensions: set[str]) -> list[dict[str, Any]]:
    libdir = prefix / "lib"
    rows: list[dict[str, Any]] = []
    for p in sorted(prefix.rglob("*")):
        if not is_elf(p): continue
        rel = "prefix/" + p.relative_to(prefix).as_posix()
        mutate = mode == "lr3" or (mode == "lr2" and rel in native_extensions)
        before = elf_surface(p, readelf)
        expected = relative_runpath(p, libdir) if mutate else None
        mutation_command = None
        if mutate:
            mutation_command = patchelf_set_runpath_command(patchelf, expected, p)
            q = run(mutation_command, timeout=180)
            if q.returncode:
                raise RuntimeError(f"patchelf failed for {rel}: {q.stderr}")
        after = elf_surface(p, readelf)
        alignment = alignment_policy(before["load_alignments"], after["load_alignments"])
        alignment_preserved = alignment["preserved"]
        alignment_16k = alignment["after_all_16k"]
        exact = (
            before["type"] == after["type"] and before["machine"] == after["machine"]
            and before["needed"] == after["needed"] and before["soname"] == after["soname"]
            and before["rpath"] == after["rpath"]
            and (not mutate or after["runpath"] == [expected])
            and alignment_preserved and alignment_16k
        )
        rows.append({
            "path": rel, "mutated": mutate, "mutation": "set-dt-runpath" if mutate else "none",
            "mutation_command": mutation_command,
            "reason": "complete-per-object-relative-native-closure" if mode == "lr3" else ("direct-extension-provider-lookup" if mutate else "control-unmodified"),
            "expected_runpath": expected, "before": before, "after": after,
            "alignment_policy": alignment,
            "alignment_preserved": alignment_preserved, "alignment_16k_compatible": alignment_16k,
            "exact_mutation_check": exact,
        })
    return rows


def resolve_runpath_dirs(consumer: Path, runpaths: list[str]) -> set[Path]:
    out: set[Path] = set()
    for group in runpaths:
        for item in group.split(":"):
            if item == "$ORIGIN": out.add(consumer.parent.resolve())
            elif item.startswith("$ORIGIN/"): out.add((consumer.parent / item[len("$ORIGIN/"):]).resolve())
    return out


def closure_result(prefix: Path, rows: list[dict[str, Any]], provider_map: dict[str, Any]) -> dict[str, Any]:
    surface_by_rel = {r["path"]: r["after"] for r in rows}
    unresolved: list[dict[str, Any]] = []
    checked = 0
    for edge in provider_map["edges"]:
        if edge["provider"]["kind"] != "archive-member": continue
        checked += 1
        consumer_rel = edge["consumer"]
        surf = surface_by_rel.get(consumer_rel)
        if surf is None:
            unresolved.append({"consumer": consumer_rel, "needed": edge["needed"], "reason": "consumer-not-in-runtime"})
            continue
        consumer = prefix.parent / consumer_rel
        dirs = resolve_runpath_dirs(consumer, surf.get("runpath", []))
        providers = [prefix.parent / x for x in edge["provider"]["paths"]]
        if not any(p.parent.resolve() in dirs for p in providers):
            unresolved.append({
                "consumer": consumer_rel, "needed": edge["needed"],
                "provider_paths": edge["provider"]["paths"],
                "consumer_runpath": surf.get("runpath", []),
            })
    return {"checked_internal_edges": checked, "unresolved_internal_edges": len(unresolved), "unresolved": unresolved}


def split_runtime_paths(groups: list[str]) -> list[str]:
    return [item for group in groups for item in group.split(":") if item]


def classify_launcher_runpath(groups: list[str], desired: str, compiler_path: str) -> dict[str, Any]:
    entries = split_runtime_paths(groups)
    if entries.count(desired) != 1:
        raise ValueError(f"desired launcher RUNPATH missing or duplicated: {entries}")
    compiler = Path(compiler_path)
    if not compiler.is_absolute():
        compiler = (Path.cwd() / compiler).resolve(strict=False)
    # Termux clang's default config injects $PREFIX/bin/../../usr/lib, which
    # normalizes to $PREFIX/lib. Only this known toolchain path may accompany
    # the requested relative launcher RUNPATH before normalization.
    default_lib = os.path.normpath(str(compiler.parent / ".." / ".." / "usr" / "lib"))
    extras = [item for item in entries if item != desired]
    unexpected = [
        item for item in extras
        if not os.path.isabs(item) or os.path.normpath(item) != default_lib
    ]
    if unexpected:
        raise ValueError(f"unexpected launcher RUNPATH entries: {unexpected}; all={entries}")
    return {
        "entries": entries,
        "desired": desired,
        "compiler_path": str(compiler),
        "allowed_toolchain_default": default_lib,
        "toolchain_default_entries": extras,
        "requires_normalization": bool(extras),
    }


def normalize_launcher_runpath(binary: Path, desired: str, cc: str, patchelf: str, readelf: str) -> dict[str, Any]:
    compile_surface = elf_surface(binary, readelf)
    if compile_surface["rpath"]:
        raise RuntimeError(f"launcher contains unsupported DT_RPATH: {compile_surface['rpath']}")
    compiler_path = shutil.which(cc) or cc
    try:
        classification = classify_launcher_runpath(compile_surface["runpath"], desired, compiler_path)
    except ValueError as e:
        raise RuntimeError(str(e)) from e
    normalization_command: list[str] | None = None
    if classification["requires_normalization"]:
        normalization_command = patchelf_set_runpath_command(patchelf, desired, binary)
        q = run(normalization_command, timeout=180)
        if q.returncode:
            raise RuntimeError(f"launcher RUNPATH normalization failed: {q.stderr}")
    final_surface = elf_surface(binary, readelf)
    exact = (
        final_surface["runpath"] == [desired]
        and not final_surface["rpath"]
        and compile_surface["type"] == final_surface["type"]
        and compile_surface["machine"] == final_surface["machine"]
        and compile_surface["needed"] == final_surface["needed"]
        and compile_surface["soname"] == final_surface["soname"]
        and alignment_policy(compile_surface["load_alignments"], final_surface["load_alignments"])["preserved"]
    )
    if not exact:
        raise RuntimeError(
            "launcher RUNPATH normalization changed a protected ELF surface: "
            + json.dumps({"before": compile_surface, "after": final_surface}, sort_keys=True)
        )
    return {
        "action": "patchelf-set-runpath" if normalization_command else "none",
        "classification": classification,
        "command": normalization_command,
        "compile_surface": compile_surface,
        "surface": final_surface,
        "alignment_policy": alignment_policy(compile_surface["load_alignments"], final_surface["load_alignments"]),
        "exact_normalization_check": exact,
    }


def compile_launchers(source_dir: Path, prefix: Path, build: Path, cc: str, patchelf: str, readelf: str) -> dict[str, Any]:
    build.mkdir(parents=True, exist_ok=True)
    include = prefix / "include" / f"python{PYTHON_MM}"
    lib = prefix / "lib"
    variants = {
        "LA-0": "launcher_la0_pyconfig.c",
        "LA-1": "launcher_la1_bytesmain.c",
        "LA-2": "launcher_la2_programs_python.c",
        "LA-3": "launcher_la3_android_signal.c",
        "LR-0": "launcher_lr0_self_reexec.c",
    }
    result: dict[str, Any] = {}
    for name, src_name in variants.items():
        src = source_dir / src_name
        out = build / name.lower().replace("-", "_")
        desired_runpath = "$ORIGIN/../lib"
        cmd = [
            cc, "-fPIE", "-pie", "-O2", "-Wall", "-Wextra", "-pthread",
            "-Wl,-z,max-page-size=16384", "-Wl,-z,common-page-size=16384",
            f"-I{include}", str(src), f"-L{lib}", f"-lpython{PYTHON_MM}",
            "-ldl", "-lm", "-llog", "-Wl,--enable-new-dtags", f"-Wl,-rpath,{desired_runpath}", "-o", str(out),
        ]
        p = run(cmd, timeout=300)
        if p.returncode:
            raise RuntimeError(f"launcher compile failed {name}:\n{p.stdout}\n{p.stderr}")
        normalization = normalize_launcher_runpath(out, desired_runpath, cc, patchelf, readelf)
        result[name] = {
            "source": src_name,
            "source_sha256": sha256(src),
            "binary": str(out),
            "build_command": cmd,
            "runpath_normalization": normalization,
            "surface": normalization["surface"],
        }
    return result


def install_launcher(prefix: Path, launcher: Path) -> Path:
    b = prefix / "bin"
    b.mkdir(parents=True, exist_ok=True)
    target = b / "python3.14"
    shutil.copy2(launcher, target)
    os.chmod(target, 0o755)
    for name, link in (("python3", "python3.14"), ("python", "python3")):
        p = b / name
        if p.exists() or p.is_symlink(): p.unlink()
        p.symlink_to(link)
    return target


PROBE = r'''
import ctypes, importlib, json, os, subprocess, sys
mods=json.loads(os.environ.get("HW_T_EXTENSION_MODULES","[]"))
fail={}
for m in mods:
    try: importlib.import_module(m)
    except BaseException as e: fail[m]=type(e).__name__+":"+str(e)
prefix=os.environ.get("HW_T_EXPECTED_PREFIX","")
dl={}
for n in ("libcrypto_python.so","libssl_python.so","libsqlite3_python.so"):
    p=os.path.join(prefix,"lib",n)
    try: ctypes.CDLL(p); dl[n]="pass"
    except BaseException as e: dl[n]=type(e).__name__+":"+str(e)
for rel in ("lib/engines-3/afalg.so","lib/ossl-modules/legacy.so"):
    p=os.path.join(prefix,rel)
    try: ctypes.CDLL(p); dl[rel]="pass"
    except BaseException as e: dl[rel]=type(e).__name__+":"+str(e)
child_code='import json,os,ssl,sqlite3,_hashlib,sys; print(json.dumps({"executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix,"ld":os.environ.get("LD_LIBRARY_PATH")}))'
env=dict(os.environ); env.pop("LD_LIBRARY_PATH",None)
cp=subprocess.run([sys.executable,"-c",child_code],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
child={"rc":cp.returncode,"stdout":cp.stdout,"stderr":cp.stderr}
print(json.dumps({
 "executable":sys.executable,"base_executable":getattr(sys,"_base_executable",None),"prefix":sys.prefix,"base_prefix":sys.base_prefix,
 "path":sys.path,"ld_library_path":os.environ.get("LD_LIBRARY_PATH"),"self_reexec":os.environ.get("HW_T_LR0_SELF_REEXEC"),
 "extension_failures":fail,"extension_count":len(mods),"dlopen":dl,"child":child,
},sort_keys=True))
'''

GETPATH_PROBE = r'''
import json, os, sys
print(json.dumps({"executable":sys.executable,"base_executable":getattr(sys,"_base_executable",None),"prefix":sys.prefix,"base_prefix":sys.base_prefix,"path":sys.path,"argv0":sys.argv[0],"ld":os.environ.get("LD_LIBRARY_PATH")},sort_keys=True))
'''


def clean_env(prefix: Path, work: Path) -> dict[str, str]:
    env = dict(os.environ)
    for k in ("LD_LIBRARY_PATH","PYTHONHOME","PYTHONPATH","VIRTUAL_ENV","__PYVENV_LAUNCHER__","CPYTHON_HOME","HW_T_LR0_SELF_REEXEC"):
        env.pop(k, None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = str(work / "pycache")
    env["HW_T_EXPECTED_PREFIX"] = str(prefix)
    ca = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr")) / "etc/tls/cert.pem"
    if ca.is_file(): env["SSL_CERT_FILE"] = str(ca)
    return env


def parse_last_json(text: str) -> Any:
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line: continue
        try: return json.loads(line)
        except json.JSONDecodeError: pass
    return None


def execute_runtime_probe(binary: Path, prefix: Path, work: Path, modules: list[str], *, argv0: str | None = None, timeout: int = 240) -> dict[str, Any]:
    env = clean_env(prefix, work)
    env["HW_T_EXTENSION_MODULES"] = json.dumps(modules)
    if argv0 is None:
        cmd = [str(binary), "-c", PROBE]
    else:
        cmd = ["bash", "-c", 'exec -a "$1" "$2" -c "$3"', "--", argv0, str(binary), PROBE]
    p = run(cmd, env=env, timeout=timeout)
    data = parse_last_json(p.stdout)
    ext_fail = len(data.get("extension_failures", {})) if isinstance(data, dict) else None
    dl_pass = isinstance(data, dict) and all(v == "pass" for v in data.get("dlopen", {}).values())
    child_pass = isinstance(data, dict) and data.get("child", {}).get("rc") == 0 and parse_last_json(data.get("child", {}).get("stdout", "")) is not None
    return {
        "command": cmd, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
        "data": data, "startup_pass": p.returncode == 0 and isinstance(data, dict),
        "required_extension_failures": ext_fail, "dlopen_pass": dl_pass, "child_reentry_pass": child_pass,
        "ld_library_path_absent": isinstance(data, dict) and data.get("ld_library_path") is None,
        "self_reexec_absent": isinstance(data, dict) and data.get("self_reexec") is None,
    }


def executable_path_state(binary: Path) -> dict[str, Any]:
    lexists = os.path.lexists(binary)
    is_link = binary.is_symlink()
    target = None
    if is_link:
        try: target = os.readlink(binary)
        except OSError: target = None
    return {
        "path": str(binary),
        "lexists": lexists,
        "exists": binary.exists(),
        "is_symlink": is_link,
        "symlink_target": target,
        "resolved_target": str(binary.resolve(strict=False)),
    }


def execute_getpath(binary: Path, prefix: Path, work: Path, *, argv0: str | None = None, timeout: int = 120, record_exec_error: bool = False) -> dict[str, Any]:
    env = clean_env(prefix, work)
    if argv0 is None: cmd = [str(binary), "-c", GETPATH_PROBE]
    else: cmd = ["bash", "-c", 'exec -a "$1" "$2" -c "$3"', "--", argv0, str(binary), GETPATH_PROBE]
    before = executable_path_state(binary)
    try:
        p = run(cmd, env=env, timeout=timeout)
    except OSError as e:
        if not record_exec_error:
            raise
        return {
            "command": cmd, "returncode": None, "stdout": "", "stderr": "", "data": None, "pass": False,
            "path_state": before,
            "execution_error": {"type": type(e).__name__, "errno": e.errno, "message": str(e), "filename": getattr(e, "filename", None)},
        }
    data = parse_last_json(p.stdout)
    return {"command": cmd, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "data": data, "pass": p.returncode == 0 and isinstance(data, dict), "path_state": before}


def variant_pass(probe: dict[str, Any], closure: dict[str, Any], *, allow_reexec: bool = False) -> bool:
    return bool(
        probe["startup_pass"] and probe["required_extension_failures"] == 0 and probe["dlopen_pass"] and probe["child_reentry_pass"]
        and closure["unresolved_internal_edges"] == 0
        and (allow_reexec or (probe["ld_library_path_absent"] and probe["self_reexec_absent"]))
    )


def copy_prefix(src: Path, dst: Path) -> None:
    if dst.exists(): shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=True)


def venv_case(base_python: Path, prefix: Path, work: Path, path: Path, mode: str) -> dict[str, Any]:
    if path.exists(): shutil.rmtree(path)
    flag = "--symlinks" if mode == "symlinks" else "--copies"
    env = clean_env(prefix, work)
    p = run([str(base_python), "-m", "venv", "--without-pip", flag, str(path)], env=env, timeout=300)
    py = path / "bin" / "python"
    result = {"create_rc": p.returncode, "create_stdout": p.stdout, "create_stderr": p.stderr, "python": str(py), "mode": mode}
    if p.returncode == 0:
        result["run"] = execute_getpath(py, prefix, work)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--artifact-dir", type=Path, required=True)
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--source-dir", type=Path, required=True)
    ap.add_argument("--cc", default="clang")
    ap.add_argument("--patchelf", default="patchelf")
    ap.add_argument("--readelf", default="readelf")
    args = ap.parse_args()
    root=args.root.resolve(); archive=args.archive.resolve(); out=args.output_dir.resolve(); artifacts=args.artifact_dir.resolve(); work=args.work_dir.resolve(); source=args.source_dir.resolve()
    out.mkdir(parents=True, exist_ok=True); artifacts.mkdir(parents=True, exist_ok=True); work.mkdir(parents=True, exist_ok=True)
    if archive.stat().st_size != EXPECTED_ARCHIVE_SIZE or sha256(archive) != EXPECTED_ARCHIVE_SHA:
        raise SystemExit("official archive identity mismatch")
    control_dir=root/"experiments/epoch2-upstream-thin-control"
    artifact_dir=root/"experiments/epoch2-upstream-thin-artifact-prototype"
    if sha256(control_dir/"upstream-control-authority.json") != EXPECTED_CONTROL_SHA: raise SystemExit("UT-0 authority mismatch")
    if sha256(artifact_dir/"artifact-prototype-authority.json") != EXPECTED_ARTIFACT_SHA: raise SystemExit("UT-1 authority mismatch")

    extracted=work/"official"; shutil.rmtree(extracted,ignore_errors=True)
    extraction=safe_extract(archive,extracted)
    prefix_src=extracted/"prefix"
    verification=verify_official_prefix(extracted,control_dir)
    if not verification["pass"]: raise SystemExit("official extraction does not match UT-0 authority: "+json.dumps(verification["errors"][:10]))
    dump(out/"official-extraction-verification.json", {"schema_version":1,"archive_sha256":EXPECTED_ARCHIVE_SHA,"extraction":extraction,"prefix_verification":verification})

    inventory=load(control_dir/"elf-and-extension-inventory.json")
    provider_map=load(control_dir/"dependency-provider-map.json")
    native_extensions=set(inventory["native_extensions"])
    modules=sorted({Path(x).name.split(".cpython-")[0] for x in native_extensions})
    patchelf_caps=patchelf_capabilities(args.patchelf)
    if not patchelf_caps["page_size_supported"]:
        dump(out/"patchelf-capabilities.json", {"schema_version":1, **patchelf_caps})
        raise SystemExit("patchelf lacks required --page-size support: "+json.dumps(patchelf_caps,sort_keys=True))
    launchers=compile_launchers(source,prefix_src,work/"launchers",args.cc,args.patchelf,args.readelf)
    build_public={k:{kk:vv for kk,vv in v.items() if kk!="binary"} for k,v in launchers.items()}
    dump(out/"launcher-build-evidence.json", {"schema_version":1,"compiler":run([args.cc,"--version"]).stdout.splitlines()[:1],"patchelf_capabilities":patchelf_caps,"variants":build_public})

    loader_rows=[]; native_rows: dict[str,list[dict[str,Any]]]={}
    for code, mode, launcher_key in (("LR-0","lr0","LR-0"),("LR-1","lr1","LA-0"),("LR-2","lr2","LA-0"),("LR-3","lr3","LA-0")):
        prefix=work/"runtimes"/code.lower().replace("-","_")/"prefix"
        copy_prefix(prefix_src,prefix)
        binary=install_launcher(prefix,Path(launchers[launcher_key]["binary"]))
        rows=patch_objects(prefix,mode,args.patchelf,args.readelf,native_extensions) if mode in ("lr2","lr3") else patch_objects(prefix,"none",args.patchelf,args.readelf,native_extensions)
        closure=closure_result(prefix,rows,provider_map)
        probe=execute_runtime_probe(binary,prefix,work,modules)
        passed=variant_pass(probe,closure,allow_reexec=(code=="LR-0"))
        clean_pass=variant_pass(probe,closure,allow_reexec=False)
        loader_rows.append({"variant":code,"description":mode,"runtime_prefix":str(prefix),"closure":closure,"probe":probe,"control_pass":passed,"exit_candidate_pass":clean_pass})
        native_rows[code]=rows

    candidates=[x["variant"] for x in loader_rows if x["exit_candidate_pass"] and x["variant"] in ("LR-1","LR-2","LR-3")]
    if not candidates: raise SystemExit("no loader variant satisfies clean exit candidate")
    selected_loader=candidates[0]
    selected_prefix=work/"runtimes"/selected_loader.lower().replace("-","_")/"prefix"
    selected_rows=native_rows[selected_loader]

    launcher_rows=[]
    for code in ("LA-0","LA-1","LA-2","LA-3"):
        prefix=work/"launcher-runtimes"/code.lower().replace("-","_")/"prefix"
        copy_prefix(selected_prefix,prefix)
        binary=install_launcher(prefix,Path(launchers[code]["binary"]))
        probe=execute_runtime_probe(binary,prefix,work,modules)
        launcher_rows.append({"variant":code,"probe":probe,"pass":bool(probe["startup_pass"] and probe["required_extension_failures"]==0 and probe["dlopen_pass"] and probe["child_reentry_pass"] and probe["ld_library_path_absent"] and probe["self_reexec_absent"]),"binary_sha256":sha256(binary),"source":launchers[code]["source"]})
    by={x["variant"]:x for x in launcher_rows}
    selected_launcher=next((x for x in ("LA-2","LA-1","LA-0","LA-3") if by[x]["pass"]),None)
    if selected_launcher is None: raise SystemExit("no launcher variant passed")

    lr4=work/"runtimes"/"lr4"/"prefix"
    copy_prefix(selected_prefix,lr4)
    lr4_bin=install_launcher(lr4,Path(launchers[selected_launcher]["binary"]))
    lr4_probe=execute_runtime_probe(lr4_bin,lr4,work,modules)
    selected_closure=next(x["closure"] for x in loader_rows if x["variant"]==selected_loader)
    lr4_pass=variant_pass(lr4_probe,selected_closure,allow_reexec=False)
    if not lr4_pass: raise SystemExit("LR-4 selected candidate failed")

    # Discovery matrix at location A.
    matrix_root=work/"discovery"; shutil.rmtree(matrix_root,ignore_errors=True); matrix_root.mkdir(parents=True)
    a=matrix_root/"location-a"/"prefix"; copy_prefix(lr4,a); real=a/"bin/python3.14"
    rel_link=a/"bin/python-rel"; rel_link.symlink_to("python3.14")
    abs_link=a/"bin/python-abs"; abs_link.symlink_to(real)
    ext_dir=matrix_root/"external"; ext_dir.mkdir(); ext_link=ext_dir/"python"; ext_link.symlink_to(real)
    copied=ext_dir/"python-copy"; shutil.copy2(real,copied); os.chmod(copied,0o755)
    discovery={
        "direct_real_path": execute_getpath(real,a,work),
        "relative_in_tree_symlink": execute_getpath(rel_link,a,work),
        "absolute_in_tree_symlink": execute_getpath(abs_link,a,work),
        "external_symlink": execute_getpath(ext_link,a,work),
        "altered_argv0": execute_getpath(real,a,work,argv0="hw-t-altered-python"),
        "copied_executable_without_prefix": execute_getpath(copied,a,work),
    }
    pre_venv_symlink=venv_case(real,a,work,matrix_root/"venv-pre-move-symlink","symlinks")
    pre_venv_copy=venv_case(real,a,work,matrix_root/"venv-pre-move-copy","copies")
    discovery["venv_symlink_mode"] = pre_venv_symlink
    discovery["venv_copy_mode"] = pre_venv_copy

    # Whole-prefix move and post-move cases.
    a_parent=a.parent; b_parent=matrix_root/"location-b"; b_parent.mkdir(parents=True,exist_ok=True); b=b_parent/"prefix"
    probe_a=execute_runtime_probe(real,a,work,modules)
    shutil.move(str(a),str(b)); real_b=b/"bin/python3.14"
    probe_b=execute_runtime_probe(real_b,b,work,modules)
    discovery["runtime_moved_before_fresh_venv_creation"] = venv_case(real_b,b,work,matrix_root/"venv-post-move-fresh","symlinks")
    if "run" in pre_venv_symlink:
        discovery["pre_existing_venv_after_base_move"] = execute_getpath(Path(pre_venv_symlink["python"]),b,work,record_exec_error=True)
        discovery["pre_existing_venv_after_base_move"]["venv_mode"] = "symlinks"
    else:
        discovery["pre_existing_venv_after_base_move"] = {"pass":False,"reason":"pre-move-venv-creation-failed","venv_mode":"symlinks"}
    if "run" in pre_venv_copy:
        discovery["pre_existing_copy_venv_after_base_move"] = execute_getpath(Path(pre_venv_copy["python"]),b,work,record_exec_error=True)
        discovery["pre_existing_copy_venv_after_base_move"]["venv_mode"] = "copies"
    else:
        discovery["pre_existing_copy_venv_after_base_move"] = {"pass":False,"reason":"pre-move-copy-venv-creation-failed","venv_mode":"copies"}

    # Patch-level replacement at the same base path.
    repl_parent=matrix_root/"replacement"; repl=repl_parent/"prefix"; repl_parent.mkdir(parents=True,exist_ok=True); copy_prefix(lr4,repl)
    repl_py=repl/"bin/python3.14"; repl_venv=venv_case(repl_py,repl,work,matrix_root/"venv-replacement","symlinks")
    replacement_before=sha256(repl_py)
    old=repl_parent/"prefix.old"; repl.rename(old); copy_prefix(lr4,repl); shutil.rmtree(old)
    replacement_after=sha256(repl/"bin/python3.14")
    if "run" in repl_venv:
        repl_run=execute_getpath(Path(repl_venv["python"]),repl,work)
    else: repl_run={"pass":False,"reason":"venv-creation-failed"}
    discovery["patch_level_base_replacement"]={"before_launcher_sha256":replacement_before,"after_launcher_sha256":replacement_after,"run":repl_run}

    relocation={
        "location_a":probe_a,"location_b_after_whole_prefix_move":probe_b,
        "whole_prefix_relocation_pass":bool(probe_a["startup_pass"] and probe_b["startup_pass"] and probe_b["required_extension_failures"]==0 and probe_b["child_reentry_pass"] and probe_b["ld_library_path_absent"]),
        "subprocess_child_reentry_pass":bool(probe_b["child_reentry_pass"]),
    }

    api_command=["/system/bin/getprop","ro.build.version.sdk"] if Path("/system/bin/getprop").exists() else ["getprop","ro.build.version.sdk"]
    api_proc=run(api_command)
    api_text=api_proc.stdout.strip(); api=int(api_text) if api_text.isdigit() else None
    api_probe={"command":api_command,"returncode":api_proc.returncode,"stdout":api_proc.stdout,"stderr":api_proc.stderr,"parsed_android_api":api}
    uname=run(["uname","-a"]).stdout.strip()
    native_evidence={
        "schema_version":1,"selected_loader_variant":selected_loader,"selected_launcher_variant":selected_launcher,
        "patchelf_version":run([args.patchelf,"--version"]).stdout.strip(),"patchelf_capabilities":patchelf_caps,"readelf_version":run([args.readelf,"--version"]).stdout.splitlines()[:1],
        "device":{"android_api":api,"minimum_package_api":24,"api_compatible":api is not None and api>=24,"api_probe":api_probe,"uname":uname,"execution_context":"Termux app process in Android linker namespace"},
        "transformed_elf_count":sum(1 for r in selected_rows if r["mutated"]),
        "all_exact_mutations":all(r["exact_mutation_check"] for r in selected_rows),
        "all_alignment_preserved":all(r["alignment_preserved"] for r in selected_rows),
        "all_16k_compatible":all(r["alignment_16k_compatible"] for r in selected_rows),
        "alignment_policy":"Existing PT_LOAD count may grow but may not shrink; every pre/post PT_LOAD p_align must remain exactly 0x4000.",
        "objects":selected_rows,
        "bounded_bionic_checks":{
            "origin_direct_lookup":lr4_probe["startup_pass"],"transitive_extension_lookup":lr4_probe["required_extension_failures"]==0,
            "dlopen":lr4_probe["dlopen_pass"],"minimum_api":api is not None and api>=24,"modern_linker_namespace":lr4_probe["startup_pass"],
        },
    }

    exit_condition={
        "project_required_LD_LIBRARY_PATH_absent":lr4_probe["ld_library_path_absent"],
        "loader_bootstrap_self_reexec_absent":lr4_probe["self_reexec_absent"],
        "unresolved_internal_edges":selected_closure["unresolved_internal_edges"],
        "required_extension_failures":lr4_probe["required_extension_failures"],
        "whole_prefix_relocation_pass":relocation["whole_prefix_relocation_pass"],
        "subprocess_child_reentry_pass":relocation["subprocess_child_reentry_pass"],
    }
    gate_condition={
        "project_required_LD_LIBRARY_PATH_absent":exit_condition["project_required_LD_LIBRARY_PATH_absent"] is True,
        "loader_bootstrap_self_reexec_absent":exit_condition["loader_bootstrap_self_reexec_absent"] is True,
        "unresolved_internal_edges_zero":exit_condition["unresolved_internal_edges"]==0,
        "required_extension_failures_zero":exit_condition["required_extension_failures"]==0,
        "whole_prefix_relocation_pass":exit_condition["whole_prefix_relocation_pass"] is True,
        "subprocess_child_reentry_pass":exit_condition["subprocess_child_reentry_pass"] is True,
        "all_exact_mutations":native_evidence["all_exact_mutations"] is True,
        "all_alignment_preserved":native_evidence["all_alignment_preserved"] is True,
        "all_16k_compatible":native_evidence["all_16k_compatible"] is True,
        "android_api_compatible":native_evidence["device"]["api_compatible"] is True,
    }
    exit_pass=all(gate_condition.values())

    loader_matrix={"schema_version":1,"variants":loader_rows,"selected_input_variant":selected_loader,"lr4":{"selected_from":selected_loader,"launcher":selected_launcher,"probe":lr4_probe,"pass":lr4_pass},"exit_condition":exit_condition,"gate_condition":gate_condition,"pass":exit_pass}
    launcher_matrix={"schema_version":1,"variants":launcher_rows,"selection_order":["LA-2","LA-1","LA-0","LA-3"],"selected":selected_launcher,"programs_python_equivalence":"LA-2 is the POSIX Programs/python.c entry path; LA-1 is its minimal equivalent.","android_mandatory_initialization_selected":selected_launcher=="LA-3"}
    executable_matrix={"schema_version":1,"selected_loader":selected_loader,"selected_launcher":selected_launcher,"cases":discovery,"supported_boundary":{k:bool((v.get("run",v)).get("pass",False)) if isinstance(v,dict) else False for k,v in discovery.items()}}
    relocation_results={"schema_version":1,**relocation,"exit_condition":exit_condition,"gate_condition":gate_condition}
    dump(out/"loader-variant-matrix.json",loader_matrix)
    dump(out/"launcher-variant-matrix.json",launcher_matrix)
    dump(out/"executable-discovery-matrix.json",executable_matrix)
    dump(out/"native-loader-evidence.json",native_evidence)
    dump(out/"relocation-results.json",relocation_results)
    dump(out/"ut2-gate-diagnostics.json",{"schema_version":1,"pass":exit_pass,"exit_condition":exit_condition,"gate_condition":gate_condition,"failed_gate_conditions":[k for k,v in gate_condition.items() if not v]})
    shutil.copy2(lr4_bin,artifacts/"selected-launcher")
    os.chmod(artifacts/"selected-launcher",0o755)
    dump(artifacts/"selected-candidate.json",{"schema_version":1,"selected_loader":selected_loader,"selected_launcher":selected_launcher,"launcher_sha256":sha256(artifacts/"selected-launcher"),"exit_condition":exit_condition,"gate_condition":gate_condition,"product_selectable":False})
    if not exit_pass:
        raise SystemExit("UT-2 gate failed: "+json.dumps({"exit_condition":exit_condition,"gate_condition":gate_condition},sort_keys=True))
    print(json.dumps({"pass":True,"selected_loader":selected_loader,"selected_launcher":selected_launcher,"exit_condition":exit_condition,"gate_condition":gate_condition,"output_dir":str(out)},indent=2,sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

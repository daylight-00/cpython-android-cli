#!/usr/bin/env python3
"""Qualify the exact canonical install-only artifact on an exact Android API 24 AArch64 target."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))
from archive import sha256_file, write_json  # noqa: E402

FAMILY_RESULT_SHA = "c43975ec955f0d4f692567d728ded4200c1ea246574e2d514fbd44dca64ff3f7"
FAMILY_RESULT_SIZE = 87216775
DATA_RESULT_SHA = "6419154d3888ac1e3e5331b11b9692262ca2d90709389e20dfeb848f28507d1c"
DATA_RESULT_SIZE = 459042
INSTALL_NAME = "cpython-3.14.6+e3-full-r5-aarch64-linux-android-install_only.tar.gz"
INSTALL_SHA = "c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56"
CURRENT_DATA_NAME = "android-data-ca-2026.6.17-tzdata-2026.3-r1.tar.zst"
CURRENT_DATA_SHA = "e7dcdfa84f093d8bbdea50c80f25b9f20bddd8619199610405c4ba344790268d"
RELEASE_ID = "cpython-3.14.6+e3-r3-aarch64-linux-android"
RELEASE_SHA = "2c31578f95a11291eee1693db80048568a7b533e77877f36a8b1570241ce1e1c"
RELEASE_FINGERPRINT = "c8d76b6dcb934c12098efb2de985c5ab4799e4b5db5ae1c2b7c0f5a68438a82a"


def run(command: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None, timeout: int = 600) -> dict[str, Any]:
    try:
        p = subprocess.run(command, env=env, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": command, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as e:
        return {"command": command, "returncode": 124, "stdout": e.stdout or "", "stderr": e.stderr or "", "timed_out": True}
    except OSError as e:
        return {"command": command, "returncode": 127, "stdout": "", "stderr": f"{type(e).__name__}: {e}", "timed_out": False}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def safe_extract(tf: tarfile.TarFile, destination: Path, members: list[tarfile.TarInfo] | None = None) -> None:
    destination = destination.resolve()
    selected = members if members is not None else tf.getmembers()
    for member in selected:
        target = (destination / member.name).resolve()
        if target != destination and destination not in target.parents:
            raise ValueError(f"unsafe tar member: {member.name}")
    tf.extractall(destination, members=selected)


def extract_named_from_outer(archive: Path, suffix: str, destination: Path, zstd: str) -> Path:
    listing = subprocess.run(["tar", "--zstd", "-tf", str(archive)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if listing.returncode != 0:
        raise RuntimeError({"stage": "outer-list", "stderr": listing.stderr})
    matches = [line for line in listing.stdout.splitlines() if line.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError((suffix, matches))
    extract = subprocess.run(["tar", "--zstd", "-xOf", str(archive), matches[0]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if extract.returncode != 0:
        raise RuntimeError({"stage": "outer-extract", "stderr": extract.stderr.decode(errors="replace")})
    destination.write_bytes(extract.stdout)
    return destination


def zstd_decompress(source: Path, destination: Path, zstd: str) -> dict[str, Any]:
    row = run([zstd, "-q", "-d", "-f", str(source), "-o", str(destination)], timeout=600)
    if row["returncode"] != 0:
        raise RuntimeError(row)
    return row


def tree_digest(root: Path, *, include_mode: bool) -> str:
    h = hashlib.sha256()
    for p in sorted([root, *root.rglob("*")], key=lambda x: x.relative_to(root).as_posix() if x != root else ""):
        rel = "." if p == root else p.relative_to(root).as_posix()
        if p.is_symlink():
            kind = "l"; payload = os.readlink(p).encode()
        elif p.is_dir():
            kind = "d"; payload = b""
        elif p.is_file():
            kind = "f"; payload = p.read_bytes()
        else:
            continue
        h.update(kind.encode() + b"\0" + rel.encode() + b"\0")
        if include_mode:
            h.update(f"{stat.S_IMODE(p.lstat().st_mode):04o}".encode() + b"\0")
        h.update(hashlib.sha256(payload).digest())
    return h.hexdigest()


def make_uncompressed_install_tar(source_gz: Path, destination: Path) -> None:
    with gzip.open(source_gz, "rb") as src, destination.open("wb") as out:
        shutil.copyfileobj(src, out)


def make_uncompressed_data_tar(source_zst: Path, destination: Path, zstd: str) -> dict[str, Any]:
    return zstd_decompress(source_zst, destination, zstd)


def parse_json_stdout(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("returncode") != 0:
        return {}
    try:
        v = json.loads(row.get("stdout", "").strip())
    except json.JSONDecodeError:
        return {}
    return v if isinstance(v, dict) else {}


@dataclass
class Target:
    mode: str
    serial: str | None
    adb: str
    root: str

    def shell(self, command: str, *, timeout: int = 600) -> dict[str, Any]:
        if self.mode == "local":
            return run(["/system/bin/sh", "-c", command], timeout=timeout)
        assert self.serial
        return run([self.adb, "-s", self.serial, "shell", command], timeout=timeout)

    def push(self, source: Path, destination: str, *, timeout: int = 1200) -> dict[str, Any]:
        if self.mode == "local":
            try:
                Path(destination).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                return {"command": ["copy", str(source), destination], "returncode": 0, "stdout": "", "stderr": "", "timed_out": False}
            except OSError as e:
                return {"command": ["copy", str(source), destination], "returncode": 1, "stdout": "", "stderr": str(e), "timed_out": False}
        assert self.serial
        return run([self.adb, "-s", self.serial, "push", str(source), destination], timeout=timeout)

    def cleanup(self) -> dict[str, Any]:
        return self.shell(f"rm -rf {shlex.quote(self.root)}", timeout=300)


def discover_target(mode: str, adb: str, serial: str | None) -> tuple[Target | None, dict[str, Any]]:
    evidence: dict[str, Any] = {"requested_mode": mode, "requested_serial": serial}
    local_sdk = run(["/system/bin/getprop", "ro.build.version.sdk"]) if Path("/system/bin/getprop").exists() else {"returncode": 127, "stdout": "", "stderr": "missing", "command": []}
    local_abi = run(["/system/bin/getprop", "ro.product.cpu.abi"]) if Path("/system/bin/getprop").exists() else {"returncode": 127, "stdout": "", "stderr": "missing", "command": []}
    local_uname = run(["uname", "-m"])
    evidence["local"] = {"sdk": local_sdk, "abi": local_abi, "uname": local_uname}
    if mode in ("auto", "local") and local_sdk.get("stdout", "").strip() == "24" and local_uname.get("stdout", "").strip() in ("aarch64", "arm64"):
        return Target("local", None, adb, f"{os.environ.get('TMPDIR', '/data/local/tmp')}/hw-t-rb5-api24-{uuid.uuid4().hex[:10]}"), evidence
    if mode == "local":
        return None, evidence
    adb_path = shutil.which(adb) or (adb if Path(adb).exists() else None)
    if not adb_path:
        evidence["adb_error"] = "adb-not-found"
        return None, evidence
    devices = run([adb_path, "devices", "-l"])
    evidence["adb_devices"] = devices
    candidates: list[dict[str, Any]] = []
    listed: list[str] = []
    if devices["returncode"] == 0:
        for line in devices["stdout"].splitlines()[1:]:
            if not line.strip() or "\tdevice" not in line:
                continue
            s = line.split()[0]; listed.append(s)
    if serial:
        listed = [serial] if serial in listed else []
    for s in listed:
        sdk = run([adb_path, "-s", s, "shell", "getprop ro.build.version.sdk"])
        abi = run([adb_path, "-s", s, "shell", "getprop ro.product.cpu.abi"])
        abilist = run([adb_path, "-s", s, "shell", "getprop ro.product.cpu.abilist"])
        uname = run([adb_path, "-s", s, "shell", "uname -m"])
        row = {"serial": s, "sdk": sdk, "abi": abi, "abilist": abilist, "uname": uname}
        row["exact"] = sdk.get("stdout", "").strip() == "24" and (
            abi.get("stdout", "").strip() == "arm64-v8a" or "arm64-v8a" in abilist.get("stdout", "").strip().split(",") or uname.get("stdout", "").strip() in ("aarch64", "arm64")
        )
        candidates.append(row)
    evidence["adb_candidates"] = candidates
    exact = [x for x in candidates if x["exact"]]
    if len(exact) != 1:
        evidence["selection_error"] = f"expected-one-exact-api24-aarch64-target-observed-{len(exact)}"
        return None, evidence
    return Target("adb", exact[0]["serial"], adb_path, f"/data/local/tmp/hw-t-rb5-api24-{uuid.uuid4().hex[:10]}"), evidence


def q(value: str) -> str:
    return shlex.quote(value)


def target_env(prefix: str, data: str, state: str) -> str:
    values = {
        "ANDROID_DATA": "/data", "ANDROID_ROOT": "/system", "HOME": f"{state}/home", "TMPDIR": f"{state}/tmp",
        "PATH": f"{prefix}/bin:/system/bin:/system/xbin", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0", "PIP_DISABLE_PIP_VERSION_CHECK": "1", "SSL_CERT_FILE": f"{data}/ca/ca-bundle.pem",
        "TZPATH": f"{data}/zoneinfo",
    }
    return "/system/bin/env -i " + " ".join(f"{k}={q(v)}" for k, v in values.items())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family-result", required=True)
    ap.add_argument("--data-result", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--target-mode", choices=("auto", "local", "adb"), default="auto")
    ap.add_argument("--adb", default="adb")
    ap.add_argument("--serial")
    ap.add_argument("--zstd", default="zstd")
    ap.add_argument("--pkg-config", default="pkg-config")
    args = ap.parse_args()

    out = Path(args.output_dir).resolve(); family = Path(args.family_result).resolve(); data_result = Path(args.data_result).resolve()
    if out.exists(): shutil.rmtree(out)
    (out / "receipts").mkdir(parents=True); (out / "logs").mkdir(); (out / "evidence").mkdir()
    checks: dict[str, bool] = {}; errors: list[str] = []; evidence: dict[str, Any] = {}

    identity = {
        "family_result": {"path": str(family), "sha256": sha256_file(family), "size_bytes": family.stat().st_size},
        "data_result": {"path": str(data_result), "sha256": sha256_file(data_result), "size_bytes": data_result.stat().st_size},
    }
    checks["exact_family_result"] = identity["family_result"]["sha256"] == FAMILY_RESULT_SHA and identity["family_result"]["size_bytes"] == FAMILY_RESULT_SIZE
    checks["exact_data_result"] = identity["data_result"]["sha256"] == DATA_RESULT_SHA and identity["data_result"]["size_bytes"] == DATA_RESULT_SIZE
    write_json(out / "receipts/input-identity.json", {"schema_version": 1, "pass": checks["exact_family_result"] and checks["exact_data_result"], **identity})
    if not checks["exact_family_result"] or not checks["exact_data_result"]:
        errors.append("exact-input-identity-failed")

    target: Target | None = None
    with tempfile.TemporaryDirectory(prefix="rb5-api24-") as td:
        work = Path(td)
        try:
            install = extract_named_from_outer(family, f"target/candidate/{INSTALL_NAME}", work / INSTALL_NAME, args.zstd)
            current_data = extract_named_from_outer(data_result, f"target/artifacts/{CURRENT_DATA_NAME}", work / CURRENT_DATA_NAME, args.zstd)
            checks["exact_install_only"] = sha256_file(install) == INSTALL_SHA
            checks["exact_current_data"] = sha256_file(current_data) == CURRENT_DATA_SHA
            write_json(out / "receipts/artifact-identity.json", {
                "schema_version": 1, "pass": checks["exact_install_only"] and checks["exact_current_data"],
                "release_id": RELEASE_ID, "release_sha256": RELEASE_SHA, "release_fingerprint_sha256": RELEASE_FINGERPRINT,
                "install_only": {"filename": install.name, "sha256": sha256_file(install), "size_bytes": install.stat().st_size},
                "current_data": {"filename": current_data.name, "sha256": sha256_file(current_data), "size_bytes": current_data.stat().st_size},
            })

            install_tar = work / "install-only.tar"; make_uncompressed_install_tar(install, install_tar)
            data_tar = work / "data.tar"; evidence["data_decompress"] = make_uncompressed_data_tar(current_data, data_tar, args.zstd)
            local_extract = work / "local-extract"; local_extract.mkdir()
            with tarfile.open(install_tar, "r:") as tf: safe_extract(tf, local_extract)
            prefix_local = local_extract / "python"
            data_extract = work / "data-extract"; data_extract.mkdir()
            with tarfile.open(data_tar, "r:") as tf: safe_extract(tf, data_extract)
            data_local = data_extract / "data"
            modules = sorted(p.name.removesuffix(".cpython-314-aarch64-linux-android.so") for p in (prefix_local / "lib/python3.14/lib-dynload").glob("*.cpython-314-aarch64-linux-android.so"))
            checks["extension_inventory_67"] = len(modules) == 67
            before_content = tree_digest(prefix_local, include_mode=False); before_full = tree_digest(prefix_local, include_mode=True)

            pc_env = dict(os.environ); pc_env["PKG_CONFIG_PATH"] = pc_env["PKG_CONFIG_LIBDIR"] = str(prefix_local / "lib/pkgconfig")
            pkg_rows = {p: run([args.pkg_config, "--cflags", "--libs", p], env=pc_env) for p in ("python-3.14", "python-3.14-embed")}
            checks["pkg_config"] = all(r["returncode"] == 0 and str(prefix_local) in r["stdout"] and "/data/data/com.termux/files/usr" not in r["stdout"].replace(str(prefix_local), "<PREFIX>") for r in pkg_rows.values())
            evidence["pkg_config"] = pkg_rows

            target, target_discovery = discover_target(args.target_mode, args.adb, args.serial)
            evidence["target_discovery"] = target_discovery
            checks["exact_target_available"] = target is not None
            if target is None:
                raise RuntimeError("exact-api24-aarch64-target-not-found")

            root = target.root; runtime_a = f"{root}/runtime-a/prefix"; runtime_b = f"{root}/relocated/deep/path/prefix"; target_data = f"{root}/data"; state = f"{root}/state"
            setup = target.shell(f"rm -rf {q(root)} && mkdir -p {q(root)} {q(state+'/home')} {q(state+'/tmp')} {q(root+'/runtime-a')} {q(root+'/relocated/deep/path')}")
            evidence["target_setup"] = setup; checks["target_setup"] = setup["returncode"] == 0
            push_i = target.push(install_tar, f"{root}/install-only.tar"); push_d = target.push(data_tar, f"{root}/data.tar")
            evidence["push"] = {"install": push_i, "data": push_d}; checks["target_push"] = push_i["returncode"] == 0 and push_d["returncode"] == 0
            extract = target.shell(
                f"mkdir -p {q(root+'/install-extract')} {q(root+'/data-extract')} && "
                f"(toybox tar -xf {q(root+'/install-only.tar')} -C {q(root+'/install-extract')} || tar -xf {q(root+'/install-only.tar')} -C {q(root+'/install-extract')}) && "
                f"(toybox tar -xf {q(root+'/data.tar')} -C {q(root+'/data-extract')} || tar -xf {q(root+'/data.tar')} -C {q(root+'/data-extract')}) && "
                f"mv {q(root+'/install-extract/python')} {q(runtime_a)} && mv {q(root+'/data-extract/data')} {q(target_data)}"
            , timeout=1200)
            evidence["target_extract"] = extract; checks["target_extract"] = extract["returncode"] == 0

            ident_cmd = "printf '{\"sdk\":\"%s\",\"release\":\"%s\",\"abi\":\"%s\",\"abilist\":\"%s\",\"uname\":\"%s\",\"id\":\"%s\"}\\n' \"$(getprop ro.build.version.sdk)\" \"$(getprop ro.build.version.release)\" \"$(getprop ro.product.cpu.abi)\" \"$(getprop ro.product.cpu.abilist)\" \"$(uname -m)\" \"$(id)\""
            ident_row = target.shell(ident_cmd); ident = parse_json_stdout(ident_row); evidence["target_identity"] = {"command": ident_row, "data": ident}
            checks["target_api24"] = ident.get("sdk") == "24"
            checks["target_aarch64"] = ident.get("uname") in ("aarch64", "arm64") or ident.get("abi") == "arm64-v8a" or "arm64-v8a" in ident.get("abilist", "").split(",")

            probe_code = f'''import hashlib,importlib,json,os,stat,subprocess,sys,sysconfig\nfrom pathlib import Path\nfrom zoneinfo import ZoneInfo\nprefix=Path(sys.prefix); modules={modules!r}\nfail={{}}\nfor name in modules:\n try: importlib.import_module(name)\n except BaseException as e: fail[name]=type(e).__name__+":"+str(e)\nctx=__import__('ssl').create_default_context(); zones={{z:str(ZoneInfo(z)) for z in ('UTC','Asia/Seoul','America/New_York')}}\nchild_code="import json,os,sys;print(json.dumps({{'pass':True,'executable':sys.executable,'prefix':sys.prefix,'ld':os.environ.get('LD_LIBRARY_PATH')}}))"\nenv=dict(os.environ);env.pop('LD_LIBRARY_PATH',None)\nchild=subprocess.run([sys.executable,'-c',child_code],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)\ntry: child_data=json.loads(child.stdout.strip())\nexcept BaseException: child_data=None\ndef digest(root):\n h=hashlib.sha256()\n for p in sorted([root,*root.rglob('*')],key=lambda x:'.' if x==root else x.relative_to(root).as_posix()):\n  rel='.' if p==root else p.relative_to(root).as_posix()\n  if p.is_symlink(): kind='l'; payload=os.readlink(p).encode()\n  elif p.is_dir(): kind='d'; payload=b''\n  elif p.is_file(): kind='f'; payload=p.read_bytes()\n  else: continue\n  h.update(kind.encode()+b'\\0'+rel.encode()+b'\\0'+hashlib.sha256(payload).digest())\n return h.hexdigest()\nwrite_bits=[]\nfor p in [prefix,*prefix.rglob('*')]:\n if not p.is_symlink() and stat.S_IMODE(p.stat().st_mode)&0o222: write_bits.append(str(p))\npaths=sysconfig.get_paths(); within=lambda v:isinstance(v,str) and (v==str(prefix) or v.startswith(str(prefix)+os.sep))\nvars={{k:sysconfig.get_config_var(k) for k in ('ANDROID_API_LEVEL','HOST_GNU_TYPE','BUILD_GNU_TYPE','SOABI','prefix','exec_prefix','LIBDIR','LIBDEST','INCLUDEPY','DESTSHARED','LIBPL')}}\npath_ok=all(within(v) for v in paths.values()); var_ok=all(within(vars[k]) for k in ('prefix','exec_prefix','LIBDIR','LIBDEST','INCLUDEPY','DESTSHARED','LIBPL'))\nprint(json.dumps({{'pass':not fail and len(modules)==67 and child.returncode==0 and isinstance(child_data,dict) and child_data.get('pass') is True and child_data.get('ld') is None and path_ok and var_ok,'version':list(sys.version_info[:3]),'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix,'platform':sysconfig.get_platform(),'extension_count':len(modules),'extension_failures':fail,'child':{{'returncode':child.returncode,'data':child_data,'stderr':child.stderr}},'ca_count':len(ctx.get_ca_certs()),'zones':zones,'sysconfig':{{'paths':paths,'vars':vars,'paths_within_prefix':path_ok,'path_vars_within_prefix':var_ok}},'tree_content_sha256':digest(prefix),'write_bit_paths':write_bits,'page_size':os.sysconf('SC_PAGE_SIZE'),'ld_library_path':os.environ.get('LD_LIBRARY_PATH')}},sort_keys=True))\n'''
            probe_file = work / "probe.py"; probe_file.write_text(probe_code, encoding="utf-8")
            push_probe = target.push(probe_file, f"{root}/probe.py"); evidence["push_probe"] = push_probe; checks["probe_push"] = push_probe["returncode"] == 0

            def probe(prefix: str, label: str) -> dict[str, Any]:
                env_cmd = target_env(prefix, target_data, state)
                row = target.shell(f"mkdir -p {q(state+'/home')} {q(state+'/tmp')} && {env_cmd} {q(prefix+'/bin/python3.14')} {q(root+'/probe.py')}", timeout=900)
                parsed = parse_json_stdout(row); evidence[label] = {"command": row, "data": parsed}; return parsed

            p_a = probe(runtime_a, "runtime_location_a"); checks["startup_location_a"] = p_a.get("pass") is True
            relocate = target.shell(f"mv {q(runtime_a)} {q(runtime_b)}"); evidence["relocation"] = relocate; checks["relocation_move"] = relocate["returncode"] == 0
            p_b = probe(runtime_b, "runtime_location_b"); checks["startup_and_relocation"] = p_b.get("pass") is True
            checks["native_extensions"] = p_b.get("extension_count") == 67 and p_b.get("extension_failures") == {}
            checks["subprocess_reentry"] = (p_b.get("child") or {}).get("data", {}).get("pass") is True
            checks["runtime_data"] = p_b.get("ca_count", 0) > 0 and set((p_b.get("zones") or {})) == {"UTC", "Asia/Seoul", "America/New_York"}
            checks["sysconfig_api24"] = (p_b.get("sysconfig") or {}).get("vars", {}).get("ANDROID_API_LEVEL") in (24, "24") and p_b.get("platform") == "android-24-arm64_v8a"

            env_b = target_env(runtime_b, target_data, state)
            aliases = {n: target.shell(f"{env_b} {q(runtime_b+'/bin/'+n)} -c \"import json,sys;print(json.dumps({{'pass':True,'executable':sys.executable}}))\"") for n in ("python", "python3", "python3.14")}
            evidence["python_aliases"] = aliases; checks["python_aliases"] = all(r["returncode"] == 0 and parse_json_stdout(r).get("pass") is True for r in aliases.values())
            pip_rows = {
                "version": target.shell(f"{env_b} {q(runtime_b+'/bin/python3.14')} -m pip --version", timeout=300),
                "list": target.shell(f"{env_b} {q(runtime_b+'/bin/python3.14')} -m pip list --format=json --disable-pip-version-check", timeout=600),
                "console": target.shell(f"{env_b} {q(runtime_b+'/bin/pip3.14')} --version", timeout=300),
            }
            evidence["pip"] = pip_rows
            try: pip_list = json.loads(pip_rows["list"]["stdout"].strip())
            except json.JSONDecodeError: pip_list = None
            checks["bounded_pip"] = pip_rows["version"]["returncode"] == 0 and pip_rows["list"]["returncode"] == 0 and isinstance(pip_list, list) and pip_rows["console"]["returncode"] == 0

            venv_path = f"{state}/venvs/fresh"
            v_create = target.shell(f"{env_b} {q(runtime_b+'/bin/python3.14')} -m venv --without-pip --symlinks {q(venv_path)}", timeout=600)
            v_probe = target.shell(f"{env_b} {q(venv_path+'/bin/python')} -c \"import json,sys;print(json.dumps({{'pass':sys.prefix!=sys.base_prefix,'prefix':sys.prefix,'base_prefix':sys.base_prefix}}))\"", timeout=300)
            evidence["venv"] = {"create": v_create, "probe": v_probe}; checks["venv"] = v_create["returncode"] == 0 and parse_json_stdout(v_probe).get("pass") is True

            cfg_rows = {o: target.shell(f"{env_b} {q(runtime_b+'/bin/python3.14-config')} {q(o)}", timeout=300) for o in ("--prefix", "--exec-prefix", "--includes", "--cflags", "--libs", "--ldflags", "--extension-suffix", "--configdir")}
            evidence["python_config"] = cfg_rows; checks["python_config"] = all(r["returncode"] == 0 and "/data/data/com.termux/files/usr" not in (r["stdout"] + r["stderr"]).replace(runtime_b, "<PREFIX>") for r in cfg_rows.values())

            before_ro = p_b.get("tree_content_sha256")
            chmod = target.shell(f"chmod -R a-w {q(runtime_b)}"); evidence["read_only_chmod"] = chmod
            p_ro = probe(runtime_b, "read_only_runtime")
            checks["read_only_execution"] = chmod["returncode"] == 0 and p_ro.get("pass") is True and p_ro.get("write_bit_paths") == []
            checks["target_tree_content_invariance"] = before_ro and p_ro.get("tree_content_sha256") == before_ro

            after_content = tree_digest(prefix_local, include_mode=False); after_full = tree_digest(prefix_local, include_mode=True)
            checks["frozen_family_invariance"] = before_content == after_content and before_full == after_full and sha256_file(install) == INSTALL_SHA and sha256_file(family) == FAMILY_RESULT_SHA
            evidence["frozen_invariance"] = {"before_content": before_content, "after_content": after_content, "before_full": before_full, "after_full": after_full}
        except Exception as e:  # noqa: BLE001
            errors.append(f"{type(e).__name__}: {e}")
        finally:
            if target is not None:
                evidence["target_cleanup"] = target.cleanup()

    failed = sorted(k for k, v in checks.items() if v is not True)
    result = {
        "schema_version": 1, "result_kind": "epoch3-rb5-api24-runtime-candidate", "pass": not failed and not errors,
        "checks": dict(sorted(checks.items())), "failed_checks": failed, "errors": errors,
        "release": {"release_id": RELEASE_ID, "release_sha256": RELEASE_SHA, "family_fingerprint_sha256": RELEASE_FINGERPRINT, "install_only_sha256": INSTALL_SHA},
        "target": {"mode": target.mode if target else None, "serial": target.serial if target else None, "required_android_api": 24, "architecture": "aarch64"},
        "evidence": evidence,
        "claim_boundary": {"api24_runtime_started": True, "api24_runtime_candidate": not failed and not errors, "api24_runtime_accepted": False, "rb5_closed": False, "actual_16k_runtime_qualified": False, "non_termux_android_context_qualified": False, "selectable": False, "publication": False, "artifact_bytes_changed": False},
    }
    write_json(out / "result.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

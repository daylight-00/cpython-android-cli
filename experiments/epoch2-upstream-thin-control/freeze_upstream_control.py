#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
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
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

OUT_FILES = {
    "gate-contract": "gate-contract.json",
    "upstream-input-manifest": "upstream-input-manifest.json",
    "package-and-file-hashes": "package-and-file-hashes.json",
    "elf-and-extension-inventory": "elf-and-extension-inventory.json",
    "dependency-provider-map": "dependency-provider-map.json",
    "sysconfig-census": "sysconfig-census.json",
    "package-layout-map": "package-layout-map.json",
    "provenance-map": "provenance-map.json",
    "producer-delta": "producer-delta.json",
}
SYSTEM_SONAMES = {
    "libandroid.so", "libc.so", "libdl.so", "liblog.so", "libm.so", "libz.so", "libpthread.so", "librt.so", "libresolv.so", "libgcc.so",
    "libEGL.so", "libGLESv2.so", "libGLESv3.so", "libOpenSLES.so", "libjnigraphics.so",
    "libmediandk.so", "libnativewindow.so", "libvulkan.so", "libaaudio.so", "libcamera2ndk.so",
}
TEXT_SUFFIXES = {".txt", ".md", ".rst", ".json", ".py", ".h", ".pc", ".cfg", ".ini", ".cmake"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha(obj: Any) -> str:
    b = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(b).hexdigest()


def dump(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def safe_name(name: str) -> str:
    if not name or "\x00" in name or name.startswith("/"):
        raise ValueError(f"unsafe archive member: {name!r}")
    n = posixpath.normpath(name)
    if n == ".":
        return n
    if n == ".." or n.startswith("../"):
        raise ValueError(f"unsafe archive member: {name!r}")
    return n


def safe_link(member_name: str, linkname: str) -> str:
    if not linkname or linkname.startswith("/") or "\x00" in linkname:
        raise ValueError(f"unsafe link target: {member_name!r} -> {linkname!r}")
    base = posixpath.dirname(member_name)
    target = posixpath.normpath(posixpath.join(base, linkname))
    if target == ".." or target.startswith("../"):
        raise ValueError(f"escaping link target: {member_name!r} -> {linkname!r}")
    return target


def safe_hardlink(linkname: str) -> str:
    if not linkname or linkname.startswith("/") or "\x00" in linkname:
        raise ValueError(f"unsafe hardlink target: {linkname!r}")
    target = posixpath.normpath(linkname)
    if target in {".", ".."} or target.startswith("../"):
        raise ValueError(f"escaping hardlink target: {linkname!r}")
    return target


def member_kind(m: tarfile.TarInfo) -> str:
    if m.isfile(): return "file"
    if m.isdir(): return "directory"
    if m.issym(): return "symlink"
    if m.islnk(): return "hardlink"
    return "unsupported"


def inventory_and_extract(archive: Path, dest: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    names: set[str] = set()
    hardlinks: list[tuple[tarfile.TarInfo, str]] = []
    errors: list[str] = []
    with tarfile.open(archive, "r:gz") as tf:
        members = tf.getmembers()
        for m in members:
            name = safe_name(m.name)
            if name == ".":
                if not m.isdir(): raise ValueError("archive root member is not a directory")
                continue
            if name in names:
                raise ValueError(f"duplicate archive member: {name}")
            names.add(name)
            kind = member_kind(m)
            if kind == "unsupported":
                raise ValueError(f"unsupported archive member type: {name}")
            link_target = None
            if kind == "symlink":
                link_target = safe_link(name, m.linkname)
            elif kind == "hardlink":
                link_target = safe_hardlink(m.linkname)
            rec: dict[str, Any] = {
                "path": name,
                "type": kind,
                "mode": oct(m.mode & 0o7777),
                "uid": m.uid,
                "gid": m.gid,
                "mtime": m.mtime,
                "size": m.size,
                "linkname": m.linkname or None,
                "sha256": None,
            }
            out = dest / name
            if kind == "directory":
                out.mkdir(parents=True, exist_ok=True)
            elif kind == "file":
                out.parent.mkdir(parents=True, exist_ok=True)
                src = tf.extractfile(m)
                if src is None:
                    raise ValueError(f"cannot read archive member: {name}")
                h = hashlib.sha256()
                with out.open("wb") as f:
                    for chunk in iter(lambda: src.read(1024 * 1024), b""):
                        h.update(chunk); f.write(chunk)
                os.chmod(out, m.mode & 0o777)
                rec["sha256"] = h.hexdigest()
            elif kind == "symlink":
                out.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(m.linkname, out)
            else:
                hardlinks.append((m, name))
            records.append(rec)
        by_path = {r["path"]: r for r in records}
        for m, name in hardlinks:
            target = safe_hardlink(m.linkname)
            src = dest / target
            out = dest / name
            if not src.is_file():
                raise ValueError(f"hardlink target missing: {name} -> {target}")
            out.parent.mkdir(parents=True, exist_ok=True)
            os.link(src, out)
            by_path[name]["sha256"] = sha256_file(out)
    for r in records:
        p = dest / r["path"]
        if r["type"] == "file" and sha256_file(p) != r["sha256"]:
            errors.append(r["path"])
    return records, errors


def run_text(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout


def parse_readelf(path: Path, rel: str) -> dict[str, Any]:
    result: dict[str, Any] = {"path": rel, "sha256": sha256_file(path)}
    rc, hdr = run_text(["readelf", "-W", "-h", str(path)])
    result["readelf_header_rc"] = rc
    fields = {}
    for line in hdr.splitlines():
        m = re.match(r"\s*([^:]+):\s*(.*)$", line)
        if m: fields[m.group(1).strip().lower().replace(" ", "_")] = m.group(2).strip()
    result.update({
        "elf_class": fields.get("class"), "data": fields.get("data"),
        "osabi": fields.get("os/abi"), "type": fields.get("type"),
        "machine": fields.get("machine"), "entry_point": fields.get("entry_point_address"),
    })
    rc, dyn = run_text(["readelf", "-W", "-d", str(path)])
    needed = re.findall(r"\(NEEDED\).*?\[(.*?)\]", dyn)
    soname = re.findall(r"\(SONAME\).*?\[(.*?)\]", dyn)
    rpath = re.findall(r"\(RPATH\).*?\[(.*?)\]", dyn)
    runpath = re.findall(r"\(RUNPATH\).*?\[(.*?)\]", dyn)
    result.update({"readelf_dynamic_rc": rc, "needed": sorted(set(needed)), "soname": soname[0] if soname else None,
                   "rpath": rpath[0] if rpath else None, "runpath": runpath[0] if runpath else None})
    rc, notes = run_text(["readelf", "-W", "-n", str(path)])
    build_ids = re.findall(r"Build ID:\s*([0-9a-fA-F]+)", notes)
    api_candidates = []
    for pat in [r"Android[^\n]*?ABI[^\n]*?(\d+)", r"NT_VERSION[^\n]*?(\d+)", r"Android[^\n]*?api[^\n]*?(\d+)"]:
        api_candidates += [int(x) for x in re.findall(pat, notes, re.I)]
    result.update({"readelf_notes_rc": rc, "build_id": build_ids[0].lower() if build_ids else None,
                   "android_api_candidates": sorted(set(api_candidates))})
    rc, ph = run_text(["readelf", "-W", "-l", str(path)])
    interp = re.findall(r"Requesting program interpreter:\s*([^\]]+)\]", ph)
    result.update({"readelf_program_headers_rc": rc, "interpreter": interp[0] if interp else None})
    return result


def ast_build_vars(path: Path) -> dict[str, Any]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "build_time_vars" for t in node.targets):
                value = ast.literal_eval(node.value)
                return value if isinstance(value, dict) else {}
    except Exception:
        pass
    return {}


def text_candidates(root: Path, records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    apis: list[dict[str, Any]] = []
    urls: list[dict[str, Any]] = []
    pats = [
        ("android-api-assignment", re.compile(r"(?:ANDROID_API_LEVEL|android_api_level|__ANDROID_API__)\D{0,12}(\d{2})", re.I)),
        ("compiler-target", re.compile(r"(?:aarch64|x86_64)-linux-android(\d{2})", re.I)),
        ("android-platform", re.compile(r"android[-_](\d{2})", re.I)),
    ]
    url_re = re.compile(r"https?://[^\s\"'<>]+")
    for rec in records:
        if rec["type"] != "file" or rec["size"] > 2_000_000:
            continue
        p = root / rec["path"]
        if p.suffix.lower() not in TEXT_SUFFIXES and p.name not in {"Makefile", "LICENSE", "README"}:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for kind, pat in pats:
            for m in pat.finditer(text):
                n = int(m.group(1))
                if 16 <= n <= 99: apis.append({"value": n, "source": rec["path"], "kind": kind})
        for u in sorted(set(url_re.findall(text))):
            urls.append({"url": u.rstrip(".,);]"), "source": rec["path"]})
    return apis, urls


def classify_packaged_elf(soname: str, paths: list[str], extensions: list[str]) -> str:
    base = PurePosixPath(paths[0]).name
    if soname.startswith("libpython") or base.startswith("libpython") or base.startswith("python") or any(p.startswith("prefix/bin/python") for p in paths):
        return "cpython-runtime"
    if "_python.so" in soname or "_python.so" in base:
        return "beeware-inherited-dependency"
    if any(p.startswith("prefix/lib/engines-3/") or p.startswith("prefix/lib/ossl-modules/") for p in paths):
        return "beeware-inherited-openssl-component"
    if soname == "libc++_shared.so" or base == "libc++_shared.so":
        return "android-ndk-runtime"
    if any(p in extensions for p in paths):
        return "cpython-extension"
    return "packaged-elf-unclassified"

def version_strings(path: Path) -> list[str]:
    rc, out = run_text(["strings", "-a", str(path)])
    if rc != 0: return []
    patterns = [r"OpenSSL\s+\d+\.\d+\.\d+[^\n]*", r"SQLite\s+\d+\.\d+\.\d+[^\n]*",
                r"\b3\.\d{1,2}\.\d{1,2}\b", r"\b1\.0\.\d+\b", r"libffi[^\n]{0,40}\d+\.\d+\.\d+"]
    vals: set[str] = set()
    for pat in patterns:
        vals.update(x.strip()[:160] for x in re.findall(pat, out, re.I))
    return sorted(vals)[:20]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--archive", required=True)
    ap.add_argument("--sigstore")
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--package-url", required=True)
    ap.add_argument("--release-page-url", required=True)
    ap.add_argument("--source-url", required=True)
    ap.add_argument("--source-sha256", required=True)
    ap.add_argument("--producer-authority", default="experiments/epoch2-termux-native-cpython3146-producer/producer-authority.json")
    ap.add_argument("--output-dir", default="experiments/epoch2-upstream-thin-control")
    ap.add_argument("--predecessor-head", required=True)
    ap.add_argument("--predecessor-tree", required=True)
    x = ap.parse_args()
    repo = Path(x.root).resolve(); archive = Path(x.archive).resolve(); out = repo / x.output_dir
    out.mkdir(parents=True, exist_ok=True)
    actual_sha = sha256_file(archive)
    if actual_sha != x.expected_sha256:
        raise SystemExit(f"archive sha256 mismatch: {actual_sha}")
    if shutil.which("readelf") is None or shutil.which("strings") is None:
        raise SystemExit("readelf and strings are required")
    producer = json.loads((repo / x.producer_authority).read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="ut0-extract-") as td:
        extracted = Path(td) / "root"; extracted.mkdir()
        records, extraction_errors = inventory_and_extract(archive, extracted)
        top = Counter(PurePosixPath(r["path"]).parts[0] for r in records if PurePosixPath(r["path"]).parts)
        prefix_records = [r for r in records if r["path"] == "prefix" or r["path"].startswith("prefix/")]
        prefix_snapshot = canonical_sha([{k:r[k] for k in ("path","type","mode","size","linkname","sha256")} for r in prefix_records])

        build_details_paths = [r["path"] for r in records if r["type"] == "file" and PurePosixPath(r["path"]).name == "build-details.json"]
        build_details = []
        for p in build_details_paths:
            try: build_details.append({"path": p, "data": json.loads((extracted / p).read_text(encoding="utf-8"))})
            except Exception as e: build_details.append({"path": p, "error": str(e)})
        sys_paths = [r["path"] for r in records if r["type"] == "file" and PurePosixPath(r["path"]).name.startswith("_sysconfigdata") and r["path"].endswith(".py")]
        sys_items = []
        all_vars: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for p in sys_paths:
            vars_ = ast_build_vars(extracted / p)
            sys_items.append({"path": p, "variable_count": len(vars_), "build_time_vars_sha256": canonical_sha(vars_)})
            for k, v in vars_.items(): all_vars[k].append({"path": p, "value": v})
        selected_keys = ["ANDROID_API_LEVEL","HOST_GNU_TYPE","BUILD_GNU_TYPE","MULTIARCH","SOABI","EXT_SUFFIX","SHLIB_SUFFIX","ABIFLAGS","Py_ENABLE_SHARED","CONFIG_ARGS","CC","CFLAGS","LDFLAGS","prefix","exec_prefix"]
        selected_vars = {k: all_vars[k] for k in selected_keys if k in all_vars}
        api_text, discovered_urls = text_candidates(extracted, records)

        elf_records = []
        for r in records:
            if r["type"] != "file" or r["size"] < 4: continue
            p = extracted / r["path"]
            with p.open("rb") as f: magic = f.read(4)
            if magic == b"\x7fELF": elf_records.append(parse_readelf(p, r["path"]))
        for e in elf_records:
            for v in e["android_api_candidates"]: api_text.append({"value": v, "source": e["path"], "kind": "elf-note"})

        direct_api = []
        for k in ["ANDROID_API_LEVEL"]:
            for item in selected_vars.get(k, []):
                try: direct_api.append(int(item["value"]))
                except Exception: pass
        for bd in build_details:
            data = bd.get("data", {})
            blob = json.dumps(data, sort_keys=True)
            for m in re.finditer(r"(?:android|api)[^0-9]{0,10}(\d{2})", blob, re.I):
                v=int(m.group(1))
                if 16 <= v <= 99: api_text.append({"value":v,"source":bd["path"],"kind":"build-details"})
        authoritative_api = list(direct_api) + [int(a["value"]) for a in api_text if a.get("kind") in {"elf-note", "build-details"} or a.get("source") in sys_paths]
        api_values = sorted(set(authoritative_api))
        minimum_api = max(api_values) if api_values else None

        version = None; platform = None; ext_suffix = None; multiarch = None
        if build_details:
            d = build_details[0].get("data", {})
            vi = d.get("language", {}).get("version_info", {})
            if not vi:
                candidate = d.get("implementation", {}).get("version", {})
                vi = candidate if isinstance(candidate, dict) else {}
            if all(vi.get(k) is not None for k in ("major", "minor", "micro")):
                version = f"{vi['major']}.{vi['minor']}.{vi['micro']}"
            platform = d.get("platform")
            ext_suffix = d.get("abi", {}).get("extension_suffix")
            multiarch = d.get("implementation", {}).get("_multiarch")
        if not version:
            m = re.search(r"python-(\d+\.\d+\.\d+)-", archive.name); version = m.group(1) if m else None
        target_candidates = []
        for k in ["HOST_GNU_TYPE","MULTIARCH"]:
            for item in selected_vars.get(k, []): target_candidates.append(str(item["value"]))
        target_candidates += [x for x in [multiarch, platform] if x]
        target = next((t for t in target_candidates if "aarch64" in t and "android" in t), None)
        target = "aarch64-linux-android" if target and "aarch64" in target else target

        extensions = []
        for e in elf_records:
            name = PurePosixPath(e["path"]).name
            is_ext = ("/lib-dynload/" in f"/{e['path']}" or ".cpython-" in name or ".abi3.so" in name)
            if is_ext: extensions.append(e["path"])

        providers: dict[str, list[str]] = defaultdict(list)
        for e in elf_records:
            key = e.get("soname") or PurePosixPath(e["path"]).name
            providers[key].append(e["path"])
        dependency_edges=[]; unresolved=[]
        for e in elf_records:
            for need in e["needed"]:
                if need in providers:
                    provider={"kind":"archive-member","paths":providers[need]}
                elif need in SYSTEM_SONAMES:
                    provider={"kind":"android-system","paths":[]}
                else:
                    provider={"kind":"unresolved","paths":[]}; unresolved.append({"consumer":e["path"],"needed":need})
                dependency_edges.append({"consumer":e["path"],"needed":need,"provider":provider})

        dependency_products=[]; unclassified=[]
        for soname, paths in sorted(providers.items()):
            cls=classify_packaged_elf(soname, paths, extensions)
            if cls == "packaged-elf-unclassified":
                unclassified.append({"soname":soname,"paths":paths})
            versions=[]
            if cls.startswith("beeware-inherited-"):
                versions=version_strings(extracted / paths[0])
            dependency_products.append({"soname":soname,"paths":paths,"classification":cls,"version_string_candidates":versions})

        license_paths = sorted(r["path"] for r in records if r["type"]=="file" and re.search(r"(^|/)(LICENSE|LICENCE|COPYING|NOTICE)(\.|$)", r["path"], re.I))
        metadata_paths = sorted(r["path"] for r in records if r["type"]=="file" and (PurePosixPath(r["path"]).name in {"README.md","README.rst","build-details.json","pyconfig.h","Makefile"} or r["path"].endswith(".pc") or "_sysconfigdata" in r["path"]))

        package_hashes = {
            "schema_version":1,"evidence_kind":"package-and-file-hashes","package_sha256":actual_sha,
            "archive_member_count":len(records),"regular_file_count":sum(r["type"]=="file" for r in records),
            "archive_member_manifest_sha256":canonical_sha(records),"prefix_snapshot_sha256":prefix_snapshot,
            "extraction_byte_mismatch_paths":extraction_errors,"members":records,
        }
        gate = {
            "schema_version":1,"gate_id":"E2-R1/UT-0","work_class":"L","status":"executed",
            "question":"What exactly exists in the unmodified official Python.org Android package and its inherited BeeWare dependency set?",
            "required_roles":list(OUT_FILES)+["independent-audit","machine-authority","evidence-freeze"],
            "claim_boundary":{"official_upstream_identity":True,"archive_mutation":False,"android_runtime":False,"device_qualification":False,"product_selection":False,"publication":False},
            "predecessor":{"commit":x.predecessor_head,"tree":x.predecessor_tree},
        }
        input_manifest = {
            "schema_version":1,"evidence_kind":"upstream-input-manifest","product":"CPython Android embeddable package",
            "version":version,"architecture":"aarch64","target":target,"minimum_android_api":minimum_api,
            "filename":archive.name,"size":archive.stat().st_size,"sha256":actual_sha,"expected_sha256":x.expected_sha256,
            "package_url":x.package_url,"release_page_url":x.release_page_url,"release_date":"2026-06-10",
            "sigstore":{"path":Path(x.sigstore).name if x.sigstore else None,"sha256":sha256_file(Path(x.sigstore)) if x.sigstore else None,"verified_identity":False,"role":"upstream verification material captured; release-page SHA-256 is the byte acceptance authority"},
            "source_release":{"url":x.source_url,"sha256":x.source_sha256,"tag":"v3.14.6"},
            "acquisition":{"method":"bounded-owner-run-https","drive_search_result":"exact archive absent"},
            "identity_checks":{"checksum_match":actual_sha==x.expected_sha256,"version_match":version=="3.14.6","target_match":target=="aarch64-linux-android","minimum_api_identified":minimum_api is not None,"build_details_present":bool(build_details_paths),"prefix_present":bool(prefix_records)},
        }
        elf_inv = {
            "schema_version":1,"evidence_kind":"elf-and-extension-inventory","elf_count":len(elf_records),
            "native_extension_count":len(extensions),"native_extensions":sorted(extensions),"elf_objects":elf_records,
            "machine_set":sorted({e.get("machine") for e in elf_records if e.get("machine")}),
        }
        provider_map = {
            "schema_version":1,"evidence_kind":"dependency-provider-map","providers":dict(sorted(providers.items())),
            "dependency_products":dependency_products,"edges":dependency_edges,"unresolved_edges":unresolved,
            "unclassified_packaged_elf":unclassified,"android_system_sonames":sorted(SYSTEM_SONAMES),
        }
        sysconfig = {
            "schema_version":1,"evidence_kind":"sysconfig-census","build_details":build_details,
            "sysconfigdata":sys_items,"selected_build_time_vars":selected_vars,"api_candidates":api_text,
            "selected_minimum_android_api":minimum_api,"selected_version":version,"selected_target":target,
            "selected_platform":platform,"selected_multiarch":multiarch,"selected_extension_suffix":ext_suffix,
        }
        layout = {
            "schema_version":1,"evidence_kind":"package-layout-map","top_level_counts":dict(sorted(top.items())),
            "has_prefix_root":any(r["path"]=="prefix" or r["path"].startswith("prefix/") for r in records),
            "prefix_member_count":len(prefix_records),"build_details_paths":build_details_paths,
            "sysconfigdata_paths":sys_paths,"license_paths":license_paths,"metadata_paths":metadata_paths,
            "archive_types":dict(Counter(r["type"] for r in records)),
        }
        provenance = {
            "schema_version":1,"evidence_kind":"provenance-map","binary":{"package_url":x.package_url,"release_page_url":x.release_page_url,"sha256":actual_sha},
            "cpython_source":{"tag":"v3.14.6","source_archive_url":x.source_url,"source_archive_sha256":x.source_sha256,"build_recipe_url":"https://github.com/python/cpython/blob/v3.14.6/Android/android.py","android_build_documentation":"https://docs.python.org/3.14/using/android.html"},
            "dependencies":{"recipe_family_url":"https://github.com/beeware/cpython-android-source-deps","products":[d for d in dependency_products if d["classification"].startswith("beeware-inherited-")]},
            "patches":{"project_local_patches":[],"binary_mutations":[],"upstream_patch_manifest_paths":[p for p in metadata_paths if "patch" in p.lower()]},
            "licenses":{"archive_license_paths":license_paths,"cpython_license_url":"https://docs.python.org/3.14/license.html"},
            "archive_metadata_sources":metadata_paths,"discovered_urls":discovered_urls,
            "provenance_gaps":([{"kind":"unclassified-packaged-elf","items":unclassified}] if unclassified else []) + ([{"kind":"missing-license-files"}] if not license_paths else []),
        }
        pprod=producer["product"]
        delta = {
            "schema_version":1,"evidence_kind":"producer-delta","comparison_boundary":"official binary-derived control versus reconstructed Termux-native producer authority; reconstructed producer is not an input",
            "official":{"package_sha256":actual_sha,"version":version,"target":target,"minimum_android_api":minimum_api,"prefix_snapshot_sha256":prefix_snapshot,"member_count":len(records),"elf_count":len(elf_records),"extension_count":len(extensions),"dependency_products":[d["soname"] for d in dependency_products if d["classification"].startswith("beeware-inherited-")]},
            "reconstructed_producer":{"authority_path":x.producer_authority,"authority_sha256":sha256_file(repo/x.producer_authority),"package_sha256":pprod["package_sha256"],"version":pprod["python_version"],"target":pprod["target_host"],"minimum_android_api":pprod["android_api"],"prefix_snapshot_sha256":pprod["prefix_snapshot_sha256"],"source_commit":pprod["source_commit"],"artifact_topology":sorted(producer["artifacts"])},
            "differences":{"package_bytes_equal":actual_sha==pprod["package_sha256"],"version_equal":version==pprod["python_version"],"target_equal":target==pprod["target_host"],"minimum_api_equal":minimum_api==pprod["android_api"],"prefix_snapshot_equal":prefix_snapshot==pprod["prefix_snapshot_sha256"],"topology":"official single embeddable package versus reconstructed runtime-base/development-addon/test-addon split"},
            "non_claims":["reconstructed producer equivalence","runtime execution","relocation","device qualification","product selection","publication"],
        }
        outputs = {"gate-contract":gate,"upstream-input-manifest":input_manifest,"package-and-file-hashes":package_hashes,
                   "elf-and-extension-inventory":elf_inv,"dependency-provider-map":provider_map,"sysconfig-census":sysconfig,
                   "package-layout-map":layout,"provenance-map":provenance,"producer-delta":delta}
        for role, obj in outputs.items(): dump(out/OUT_FILES[role], obj)
        try: output_label=str(out.relative_to(repo))
        except ValueError: output_label=str(out)
        summary={"pass":all(input_manifest["identity_checks"].values()) and not extraction_errors and not unresolved and not unclassified and bool(license_paths) and len(elf_records)>0 and len(extensions)>0,
                 "output_dir":output_label,"package_sha256":actual_sha,"member_count":len(records),"elf_count":len(elf_records),"extension_count":len(extensions),"minimum_android_api":minimum_api,"unresolved_dependency_count":len(unresolved),"unclassified_packaged_elf_count":len(unclassified),"provenance_gap_count":len(provenance["provenance_gaps"])}
        print(json.dumps(summary,indent=2,sort_keys=True))
        return 0 if summary["pass"] else 1

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as e:
        print(json.dumps({"pass":False,"error":f"{type(e).__name__}: {e}"},indent=2),file=sys.stderr)
        raise

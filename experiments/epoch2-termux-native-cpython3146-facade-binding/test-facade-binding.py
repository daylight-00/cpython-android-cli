#!/usr/bin/env python3
"""Self-contained regression tests for the Termux-native façade producer binding."""
from __future__ import annotations
import hashlib, io, json, os, subprocess, sys, tarfile, tempfile
from pathlib import Path
from typing import Any


def canonical(v: Any) -> bytes:
    return (json.dumps(v, indent=2, sort_keys=True) + "\n").encode()

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def entry(path: str, kind: str, mode: str, data: bytes | None = None, target: str | None = None, cls: str = "OWNED_PAYLOAD") -> dict[str, Any]:
    row: dict[str, Any] = {"archive_path": f"payload/{path}", "payload_path": path, "entry_class": cls, "type": kind, "mode": mode}
    if data is not None: row.update(size=len(data), sha256=hashlib.sha256(data).hexdigest(), elf=False)
    if target is not None: row["symlink_target"] = target
    return row

def make_artifact(root: Path, name: str, rows: list[dict[str, Any]], payload: dict[str, bytes]) -> tuple[Path, Path]:
    aid=f"fixture-{name}"; manifest={"schema_version":1,"manifest_kind":"artifact-manifest","artifact":{"name":name,"artifact_id":aid},"entries":rows}
    mp=root/f"manifests/{name}.manifest.json"; mp.parent.mkdir(parents=True,exist_ok=True); mp.write_bytes(canonical(manifest))
    tar_path=root/f"{name}.tar"; zst=root/f"artifacts/{aid}.tar.zst"; zst.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(tar_path,"w",format=tarfile.PAX_FORMAT) as t:
        for dirname in (aid,f"{aid}/metadata",f"{aid}/payload"):
            i=tarfile.TarInfo(dirname); i.type=tarfile.DIRTYPE; i.mode=0o700; t.addfile(i)
        meta=canonical(manifest); i=tarfile.TarInfo(f"{aid}/metadata/manifest.json"); i.mode=0o600; i.size=len(meta); t.addfile(i,io.BytesIO(meta))
        for row in rows:
            n=f"{aid}/{row['archive_path']}"; i=tarfile.TarInfo(n); i.mode=int(row['mode'],8)
            if row['type']=="directory": i.type=tarfile.DIRTYPE; t.addfile(i)
            elif row['type']=="symlink": i.type=tarfile.SYMTYPE; i.linkname=row['symlink_target']; t.addfile(i)
            else:
                data=payload[row['payload_path']]; i.size=len(data); t.addfile(i,io.BytesIO(data))
    subprocess.run(["zstd","-q","-f","-T1","--check","-o",str(zst),str(tar_path)],check=True); tar_path.unlink()
    return zst,mp

def run(cmd:list[str], cwd:Path, env:dict[str,str], expect:int=0) -> subprocess.CompletedProcess[str]:
    p=subprocess.run(cmd,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode!=expect: raise AssertionError(f"rc {p.returncode}!={expect}: {cmd}\n{p.stdout}\n{p.stderr}")
    return p

def main()->int:
    repo=Path(__file__).resolve().parents[2]; helper=repo/"components/standalone/lib/materialize_frozen_producer.py"
    tests=[]
    with tempfile.TemporaryDirectory(prefix="e2p2-binding-test-") as td:
        root=Path(td); authority=root/"authority"
        runtime_rows=[entry("bin","directory","0700"),entry("bin/python3.14","regular","0755",b"fixture-launcher"),entry("bin/python3","symlink","0777",target="python3.14"),entry("bin/python","symlink","0777",target="python3"),entry("lib","directory","0700"),entry("lib/python3.14","directory","0700"),entry("lib/python3.14/LICENSE.txt","regular","0644",b"license")]
        dev_rows=[entry("lib","directory","0700",cls="STRUCTURAL_PARENT"),entry("lib/python3.14","directory","0700",cls="STRUCTURAL_PARENT"),entry("include","directory","0700"),entry("include/Python.h","regular","0644",b"header")]
        test_rows=[entry("lib","directory","0700",cls="STRUCTURAL_PARENT"),entry("lib/python3.14","directory","0700",cls="STRUCTURAL_PARENT"),entry("lib/python3.14/test","directory","0700"),entry("lib/python3.14/test/test_x.py","regular","0644",b"pass\n")]
        specs={}
        for name,rows,payload in [("runtime-base",runtime_rows,{"bin/python3.14":b"fixture-launcher","lib/python3.14/LICENSE.txt":b"license"}),("development-addon",dev_rows,{"include/Python.h":b"header"}),("test-addon",test_rows,{"lib/python3.14/test/test_x.py":b"pass\n"})]:
            a,m=make_artifact(authority,name,rows,payload); specs[name]={"archive":{"path":a.relative_to(authority).as_posix(),"filename":a.name,"sha256":sha(a),"size":a.stat().st_size},"manifest":{"path":m.relative_to(authority).as_posix(),"sha256":sha(m),"size":m.stat().st_size}}
        product_lock=authority/"product-lock.json"; product_lock.write_text("{}\n")
        files={}
        for spec in specs.values():
            for k in ("archive","manifest"):
                r=spec[k]; files[r['path']]={"sha256":r['sha256'],"size":r['size']}
        files['product-lock.json']={"sha256":sha(product_lock),"size":product_lock.stat().st_size}
        index={"schema_version":1,"authority_kind":"fixture-authority","status":"frozen-pass","files":files}; ip=authority/"authority-index.json"; ip.write_bytes(canonical(index))
        lock=repo/"config/products/cpython-3.14.6-aarch64-linux-android.lock.json"
        binding={"schema_version":1,"binding_version":1,"status":"frozen-authority-bound","authority":{"kind":"fixture-authority","remote":"unused:","index":{"path":"authority-index.json","sha256":sha(ip),"size":ip.stat().st_size},"files":files},"artifacts":specs,"composition":{"selected_artifacts":["runtime-base","development-addon"],"preserved_unselected_artifacts":["test-addon"],"expected_owned_paths":9,"expected_structural_references":2},"product":{"launcher_sha256":hashlib.sha256(b"fixture-launcher").hexdigest()},"materialization":{"work_root":"work"},"repository_product_lock":str(lock)}
        bp=root/"binding.json"; bp.write_bytes(canonical(binding)); env={**os.environ,"TARGET_ID":"fixture","BUILD_PROFILE":"release"}
        cmd=[sys.executable,str(helper),"--root",str(repo),"--binding",str(bp),"--authority-root",str(authority),"--work-root",str(root/"work"),"--out-root",str(root/"out"),"--no-acquire"]
        run(cmd,repo,env); tests.append(("exact_composition",(root/"work/prefix/include/Python.h").read_bytes()==b"header" and not (root/"work/prefix/lib/python3.14/test").exists()))
        tests.append(("structural_parent_nonownership",(root/"work/prefix/lib/python3.14/LICENSE.txt").read_bytes()==b"license"))
        runtime=authority/specs['runtime-base']['archive']['path']; original=runtime.read_bytes(); runtime.write_bytes(original[:-1]+bytes([original[-1]^1])); run(cmd,repo,env,expect=1); runtime.write_bytes(original); tests.append(("archive_mutation_rejected",True))
    result={"schema_version":1,"test_count":len(tests),"pass_count":sum(v for _,v in tests),"pass":all(v for _,v in tests),"tests":[{"name":n,"pass":v} for n,v in tests]}; print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result['pass'] else 1
if __name__=="__main__": raise SystemExit(main())

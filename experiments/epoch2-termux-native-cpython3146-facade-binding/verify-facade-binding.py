#!/usr/bin/env python3
"""Verify the current E2-P2 Termux-native CPython 3.14.6 façade binding."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
from typing import Any

EXPECTED_BASE_FAILURES={"authority_file_identities","branch_active","build_contract","documentation_status","package_contract"}
EXPECTED_AUDIT_FAILURES={"branch","current_context","facade_lock_pinned","facade_stage3b_steps","roadmap"}

def read(path:Path)->dict[str,Any]:
    v=json.loads(path.read_text(encoding="utf-8"));
    if not isinstance(v,dict): raise TypeError(path)
    return v

def sha(path:Path)->str:
    h=hashlib.sha256();
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def run(argv:list[str],root:Path,env:dict[str,str]|None=None,timeout:int=240)->subprocess.CompletedProcess[str]:
    return subprocess.run(argv,cwd=root,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)

def parsed(proc:subprocess.CompletedProcess[str])->dict[str,Any]:
    try:
        v=json.loads(proc.stdout); return v if isinstance(v,dict) else {}
    except Exception:return {}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]); ns=ap.parse_args(); root=ns.root.resolve()
    exp=root/"experiments/epoch2-termux-native-cpython3146-facade-binding"; errors={}; checks={}
    def ck(n:str,v:Any): checks[n]=bool(v)
    try: authority=read(exp/"facade-binding-authority.json")
    except Exception as e: authority={}; errors["authority"]=f"{type(e).__name__}: {e}"
    try: contract=read(root/"components/standalone/contracts/facade-v1.json")
    except Exception as e: contract={}; errors["contract"]=f"{type(e).__name__}: {e}"
    try: binding=read(root/"components/standalone/contracts/termux-native-cpython3146-producer-binding-v1.json")
    except Exception as e: binding={}; errors["binding"]=f"{type(e).__name__}: {e}"
    try: lock=read(root/"config/products/cpython-3.14.6-aarch64-linux-android.lock.json")
    except Exception as e: lock={}; errors["lock"]=f"{type(e).__name__}: {e}"
    branch=run(["git","branch","--show-current"],root)
    ck("branch_main",branch.returncode==0 and branch.stdout.strip()=="main")
    ck("diff_check",run(["git","diff","--check","HEAD"],root).returncode==0)
    ck("authority_identity",authority.get("schema_version")==1 and authority.get("authority_kind")=="e2p2-termux-native-cpython3146-facade-binding" and authority.get("status")=="frozen-pass")
    identities=authority.get("file_identities",{})
    ck("file_identities",isinstance(identities,dict) and bool(identities) and all((root/p).is_file() and sha(root/p)==d for p,d in identities.items()))
    build=contract.get("operations",{}).get("build",{}); package=contract.get("operations",{}).get("package",{}); verify=contract.get("operations",{}).get("verify",{})
    ck("contract_identity",contract.get("schema_version")==1 and contract.get("contract_version")==1 and contract.get("stable_command")=="components/standalone/bin/cpython-android-standalone")
    ck("contract_binding",contract.get("producer_binding",{}).get("binding_contract")=="components/standalone/contracts/termux-native-cpython3146-producer-binding-v1.json" and contract.get("producer_binding",{}).get("freeze_commit")=="d1f19039af727344c77f2d0fac0806553da86bcc")
    ck("build_route",build.get("host_role")=="termux" and [r.get("id") for r in build.get("steps",[])]==["materialize-frozen-producer"] and build.get("receipt")=="results/termux/epoch2-standalone/build-receipt.json")
    ck("package_route",package.get("host_role")=="termux" and package.get("input_prefix")=="work/termux/e2p2-termux-native-cpython3146-facade/prefix" and package.get("input_launcher")=="out/{target_id}/{build_profile}/bin/python3.14")
    ck("verify_route",verify.get("repository_implementation")=="experiments/epoch2-termux-native-cpython3146-facade-binding/verify-facade-binding.py" and verify.get("scopes")==["repository","envelope"])
    ck("binding_identity",binding.get("schema_version")==1 and binding.get("binding_version")==1 and binding.get("status")=="frozen-authority-bound")
    ck("binding_authority",binding.get("authority",{}).get("index",{}).get("sha256")=="1ef9bf7cfac11dd592241ad08e0c2eb8105148782044d78c48a7481d0f93f4f2" and binding.get("authority",{}).get("remote")=="gdrive:HW-T/cpython-android-cli/authorities/e2p2/producers/termux-native-cpython3146/frozen-product-v1")
    ck("binding_composition",binding.get("composition",{}).get("selected_artifacts")==["runtime-base","development-addon"] and binding.get("composition",{}).get("preserved_unselected_artifacts")==["test-addon"] and binding.get("composition",{}).get("expected_owned_paths")==1168)
    arts=binding.get("artifacts",{})
    ck("artifact_identities",arts.get("runtime-base",{}).get("archive",{}).get("sha256")=="7119e97cb43fb19ef4dce3eec145bb867b8070b9f8b7772c74a5885f4fe53c03" and arts.get("development-addon",{}).get("archive",{}).get("sha256")=="73dc90a8ead6c58d040a2fc31386f1c00ff38ce84fd4507229e8e9bc18902b6f" and arts.get("test-addon",{}).get("archive",{}).get("sha256")=="5bb4c1a45a2c04031c8c8c1a0be05fc02ad4653f21492b63559039105be5ce03")
    pa=lock.get("producer_authority",{})
    ck("product_lock",lock.get("python_version")=="3.14.6" and lock.get("archive",{}).get("sha256")=="517f4b0d113c4c1cf6931c230b6b517bee7a2b7f8b4f0f099a148260fa3ac8e7" and lock.get("canonical_host")=="aarch64-unknown-linux-android" and pa.get("freeze_commit")=="d1f19039af727344c77f2d0fac0806553da86bcc")
    env={**os.environ,"PROJECT_ROLE":"termux","TARGET_ID":"aarch64-linux-android24","TARGET_HOST":"aarch64-linux-android","ANDROID_API":"24","PYTHON_VERSION":"3.14.6","PYTHON_MM":"3.14","BUILD_PROFILE":"release","PYTHONDONTWRITEBYTECODE":"1"}
    stable=root/"components/standalone/bin/cpython-android-standalone"
    plans=[]
    for op in ("build","package","verify"):
        p=run([str(stable),"plan",op],root,env); plans.append((p,parsed(p)))
    ck("stable_plans",all(p.returncode==0 and d.get("contract_validation",{}).get("pass") is True for p,d in plans))
    test=run([sys.executable,str(exp/"test-facade-binding.py")],root,env,300); td=parsed(test)
    ck("binding_regression",test.returncode==0 and td.get("pass") is True and td.get("test_count")==3)
    old=run([sys.executable,str(root/"experiments/epoch2-standalone-build-facade/verify-e2p2-standalone-facade.py"),"--root",str(root)],root,env,300); od=parsed(old)
    ck("historical_facade_adjudication",old.returncode==1 and set(od.get("failed_checks",[]))==EXPECTED_BASE_FAILURES and od.get("check_count")==24 and od.get("pass_count")==19)
    audit=run([sys.executable,str(root/"experiments/epoch2-standalone-build-facade/verify-e2p2-custom-ndk-provenance-audit.py"),"--root",str(root)],root,env); ad=parsed(audit)
    ck("historical_ndk_adjudication",audit.returncode==1 and set(ad.get("failed_checks",[]))==EXPECTED_AUDIT_FAILURES and ad.get("check_count")==49 and ad.get("pass_count")==44)
    current=(root/"docs/CURRENT_CONTEXT.md").read_text(encoding="utf-8"); roadmap=(root/"docs/roadmap/EPOCH2_ROADMAP.md").read_text(encoding="utf-8"); doc=(root/"docs/contracts/E2P2_STANDALONE_FACADE_CONTRACT.md").read_text(encoding="utf-8")
    ck("documentation","façade producer binding frozen" in current and "binding frozen; real façade execution next" in roadmap and "producer binding frozen — real façade execution next" in doc)
    ck("claim_boundary",binding.get("claim_boundary")=={"qualification":False,"publication":False,"real_e2p1_envelope_produced":False,"real_facade_build_executed":False,"selectability":False,"transition_behavior":False})
    failed=sorted(k for k,v in checks.items() if not v); result={"schema_version":1,"verification_kind":"e2p2-termux-native-cpython3146-facade-binding","pass":not failed and not errors,"check_count":len(checks),"pass_count":sum(checks.values()),"failed_checks":failed,"parse_errors":errors,"checks":dict(sorted(checks.items())),"historical":{"facade":{"raw_rc":old.returncode,"failed_checks":od.get("failed_checks")},"custom_ndk":{"raw_rc":audit.returncode,"failed_checks":ad.get("failed_checks")}},"claim_boundary":"Producer binding and routing only; real facade execution, E2-P1 envelope acceptance, qualification, selection, publication, installer conversion, and transitions remain unclaimed."}; print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result['pass'] else 1
if __name__=="__main__": raise SystemExit(main())

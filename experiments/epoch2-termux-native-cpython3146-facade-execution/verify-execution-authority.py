#!/usr/bin/env python3
"""Verify the frozen bound Termux-native CPython 3.14.6 façade execution authority."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
from typing import Any

EXPECTED_BINDING_FAILURES={"documentation","file_identities","verify_route"}
EXPECTED_RESULT_SHA="1e0ee255513c7695285d2051bcc6044f7f5052f9a0480c6775170b006abfbb97"
EXPECTED_ENVELOPE_SHA="66c2a39b7164701d3a14cff538be298abcf30c696150f6abf7785e212c1b4727"
EXPECTED_RELEASE_SHA="64825d3afabbda7c90992debfb11e771baeff5514f2b6e6d13584dc7ac6fcf85"
EXPECTED_PRIVATE_INDEX="5fd8c03b53bcb749cfa221277e75f16b2392e6cec3a184b716f98e24d84fe0b5"
EXPECTED_INPUT_COMMIT="863dccbb31acf4ffe32dd0e26630dd861f96d992"
EXPECTED_INPUT_TREE="560267eb71d3a26dab019802f0dd2427fe81a774"
VERIFY_PATH="experiments/epoch2-termux-native-cpython3146-facade-execution/verify-execution-authority.py"
AUTHORITY_PATH="experiments/epoch2-termux-native-cpython3146-facade-execution/execution-authority.json"
AUDIT_PATH="experiments/epoch2-termux-native-cpython3146-facade-execution/execution-authority-external-audit.json"

def read(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise TypeError(path)
    return value

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def run(argv:list[str],root:Path,env:dict[str,str]|None=None,timeout:int=300)->subprocess.CompletedProcess[str]:
    return subprocess.run(argv,cwd=root,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)

def parsed(proc:subprocess.CompletedProcess[str])->dict[str,Any]:
    try:
        value=json.loads(proc.stdout); return value if isinstance(value,dict) else {}
    except Exception: return {}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]); ns=ap.parse_args(); root=ns.root.resolve()
    checks:dict[str,bool]={}; errors:dict[str,str]={}
    def ck(name:str,value:Any): checks[name]=bool(value)
    try: authority=read(root/AUTHORITY_PATH)
    except Exception as exc: authority={}; errors["authority"]=f"{type(exc).__name__}: {exc}"
    try: audit=read(root/AUDIT_PATH)
    except Exception as exc: audit={}; errors["audit"]=f"{type(exc).__name__}: {exc}"
    try: contract=read(root/"components/standalone/contracts/facade-v1.json")
    except Exception as exc: contract={}; errors["contract"]=f"{type(exc).__name__}: {exc}"
    try: binding=read(root/"components/standalone/contracts/termux-native-cpython3146-producer-binding-v1.json")
    except Exception as exc: binding={}; errors["binding"]=f"{type(exc).__name__}: {exc}"
    try: lock=read(root/"config/products/cpython-3.14.6-aarch64-linux-android.lock.json")
    except Exception as exc: lock={}; errors["lock"]=f"{type(exc).__name__}: {exc}"
    ck("branch_main",run(["git","branch","--show-current"],root).stdout.strip()=="main")
    ck("diff_check",run(["git","diff","--check","HEAD"],root).returncode==0)
    ck("authority_identity",authority.get("schema_version")==1 and authority.get("authority_version")==1 and authority.get("authority_kind")=="e2p2-termux-native-cpython3146-bound-facade-execution-authority-freeze" and authority.get("status")=="frozen-pass-unqualified-envelope")
    ck("authority_predecessor",authority.get("predecessor",{}).get("commit")==EXPECTED_INPUT_COMMIT and authority.get("predecessor",{}).get("tree")==EXPECTED_INPUT_TREE and authority.get("predecessor",{}).get("result_archive_sha256")==EXPECTED_RESULT_SHA)
    envelope=authority.get("envelope",{})
    ck("authority_envelope",envelope.get("artifact_id")=="cpython-3.14.6-aarch64-linux-android24-install_only_stripped" and envelope.get("archive",{}).get("sha256")==EXPECTED_ENVELOPE_SHA and envelope.get("release_index",{}).get("sha256")==EXPECTED_RELEASE_SHA and envelope.get("manifest_entry_count")==1169 and envelope.get("stripped_elf_count")==81)
    private=authority.get("private_authority",{})
    ck("authority_private",private.get("remote")=="gdrive:HW-T/cpython-android-cli/authorities/e2p2/envelopes/termux-native-cpython3146/install-only-stripped-v1" and private.get("index_sha256")==EXPECTED_PRIVATE_INDEX and private.get("file_count")==20 and private.get("readback_pass") is True)
    ck("authority_verification",authority.get("verification")=={"build":"9/9","determinism":"4/4","envelope":"52/52-canonical-and-replay","external_audit":"33/33","independent":"27/27","repository":"20/20-before-and-after"})
    ck("authority_toolchain",authority.get("toolchain",{}).get("ndk_revision")=="27.3.13750724" and authority.get("toolchain",{}).get("prebuilt_tag")=="linux-arm64" and authority.get("toolchain",{}).get("compiler")=="aarch64-linux-android24-clang" and authority.get("toolchain",{}).get("strip_tool")=="llvm-objcopy")
    ck("authority_claim_boundary",authority.get("claim_boundary")=={"e2p1_envelope_produced":True,"installer_conversion":False,"publication":False,"selectability":False,"static_envelope_review":True,"target_qualification":False,"transition_behavior":False})
    identities=authority.get("file_identities",{})
    ck("file_identities",isinstance(identities,dict) and bool(identities) and all((root/path).is_file() and sha(root/path)==digest for path,digest in identities.items()))
    ck("external_audit",audit.get("schema_version")==1 and audit.get("audit_kind")=="e2p2-termux-native-cpython3146-bound-facade-execution-authority-external-audit" and audit.get("source_result_sha256")==EXPECTED_RESULT_SHA and audit.get("pass") is True and audit.get("check_count")==33 and audit.get("pass_count")==33 and audit.get("failed_checks")==[])
    ck("contract_identity",contract.get("schema_version")==1 and contract.get("contract_version")==1 and contract.get("stable_command")=="components/standalone/bin/cpython-android-standalone")
    ck("contract_binding",contract.get("producer_binding",{}).get("binding_contract")=="components/standalone/contracts/termux-native-cpython3146-producer-binding-v1.json" and contract.get("producer_binding",{}).get("freeze_commit")=="d1f19039af727344c77f2d0fac0806553da86bcc")
    execution=contract.get("execution_authority",{})
    ck("contract_execution_authority",execution=={"authority_path":AUTHORITY_PATH,"authority_version":1,"execution_input_commit":EXPECTED_INPUT_COMMIT,"execution_input_tree":EXPECTED_INPUT_TREE,"private_authority_index_sha256":EXPECTED_PRIVATE_INDEX,"result_archive_sha256":EXPECTED_RESULT_SHA,"status":"frozen-pass-unqualified-envelope"})
    operations=contract.get("operations",{}); build=operations.get("build",{}); package=operations.get("package",{}); verify=operations.get("verify",{})
    ck("build_route",build.get("host_role")=="termux" and [row.get("id") for row in build.get("steps",[])]==["materialize-frozen-producer"])
    ck("package_route",package.get("host_role")=="termux" and package.get("primary_flavor")=="install_only_stripped" and package.get("input_prefix")=="work/termux/e2p2-termux-native-cpython3146-facade/prefix")
    ck("verify_route",verify.get("repository_implementation")==VERIFY_PATH and verify.get("envelope_implementation")=="components/standalone/lib/verify_envelope.py" and verify.get("scopes")==["repository","envelope"])
    ck("binding_preserved",binding.get("status")=="frozen-authority-bound" and binding.get("composition",{}).get("selected_artifacts")==["runtime-base","development-addon"] and binding.get("composition",{}).get("preserved_unselected_artifacts")==["test-addon"])
    ck("product_lock",lock.get("python_version")=="3.14.6" and lock.get("source_head")=="c63aec69bd59c55314c06c23f4c22c03de76fe45" and lock.get("ndk_version")=="27.3.13750724" and lock.get("producer_authority",{}).get("authority_index_sha256")=="1ef9bf7cfac11dd592241ad08e0c2eb8105148782044d78c48a7481d0f93f4f2")
    env={**os.environ,"PROJECT_ROLE":"termux","TARGET_ID":"aarch64-linux-android24","TARGET_HOST":"aarch64-linux-android","ANDROID_API":"24","PYTHON_VERSION":"3.14.6","PYTHON_MM":"3.14","BUILD_PROFILE":"release","PYTHONDONTWRITEBYTECODE":"1"}
    stable=root/"components/standalone/bin/cpython-android-standalone"; plans=[]
    for op in ("build","package","verify"):
        proc=run([str(stable),"plan",op],root,env); plans.append((proc,parsed(proc)))
    ck("stable_plans",all(proc.returncode==0 and data.get("contract_validation",{}).get("pass") is True for proc,data in plans))
    predecessor=run([sys.executable,str(root/"experiments/epoch2-termux-native-cpython3146-facade-binding/verify-facade-binding.py"),"--root",str(root)],root,env,600); predecessor_data=parsed(predecessor)
    ck("binding_adjudication",predecessor.returncode==1 and predecessor_data.get("check_count")==20 and predecessor_data.get("pass_count")==17 and set(predecessor_data.get("failed_checks",[]))==EXPECTED_BINDING_FAILURES)
    current=(root/"docs/CURRENT_CONTEXT.md").read_text(encoding="utf-8"); roadmap=(root/"docs/roadmap/EPOCH2_ROADMAP.md").read_text(encoding="utf-8"); contract_doc=(root/"docs/contracts/E2P2_STANDALONE_FACADE_CONTRACT.md").read_text(encoding="utf-8")
    ck("documentation","bound façade execution authority frozen" in current and "Real façade execution authority frozen" in roadmap and "execution authority accepted" in contract_doc)
    evidence=(root/"docs/evidence/E2P2_TERMUX_NATIVE_CPYTHON3146_FACADE_EXECUTION_AUTHORITY_FREEZE.md").read_text(encoding="utf-8")
    ck("evidence","66c2a39b7164701d3a14cff538be298abcf30c696150f6abf7785e212c1b4727" in evidence and "52/52" in evidence and "27/27" in evidence and "not qualified" in evidence)
    ck("next_action",authority.get("next_action_class")=="qualify-frozen-termux-native-cpython3146-envelope")
    failed=sorted(name for name,value in checks.items() if not value)
    result={"schema_version":1,"verification_kind":"e2p2-termux-native-cpython3146-bound-facade-execution-authority-freeze","pass":not failed and not errors,"check_count":len(checks),"pass_count":sum(checks.values()),"failed_checks":failed,"parse_errors":errors,"checks":dict(sorted(checks.items())),"historical":{"binding":{"raw_rc":predecessor.returncode,"failed_checks":predecessor_data.get("failed_checks")}},"claim_boundary":"The real deterministic unqualified E2-P1 envelope and static review are frozen. E2-P3 target qualification, selection, publication, installer conversion, and transition behavior remain unclaimed."}
    print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result["pass"] else 1

if __name__=="__main__": raise SystemExit(main())

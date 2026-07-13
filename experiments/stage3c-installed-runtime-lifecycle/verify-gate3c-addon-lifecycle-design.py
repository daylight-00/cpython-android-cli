#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
EXPECTED_GROUPS={"preflight":10,"composition":10,"uninstall":9,"recovery":12,"locking":2,"behavior":7}
EXPECTED_STATES={"empty":([],0),"runtime":(["runtime-base"],714),"runtime-development":(["runtime-base","development-addon"],1168),"runtime-test":(["runtime-base","test-addon"],2502),"composed":(["runtime-base","development-addon","test-addon"],2956)}
EXPECTED_ARTIFACTS={
"runtime-base":("cpython-android-cli-3.14.6-android24-aarch64-runtime-base","2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743","ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a",714,0,None),
"development-addon":("cpython-android-cli-3.14.6-android24-aarch64-development-addon","f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea","9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a",454,2,"runtime-base"),
"test-addon":("cpython-android-cli-3.14.6-android24-aarch64-test-addon","02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1","47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f",1788,2,"runtime-base")}
EXPECTED_BLOBS={"recovery_common.py":"3183ba0861ef45e7a395201bec0085f3f69fb248","recovery_operations.py":"8a307065e00fd7a7332541f4911c5478945374ee","recovery_engine.py":"aebf5b9a33d163f7f8758f785ca621c94c0e478b","recovery_durability.py":"61bfb859f73acccb0dfcce1d2a630bfd1ffc2d3f"}
EXPECTED_SHA={"recovery_operations_missing_leaf.py":"61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021","recovery_engine_missing_leaf.py":"33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a"}
def readj(path:Path)->dict[str,Any]:
 value=json.loads(path.read_text(encoding="utf-8"))
 if not isinstance(value,dict): raise ValueError(path)
 return value
def sha256(path:Path)->str:
 h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
def git_blob(path:Path)->str:
 data=path.read_bytes(); return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
def cjson(value:Any)->bytes:
 return (json.dumps(value,indent=2,sort_keys=True)+"\n").encode()
def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("--project-root",type=Path,required=True); p.add_argument("--matrix",type=Path,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--require-pass",action="store_true"); a=p.parse_args()
 root=a.project_root.resolve(); matrix=readj(a.matrix.resolve()); checks:dict[str,bool]={}
 def check(name:str,value:bool)->None: checks[name]=bool(value)
 check("matrix_schema_v1",matrix.get("schema_version")==1)
 check("matrix_kind_exact",matrix.get("matrix_kind")=="stage3c-phase5-gate3c-addon-lifecycle-design")
 check("matrix_status_target_pending",matrix.get("status")=="DESIGN_FROZEN_TARGET_EVIDENCE_PENDING")
 check("target_exact",matrix.get("target")=="Termux on Android arm64")
 authority=matrix.get("authority",{}); artifacts=authority.get("artifacts",{})
 check("artifact_order_exact",authority.get("artifact_order")==["runtime-base","development-addon","test-addon"])
 for name,(aid,archive,manifest,count,structural,prereq) in EXPECTED_ARTIFACTS.items():
  item=artifacts.get(name,{})
  check(f"{name}_artifact_id",item.get("artifact_id")==aid)
  check(f"{name}_archive_sha256",item.get("archive_sha256")==archive)
  check(f"{name}_manifest_sha256",item.get("manifest_sha256")==manifest)
  check(f"{name}_owned_count",item.get("owned_paths")==count)
  check(f"{name}_structural_count",item.get("structural_parents")==structural)
  check(f"{name}_prerequisite",item.get("prerequisite")==prereq)
 check("manifest_index_exact",authority.get("manifest_index_sha256")=="540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1")
 check("contract_index_exact",authority.get("contract_index_sha256")=="79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3")
 check("gate3b_archive_exact",authority.get("gate3b_archive_sha256")=="0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b")
 check("gate3b_index_exact",authority.get("gate3b_result_index_sha256")=="f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9")
 check("shared_namespace_exact",authority.get("shared_structural_namespace")==["lib","lib/python3.14"])
 check("registered_total_2956",authority.get("registered_owned_path_total")==2956)
 check("structural_total_4",authority.get("structural_reference_total")==4)
 states=authority.get("states",{})
 for name,(names,count) in EXPECTED_STATES.items():
  item=states.get(name,{})
  check(f"state_{name}_artifacts",item.get("artifacts")==names)
  check(f"state_{name}_count",item.get("owned_path_count")==count and item.get("artifact_count")==len(names))
 recovery=root/"experiments/stage3c-installation-recovery"
 for name,want in EXPECTED_BLOBS.items(): check(f"blob_{name}",git_blob(recovery/name)==want and authority.get("integrated_engine_git_blobs",{}).get(name)==want)
 for name,want in EXPECTED_SHA.items(): check(f"sha_{name}",sha256(recovery/name)==want and authority.get("corrected_engine_sha256",{}).get(name)==want)
 ops=(recovery/"recovery_operations.py").read_text(encoding="utf-8")
 corrected=(recovery/"recovery_operations_missing_leaf.py").read_text(encoding="utf-8")
 check("engine_prerequisite_guard_present",all(x in ops for x in ['prerequisite = manifest["compatibility"]["prerequisite"]','prerequisite["artifact"] not in artifact_map','artifact_map[prerequisite["artifact"]]["artifact_id"] != prerequisite["artifact_id"]','raise RuntimeError("prerequisite not installed")']))
 check("engine_runtime_dependent_guard_present",all(x in ops for x in ['if artifact == "runtime-base":','raise RuntimeError("dependent addons installed")']))
 check("corrected_uninstall_is_frozen",re.search(r"^uninstall = frozen\.uninstall$",corrected,re.M) is not None)
 policy=matrix.get("policy",{})
 check("addon_prerequisites_exact",policy.get("addon_prerequisites")=={"development-addon":["runtime-base"],"test-addon":["runtime-base"]})
 check("no_inter_addon_dependency",policy.get("inter_addon_dependency") is None)
 check("either_addon_removal_order",policy.get("addon_uninstall_order")=="either-addon-may-be-removed-first")
 scenarios=matrix.get("scenarios",[]); ids=[x.get("id") for x in scenarios]
 check("matrix_canonical_json",a.matrix.resolve().read_bytes()==cjson(matrix))
 check("scenario_count_50",matrix.get("scenario_count")==50 and len(scenarios)==50)
 check("scenario_ids_unique",len(ids)==len(set(ids)) and all(isinstance(x,str) for x in ids))
 expected_ids={f"P{i:02d}" for i in range(1,11)}|{f"C{i:02d}" for i in range(1,11)}|{f"U{i:02d}" for i in range(1,10)}|{f"R{i:02d}" for i in range(1,13)}|{f"L{i:02d}" for i in range(1,3)}|{f"B{i:02d}" for i in range(1,8)}
 check("scenario_ids_exact",set(ids)==expected_ids)
 check("scenario_group_counts",matrix.get("scenario_group_counts")==EXPECTED_GROUPS and {g:sum(x.get("group")==g for x in scenarios) for g in EXPECTED_GROUPS}==EXPECTED_GROUPS)
 check("scenario_required_fields",all(set(x)>={"id","group","operation","initial_state","expected_state","expected_result","required_evidence"} and x.get("required_evidence") for x in scenarios))
 byid={x["id"]:x for x in scenarios}
 check("test_first_install_present",byid.get("C03",{}).get("initial_state")=="runtime" and byid.get("C05",{}).get("initial_state")=="runtime-test")
 check("development_first_removal_allowed",byid.get("U02",{}).get("expected_state")=="runtime-test" and byid.get("U02",{}).get("expected_result")=="PASS")
 check("runtime_successful_uninstall_absent",not any(x.get("operation")=="uninstall runtime-base" and x.get("expected_result","" ).startswith("PASS") for x in scenarios))
 preflight=[x for x in scenarios if x.get("group")=="preflight"]
 check("preflight_zero_mutation",all(x.get("mutation_count")==0 for x in preflight))
 recovery_rows=[x for x in scenarios if x.get("group")=="recovery"]
 check("recovery_operation_cross_product",{x.get("operation_key") for x in recovery_rows}=={"development-install","test-install","development-uninstall","test-uninstall"} and all(sum(y.get("operation_key")==op for y in recovery_rows)==3 for op in {x.get("operation_key") for x in recovery_rows}))
 check("recovery_boundaries_exact",{(x.get("crash_boundary"),x.get("process_rc")) for x in recovery_rows}=={("PREPARED",90),("LATE_APPLYING",93),("COMMITTED",92)})
 check("recovery_second_noop",all(x.get("second_recovery")=="NOOP" for x in recovery_rows))
 check("behavior_surface_exact",{x.get("id") for x in scenarios if x.get("group")=="behavior"}=={f"B{i:02d}" for i in range(1,8)})
 req=set(matrix.get("target_evidence_requirements",[]))
 check("evidence_requirements_complete",{"archive safety inspection","synchronous raw stdout/stderr","real process return codes","canonical machine JSON","root result-index recomputation","independent verifier","runtime behavior probes","explicit claim boundary"}<=req)
 execution=matrix.get("execution_contract",{})
 check("single_wrapper_required",execution.get("single_termux_wrapper") is True)
 check("zstd_new_archives",execution.get("new_archive_suffix")==".tar.zst")
 check("historical_tgz_immutable",execution.get("historical_tgz_immutable") is True)
 claim=matrix.get("claim_boundary",{})
 check("design_does_not_claim_target",all(term in claim.get("not_proved_by_design","") for term in ["target addon lifecycle","Gate 3D final uninstall","upgrade","downgrade"]))
 check("target_archive_required",claim.get("gate3c_close_requires")=="A complete independently inspected Termux result archive.")
 docs=(root/"experiments/stage3c-installed-runtime-lifecycle/GATE3C_ADDON_LIFECYCLE_DESIGN.md").read_text(encoding="utf-8")
 check("design_doc_policy_boundary",all(x in docs for x in ["Both addons require only the exact runtime-base identity","test-addon does not depend on development-addon","50 scenarios","Gate 3D final runtime-base uninstall remains deferred"]))
 if len(checks)!=73: raise RuntimeError(f"unexpected check count: {len(checks)}")
 failed=sorted(k for k,v in checks.items() if not v)
 result={"schema_version":1,"verification_kind":"stage3c-phase5-gate3c-addon-lifecycle-design-verification","pass":not failed,"check_count":len(checks),"checks":checks,"failed_checks":failed,"matrix_sha256":sha256(a.matrix.resolve()),"observed":{"scenario_count":len(scenarios),"scenario_group_counts":matrix.get("scenario_group_counts"),"engine_git_blobs":{n:git_blob(recovery/n) for n in EXPECTED_BLOBS},"corrected_engine_sha256":{n:sha256(recovery/n) for n in EXPECTED_SHA}},"claim_boundary":matrix.get("claim_boundary")}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(cjson(result)); print(json.dumps(result,indent=2,sort_keys=True)); print("\nGATE3C_ADDON_LIFECYCLE_DESIGN_VERIFICATION="+("73/73 PASS" if result["pass"] else "FAIL"))
 return 0 if result["pass"] or not a.require_pass else 41
if __name__=="__main__": raise SystemExit(main())

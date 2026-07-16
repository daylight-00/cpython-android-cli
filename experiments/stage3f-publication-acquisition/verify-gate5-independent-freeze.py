#!/usr/bin/env python3
"""Independently verify the corrected Stage 3-F publication/acquisition freeze."""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
from typing import Any

BRANCH="agent/stage3f-publication-acquisition"
MAIN="b5a2ca39d1250122312355dd3dbc6165b9409786"
GATE4_RECORD_HEAD="1e7797218473463bc85f6413c49080301eda2ad7"
GATE4_RECORD_TREE="a3a1cb90f12b20ab47203b4f6b47d8a9694b0e04"
GATE4_RECORD_RESULT="daaf64255fce6d9c1ef2f5eb5e57d8dcc85472a4be48e56c47f21b94dee891f8"
GATE4_TARGET_RESULT="6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b"
GATE4_V1_RESULT="2a076288652f1c342da49eccbe4507291df05d1d596b5c6f1d5646610b5990be"
HIST_SNAPSHOT="a00027a81956ef175bf537eff3a92286e26c1120fa536d0a8ad6a096a1760f8c"
RETAINED_SNAPSHOT="dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233"
RETAINED_FILE="419a9d4303fd6b3d7686400c7a275117ae6fe3421c93c30ff356529fc483b9e3"
A145="2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2"
A146="f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208"
K145="cpython-3.14.5-linux-aarch64-none"
K146="cpython-3.14.6-linux-aarch64-none"

REQUIRED=[
"README.md","docs/PROJECT_CONTEXT_STAGE3F.md","docs/PROJECT_ORIENTATION.md","docs/GITHUB_COLLABORATION_WORKFLOW.md",
"docs/stages/STAGE3F_SCOPE.md","docs/handoff/README.md",
"docs/handoff/2026-07-16-stage3f-gate4-retention-correction-acceptance.md",
"docs/handoff/2026-07-16-stage3f-independent-freeze.md",
"docs/evidence/STAGE3F_GATE4_V1_DERIVATION_FAILURE.md",
"docs/evidence/STAGE3F_GATE4_RETAINED_ARTIFACT_ACQUISITION_RESULT.md",
"docs/evidence/STAGE3F_GATE5_INDEPENDENT_FREEZE.md","docs/evidence/STAGE3F_FINAL_SUMMARY.md",
"experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json",
"experiments/stage3f-publication-acquisition/gate2-retention-correction-authority.json",
"experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json",
"experiments/stage3f-publication-acquisition/gate4-retained-artifact-acquisition-authority.json",
"experiments/stage3f-publication-acquisition/GATE5_INDEPENDENT_PUBLICATION_ACQUISITION_FREEZE.md",
"experiments/stage3f-publication-acquisition/gate5-independent-publication-acquisition-freeze.json",
]

def dig(v:Any,*keys:str,default:Any=None)->Any:
    for k in keys:
        if not isinstance(v,dict) or k not in v:return default
        v=v[k]
    return v

def canonical(v:Any)->bytes:
    return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()

def verify(root:Path)->dict[str,Any]:
    root=root.resolve(); missing=[]; errors={}
    def text(rel:str)->str:
        p=root/rel
        if not p.is_file():missing.append(rel);return ""
        try:return p.read_text(encoding="utf-8")
        except Exception as e:errors[rel]=f"{type(e).__name__}: {e}";return ""
    def data(rel:str)->dict[str,Any]:
        raw=text(rel)
        if not raw:return {}
        try:v=json.loads(raw)
        except Exception as e:errors[rel]=f"{type(e).__name__}: {e}";return {}
        if not isinstance(v,dict):errors[rel]="top-level JSON is not object";return {}
        return v
    for rel in REQUIRED:text(rel)
    readme=text("README.md"); ctx=text("docs/PROJECT_CONTEXT_STAGE3F.md"); scope=text("docs/stages/STAGE3F_SCOPE.md")
    orient=text("docs/PROJECT_ORIENTATION.md"); handoff=text("docs/handoff/README.md")
    g4fail=text("docs/evidence/STAGE3F_GATE4_V1_DERIVATION_FAILURE.md")
    g4result=text("docs/evidence/STAGE3F_GATE4_RETAINED_ARTIFACT_ACQUISITION_RESULT.md")
    g5doc=text("experiments/stage3f-publication-acquisition/GATE5_INDEPENDENT_PUBLICATION_ACQUISITION_FREEZE.md")
    g5ev=text("docs/evidence/STAGE3F_GATE5_INDEPENDENT_FREEZE.md"); final=text("docs/evidence/STAGE3F_FINAL_SUMMARY.md")
    g5handoff=text("docs/handoff/2026-07-16-stage3f-independent-freeze.md")
    old=data("experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json")
    corr=data("experiments/stage3f-publication-acquisition/gate2-retention-correction-authority.json")
    retained=data("experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json")
    g4=data("experiments/stage3f-publication-acquisition/gate4-retained-artifact-acquisition-authority.json")
    g5=data("experiments/stage3f-publication-acquisition/gate5-independent-publication-acquisition-freeze.json")
    retained_raw=(root/"experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json").read_bytes() if (root/"experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json").is_file() else b""
    body=retained.get("snapshot",{}) if isinstance(retained,dict) else {}; rows=body.get("rows",[]) if isinstance(body,dict) else []
    rowmap={r.get("key"):r for r in rows if isinstance(r,dict)} if isinstance(rows,list) else {}
    def git(*args:str):return subprocess.run(["git",*args],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    branch=git("symbolic-ref","--quiet","--short","HEAD"); diff=git("diff","--check","HEAD")
    checks={
      "required_files":all((root/r).is_file() for r in REQUIRED),
      "parse_clean":not errors,
      "branch":branch.returncode==0 and branch.stdout.strip()==BRANCH,
      "git_diff_check":diff.returncode==0,
      "readme_frozen":"Stage 3-F  publication and acquisition boundaries       frozen — Gate 5 independent freeze complete" in readme,
      "context_frozen":"> **Status:** Stage 3-F frozen through Gate 5 independent publication/acquisition freeze" in ctx,
      "scope_frozen":"> **Status:** FROZEN — Gate 5 independent publication/acquisition freeze complete" in scope,
      "orientation_complete":"Stage 3-F is complete and frozen through Gate 5" in orient,
      "handoff_gate5":"Stage 3-F Gate 5 independent publication freeze          FROZEN" in handoff,
      "historical_snapshot_preserved":old.get("snapshot_sha256")==HIST_SNAPSHOT,
      "correction_status":corr.get("status")=="accepted-explicit-authority-correction",
      "historical_unselectable":dig(corr,"historical_snapshot","selectable_for_acquisition") is False or dig(corr,"correction_policy","historical_snapshot_selectable") is False,
      "ordinary_redefinition_forbidden":dig(corr,"correction_policy","ordinary_exact_key_redefinition_allowed") is False,
      "retained_selectable":dig(corr,"correction_policy","retained_snapshot_selectable") is True,
      "v1_failure_bound":GATE4_V1_RESULT in g4fail and dig(corr,"trigger","gate4_v1_result_archive_sha256")==GATE4_V1_RESULT,
      "retained_envelope":set(retained)=={"schema_version","snapshot","snapshot_sha256"} and retained.get("schema_version")==1,
      "retained_digest":retained.get("snapshot_sha256")==RETAINED_SNAPSHOT and hashlib.sha256(canonical(body)).hexdigest()==RETAINED_SNAPSHOT,
      "retained_file":len(retained_raw)==2997 and hashlib.sha256(retained_raw).hexdigest()==RETAINED_FILE and retained_raw==canonical(retained),
      "retained_rows":[r.get("key") for r in rows if isinstance(r,dict)]==[K145,K146],
      "artifact_145":dig(rowmap.get(K145,{}),"artifact","size")==9761545 and dig(rowmap.get(K145,{}),"artifact","sha256")==A145,
      "artifact_146":dig(rowmap.get(K146,{}),"artifact","size")==11788907 and dig(rowmap.get(K146,{}),"artifact","sha256")==A146,
      "retention_provenance":all(dig(rowmap.get(k,{}),"provenance","retention_status")=="exact-bytes-preserved-in-target-result" for k in (K145,K146)),
      "gate4_status":g4.get("status")=="accepted-target-evidence-independent-audit-complete",
      "gate4_target_archive":dig(g4,"accepted_result","archive_sha256")==GATE4_TARGET_RESULT and dig(g4,"accepted_result","archive_size")==42968242,
      "gate4_archive_safety":dig(g4,"accepted_result","safe_member_count")==62 and dig(g4,"accepted_result","result_index_count")==46,
      "gate4_target_checks":dig(g4,"accepted_result","target_matrix","check_count")==16 and dig(g4,"accepted_result","target_matrix","pass_count")==16,
      "gate4_independent_checks":dig(g4,"accepted_result","independent_audit","check_count")==31 and dig(g4,"accepted_result","independent_audit","pass_count")==31,
      "gate4_fidelity":dig(g4,"artifact_identities",K145,"payload_fidelity")=="714/714 strict" and dig(g4,"artifact_identities",K146,"payload_fidelity")=="714/714 strict",
      "gate4_no_uv":dig(g4,"protected_state","uv_invocation") is False,
      "gate4_no_execution":dig(g4,"protected_state","product_execution") is False,
      "gate4_no_install":dig(g4,"protected_state","installation_mutation") is False,
      "gate4_no_external":dig(g4,"protected_state","external_network") is False,
      "gate4_result_doc":GATE4_TARGET_RESULT in g4result and "16/16 PASS" in g4result and "31/31 PASS" in g4result,
      "gate5_status":g5.get("status")=="independent-freeze-complete",
      "gate5_class":g5.get("class")=="R-repository-independent-freeze",
      "gate5_repository_input":dig(g5,"repository_input","head")==GATE4_RECORD_HEAD and dig(g5,"repository_input","tree")==GATE4_RECORD_TREE and dig(g5,"repository_input","main")==MAIN,
      "gate5_record_result":dig(g5,"repository_record_result","archive_sha256")==GATE4_RECORD_RESULT and dig(g5,"repository_record_result","archive_size")==20514,
      "gate5_record_safety":dig(g5,"repository_record_result","safe_member_count")==49 and dig(g5,"repository_record_result","result_index_count")==46,
      "gate5_lineage":dig(g5,"accepted_authority","retained_snapshot_sha256")==RETAINED_SNAPSHOT and dig(g5,"accepted_authority","gate4_target_result_sha256")==GATE4_TARGET_RESULT,
      "gate5_limits":dig(g5,"claim_boundary","public_endpoint") is False and dig(g5,"claim_boundary","uv_acquisition") is False and dig(g5,"claim_boundary","installation") is False,
      "gate5_doc":"> **Status:** FROZEN" in g5doc and "Gate 5 closes Stage 3-F" in g5doc,
      "gate5_evidence":"> **Status:** FROZEN — independent publication/acquisition freeze complete" in g5ev and GATE4_RECORD_HEAD in g5ev,
      "final_summary":GATE4_TARGET_RESULT in final and GATE4_RECORD_RESULT in final and RETAINED_SNAPSHOT in final,
      "gate5_handoff":GATE4_RECORD_HEAD in g5handoff and GATE4_RECORD_TREE in g5handoff and "no gate is active" in g5handoff.lower(),
    }
    failed=sorted(k for k,v in checks.items() if not v)
    return {"schema_version":1,"verification_kind":"stage3f-gate5-independent-publication-acquisition-freeze","pass":not failed and not missing and not errors,"check_count":len(checks),"pass_count":sum(checks.values()),"failed_checks":failed,"missing_files":sorted(set(missing)),"parse_errors":errors,"checks":dict(sorted(checks.items()))}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]);a=ap.parse_args()
    r=verify(a.root);print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["pass"] else 1
if __name__=="__main__":raise SystemExit(main())

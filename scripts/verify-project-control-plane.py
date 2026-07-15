#!/usr/bin/env python3
"""Verify frozen Stage 3-D and active Stage 3-E through Gate 3."""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path
from typing import Any

BRANCH="agent/stage3e-managed-python-distribution"
GATE2_ARCHIVE="3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2"
AUDIT_SHA="5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d"

def dig(v:Any,*ks,default=None):
    for k in ks:
        if not isinstance(v,dict) or k not in v:return default
        v=v[k]
    return v

def verify(root:Path)->dict[str,Any]:
    root=root.resolve(); missing=[]; parse_errors={}
    def text(path):
        p=root/path
        if not p.is_file(): missing.append(path); return ""
        try:return p.read_text(encoding="utf-8")
        except Exception as e:parse_errors[path]=f"{type(e).__name__}: {e}"; return ""
    def data(path):
        raw=text(path)
        if not raw:return {}
        try:v=json.loads(raw)
        except Exception as e:parse_errors[path]=f"{type(e).__name__}: {e}"; return {}
        if not isinstance(v,dict):parse_errors[path]="top-level JSON is not object"; return {}
        return v
    readme=text("README.md"); ctx=text("docs/PROJECT_CONTEXT_STAGE3E.md"); scope=text("docs/stages/STAGE3E_SCOPE.md")
    orient=text("docs/PROJECT_ORIENTATION.md"); handoff=text("docs/handoff/README.md")
    evidence=text("docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md")
    g6=data("experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json")
    g1=data("experiments/stage3e-managed-python-distribution/gate1-authority.json")
    g2=data("experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json")
    audit=data("experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json")
    g3doc=text("experiments/stage3e-managed-python-distribution/GATE3_MANAGED_PYTHON_DISTRIBUTION_CONTRACT.md")
    g3=data("experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json")
    required=["README.md","docs/PROJECT_CONTEXT_STAGE3D.md","docs/PROJECT_CONTEXT_STAGE3E.md","docs/stages/STAGE3E_SCOPE.md","docs/PROJECT_ORIENTATION.md","docs/handoff/README.md","docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md","experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json","experiments/stage3e-managed-python-distribution/gate1-authority.json","experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json","experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json","experiments/stage3e-managed-python-distribution/GATE3_MANAGED_PYTHON_DISTRIBUTION_CONTRACT.md","experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json","scripts/test-verify-project-control-plane.py"]
    def git(*args):return subprocess.run(["git",*args],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    br=git("symbolic-ref","--quiet","--short","HEAD"); diff=git("diff","--check","HEAD")
    checks={
      "required_files":all((root/p).is_file() for p in required),"parse_clean":not parse_errors,
      "branch_active":br.returncode==0 and br.stdout.strip()==BRANCH,
      "readme_current":"active — Gate 3 contract frozen; Gate 4 next" in readme,
      "context_status":"> **Status:** Stage 3-E active — Gate 3 managed-Python distribution contract frozen" in ctx,
      "context_gate2":"FROZEN — external re-audit 117/117" in ctx,
      "context_gate3":"Gate 3  managed-Python distribution contract            FROZEN" in ctx,
      "context_gate4":"Gate 4  target implementation and lifecycle validation  ACTIVE NEXT" in ctx,
      "scope_status":"> **Status:** ACTIVE — Gate 3 contract frozen; Gate 4 next" in scope,
      "scope_exact":"Exact patch-version requests are canonical" in scope,
      "orientation_current":"Stage 3-E Gate 2 is accepted" in orient and "Gate 4 is active next" in orient,
      "handoff_current":"Stage 3-E Gate 3 managed-Python distribution contract   FROZEN" in handoff and "ACTIVE NEXT" in handoff,
      "evidence_identity":GATE2_ARCHIVE in evidence and AUDIT_SHA in evidence and "117/117 PASS" in evidence,
      "gate6_frozen":dig(g6,"status")=="accepted-bounded-feasibility",
      "gate1_frozen":dig(g1,"status")=="design-frozen",
      "gate2_status":dig(g2,"status")=="target-evidence-accepted-by-external-reaudit",
      "gate2_archive":dig(g2,"accepted_result","archive_sha256")==GATE2_ARCHIVE,
      "gate2_index":dig(g2,"accepted_result","result_index_count")==168,
      "gate2_audit":dig(g2,"accepted_result","external_audit","check_count")==117 and dig(g2,"accepted_result","external_audit","pass_count")==117 and dig(g2,"accepted_result","external_audit","sha256")==AUDIT_SHA,
      "gate2_selection":dig(g2,"accepted_observations","minor_selection","resolved_version")=="3.14.6" and dig(g2,"accepted_observations","minor_selection","order_independent") is True,
      "audit_pass":audit.get("accepted") is True and audit.get("check_count")==117 and audit.get("pass_count")==117 and audit.get("failed_checks")==[],
      "gate3_doc_status":"> **Status:** CONTRACT FROZEN" in g3doc,
      "gate3_status":g3.get("status")=="contract-frozen",
      "gate3_selector":dig(g3,"selection_contract","canonical")=="exact-patch-version-request",
      "gate3_minor":dig(g3,"selection_contract","minor","observed")=="3.14.6" and dig(g3,"selection_contract","minor","patch_exact") is False,
      "gate3_unspecified":dig(g3,"selection_contract","unspecified","observed")=="3.14.6" and dig(g3,"selection_contract","unspecified","patch_exact") is False,
      "gate3_root":dig(g3,"installation_contract","first_persistent_root")=="project-owned-explicit-install-dir" and dig(g3,"installation_contract","uv_default_managed_dir") is False,
      "gate3_system_coexistence":dig(g3,"coexistence","stage3d_system_python_contract")=="unchanged-and-independent",
      "gate3_gate4":dig(g3,"gate_sequence","gate4")=="ACTIVE_NEXT_PROJECT_OWNED_PERSISTENT_ROOT_VALIDATION",
      "git_diff_check":diff.returncode==0,
    }
    failed=sorted(k for k,v in checks.items() if not v)
    return {"schema_version":1,"verification_kind":"project-control-plane-through-stage3e-gate3","pass":not failed and not missing and not parse_errors,"check_count":len(checks),"pass_count":sum(checks.values()),"failed_checks":failed,"missing_files":sorted(set(missing)),"parse_errors":parse_errors,"checks":dict(sorted(checks.items())),"claim_boundary":"Stage 3-E Gate 3 freezes exact-key managed distribution policy; Gate 4 persistent-root behavior remains unaccepted."}

def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();r=verify(a.root);print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["pass"] else 1
if __name__=="__main__":raise SystemExit(main())

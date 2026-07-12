#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path
from typing import Any

GATE3A_INDEX='a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128'
PHASE4_INDEX='878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce'
ENGINE_SHA='33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a'
OPS_SHA='61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021'

def canonical(v:Any)->bytes: return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def readj(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text());
    if not isinstance(v,dict): raise ValueError(p)
    return v
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--results-dir',required=True,type=Path); ap.add_argument('--output',required=True,type=Path); a=ap.parse_args()
    r=a.results_dir.resolve()
    paths={
      'gate3a_index':r/'input/gate3a/result-index.json','gate3a_verification':r/'input/gate3a/verification.json','gate3a_workflow':r/'input/gate3a/workflow-status.json','phase4_index':r/'input/gate3a/input/phase4/result-index.json',
      'historical_verification':r/'historical-relocation-verification.json','historical_workflow':r/'historical-workflow-status.json','engine_authority':r/'engine-authority.json','patch_authority':r/'patch-authority.json','baseline_install':r/'baseline/install-result.json',
    }
    missing=sorted(str(p) for p in paths.values() if not p.is_file()); errors={}; values={}
    for n,p in paths.items():
        if not p.is_file(): continue
        try: values[n]=readj(p)
        except Exception as e: errors[str(p)]=repr(e)
    gv=values.get('gate3a_verification',{}); gw=values.get('gate3a_workflow',{}); hv=values.get('historical_verification',{}); hw=values.get('historical_workflow',{}); ea=values.get('engine_authority',{}); pa=values.get('patch_authority',{}); install=values.get('baseline_install',{})
    checks={
      'all_required_outputs_present':not missing,
      'all_required_outputs_parse':not errors,
      'accepted_gate3a_index_exact':paths['gate3a_index'].is_file() and sha(paths['gate3a_index'])==GATE3A_INDEX,
      'accepted_gate3a_verification_69':gv.get('pass') is True and gv.get('check_count')==69 and gv.get('failed_checks')==[],
      'accepted_gate3a_workflow_zero':gw.get('pass') is True and bool(gw.get('returncodes')) and all(x==0 for x in gw.get('returncodes',{}).values()),
      'accepted_phase4_index_exact':paths['phase4_index'].is_file() and sha(paths['phase4_index'])==PHASE4_INDEX,
      'historical_relocation_verification_46':hv.get('pass') is True and hv.get('check_count')==46 and hv.get('failed_checks')==[],
      'historical_workflow_zero':hw.get('pass') is True and bool(hw.get('returncodes')) and all(x==0 for x in hw.get('returncodes',{}).values()),
      'baseline_install_create_714':install.get('pass') is True and install.get('action_counts')=={'create':714} and install.get('mutation_count')==715,
      'engine_authority_pass':ea.get('pass') is True,
      'engine_path_corrected':str(ea.get('engine_path','')).endswith('recovery_engine_missing_leaf.py'),
      'engine_sha_exact':ea.get('engine_sha256')==ENGINE_SHA,
      'operations_sha_exact':ea.get('operations_sha256')==OPS_SHA,
      'patch_authority_pass':pa.get('pass') is True and pa.get('baseline_engine_override_count')==1 and pa.get('relocation_engine_override_count')==1 and pa.get('relocation_baseline_override_count')==1 and pa.get('relocation_engine_forward_count')==1,
      'machine_json_canonical':all(p.read_bytes()==canonical(values[n]) for n,p in paths.items() if n in values),
    }
    if len(checks)!=15: raise RuntimeError(len(checks))
    failed=sorted(k for k,v in checks.items() if not v)
    out={'schema_version':1,'pass':not failed,'check_count':15,'checks':checks,'failed_checks':failed,'missing_outputs':missing,'parse_errors':errors,'historical_observed':hv.get('observed'),'claim_boundary':{'proved':'The accepted corrected engine reproduced the historical 46-check complete-root relocation contract on Termux.','not_proved':'Cross-filesystem relocation and later lifecycle gates remain separate.'}}
    a.output.resolve().write_bytes(canonical(out)); print(json.dumps(out,indent=2,sort_keys=True)); return 0 if out['pass'] else 96
if __name__=='__main__': raise SystemExit(main())

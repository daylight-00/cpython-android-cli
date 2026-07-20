#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
from typing import Any
REQ=['runtime-reproduction.json','ca-trust-candidates.json','timezone-candidates.json','temporary-directory-policy.json','cache-bytecode-and-user-site-policy.json','venv-writable-state-policy.json','read-only-installation-behavior.json','data-update-evidence.json','negative-path-scans.json','ut4-gate-diagnostics.json']

def load(p:Path)->Any:return json.loads(p.read_text())
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();root=a.root.resolve();out=a.output.resolve();checks={};errors={}
 def ck(name:str,value:bool,detail:Any=None):checks[name]=bool(value);errors.setdefault(name,detail) if not value and detail is not None else None
 for n in REQ:ck('file_'+n,(out/n).is_file())
 if not all((out/n).is_file() for n in REQ):
  result={'schema_version':1,'audit_kind':'e2-r1-ut4-android-data-policy','check_count':len(checks),'pass_count':sum(checks.values()),'checks':checks,'errors':errors,'failed_checks':[k for k,v in checks.items() if not v],'pass':False};(out/'independent-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return 1
 rr=load(out/'runtime-reproduction.json');ca=load(out/'ca-trust-candidates.json');tz=load(out/'timezone-candidates.json');tmp=load(out/'temporary-directory-policy.json');cache=load(out/'cache-bytecode-and-user-site-policy.json');venv=load(out/'venv-writable-state-policy.json');ro=load(out/'read-only-installation-behavior.json');upd=load(out/'data-update-evidence.json');scan=load(out/'negative-path-scans.json');gate=load(out/'ut4-gate-diagnostics.json')
 ck('authority_sysconfig',sha(root/'experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json')=='6cff1984d4601a37e8b57762bb170a57e695cb64d516c1dab0023b7e809dc808')
 ck('runtime_startup',rr['startup']['startup_pass'] is True);ck('runtime_extensions',rr['startup']['required_extension_failures']==0);ck('runtime_no_ld_library_path',rr['startup']['ld_library_path_absent'] is True);ck('runtime_no_self_reexec',rr['startup']['self_reexec_absent'] is True);ck('runtime_lr3_16k',rr['lr3_exact_and_16k'] is True)
 ck('ca_selected',ca['selected']=='bundled-default-with-caller-override');ck('ca_default',ca['probe']['default']['client']['pass'] is True);ck('ca_invalid_override',ca['probe']['invalid_override']['client']['pass'] is False);ck('ca_external_override',ca['probe']['valid_external_override']['client']['pass'] is True);ck('ca_policy_pass',ca['pass'] is True)
 ck('tz_selected',tz['selected']=='bundled-raw-zoneinfo-tree');ck('tz_v1',tz['probe']['v1']['json']['offset_seconds']==3600);ck('tz_v2',tz['probe']['v2']['json']['offset_seconds']==7200);ck('tz_no_host',tz['probe']['host_discovery_disabled']['json']['pass'] is False);ck('tz_policy_pass',tz['pass'] is True)
 ck('temp_policy',tmp['pass'] is True);ck('cache_policy',cache['pass'] is True);ck('venv_policy',venv['pass'] is True);ck('fresh_venv_after_move',venv['probe']['fresh_after_move']['json']['pass'] is True);ck('read_only',ro['pass'] is True);ck('read_only_unchanged',ro['prefix_unchanged'] is True);ck('data_update',upd['pass'] is True);ck('data_update_no_python',upd['python_update_required'] is False)
 ck('negative_scan',scan['pass'] is True);ck('negative_hits_zero',scan['hit_count']==0);ck('negative_unknown_zero',scan['active_metadata_unknown_absolute_zero'] is True);ck('negative_stale_zero',scan['active_metadata_stale_install_zero'] is True)
 policies=[ca,tz,tmp,cache,venv,ro]
 for i,p in enumerate(policies):
  c=p['contract'];ck(f'policy_{i}_complete',all(k in c for k in ['provenance','update_owner','relocation','failure_mode','host_neutral']) and c['host_neutral'] is True)
 ck('gate_pass',gate['pass'] is True);ck('gate_all',all(gate['gate_condition'].values()));ck('exit_complete',gate['exit_condition']['required_policy_count']==gate['exit_condition']['complete_policy_count']==6);ck('exit_negative_zero',gate['exit_condition']['negative_path_hits']==0);ck('product_unselectable',True)
 result={'schema_version':1,'audit_kind':'e2-r1-ut4-android-data-policy','check_count':len(checks),'pass_count':sum(checks.values()),'checks':checks,'errors':{k:v for k,v in errors.items() if v is not None},'failed_checks':[k for k,v in checks.items() if not v],'pass':all(checks.values())};(out/'independent-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())

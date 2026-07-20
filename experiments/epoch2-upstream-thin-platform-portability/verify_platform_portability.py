#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from typing import Any
OUTPUT_REL='experiments/epoch2-upstream-thin-platform-portability';NEXT_ACTION='execute-e2-r1-ut7-upstream-evolution-and-maintenance-portability';NEXT_TASK='E2-R1-UT-7';AUTHORITY='platform-portability-authority.json'
PRIMARY=['current-device-probe.json','runtime-reproduction.json','environment-matrix.json','static-16k-matrix.json','runtime-platform-matrix.json','minimum-api-claim.json','supported-contexts.json','withheld-claims.json','ut6-gate-diagnostics.json','independent-audit.json']
SCRIPTS=['run_platform_portability_experiment.py','audit_platform_portability.py','verify_platform_portability.py','test_verify_platform_portability.py','finalize_platform_portability.py','run-ut6-platform-portability.sh']
NEW_DOCS=['README.md',*PRIMARY,AUTHORITY,'evidence-freeze.md']
FORBIDDEN_CLAIM_PATTERNS=[r'api\s*24\s*(is|as)\s*(the\s*)?(supported|minimum)',r'all\s+android',r'all\s+devices',r'16\s*ki?b\s+runtime\s+(supported|qualified)',r'non-termux\s+(supported|qualified)',r'root\s+(supported|qualified)',r'adb\s+(supported|qualified)']
def load(p:Path)->Any:return json.loads(p.read_text())
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def public_contract_scan(values:list[Any])->dict[str,Any]:
 text='\n'.join(json.dumps(v,sort_keys=True) for v in values);hits=[pat for pat in FORBIDDEN_CLAIM_PATTERNS if re.search(pat,text,re.I)];return {'pass':not hits,'hits':hits}
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=None);ap.add_argument('--output-dir',default=OUTPUT_REL);ap.add_argument('--expected-predecessor-head');ap.add_argument('--expected-predecessor-tree');a=ap.parse_args();root=(a.root if a.root is not None else Path.cwd()).resolve();out=root/a.output_dir;checks={};errors={}
 def ck(n:str,v:bool,d:Any='failed'):checks[n]=bool(v);errors.setdefault(n,str(d)) if not v else None
 try:
  device=load(out/'current-device-probe.json');repro=load(out/'runtime-reproduction.json');env=load(out/'environment-matrix.json');static=load(out/'static-16k-matrix.json');runtime=load(out/'runtime-platform-matrix.json');minimum=load(out/'minimum-api-claim.json');supported=load(out/'supported-contexts.json');withheld=load(out/'withheld-claims.json');gate=load(out/'ut6-gate-diagnostics.json');audit=load(out/'independent-audit.json');authority=load(out/AUTHORITY);state=load(root/'docs/current/STATE.json');task=load(root/'docs/current/AGENT_TASK.json');catalog=load(root/'docs/agent/TASK_CATALOG.json');registry=load(root/'docs/documentation/document-registry.json')
 except Exception as e:
  print(json.dumps({'pass':False,'check_count':0,'pass_count':0,'failed_checks':['load'],'errors':{'load':repr(e)},'checks':{}},indent=2,sort_keys=True));return 1
 ck('device-pass',device.get('pass') is True,device)
 ck('reproduction-pass',repro.get('pass') is True,repro)
 ck('environment-pass',env.get('pass') is True,env)
 ck('environment-current-single',len(env.get('current_assembly',[]))==1,env.get('current_assembly'))
 ck('environment-current-direct',env.get('current_assembly',[{}])[0].get('evidence_kind')=='direct-current-run',env.get('current_assembly'))
 ck('environment-historical-not-current',all(x.get('current_assembly') is False for x in env.get('related_historical_evidence',[])),env.get('related_historical_evidence'))
 ck('environment-api24-withheld',env.get('requested_boundaries',{}).get('minimum_claimed_api',{}).get('status','').startswith('withheld'),env)
 ck('environment-nontermux-withheld',env.get('requested_boundaries',{}).get('clean_non_termux_path',{}).get('status','').startswith('withheld'),env)
 ck('static-pass',static.get('pass') is True,static.get('summary'))
 ck('static-elf-counts',static.get('runtime_elf_count')==81 and static.get('wheel_elf_count')==1,static)
 ck('static-alignments',static.get('summary',{}).get('all_load_alignments_16k') is True,static.get('summary'))
 ck('static-offsets',static.get('summary',{}).get('all_segment_offsets_congruent_16k') is True,static.get('summary'))
 ck('static-identities',static.get('summary',{}).get('post_mutation_identity_matches')==81 and static.get('summary',{}).get('post_mutation_identity_expected')==81,static.get('summary'))
 ck('static-runpath-layout',static.get('summary',{}).get('post_runpath_layout_matches') is True,static.get('summary'))
 ck('static-selected-launcher-identity',static.get('summary',{}).get('selected_launcher_identity_match') is True,static.get('summary'))
 aliases={x.get('path'):x for x in static.get('symlink_aliases',[])};expected_aliases={'bin/python':'bin/python3.14','bin/python3':'bin/python3.14','lib/libsqlite3.so.0':'lib/libsqlite3_python.so'}
 ck('static-symlink-alias-count',static.get('runtime_elf_symlink_alias_count')==3 and len(aliases)==3,static.get('symlink_aliases'))
 ck('static-symlink-alias-paths',set(aliases)==set(expected_aliases),sorted(aliases))
 ck('static-symlink-alias-targets',all(aliases.get(k,{}).get('resolved_path')==v for k,v in expected_aliases.items()),aliases)
 ck('static-symlink-alias-identities',static.get('summary',{}).get('symlink_alias_inventory_complete') is True and static.get('summary',{}).get('symlink_alias_identity_matches')==3,static.get('summary'))
 ck('runtime-pass',runtime.get('pass') is True,runtime)
 cases={x.get('case'):x for x in runtime.get('cases',[])};required={'launcher-libpython-native-closure','clean-isolated-termux-extraction','whole-prefix-relocation','fresh-symlink-venv-after-relocation','native-extension-wheel-in-fresh-venv'}
 ck('runtime-case-set',required.issubset(cases),sorted(cases))
 for n in sorted(required):ck('runtime-pass:'+n,cases.get(n,{}).get('status')=='pass',cases.get(n))
 ck('runtime-pip-withheld',cases.get('selected-base-pip-path',{}).get('status')=='withheld-not-selected',cases.get('selected-base-pip-path'))
 ck('runtime-uv-withheld',cases.get('selected-uv-path',{}).get('status')=='withheld-not-selected',cases.get('selected-uv-path'))
 ck('minimum-withheld',minimum.get('status')=='withheld' and minimum.get('public_minimum_release_api') is None,minimum)
 ck('minimum-modern-not-proof',minimum.get('modern_device_used_as_minimum_proof') is False,minimum)
 ck('minimum-no-selection',minimum.get('epoch3_decision_made') is False,minimum)
 ck('supported-pass',supported.get('pass') is True and len(supported.get('public_claims',[]))==3,supported)
 ck('supported-boundaries',len(supported.get('explicit_boundaries',[]))>=4,supported)
 public_scan=public_contract_scan([minimum,supported]);ck('supported-public-contract-scan',public_scan['pass'],public_scan)
 ck('withheld-pass',withheld.get('pass') is True and len(withheld.get('claims',[]))>=9,withheld)
 claims={x.get('claim') for x in withheld.get('claims',[])}
 for c in ['Android API 24 minimum runtime support','Any minimum release API','Non-Termux Android app namespace support','ADB shell support','root execution support','emulator support','x86_64, armeabi-v7a, or other ABI support','all Android versions, OEMs, kernels, or devices','base pip or uv product inclusion']:ck('withheld:'+c,c in claims,claims)
 ck('gate-pass',gate.get('pass') is True,gate)
 ck('gate-failed-empty',gate.get('failed_gate_conditions')==[],gate)
 ck('gate-no-modern-inference',gate.get('gate_condition',{}).get('no_modern_as_minimum_inference') is True,gate)
 ck('gate-no-broad',gate.get('gate_condition',{}).get('no_broad_platform_claims') is True,gate)
 ck('gate-minimum-not-claimed',gate.get('exit_condition',{}).get('minimum_release_api_claimed') is False,gate)
 ck('gate-negative-scan-scope',gate.get('negative_claim_scan',{}).get('scope')==['minimum-api-claim.json','supported-contexts.json'],gate.get('negative_claim_scan'))
 ck('audit-pass',audit.get('pass') is True and audit.get('pass_count')==audit.get('check_count'),audit)
 ck('authority-kind',authority.get('authority_kind')=='e2-r1-ut6-platform-portability',authority.get('authority_kind'))
 ck('authority-status',authority.get('status')=='frozen-pass-bounded-platform-claims-and-explicit-withholding',authority.get('status'))
 ck('authority-next-action',authority.get('next_action_class')==NEXT_ACTION,authority.get('next_action_class'))
 ck('authority-minimum-false',authority.get('claim_boundary',{}).get('minimum_release_api') is False,authority.get('claim_boundary'))
 ck('authority-static16k-true',authority.get('claim_boundary',{}).get('static_16k_compatibility') is True,authority.get('claim_boundary'))
 ck('authority-static-alias-inventory',authority.get('static_16k',{}).get('symlink_alias_inventory_complete') is True and authority.get('static_16k',{}).get('selected_launcher_identity_match') is True,authority.get('static_16k'))
 ck('authority-no-broad-device',authority.get('claim_boundary',{}).get('broad_device_qualification') is False,authority.get('claim_boundary'))
 ck('authority-no-selection',authority.get('epoch3_selection_made') is False,authority)
 if a.expected_predecessor_head:ck('authority-predecessor-head',authority.get('predecessor',{}).get('commit')==a.expected_predecessor_head,authority.get('predecessor'))
 if a.expected_predecessor_tree:ck('authority-predecessor-tree',authority.get('predecessor',{}).get('tree')==a.expected_predecessor_tree,authority.get('predecessor'))
 for n in [*PRIMARY,*SCRIPTS]:
  p=out/n;ck('file-present:'+n,p.is_file(),p)
  if p.is_file():ck('file-identity:'+n,authority.get('file_identities',{}).get(n)==sha(p),(authority.get('file_identities',{}).get(n),sha(p)))
 auth_sha=sha(out/AUTHORITY)
 ck('state-revision',state.get('state_revision')==13,state.get('state_revision'))
 ck('state-next-action',state.get('next_action_class')==NEXT_ACTION,state.get('next_action_class'))
 ck('state-gate-ready',state.get('program',{}).get('gate',{}).get('id')=='E2-R1/UT-7' and state.get('program',{}).get('gate',{}).get('status')=='ready',state.get('program'))
 acc=[x for x in state.get('accepted_authorities',[]) if x.get('path')==f'{OUTPUT_REL}/{AUTHORITY}'];ck('state-authority-binding',len(acc)==1 and acc[0].get('sha256')==auth_sha,acc)
 ck('state-risk-ut7',any('UT-7' in x for x in state.get('unresolved_risks',[])),state.get('unresolved_risks'))
 ck('task-state-revision',task.get('state_revision')==13,task.get('state_revision'))
 ck('task-id',task.get('task',{}).get('id')==NEXT_TASK,task.get('task'))
 ck('task-action',task.get('task',{}).get('action_class')==NEXT_ACTION,task.get('task'))
 ck('task-gate-ready',task.get('program_gate',{}).get('id')=='E2-R1/UT-7' and task.get('program_gate',{}).get('status')=='ready',task.get('program_gate'))
 req=[x for x in task.get('required_authorities',[]) if x.get('path')==f'{OUTPUT_REL}/{AUTHORITY}'];ck('task-authority-binding',len(req)==1 and req[0].get('sha256')==auth_sha,req)
 ut7=next((x for x in catalog.get('tasks',[]) if x.get('task_id')==NEXT_TASK),None);ck('catalog-ut7-exists',ut7 is not None,ut7)
 if ut7:
  ck('catalog-ut7-ready',ut7.get('activation',{}).get('status')=='ready' and ut7.get('activation',{}).get('accepted_authority_sha256')==auth_sha,ut7.get('activation'))
  ck('catalog-ut7-contract',ut7.get('completion_contract',{}).get('pass',{}).get('successor_task_id')=='E2-R1-API36-1',ut7.get('completion_contract'))
 ck('catalog-api36-exists',any(x.get('task_id')=='E2-R1-API36-1' for x in catalog.get('tasks',[])),None)
 docs={x.get('path') for x in registry.get('documents',[])}
 for n in NEW_DOCS:ck('registry:'+n,f'{OUTPUT_REL}/{n}' in docs,docs)
 ck('registry-next-action',registry.get('basis',{}).get('next_action_class')==NEXT_ACTION,registry.get('basis'))
 failed=[k for k,v in checks.items() if not v];result={'schema_version':1,'verifier_kind':'ut6-focused','pass':not failed,'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':failed,'errors':{k:v for k,v in errors.items() if k in failed},'checks':checks};print(json.dumps(result,indent=2,sort_keys=True));return 0 if not failed else 1
if __name__=='__main__':raise SystemExit(main())

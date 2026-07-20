#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any

def load(p:Path)->Any:return json.loads(p.read_text())
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();o=a.output.resolve();errors={};checks={}
 def ck(name:str,val:bool,detail:Any=None):checks[name]=bool(val);errors.setdefault(name,detail) if not val else None
 env=load(o/'environment-matrix.json');static=load(o/'static-16k-matrix.json');runtime=load(o/'runtime-platform-matrix.json');minimum=load(o/'minimum-api-claim.json');supported=load(o/'supported-contexts.json');withheld=load(o/'withheld-claims.json');gate=load(o/'ut6-gate-diagnostics.json');repro=load(o/'runtime-reproduction.json');device=load(o/'current-device-probe.json')
 ck('device-probe-pass',device.get('pass') is True,device)
 ck('device-api-at-least-package-floor',isinstance(device.get('android_api'),int) and device['android_api']>=24,device.get('android_api'))
 ck('device-aarch64',device.get('machine') in {'aarch64','arm64'},device.get('machine'))
 ck('environment-pass',env.get('pass') is True,env)
 ck('current-environment-single',len(env.get('current_assembly',[]))==1,env.get('current_assembly'))
 ck('current-environment-direct',env['current_assembly'][0].get('evidence_kind')=='direct-current-run',env['current_assembly'][0])
 ck('current-environment-current-assembly',env['current_assembly'][0].get('current_assembly') is True,env['current_assembly'][0])
 ck('historical-environments-two',len(env.get('related_historical_evidence',[]))==2,env.get('related_historical_evidence'))
 ck('historical-not-current',all(x.get('current_assembly') is False for x in env.get('related_historical_evidence',[])),env.get('related_historical_evidence'))
 ck('api24-request-withheld',env['requested_boundaries']['minimum_claimed_api'].get('status','').startswith('withheld'),env['requested_boundaries']['minimum_claimed_api'])
 ck('termux-direct-pass',env['requested_boundaries']['termux'].get('status')=='pass',env['requested_boundaries']['termux'])
 ck('non-termux-withheld',env['requested_boundaries']['clean_non_termux_path'].get('status','').startswith('withheld'),env['requested_boundaries']['clean_non_termux_path'])
 ck('static-pass',static.get('pass') is True,static.get('summary'))
 ck('static-runtime-elf-count',static.get('runtime_elf_count')==81,static.get('runtime_elf_count'))
 ck('static-wheel-elf-count',static.get('wheel_elf_count')==1,static.get('wheel_elf_count'))
 ck('static-readelf-pass',static['summary'].get('all_readelf_pass') is True,static['summary'])
 ck('static-alignments-16k',static['summary'].get('all_load_alignments_16k') is True,static['summary'])
 ck('static-offset-congruence',static['summary'].get('all_segment_offsets_congruent_16k') is True,static['summary'])
 ck('static-post-mutation-count',static['summary'].get('post_mutation_identity_matches')==81,static['summary'])
 ck('static-post-mutation-expected',static['summary'].get('post_mutation_identity_expected')==81,static['summary'])
 ck('static-post-runpath',static['summary'].get('post_runpath_layout_matches') is True,static['summary'])
 ck('static-selected-launcher-identity',static['summary'].get('selected_launcher_identity_match') is True,static['summary'])
 aliases={x.get('path'):x for x in static.get('symlink_aliases',[])};expected_aliases={'bin/python':'bin/python3.14','bin/python3':'bin/python3.14','lib/libsqlite3.so.0':'lib/libsqlite3_python.so'}
 ck('static-symlink-alias-count',static.get('runtime_elf_symlink_alias_count')==3 and len(aliases)==3,static.get('symlink_aliases'))
 ck('static-symlink-alias-paths',set(aliases)==set(expected_aliases),sorted(aliases))
 ck('static-symlink-alias-targets',all(aliases.get(k,{}).get('resolved_path')==v for k,v in expected_aliases.items()),aliases)
 ck('static-symlink-alias-identities',static['summary'].get('symlink_alias_inventory_complete') is True and static['summary'].get('symlink_alias_identity_matches')==3,static['summary'])
 ck('static-relocation-sections-inventoried',static['summary'].get('relocation_section_inventory_complete') is True,static['summary'])
 ck('runtime-pass',runtime.get('pass') is True,runtime)
 cases={x['case']:x for x in runtime.get('cases',[])}
 required={'launcher-libpython-native-closure','clean-isolated-termux-extraction','whole-prefix-relocation','fresh-symlink-venv-after-relocation','native-extension-wheel-in-fresh-venv'}
 ck('runtime-required-case-set',required.issubset(cases),sorted(cases))
 for name in sorted(required):ck('runtime-pass:'+name,cases.get(name,{}).get('status')=='pass',cases.get(name))
 ck('runtime-pip-withheld',cases.get('selected-base-pip-path',{}).get('status')=='withheld-not-selected',cases.get('selected-base-pip-path'))
 ck('runtime-uv-withheld',cases.get('selected-uv-path',{}).get('status')=='withheld-not-selected',cases.get('selected-uv-path'))
 ck('minimum-pass',minimum.get('pass') is True,minimum)
 ck('minimum-public-none',minimum.get('public_minimum_release_api') is None,minimum)
 ck('minimum-status-withheld',minimum.get('status')=='withheld',minimum)
 ck('minimum-package-floor-24',minimum.get('package_declared_floor_api')==24,minimum)
 ck('minimum-modern-not-proof',minimum.get('modern_device_used_as_minimum_proof') is False,minimum)
 ck('minimum-no-epoch3-decision',minimum.get('epoch3_decision_made') is False,minimum)
 ck('supported-pass',supported.get('pass') is True,supported)
 ck('supported-public-claim-count',len(supported.get('public_claims',[]))==3,supported.get('public_claims'))
 ck('supported-explicit-boundaries',len(supported.get('explicit_boundaries',[]))>=4,supported.get('explicit_boundaries'))
 ck('supported-no-epoch3-selection',supported.get('epoch3_selection_made') is False,supported)
 ck('withheld-pass',withheld.get('pass') is True,withheld)
 claims=[x.get('claim') for x in withheld.get('claims',[])]
 for expected in ['Android API 24 minimum runtime support','Any minimum release API','Non-Termux Android app namespace support','ADB shell support','root execution support','emulator support','x86_64, armeabi-v7a, or other ABI support','all Android versions, OEMs, kernels, or devices','base pip or uv product inclusion']:
  ck('withheld:'+expected,expected in claims,claims)
 ck('reproduction-pass',repro.get('pass') is True,repro)
 ck('gate-pass',gate.get('pass') is True,gate)
 ck('gate-failed-empty',gate.get('failed_gate_conditions')==[],gate.get('failed_gate_conditions'))
 ck('gate-no-modern-inference',gate.get('gate_condition',{}).get('no_modern_as_minimum_inference') is True,gate)
 ck('gate-no-broad-claims',gate.get('gate_condition',{}).get('no_broad_platform_claims') is True,gate)
 ck('gate-no-minimum-claim',gate.get('exit_condition',{}).get('minimum_release_api_claimed') is False,gate)
 ck('gate-negative-hits-zero',gate.get('exit_condition',{}).get('negative_claim_hits')==0,gate)
 ck('gate-negative-scan-scope',gate.get('negative_claim_scan',{}).get('scope')==['minimum-api-claim.json','supported-contexts.json'],gate.get('negative_claim_scan'))
 failed=[k for k,v in checks.items() if not v];result={'schema_version':1,'audit_kind':'ut6-independent','check_count':len(checks),'pass_count':sum(checks.values()),'checks':checks,'failed_checks':failed,'errors':{k:v for k,v in errors.items() if k in failed},'pass':not failed};(o/'independent-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if not failed else 1
if __name__=='__main__':raise SystemExit(main())

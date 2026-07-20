#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any
FILES=['input-identities.json','patch-update-rehearsal.json','configuration-only-delta.json','layout-and-extension-delta.json','runpath-and-sysconfig-delta.json','wheel-and-pip-delta.json','python315-preview-delta.json','security-ownership.json','ut7-gate-diagnostics.json']
def load(p:Path)->Any:return json.loads(p.read_text())
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();o=a.output.resolve();d={n:load(o/n) for n in FILES};checks={};errors={}
 def ck(name:str,cond:bool,detail:Any=None):checks[name]=bool(cond);errors[name]=detail
 i=d['input-identities.json'];r=d['patch-update-rehearsal.json'];c=d['configuration-only-delta.json'];l=d['layout-and-extension-delta.json'];s=d['runpath-and-sysconfig-delta.json'];w=d['wheel-and-pip-delta.json'];p=d['python315-preview-delta.json'];sec=d['security-ownership.json'];g=d['ut7-gate-diagnostics.json']
 ck('input-pass',i.get('pass') is True,i)
 ck('input-count',len(i.get('inputs',[]))==3,i.get('inputs'))
 roles=[x.get('role') for x in i.get('inputs',[])];ck('input-roles',roles==['current-accepted','official-patch-predecessor','python315-preview'],roles)
 versions=[x.get('version') for x in i.get('inputs',[])];ck('input-versions',versions==['3.14.6','3.14.5','3.15.0b4'],versions)
 ck('sigstore-bound',i.get('all_sigstore_digest_bound') is True,i)
 ck('owner-inputs-bound',i.get('all_exact_owner_inputs') is True,i)
 ck('input-preview-no-release',i.get('preview_release_claim') is False,i)
 for x in i.get('inputs',[]):
  ck('input-sha:'+x.get('role','?'),isinstance(x.get('sha256'),str) and len(x['sha256'])==64,x)
  ck('input-size:'+x.get('role','?'),isinstance(x.get('size'),int) and x['size']>20_000_000,x)
  ck('input-url:'+x.get('role','?'),str(x.get('url','')).startswith('https://www.python.org/ftp/python/'),x)
  ck('input-sigstore-match:'+x.get('role','?'),x.get('sigstore_digest_match') is True,x)
  ck('input-owner-mode:'+x.get('role','?'),x.get('acquisition_scope')=='bounded-owner-local' and x.get('exact_identity_verified') is True and x.get('acquisition_mode') in {'owner-local-cache-reuse','owner-local-bounded-download'} and isinstance(x.get('network_acquisition'),bool),x)
 ck('rehearsal-pass',r.get('pass') is True,r)
 ck('rehearsal-version-pair',r.get('from_version')=='3.14.5' and r.get('to_version')=='3.14.6',r)
 ck('rehearsal-identity-change-list',r.get('expected_identity_changes')==['version','URL','checksum','upstream metadata','expected package identity'],r.get('expected_identity_changes'))
 ck('rehearsal-all-other-recorded',r.get('every_non_identity_delta_recorded') is True,r)
 delta=r.get('all_other_normalized_file_changes',{});ck('rehearsal-delta-shape',all(k in delta for k in ['added','removed','changed','added_count','removed_count','changed_count']),delta)
 ck('rehearsal-qualification-replay',len(r.get('qualification_replay_required',[]))==6,r.get('qualification_replay_required'))
 ck('config-pass',c.get('pass') is True,c)
 ck('config-candidate-explicit',isinstance(c.get('patch_update',{}).get('configuration_only_candidate'),bool),c)
 ck('config-delta-count-explicit',isinstance(c.get('patch_update',{}).get('non_configuration_delta_count'),int),c)
 ck('config-identity-fields-complete',c.get('patch_update',{}).get('configuration_changes')==['version','URL','checksum','upstream metadata','expected package identity'],c)
 assumptions=c.get('version_specific_assumptions',{});ck('assumptions-pass',assumptions.get('pass') is True,assumptions)
 ck('assumptions-scanned',assumptions.get('files_scanned',0)>0,assumptions)
 ck('assumptions-literals',assumptions.get('files_with_version_literals',0)>0,assumptions)
 ck('assumptions-parameterize',assumptions.get('parameterization_required') is True,assumptions)
 ck('config-no-qualification-bypass',c.get('automation_boundary',{}).get('configuration_only_may_not_bypass_runtime_qualification') is True,c)
 ck('layout-pass',l.get('pass') is True,l)
 for scope in ['patch_update','python315_preview']:
  x=l.get(scope,{});ck('layout-complete:'+scope,all(k in x for k in ['normalized_layout','extension_modules','shared_libraries','raw_counts']),x)
  for name in ['normalized_layout','extension_modules','shared_libraries']:
   y=x.get(name,{});ck(f'layout-delta-shape:{scope}:{name}',all(k in y for k in ['added','removed','added_count','removed_count']),y)
 ck('runpath-sysconfig-pass',s.get('pass') is True,s)
 for scope in ['patch_update','python315_preview']:
  x=s.get(scope,{});ck('runpath-sysconfig-complete:'+scope,all(k in x for k in ['sysconfig_keys','sysconfig_selected','sysconfig_change_classes','runpaths']),x)
  ck('sysconfig-classification:'+scope,sum(x.get('sysconfig_change_classes',{}).values())==x.get('sysconfig_selected',{}).get('changed_count'),x)
 ck('loader-authority-binding',len(s.get('selected_launcher_authority_sha256',''))==64,s)
 ck('sysconfig-authority-binding',len(s.get('sysconfig_authority_sha256',''))==64,s)
 ck('wheel-pip-pass',w.get('pass') is True,w)
 ck('wheel-patch-complete',all(k in w.get('patch_update',{}) for k in ['wheels','python_json','pip_strategy','compatibility_qualification_required']),w)
 ck('wheel-preview-complete',all(k in w.get('python315_preview',{}) for k in ['wheels','python_json','pip_strategy','expected_abi_tag_family','release_or_product_selection']),w)
 ck('wheel-preview-cp315',w.get('python315_preview',{}).get('expected_abi_tag_family')=='cp315',w)
 ck('wheel-no-product-selection',w.get('python315_preview',{}).get('release_or_product_selection') is False,w)
 ck('pip-not-selected',w.get('ut5_base_pip_selected') is False,w)
 ck('uv-not-selected',w.get('ut5_uv_selected') is False,w)
 ck('preview-pass',p.get('pass') is True,p)
 ck('preview-version',p.get('preview_version')=='3.15.0b4',p)
 ck('preview-only',p.get('preview_only') is True,p)
 ck('preview-no-release',p.get('release_claim') is False,p)
 ck('preview-no-runtime-support',p.get('runtime_support_claim') is False,p)
 ck('preview-no-product-selection',p.get('product_selection') is False,p)
 for k in ['package_and_prefix_layout','launcher_and_getpath','sysconfig','extension_surface','wheel_and_abi_tags','pidfd_related_subprocess_behavior','pip_strategy','version_specific_transformations','all_normalized_layout_changes']:
  ck('preview-role:'+k,k in p,p)
 ck('preview-pidfd-static',isinstance(p.get('pidfd_related_subprocess_behavior',{}).get('static_evidence'),list),p)
 ck('preview-pidfd-not-runtime',p.get('pidfd_related_subprocess_behavior',{}).get('direct_runtime_qualified') is False,p)
 ck('preview-evidence-not-release',p.get('evidence_not_release_claim') is True,p)
 ck('security-pass',sec.get('pass') is True,sec)
 ck('security-owner-count',len(sec.get('ownership',[]))>=5,sec)
 owners={x.get('owner') for x in sec.get('ownership',[])};ck('security-upstream-owner','CPython upstream' in owners,owners)
 ck('security-local-owner','local cpython-android-cli maintainers' in owners,owners)
 ck('maintenance-roles',sec.get('maintenance_model',{}).get('minimum_roles')==['implementation maintainer','independent reviewer'],sec)
 ck('maintenance-steps',len(sec.get('maintenance_model',{}).get('patch_update_steps',[]))==5,sec)
 ck('automatic-release-false',sec.get('maintenance_model',{}).get('automatic_release_on_green') is False,sec)
 ck('gate-pass',g.get('pass') is True,g)
 ck('gate-failed-empty',g.get('failed_gate_conditions')==[],g)
 expected={'official_inputs_sigstore_bound','patch_update_rehearsal_complete','configuration_only_boundary_explicit','layout_and_extension_delta_complete','runpath_and_sysconfig_delta_complete','wheel_and_pip_delta_complete','python315_preview_delta_complete','preview_release_claim_absent','version_specific_assumptions_explicit','security_ownership_explicit','update_burden_explicit','authority_bindings_exact','epoch3_selection_absent'}
 ck('gate-condition-set',set(g.get('gate_condition',{}))==expected,g.get('gate_condition'))
 ck('gate-all-true',all(v is True for v in g.get('gate_condition',{}).values()),g.get('gate_condition'))
 ck('gate-preview-false',g.get('exit_condition',{}).get('preview_release_claim') is False,g)
 ck('gate-epoch3-false',g.get('exit_condition',{}).get('epoch3_selection') is False,g)
 failed=[k for k,v in checks.items() if not v];result={'schema_version':1,'audit_kind':'ut7-independent','check_count':len(checks),'pass_count':sum(checks.values()),'checks':checks,'failed_checks':failed,'errors':{k:errors[k] for k in failed},'pass':not failed};dump=lambda p,v:p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');dump(o/'independent-audit.json',result);print(json.dumps(result,indent=2,sort_keys=True));return 0 if not failed else 1
if __name__=='__main__':raise SystemExit(main())

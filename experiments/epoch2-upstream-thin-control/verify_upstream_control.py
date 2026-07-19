#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

REQUIRED = {
 'gate-contract':'gate-contract.json','upstream-input-manifest':'upstream-input-manifest.json',
 'package-and-file-hashes':'package-and-file-hashes.json','elf-and-extension-inventory':'elf-and-extension-inventory.json',
 'dependency-provider-map':'dependency-provider-map.json','sysconfig-census':'sysconfig-census.json',
 'package-layout-map':'package-layout-map.json','provenance-map':'provenance-map.json','producer-delta':'producer-delta.json',
 'independent-audit':'independent-audit.json','machine-authority':'upstream-control-authority.json','evidence-freeze':'evidence-freeze.md',
}
FORBIDDEN={'docs/current/STATE.json','docs/current/AGENT_TASK.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'}

def load(p: Path): return json.loads(p.read_text(encoding='utf-8'))
def sha(p: Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()

def verify(root: Path, output_dir: str, archive: Path|None=None, repository_state: bool=False):
 out=root/output_dir; checks={}; errors={}
 def ck(n,v,e=''): checks[n]=bool(v); errors.update({n:e} if not v and e else {})
 missing=[f for f in REQUIRED.values() if not (out/f).is_file()]; ck('required_roles',not missing,','.join(missing))
 docs={}
 try:
  for role,f in REQUIRED.items():
   if f.endswith('.json') and (out/f).is_file(): docs[role]=load(out/f)
  ck('parse',True)
 except Exception as e: ck('parse',False,str(e))
 m=docs.get('upstream-input-manifest',{}); h=docs.get('package-and-file-hashes',{}); e=docs.get('elf-and-extension-inventory',{}); d=docs.get('dependency-provider-map',{}); s=docs.get('sysconfig-census',{}); l=docs.get('package-layout-map',{}); p=docs.get('provenance-map',{}); delta=docs.get('producer-delta',{}); audit=docs.get('independent-audit',{}); auth=docs.get('machine-authority',{}); gate=docs.get('gate-contract',{})
 ck('gate_identity',gate.get('gate_id')=='E2-R1/UT-0' and gate.get('work_class')=='L')
 roles=set(gate.get('required_roles',[])); ck('gate_roles',set(REQUIRED).issubset(roles))
 ck('input_identity',m.get('version')=='3.14.6' and m.get('target')=='aarch64-linux-android' and isinstance(m.get('minimum_android_api'),int) and m.get('sha256')==m.get('expected_sha256')==h.get('package_sha256'))
 ck('input_checks',bool(m.get('identity_checks')) and all(m['identity_checks'].values()))
 if archive is not None: ck('archive_readback',archive.is_file() and sha(archive)==m.get('sha256'))
 members=h.get('members',[]); ck('member_inventory',h.get('archive_member_count')==len(members)>100 and len({q.get('path') for q in members})==len(members))
 ck('no_mutation_fingerprint',h.get('extraction_byte_mismatch_paths')==[] and isinstance(h.get('archive_member_manifest_sha256'),str) and isinstance(h.get('prefix_snapshot_sha256'),str))
 elfs=e.get('elf_objects',[]); ck('elf_inventory',e.get('elf_count')==len(elfs)>0 and e.get('native_extension_count')==len(e.get('native_extensions',[]))>0)
 ck('elf_target',all('AArch64' in (q.get('machine') or '') for q in elfs))
 ck('dependency_closure',d.get('unresolved_edges')==[] and d.get('unclassified_packaged_elf')==[])
 ck('inherited_dependencies',any(q.get('classification')=='beeware-inherited-dependency' for q in d.get('dependency_products',[])))
 ck('sysconfig_census',s.get('selected_version')=='3.14.6' and s.get('selected_target')=='aarch64-linux-android' and s.get('selected_minimum_android_api')==m.get('minimum_android_api') and bool(s.get('build_details')))
 ck('layout',l.get('has_prefix_root') is True and l.get('prefix_member_count',0)>100 and bool(l.get('license_paths')))
 ck('provenance',p.get('provenance_gaps')==[] and p.get('patches',{}).get('project_local_patches')==[] and p.get('patches',{}).get('binary_mutations')==[])
 ck('producer_delta',delta.get('official',{}).get('package_sha256')==m.get('sha256') and delta.get('comparison_boundary','').startswith('official binary-derived control') and 'runtime execution' in delta.get('non_claims',[]))
 ck('audit',audit.get('pass') is True and audit.get('failed_checks')==[] and audit.get('blockers')==[])
 ids=auth.get('file_identities',{}); idok=bool(ids)
 for f,digest in ids.items():
  if not (out/f).is_file() or sha(out/f)!=digest: idok=False; break
 ck('authority_file_identities',idok)
 ck('authority_status',auth.get('status')=='frozen-pass-exact-official-upstream-control' and auth.get('official_input',{}).get('sha256')==m.get('sha256'))
 ck('authority_claim_boundary',auth.get('claim_boundary',{}).get('official_upstream_identity') is True and auth.get('claim_boundary',{}).get('android_runtime') is False and auth.get('claim_boundary',{}).get('publication') is False)
 ck('authority_no_live_binding',not(set(ids)&FORBIDDEN))
 authority_sha=sha(out/'upstream-control-authority.json') if (out/'upstream-control-authority.json').is_file() else ''
 freeze=(out/'evidence-freeze.md').read_text(encoding='utf-8') if (out/'evidence-freeze.md').is_file() else ''
 ck('evidence_freeze_binding',authority_sha and authority_sha in freeze and m.get('sha256','') in freeze)
 if repository_state:
  try:
   state=load(root/'docs/current/STATE.json'); catalog=load(root/'docs/agent/TASK_CATALOG.json'); reg=load(root/'docs/documentation/document-registry.json')
   protocol_path=root/'docs/agent/SESSION_PROTOCOL.md'; protocol=protocol_path.read_text(encoding='utf-8')
   protocol_revision_match=re.search(r'^> \*\*Revision:\*\* (\d+)\s*$',protocol,re.M)
   protocol_revision=int(protocol_revision_match.group(1)) if protocol_revision_match else None
   ck('transport_directionality',all(q in protocol for q in ['agent → owner','owner → agent','owner uploads one complete result archive and sidecar with `rclone`','fetches the exact raw bytes through the Google Drive connector','Expose the exact artifact under `/mnt/data`','do not retry']))
   ck('session_protocol_identity',protocol_revision==2 and state.get('agent_onboarding',{}).get('session_protocol_revision')==2 and state.get('session_protocol',{}).get('revision')==2 and state.get('session_protocol',{}).get('sha256')==sha(protocol_path))
   action='execute-e2-r1-ut1-astral-artifact-and-metadata-prototype'
   actions=[state.get('next_action_class'),state.get('program',{}).get('next_action_class'),state.get('control_work',{}).get('next_action_class'),state.get('control_work',{}).get('resume_program_action_class')]
   ck('state_action',len(set(actions))==1 and actions[0]==action)
   ck('state_gate',state.get('program',{}).get('gate',{}).get('id')=='E2-R1/UT-1' and state.get('program',{}).get('gate',{}).get('status')=='ready')
   a=[q for q in state.get('accepted_authorities',[]) if q.get('id')=='e2-r1-ut0-exact-official-upstream-control']; ck('state_authority',len(a)==1 and a[0].get('sha256')==authority_sha)
   ck('catalog_identity',state.get('task_catalog',{}).get('sha256')==sha(root/'docs/agent/TASK_CATALOG.json'))
   ut1=[q for q in catalog.get('tasks',[]) if q.get('task_id')=='E2-R1-UT-1']; ut2=[q for q in catalog.get('tasks',[]) if q.get('task_id')=='E2-R1-UT-2']
   ck('ut1_ready',len(ut1)==1 and ut1[0].get('activation',{}).get('status')=='ready' and bool(ut1[0].get('completion_contract')))
   ck('ut2_cataloged',len(ut2)==1 and ut2[0].get('activation',{}).get('status')=='blocked-on-predecessor-authority')
   tracked=subprocess.check_output(['git','-C',str(root),'ls-files','--','*.md','*.json'],text=True).splitlines(); rpaths=[q.get('path') for q in reg.get('documents',[])]
   ck('registry_coverage',sorted(tracked)==sorted(rpaths) and len(rpaths)==len(set(rpaths)))
   rr=subprocess.run([sys.executable,str(root/'experiments/agent-task-completion/render-document-views.py'),'--root',str(root),'--check'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   ck('generated_views',rr.returncode==0,rr.stdout+rr.stderr)
   on=subprocess.run([sys.executable,str(root/'tools/agent_onboard.py'),'--root',str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   ck('onboarding_route',on.returncode==0,on.stdout+on.stderr)
  except Exception as ex: ck('repository_state_parse',False,str(ex))
 failed=[k for k,v in checks.items() if not v]
 return {'schema_version':1,'verifier_kind':'e2-r1-ut0-exact-official-upstream-control','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--output-dir',default='experiments/epoch2-upstream-thin-control'); ap.add_argument('--archive'); ap.add_argument('--repository-state',action='store_true'); x=ap.parse_args()
 r=verify(Path(x.root).resolve(),x.output_dir,Path(x.archive).resolve() if x.archive else None,x.repository_state); print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r['pass'] else 1
if __name__=='__main__': sys.exit(main())

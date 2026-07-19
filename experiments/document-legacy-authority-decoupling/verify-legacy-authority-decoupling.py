#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,subprocess,sys
from pathlib import Path
REG=Path('docs/documentation/document-registry.json');STATE=Path('docs/current/STATE.json');MAP=Path('docs/documentation/legacy-authority-decoupling-map.json');RENDER=Path('experiments/document-legacy-authority-decoupling/render-document-views.py');RESOLVE=Path('experiments/document-legacy-authority-decoupling/verify-legacy-binding-resolution.py')
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def tracked(root):
 raw=subprocess.check_output(['git','ls-files','-z','--','*.md','*.json'],cwd=root);return {x.decode() for x in raw.split(b'\0') if x}
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default='.');a.add_argument('--render-result');a.add_argument('--binding-result');x=a.parse_args();r=Path(x.root).resolve();checks={};err={}
 def ck(n,v,e=''):checks[n]=bool(v);err.update({n:e} if not v and e else {})
 try:reg=load(r/REG);s=load(r/STATE);m=load(r/MAP);ck('parse',True)
 except Exception as e:reg={};s={};m={};ck('parse',False,str(e))
 t=tracked(r);docs=reg.get('documents',[]);rp={d.get('path') for d in docs if isinstance(d,dict)};by={d.get('path'):d for d in docs if isinstance(d,dict)}
 ck('registry_coverage',t==rp,f'missing={sorted(t-rp)} extra={sorted(rp-t)}')
 ck('registry_identity',reg.get('schema_version')==5 and reg.get('schema_path')=='docs/documentation/document-registry-v5.schema.json' and reg.get('basis',{}).get('migration_complete') is True)
 ck('state_identity',s.get('schema_version')==4 and s.get('schema_path')=='docs/current/STATE-v4.schema.json' and s.get('state_revision')==4)
 ck('predecessor',s.get('predecessor')=={'commit':'d201957a11861147bdbe11b6a91bf68fb6714a4d','tree':'1c0c692d7763487ad2ba0d91a7f2bf04b6e0b423'} and m.get('predecessor')=={'commit':'d201957a11861147bdbe11b6a91bf68fb6714a4d','tree':'1c0c692d7763487ad2ba0d91a7f2bf04b6e0b423'})
 c=s.get('control_work',{});ck('migration_closed',c.get('completed_phase')==5 and c.get('next_phase') is None and c.get('migration_complete') is True and c.get('status')=='completed')
 ck('program_resumed',s.get('next_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control' and s.get('program',{}).get('next_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control' and s.get('program',{}).get('gate',{}).get('id')=='E2-R1/UT-0')
 ck('legacy_risk_removed',not any('legacy live-document' in str(z).lower() for z in s.get('unresolved_risks',[])))
 ck('claim_boundary',s.get('claim_boundaries')=={'dual_real_device_aarch64_termux_compatibility':True,'emulator_qualified':False,'epoch3_feature_selection_started':False,'publication_authorized':False,'selectable':False})
 ck('active_plan_preserved',s.get('active_plan',{}).get('path')=='docs/roadmap/EPOCH2_PROGRAM_PLAN.md')
 ck('navigation_target_count',s.get('navigation',{}).get('target_count')==15 and len(s.get('render_targets',{}).get('navigation',[]))==15)
 if x.render_result:
  try:z=load(Path(x.render_result));ck('generated_views',z.get('pass') is True and z.get('target_count')==19)
  except Exception as e:ck('generated_views',False,str(e))
 else:
  p=subprocess.run([sys.executable,str(r/RENDER),'--root',str(r),'--check'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);ck('generated_views',p.returncode==0,p.stderr or p.stdout)
 if x.binding_result:
  try:z=load(Path(x.binding_result));ck('binding_resolution',z.get('pass') is True and z.get('check_count')==12 and z.get('pass_count')==12)
  except Exception as e:ck('binding_resolution',False,str(e))
 else:
  q=subprocess.run([sys.executable,str(r/RESOLVE),'--root',str(r)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);ck('binding_resolution',q.returncode==0,q.stderr or q.stdout)
 ck('map_registered',by.get('docs/documentation/legacy-authority-decoupling-map.json',{}).get('lifecycle_class')=='FROZEN_AUTHORITY')
 snaps=[z.get('snapshot_path') for z in m.get('bindings',[])];ck('snapshots_registered',len(snaps)==24 and all(by.get(p,{}).get('lifecycle_class')=='HISTORICAL_SNAPSHOT' and by.get(p,{}).get('machine_binding_policy')=='allowed-immutable-compatibility-snapshot' for p in snaps))
 ck('history_index_registered',by.get('docs/history/legacy-authority-bindings/README.md',{}).get('lifecycle_class')=='GENERATED_VIEW')
 ck('baseline_successor',by.get('docs/documentation/legacy-live-binding-baseline.json',{}).get('current_successors')==['docs/documentation/legacy-authority-decoupling-map.json'])
 ck('stable_policy',by.get('docs/documentation/LEGACY_AUTHORITY_DECOUPLING.md',{}).get('lifecycle_class')=='STABLE')
 text=(r/'docs/documentation/DOCUMENTATION_SYSTEM.md').read_text();ck('system_resolved','resolved through `legacy-authority-decoupling-map.json`' in text and 'Bulk physical relocation is not required' in text)
 latest=next((a for a in s.get('accepted_authorities',[]) if a.get('id')=='document-legacy-authority-decoupling-phase5'),{});ck('state_selects_authority',latest.get('path')=='experiments/document-legacy-authority-decoupling/legacy-authority-decoupling-authority.json' and len(str(latest.get('sha256','')))==64)
 ck('no_physical_moves',reg.get('basis',{}).get('physical_moves_allowed') is False and reg.get('basis',{}).get('physical_moves_decision')=='not-required')
 failed=[k for k,v in checks.items() if not v];o={'schema_version':1,'verifier_kind':'document-legacy-authority-decoupling-phase5','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':err,'metrics':{'tracked_document_count':len(t),'registry_document_count':len(rp),'snapshot_count':len(snaps),'navigation_target_count':len(s.get('render_targets',{}).get('navigation',[]))}};print(json.dumps(o,indent=2,sort_keys=True));return 0 if o['pass'] else 1
if __name__=='__main__':sys.exit(main())

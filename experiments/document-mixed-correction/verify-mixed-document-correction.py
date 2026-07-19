#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,os,re,subprocess,sys
from pathlib import Path
STATE='docs/current/STATE.json';REG='docs/documentation/document-registry.json';MAN='experiments/document-mixed-correction/legacy-mixed-paths.json';NAV='experiments/document-mixed-correction/navigation-targets.json'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def tracked(root):return set(subprocess.check_output(['git','ls-files','--','*.md','*.json'],cwd=root,text=True).splitlines())
def bindings(root,paths):
 found=[]
 for p in paths:
  if not p.endswith('.json'):continue
  try:o=load(root/p)
  except Exception:continue
  stack=[o]
  while stack:
   x=stack.pop()
   if isinstance(x,dict):
    fi=x.get('file_identities')
    if isinstance(fi,dict):
     for q,d in fi.items():found.append((p,q,d))
    stack.extend(x.values())
   elif isinstance(x,list):stack.extend(x)
 return found
def verify(root):
 fast=os.environ.get('HW_T_PHASE4_FIXTURE_FAST')=='1'
 checks={};errors={}
 def ck(n,v,e=''):checks[n]=bool(v);errors.update({n:e} if not v and e else {})
 try:s=load(root/STATE);r=load(root/REG);m=load(root/MAN);nav=load(root/NAV);ck('parse',True)
 except Exception as e:s={};r={};m={};nav={};ck('parse',False,str(e))
 paths=tracked(root);docs=r.get('documents',[]);rp=[x.get('path') for x in docs];by={x.get('path'):x for x in docs}
 ck('registry_identity',r.get('schema_version')==4 and r.get('schema_path')=='docs/documentation/document-registry-v4.schema.json')
 ck('registry_coverage',set(rp)==paths and len(rp)==len(set(rp))==len(paths),f'{len(paths)}/{len(rp)}')
 ck('state_identity',s.get('schema_version')==3 and s.get('schema_path')=='docs/current/STATE-v3.schema.json' and s.get('state_revision')==3)
 ck('predecessor',s.get('predecessor')=={'commit':'38889c8ec1daf26ac029a230bb2281296ef92680','tree':'64a5d860c92235a5a857cc97f473b436fb2db468'})
 ck('single_current_source',sum(x.get('lifecycle_class')=='CURRENT_SOURCE' for x in docs)==1 and by.get(STATE,{}).get('lifecycle_class')=='CURRENT_SOURCE')
 ck('stable_guide',by.get('docs/PROJECT_GUIDE.md',{}).get('lifecycle_class')=='STABLE' and s.get('project_guide',{}).get('path')=='docs/PROJECT_GUIDE.md' and s.get('project_guide',{}).get('sha256')==sha(root/'docs/PROJECT_GUIDE.md'))
 ck('stable_documentation_system',by.get('docs/documentation/DOCUMENTATION_SYSTEM.md',{}).get('lifecycle_class')=='STABLE')
 active={x['path'] for x in docs if x.get('lifecycle_class')=='ACTIVE_PLAN'}
 ck('active_plan_set',active=={'docs/roadmap/EPOCH2_PROGRAM_PLAN.md','docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md'},str(sorted(active)))
 ap=s.get('active_plan',{});ck('state_selects_plan',ap.get('path')=='docs/roadmap/EPOCH2_PROGRAM_PLAN.md' and ap.get('sha256')==sha(root/ap.get('path','x')) and ap.get('detail_path')=='docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md' and ap.get('detail_sha256')==sha(root/ap.get('detail_path','x')))
 snap=['docs/PROJECT_ORIENTATION.md','docs/PROJECT_CONTEXT.md','docs/PROJECT_CONTEXT_STAGE3.md','docs/PROJECT_CONTEXT_STAGE3C.md','docs/PROJECT_CONTEXT_STAGE3D.md','docs/PROJECT_CONTEXT_STAGE3E.md','docs/PROJECT_CONTEXT_STAGE3F.md','docs/roadmap/EPOCH2_ROADMAP.md','docs/roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md']
 ck('mixed_paths_historical',all(by.get(p,{}).get('lifecycle_class')=='HISTORICAL_SNAPSHOT' and by[p].get('snapshot_semantics')=='status-language-is-relative-to-the-recorded-snapshot' for p in snap))
 phase=['docs/documentation/DOCUMENT_LIFECYCLE.md','docs/documentation/CURRENT_STATE_AUTHORITY.md','docs/documentation/GENERATED_NAVIGATION.md'];ck('phase_contracts_frozen',all(by.get(p,{}).get('lifecycle_class')=='FROZEN_AUTHORITY' for p in phase))
 ids=m.get('byte_preserved_paths',{});ok=True
 for p,d in ids.items():
  q=root/('docs/history/2026-07-19-pre-phase4-root-readme-snapshot.md' if p=='README.md' else p)
  if not q.is_file() or sha(q)!=d:ok=False;break
 ck('predecessor_mixed_bytes_preserved',ok)
 ck('old_paths_exist',all((root/p).is_file() for p in snap+phase))
 guide=(root/'docs/PROJECT_GUIDE.md').read_text(encoding='utf-8').lower();forbid=['execute-document-','next action','current gate','held ready','active blocker'];ck('guide_temporal_neutral',not any(x in guide for x in forbid))
 plan=(root/'docs/roadmap/EPOCH2_PROGRAM_PLAN.md').read_text(encoding='utf-8').lower();forbidp=['current disposition','frozen pass','note9 api','s22 ultra','next action','held ready'];ck('plan_status_neutral',not any(x in plan for x in forbidp))
 system=(root/'docs/documentation/DOCUMENTATION_SYSTEM.md').read_text(encoding='utf-8').lower();ck('system_phase_neutral',not re.search(r'phase [0-9]+ (next|ready|pending)',system))
 hist=(root/'docs/history/README.md').read_text(encoding='utf-8') if (root/'docs/history/README.md').is_file() else '';ck('history_interpretation',"snapshot" in hist.lower() and 'STATE.json' in hist and 'PROJECT_GUIDE.md' in hist)
 road=(root/'docs/roadmap/README.md').read_text(encoding='utf-8') if (root/'docs/roadmap/README.md').is_file() else '';ck('roadmap_layering','Canonical active plans' in road and 'Historical plan snapshots' in road)
 ck('readme_snapshot',sha(root/'docs/history/2026-07-19-pre-phase4-root-readme-snapshot.md')==ids.get('README.md'))
 cur=(root/'README.md').read_text(encoding='utf-8');ck('root_readme_normalized',len(cur.splitlines())<130 and 'docs/PROJECT_GUIDE.md' in cur and 'Stage 3-B frozen result' not in cur)
 if fast:
  ck('generated_views',True)
 else:
  rr=subprocess.run([sys.executable,str(root/'experiments/document-mixed-correction/render-document-views.py'),'--root',str(root),'--check'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:rj=json.loads(rr.stdout)
  except Exception:rj={}
  ck('generated_views',rr.returncode==0 and rj.get('pass') is True and rj.get('target_count')==18,rr.stdout+rr.stderr)
 ck('navigation_targets',len(nav.get('targets',[]))==14 and s.get('navigation',{}).get('target_count')==14 and s.get('navigation',{}).get('history_root')=='docs/history/README.md')
 ck('next_action',s.get('next_action_class')=='execute-document-lifecycle-phase5-legacy-authority-decoupling' and s.get('control_work',{}).get('completed_phase')==4)
 claims=s.get('claim_boundaries',{});ck('claim_boundary',claims.get('dual_real_device_aarch64_termux_compatibility') is True and claims.get('emulator_qualified') is False and claims.get('selectable') is False and claims.get('publication_authorized') is False and claims.get('epoch3_feature_selection_started') is False)
 live={p for p,e in by.items() if e.get('lifecycle_class') in {'CURRENT_SOURCE','CURRENT_REGISTRY','GENERATED_VIEW','STABLE_WITH_GENERATED_SECTION'}}

 if fast:
  try: pa=load(root/'experiments/document-mixed-correction/document-mixed-correction-authority.json'); direct=pa.get('file_identities',{})
  except Exception: direct={}
  ck('legacy_binding_count',True);ck('no_new_live_bindings','docs/current/STATE.json' not in direct and 'docs/documentation/document-registry.json' not in direct)
 else:
  b=bindings(root,paths);legacy={(a,t,d) for a,t,d in b if t in {'README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md','docs/roadmap/EPOCH2_ROADMAP.md'}};new=[x for x in b if x[1] in live and x[1] not in {'README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'}]
  ck('legacy_binding_count',len(legacy)==24,str(len(legacy)));ck('no_new_live_bindings',not new,str(new[:3]))
 failed=[k for k,v in checks.items() if not v];return {'schema_version':1,'verifier_kind':'document-mixed-correction-phase4','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors,'tracked_document_count':len(paths)}
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default='.');x=a.parse_args();o=verify(Path(x.root).resolve());print(json.dumps(o,indent=2,sort_keys=True));return 0 if o['pass'] else 1
if __name__=='__main__':sys.exit(main())

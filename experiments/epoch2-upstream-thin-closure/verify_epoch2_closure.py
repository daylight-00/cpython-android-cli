#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from typing import Any
OUT=Path('experiments/epoch2-upstream-thin-closure')
EXPECTED_HEAD='082d005716934ea63f98c6fe232151b6c9b813ab'
EXPECTED_TREE='097b4b7cce6d7fb6d6552a381a74350cd132f9ef'
DOCS=['README.md','closure-gate-matrix.json','producer-independent-evidence-export.json','accepted-product-seed-boundary.json','unresolved-risk-register.json','epoch1-inheritance-matrix.json','reference-hierarchy.json','mandatory-invariants.json','selectable-options.json','reference-deviation-register.json','producer-only-deferred-register.json','epoch3-initialization-contract.json','independent-audit.json','closure-authority.json','evidence-freeze.md']
SCRIPTS=['build_epoch2_closure.py','audit_epoch2_closure.py','finalize_epoch2_closure.py','verify_epoch2_closure.py','test_verify_epoch2_closure.py','run-epoch2-closure.sh']
def load(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def run(root:Path,argv:list[str])->tuple[bool,str]:
 p=subprocess.run(argv,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);return p.returncode==0,p.stdout+p.stderr
def verify(root:Path, external:bool=True)->dict[str,Any]:
 root=root.resolve();out=root/OUT;checks=[];details={}
 def ck(name:str,ok:bool,detail:Any=None):
  checks.append((name,bool(ok)))
  if detail is not None and not ok:details[name]=detail
 for n in DOCS+SCRIPTS:ck(f'file:{n}',(out/n).is_file())
 try:
  gate=load(out/'closure-gate-matrix.json');exp=load(out/'producer-independent-evidence-export.json');seed=load(out/'accepted-product-seed-boundary.json');risk=load(out/'unresolved-risk-register.json');e1=load(out/'epoch1-inheritance-matrix.json');ref=load(out/'reference-hierarchy.json');inv=load(out/'mandatory-invariants.json');sel=load(out/'selectable-options.json');dev=load(out/'reference-deviation-register.json');prod=load(out/'producer-only-deferred-register.json');init=load(out/'epoch3-initialization-contract.json');audit=load(out/'independent-audit.json');auth=load(out/'closure-authority.json');state=load(root/'docs/current/STATE.json');task=load(root/'docs/current/AGENT_TASK.json');cat=load(root/'docs/agent/TASK_CATALOG.json');reg=load(root/'docs/documentation/document-registry.json')
 except Exception as e:
  ck('parse',False,str(e));gate=exp=seed=risk=e1=ref=inv=sel=dev=prod=init=audit=auth=state=task=cat=reg={}
 ck('gate-pass',gate.get('all_resolved') is True and gate.get('resolved_count')==8 and gate.get('gate_count')==8)
 ck('gate-statuses',all(str(x.get('status','')).startswith('resolved-pass') for x in gate.get('gates',[])))
 ck('gate-no-selection',gate.get('epoch3_selection_made') is False)
 ck('export-pass',exp.get('status')=='frozen-complete-for-epoch3-initialization' and exp.get('producer_independent') is True)
 ck('export-no-selection',exp.get('epoch3_selection_made') is False)
 ck('seed-status',seed.get('status')=='accepted-for-epoch3-initialization-not-selectable-release')
 ck('seed-input',seed.get('official_input',{}).get('sha256')=='38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5')
 ck('seed-release-false',seed.get('release_product') is False and seed.get('epoch3_selection_made') is False)
 ck('risk-complete',risk.get('risk_count')==16 and risk.get('closure_blocker_count')==0)
 ck('risk-no-hidden-blocker',all(x.get('blocks_epoch2_closure') is False for x in risk.get('risks',[])))
 ck('reference-two-axis',len(ref.get('axes',[]))==3 and ref.get('reference_hierarchy_kind')=='epoch3-two-axis-reference-policy')
 ck('reference-overall-primary',ref.get('overall_primary_reference')=='Astral python-build-standalone')
 ck('reference-secondary-pythonorg','Python.org / CPython Android prebuilt products' in ref.get('secondary_references',[]))
 ck('reference-astral',any(x.get('axis')=='consumer-product-structure' and x.get('primary')=='Astral python-build-standalone' for x in ref.get('axes',[])))
 ck('reference-pythonorg',any(x.get('axis')=='android-runtime-provenance' and x.get('primary')=='Python.org / CPython Android release process' for x in ref.get('axes',[])))
 ck('reference-epoch4',any(x.get('axis')=='full-source-producer' and x.get('primary')=='Epoch 4 project-owned producer' for x in ref.get('axes',[])))
 ck('invariants',inv.get('invariant_count')==14 and all(x.get('requirement')=='mandatory' for x in inv.get('invariants',[])))
 ck('epoch1-inheritance',len(e1.get('items',[]))==10 and all(x.get('automatic_implementation_import') is False for x in e1.get('items',[])))
 ck('selection-input-complete',sel.get('item_count')==18 and len(sel.get('items',[]))==18)
 ck('selection-not-started',sel.get('selection_complete') is False and sel.get('product_selection_made') is False and all(x.get('selection_status')=='pending-epoch3' for x in sel.get('items',[])))
 ck('selection-vocabulary',all(x.get('allowed_product_dispositions')==['adopt','adopt-with-redesign','exclude','defer-to-epoch4'] for x in sel.get('items',[])))
 ck('deviation-separated',len(dev.get('deviations',[]))==12 and any(x.get('class')=='producer-only' for x in dev.get('deviations',[])) and any(x.get('class')=='product-delta' for x in dev.get('deviations',[])))
 ck('reduction-reviewed',len(dev.get('reduction_opportunities',[]))==5)
 ck('producer-deferred',len(prod.get('questions',[]))==6 and prod.get('epoch3_product_contract_must_not_depend_on_resolution') is True)
 ck('init-ready',init.get('status')=='ready-not-started' and init.get('epoch3_selection_started') is False)
 ck('init-gates',len(init.get('required_initialization_gates',[]))==4)
 ck('init-no-expansion',init.get('implementation_may_expand_before_selection_complete') is False)
 ck('audit-pass',audit.get('pass') is True and audit.get('status')=='pass' and audit.get('failed_checks')==[])
 ck('audit-count',audit.get('check_count')==audit.get('pass_count') and audit.get('check_count',0)>=80)
 ck('authority-kind',auth.get('authority_kind')=='epoch2-closure-and-producer-independent-evidence-export')
 ck('authority-status',auth.get('status')=='frozen-pass-epoch2-closed-epoch3-initialization-ready')
 ck('authority-predecessor',auth.get('predecessor')=={'commit':EXPECTED_HEAD,'tree':EXPECTED_TREE})
 ck('authority-next',auth.get('next_action_class')=='initialize-epoch3-from-accepted-evidence-export')
 boundary=auth.get('claim_boundary',{})
 ck('authority-boundary',boundary=={'epoch2_closed':True,'producer_independent_export_complete':True,'accepted_seed_for_initialization':True,'epoch3_initialization_ready':True,'epoch3_selection_started':False,'product_selectability':False,'minimum_android_api_selected':False,'runtime_16k_device_qualified':False,'publication':False})
 for n,h in auth.get('file_identities',{}).items():
  p=out/n;ck(f'authority-file:{n}',p.is_file() and sha(p)==h)
 forbidden={'docs/current/STATE.json','docs/current/AGENT_TASK.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'}
 bound={str(OUT/n) for n in auth.get('file_identities',{})}|set(auth.get('repository_transition_file_identities',{}))
 ck('no-forbidden-live-binding',not (forbidden&bound),sorted(forbidden&bound))
 for p,h in auth.get('repository_transition_file_identities',{}).items():ck(f'transition-file:{p}',(root/p).is_file() and sha(root/p)==h)
 ck('charter-e2-closed','> **Status:** CLOSED — producer-independent evidence export frozen 2026-07-21' in (root/'docs/epochs/EPOCH2_CHARTER.md').read_text())
 ck('charter-e3-ready','> **Status:** READY FOR INITIALIZATION — selection not started' in (root/'docs/epochs/EPOCH3_CHARTER.md').read_text())
 ck('plan-closed','> **Lifecycle:** historical completed plan — closed by E2-CLOSURE' in (root/'docs/roadmap/EPOCH2_PROGRAM_PLAN.md').read_text())
 ck('state-revision',state.get('state_revision')==16)
 ck('state-predecessor',state.get('predecessor')=={'commit':EXPECTED_HEAD,'tree':EXPECTED_TREE})
 ck('state-epoch',state.get('program',{}).get('epoch')=={'id':'E3','name':'clean upstream-derived Android standalone distribution','status':'ready-not-started'})
 ck('state-gate',state.get('program',{}).get('gate')=={'id':'E3/INIT','name':'Epoch 3 initialization decisions and contract freeze','status':'ready'})
 ck('state-next',state.get('next_action_class')=='initialize-epoch3-from-accepted-evidence-export' and state.get('program',{}).get('next_action_class')=='initialize-epoch3-from-accepted-evidence-export')
 ck('state-no-selection',state.get('claim_boundaries',{}).get('epoch3_feature_selection_started') is False and state.get('claim_boundaries',{}).get('selectable') is False and state.get('claim_boundaries',{}).get('publication_authorized') is False)
 closure_rows=[x for x in state.get('accepted_authorities',[]) if x.get('id')=='epoch2-closure-and-producer-independent-evidence-export']
 ck('state-authority-once',len(closure_rows)==1)
 ck('state-authority-sha',len(closure_rows)==1 and closure_rows[0].get('sha256')==sha(out/'closure-authority.json'))
 ck('state-risk-count',len(state.get('unresolved_risks',[]))==16)
 ck('state-active-plan',state.get('active_plan',{}).get('path')=='docs/epochs/EPOCH3_CHARTER.md')
 ck('task-id',task.get('task',{}).get('id')=='E3-INIT')
 ck('task-action',task.get('task',{}).get('action_class')=='initialize-epoch3-from-accepted-evidence-export')
 ck('task-gate',task.get('program_gate')==state.get('program',{}).get('gate'))
 ck('task-state-revision',task.get('state_revision')==16)
 ck('task-no-selection',task.get('claim_boundary',{}).get('epoch3_selection_claim') is False and task.get('claim_boundary',{}).get('product_selectability_claim') is False)
 ck('task-init-contract',any(x.get('path')==str(OUT/'epoch3-initialization-contract.json') for x in task.get('required_reads',[])))
 matches=[x for x in cat.get('tasks',[]) if x.get('task_id')=='E3-INIT']
 ck('catalog-e3-init-once',len(matches)==1)
 ck('catalog-activation',len(matches)==1 and matches[0].get('activation',{}).get('accepted_authority_sha256')==sha(out/'closure-authority.json'))
 ck('catalog-selection-before-implementation',len(matches)==1 and matches[0].get('completion_contract',{}).get('always',{}).get('implementation_expansion_before_selection_complete_forbidden') is True)
 ck('catalog-hash',state.get('task_catalog',{}).get('sha256')==sha(root/'docs/agent/TASK_CATALOG.json'))
 registered={x.get('path') for x in reg.get('documents',[])}
 for n in DOCS:ck(f'registry:{n}',str(OUT/n) in registered)
 e2plan=[x for x in reg.get('documents',[]) if x.get('path')=='docs/roadmap/EPOCH2_PROGRAM_PLAN.md']
 ck('registry-e2-plan-historical',len(e2plan)==1 and e2plan[0].get('lifecycle_class')=='HISTORICAL_SNAPSHOT')
 ck('registry-count',reg.get('basis',{}).get('tracked_document_count')==len(reg.get('documents',[])))
 ck('registry-next',reg.get('basis',{}).get('next_action_class')=='initialize-epoch3-from-accepted-evidence-export')
 ck('registry-active-plan',reg.get('basis',{}).get('canonical_active_plan')=='docs/epochs/EPOCH3_CHARTER.md')
 ok,msg=run(root,[sys.executable,'-B',str(root/'experiments/agent-task-completion/render-document-views.py'),'--root',str(root),'--check']);ck('generated-views',ok,msg)

 if external:
  ok,msg=run(root,[sys.executable,'-B',str(root/'tools/agent_onboard.py'),'--root',str(root)]);ck('agent-onboard',ok,msg)
 failed=[n for n,ok in checks if not ok]
 return {'schema_version':1,'verifier':'epoch2-closure-focused','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':dict(checks),'details':details}
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--no-external',action='store_true');a=ap.parse_args();r=verify(a.root,external=not a.no_external);print(json.dumps(r,indent=2,sort_keys=True));return 0 if r['pass'] else 1
if __name__=='__main__':raise SystemExit(main())

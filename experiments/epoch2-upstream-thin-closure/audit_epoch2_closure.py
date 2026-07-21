#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
OUT=Path('experiments/epoch2-upstream-thin-closure')
REQUIRED=['closure-gate-matrix.json','producer-independent-evidence-export.json','accepted-product-seed-boundary.json','unresolved-risk-register.json','epoch1-inheritance-matrix.json','reference-hierarchy.json','mandatory-invariants.json','selectable-options.json','reference-deviation-register.json','producer-only-deferred-register.json','epoch3-initialization-contract.json','README.md']
def load(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));a=ap.parse_args();root=a.root.resolve();out=root/OUT
 checks=[]
 def ck(name:str,ok:bool,detail:Any=None):checks.append({'name':name,'pass':bool(ok),**({} if detail is None else {'detail':detail})})
 for n in REQUIRED:ck(f'file:{n}',(out/n).is_file())
 try:
  gate=load(out/'closure-gate-matrix.json');exp=load(out/'producer-independent-evidence-export.json');seed=load(out/'accepted-product-seed-boundary.json');risk=load(out/'unresolved-risk-register.json');e1=load(out/'epoch1-inheritance-matrix.json');ref=load(out/'reference-hierarchy.json');inv=load(out/'mandatory-invariants.json');sel=load(out/'selectable-options.json');dev=load(out/'reference-deviation-register.json');prod=load(out/'producer-only-deferred-register.json');init=load(out/'epoch3-initialization-contract.json')
 except Exception as e:
  ck('parse',False,str(e));gate=exp=seed=risk=e1=ref=inv=sel=dev=prod=init={}
 ck('gate-kind',gate.get('matrix_kind')=='epoch2-closure-gate-matrix')
 ck('gate-count',gate.get('gate_count')==8 and len(gate.get('gates',[]))==8)
 ck('gate-ids',[x.get('id') for x in gate.get('gates',[])]==[f'E2-G{i}' for i in range(1,9)])
 ck('gate-resolved',gate.get('all_resolved') is True and gate.get('resolved_count')==8 and all(str(x.get('status','')).startswith('resolved-pass') for x in gate.get('gates',[])))
 ck('gate-no-selection',gate.get('epoch3_selection_made') is False)
 ck('gate-decision',gate.get('closure_decision')=='close-epoch2-and-enable-epoch3-initialization-without-product-selection')
 bindings=gate.get('authority_bindings',{})
 for k,row in sorted(bindings.items()):
  p=root/row.get('path','');ck(f'binding-file:{k}',p.is_file());ck(f'binding-sha:{k}',p.is_file() and sha(p)==row.get('sha256'))
 ck('export-kind',exp.get('export_kind')=='epoch2-producer-independent-evidence-export')
 ck('export-producer-independent',exp.get('producer_independent') is True)
 ck('export-no-selection',exp.get('epoch3_selection_made') is False)
 for key in ['exact_upstream_inputs','exact_local_delta','mandatory_invariants','selectable_item_evidence','selection_candidates_and_tradeoffs','supported_platform_claims','withheld_platform_claims','artifact_and_metadata_contract','qualification_contract','unresolved_risks','accepted_product_seed','epoch4_deferred_questions']:
  ck(f'export-section:{key}',key in exp)
 official=(exp.get('exact_upstream_inputs') or [{}])[0]
 ck('official-filename',official.get('filename')=='python-3.14.6-aarch64-linux-android.tar.gz')
 ck('official-sha',official.get('sha256')=='38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5')
 ck('official-size',official.get('size')==22358404)
 ck('official-target',official.get('target')=='aarch64-linux-android' and official.get('minimum_android_api')==24)
 ck('seed-kind',seed.get('boundary_kind')=='epoch3-accepted-product-seed')
 ck('seed-status',seed.get('status')=='accepted-for-epoch3-initialization-not-selectable-release')
 ck('seed-id',seed.get('seed_id')=='pythonorg-cpython-3.14.6-android-aarch64-upstream-thin-v1')
 ck('seed-official',seed.get('official_input')==official)
 ck('seed-overlay-count',len(seed.get('included_bounded_overlays',[]))==5)
 ck('seed-la2',any(x.get('id')=='LA-2' for x in seed.get('included_bounded_overlays',[])))
 ck('seed-lr3',any(x.get('id')=='LR-3' for x in seed.get('included_bounded_overlays',[])))
 ck('seed-not-release',seed.get('release_product') is False and seed.get('epoch3_selection_made') is False)
 ck('seed-excludes-api36',any('API36' in x for x in seed.get('excluded_from_seed',[])))
 ck('reference-kind',ref.get('reference_hierarchy_kind')=='epoch3-two-axis-reference-policy')
 ck('reference-overall-primary',ref.get('overall_primary_reference')=='Astral python-build-standalone')
 ck('reference-secondary-pythonorg','Python.org / CPython Android prebuilt products' in ref.get('secondary_references',[]))
 axes={x.get('axis'):x for x in ref.get('axes',[])}
 ck('reference-structural',axes.get('consumer-product-structure',{}).get('primary')=='Astral python-build-standalone')
 ck('reference-android',axes.get('android-runtime-provenance',{}).get('primary')=='Python.org / CPython Android release process')
 ck('reference-producer-epoch4',axes.get('full-source-producer',{}).get('primary')=='Epoch 4 project-owned producer')
 ck('invariant-count',inv.get('invariant_count')==14 and len(inv.get('invariants',[]))==14)
 ck('invariant-ids',[x.get('id') for x in inv.get('invariants',[])]==[f'INV-{i:02d}' for i in range(1,15)])
 ck('invariant-mandatory',all(x.get('requirement')=='mandatory' for x in inv.get('invariants',[])))
 ck('epoch1-count',len(e1.get('items',[]))==10)
 ck('epoch1-no-auto-import',all(x.get('automatic_implementation_import') is False for x in e1.get('items',[])))
 ck('selection-count',sel.get('item_count')==18 and len(sel.get('items',[]))==18)
 ck('selection-pending',all(x.get('selection_status')=='pending-epoch3' for x in sel.get('items',[])))
 ck('selection-not-complete',sel.get('selection_complete') is False and sel.get('product_selection_made') is False)
 ck('selection-vocabulary',all(x.get('allowed_product_dispositions')==['adopt','adopt-with-redesign','exclude','defer-to-epoch4'] for x in sel.get('items',[])))
 ck('selection-no-auto-adopt',all(x.get('experiment_success_implies_inclusion') is False for x in sel.get('items',[])))
 ids={x.get('id') for x in sel.get('items',[])}
 for i in range(1,19):ck(f'selection-id:{i:02d}',f'SEL-{i:02d}' in ids)
 ck('deviation-count',len(dev.get('deviations',[]))==12)
 classes={x.get('class') for x in dev.get('deviations',[])}
 ck('deviation-classes',{'product-delta','optional-product-delta','representation-delta','product-policy','experiment-only','producer-only','experiment-control'}<=classes)
 ck('reduction-opportunities',len(dev.get('reduction_opportunities',[]))==5)
 ck('producer-count',len(prod.get('questions',[]))==6)
 ck('producer-deferred',prod.get('status')=='deferred-not-blocking-epoch2-closure' and prod.get('epoch3_product_contract_must_not_depend_on_resolution') is True)
 ck('risk-count',risk.get('risk_count')==16 and len(risk.get('risks',[]))==16)
 ck('risk-no-hidden-blocker',risk.get('closure_blocker_count')==0 and all(x.get('blocks_epoch2_closure') is False for x in risk.get('risks',[])))
 ck('risk-policy','implicit product support' in risk.get('claim_policy',''))
 ck('init-kind',init.get('contract_kind')=='epoch3-initialization-contract')
 ck('init-ready',init.get('status')=='ready-not-started' and init.get('epoch3_selection_started') is False)
 ck('init-gates',len(init.get('required_initialization_gates',[]))==4)
 ck('init-selection-ids',init.get('required_selection_item_ids')==[f'SEL-{i:02d}' for i in range(1,19)])
 ck('init-no-expansion',init.get('implementation_may_expand_before_selection_complete') is False)
 ck('init-next',init.get('next_action_class')=='initialize-epoch3-from-accepted-evidence-export')
 failed=[x['name'] for x in checks if not x['pass']]
 result={'schema_version':1,'audit_kind':'epoch2-closure-independent-audit','status':'pass' if not failed else 'fail','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks}
 (out/'independent-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps(result,indent=2,sort_keys=True));return 0 if not failed else 1
if __name__=='__main__':raise SystemExit(main())

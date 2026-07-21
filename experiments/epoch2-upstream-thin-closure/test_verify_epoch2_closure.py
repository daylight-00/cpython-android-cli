#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, shutil, subprocess, tempfile
from pathlib import Path
from typing import Callable

def load_module(path:Path):
 spec=importlib.util.spec_from_file_location('closure_verify',path);m=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(m);return m

def jedit(path:Path, fn:Callable[[dict],None]):
 o=json.loads(path.read_text());fn(o);path.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));a=ap.parse_args();root=a.root.resolve();tmp=Path(tempfile.mkdtemp(prefix='e2-closure-negative-'));repo=tmp/'repo'
 repo.mkdir(parents=True,exist_ok=True)
 subprocess.run(['git','-C',str(root),'checkout-index','--all','--force',f'--prefix={repo.as_posix()}/'],check=True)
 v=load_module(repo/'experiments/epoch2-upstream-thin-closure/verify_epoch2_closure.py')
 baseline=v.verify(repo,external=False)
 if not baseline['pass']:print(json.dumps(baseline,indent=2,sort_keys=True));return 1
 fixtures=[]
 def case(name:str,path:str,mut:Callable[[Path],None],expected:str):
  p=repo/path;original=p.read_bytes();mut(p);result=v.verify(repo,external=False);p.write_bytes(original);ok=(not result['pass'] and expected in result['failed_checks']);fixtures.append({'name':name,'pass':ok,'expected_check':expected,'failed_checks':result['failed_checks']});
 case('gate-unresolved','experiments/epoch2-upstream-thin-closure/closure-gate-matrix.json',lambda p:jedit(p,lambda o:o.update({'all_resolved':False})),'gate-pass')
 case('seed-promoted-to-release','experiments/epoch2-upstream-thin-closure/accepted-product-seed-boundary.json',lambda p:jedit(p,lambda o:o.update({'release_product':True})),'seed-release-false')
 case('selection-prematurely-complete','experiments/epoch2-upstream-thin-closure/selectable-options.json',lambda p:jedit(p,lambda o:o.update({'selection_complete':True,'product_selection_made':True})),'selection-not-started')
 case('risk-hidden-blocker','experiments/epoch2-upstream-thin-closure/unresolved-risk-register.json',lambda p:jedit(p,lambda o:(o.update({'closure_blocker_count':1}),o['risks'][0].update({'blocks_epoch2_closure':True}))),'risk-complete')
 case('reference-axis-drift','experiments/epoch2-upstream-thin-closure/reference-hierarchy.json',lambda p:jedit(p,lambda o:o['axes'][0].update({'primary':'local-fork'})),'reference-astral')
 case('producer-contract-dependency','experiments/epoch2-upstream-thin-closure/producer-only-deferred-register.json',lambda p:jedit(p,lambda o:o.update({'epoch3_product_contract_must_not_depend_on_resolution':False})),'producer-deferred')
 case('authority-live-binding','experiments/epoch2-upstream-thin-closure/closure-authority.json',lambda p:jedit(p,lambda o:o['repository_transition_file_identities'].update({'docs/current/STATE.json':'0'*64})),'no-forbidden-live-binding')
 case('epoch2-charter-reopened','docs/epochs/EPOCH2_CHARTER.md',lambda p:p.write_text(p.read_text().replace('CLOSED — producer-independent evidence export frozen 2026-07-21','ACTIVE')),'charter-e2-closed')
 case('state-selection-started','docs/current/STATE.json',lambda p:jedit(p,lambda o:o['claim_boundaries'].update({'epoch3_feature_selection_started':True})),'state-no-selection')
 case('task-action-drift','docs/current/AGENT_TASK.json',lambda p:jedit(p,lambda o:o['task'].update({'action_class':'implement-epoch3-clean-upstream-derived-product'})),'task-action')
 case('catalog-implementation-before-selection','docs/agent/TASK_CATALOG.json',lambda p:jedit(p,lambda o:next(x for x in o['tasks'] if x['task_id']=='E3-INIT')['completion_contract']['always'].update({'implementation_expansion_before_selection_complete_forbidden':False})),'catalog-selection-before-implementation')
 case('registry-missing-authority','docs/documentation/document-registry.json',lambda p:jedit(p,lambda o:o.update({'documents':[x for x in o['documents'] if x['path']!='experiments/epoch2-upstream-thin-closure/closure-authority.json']})),'registry:closure-authority.json')
 case('output-byte-drift','experiments/epoch2-upstream-thin-closure/mandatory-invariants.json',lambda p:p.write_bytes(p.read_bytes()+b' '),'authority-file:mandatory-invariants.json')
 failed=[x['name'] for x in fixtures if not x['pass']]
 result={'schema_version':1,'test_kind':'epoch2-closure-negative-regression','pass':not failed,'baseline_check_count':baseline['check_count'],'fixture_count':len(fixtures),'pass_count':len(fixtures)-len(failed),'failed_checks':failed,'fixtures':fixtures}
 print(json.dumps(result,indent=2,sort_keys=True));shutil.rmtree(tmp,ignore_errors=True);return 0 if not failed else 1
if __name__=='__main__':raise SystemExit(main())

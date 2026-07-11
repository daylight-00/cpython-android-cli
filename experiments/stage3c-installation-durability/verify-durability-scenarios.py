#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, stat, hashlib
from pathlib import Path
EXPECTED_GATE3_INDEX='f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd'
def rj(p):
 v=json.loads(p.read_text());
 if not isinstance(v,dict): raise ValueError(p)
 return v
def cb(v): return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def atomic_ok(doc,label,parent):
 rows=[e for e in doc['events'] if e['label']==label]
 return [e['op'] for e in rows]==['OPEN_TEMP','WRITE_TEMP','FSYNC_FILE','REPLACE','FSYNC_DIR'] and rows[-1]['path']==str(parent) and all(rows[i]['seq']<rows[i+1]['seq'] for i in range(4))
def main():
 p=argparse.ArgumentParser(); p.add_argument('--gate3-results',type=Path,required=True); p.add_argument('--scenario-results',type=Path,required=True); p.add_argument('--work-root',type=Path,required=True); p.add_argument('--input-before',type=Path,required=True); p.add_argument('--input-after',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); gate=a.gate3_results.resolve(); res=a.scenario_results.resolve(); work=a.work_root.resolve(); checks={}
 def ck(n,v): checks[n]=bool(v)
 s=rj(gate/'scenario.json'); v=rj(gate/'verification.json'); w=rj(gate/'workflow-status.json'); before=rj(a.input_before.resolve()); after=rj(a.input_after.resolve()); sc=rj(res/'scenario.json'); cap=rj(res/'capability.json'); contract=rj(res/'durability-contract.json')
 ck('gate3_scenario_pass_55',s.get('pass') is True and s.get('check_count')==55 and s.get('failed_checks')==[]); ck('gate3_verify_pass_82',v.get('pass') is True and v.get('check_count')==82 and v.get('failed_checks')==[]); ck('gate3_workflow_pass',w.get('pass') is True and all(x==0 for x in w.get('returncodes',{}).values())); ck('gate3_index_exact',sha(gate/'result-index.json')==EXPECTED_GATE3_INDEX); ck('input_unchanged',before.get('pass') is True and after.get('pass') is True and before.get('entry_count')==after.get('entry_count') and before.get('fingerprint')==after.get('fingerprint'))
 ck('scenario_pass',sc.get('pass') is True and sc.get('failed_checks')==[] and all(sc.get('checks',{}).values())); ck('scenario_count_self_consistent',sc.get('check_count')==len(sc.get('checks',{}))); ck('cap_regular_fsync',cap.get('regular_file_fsync') is True); ck('cap_dir_fsync',cap.get('directory_fsync') is True); ck('cap_same_fs',cap.get('same_filesystem') is True); ck('contract_kind',contract.get('contract_kind')=='cpython-android-cli-durability-protocol'); ck('contract_atomic',contract['primitives']['atomic-replace']==['OPEN_TEMP','WRITE_TEMP','FSYNC_FILE','REPLACE','FSYNC_DIR']); ck('claim_boundary','sudden power loss' in contract['claim_boundary']['not_proved'])
 names=['trace-atomic-create.json','trace-atomic-replace.json','trace-mkdir.json','trace-move.json','trace-unlink.json','trace-rmdir.json','trace-transaction.json']; docs={n:rj(res/n) for n in names}; ck('trace_set_exact',sorted(p.name for p in res.glob('trace-*.json'))==sorted(names)); ck('trace_canonical',all((res/n).read_bytes()==cb(docs[n]) for n in names)); ck('trace_counts_exact',all(d['event_count']==len(d['events']) for d in docs.values())); ck('trace_seq_contiguous',all([e['seq'] for e in d['events']]==list(range(1,len(d['events'])+1)) for d in docs.values()))
 prim=work/'primitive'; ck('atomic_create_pattern',atomic_ok(docs['trace-atomic-create.json'],'atomic-create',prim)); ck('atomic_replace_pattern',atomic_ok(docs['trace-atomic-replace.json'],'atomic-replace',prim)); ck('atomic_create_target',docs['trace-atomic-create.json']['events'][3]['target']==str(prim/'state.json')); ck('atomic_replace_target',docs['trace-atomic-replace.json']['events'][3]['target']==str(prim/'state.json'))
 md=docs['trace-mkdir.json']['events']; ck('mkdir_pattern',[e['op'] for e in md]==['MKDIR','FSYNC_DIR','FSYNC_DIR']); ck('mkdir_newdir_path',md[1]['path']==str(prim/'newdir')); ck('mkdir_parent_path',md[2]['path']==str(prim))
 mv=docs['trace-move.json']['events']; ck('move_pattern',[e['op'] for e in mv]==['MOVE','FSYNC_DIR','FSYNC_DIR']); ck('move_source_parent',mv[1]['path']==str(prim/'source')); ck('move_dest_parent',mv[2]['path']==str(prim/'destination'))
 un=docs['trace-unlink.json']['events']; rd=docs['trace-rmdir.json']['events']; ck('unlink_pattern',[e['op'] for e in un]==['UNLINK','FSYNC_DIR']); ck('unlink_parent',un[1]['path']==str(prim/'destination')); ck('rmdir_pattern',[e['op'] for e in rd]==['RMDIR','FSYNC_DIR']); ck('rmdir_parent',rd[1]['path']==str(prim))
 td=docs['trace-transaction.json']; labels=['journal-prepared','payload','journal-applying','registry','journal-committed','backup-cleanup']; first={x:min(e['seq'] for e in td['events'] if e['label']==x) for x in labels}; ck('transaction_order',[first[x] for x in labels]==sorted(first.values())); tr=work/'transaction';
 for lab,path in [('journal-prepared',tr/'state/journal.json'),('payload',tr/'prefix/payload'),('journal-applying',tr/'state/journal.json'),('registry',tr/'state/registry.json'),('journal-committed',tr/'state/journal.json')]: ck('transaction_atomic_'+lab,atomic_ok(td,lab,path.parent))
 cleanup=[e for e in td['events'] if e['label']=='backup-cleanup']; ck('transaction_cleanup_pattern',[e['op'] for e in cleanup]==['UNLINK','FSYNC_DIR']); ck('transaction_cleanup_parent',cleanup[-1]['path']==str(tr/'backup')); ck('transaction_event_count',td['event_count']==27)
 ck('final_journal_committed',rj(tr/'state/journal.json')=={'state':'COMMITTED'}); ck('final_registry_exact',rj(tr/'state/registry.json')=={'owned':['payload']}); ck('final_payload_exact',(tr/'prefix/payload').read_bytes()==b'payload-v1\n'); ck('final_backup_absent',not (tr/'backup/old').exists()); ck('no_atomic_temps',not list(work.rglob('.*.tmp-*')))
 neg=rj(res/'negative-missing-parent-fsync.json'); ck('negative_missing_count',neg['event_count']==4); ck('negative_missing_last_not_fsync',neg['events'][-1]['op']=='REPLACE'); order=rj(res/'negative-transaction-order.json')['declared_first_order']; ck('negative_order_registry_before_payload',order['registry']<order['payload']); ck('negative_order_not_valid',[order[x] for x in labels]!=sorted(order.values()))
 ck('work_root_set',{p.name for p in work.iterdir()}=={'capability','primitive','transaction'}); ck('scenario_canonical',(res/'scenario.json').read_bytes()==cb(sc)); ck('contract_canonical',(res/'durability-contract.json').read_bytes()==cb(contract)); ck('capability_canonical',(res/'capability.json').read_bytes()==cb(cap))
 if len(checks) != 53:
  raise RuntimeError(f'unexpected check count: {len(checks)}')
 failed=sorted(k for k,v in checks.items() if not v); result={'schema_version':1,'pass':not failed,'check_count':len(checks),'checks':checks,'failed_checks':failed,'observed':{'scenario_check_count':sc['check_count'],'trace_count':len(names),'transaction_event_count':td['event_count']},'claim_boundary':contract['claim_boundary']}; a.output.resolve().write_bytes(cb(result)); print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result['pass'] else 49
if __name__=='__main__': raise SystemExit(main())

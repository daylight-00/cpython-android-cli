#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, shutil, stat
from pathlib import Path
from durability_common import *
EXPECTED_GATE3_INDEX='f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd'

def main():
 p=argparse.ArgumentParser(); p.add_argument('--gate3-results',type=Path,required=True); p.add_argument('--work-root',type=Path,required=True); p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--require-pass',action='store_true'); a=p.parse_args()
 gate=a.gate3_results.resolve(); work=a.work_root.resolve(); out=a.output_dir.resolve(); shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True); out.mkdir(parents=True,exist_ok=True)
 checks={}
 def check(n,v): checks[n]=bool(v)
 def save(n,v): (out/n).write_bytes(canonical_json_bytes(v)); return v
 s=read_json(gate/'scenario.json'); v=read_json(gate/'verification.json'); w=read_json(gate/'workflow-status.json')
 check('gate3_scenario_pass_55',s.get('pass') is True and s.get('check_count')==55 and s.get('failed_checks')==[])
 check('gate3_verification_pass_82',v.get('pass') is True and v.get('check_count')==82 and v.get('failed_checks')==[])
 check('gate3_workflow_pass',w.get('pass') is True and all(x==0 for x in w.get('returncodes',{}).values()))
 check('gate3_result_index_exact',sha256_file(gate/'result-index.json')==EXPECTED_GATE3_INDEX)
 check('gate3_claim_boundary_present','power-loss durability' in s.get('claim_boundary',{}).get('not_proved',''))

 caproot=work/'capability'; caproot.mkdir(); cap={}
 f=caproot/'file'; fd=os.open(f,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.write(fd,b'capability\n'); os.fsync(fd); os.close(fd); cap['regular_file_fsync']=True
 d=caproot/'dir'; d.mkdir(); dfd=os.open(d,os.O_RDONLY|getattr(os,'O_DIRECTORY',0)); os.fsync(dfd); os.close(dfd); cap['directory_fsync']=True
 cap['same_filesystem']=caproot.stat().st_dev==(work/'capability').stat().st_dev
 cap['o_directory_available']=hasattr(os,'O_DIRECTORY')
 cap['file_mode']=f'{stat.S_IMODE(f.stat().st_mode):04o}'
 cap['dir_mode']=f'{stat.S_IMODE(d.stat().st_mode):04o}'
 save('capability.json',cap)
 for k,val in cap.items(): check('capability_'+k, val is True if isinstance(val,bool) else bool(val))
 check('capability_file_mode_0600',cap['file_mode']=='0600'); check('capability_dir_mode_nonzero',cap['dir_mode']!='0000')

 contract={'schema_version':1,'contract_kind':'cpython-android-cli-durability-protocol','primitives':{
 'atomic-replace':['OPEN_TEMP','WRITE_TEMP','FSYNC_FILE','REPLACE','FSYNC_DIR'],
 'mkdir':['MKDIR','FSYNC_DIR_NEW','FSYNC_DIR_PARENT'],
 'move':['MOVE','FSYNC_DIR_SOURCE_PARENT','FSYNC_DIR_DESTINATION_PARENT'],
 'unlink':['UNLINK','FSYNC_DIR_PARENT'],
 'rmdir':['RMDIR','FSYNC_DIR_PARENT']},
 'transaction_order':['journal-prepared','payload','journal-applying','registry','journal-committed','backup-cleanup'],
 'claim_boundary':{'proved':'Successful primitive calls and trace ordering on the target filesystem.','not_proved':'Persistence across kernel panic, sudden power loss, storage-controller failure, or a crash inside one filesystem primitive.'}}
 save('durability-contract.json',contract)
 check('contract_kind_exact',contract['contract_kind']=='cpython-android-cli-durability-protocol'); check('contract_atomic_sequence_exact',contract['primitives']['atomic-replace']==['OPEN_TEMP','WRITE_TEMP','FSYNC_FILE','REPLACE','FSYNC_DIR']); check('contract_claim_boundary_exact','sudden power loss' in contract['claim_boundary']['not_proved'])

 pr=work/'primitive'; pr.mkdir(); t=Trace(); target=pr/'state.json'; data1=canonical_json_bytes({'generation':1}); atomic_replace_bytes(target,data1,0o600,t,'atomic-create'); ok,why=audit_atomic(t.events,'atomic-create',target); doc=t.document('atomic-create'); save('trace-atomic-create.json',doc)
 check('atomic_create_audit_pass',ok); check('atomic_create_reasons_empty',why==[]); check('atomic_create_bytes_exact',target.read_bytes()==data1); check('atomic_create_mode_0600',stat.S_IMODE(target.stat().st_mode)==0o600); check('atomic_create_no_temp',not list(pr.glob('.state.json.tmp-*'))); check('atomic_create_event_count_5',doc['event_count']==5)
 t=Trace(); data2=canonical_json_bytes({'generation':2}); atomic_replace_bytes(target,data2,0o600,t,'atomic-replace'); ok,why=audit_atomic(t.events,'atomic-replace',target); doc=t.document('atomic-replace'); save('trace-atomic-replace.json',doc)
 check('atomic_replace_audit_pass',ok); check('atomic_replace_reasons_empty',why==[]); check('atomic_replace_bytes_exact',target.read_bytes()==data2); check('atomic_replace_mode_0600',stat.S_IMODE(target.stat().st_mode)==0o600); check('atomic_replace_no_temp',not list(pr.glob('.state.json.tmp-*'))); check('atomic_replace_event_count_5',doc['event_count']==5)

 t=Trace(); nd=pr/'newdir'; durable_mkdir(nd,0o700,t,'mkdir'); doc=t.document('mkdir'); save('trace-mkdir.json',doc); ops=[e['op'] for e in t.events]
 check('mkdir_ops_exact',ops==['MKDIR','FSYNC_DIR','FSYNC_DIR']); check('mkdir_new_dir_fsync',t.events[1]['path']==str(nd)); check('mkdir_parent_fsync',t.events[2]['path']==str(pr)); check('mkdir_exists',nd.is_dir()); check('mkdir_mode_0700',stat.S_IMODE(nd.stat().st_mode)==0o700)

 srcd=pr/'source'; dstd=pr/'destination'; srcd.mkdir(); dstd.mkdir(); src=srcd/'item'; src.write_bytes(b'move-me\n')
 t=Trace(); dst=dstd/'item'; durable_move(src,dst,t,'move'); doc=t.document('move'); save('trace-move.json',doc); ops=[e['op'] for e in t.events]
 check('move_ops_exact',ops==['MOVE','FSYNC_DIR','FSYNC_DIR']); check('move_source_parent_fsync',t.events[1]['path']==str(srcd)); check('move_destination_parent_fsync',t.events[2]['path']==str(dstd)); check('move_source_absent',not src.exists()); check('move_destination_exact',dst.read_bytes()==b'move-me\n')

 t=Trace(); durable_unlink(dst,t,'unlink'); doc=t.document('unlink'); save('trace-unlink.json',doc); check('unlink_ops_exact',[e['op'] for e in t.events]==['UNLINK','FSYNC_DIR']); check('unlink_parent_fsync',t.events[1]['path']==str(dstd)); check('unlink_absent',not dst.exists())
 t=Trace(); durable_rmdir(nd,t,'rmdir'); doc=t.document('rmdir'); save('trace-rmdir.json',doc); check('rmdir_ops_exact',[e['op'] for e in t.events]==['RMDIR','FSYNC_DIR']); check('rmdir_parent_fsync',t.events[1]['path']==str(pr)); check('rmdir_absent',not nd.exists())

 tr=work/'transaction'; (tr/'state').mkdir(parents=True); (tr/'prefix').mkdir(); (tr/'backup').mkdir(); backup=tr/'backup/old'; backup.write_bytes(b'old\n')
 trace=Trace(); journal=tr/'state/journal.json'; registry=tr/'state/registry.json'; payload=tr/'prefix/payload'
 atomic_replace_bytes(journal,canonical_json_bytes({'state':'PREPARED'}),0o600,trace,'journal-prepared')
 atomic_replace_bytes(payload,b'payload-v1\n',0o600,trace,'payload')
 atomic_replace_bytes(journal,canonical_json_bytes({'state':'APPLYING','mutations':[{'status':'APPLIED'}]}),0o600,trace,'journal-applying')
 atomic_replace_bytes(registry,canonical_json_bytes({'owned':['payload']}),0o600,trace,'registry')
 atomic_replace_bytes(journal,canonical_json_bytes({'state':'COMMITTED'}),0o600,trace,'journal-committed')
 durable_unlink(backup,trace,'backup-cleanup')
 tdoc=trace.document('transaction'); save('trace-transaction.json',tdoc)
 labels=['journal-prepared','payload','journal-applying','registry','journal-committed','backup-cleanup']; first={lab:min(e['seq'] for e in trace.events if e['label']==lab) for lab in labels}
 check('transaction_labels_exact',list(first)==labels); check('transaction_order_exact',[first[x] for x in labels]==sorted(first.values()));
 for lab,target_path in [('journal-prepared',journal),('payload',payload),('journal-applying',journal),('registry',registry),('journal-committed',journal)]:
  ok,why=audit_atomic(trace.events,lab,target_path); check('transaction_'+lab+'_audit',ok and why==[])
 check('transaction_cleanup_ops',[e['op'] for e in trace.events if e['label']=='backup-cleanup']==['UNLINK','FSYNC_DIR']); check('transaction_committed_exact',read_json(journal)=={'state':'COMMITTED'}); check('transaction_registry_exact',read_json(registry)=={'owned':['payload']}); check('transaction_payload_exact',payload.read_bytes()==b'payload-v1\n'); check('transaction_backup_absent',not backup.exists()); check('transaction_event_count_27',tdoc['event_count']==27)

 missing={'schema_version':1,'trace_kind':'negative-missing-parent-fsync','events':[dict(e) for e in read_json(out/'trace-atomic-create.json')['events'][:-1]]}; missing['event_count']=len(missing['events']); save('negative-missing-parent-fsync.json',missing); ok,why=audit_atomic(missing['events'],'atomic-create',target)
 check('negative_missing_parent_fsync_rejected',not ok); check('negative_missing_parent_reason','operation-sequence' in why and 'parent-fsync-path' in why)
 reordered=[dict(e) for e in trace.events]; order={'journal-prepared':1,'registry':2,'payload':3,'journal-applying':4,'journal-committed':5,'backup-cleanup':6}; neg_first={lab:order[lab] for lab in order}; save('negative-transaction-order.json',{'schema_version':1,'trace_kind':'negative-transaction-order','declared_first_order':neg_first,'events':reordered})
 check('negative_transaction_order_rejected',[neg_first[x] for x in labels]!=sorted(neg_first.values())); check('negative_transaction_has_registry_before_payload',neg_first['registry']<neg_first['payload'])

 traces=sorted(p.name for p in out.glob('trace-*.json')); check('positive_trace_count_7',len(traces)==7); check('positive_traces_canonical',all(p.read_bytes()==canonical_json_bytes(read_json(p)) for p in out.glob('trace-*.json'))); check('work_roots_exact',{p.name for p in work.iterdir()}=={'capability','primitive','transaction'})
 if len(checks) != 64:
  raise RuntimeError(f'unexpected check count: {len(checks)}')
 N=len(checks)
 failed=sorted(k for k,v in checks.items() if not v); result={'schema_version':1,'pass':not failed,'check_count':N,'checks':checks,'failed_checks':failed,'observed':{'positive_traces':traces,'transaction_event_count':tdoc['event_count']},'claim_boundary':contract['claim_boundary']}; save('scenario.json',result); print(json.dumps(result,indent=2,sort_keys=True)); print('STAGE3C_PHASE4_DURABILITY_SCENARIOS='+('PASS' if result['pass'] else 'FAIL')); return 0 if result['pass'] or not a.require_pass else 48
if __name__=='__main__': raise SystemExit(main())

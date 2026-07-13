#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_GROUPS={'preflight':6,'teardown':8,'residual':10,'recovery':12,'locking':2,'audit':6}
EXPECTED_STATES={
 'empty':([],0,0),
 'runtime':(['runtime-base'],1,714),
 'runtime-development':(['runtime-base','development-addon'],2,1168),
 'runtime-test':(['runtime-base','test-addon'],2,2502),
 'composed':(['runtime-base','development-addon','test-addon'],3,2956),
}
EXPECTED_BLOBS={
 'recovery_common.py':'3183ba0861ef45e7a395201bec0085f3f69fb248',
 'recovery_durability.py':'61bfb859f73acccb0dfcce1d2a630bfd1ffc2d3f',
 'recovery_engine.py':'aebf5b9a33d163f7f8758f785ca621c94c0e478b',
 'recovery_operations.py':'8a307065e00fd7a7332541f4911c5478945374ee',
}
G3B_ARCH='0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b'
G3B_INDEX='f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9'
G3C_ARCH='43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a'
G3C_INDEX='fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c'
G3C_SAFETY='ab338579025da63dec1750e3a7649c9a5f260cd4556f60ab3b3ade6140187bb9'
CONTRACT='79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3'


def cjson(v:Any)->bytes:return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git_blob(root:Path,rel:str)->str:
 return subprocess.check_output(['git','-C',str(root),'rev-parse',f'HEAD:{rel}'],text=True).strip()

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--project-root',type=Path,required=True); ap.add_argument('--matrix',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--require-pass',action='store_true'); a=ap.parse_args()
 root=a.project_root.resolve(); matrix=json.loads(a.matrix.read_text()); scenarios=matrix.get('scenarios',[]); checks={}
 def ck(k:str,v:Any)->None: checks[k]=bool(v)
 auth=matrix.get('authority',{}); policy=matrix.get('policy',{}); classes=matrix.get('final_state_classes',{})
 ck('matrix_canonical_json',a.matrix.read_bytes()==cjson(matrix))
 ck('schema_v1',matrix.get('schema_version')==1)
 ck('matrix_kind_exact',matrix.get('matrix_kind')=='stage3c-phase5-gate3d-final-uninstall-design')
 ck('status_target_pending',matrix.get('status')=='DESIGN_FROZEN_TARGET_EVIDENCE_PENDING')
 ck('target_exact',matrix.get('target')=='Termux on Android arm64')
 ck('scenario_count_44',matrix.get('scenario_count')==44 and len(scenarios)==44)
 ck('group_counts_exact',matrix.get('scenario_group_counts')==EXPECTED_GROUPS and Counter(s.get('group') for s in scenarios)==Counter(EXPECTED_GROUPS))
 ids=[s.get('id') for s in scenarios]
 expected_ids=[f'P{i:02d}' for i in range(1,7)]+[f'T{i:02d}' for i in range(1,9)]+[f'S{i:02d}' for i in range(1,11)]+[f'R{i:02d}' for i in range(1,13)]+[f'L{i:02d}' for i in range(1,3)]+[f'A{i:02d}' for i in range(1,7)]
 ck('scenario_ids_exact',ids==expected_ids)
 ck('scenario_ids_unique',len(ids)==len(set(ids)))
 ck('required_evidence_all',all(set(['process_output','before_snapshot','after_snapshot','registry_snapshot','payload_inventory','residual_inventory','transaction_inventory']).issubset(s.get('required_evidence',[])) for s in scenarios))
 # authority
 g3b=auth.get('gate3b',{}); g3c=auth.get('gate3c',{})
 ck('gate3b_archive_exact',g3b.get('archive_sha256')==G3B_ARCH)
 ck('gate3b_index_exact',g3b.get('result_index_sha256')==G3B_INDEX)
 ck('gate3b_pass_counts',g3b.get('scenario_pass')=='29/29' and g3b.get('verifier_pass')=='62/62')
 ck('gate3c_archive_exact',g3c.get('archive_sha256')==G3C_ARCH)
 ck('gate3c_index_exact',g3c.get('result_index_sha256')==G3C_INDEX)
 ck('gate3c_safety_exact',g3c.get('result_tree_safety_sha256')==G3C_SAFETY)
 ck('gate3c_pass_counts',g3c.get('scenario_pass')=='50/50' and g3c.get('verifier_pass')=='103/103' and g3c.get('external_audit_pass')=='27/27')
 ck('contract_index_exact',auth.get('contract_index_sha256')==CONTRACT)
 ck('shared_namespace_exact',auth.get('shared_structural_namespace')==['lib','lib/python3.14'])
 subjects=auth.get('subjects',{})
 ck('subject_regular_exact',subjects.get('modified_owned_regular')=='lib/python3.14/LICENSE.txt')
 ck('subject_symlink_exact',subjects.get('modified_owned_symlink')=='bin/python')
 ck('subject_unowned_file_exact',subjects.get('unowned_file')=='lib/python3.14/site-packages/gate3d-user-file.txt')
 ck('subject_unowned_dir_exact',subjects.get('unowned_directory')=='lib/python3.14/site-packages/gate3d-user-dir')
 # states/artifacts
 for name,(arts,count,owned) in EXPECTED_STATES.items():
  state=auth.get('states',{}).get(name,{})
  ck(f'state_{name}_exact',state.get('artifacts')==arts and state.get('artifact_count')==count and state.get('owned_path_count')==owned)
 artifacts=auth.get('artifacts',{})
 ck('runtime_owned_714',artifacts.get('runtime-base',{}).get('owned_paths')==714)
 ck('development_owned_454',artifacts.get('development-addon',{}).get('owned_paths')==454)
 ck('test_owned_1788',artifacts.get('test-addon',{}).get('owned_paths')==1788)
 ck('addon_prerequisites_exact',artifacts.get('development-addon',{}).get('prerequisite')=='runtime-base' and artifacts.get('test-addon',{}).get('prerequisite')=='runtime-base')
 # engine blobs
 recovery='experiments/stage3c-installation-recovery'
 for name,digest in EXPECTED_BLOBS.items(): ck(f'blob_{name}',git_blob(root,f'{recovery}/{name}')==digest)
 # policies
 expected_policy={
  'runtime_uninstall_precondition':'all-addons-absent',
  'runtime_uninstall_with_any_addon':'reject-before-mutation',
  'exact_owned_leaf':'remove-and-deregister',
  'modified_owned_leaf':'preserve-report-deregister',
  'unowned_descendant':'preserve-unchanged',
  'owned_directory':'remove-only-when-empty',
  'structural_namespace':'runtime-owned-remove-when-empty-preserve-for-residual-descendant',
  'registry_after_committed_final_uninstall':'empty',
  'precommit_recovery':'restore-exact-prior-runtime-state-retain-one-rolled-back-tombstone',
  'precommit_second_recovery':'NOOP_ROLLED_BACK',
  'committed_recovery':'finalize-final-state-remove-transaction',
  'committed_second_recovery':'ZERO_TRANSACTIONS',
  'upgrade_downgrade':'out-of-scope',
 }
 for k,v in expected_policy.items(): ck(f'policy_{k}',policy.get(k)==v)
 # final state classes
 ck('final_classes_exact',set(classes)=={'exact-owned-teardown','modified-owned-residual','unowned-sentinel-residual','mixed-approved-residual'})
 ck('exact_class_distinctions',classes.get('exact-owned-teardown')=={'registry_empty':True,'owned_payload_absent':True,'approved_residuals':[],'transactions_empty':True,'prefix_root_physically_empty':True})
 ck('modified_class_distinctions',classes.get('modified-owned-residual',{}).get('registry_empty') is True and classes.get('modified-owned-residual',{}).get('owned_payload_absent') is True and classes.get('modified-owned-residual',{}).get('prefix_root_physically_empty') is False and 'modified-owned-leaf' in classes.get('modified-owned-residual',{}).get('approved_residuals',[]))
 ck('unowned_class_distinctions',classes.get('unowned-sentinel-residual',{}).get('registry_empty') is True and classes.get('unowned-sentinel-residual',{}).get('owned_payload_absent') is True and classes.get('unowned-sentinel-residual',{}).get('prefix_root_physically_empty') is False and 'unowned-sentinel' in classes.get('unowned-sentinel-residual',{}).get('approved_residuals',[]))
 ck('mixed_class_distinctions',set(classes.get('mixed-approved-residual',{}).get('approved_residuals',[]))=={'modified-owned-leaf','unowned-sentinel','required-nonempty-ancestors'})
 # preflight
 pre=[s for s in scenarios if s.get('group')=='preflight']
 ck('preflight_zero_mutation',all(s.get('mutation_count')==0 for s in pre))
 ck('preflight_dependent_count',sum(s.get('error_contains')=='dependent addons installed' for s in pre)==5)
 ck('preflight_empty_not_installed',pre[-1].get('initial_state')=='empty' and pre[-1].get('expected_result')=='REJECT_NOT_INSTALLED')
 ck('preflight_all_states',set(s.get('expected_state') for s in pre)=={'composed','runtime-development','runtime-test','empty'})
 # teardown
 td=[s for s in scenarios if s.get('group')=='teardown']
 ck('teardown_both_orders',td[0].get('operation_sequence')==['uninstall test-addon','uninstall development-addon','uninstall runtime-base'] and td[1].get('operation_sequence')==['uninstall development-addon','uninstall test-addon','uninstall runtime-base'])
 ck('teardown_one_addon_states',td[2].get('initial_state')=='runtime-development' and td[3].get('initial_state')=='runtime-test')
 ck('teardown_runtime_only',td[4].get('initial_state')=='runtime' and td[4].get('operation')=='uninstall runtime-base')
 ck('teardown_guarded_orders',all('reject uninstall runtime-base' in s.get('operation_sequence',[]) for s in td[5:7]))
 ck('teardown_repeat_rejection',td[7].get('expected_result')=='EXACT_THEN_IDEMPOTENT_REJECTION')
 ck('teardown_final_empty',all(s.get('expected_state')=='empty' and s.get('final_state_class')=='exact-owned-teardown' for s in td))
 # residual
 rs=[s for s in scenarios if s.get('group')=='residual']
 ck('residual_count_10',len(rs)==10)
 ck('residual_modified_regular',sum(s.get('subject')=='modified-owned-regular' for s in rs)==3)
 ck('residual_modified_symlink',sum(s.get('subject')=='modified-owned-symlink' for s in rs)==2)
 ck('residual_unowned_file',any(s.get('subject')=='unowned-file' for s in rs))
 ck('residual_unowned_directory',any(s.get('subject')=='unowned-directory' for s in rs))
 ck('residual_owned_directory_rule',any(s.get('subject')=='unowned-descendant-under-owned-directory' for s in rs))
 ck('residual_shared_namespace_rule',any(s.get('subject')=='unowned-file-under-shared-namespace' for s in rs))
 ck('residual_combined',any(s.get('final_state_class')=='mixed-approved-residual' for s in rs))
 ck('residual_reinstall_collision',rs[-1].get('expected_result')=='RESIDUAL_COLLISION_REJECTED')
 # recovery
 rec=[s for s in scenarios if s.get('group')=='recovery']
 ck('recovery_count_12',len(rec)==12)
 ck('recovery_subject_cross_product',Counter(s.get('subject') for s in rec)==Counter({'exact-owned':3,'modified-owned-regular':3,'modified-owned-symlink':3,'unowned-file':3}))
 ck('recovery_boundary_cross_product',Counter(s.get('crash_boundary') for s in rec)==Counter({'prepared':4,'applying-late':4,'committed':4}))
 ck('recovery_rc_exact',Counter(s.get('expected_crash_returncode') for s in rec)==Counter({90:4,93:4,92:4}))
 ck('recovery_actions_exact',all((s.get('crash_boundary')=='committed' and s.get('expected_recovery_action')=='FINALIZED_COMMIT') or (s.get('crash_boundary')!='committed' and s.get('expected_recovery_action')=='ROLLED_BACK') for s in rec))
 ck('recovery_second_exact',all((s.get('crash_boundary')=='committed' and s.get('expected_second_recovery')=='ZERO_TRANSACTIONS') or (s.get('crash_boundary')!='committed' and s.get('expected_second_recovery')=='NOOP_ROLLED_BACK') for s in rec))
 ck('recovery_starts_composed_then_runtime',all(s.get('initial_state')=='composed' and s.get('setup_sequence')==['uninstall test-addon','uninstall development-addon'] and s.get('precommit_state')=='runtime' for s in rec))
 # locking/audit
 lock=[s for s in scenarios if s.get('group')=='locking']; audit=[s for s in scenarios if s.get('group')=='audit']
 ck('locking_rc44',len(lock)==2 and all(s.get('expected_returncode')==44 and s.get('mutation_count')==0 for s in lock))
 ck('audit_count_6',len(audit)==6)
 ck('audit_distinctions',set(audit[0].get('assertions',[]))=={'registry_empty','owned_payload_absent','approved_residuals_empty','transactions_empty','prefix_root_physically_empty'})
 ck('audit_modified_nonempty','prefix_root_not_empty' in audit[1].get('assertions',[]) and 'modified_leaf_preserved' in audit[1].get('assertions',[]))
 ck('audit_unowned_nonempty','prefix_root_not_empty' in audit[2].get('assertions',[]) and 'unowned_sentinel_unchanged' in audit[2].get('assertions',[]))
 ck('audit_structural_namespace','shared_namespace_removed_when_empty' in audit[3].get('assertions',[]) and 'shared_namespace_retained_only_for_residual_descendant' in audit[3].get('assertions',[]))
 ck('audit_recovery_topology','rolled_back_tombstone_one' in audit[4].get('assertions',[]) and 'committed_transaction_cleaned' in audit[4].get('assertions',[]))
 ck('audit_evidence_contract',set(['raw_stdout_stderr','real_returncodes','canonical_json','archive_safety','complete_root_result_index','independent_verifier','explicit_claim_boundary']).issubset(audit[5].get('assertions',[])))
 # execution/evidence/claims
 req=set(matrix.get('target_evidence_requirements',[]))
 ck('evidence_requirements_complete',set(['fresh authority extraction','inode-separated roots','synchronous raw stdout and stderr','real process return codes','before and after registry snapshots','owned payload and residual inventories','journal and transaction snapshots','second-recovery evidence','canonical machine JSON','archive safety report','complete root result-index recomputation','independent verifier','explicit claim boundary']).issubset(req))
 execution=matrix.get('execution_contract',{})
 ck('single_wrapper_required',execution.get('single_termux_wrapper') is True)
 ck('historical_tgz_immutable',execution.get('historical_tgz_immutable') is True)
 ck('zstd_new_archive',execution.get('new_archive_suffix')=='.tar.zst')
 ck('pass_or_fail_archive',execution.get('pass_or_fail_archive_required') is True)
 claim=matrix.get('claim_boundary',{})
 ck('claim_design_only','forty-four-scenario' in claim.get('proved_by_design',''))
 ck('claim_no_target','No target final multi-artifact/runtime-base uninstall' in claim.get('not_proved_by_design',''))
 ck('claim_close_requires_archive','independently inspected Termux result archive' in claim.get('gate3d_close_requires',''))
 # repository docs
 paths={
  'design':'experiments/stage3c-installed-runtime-lifecycle/GATE3D_FINAL_UNINSTALL_DESIGN.md',
  'handoff':'docs/handoff/PHASE5_GATE3D_FINAL_UNINSTALL_HANDOFF_20260713.md',
  'scope':'docs/stages/STAGE3C_PHASE5_SCOPE.md',
  'handoff_readme':'docs/handoff/README.md',
  'experiment_readme':'experiments/stage3c-installed-runtime-lifecycle/README.md',
  'ledger':'docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md',
  'gate3b':'docs/evidence/STAGE3C_PHASE5_GATE3B_PRESERVATION_ACCEPTANCE_RESULT.md',
  'gate3c':'docs/evidence/STAGE3C_PHASE5_GATE3C_ADDON_LIFECYCLE_ACCEPTANCE_RESULT.md',
 }
 texts={k:(root/v).read_text() for k,v in paths.items()}
 ck('design_doc_status','DESIGN FROZEN — target evidence pending' in texts['design'])
 ck('design_doc_44','exactly 44 scenarios' in texts['design'])
 ck('design_doc_distinctions',all(x in texts['design'] for x in ['registry empty','owned payload absent','approved residuals present or absent','prefix root physically empty or non-empty']))
 ck('design_doc_claim_boundary','does not prove target final uninstall' in texts['design'])
 ck('gate3b_doc_authority',G3B_ARCH in texts['gate3b'] and G3B_INDEX in texts['gate3b'])
 ck('gate3c_doc_authority',G3C_ARCH in texts['gate3c'] and G3C_INDEX in texts['gate3c'] and G3C_SAFETY in texts['gate3c'])
 ck('handoff_design_frozen','Frozen design result' in texts['handoff'] and '44' in texts['handoff'] and 'TARGET IMPLEMENTATION READY' in texts['handoff'])
 ck('scope_design_frozen','Gate 3D' in texts['scope'] and 'design is frozen at 108/108' in texts['scope'] and 'TARGET READY / EVIDENCE PENDING' in texts['scope'])
 ck('handoff_readme_design_frozen','Gate 3D final uninstall' in texts['handoff_readme'] and 'DESIGN FROZEN' in texts['handoff_readme'])
 ck('experiment_readme_design_frozen','Gate 3D final runtime-base uninstall' in texts['experiment_readme'] and 'DESIGN FROZEN' in texts['experiment_readme'])
 ck('ledger_design_path','GATE3D_FINAL_UNINSTALL_DESIGN.md' in texts['ledger'] and 'gate3d-final-uninstall-matrix.json' in texts['ledger'])
 ck('gate4_deferred_docs',all('Gate 4' in texts[k] and 'deferred' in texts[k].lower() for k in ['design','handoff','scope','handoff_readme']))
 failed=sorted(k for k,v in checks.items() if not v)
 result={'schema_version':1,'verification_kind':'stage3c-phase5-gate3d-final-uninstall-design-verification','pass':not failed,'check_count':len(checks),'pass_count':sum(checks.values()),'checks':checks,'failed_checks':failed,'matrix_sha256':sha256(a.matrix.resolve()),'observed':{'scenario_count':len(scenarios),'scenario_group_counts':dict(Counter(s.get('group') for s in scenarios)),'engine_git_blobs':{n:git_blob(root,f'{recovery}/{n}') for n in EXPECTED_BLOBS}},'claim_boundary':claim}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(cjson(result)); print(json.dumps(result,indent=2,sort_keys=True)); print(f"\nGATE3D_FINAL_UNINSTALL_DESIGN_VERIFICATION={result['pass_count']}/{result['check_count']} "+('PASS' if result['pass'] else 'FAIL'))
 return 0 if result['pass'] or not a.require_pass else 41
if __name__=='__main__': raise SystemExit(main())

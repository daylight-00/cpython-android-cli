#!/usr/bin/env python3
"""Verify the current repository control-plane documentation contract."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
def text(path:str)->str: return (REPO/path).read_text(encoding='utf-8')

readme=text('README.md')
current=text('docs/PROJECT_CONTEXT_STAGE3D.md')
stage3c=text('docs/PROJECT_CONTEXT_STAGE3C.md')
stage3=text('docs/PROJECT_CONTEXT_STAGE3.md')
workflow=text('docs/GITHUB_COLLABORATION_WORKFLOW.md')
protocol=text('docs/handoff/COLLABORATION_PROTOCOL.md')
handoff=text('docs/handoff/README.md')
ledger=text('docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md')
phase5=text('docs/stages/STAGE3C_PHASE5_SCOPE.md')
stage3d_scope=text('docs/stages/STAGE3D_SCOPE.md')
design=text('experiments/stage3d-consumer-integration/GATE1_CONSUMER_AUTHORITY_DESIGN.md')
authority=json.loads(text('experiments/stage3d-consumer-integration/gate1-consumer-authority.json'))
matrix=json.loads(text('experiments/stage3d-consumer-integration/gate2-consumer-discovery-matrix.json'))

checks={
 'readme_gate3c_frozen':'Gate 4E independent freeze complete' in readme,
 'readme_stage3d_active':'Stage 3-D  consumer integration                         active — Gate 1 design frozen' in readme,
 'readme_current_context_path':'docs/PROJECT_CONTEXT_STAGE3D.md' in readme,
 'readme_drive_tar_zst_exchange':'Google Drive, normally one .tar.zst per direction' in readme,
 'readme_stage3d_boundary':'## Stage 3-D active boundary' in readme,
 'current_context_status':'> **Status:** Current handoff context' in current,
 'current_context_branch':'agent/stage3d-consumer-integration' in current,
 'current_context_gate4_identity':all(x in current for x in ('68b67dcc3b65872e1034c487747d3fcd1ad5a319','2115f6fa3b923c9fcf21a1b8343cb6149afb6cc7')),
 'current_context_gate4_66':'matrix           66/66 PASS' in current,
 'current_context_gate2_active':'Gate 2  read-only Termux discovery census      ACTIVE NEXT' in current,
 'current_context_system_python':'system Python' in current and 'explicit absolute interpreter' in current,
 'current_context_no_managed_claim':'Managed-Python emulation is not accepted' in current,
 'current_context_no_global_links':'Do not create global interpreter links' in current,
 'current_context_transport':'one `.tar.zst` per direction' in current,
 'current_context_no_github_connector':'GitHub connector/API operations are not part of this workflow' in current,
 'current_context_authorship':'daylight-00 <hwjang00@snu.ac.kr>' in current,
 'stage3c_context_historical':'HISTORICAL FROZEN SNAPSHOT' in stage3c and 'PROJECT_CONTEXT_STAGE3D.md' in stage3c,
 'stage3_context_historical':'HISTORICAL SNAPSHOT' in stage3,
 'workflow_local_git_default':'real local Git repository or an exact bundle reconstruction' in workflow,
 'workflow_no_connector_default':'GitHub connector operations are not the default' in workflow,
 'workflow_single_archive':'one `.tar.zst` per direction' in workflow,
 'workflow_patch_partial_full':all(x in workflow for x in ('patch','partial bundle','full bundle')),
 'workflow_flexible_timing':'Commit and push timing is deliberately flexible' in workflow,
 'workflow_authorship_exact':'daylight-00 <hwjang00@snu.ac.kr>' in workflow,
 'workflow_target_archive_audit':'A console marker alone is never acceptance' in workflow,
 'workflow_current_stage3d':'docs/PROJECT_CONTEXT_STAGE3D.md' in workflow and 'gate2-consumer-discovery-matrix.json' in workflow,
 'protocol_minimum_user_work':'minimum manual work' in protocol,
 'protocol_single_archive':'one `.tar.zst` per direction' in protocol,
 'protocol_bundle_selection':all(x in protocol for x in ('patch','partial bundle','full bundle')),
 'protocol_authorship_exact':'daylight-00 <hwjang00@snu.ac.kr>' in protocol,
 'protocol_main_after_validation':'fast-forward the canonical branch only after validation' in protocol,
 'protocol_current_stage3d':'docs/PROJECT_CONTEXT_STAGE3D.md' in protocol and 'gate2-consumer-discovery-matrix.json' in protocol,
 'handoff_current_context':'../PROJECT_CONTEXT_STAGE3D.md' in handoff,
 'orientation_current_context':'docs/PROJECT_CONTEXT_STAGE3D.md' in text('docs/PROJECT_ORIENTATION.md') and 'gate1-consumer-authority.json' in text('docs/PROJECT_ORIENTATION.md'),
 'handoff_gate4_frozen':'Gate 4 upgrade/downgrade                             FROZEN — Gate 4E, 66/66' in handoff,
 'handoff_gate2_next':'Stage 3-D Gate 2 read-only Termux discovery census     ACTIVE NEXT' in handoff,
 'ledger_gate4_archives':all(x in ledger for x in ('ef24baca1f01d3e106825fb99e537d68ba0beffa9cd4e92577e43bd35421e77c','98ab810732dd2eb35bff9180dcb8fa1ec872eb09103d58670edb481cc9e3e5b2')),
 'ledger_next_gate2':'64-scenario read-only Termux consumer discovery census' in ledger,
 'phase5_frozen':'FROZEN — Gate 4E independent transition freeze complete' in phase5,
 'phase5_gate4_66':'Gate 4    upgrade and downgrade with second frozen product        FROZEN — 66/66' in phase5,
 'phase5_gate4d_frozen':'Gate 4D   bidirectional Termux target validation                  FROZEN' in phase5,
 'stage3d_scope_active':'ACTIVE — Gate 1 scope and authority design frozen' in stage3d_scope,
 'stage3d_scope_system_first':'Primary consumer:** uv using the installed interpreter as a system Python' in stage3d_scope,
 'stage3d_scope_download_disabled':'automatic Python downloads disabled' in stage3d_scope,
 'stage3d_scope_no_global':'must not alter global shell files' in stage3d_scope,
 'stage3d_scope_64':'total                          64' in stage3d_scope,
 'design_frozen':'DESIGN FROZEN' in design,
 'design_system_first':'System-Python integration is selected first' in design,
 'design_no_mutation':all(x in design for x in ('writing `$PREFIX/bin/python*`','placing product bytes in uv\'s managed installation directory','patching uv')),
 'authority_status':authority.get('status')=='design-frozen',
 'authority_model':authority.get('primary_model')=='uv-system-python',
 'authority_gate4_commit':authority['input_authority']['gate4e_commit']=='68b67dcc3b65872e1034c487747d3fcd1ad5a319',
 'authority_gate4_tree':authority['input_authority']['gate4e_tree']=='2115f6fa3b923c9fcf21a1b8343cb6149afb6cc7',
 'authority_gate2_pending':authority['gate_sequence']['gate2']=='PENDING_READ_ONLY_TERMUX_CENSUS',
 'authority_managed_deferred':authority['gate_sequence']['gate6']=='DEFERRED_OPTIONAL_MANAGED_PYTHON_RESEARCH',
 'matrix_64':matrix.get('scenario_count')==64 and len(matrix.get('scenarios',[]))==64,
 'matrix_groups':matrix.get('group_counts')=={'explicit':8,'natural':32,'project':8,'precedence-negative':12,'transition-continuity':4},
 'matrix_download_disabled':'python-downloads-disabled' in matrix.get('global_requirements',[]),
 'matrix_unique_ids':len({x['id'] for x in matrix.get('scenarios',[])})==64,
}

required=(
 'README.md','docs/PROJECT_CONTEXT_STAGE3D.md','docs/PROJECT_CONTEXT_STAGE3C.md','docs/stages/STAGE3D_SCOPE.md',
 'docs/stages/STAGE3C_PHASE5_SCOPE.md','docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md',
 'experiments/stage3d-consumer-integration/GATE1_CONSUMER_AUTHORITY_DESIGN.md',
 'experiments/stage3d-consumer-integration/gate1-consumer-authority.json',
 'experiments/stage3d-consumer-integration/gate2-consumer-discovery-matrix.json',
 'experiments/stage3d-consumer-integration/verify-gate1-consumer-authority-design.py',
 'docs/evidence/STAGE3D_GATE1_CONSUMER_AUTHORITY_DESIGN_RESULT.md',
 'experiments/stage3c-gate4-transition/gate4e-transition-freeze-authority.json',
 'docs/evidence/STAGE3C_PHASE5_GATE4E_INDEPENDENT_TRANSITION_FREEZE.md',
 'docs/GITHUB_COLLABORATION_WORKFLOW.md','docs/handoff/COLLABORATION_PROTOCOL.md')
checks['all_current_reading_paths_exist']=all((REPO/p).exists() for p in required)
checks['git_diff_check']=subprocess.run(['git','-C',str(REPO),'diff','--check','HEAD'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True).returncode==0
checks['python_source_compiles']=subprocess.run(['python3','-m','py_compile',str(Path(__file__)),str(REPO/'experiments/stage3d-consumer-integration/verify-gate1-consumer-authority-design.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True).returncode==0

failed=sorted(k for k,v in checks.items() if not v)
result={
 'schema_version':1,'verification_kind':'project-control-plane-reconciliation','pass':not failed,
 'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':failed,'checks':dict(sorted(checks.items())),
 'observed':{
   'head':subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),
   'tree_before_commit':subprocess.check_output(['git','-C',str(REPO),'write-tree'],text=True).strip(),
   'current_context_sha256':hashlib.sha256((REPO/'docs/PROJECT_CONTEXT_STAGE3D.md').read_bytes()).hexdigest(),
   'matrix_sha256':hashlib.sha256((REPO/'experiments/stage3d-consumer-integration/gate2-consumer-discovery-matrix.json').read_bytes()).hexdigest(),
 },
 'claim_boundary':'Repository documentation, authority, and scenario-design alignment only. No Termux consumer behavior is accepted.'
}
print(json.dumps(result,indent=2,sort_keys=True))
raise SystemExit(0 if result['pass'] else 1)

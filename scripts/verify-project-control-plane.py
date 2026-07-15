#!/usr/bin/env python3
"""Verify the current Stage 3-D repository control plane."""
from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def t(p): return (R/p).read_text()
def j(p): return json.loads(t(p))
ctx=t('docs/PROJECT_CONTEXT_STAGE3D.md'); scope=t('docs/stages/STAGE3D_SCOPE.md'); readme=t('README.md'); orient=t('docs/PROJECT_ORIENTATION.md'); handoff=t('docs/handoff/README.md'); workflow=t('docs/GITHUB_COLLABORATION_WORKFLOW.md'); protocol=t('docs/handoff/COLLABORATION_PROTOCOL.md'); lessons=t('docs/session-operations/LESSONS_AND_CHANGELOG.md'); g2=j('experiments/stage3d-consumer-integration/gate2-consumer-census-authority.json'); g3=j('experiments/stage3d-consumer-integration/gate3-system-python-contract.json'); m=j('experiments/stage3d-consumer-integration/gate4-consumer-integration-validation-matrix.json')
checks={
 'readme_gate4e':'Gate 4E independent freeze complete' in readme,
 'readme_stage3d':'active — Gate 3 contract frozen; Gate 4 next' in readme,
 'context_status':'> **Status:** Current handoff context' in ctx,
 'context_branch':'agent/stage3d-consumer-integration' in ctx,
 'context_gate4':'Gate 4  target implementation/validation       ACTIVE NEXT' in ctx,
 'context_gate2_archive':'4958b3e669950035f21baf5783fa54029366182cdc36ecf1fb909dfb8276e98c' in ctx,
 'context_run_sync_gap':'Gate 2 executed no `uv run` and no `uv sync`' in ctx,
 'scope_status':'ACTIVE — Gate 3 system-Python contract frozen; Gate 4 next' in scope,
 'scope_matrix':'48-scenario matrix' in scope,
 'scope_prohibitions':'root/proot/Shizuku/Docker' in scope,
 'orientation_current':'GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT.md' in orient and 'gate4-consumer-integration-validation-matrix.json' in orient,
 'handoff_current':'Stage 3-D Gate 4 target implementation/validation       ACTIVE NEXT' in handoff,
 'workflow_current':'GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT.md' in workflow and 'gate4-consumer-integration-validation-matrix.json' in workflow,
 'protocol_current':'GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT.md' in protocol and 'gate4-consumer-integration-validation-matrix.json' in protocol,
 'lesson_prune':'transient workspace versus evidence archive' in lessons,
 'g2_status':g2['status']=='target-evidence-accepted',
 'g2_64':g2['scenario_results']['count']==64 and g2['scenario_results']['expectation_match']==64,
 'g2_coverage':g2['process_coverage']['uv_run']==0 and g2['process_coverage']['uv_sync']==0,
 'g3_status':g3['status']=='contract-frozen',
 'g3_selector':g3['canonical_contract']['selector']=='explicit-absolute-interpreter-path',
 'g3_gate4':g3['gate_sequence']['gate4']=='ACTIVE_NEXT_TARGET_IMPLEMENTATION_VALIDATION',
 'matrix_48':m['scenario_count']==48 and len(m['scenarios'])==48,
 'matrix_run_sync':sum(x['operation']=='uv-run-explicit-interpreter' for x in m['scenarios'])==8 and sum(x['operation']=='uv-sync-explicit-interpreter' for x in m['scenarios'])==8,
 'reading_paths':all((R/p).is_file() for p in ['docs/PROJECT_CONTEXT_STAGE3D.md','docs/stages/STAGE3D_SCOPE.md','experiments/stage3d-consumer-integration/GATE2_READ_ONLY_CONSUMER_CENSUS.md','experiments/stage3d-consumer-integration/GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT.md','docs/handoff/STAGE3D_EVIDENCE_LEDGER.md']),
 'git_diff_check':subprocess.run(['git','-C',str(R),'diff','--check','HEAD'],stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode==0,
}
checks['python_compile']=subprocess.run([sys.executable,'-m','py_compile',str(Path(__file__)),str(R/'experiments/stage3d-consumer-integration/verify-gate2-consumer-census.py'),str(R/'experiments/stage3d-consumer-integration/verify-gate3-system-python-contract.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode==0
failed=sorted(k for k,v in checks.items() if not v); out={'schema_version':1,'verification_kind':'project-control-plane-reconciliation','pass':not failed,'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':failed,'checks':dict(sorted(checks.items())),'observed':{'head':subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip(),'tree_before_commit':subprocess.check_output(['git','-C',str(R),'write-tree'],text=True).strip(),'gate3_authority_sha256':hashlib.sha256((R/'experiments/stage3d-consumer-integration/gate3-system-python-contract.json').read_bytes()).hexdigest()},'claim_boundary':'Current repository context and contract alignment only; Gate 4 target behavior remains pending.'}
print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['pass'] else 1)

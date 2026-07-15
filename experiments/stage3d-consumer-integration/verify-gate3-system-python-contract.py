#!/usr/bin/env python3
"""Verify the Stage 3-D Gate 3 contract and Gate 4 validation design."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; EXP=Path(__file__).resolve().parent

def load(name): return json.loads((EXP/name).read_text())
def text(rel): return (ROOT/rel).read_text()
checks={}
def ck(k,v):
 if k in checks: raise RuntimeError(k)
 checks[k]=bool(v)

g2=load('gate2-consumer-census-authority.json'); g3=load('gate3-system-python-contract.json'); m=load('gate4-consumer-integration-validation-matrix.json')
ctx=text('docs/PROJECT_CONTEXT_STAGE3D.md'); scope=text('docs/stages/STAGE3D_SCOPE.md'); design=text('experiments/stage3d-consumer-integration/GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT.md'); census=text('experiments/stage3d-consumer-integration/GATE2_READ_ONLY_CONSUMER_CENSUS.md'); readme=text('README.md'); handoff=text('docs/handoff/README.md'); ledger=text('docs/handoff/STAGE3D_EVIDENCE_LEDGER.md')
ck('g2_schema',g2['schema_version']==1); ck('g2_kind',g2['authority_kind']=='stage3d-gate2-read-only-consumer-census'); ck('g2_status',g2['status']=='target-evidence-accepted')
ck('g2_archive',g2['result_archive']['sha256']=='4958b3e669950035f21baf5783fa54029366182cdc36ecf1fb909dfb8276e98c' and g2['result_archive']['size']==61374)
ck('g2_safe',g2['result_archive']['safe_member_count']==849 and g2['result_archive']['self_index_entry_count']==780)
ck('g2_counts',g2['scenario_results']['count']==64 and g2['scenario_results']['expectation_match']==64 and g2['scenario_results']['strict_pass']==12)
ck('g2_process_coverage',g2['process_coverage']=={'process_records':172,'uv_python_find':72,'uv_run':0,'uv_sync':0,'uv_venv':14})
ck('g2_packaging_boundary',g2['packaging_recovery']['census_reexecuted'] is False and g2['packaging_recovery']['retained_evidence_file_count']==734)
ck('g3_schema',g3['schema_version']==1); ck('g3_kind',g3['authority_kind']=='stage3d-gate3-system-python-integration-contract'); ck('g3_status',g3['status']=='contract-frozen')
ck('g3_input_commit',g3['input_authority']['gate1_commit']=='b0b938b6f8d4eea67e2fac1eca83f69c835a9cac'); ck('g3_input_tree',g3['input_authority']['gate1_tree']=='3b86355f3236a850512e8e1bdb6b3e1df73362f5')
ck('g3_input_archive',g3['input_authority']['gate2_archive_sha256']==g2['result_archive']['sha256'])
ck('g3_model',g3['primary_model']=='uv-system-python'); ck('g3_selector',g3['canonical_contract']['selector']=='explicit-absolute-interpreter-path'); ck('g3_interpreter',g3['canonical_contract']['interpreter']=='<installed-prefix>/bin/python')
for flag in ('--no-python-downloads','--offline','--no-managed-python','--system'): ck('find_'+flag,g3['canonical_contract']['find_flags'].count(flag)==1)
ck('venv_python_flag','--python <absolute-interpreter>' in g3['canonical_contract']['venv_flags'])
ck('identity_checks',set(g3['canonical_contract']['required_identity_checks'])=={'selected-realpath','implementation=CPython','exact-patch-version','android-platform','expected-base-prefix'})
ck('secondary_install_dir',any('install-directory' in x for x in g3['supported_surfaces']['bounded_secondary']))
ck('secondary_unique_name',any('unique executable' in x for x in g3['supported_surfaces']['bounded_secondary']))
ck('conditional_minor',set(g3['supported_surfaces']['conditional_not_product_exact'])=={'PATH python3.14','version request 3.14','.python-version 3.14','requires-python within 3.14'})
ck('run_deferred','uv run' in g3['not_yet_supported']); ck('sync_deferred','uv sync' in g3['not_yet_supported']); ck('managed_deferred','managed-Python registration or emulation' in g3['not_yet_supported'])
for item in ('global-prefix-links','shell-startup-edits','managed-install-dir-registration','uv-patching','python-download-fallback','registry-schema-change','journal-schema-change','root','proot','shizuku','docker'): ck('forbidden_'+item,item in g3['mutation_policy']['forbidden'])
ck('gate_sequence',g3['gate_sequence']['gate2']=='FROZEN_TARGET_EVIDENCE' and g3['gate_sequence']['gate3']=='FROZEN_SYSTEM_PYTHON_CONTRACT' and g3['gate_sequence']['gate4']=='ACTIVE_NEXT_TARGET_IMPLEMENTATION_VALIDATION')
rows=m['scenarios']; groups=Counter(r['group'] for r in rows)
ck('matrix_schema',m['schema_version']==1); ck('matrix_kind',m['matrix_kind']=='stage3d-gate4-consumer-integration-target-validation'); ck('matrix_status',m['status']=='design-frozen-not-executed'); ck('matrix_count',m['scenario_count']==48 and len(rows)==48 and len({r['id'] for r in rows})==48)
ck('matrix_groups',groups==Counter({'pending-command-surface':16,'precedence-negative-invariant':12,'explicit-reconfirmation':8,'bounded-discovery':8,'transition-continuity':4}) and dict(groups)==m['group_counts'])
ck('matrix_run',sum(r['operation']=='uv-run-explicit-interpreter' for r in rows)==8); ck('matrix_sync',sum(r['operation']=='uv-sync-explicit-interpreter' for r in rows)==8)
ck('matrix_products',all({r['product'] for r in rows if r['group']==g}=={'3.14.5','3.14.6'} for g in ('explicit-reconfirmation','bounded-discovery')))
ck('matrix_topologies',all({r['topology'] for r in rows if r['group']==g}=={'runtime-only','runtime+development','runtime+test','full'} for g in ('explicit-reconfirmation','bounded-discovery')))
ck('matrix_transition',sum(r['group']=='transition-continuity' for r in rows)==4)
for req in ('python-downloads-disabled','managed-python-disabled','raw-process-evidence','repository-invariant','canonical-product-invariant','global-links-invariant','pass-or-fail-safe-archive'): ck('matrix_req_'+req,req in m['global_requirements'])
ck('ctx_active','Gate 4 target implementation and validation' in ctx and 'Gate 3  system-Python integration contract     FROZEN' in ctx)
ck('ctx_coverage_gap','Gate 2 executed no `uv run` and no `uv sync`' in ctx); ck('scope_active','Gate 3 system-Python contract frozen; Gate 4 next' in scope); ck('scope_48','48-scenario matrix' in scope)
ck('design_exact','absolute installed interpreter path' in design); ck('design_deferred','Gate 2 did not execute `uv run` or `uv sync`' in design); ck('census_coverage','uv python find   72' in census and 'uv sync           0' in census)
ck('readme_status','active — Gate 3 contract frozen; Gate 4 next' in readme); ck('handoff_status','Stage 3-D Gate 4 target implementation/validation       ACTIVE NEXT' in handoff); ck('ledger_archive','4958b3e669950035f21baf5783fa54029366182cdc36ecf1fb909dfb8276e98c' in ledger)
required=['docs/evidence/STAGE3D_GATE2_READ_ONLY_CONSUMER_CENSUS_RESULT.md','docs/evidence/STAGE3D_GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT_RESULT.md','docs/handoff/STAGE3D_EVIDENCE_LEDGER.md','experiments/stage3d-consumer-integration/verify-gate2-consumer-census.py','experiments/stage3d-consumer-integration/run-gate3-system-python-contract.sh']
ck('required_paths',all((ROOT/p).is_file() for p in required)); ck('runner_exec',(EXP/'run-gate3-system-python-contract.sh').stat().st_mode&0o111!=0)
ck('git_diff_check',subprocess.run(['git','-C',str(ROOT),'diff','--check','HEAD'],stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode==0)
ck('python_compile',subprocess.run([sys.executable,'-m','py_compile',str(EXP/'verify-gate2-consumer-census.py'),str(EXP/'verify-gate3-system-python-contract.py'),str(ROOT/'scripts/verify-project-control-plane.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode==0)
failed=sorted(k for k,v in checks.items() if not v); result={'schema_version':1,'verification_kind':'stage3d-gate3-system-python-contract-verification','pass':not failed,'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':failed,'checks':dict(sorted(checks.items())),'observed':{'gate2_authority_sha256':hashlib.sha256((EXP/'gate2-consumer-census-authority.json').read_bytes()).hexdigest(),'gate3_authority_sha256':hashlib.sha256((EXP/'gate3-system-python-contract.json').read_bytes()).hexdigest(),'gate4_matrix_sha256':hashlib.sha256((EXP/'gate4-consumer-integration-validation-matrix.json').read_bytes()).hexdigest(),'tree_before_commit':subprocess.check_output(['git','-C',str(ROOT),'write-tree'],text=True).strip()},'claim_boundary':'Repository acceptance of Gate 2 evidence and Gate 3 contract design only; Gate 4 target behavior remains pending.'}
print(json.dumps(result,indent=2,sort_keys=True)); print(); print(f"STAGE3D_GATE3_SYSTEM_PYTHON_CONTRACT_VERIFICATION={result['pass_count']}/{result['check_count']} {'PASS' if result['pass'] else 'FAIL'}")
raise SystemExit(0 if result['pass'] else 1)

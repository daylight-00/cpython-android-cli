#!/usr/bin/env python3
import hashlib,json,py_compile,re,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
decision_path=root/'experiments/stage3c-gate4-second-product-authority/gate4a-a2b-termux-native-toolchain-authority.json'
audit_path=root/'docs/evidence/STAGE3C_PHASE5_GATE4A_A2B_TERMUX_NATIVE_TOOLCHAIN_EXTERNAL_AUDIT.json'
checks={}
def ck(k,v): checks[k]=bool(v)
def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(p):
 o=load(p); return p.read_bytes()==(json.dumps(o,indent=2,sort_keys=True)+'\n').encode()
D=load(decision_path); A=load(audit_path)
ck('decision_canonical',canonical(decision_path)); ck('audit_canonical',canonical(audit_path))
ck('decision_schema',D.get('schema_version')==1 and D.get('status')=='accepted')
ck('decision_id_exact',D.get('decision_id')=='stage3c-phase5-gate4a-a2b-termux-native-toolchain-authority-20260714')
ck('audit_pass',A.get('pass') is True and A.get('pass_count')==46 and A.get('check_count')==46 and not A.get('failed_checks'))
ck('audit_hash_bound',D['evidence']['external_audit']['sha256']==sha(audit_path))
ck('a2_complete',D['acceptance']['a2_exact_input_and_toolchain_capture']=='complete')
ck('a2a_preserved',D['acceptance']['a2a_remote_inputs']=='frozen-pass')
ck('a2b_accepted',D['acceptance']['a2b_termux_native_binary_toolchain']=='frozen-pass')
ck('a3_ready_only',D['acceptance']['a3_clean_replay']=='ready-not-started')
ck('later_pending',D['acceptance']['a4_through_a6']=='pending')
ck('first_product_unchanged',D['base_design']['historical_first_product_authority_unchanged'])
ck('scoped_exception_explicit','second-product' in D['base_design']['scoped_exception'] and 'first-product' in D['base_design']['scoped_exception'])
asset=D['producer']['asset']; overlay=D['toolchain_overlay']; workflow=D['producer']['workflow']
ck('asset_identity',asset=={'md5':'ab87309abc53830892e0556b91438fa5','name':'android-ndk-r27d-aarch64-linux-android.tar.xz','sha256':'7aac94c85931c698ef13f8679c3472d3d6c7a4566e4c8bff112be91aff527bd7','size':156427268})
ck('ndk_revision',D['producer']['ndk_revision']=='27.3.13750724')
ck('prebuilt_host',D['producer']['prebuilt_host']=='linux-arm64')
ck('producer_binding',workflow=={'commit':'63b097b4db9b1d2ab445d6637eab16718f6c513b','job_id':86867844060,'run_id':29265009312})
ck('authority_remote',D['authority_remote']=='gdrive:HW-T/cpython-android-cli/authorities/gate4a/toolchains/android-ndk-custom/r27/android-aarch64')
ck('original_lld',overlay['original_lld_sha256']=='cf9f6f56dfcb28642025a73f5ba7c7a17966cc2c71bea0ccb0f16c21d07b15b' if False else overlay['original_lld_sha256']=='cf9f6f56dfcb286d52425a73f5ba7c7a17966cc2c71bea0ccb0f16c21d07b15b')
ck('patched_lld',overlay['patched_lld_sha256']=='eee71a33b1c9924eeb576673d033008b1e520f84a112a7102cc9482142bf5a09')
ck('overlay_patch_exact',overlay['patch']=={'after':64,'before':8,'offset':392,'semantic':'ELF64 PT_TLS p_align'})
ck('overlay_ephemeral',overlay['ephemeral'] and not overlay['original_ndk_mutated'])
ck('binary_not_source_claim','source-rebuild reproducibility of android-ndk-custom' in D['claim_boundary']['not_accepted'])
ck('no_official_equivalence','equivalence with the official Linux-host NDK binary set' in D['claim_boundary']['not_accepted'])
ck('no_a3_claim','A3 replay or any product artifact' in D['claim_boundary']['not_accepted'])
ck('base_binding',D['repository_binding']['pre_decision_head']=='33d86c97f630a780e7d9c61421e0c2ba57b0ad6a' and D['repository_binding']['pre_decision_tree']=='f4ad419e9f9476355dd80a663b5e010149de51ba')
expected_archives={'census':'9721c17248b181a934acdf28204df51b7fe3ac308239fed41265948f1ff5b45d','linker_diagnostic':'b9a0c998b4a3059be80f93f5808e547141937920ce64a08910113fb81e80f2d3','overlay_witness':'d71828ede5925d550000666f0a86906682bed8b9c3dca1d004bc4cda2cb1fb59','producer_binding':'bba0ea4c8df4115fee0c5a5c24c33cfa1114f5acf81a1644cfdeeb4810715a2e','provenance_diagnostic':'585fdca325a621eb580e8f56016d1e389ca58a2713fe08fa3a2873fafb38284c'}
ck('archive_bindings',D['evidence']['result_archives']==expected_archives)
# Document alignment
paths=['README.md','docs/PROJECT_CONTEXT_STAGE3C.md','docs/evidence/STAGE3C_PHASE5_GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN_RESULT.md','docs/evidence/STAGE3C_PHASE5_GATE4A_A2B_TERMUX_NATIVE_TOOLCHAIN_AUTHORITY_DECISION.md','docs/handoff/PHASE5_GATE4_UPGRADE_DOWNGRADE_HANDOFF_20260713.md','docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md','docs/stages/STAGE3C_PHASE5_SCOPE.md','experiments/stage3c-gate4-second-product-authority/GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN.md','experiments/stage3c-gate4-second-product-authority/README.md']
texts={p:(root/p).read_text() for p in paths}
ck('root_status','A2 complete; A3 clean replay ready' in texts['README.md'])
ck('context_status','A2 complete; A3 clean replay ready' in texts['docs/PROJECT_CONTEXT_STAGE3C.md'])
ck('scope_status','A2 PASS / A3 READY' in texts['docs/stages/STAGE3C_PHASE5_SCOPE.md'])
ck('handoff_next_a3','Begin Gate 4A A3 clean replay' in texts['docs/handoff/PHASE5_GATE4_UPGRADE_DOWNGRADE_HANDOFF_20260713.md'])
ck('ledger_a2_pass','A2 FROZEN PASS' in texts['docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md'])
ck('experiment_a2_pass','A2 input capture                   FROZEN PASS' in texts['experiments/stage3c-gate4-second-product-authority/README.md'])
ck('decision_doc_identity','7aac94c85931c698ef13f8679c3472d3d6c7a4566e4c8bff112be91aff527bd7' in texts['docs/evidence/STAGE3C_PHASE5_GATE4A_A2B_TERMUX_NATIVE_TOOLCHAIN_AUTHORITY_DECISION.md'])
ck('decision_doc_limits','source-rebuild reproducibility' in texts['docs/evidence/STAGE3C_PHASE5_GATE4A_A2B_TERMUX_NATIVE_TOOLCHAIN_AUTHORITY_DECISION.md'])
ck('design_history_preserved','original workstation topology remains historical design authority' in texts['experiments/stage3c-gate4-second-product-authority/GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN.md'])
for p in [Path(__file__).resolve(),root/'experiments/stage3c-gate4-second-product-authority/verify-gate4a-a2b-termux-native-toolchain-evidence.py']:
 py_compile.compile(str(p),doraise=True)
ck('python_sources_compile',True)
diff=subprocess.run(['git','-C',str(root),'diff','--check'],capture_output=True,text=True)
ck('git_diff_check',diff.returncode==0)
failed=sorted(k for k,v in checks.items() if not v)
out={'schema_version':1,'verification_kind':'stage3c-phase5-gate4a-a2b-termux-native-toolchain-authority-verification','pass':not failed,'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':failed,'checks':dict(sorted(checks.items())),'decision_sha256':sha(decision_path),'audit_sha256':sha(audit_path),'claim_boundary':'Repository authority acceptance only. A2 is complete and A3 is ready but not executed; no second-product artifact or transition behavior is claimed.'}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['pass'] else 41)

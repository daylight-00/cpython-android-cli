#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, py_compile, subprocess
from collections import Counter
from pathlib import Path

FIRST_VERSION='3.14.6'
FIRST_HEAD='c63aec69bd59c55314c06c23f4c22c03de76fe45'
SECOND_VERSION='3.14.5'
SECOND_TAG='v3.14.5'
SECOND_HEAD='5607950ef232dad16d75c0cf53101d9649d89115'
HOST='aarch64-linux-android'
API=24
NDK='27.3.13750724'
SOURCE_SHA='7e32597b99e5d9a39abed35de4693fa169df3e5850d4c334337ffd6a19a36db6'
OFFICIAL_ANDROID_SHA='f008321abf837fcaec569df143283ece0e764b18d8c75763200160553f906af1'
ANDROID_PY_BLOB='ec4d28bbaad84d4db730678a5d627c4703bbb401'
ANDROID_ENV_BLOB='5859c0eac4a88fb552c495d46b77422ac5cdc2f0'
G3B_ARCH='0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b'
G3C_ARCH='43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a'
G3D_ARCH='579b880495098e9a46b40e2d96c9555178d0ad8c725d40768e6b854227d66143'

def cjson(obj): return (json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()
def sha256(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text())
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--project-root',required=True,type=Path)
 p.add_argument('--input',required=True,type=Path)
 p.add_argument('--matrix',required=True,type=Path)
 p.add_argument('--output',required=True,type=Path)
 p.add_argument('--require-pass',action='store_true')
 a=p.parse_args(); root=a.project_root.resolve(); inp=load(a.input); matrix=load(a.matrix)
 checks={}
 def ck(name,cond): checks[name]=bool(cond)
 # selected input
 ck('input_schema',inp.get('schema_version')==1)
 ck('input_kind',inp.get('verification_kind')=='stage3c-phase5-gate4a-second-product-authority-selected-input')
 ck('input_status',inp.get('status')=='selected-design-input-input-capture-pending')
 ck('input_claim_selection_only','not a product lock' in inp.get('claim_boundary','') and 'transition design' in inp.get('claim_boundary',''))
 first=inp.get('first_product',{}); second=inp.get('second_product_selection',{})
 ck('first_version',first.get('python_version')==FIRST_VERSION)
 ck('first_tag',first.get('source_tag')=='v3.14.6')
 ck('first_head',first.get('source_head')==FIRST_HEAD)
 ck('first_host',first.get('target_host')==HOST)
 ck('first_api',first.get('android_api')==API)
 ck('first_ndk',first.get('ndk_version')==NDK)
 ck('first_lock_path',first.get('product_lock')=='config/products/cpython-3.14.6-aarch64-linux-android.lock.json')
 ck('first_dep_lock_path',first.get('dependency_lock')=='config/dependencies/android-source-deps-aarch64-linux-android.lock.json')
 ck('second_version',second.get('python_version')==SECOND_VERSION)
 ck('second_tag',second.get('source_tag')==SECOND_TAG)
 ck('second_head',second.get('source_head')==SECOND_HEAD)
 ck('second_selection_class',second.get('selection_class')=='immediate-stable-predecessor-same-minor')
 ck('second_host',second.get('target_host')==HOST)
 ck('second_api',second.get('android_api')==API)
 ck('second_ndk',second.get('ndk_version')==NDK)
 refs=second.get('official_references',{})
 src=refs.get('source_tar_xz',{}); off=refs.get('android_aarch64_package',{})
 ck('source_reference_filename',src.get('filename')=='Python-3.14.5.tar.xz')
 ck('source_reference_url',src.get('url')=='https://www.python.org/ftp/python/3.14.5/Python-3.14.5.tar.xz')
 ck('source_reference_sha',src.get('sha256')==SOURCE_SHA)
 ck('source_reference_role',src.get('authority_role')=='reference-only')
 ck('official_android_filename',off.get('filename')=='python-3.14.5-aarch64-linux-android.tar.gz')
 ck('official_android_url',off.get('url')=='https://www.python.org/ftp/python/3.14.5/python-3.14.5-aarch64-linux-android.tar.gz')
 ck('official_android_sha',off.get('sha256')==OFFICIAL_ANDROID_SHA)
 ck('official_android_not_authority',off.get('authority_role')=='reference-only-not-project-product')
 producer=second.get('source_native_producer',{})
 ck('android_py_blob',producer.get('Android/android.py',{}).get('git_blob_sha')==ANDROID_PY_BLOB)
 ck('android_py_sha_pending',producer.get('Android/android.py',{}).get('sha256_status')=='capture-required')
 ck('android_env_blob',producer.get('Android/android-env.sh',{}).get('git_blob_sha')==ANDROID_ENV_BLOB)
 ck('android_env_sha_pending',producer.get('Android/android-env.sh',{}).get('sha256_status')=='capture-required')
 deps=inp.get('dependency_selection',{}); products=deps.get('products',[])
 expected=[('bzip2','bzip2-1.0.8-3'),('libffi','libffi-3.4.4-3'),('openssl','openssl-3.0.20-0'),('sqlite','sqlite-3.50.4-0'),('xz','xz-5.4.6-1'),('zstd','zstd-1.5.7-2')]
 ck('dependency_rule_source_native','exact v3.14.5 Android/android.py' in deps.get('authority_rule',''))
 ck('dependency_count_6',len(products)==6)
 ck('dependency_order_exact',[(x.get('name'),x.get('release_tag')) for x in products]==expected)
 ck('dependency_filenames_exact',all(x.get('filename')==f"{x.get('release_tag')}-{HOST}.tar.gz" for x in products))
 openssl=next((x for x in products if x.get('name')=='openssl'),{})
 ck('openssl_3020',openssl.get('release_tag')=='openssl-3.0.20-0')
 ck('openssl_fresh_capture',openssl.get('identity_source')=='fresh-capture-required')
 ck('openssl_real_delta',openssl.get('differs_from_first_product') is True)
 ck('other_dep_identity_rule',all(x.get('identity_source')=='reusable-first-lock-plus-fresh-download-verification' for x in products if x.get('name')!='openssl'))
 req_outputs=set(inp.get('required_authority_outputs',[]))
 for key,text in {
  'output_runtime':'runtime-base archive and manifest','output_dev':'development-addon archive and manifest','output_test':'test-addon archive and manifest',
  'output_lock':'product lock and manifest index','output_registry':'ownership registry template','output_closure':'native closure evidence',
  'output_behavior':'runtime and addon behavior evidence','output_provenance':'exact source, producer, dependency, toolchain, and build provenance',
  'output_byte_exact':'byte-exact archive and manifest identities'}.items(): ck(key,text in req_outputs)
 shortcuts=set(inp.get('forbidden_shortcuts',[]))
 ck('shortcut_no_version_edit','manual version-string editing' in shortcuts)
 ck('shortcut_no_relabel','copying first-product payload and relabeling it' in shortcuts)
 ck('shortcut_official_not_authority','using the official Python.org Android package as the project product authority' in shortcuts)
 ck('shortcut_no_first_lock_reuse','reusing the first product lock as the second product lock' in shortcuts)
 ck('shortcut_no_transition_early','starting transition policy or target scenarios before independent second-product freeze' in shortcuts)
 # matrix structure
 ck('matrix_schema',matrix.get('schema_version')==1)
 ck('matrix_kind',matrix.get('verification_kind')=='stage3c-phase5-gate4a-second-product-authority-design-matrix')
 ck('matrix_status',matrix.get('status')=='design-frozen-input-capture-pending')
 ck('matrix_input_path',matrix.get('selected_input')=='experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-input.json')
 stages=matrix.get('stages',[]); expected_stage_ids=['A1','A2','A3','A4','A5','A6']
 ck('stage_count_6',matrix.get('stage_count')==6 and len(stages)==6)
 ck('stage_ids_exact',[x.get('id') for x in stages]==expected_stage_ids)
 ck('stage_names_exact',[x.get('name') for x in stages]==['selection-and-design','input-capture','upstream-replay','three-artifact-materialization','standalone-target-validation','external-audit-and-freeze'])
 ck('stage_locations_exact',[x.get('execution_location') for x in stages]==['repository','workstation','workstation','workstation','termux','independent'])
 ck('only_a1_frozen',stages[0].get('status')=='design-frozen-input-capture-pending' and all(x.get('status')=='pending' for x in stages[1:]))
 requirements=matrix.get('requirements',[])
 ck('requirement_count_36',matrix.get('requirement_count')==36 and len(requirements)==36)
 ids=[x.get('id') for x in requirements]
 ck('requirement_ids_unique',len(ids)==len(set(ids)))
 ck('requirement_ids_prefix',all(i.startswith('G4A-') for i in ids))
 groups=Counter(x.get('group') for x in requirements)
 ck('requirement_group_counts',groups==Counter({'identity':6,'producer':6,'replay':5,'materialization':5,'target':5,'freeze':5,'claim':4}))
 ck('requirements_have_evidence',all(x.get('statement') and x.get('required_evidence') for x in requirements))
 # Important semantic requirements
 statements='\n'.join(x.get('statement','') for x in requirements)
 for name,term in {
   'req_immediate_predecessor':'immediate stable predecessor','req_exact_commit':SECOND_HEAD,'req_reference_not_authority':'reference identities, not the project product authority',
   'req_openssl_delta':'OpenSSL 3.0.20-0','req_all_dependencies':'All six dependency assets','req_clean_worktree':'clean source worktree',
   'req_no_payload_copy':'No first-product payload bytes','req_three_artifacts':'Runtime-base, development-addon, and test-addon',
   'req_disjoint_ownership':'disjoint artifact ownership','req_termux_fresh':'fresh inode-separated Termux roots','req_uv':'uv explicit interpreter',
   'req_no_transition_target':'No upgrade or downgrade operation','req_pass_fail_archive':'complete result archive','req_archive_safety':'Archive members are safe',
   'req_external_audit':'Independent audit','req_first_authority_immutable':'remain immutable inputs','req_no_transition_policy':'No mixed-version compatibility',
   'req_a6_gate':'only after A6 independent freeze'
 }.items(): ck(name,term in statements)
 ec=matrix.get('execution_contract',{})
 ck('execution_zstd',ec.get('new_evidence_archive_suffix')=='.tar.zst')
 ck('execution_pass_fail',ec.get('pass_or_fail_archive_required') is True)
 ck('execution_tgz_immutable',ec.get('historical_tgz_immutable') is True)
 ck('execution_sync_raw',ec.get('synchronous_raw_stdout_stderr') is True)
 ck('execution_real_rc',ec.get('real_returncodes') is True)
 ck('execution_canonical_json',ec.get('canonical_json') is True)
 ck('execution_indexes',ec.get('complete_result_indexes') is True)
 ck('execution_external_audit',ec.get('independent_external_audit') is True)
 claim=matrix.get('claim_boundary',{})
 ck('claim_design_scope','genuine v3.14.5 source-native producer input' in claim.get('proved_by_design',''))
 ck('claim_no_product','No second-product archive' in claim.get('not_proved_by_design',''))
 ck('claim_no_transition','upgrade' in claim.get('not_proved_by_design','') and 'downgrade' in claim.get('not_proved_by_design',''))
 ck('claim_a6_required',claim.get('transition_design_requires')=='A6 independently frozen second-product authority.')
 # Existing first product locks remain exact
 first_lock=load(root/first['product_lock']); dep_lock=load(root/first['dependency_lock'])
 ck('repo_first_lock_version',first_lock.get('python_version')==FIRST_VERSION)
 ck('repo_first_lock_head',first_lock.get('source_head')==FIRST_HEAD)
 ck('repo_first_lock_host',first_lock.get('target_host')==HOST)
 ck('repo_first_lock_api',first_lock.get('android_api')==API)
 ck('repo_first_lock_ndk',first_lock.get('ndk_version')==NDK)
 ck('repo_dep_lock_head',dep_lock.get('source_head')==FIRST_HEAD)
 ck('repo_dep_lock_openssl_357',next(x for x in dep_lock.get('products',[]) if x.get('name')=='openssl').get('release_tag')=='openssl-3.5.7-0')
 # Documentation/control-plane alignment
 doc_paths={
  'design':'experiments/stage3c-gate4-second-product-authority/GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN.md',
  'readme':'experiments/stage3c-gate4-second-product-authority/README.md',
  'root_readme':'README.md','context':'docs/PROJECT_CONTEXT_STAGE3C.md','scope':'docs/stages/STAGE3C_PHASE5_SCOPE.md',
  'handoff':'docs/handoff/PHASE5_GATE4_UPGRADE_DOWNGRADE_HANDOFF_20260713.md','ledger':'docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md',
  'handoff_readme':'docs/handoff/README.md','evidence':'docs/evidence/STAGE3C_PHASE5_GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN_RESULT.md'}
 texts={k:(root/v).read_text() for k,v in doc_paths.items()}
 ck('design_status',('DESIGN FROZEN — exact input capture pending' in texts['design']) or ('FROZEN PASS — A1-A6 complete' in texts['design']))
 ck('design_second_identity',SECOND_VERSION in texts['design'] and SECOND_HEAD in texts['design'])
 ck('design_openssl_delta','OpenSSL 3.0.20-0' in texts['design'] and 'OpenSSL 3.5.7-0' in texts['design'])
 ck('design_six_stages',all(f'{x} ' in texts['design'] for x in expected_stage_ids))
 ck('design_no_transition','does not freeze' in texts['design'] and 'upgrade' in texts['design'] and 'downgrade' in texts['design'])
 ck('experiment_readme_selected',SECOND_HEAD in texts['readme'] and ('input capture pending' in texts['readme'] or 'A2 input capture                 FROZEN PASS' in texts['readme'] or 'A6 independent freeze            FROZEN PASS' in texts['readme']))
 ck('root_readme_gate4a','CPython 3.14.5' in texts['root_readme'] and 'Gate 4A' in texts['root_readme'])
 ck('context_gate4a',('CPython 3.14.5' in texts['context'] or 'CPython version  3.14.5' in texts['context']) and 'A1' in texts['context'] and 'A6' in texts['context'])
 ck('scope_gate4a','Gate 4A' in texts['scope'] and '3.14.5' in texts['scope'])
 ck('handoff_selection','Selected second product' in texts['handoff'] and SECOND_HEAD in texts['handoff'])
 ck('handoff_no_target','No second-product target authority' in texts['handoff'])
 ck('ledger_design_entry','Gate 4A — second-product authority acquisition design' in texts['ledger'] and ('input capture pending' in texts['ledger'] or 'A2 FROZEN PASS' in texts['ledger']))
 ck('handoff_reading_path','GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN.md' in texts['handoff_readme'])
 ck('evidence_design_pass','DESIGN FROZEN' in texts['evidence'] and 'second-product artifact authority is not yet created' in texts['evidence'])
 ck('frozen_hashes_present',all(h in texts['ledger']+texts['handoff'] for h in [G3B_ARCH,G3C_ARCH,G3D_ARCH]))
 # repository health
 py_compile.compile(str(Path(__file__).resolve()),doraise=True)
 ck('python_source_compiles',True)
 diff=subprocess.run(['git','-C',str(root),'diff','--check'],capture_output=True,text=True)
 ck('git_diff_check',diff.returncode==0)
 failed=sorted(k for k,v in checks.items() if not v)
 result={
  'schema_version':1,'verification_kind':'stage3c-phase5-gate4a-second-product-authority-design-verification',
  'pass':not failed,'check_count':len(checks),'pass_count':sum(checks.values()),'checks':checks,'failed_checks':failed,
  'input_sha256':sha256(a.input.resolve()),'matrix_sha256':sha256(a.matrix.resolve()),
  'observed':{'selected_second_version':second.get('python_version'),'selected_source_head':second.get('source_head'),'stage_count':len(stages),'requirement_count':len(requirements),'requirement_group_counts':dict(groups)},
  'claim_boundary':claim}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(cjson(result))
 print(json.dumps(result,indent=2,sort_keys=True))
 print(f"\nGATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN_VERIFICATION={result['pass_count']}/{result['check_count']} "+('PASS' if result['pass'] else 'FAIL'))
 return 0 if result['pass'] or not a.require_pass else 41
if __name__=='__main__': raise SystemExit(main())

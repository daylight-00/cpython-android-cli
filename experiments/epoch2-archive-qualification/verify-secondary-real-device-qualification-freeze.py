#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
from typing import Any
AUTH='experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json'
AUDIT='experiments/epoch2-archive-qualification/secondary-real-device-qualification-external-audit.json'
RESULT='a3231adb62c47cb17dda16b66207f3c976aa20593e2288a7d381052154147c10'
SECONDARY='6f869abe00b6e5fd50d85965dea84a12f7b6ce4c90ef20182f24831ed4b03d5d'
PRIMARY='9fbd2ce1f9c288bcdb92b19c0fffce24086671d40b2cce658f524935ad473ab1'
BASE_HEAD='054f9a154b5f0438d78835edda506ec4df5247e6'
BASE_TREE='194b31aac8e07afa6c654ff22f5954ceff1388ed'
def canonical(v:Any)->bytes:return (json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
def read(p:Path)->dict[str,Any]:
 raw=p.read_bytes(); v=json.loads(raw)
 if not isinstance(v,dict) or raw!=canonical(v): raise ValueError(p)
 return v
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(root:Path,*args:str)->str:return subprocess.run(['git',*args],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout.strip()
def evaluate(root:Path)->dict[str,Any]:
 a=read(root/AUTH); u=read(root/AUDIT); checks={}
 def ck(n,v):checks[n]=bool(v)
 ck('branch_main',git(root,'branch','--show-current')=='main')
 ck('diff_check',subprocess.run(['git','diff','--check','HEAD'],cwd=root).returncode==0)
 ck('identity',a.get('authority_kind')=='e2p3-secondary-real-device-qualification-freeze' and a.get('authority_version')==1 and a.get('status')=='frozen-pass-dual-real-device-aarch64-termux-compatibility')
 ck('predecessor',a.get('predecessor')=={'commit':BASE_HEAD,'tree':BASE_TREE})
 p=a.get('product',{}); ck('product',p.get('envelope_archive_sha256')=='66c2a39b7164701d3a14cff538be298abcf30c696150f6abf7785e212c1b4727' and p.get('release_index_sha256')=='64825d3afabbda7c90992debfb11e771baeff5514f2b6e6d13584dc7ac6fcf85' and p.get('private_authority_index_sha256')=='5fd8c03b53bcb749cfa221277e75f16b2392e6cec3a184b716f98e24d84fe0b5')
 pr=a.get('primary_profile',{}); ck('primary_identity',pr.get('android_api')==36 and pr.get('hardware')=='qcom' and pr.get('target_authority_index_sha256')==PRIMARY)
 ck('primary_verification',(pr.get('qualification'),pr.get('result_verifier'),pr.get('independent_review'))==('35/35','19/19','38/38'))
 sr=a.get('secondary_profile',{}); ck('secondary_identity',sr.get('device')=='Samsung Galaxy Note9' and sr.get('soc')=='Exynos 9810' and sr.get('android_api')==29 and sr.get('hardware')=='samsungexynos9810' and sr.get('qemu') is False)
 ck('secondary_verification',(sr.get('qualification'),sr.get('result_verifier'),sr.get('independent_review'))==('35/35','19/19','41/41'))
 ck('secondary_result',sr.get('result_archive_sha256')==RESULT and sr.get('result_archive_size')==17319)
 ck('secondary_target',sr.get('target_authority_index_sha256')==SECONDARY and sr.get('target_authority_index_size')==8692 and sr.get('target_authority_indexed_file_count')==36)
 c=a.get('closure',{}); ck('closure',c=={'accepted_claim':'dual-real-device-aarch64-termux-compatibility','profiles':['termux-real-primary-s22-ultra-api36','termux-real-secondary-exynos9810-api29'],'same_product_bytes':True,'same_qualifier_matrix':True,'upstream_thin_roadmap_affected':False})
 b=a.get('claim_boundary',{}); ck('dual_claim',b.get('dual_real_device_acceptance') is True)
 ck('individual_claims',b.get('individual_primary_real_profile') is True and b.get('individual_secondary_real_profile') is True)
 ck('emulator_unclaimed',b.get('emulator_profile') is False and b.get('combined_real_emulator_acceptance') is False and b.get('original_contract_fully_satisfied') is False)
 ck('product_unselectable',b.get('selectability') is False and b.get('publication') is False and b.get('metadata_finalization') is False)
 ck('other_unclaimed',b.get('installer_conversion') is False and b.get('transition_behavior') is False)
 ck('next_action',a.get('next_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control')
 src=u.get('source',{}); ck('audit_identity',u.get('audit_kind')=='e2p3-secondary-real-device-qualification-freeze-external-audit' and u.get('pass') is True and u.get('failed_checks')==[] and u.get('check_count')==u.get('pass_count'))
 ck('audit_authority',src.get('authority_sha256')==sha(root/AUTH))
 ck('audit_sources',src.get('result_archive_sha256')==RESULT and src.get('secondary_target_authority_index_sha256')==SECONDARY and src.get('primary_target_authority_index_sha256')==PRIMARY)
 ck('audit_checks',isinstance(u.get('checks'),dict) and len(u['checks'])==u.get('check_count') and all(u['checks'].values()))
 current=(root/'docs/CURRENT_CONTEXT.md').read_text(); road=(root/'docs/roadmap/EPOCH2_ROADMAP.md').read_text(); exp=(root/'experiments/epoch2-archive-qualification/README.md').read_text()
 ck('current_navigation','dual-device claim     accepted — AArch64 Termux compatibility' in current and 'accepted and frozen' in current)
 ck('roadmap_navigation','dual-real-device AArch64 Termux compatibility' in road and 'original real-plus-emulator contract remain unqualified' in road)
 ck('experiment_navigation','Secondary real-device freeze' in exp and SECONDARY in exp)
 ck('evidence_doc',(root/'docs/evidence/E2P3_SECONDARY_REAL_DEVICE_QUALIFICATION_AUTHORITY_FREEZE.md').is_file())
 ck('handoff_doc',(root/'docs/handoff/2026-07-19-e2p3-secondary-real-device-qualification-authority-freeze.md').is_file())
 ck('old_authorities_preserved',sha(root/'experiments/epoch2-archive-qualification/secondary-real-device-amendment-authority.json')=='65d8da89b5e3098563075b0f57d7ae6612c56321c931d0d8651d0b085848b0d6' and sha(root/'experiments/epoch2-archive-qualification/secondary-real-device-amendment-external-audit.json')=='53640fd08efc796ac017dc3a211bcb0089371e794e784f3f525a28fd977eba54')
 failed=sorted(k for k,v in checks.items() if not v)
 return {'schema_version':1,'verification_kind':'e2p3-secondary-real-device-qualification-freeze','pass':not failed,'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':failed,'checks':dict(sorted(checks.items()))}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);a=ap.parse_args();r=evaluate(a.root.resolve());print(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True));return 0 if r['pass'] else 1
if __name__=='__main__':raise SystemExit(main())

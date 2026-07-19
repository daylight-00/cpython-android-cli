#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, shutil, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_upstream_control import REQUIRED, verify
from freeze_upstream_control import classify_packaged_elf

def dump(p,o): p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fixture(root: Path):
 out=root/'experiments/epoch2-upstream-thin-control'; out.mkdir(parents=True)
 pkg='a'*64
 members=[{'path':f'prefix/f{i}','type':'file','sha256':'b'*64} for i in range(101)]
 objs=[{'path':'prefix/lib/libpython3.14.so','machine':'AArch64'}]
 docs={
 'gate-contract.json':{'gate_id':'E2-R1/UT-0','work_class':'L','required_roles':list(REQUIRED)},
 'upstream-input-manifest.json':{'version':'3.14.6','target':'aarch64-linux-android','minimum_android_api':21,'sha256':pkg,'expected_sha256':pkg,'identity_checks':{'x':True}},
 'package-and-file-hashes.json':{'package_sha256':pkg,'archive_member_count':101,'members':members,'extraction_byte_mismatch_paths':[],'archive_member_manifest_sha256':'c'*64,'prefix_snapshot_sha256':'d'*64},
 'elf-and-extension-inventory.json':{'elf_count':1,'elf_objects':objs,'native_extension_count':1,'native_extensions':['prefix/lib/python3.14/lib-dynload/_x.so']},
 'dependency-provider-map.json':{'unresolved_edges':[],'unclassified_packaged_elf':[],'dependency_products':[{'classification':'beeware-inherited-dependency','soname':'libssl_python.so'}]},
 'sysconfig-census.json':{'selected_version':'3.14.6','selected_target':'aarch64-linux-android','selected_minimum_android_api':21,'build_details':[{}]},
 'package-layout-map.json':{'has_prefix_root':True,'prefix_member_count':101,'license_paths':['prefix/LICENSE']},
 'provenance-map.json':{'provenance_gaps':[],'patches':{'project_local_patches':[],'binary_mutations':[]}},
 'producer-delta.json':{'official':{'package_sha256':pkg},'comparison_boundary':'official binary-derived control versus reconstructed','non_claims':['runtime execution']},
 'independent-audit.json':{'pass':True,'failed_checks':[],'blockers':[]},
 }
 for f,o in docs.items(): dump(out/f,o)
 ids={f:sha(out/f) for f in docs}
 auth={'status':'frozen-pass-exact-official-upstream-control','official_input':{'sha256':pkg},'file_identities':ids,'claim_boundary':{'official_upstream_identity':True,'android_runtime':False,'publication':False}}
 dump(out/'upstream-control-authority.json',auth); a=sha(out/'upstream-control-authority.json')
 (out/'evidence-freeze.md').write_text(a+'\n'+pkg+'\n')
 return out

def main():
 tmp=Path(tempfile.mkdtemp(prefix='ut0-verifier-test-')); checks={}
 try:
  checks['openssl_engine_classification']=classify_packaged_elf('afalg.so',['prefix/lib/engines-3/afalg.so'],[])=='beeware-inherited-openssl-component'
  checks['openssl_provider_classification']=classify_packaged_elf('legacy.so',['prefix/lib/ossl-modules/legacy.so'],[])=='beeware-inherited-openssl-component'
  a=tmp/'success'; fixture(a); checks['success']=verify(a,'experiments/epoch2-upstream-thin-control')['pass']
  b=tmp/'negative'; shutil.copytree(a,b); p=b/'experiments/epoch2-upstream-thin-control/dependency-provider-map.json'; o=json.loads(p.read_text()); o['unresolved_edges']=[{'needed':'bad.so'}]; dump(p,o); checks['expected_negative']=not verify(b,'experiments/epoch2-upstream-thin-control')['pass']
  c=tmp/'missing'; shutil.copytree(a,c); (c/'experiments/epoch2-upstream-thin-control/sysconfig-census.json').unlink(); checks['incomplete_missing']=not verify(c,'experiments/epoch2-upstream-thin-control')['pass']
 finally: shutil.rmtree(tmp,ignore_errors=True)
 failed=[k for k,v in checks.items() if not v]; out={'schema_version':1,'test_kind':'e2-r1-ut0-verifier-fixtures','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks}; print(json.dumps(out,indent=2,sort_keys=True)); return 0 if out['pass'] else 1
if __name__=='__main__': sys.exit(main())

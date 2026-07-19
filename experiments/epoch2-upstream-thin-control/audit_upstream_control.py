#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

FILES = [
    "gate-contract.json","upstream-input-manifest.json","package-and-file-hashes.json",
    "elf-and-extension-inventory.json","dependency-provider-map.json","sysconfig-census.json",
    "package-layout-map.json","provenance-map.json","producer-delta.json",
]

def load(p: Path): return json.loads(p.read_text(encoding="utf-8"))
def sha(p: Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--output-dir',default='experiments/epoch2-upstream-thin-control'); ap.add_argument('--archive',required=True); x=ap.parse_args()
    root=Path(x.root).resolve(); out=root/x.output_dir; archive=Path(x.archive).resolve(); checks={}; errors={}
    def ck(n,v,e=''): checks[n]=bool(v); errors.update({n:e} if not v and e else {})
    try:
        docs={f:load(out/f) for f in FILES}; ck('parse',True)
    except Exception as e: docs={}; ck('parse',False,str(e))
    missing=[f for f in FILES if not (out/f).is_file()]; ck('required_primary_outputs',not missing,','.join(missing))
    m=docs.get('upstream-input-manifest.json',{}); h=docs.get('package-and-file-hashes.json',{}); e=docs.get('elf-and-extension-inventory.json',{}); d=docs.get('dependency-provider-map.json',{}); s=docs.get('sysconfig-census.json',{}); l=docs.get('package-layout-map.json',{}); p=docs.get('provenance-map.json',{}); delta=docs.get('producer-delta.json',{})
    actual=sha(archive) if archive.is_file() else None
    ck('archive_identity',actual is not None and actual==m.get('sha256')==m.get('expected_sha256')==h.get('package_sha256'))
    ids=m.get('identity_checks',{}); ck('identity_checks',bool(ids) and all(ids.values()),str(ids))
    members=h.get('members',[]); paths=[q.get('path') for q in members]; ck('member_manifest_nonempty',len(members)>100 and len(paths)==len(set(paths)))
    ck('no_extraction_mismatch',h.get('extraction_byte_mismatch_paths')==[])
    elfs=e.get('elf_objects',[]); ck('elf_shape',e.get('elf_count')==len(elfs)>0 and e.get('native_extension_count')==len(e.get('native_extensions',[]))>0)
    ck('elf_machine',all('AArch64' in (q.get('machine') or '') for q in elfs),str(sorted({q.get('machine') for q in elfs})))
    ck('dependency_closure',d.get('unresolved_edges')==[])
    ck('provider_classification',d.get('unclassified_packaged_elf')==[])
    ck('beeware_dependency_set',any(q.get('classification')=='beeware-inherited-dependency' for q in d.get('dependency_products',[])))
    ck('sysconfig_identity',s.get('selected_version')=='3.14.6' and s.get('selected_target')=='aarch64-linux-android' and isinstance(s.get('selected_minimum_android_api'),int))
    ck('build_details',bool(s.get('build_details')) and l.get('build_details_paths'))
    ck('prefix_topology',l.get('has_prefix_root') is True and l.get('prefix_member_count',0)>100)
    ck('license_provenance',bool(l.get('license_paths')) and p.get('provenance_gaps')==[])
    ck('no_local_mutation',p.get('patches',{}).get('project_local_patches')==[] and p.get('patches',{}).get('binary_mutations')==[])
    ck('producer_delta_bounded',delta.get('comparison_boundary','').startswith('official binary-derived control') and 'runtime execution' in delta.get('non_claims',[]))
    file_ids={f:sha(out/f) for f in FILES if (out/f).is_file()}
    failed=[k for k,v in checks.items() if not v]
    result={'schema_version':1,'audit_kind':'e2-r1-ut0-independent-audit','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors,'source_file_identities':file_ids,'blockers':[] if not failed else failed}
    (out/'independent-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result['pass'] else 1
if __name__=='__main__': sys.exit(main())

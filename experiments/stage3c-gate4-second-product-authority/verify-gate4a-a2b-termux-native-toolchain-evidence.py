#!/usr/bin/env python3
import argparse, hashlib, json, os, shutil, subprocess, tarfile, tempfile
from pathlib import Path, PurePosixPath

EXPECTED = {
  'census': ('20260714-gate4a-termux-native-toolchain-census-results-20260713T234254Z.tar.zst', '9721c17248b181a934acdf28204df51b7fe3ac308239fed41265948f1ff5b45d'),
  'diagnostic': ('20260714-gate4a-termux-native-r27d-linker-diagnostic-results-20260713T235552Z.tar.zst', 'b9a0c998b4a3059be80f93f5808e547141937920ce64a08910113fb81e80f2d3'),
  'witness': ('20260714-gate4a-termux-native-r27d-overlay-witness-results-20260714T001052Z.tar.zst', 'd71828ede5925d550000666f0a86906682bed8b9c3dca1d004bc4cda2cb1fb59'),
  'provenance': ('20260714-gate4a-termux-native-r27d-provenance-results-20260714T002502Z.tar.zst', '585fdca325a621eb580e8f56016d1e389ca58a2713fe08fa3a2873fafb38284c'),
  'binding': ('20260714-gate4a-termux-native-r27d-producer-binding-results-20260714T010035Z.tar.zst', 'bba0ea4c8df4115fee0c5a5c24c33cfa1114f5acf81a1644cfdeeb4810715a2e'),
}
BASE_HEAD='33d86c97f630a780e7d9c61421e0c2ba57b0ad6a'
BASE_TREE='f4ad419e9f9476355dd80a663b5e010149de51ba'
MAIN='b5a2ca39d1250122312355dd3dbc6165b9409786'
ASSET_SHA='7aac94c85931c698ef13f8679c3472d3d6c7a4566e4c8bff112be91aff527bd7'
ASSET_SIZE=156427268
ORIGINAL_LLD='cf9f6f56dfcb286d52425a73f5ba7c7a17966cc2c71bea0ccb0f16c21d07b15b'
PATCHED_LLD='eee71a33b1c9924eeb576673d033008b1e520f84a112a7102cc9482142bf5a09'
PRODUCER='63b097b4db9b1d2ab445d6637eab16718f6c513b'
AUTHORITY='gdrive:HW-T/cpython-android-cli/authorities/gate4a/toolchains/android-ndk-custom/r27/android-aarch64'

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def canonical(path):
    raw=path.read_bytes(); obj=json.loads(raw)
    return raw == (json.dumps(obj,indent=2,sort_keys=True)+'\n').encode()

def extract(label, archive, work):
    tar_path=work/(label+'.tar')
    with open(tar_path,'wb') as out:
        cp=subprocess.run(['zstd','-q','-d','-c',str(archive)],stdout=out)
    if cp.returncode: raise RuntimeError(f'zstd failed for {label}')
    dest=work/label; dest.mkdir()
    problems=[]; seen=set(); counts={'regular':0,'directory':0,'other':0}
    with tarfile.open(tar_path,'r:') as tf:
        roots=set()
        for m in tf.getmembers():
            n=m.name; p=PurePosixPath(n)
            if n.startswith('/') or '..' in p.parts: problems.append('unsafe-name:'+n)
            if n in seen: problems.append('duplicate:'+n)
            seen.add(n)
            if p.parts: roots.add(p.parts[0])
            if m.isfile(): counts['regular']+=1
            elif m.isdir(): counts['directory']+=1
            else:
                counts['other']+=1
                if m.issym() or m.islnk():
                    t=PurePosixPath(m.linkname)
                    if m.linkname.startswith('/') or '..' in t.parts: problems.append('unsafe-link:'+n)
        if problems: raise RuntimeError(f'{label}: {problems[:3]}')
        tf.extractall(dest, filter='fully_trusted')
    if len(roots)!=1: raise RuntimeError(f'{label}: roots={sorted(roots)}')
    return dest/next(iter(roots)), counts

def load(root, rel): return json.loads((root/rel).read_text())

def verify_index(root):
    idx=load(root,'result-index.json'); entries=idx['files']; declared=idx['file_count']
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='result-index.json'}
    probs=[]
    if declared!=len(entries) or set(e['path'] for e in entries)!=actual: probs.append('membership')
    for e in entries:
        p=root/e['path']
        if not p.is_file() or p.stat().st_size!=e['size'] or sha256(p)!=e['sha256']: probs.append(e['path'])
    return {'declared':declared,'actual':len(actual),'entries':len(entries),'problems':probs,'exact':not probs,'sha256':sha256(root/'result-index.json')}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('evidence_dir'); ap.add_argument('--output')
    a=ap.parse_args(); ev=Path(a.evidence_dir)
    checks={}; details={'archives':{}}; roots={}
    def ck(n,v): checks[n]=bool(v)
    with tempfile.TemporaryDirectory(prefix='gate4a-a2b-audit-') as td:
      work=Path(td)
      for label,(name,want) in EXPECTED.items():
        p=ev/name; ck(f'{label}_archive_present',p.is_file())
        if not p.is_file(): continue
        got=sha256(p); ck(f'{label}_archive_sha256',got==want)
        root,counts=extract(label,p,work); roots[label]=root
        idx=verify_index(root); ck(f'{label}_index_exact',idx['exact'])
        ck(f'{label}_index_canonical',canonical(root/'result-index.json'))
        details['archives'][label]={'name':name,'sha256':got,'size':p.stat().st_size,'members':counts,'index':idx,'root':root.name}
      if len(roots)==5:
        c=load(roots['census'],'census/census.json'); cv=load(roots['census'],'census-verification.json'); cf=load(roots['census'],'final-status.json')
        d=load(roots['diagnostic'],'diagnostic/diagnostic.json'); dv=load(roots['diagnostic'],'diagnostic-verification.json')
        w=load(roots['witness'],'witness/overlay-witness.json'); wv=load(roots['witness'],'witness-verification.json'); wf=load(roots['witness'],'final-status.json')
        p=load(roots['provenance'],'provenance/termux-native-r27d-provenance.json'); pv=load(roots['provenance'],'provenance-verification.json')
        b=load(roots['binding'],'binding/producer-binding.json'); bv=load(roots['binding'],'binding-verification.json'); pr=load(roots['binding'],'asset-preservation.json'); bf=load(roots['binding'],'final-status.json')
        for name,path in [('census','census/census.json'),('diagnostic','diagnostic/diagnostic.json'),('witness','witness/overlay-witness.json'),('provenance','provenance/termux-native-r27d-provenance.json'),('binding','binding/producer-binding.json')]: ck(name+'_capture_canonical',canonical(roots[name]/path))
        ck('census_failure_preserved',not c['pass'] and cf['transaction_rc']==51 and cv['pass'])
        ck('census_r27d_link_failure_exact',set(c['failed_checks'])=={'required_ndk_c_compile_link_pass','required_ndk_c_artifact_is_aarch64_elf','required_ndk_c_probe_run_pass','required_ndk_c_probe_output_exact','required_ndk_shared_compile_link_pass'})
        ck('diagnostic_pass',d['pass'] and d['check_count']==13 and dv['pass'] and dv['check_count']==39)
        ck('diagnostic_root_cause',d['classification']['root_cause_confirmed_tls_underaligned_r27d_lld'])
        ck('witness_pass',w['pass'] and w['check_count']==38 and wv['pass'] and wv['check_count']==31 and wf['transaction_rc']==0)
        ck('witness_original_lld',w['details']['patch']['first']['before_sha256']==ORIGINAL_LLD and w['details']['patch']['first']['before_align']==8)
        ck('witness_patched_lld',w['details']['patch']['first']['after_sha256']==PATCHED_LLD and w['details']['patch']['first']['after_align']==64)
        ck('witness_single_byte',w['details']['patch']['first']['byte_differences']==[{'after':64,'before':8,'offset':392}])
        ck('witness_mechanical_operations',all(w['checks'][x] for x in ['overlay_c_link_pass','overlay_c_run_pass','overlay_shared_link_pass','overlay_cxx_link_pass','overlay_cxx_run_pass','original_lld_unchanged']))
        ck('witness_repository_binding',w['details']['repository']['head']==BASE_HEAD and w['details']['repository']['tree']==BASE_TREE and w['details']['repository_after']['head']==BASE_HEAD)
        ck('provenance_failure_preserved',not p['pass'] and not pv['pass'])
        ck('provenance_installed_tree_exact',p['checks']['installed_tree_identity_exact'])
        ck('binding_pass',b['pass'] and b['check_count']==32 and bv['pass'] and bv['check_count']==27 and bf['transaction_rc']==0)
        ck('binding_producer_exact',b['details']['producer']['run']['head_sha']==PRODUCER and b['details']['producer']['run']['id']==29265009312 and b['details']['producer']['job']['id']==86867844060)
        ck('binding_asset_exact',b['details']['current_asset']['digest']=='sha256:'+ASSET_SHA and b['details']['current_asset']['size']==ASSET_SIZE)
        ck('binding_binary_candidate',b['classification']['termux_native_binary_a2b_candidate_ready_for_repository_decision'] and b['classification']['installed_ndk_bound_to_exact_release_asset'])
        ck('binding_limitations_explicit',not b['classification']['source_rebuild_provenance_complete'])
        ck('preservation_pass',pr['pass'] and all(pr['checks'].values()))
        ck('preservation_remote_exact',pr['remote']['directory']==AUTHORITY and pr['local']['sha256']==ASSET_SHA and pr['local']['size']==ASSET_SIZE)
        ck('all_repository_bindings_exact',all(load(r,'final-status.json')['repository']['head']==BASE_HEAD and load(r,'final-status.json')['repository']['tree']==BASE_TREE for r in roots.values()))
        ck('remote_main_unchanged',all(load(r,'final-status.json')['repository'].get('remote_main',MAIN)==MAIN for r in roots.values()))
        details['authority']={'asset_sha256':ASSET_SHA,'asset_size':ASSET_SIZE,'remote':AUTHORITY,'producer_commit':PRODUCER,'producer_run':29265009312,'producer_job':86867844060,'original_lld_sha256':ORIGINAL_LLD,'patched_lld_sha256':PATCHED_LLD,'patch_offset':392,'patch_before':8,'patch_after':64}
    failed=sorted(k for k,v in checks.items() if not v)
    out={'schema_version':1,'verification_kind':'external-gate4a-a2b-termux-native-toolchain-evidence-audit','pass':not failed,'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':failed,'checks':dict(sorted(checks.items())),'details':details,'acceptance':{'a2a_remote_inputs':'accepted','a2b_termux_native_binary_toolchain':'accepted' if not failed else 'rejected','a2_exact_input_and_toolchain_capture':'complete' if not failed else 'open','a3_clean_replay':'ready-not-started' if not failed else 'closed'},'claim_boundary':'Accepts a scoped exact-binary Termux-native producer toolchain for Gate 4A A2b only. It does not claim source-rebuild provenance for android-ndk-custom, product artifacts, A3 execution, A4-A6, or upgrade/downgrade behavior.'}
    text=json.dumps(out,indent=2,sort_keys=True)+'\n'
    if a.output: Path(a.output).write_text(text)
    else: print(text,end='')
    return 0 if out['pass'] else 51
if __name__=='__main__': raise SystemExit(main())

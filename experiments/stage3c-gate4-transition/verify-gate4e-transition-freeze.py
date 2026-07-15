#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, tarfile, tempfile
from collections import Counter
from pathlib import Path, PurePosixPath

SCRIPT=Path(__file__).resolve().parent
REPO=SCRIPT.parents[1]
EXPECTED_HEAD='0f3103efe5b07a992b339e8b1dff6aa02b8d65a4'
EXPECTED_TREE='dcfa04898268528045ecbd230cffd48021dbb3b3'
V1_SHA='ef24baca1f01d3e106825fb99e537d68ba0beffa9cd4e92577e43bd35421e77c'
V1_SIZE=493427
V1_ROOT='20260715-gate4d-bidirectional-termux-target-validation-v1'
V2_SHA='98ab810732dd2eb35bff9180dcb8fa1ec872eb09103d58670edb481cc9e3e5b2'
V2_SIZE=720554
V2_ROOT='20260715-gate4d-corrective-focused-retest-v2'
FAILED_V1=['H01','H02','H03','H04','H05','H06','H07','H08','C11','C12','A04']
GROUPS={'audit':{'count':6,'pass':6},'collision':{'count':12,'pass':12},'happy':{'count':8,'pass':8},'locking':{'count':2,'pass':2},'preflight':{'count':14,'pass':14},'recovery':{'count':24,'pass':24}}
DISP={'baseline-evidence-replay':2,'baseline-pass-unchanged':55,'derived-audit-after-corrections':1,'focused-corrective-retest':8}

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path): return json.loads(p.read_text())
def command(*args): return subprocess.check_output(args,text=True).strip()

def extract(archive:Path, expected_root:str, out:Path):
    out.mkdir(parents=True, exist_ok=True)
    tar_path=out/'payload.tar'
    with tar_path.open('wb') as f:
        subprocess.run(['zstd','-q','-d','-c',str(archive)],stdout=f,check=True)
    with tarfile.open(tar_path,'r:') as tf:
        members=tf.getmembers(); names=[m.name for m in members]
        assert names and len(names)==len(set(names))
        roots={PurePosixPath(n).parts[0] for n in names if PurePosixPath(n).parts}
        assert roots=={expected_root}
        for m in members:
            p=PurePosixPath(m.name)
            assert not p.is_absolute() and '..' not in p.parts
            assert m.isfile() or m.isdir()
        tf.extractall(out/'extract')
    return out/'extract'/expected_root, len(members)

def verify_index(root:Path):
    idx=root/'result-index.sha256'; lines=[x for x in idx.read_text().splitlines() if x]
    indexed=[]
    for line in lines:
        h,rel=line.split('  ',1); p=root/rel
        assert p.is_file() and sha(p)==h; indexed.append(rel)
    actual=sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p!=idx)
    assert sorted(indexed)==actual
    return len(lines)

def repo_line(path:Path,key:str):
    d={}
    for line in path.read_text().splitlines():
        if '=' in line:
            k,v=line.split('=',1); d[k]=v
    return d.get(key)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--baseline',required=True,type=Path); ap.add_argument('--corrective',required=True,type=Path); ap.add_argument('--output',type=Path)
    a=ap.parse_args(); checks={}; details={}
    def ck(name,v): checks[name]=bool(v)
    ck('baseline_sha',sha(a.baseline)==V1_SHA); ck('baseline_size',a.baseline.stat().st_size==V1_SIZE)
    ck('corrective_sha',sha(a.corrective)==V2_SHA); ck('corrective_size',a.corrective.stat().st_size==V2_SIZE)
    with tempfile.TemporaryDirectory(prefix='gate4e-freeze-') as td:
        td=Path(td); v1,m1=extract(a.baseline,V1_ROOT,td/'v1'); v2,m2=extract(a.corrective,V2_ROOT,td/'v2')
        ck('baseline_safe_archive',m1>0); ck('corrective_safe_archive',m2>0)
        ck('baseline_self_index',verify_index(v1)==1223); ck('corrective_self_index',verify_index(v2)==529)
        v1s=load(v1/'gate4d-target-output/scenario-summary.json'); v1r=load(v1/'gate4d-target-output/scenario-results.json')['scenarios']
        ck('baseline_summary_shape',v1s['scenario_count']==66 and v1s['pass_count']==55 and v1s['pass'] is False)
        ck('baseline_failed_ids',v1s['failed_scenarios']==FAILED_V1)
        ck('baseline_results_66',len(v1r)==66 and len({x['scenario_id'] for x in v1r})==66)
        ck('baseline_repository_invariant',repo_line(v1/'repository-pre.txt','head')==EXPECTED_HEAD and repo_line(v1/'repository-post.txt','head')==EXPECTED_HEAD and repo_line(v1/'repository-post.txt','tree')==EXPECTED_TREE and repo_line(v1/'repository-post.txt','remote')==EXPECTED_HEAD and repo_line(v1/'repository-post.txt','status_clean')=='true')
        bv=load(v2/'baseline-verification.json'); ia=load(v2/'input-authority-verification.json'); fv=load(v2/'focused-retest-verification.json'); fi=load(v2/'gate4d-independent-adjudication-verification.json')
        fs=load(v2/'gate4d-focused-retest-output/scenario-summary.json'); fr=load(v2/'gate4d-focused-retest-output/scenario-results.json')['scenarios']
        ads=load(v2/'gate4d-adjudication/scenario-summary-adjudicated.json'); adr=load(v2/'gate4d-adjudication/scenario-results-adjudicated.json')['scenarios']
        ck('embedded_baseline_exact',sha(v2/'baseline-gate4d-v1-results.tar.zst')==V1_SHA and (v2/'baseline-gate4d-v1-results.tar.zst').stat().st_size==V1_SIZE)
        ck('baseline_audit_21',bv['pass'] and bv['pass_count']==21 and bv['check_count']==21 and not bv['failed_checks'])
        ck('input_authority_21',ia['pass'] and ia['pass_count']==21 and ia['check_count']==21 and not ia['failed_checks'])
        ck('focused_summary_8',fs['pass'] and fs['scenario_count']==8 and fs['pass_count']==8 and fs['failed_scenarios']==[])
        ck('focused_rows_exact',len(fr)==8 and [x['scenario_id'] for x in fr]==[f'H{i:02d}' for i in range(1,9)] and all(x['pass'] for x in fr))
        ck('focused_verifier_10',fv['pass'] and fv['pass_count']==10 and fv['check_count']==10 and not fv['failed_checks'])
        ck('focused_timezone_all',all(x['details']['runtime_summary']['checks']['timezone'] for x in fr))
        dev={x['scenario_id']:x for x in fr if x['scenario_id'] in {'H02','H04','H06','H08'}}
        ck('focused_development_all',len(dev)==4 and all(x['details']['runtime_summary']['checks']['development_addon'] for x in dev.values()))
        ck('focused_transition_state_all',all(all(x['checks'].get(k) for k in ('transition_rc','target_exact','source_only_absent','sentinels_preserved','transactions_empty','runtime_probe')) for x in fr))
        ck('adjudicated_summary_66',ads['pass'] and ads['scenario_count']==66 and ads['pass_count']==66 and ads['failed_scenarios']==[])
        ck('adjudicated_groups',ads['group_counts']==GROUPS)
        ck('adjudicated_dispositions',ads['disposition_counts']==DISP)
        ck('adjudicated_rows_66',len(adr)==66 and len({x['scenario_id'] for x in adr})==66 and all(x['pass'] for x in adr))
        dc=Counter(x['disposition'] for x in adr); ck('row_dispositions_exact',dict(dc)==DISP)
        by={x['scenario_id']:x for x in adr}
        ck('happy_provenance',all(by[f'H{i:02d}']['disposition']=='focused-corrective-retest' for i in range(1,9)))
        ck('collision_provenance',all(by[x]['disposition']=='baseline-evidence-replay' for x in ('C11','C12')))
        ck('derived_a04',by['A04']['disposition']=='derived-audit-after-corrections' and by['A04']['derivation']=={'collision_pass':True,'happy_pass':True})
        ck('independent_16',fi['pass'] and fi['pass_count']==16 and fi['check_count']==16 and not fi['failed_checks'])
        ck('adjudicated_hashes',sha(v2/'gate4d-adjudication/scenario-summary-adjudicated.json')=='c9637d13587fa7fe0a3e418ea2003dc33d54b21c04c0f20c7531dd03a01a8c6b' and sha(v2/'gate4d-adjudication/scenario-results-adjudicated.json')=='78ea97fbd902c7dc4bf58f9acdc43e62fb4b2a5a66597066f01f7e09f02ba662')
        ck('corrective_repository_invariant',repo_line(v2/'repository-pre.txt','head')==EXPECTED_HEAD and repo_line(v2/'repository-post.txt','head')==EXPECTED_HEAD and repo_line(v2/'repository-post.txt','tree')==EXPECTED_TREE and repo_line(v2/'repository-post.txt','remote')==EXPECTED_HEAD and repo_line(v2/'repository-post.txt','status_clean')=='true')
        auth=load(SCRIPT/'gate4d-transition-target-authority.json'); freeze=load(SCRIPT/'gate4e-transition-freeze-authority.json')
        ck('tracked_gate4d_status',auth['status']=='accepted-66-of-66' and auth['final']['pass_count']==66)
        ck('tracked_archive_bindings',auth['baseline']['archive_sha256']==V1_SHA and auth['corrective']['archive_sha256']==V2_SHA)
        ck('tracked_gate4e_status',freeze['status']=='frozen-pass' and freeze['next_state']=={'gate4':'FROZEN','stage3d':'DEFERRED'})
        ck('tracked_gate4d_hash',freeze['inputs']['gate4d_authority_sha256']==sha(SCRIPT/'gate4d-transition-target-authority.json'))
        ck('tracked_gate4c_hash',freeze['inputs']['gate4c_authority_sha256']==sha(SCRIPT/'gate4c-transition-implementation-authority.json'))
        ck('docs_gate4_frozen','Gate 4E independent freeze complete' in (REPO/'README.md').read_text() and 'FROZEN PASS' in (REPO/'docs/evidence/STAGE3C_PHASE5_GATE4E_INDEPENDENT_TRANSITION_FREEZE.md').read_text())
        details={'baseline_members':m1,'corrective_members':m2,'baseline_index':1223,'corrective_index':529,'final_groups':ads['group_counts'],'final_dispositions':ads['disposition_counts']}
    failed=sorted(k for k,v in checks.items() if not v)
    result={'schema_version':1,'verification_kind':'stage3c-phase5-gate4e-independent-transition-freeze-verification','pass':not failed,'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':failed,'checks':dict(sorted(checks.items())),'details':details,'claim_boundary':'Freezes the exact two-product Gate 4 authority. No third product, registry migration, arbitrary mixed-product repair, or consumer integration.'}
    txt=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if a.output: a.output.write_text(txt)
    print(txt,end=''); raise SystemExit(0 if result['pass'] else 1)
if __name__=='__main__': main()

#!/usr/bin/env python3
"""Independently verify the accepted Stage 3-D Gate 2 result archive."""
from __future__ import annotations
import hashlib, json, subprocess, sys, tarfile, tempfile
from collections import Counter
from pathlib import Path, PurePosixPath

EXPECTED_ARCHIVE_SHA="4958b3e669950035f21baf5783fa54029366182cdc36ecf1fb909dfb8276e98c"
EXPECTED_SIZE=61374
EXPECTED_ROOT="20260715-stage3d-gate2-read-only-consumer-census-v1"
EXPECTED_INDEX_SHA="929b8e6120621eceb2ac4f2fecd8642291f2a2145ad2b226231bb919b9973f22"
EXPECTED_SUMMARY_SHA="c36998ad55a9a835afbc5ce10e3cf00a2671cb9586281496ab7853a24cc2fede"
EXPECTED_ROWS_SHA="d7f9f41bf4370a19c021bfdf23258c124c4d2cf573981c6efdc401b74b602162"
EXPECTED_INDEPENDENT_SHA="e5169e6a4483ae48fb227accb47fe17ba78c3bf6ce9fbd3045b23013ae2a1835"

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path): return json.loads(p.read_text(encoding='utf-8'))

def main()->int:
 if len(sys.argv)!=2:
  print(f"usage: {sys.argv[0]} RESULT.tar.zst",file=sys.stderr); return 2
 arc=Path(sys.argv[1]).resolve(); checks={}
 def ck(k,v): checks[k]=bool(v)
 ck('archive_exists',arc.is_file())
 if not arc.is_file():
  print(json.dumps({'pass':False,'failed_checks':['archive_exists'],'checks':checks},indent=2)); return 1
 ck('archive_sha256',sha(arc)==EXPECTED_ARCHIVE_SHA)
 ck('archive_size',arc.stat().st_size==EXPECTED_SIZE)
 with tempfile.TemporaryDirectory(prefix='gate2-audit-') as td:
  td=Path(td); tar_path=td/'result.tar'
  cp=subprocess.run(['zstd','-q','-d','-c',str(arc)],stdout=tar_path.open('wb'),stderr=subprocess.PIPE)
  ck('zstd_decode',cp.returncode==0)
  if cp.returncode: print(json.dumps({'pass':False,'failed_checks':[k for k,v in checks.items() if not v],'checks':checks},indent=2)); return 1
  with tarfile.open(tar_path,'r:') as tf:
   ms=tf.getmembers(); names=[m.name for m in ms]
   roots={PurePosixPath(n).parts[0] for n in names if PurePosixPath(n).parts}
   ck('member_count',len(ms)==849)
   ck('unique_members',len(names)==len(set(names)))
   ck('one_root',roots=={EXPECTED_ROOT})
   ck('safe_member_types',all(m.isfile() or m.isdir() for m in ms))
   ck('safe_paths',all(not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts for m in ms))
   tf.extractall(td/'x',filter='data')
  root=td/'x'/EXPECTED_ROOT
  idx=root/'result-index.sha256'; ck('index_sha256',sha(idx)==EXPECTED_INDEX_SHA)
  expected={}
  for line in idx.read_text().splitlines():
   if line.strip(): h,rel=line.split('  ',1); expected[rel]=h
  actual={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and p!=idx}
  ck('index_count',len(expected)==780)
  ck('index_exact',expected==actual)
  summary=root/'census/census-summary.json'; rowsf=root/'census/scenario-results.json'; indf=root/'gate2-independent-verification.json'
  ck('summary_sha',sha(summary)==EXPECTED_SUMMARY_SHA); ck('rows_sha',sha(rowsf)==EXPECTED_ROWS_SHA); ck('independent_sha',sha(indf)==EXPECTED_INDEPENDENT_SHA)
  s=load(summary); rows=load(rowsf)['scenarios']; ind=load(indf)
  ck('summary_pass',s.get('pass') is True)
  ck('scenario_count',len(rows)==64 and s.get('scenario_count')==64)
  ck('expectation_match',s.get('expectation_match_count')==64 and all(r.get('expectation_match') for r in rows))
  ck('strict_controls',s.get('strict_control_count')==12 and s.get('strict_control_pass_count')==12 and all((not r.get('strict_control')) or r.get('strict_pass') for r in rows))
  ck('groups',Counter(r['group'] for r in rows)==Counter({'explicit':8,'natural':32,'project':8,'precedence-negative':12,'transition-continuity':4}))
  ck('repository_identity',s['repository']=={'branch':'agent/stage3d-consumer-integration','head':'b0b938b6f8d4eea67e2fac1eca83f69c835a9cac','remote':'b0b938b6f8d4eea67e2fac1eca83f69c835a9cac','status':'','tree':'3b86355f3236a850512e8e1bdb6b3e1df73362f5'})
  ck('invariants',all(s['checks'][k] for k in ('authority_immutable','global_paths_immutable','repository_immutable')))
  ck('uv_identity',s['uv']['version_stdout']=='uv 0.11.28 (aarch64-linux-android)' and s['uv']['sha256']=='f624c48a72b2e2e307043f339eb3ff6dbdfa0207be2053d2e5bc071709289495')
  processes=[]
  for p in (root/'census/scenarios').rglob('*.process.json'):
   d=load(p); cmd=d.get('command',[])
   if cmd and cmd[0].endswith('/uv'): processes.append(cmd)
  ops=Counter(('python find' if len(c)>2 and c[1:3]==['python','find'] else c[1] if len(c)>1 else '') for c in processes)
  ck('uv_find_count',ops['python find']==72)
  ck('uv_venv_count',ops['venv']==14)
  ck('uv_run_not_executed',ops['run']==0)
  ck('uv_sync_not_executed',ops['sync']==0)
  ck('download_disabled',all('--no-python-downloads' in c for c in processes))
  ck('independent_25',ind.get('pass') is True and ind.get('pass_count')==25 and ind.get('check_count')==25)
  recovery=load(root/'packaging-recovery/precheck.json')
  ck('packaging_only_recovery',recovery.get('pass') is True and recovery.get('claim_boundary','').startswith('Packaging-only recovery'))
 failed=sorted(k for k,v in checks.items() if not v)
 result={'schema_version':1,'verification_kind':'stage3d-gate2-accepted-archive-verification','pass':not failed,'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':failed,'checks':dict(sorted(checks.items())),'observed':{'archive_sha256':sha(arc),'archive_size':arc.stat().st_size,'uv_process_counts':dict(ops)},'claim_boundary':'Accepts census evidence and coverage only; uv run and uv sync are untested.'}
 print(json.dumps(result,indent=2,sort_keys=True)); print(); print(f"STAGE3D_GATE2_ACCEPTED_ARCHIVE_VERIFICATION={result['pass_count']}/{result['check_count']} {'PASS' if result['pass'] else 'FAIL'}")
 return 0 if result['pass'] else 1
if __name__=='__main__': raise SystemExit(main())

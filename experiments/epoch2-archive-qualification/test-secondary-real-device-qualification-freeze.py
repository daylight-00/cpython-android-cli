#!/usr/bin/env python3
from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AUTH=ROOT/'experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json'
AUDIT=ROOT/'experiments/epoch2-archive-qualification/secondary-real-device-qualification-external-audit.json'
base_a=json.loads(AUTH.read_text()); base_u=json.loads(AUDIT.read_text())
def accepts(a,u):
 b=a.get('claim_boundary',{}); s=a.get('secondary_profile',{}); src=u.get('source',{})
 return all([
  a.get('authority_kind')=='e2p3-secondary-real-device-qualification-freeze',
  a.get('status')=='frozen-pass-dual-real-device-aarch64-termux-compatibility',
  b.get('dual_real_device_acceptance') is True,
  b.get('selectability') is False,
  b.get('emulator_profile') is False,
  b.get('original_contract_fully_satisfied') is False,
  s.get('result_archive_sha256')=='a3231adb62c47cb17dda16b66207f3c976aa20593e2288a7d381052154147c10',
  s.get('target_authority_index_sha256')=='6f869abe00b6e5fd50d85965dea84a12f7b6ce4c90ef20182f24831ed4b03d5d',
  a.get('next_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control',
  u.get('pass') is True and u.get('failed_checks')==[],
  src.get('result_archive_sha256')=='a3231adb62c47cb17dda16b66207f3c976aa20593e2288a7d381052154147c10',
 ])
fixtures=[]
def case(name,which,mut):
 a=deepcopy(base_a);u=deepcopy(base_u);mut(a if which=='a' else u);fixtures.append({'name':name,'pass':not accepts(a,u)})
case('dual-claim-false','a',lambda x:x['claim_boundary'].__setitem__('dual_real_device_acceptance',False))
case('selectability-true','a',lambda x:x['claim_boundary'].__setitem__('selectability',True))
case('emulator-claimed','a',lambda x:x['claim_boundary'].__setitem__('emulator_profile',True))
case('wrong-result','a',lambda x:x['secondary_profile'].__setitem__('result_archive_sha256','0'*64))
case('wrong-target','a',lambda x:x['secondary_profile'].__setitem__('target_authority_index_sha256','0'*64))
case('wrong-next-action','a',lambda x:x.__setitem__('next_action_class','publish'))
case('audit-fail','u',lambda x:x.__setitem__('pass',False))
out={'schema_version':1,'test_kind':'e2p3-secondary-real-device-freeze-negative-fixtures','pass':accepts(base_a,base_u) and all(x['pass'] for x in fixtures),'test_count':len(fixtures),'pass_count':sum(x['pass'] for x in fixtures),'results':fixtures}
print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True));raise SystemExit(0 if out['pass'] else 1)

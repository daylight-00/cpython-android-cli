#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, stat, zipfile
from pathlib import Path

RAW='docs/references/raw/2026-07-19-epoch2-epoch4-recalibration'
ARCHIVES={
'epoch2-android-cpython-research.zip':'a21ad6708f4910cfa86d5f55d86572d0c964eabc1b659aebbac57b295e7db02c',
'cpython-android-cli-e2-e3-research-plan.zip':'d5c3cd3d5172bc46b80c5630711cd37adbe994018504822e9076d620a082424c',
'android-bionic-python-abcd-plan.zip':'992be63461623164ae6dd5d21872bd3b60d53d3fab5ea3afa01c717d81dd1511',
'android-bionic-python-design-docs.zip':'9a255166cc1cc897f74a7524074d0c23a612399c810448620d81c67058103d46'}
REQ=['README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md','docs/architecture/COMPONENT_OWNERSHIP.md','docs/decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md','docs/epochs/EPOCH2_CHARTER.md','docs/epochs/EPOCH3_CHARTER.md','docs/epochs/EPOCH4_CHARTER.md','docs/roadmap/EPOCH2_ROADMAP.md','docs/roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md','docs/references/EXTERNAL_RESEARCH_ARCHIVE_INTAKE_20260719.md','docs/evidence/E2_RECALIBRATION_AUTHORITY_FREEZE.md','experiments/epoch2-recalibration/recalibration-authority.json','experiments/epoch2-recalibration/recalibration-external-audit.json']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); a=ap.parse_args(); root=Path(a.root).resolve()
 checks=[]
 def ck(name,ok,detail=''): checks.append({'name':name,'pass':bool(ok),'detail':detail})
 for rel in REQ: ck('required:'+rel,(root/rel).is_file())
 raw=root/RAW
 for name,want in ARCHIVES.items():
  p=raw/name; ck('raw-exists:'+name,p.is_file())
  if not p.is_file(): continue
  ck('raw-sha256:'+name,sha(p)==want,sha(p))
  try:
   with zipfile.ZipFile(p) as z:
    infos=z.infolist(); names=[i.filename for i in infos]
    ck('zip-duplicates:'+name,len(names)==len(set(names)))
    safe=all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
    ck('zip-safe-paths:'+name,safe)
    roots={n.split('/')[0] for n in names if n}; ck('zip-single-root:'+name,len(roots)==1,','.join(sorted(roots)))
    special=False
    for i in infos:
     mode=(i.external_attr>>16)&0o170000
     if mode in (stat.S_IFLNK,stat.S_IFCHR,stat.S_IFBLK,stat.S_IFIFO,stat.S_IFSOCK): special=True
    ck('zip-no-special:'+name,not special)
  except Exception as e: ck('zip-readable:'+name,False,str(e))
 sums=(raw/'SHA256SUMS')
 ck('raw-sha256sums-exists',sums.is_file())
 if sums.is_file():
  got={line.split('  ',1)[1]:line.split('  ',1)[0] for line in sums.read_text().splitlines() if '  ' in line}
  ck('raw-sha256sums-coverage',got==ARCHIVES)
 man=raw/'MANIFEST.json'; ck('raw-manifest-exists',man.is_file())
 if man.is_file():
  try:
   d=json.loads(man.read_text()); ck('raw-manifest-count',d.get('archive_count')==4); ck('raw-manifest-files',{x['file'] for x in d.get('archives',[])}==set(ARCHIVES))
  except Exception as e: ck('raw-manifest-json',False,str(e))
 def text(rel):
  p=root/rel
  return p.read_text() if p.is_file() else ''
 adr=text('docs/decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md')
 e2=text('docs/epochs/EPOCH2_CHARTER.md'); e3=text('docs/epochs/EPOCH3_CHARTER.md'); e4=text('docs/epochs/EPOCH4_CHARTER.md'); road=text('docs/roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md'); cur=text('docs/CURRENT_CONTEXT.md'); readme=text('README.md')
 ck('decision-python-org','Python.org' in adr and 'Python.org' in e2)
 ck('decision-beeware','BeeWare' in adr and 'BeeWare' in e2)
 ck('decision-api36-required','API 36' in adr and 'API 36' in e2 and all(x in road for x in ['A  exact','B  same CPython','C  same CPython']))
 ck('epoch3-clean','new clean release repository' in e3 and 'Python.org' in e3)
 ck('epoch3-no-source-owner','CPython source patch production' in e3 and 'BeeWare dependency recipe production' in e3)
 ck('epoch4-source-owner','Full Astral-like Android source producer' in e4 and 'CPython source acquisition' in e4 and 'BeeWare dependency source revisions' in e4)
 ck('common-contract','retaining the accepted product contract' in e4 and 'consumer-facing product contract' in adr)
 ck('astral-structural-reference','Primary structural reference' in e3 and 'resemble Astral structurally' in e4)
 ck('note9-optional',all('optional' in x and 'deferred' in x for x in [e2,road,cur]))
 ck('emulator-unclaimed','waived' in cur and 'unclaimed' in cur)
 ck('no-dual-claim','dual-device claim     not made' in cur)
 ck('former-phases-retired','former E2-P4' in text('docs/roadmap/EPOCH2_ROADMAP.md') and 'superseded' in text('docs/roadmap/EPOCH2_ROADMAP.md'))
 ck('adr3-superseded','Status:** Superseded by ADR-0006' in text('docs/decisions/ADR-0003-REPOSITORY-TOPOLOGY.md'))
 ck('current-next-r1','E2-R1 exact official upstream control' in cur)
 ck('readme-epochs',all(x in readme for x in ['Epoch 2  Python.org/BeeWare','Epoch 3  clean upstream-derived','Epoch 4  full Astral-like']))
 auth=text('experiments/epoch2-recalibration/recalibration-authority.json'); audit=text('experiments/epoch2-recalibration/recalibration-external-audit.json')
 try:
  ad=json.loads(auth); ck('authority-base',ad['base']['commit']=='7e9210ce21b31ed2b2c9008d6c1b1dbe6daf6214' and ad['base']['tree']=='a232ec4daab0a71ba8137750e2b30df60d39b83e'); ck('authority-decisions',ad['decisions']['epoch2_api36_comparison_required'] is True and ad['decisions']['note9']=='optional-deferred-evidence')
 except Exception as e: ck('authority-json',False,str(e))
 try:
  au=json.loads(audit); ck('external-audit',au.get('pass') is True and au.get('failed_checks')==[])
 except Exception as e: ck('external-audit-json',False,str(e))
 failed=[c['name'] for c in checks if not c['pass']]
 out={'schema_version':1,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'pass':not failed}
 print(json.dumps(out,indent=2,sort_keys=True)); return 0 if not failed else 1
if __name__=='__main__': raise SystemExit(main())

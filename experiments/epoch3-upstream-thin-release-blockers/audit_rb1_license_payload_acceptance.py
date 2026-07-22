#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'experiments/epoch3-upstream-thin-release-blockers/rb1-license-payload-authority-evidence'
def load(n):return json.loads((E/n).read_text())
def main():
 x=load('component-expansion-audit.json');i=load('license-payload-inventory.json');g=load('updated-gap-register.json');a=load('independent-audit.json');checks={
 'family':i.get('family_fingerprint_sha256')=='87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302',
 'full_immutable':i.get('full_artifact',{}).get('identity',{}).get('sha256')=='20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12' and i.get('full_artifact',{}).get('identity_preserved') is True,
 'sources_exact':len(i.get('source_archives',[]))==5 and all(z.get('archive',{}).get('sha256') for z in i.get('source_archives',[])),
 'hacl_expanded':x.get('new_components',[{}])[0].get('component_class')=='hacl-star',
 'mismatch_quarantine':{(z.get('component'),z.get('quarantined_source_version')) for z in x.get('mismatch_quarantine',[])}=={('xz-liblzma','5.2.5'),('libmpdec','4.0.0')},
 'gaps_exact':g.get('blocking_gap_count')==8,
 'producer_audit_pass':a.get('pass') is True,
 'claims_open':all(z.get('selectable') is False and z.get('publication') is False for z in [x.get('claim_boundary',{}),i.get('claim_boundary',{}),g.get('claim_boundary',{}),a.get('claim_boundary',{})])}
 failed=sorted(k for k,v in checks.items() if v is not True);out={'schema_version':1,'audit_kind':'epoch3-rb1-license-payload-acceptance-independent-audit','pass':not failed,'checks':dict(sorted(checks.items())),'failed_checks':failed};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())

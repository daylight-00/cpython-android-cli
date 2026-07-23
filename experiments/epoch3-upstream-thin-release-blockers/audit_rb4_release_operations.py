#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/epoch3-upstream-thin-release-blockers'
E=BASE/'rb4-release-operations-authority-evidence'
def load(p:Path):return json.loads(p.read_text(encoding='utf-8'))
def sha(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->int:
 names=['patch-update-binding.json','catalog-transition-receipt.json','rollback-receipt.json','revocation-readback.json','security-ownership.json','result.json']
 docs={n:load(E/n) for n in names}
 catalog=docs['catalog-transition-receipt.json'];roll=docs['rollback-receipt.json'];rev=docs['revocation-readback.json'];result=docs['result.json']
 checks={
  'all_evidence_pass':all(d.get('pass') is True for d in docs.values()),
  'production_catalog_stable_across_drills':catalog['catalog_sha256']==roll['before_catalog_sha256']==rev['before_catalog_sha256']==result['production_catalog_sha256'],
  'rollback_restores_exact_baseline':roll['after_catalog_sha256']==roll['before_catalog_sha256'],
  'revocation_is_drill_only':rev.get('drill_only') is True and rev.get('production_revocation_applied') is False,
  'revoked_selection_denied':rev['checks']['revoked_selection_denied'] is True,
  'fallback_selected':rev['checks']['fallback_activation_pass'] is True,
  'ambiguous_replacement_denied':catalog['checks']['ambiguous_replacement_denied'] is True,
  'publication_withheld':result['claim_boundary']['publication'] is False and result['claim_boundary']['selectable'] is False,
 }
 out={'schema_version':1,'audit_kind':'epoch3-rb4-release-operations-independent-audit','checks':checks,'evidence_identities':{n:sha(E/n) for n in names},'failed_checks':sorted(k for k,v in checks.items() if v is not True),'pass':all(checks.values())}
 (E/'independent-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())

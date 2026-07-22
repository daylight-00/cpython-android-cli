#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=ROOT/"experiments/epoch3-upstream-thin-release-blockers/rb1-legal-overlay-authority-evidence"
def load(n):return json.loads((E/n).read_text())
def main():
 r=load("legal-overlay-result.json");i=load("legal-overlay-index.json");g=load("updated-gap-register.json");a=load("independent-audit.json");m=load("legal/component-license-map-candidate-v2.json");checks={
 "overlay_pass":r.get("pass") is True,
 "family_immutable":r.get("family_identity_preserved") is True,
 "index_exact":i.get("file_count")==72 and i.get("fingerprint_sha256")==r.get("legal_overlay_fingerprint_sha256"),
 "component_boundary":m.get("component_count")==13 and m.get("mapping_complete") is False,
 "gap_boundary":g.get("blocking_gap_count")==4,
 "producer_audit_pass":a.get("pass") is True,
 "owner_approval_open":all(x.get("owner_approved") is not True for x in [r.get("claim_boundary",{}),a.get("claim_boundary",{})]),
 "claims_open":all(x.get("selectable") is False and x.get("publication") is False and x.get("rb1_closed") is False for x in [r.get("claim_boundary",{}),g.get("claim_boundary",{}),a.get("claim_boundary",{})])}
 failed=sorted(k for k,v in checks.items() if v is not True);out={"schema_version":1,"audit_kind":"epoch3-rb1-legal-overlay-acceptance-independent-audit","pass":not failed,"checks":dict(sorted(checks.items())),"failed_checks":failed};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out["pass"] else 1
if __name__=="__main__":raise SystemExit(main())

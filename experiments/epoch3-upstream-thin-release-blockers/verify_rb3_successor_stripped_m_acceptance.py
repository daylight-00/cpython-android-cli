#!/usr/bin/env python3
"""Verify the frozen RB-3 profile-M successor stripped r5 acceptance authority."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
BASE_NAME="experiments/epoch3-upstream-thin-release-blockers"
EXPECTED_RESULT_SHA="db5ff3a3f9a5a8de4731ae5e5cebad7739bcf0330f12de01bdecb01528acd1d7"
EXPECTED_CANDIDATE_SHA="9cffe27e4e7e6b82d3bace2ea4ce56473abae683bad041d38106ec481b83d9e5"
def load(p:Path)->Any:return json.loads(p.read_text(encoding="utf-8"))
def sha256_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root:Path=ROOT)->dict[str,Any]:
 base=root/BASE_NAME
 authority=load(base/"rb3-successor-stripped-m-authority.json")
 accepted=load(base/"accepted-rb3-successor-stripped-m-r1-return.json")
 inspection=load(base/"rb3-successor-stripped-m-r1-return-inspection.json")
 evidence=base/"rb3-successor-stripped-m-authority-evidence"
 next_contract=load(base/"rb3-successor-technical-family-m-contract.json")
 external=load(evidence/"external-acceptance-audit.json");owner=load(evidence/"owner-result.json");summary=load(evidence/"owner-summary.json")
 owner_audit=load(evidence/"owner-independent-audit.json");repro=load(evidence/"reproducibility.json");mutation=load(evidence/"stripped-mutation-receipt.json")
 stripped=load(evidence/"stripped-verification.json");android=load(evidence/"stripped-android-qualification.json")
 direct=load(evidence/"native-wheel-elf-boundary.json");managed=load(evidence/"native-managed-wheel-elf-boundary.json");protected=load(evidence/"protected-state.json");index=load(evidence/"result-index.json")
 identities=authority.get("file_identities",{})
 amendment_path=base/"rb3-successor-stripped-m-temporal-verifier-amendment.json"
 amendment=load(amendment_path) if amendment_path.is_file() else {"replacements":{}}
 second_path=base/"rb3-successor-legal-family-temporal-verifier-amendment.json"
 second=load(second_path) if second_path.is_file() else {"replacements":{}}
 latest_path=base/"rb3-successor-legal-data-rebinding-temporal-verifier-amendment.json"
 latest=load(latest_path) if latest_path.is_file() else {"replacements":{}}
 replacements=amendment.get("replacements",{});second_replacements=second.get("replacements",{});latest_replacements=latest.get("replacements",{})
 def effective_hash(rel:str,expected:str)->str:
  if rel in latest_replacements:return latest_replacements[rel].get("replacement_sha256",expected)
  if rel in second_replacements:return second_replacements[rel].get("replacement_sha256",expected)
  if rel in replacements:return replacements[rel].get("replacement_sha256",expected)
  return expected
 identity_checks={rel:(root/rel).is_file() and sha256_file(root/rel)==effective_hash(rel,expected) for rel,expected in identities.items()}
 expected_boundary={"artifact_family_superseded":False,"canonical_predecessor_family_unchanged":True,"portable_raw_wheel_claim":False,"publication":False,"rb3_closed":False,"selectable":False,"successor_full_accepted":True,"successor_install_only_accepted":True,"successor_stripped_accepted":True,"successor_stripped_candidate":True,"successor_technical_family_authorized":True,"successor_technical_family_started":False,"successor_technical_family_accepted":False,"user_built_wheel_postprocessing":"out-of-scope-external-tool-responsibility"}
 candidate=accepted.get("candidate_stripped",{});accepted_candidate=authority.get("accepted_stripped",{})
 checks={
  "authority_kind":authority.get("authority_kind")=="epoch3-rb3-profile-M-successor-install-only-stripped-r5",
  "file_identities":bool(identity_checks) and all(identity_checks.values()),
  "temporal_verifier_amendment":amendment.get("amendment_kind")=="epoch3-rb3-successor-stripped-temporal-routing-verifier-amendment" and amendment.get("invariants",{}).get("accepted_stripped_bytes_changed") is False,
  "second_temporal_amendment":second.get("amendment_kind")=="epoch3-rb3-successor-legal-family-temporal-routing-verifier-amendment" and second.get("invariants",{}).get("accepted_artifact_bytes_changed") is False,
  "latest_temporal_amendment":latest.get("amendment_kind")=="epoch3-rb3-successor-legal-data-rebinding-temporal-routing-verifier-amendment" and latest.get("invariants",{}).get("accepted_artifact_bytes_changed") is False and latest.get("predecessor_amendment",{}).get("path")=="experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-family-temporal-verifier-amendment.json" and latest.get("predecessor_amendment",{}).get("sha256")=="d11ba8f48fab81fe71cbbb3ae8ceb0a8529443211a5624f7ce9e0836e9cf36a5" and all((root/rel).is_file() and sha256_file(root/rel)==row.get("replacement_sha256") for rel,row in latest_replacements.items()),
  "accepted_return_status":accepted.get("status")=="accepted-pass-successor-stripped-r5-authorized-technical-family-derivation-pending",
  "inspection_status":inspection.get("status")=="accepted-complete-pass-candidate-ready-for-bounded-acceptance",
  "result_identity":accepted.get("result_archive",{}).get("sha256")==authority.get("accepted_evidence",{}).get("result_archive_sha256")==inspection.get("result_archive",{}).get("sha256")==EXPECTED_RESULT_SHA and accepted.get("result_archive",{}).get("size_bytes")==47423566 and accepted.get("result_archive",{}).get("self_index_file_count")==84,
  "self_index_count":len(index.get("files",[]))==84,
  "candidate_identity":all(candidate.get(k)==accepted_candidate.get(k) for k in ("filename","sha256","size_bytes","member_count")) and candidate.get("sha256")==EXPECTED_CANDIDATE_SHA and candidate.get("size_bytes")==23842721 and candidate.get("member_count")==3699,
  "external_audit":external.get("pass") is True and not external.get("failed_checks") and external.get("identity",{}).get("sha256")==EXPECTED_RESULT_SHA and external.get("candidate",{}).get("sha256")==EXPECTED_CANDIDATE_SHA,
  "owner_result":owner.get("pass") is True and not owner.get("failed_checks") and len(owner.get("checks",{}))==37 and all(v is True for v in owner["checks"].values()),
  "owner_summary":summary.get("claim_transaction_rc")==0 and summary.get("failure_reason")=="none" and summary.get("claim_boundary",{}).get("successor_stripped_candidate") is True and summary.get("claim_boundary",{}).get("successor_stripped_accepted") is False,
  "owner_audit":owner_audit.get("pass") is True and not owner_audit.get("failed_checks") and len(owner_audit.get("checks",{}))==27 and all(v is True for v in owner_audit["checks"].values()),
  "reproducibility":repro.get("pass") is True and repro.get("byte_identical") is True and repro.get("first",{}).get("sha256")==EXPECTED_CANDIDATE_SHA and repro.get("second",{}).get("sha256")==EXPECTED_CANDIDATE_SHA,
  "bounded_mutation":mutation.get("decision")=="distinct-archive" and mutation.get("regular_elf_count")==81 and mutation.get("eligible_elf_count")==1 and mutation.get("changed_elf_count")==1 and mutation.get("eligible_paths")==["bin/python3.14"] and mutation.get("changed_paths")==["bin/python3.14"],
  "stripped_verification":stripped.get("pass") is True and not stripped.get("failed_checks") and len(stripped.get("checks",{}))==21 and all(v is True for v in stripped["checks"].values()),
  "android":android.get("pass") is True and not android.get("failed_checks") and len(android.get("checks",{}))==11 and all(v is True for v in android["checks"].values()),
  "direct_sdk":direct.get("pass") is True and direct.get("wheel_import_returncode")==0 and direct.get("raw_extension",{}).get("all_load_alignments_16k") is True,
  "managed_sdk":managed.get("pass") is True and managed.get("wheel_import_returncode")==0 and managed.get("raw_extension",{}).get("all_load_alignments_16k") is True,
  "wheel_repair_boundary":direct.get("raw_policy_clean") is False and managed.get("raw_policy_clean") is False and direct.get("postprocessing_boundary")==managed.get("postprocessing_boundary")=="out-of-scope-external-tool-responsibility",
  "protected_state":all(protected.get(k) is True for k in ("accepted_full_unchanged","accepted_install_only_unchanged","predecessor_stripped_unchanged","frozen_authorities_unchanged","real_managed_root_unchanged")),
  "acceptance_boundary":accepted.get("claim_boundary")==expected_boundary,
  "authority_boundary":authority.get("claim_boundary")==expected_boundary,
  "next_contract":next_contract.get("contract_kind")=="epoch3-rb3-profile-M-successor-technical-family-derivation" and next_contract.get("accepted_inputs",{}).get("install_only_stripped",{}).get("sha256")==EXPECTED_CANDIDATE_SHA and next_contract.get("success_boundary",{}).get("successor_technical_family_candidate") is True and next_contract.get("success_boundary",{}).get("predecessor_family_superseded") is False and next_contract.get("success_boundary",{}).get("rb3_closed") is False,
 }
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {"schema_version":1,"verifier_kind":"epoch3-rb3-profile-M-successor-stripped-r5-acceptance","pass":not failed,"checks":dict(sorted(checks.items())),"failed_checks":failed,"identity_checks":dict(sorted(identity_checks.items()))}
def main()->int:
 r=verify();print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["pass"] else 1
if __name__=="__main__":raise SystemExit(main())

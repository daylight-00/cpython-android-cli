#!/usr/bin/env python3
"""Verify Gate 2 canonical snapshot, deterministic repeat, and bounded fixtures."""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
import copy,json,tempfile
from pathlib import Path
from publication_snapshot import (
    FROZEN_ROWS,build_snapshot_document,canonical_bytes,load_document,
    verify_candidate_observation,verify_snapshot_document,
)
ROOT=Path(__file__).resolve().parent
TRACKED=ROOT/"gate2-publication-snapshot.json"

def mutation(document, fn):
    value=copy.deepcopy(document);fn(value);return value

def main() -> int:
    tracked=load_document(TRACKED)
    generated=build_snapshot_document()
    checks: dict[str,bool] = {}
    checks["tracked-verifies"]=verify_snapshot_document(tracked)["pass"]
    checks["tracked-canonical"]=TRACKED.read_bytes()==canonical_bytes(tracked)
    checks["tracked-equals-generated"]=tracked==generated
    with tempfile.TemporaryDirectory() as td:
        a=Path(td)/"a.json";b=Path(td)/"b.json"
        a.write_bytes(canonical_bytes(build_snapshot_document()));b.write_bytes(canonical_bytes(build_snapshot_document()))
        checks["deterministic-repeat"]=a.read_bytes()==b.read_bytes()==TRACKED.read_bytes()
    for key,row in sorted(FROZEN_ROWS.items()):
        result=verify_candidate_observation(
            tracked,key=key,observed_size=row["artifact"]["size"],observed_sha256=row["artifact"]["sha256"],
            bound_snapshot_sha256=tracked["snapshot_sha256"],
        )
        checks[f"candidate-success:{key}"]=result["promotable"] and result["verified_cache_key"]==row["artifact"]["sha256"] and result["installation_permitted"] is False

    negative: dict[str,bool] = {}
    duplicate=mutation(tracked,lambda d:d["snapshot"]["rows"].append(copy.deepcopy(d["snapshot"]["rows"][0])))
    duplicate["snapshot_sha256"]="0"*64
    negative["duplicate-key"]=not verify_snapshot_document(duplicate)["pass"]
    redefined=mutation(tracked,lambda d:d["snapshot"]["rows"][0]["artifact"].update({"sha256":"1"*64}))
    negative["redefined-key"]=not verify_snapshot_document(redefined)["pass"]
    digest=copy.deepcopy(tracked);digest["snapshot_sha256"]="2"*64
    negative["snapshot-digest-mismatch"]=not verify_snapshot_document(digest)["pass"]
    no_size=mutation(tracked,lambda d:d["snapshot"]["rows"][0]["artifact"].pop("size"))
    negative["missing-size"]=not verify_snapshot_document(no_size)["pass"]
    locator_identity=mutation(tracked,lambda d:(d["snapshot"]["rows"][0].pop("artifact"),d["snapshot"]["rows"][0]["locators"][0].update({"sha256":FROZEN_ROWS["cpython-3.14.5-linux-aarch64-none"]["artifact"]["sha256"],"size":9761522})))
    negative["locator-only-identity"]=not verify_snapshot_document(locator_identity)["pass"]
    key="cpython-3.14.5-linux-aarch64-none";row=FROZEN_ROWS[key]
    negative["candidate-size-mismatch"]=not verify_candidate_observation(tracked,key=key,observed_size=row["artifact"]["size"]+1,observed_sha256=row["artifact"]["sha256"],bound_snapshot_sha256=tracked["snapshot_sha256"])["promotable"]
    negative["candidate-hash-mismatch"]=not verify_candidate_observation(tracked,key=key,observed_size=row["artifact"]["size"],observed_sha256="f"*64,bound_snapshot_sha256=tracked["snapshot_sha256"])["promotable"]
    negative["candidate-binding-mismatch"]=not verify_candidate_observation(tracked,key=key,observed_size=row["artifact"]["size"],observed_sha256=row["artifact"]["sha256"],bound_snapshot_sha256="e"*64)["promotable"]

    incomplete: dict[str,bool] = {}
    missing_row=mutation(tracked,lambda d:d["snapshot"]["rows"].pop())
    incomplete["missing-row"]=not verify_snapshot_document(missing_row)["pass"]
    missing_hash=mutation(tracked,lambda d:d["snapshot"]["rows"][0]["artifact"].pop("sha256"))
    incomplete["missing-artifact-sha256"]=not verify_snapshot_document(missing_hash)["pass"]
    missing_provenance=mutation(tracked,lambda d:d["snapshot"]["rows"][0]["provenance"].pop("evidence_member_sha256"))
    incomplete["missing-provenance-member-digest"]=not verify_snapshot_document(missing_provenance)["pass"]
    missing_digest=copy.deepcopy(tracked);missing_digest.pop("snapshot_sha256")
    incomplete["missing-snapshot-digest"]=not verify_snapshot_document(missing_digest)["pass"]

    failed=sorted([k for k,v in checks.items() if not v]+[f"negative:{k}" for k,v in negative.items() if not v]+[f"incomplete:{k}" for k,v in incomplete.items() if not v])
    result={
        "schema_version":1,"verification_kind":"stage3f-gate2-immutable-publication-snapshot",
        "pass":not failed,"check_count":len(checks)+len(negative)+len(incomplete),
        "pass_count":sum(checks.values())+sum(negative.values())+sum(incomplete.values()),
        "failed_checks":failed,"checks":dict(sorted(checks.items())),
        "expected_negative":dict(sorted(negative.items())),"incomplete":dict(sorted(incomplete.items())),
        "snapshot_sha256":tracked.get("snapshot_sha256"),"snapshot_size":len(TRACKED.read_bytes()),
        "row_count":len(tracked["snapshot"]["rows"]),"keys":[r["key"] for r in tracked["snapshot"]["rows"]],
        "claim_boundary":"Repository-local canonicalization and candidate-observation policy only; no socket, uv, target product, cache mutation, or installation.",
    }
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result["pass"] else 1
if __name__=="__main__": raise SystemExit(main())

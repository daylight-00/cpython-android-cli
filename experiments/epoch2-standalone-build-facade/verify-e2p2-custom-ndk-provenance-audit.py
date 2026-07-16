#!/usr/bin/env python3
"""Verify the E2-P2 custom-NDK / CPython 3.14.5 provenance audit."""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path
from typing import Any

BASE_HEAD="16a0d6713eff05447b3b2e328581f6884a14c3e8"
BASE_TREE="733f92196f4ea36e2029caf366da802513f6a30d"

def read_json(path: Path, errors: dict[str,str]) -> dict[str,Any]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value,dict): raise TypeError("top-level JSON is not an object")
        return value
    except Exception as exc:
        errors[str(path)]=f"{type(exc).__name__}: {exc}"
        return {}

def strings(value: Any):
    if isinstance(value,str): yield value
    elif isinstance(value,dict):
        for k,v in value.items():
            yield str(k); yield from strings(v)
    elif isinstance(value,list):
        for item in value: yield from strings(item)

def git(root: Path,*args: str) -> str:
    return subprocess.run(["git",*args],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout.strip()

def verify(root: Path) -> dict[str,Any]:
    root=root.resolve(); errors={}; checks={}
    exp=root/"experiments/epoch2-standalone-build-facade"
    decision=read_json(exp/"e2p2-custom-ndk-python3145-provenance-audit.json",errors)
    a2b=read_json(root/"experiments/stage3c-gate4-second-product-authority/gate4a-a2b-termux-native-toolchain-authority.json",errors)
    a6=read_json(root/"experiments/stage3c-gate4-second-product-authority/gate4a-a6-second-product-authority.json",errors)
    a6audit=read_json(root/"experiments/stage3c-gate4-second-product-authority/gate4a-a6-external-audit.json",errors)
    gate6=read_json(root/"experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json",errors)
    lock=read_json(root/"config/products/cpython-3.14.6-aarch64-linux-android.lock.json",errors)
    facade=read_json(root/"components/standalone/contracts/facade-v1.json",errors)
    def ck(name: str, value: Any): checks[name]=bool(value)
    ck("decision_identity",decision.get("schema_version")==1 and decision.get("authority_kind")=="e2p2-gate1-custom-ndk-python3145-provenance-audit" and decision.get("status")=="frozen-repository-audit-pass")
    ck("repository_input",decision.get("repository_input")=={"branch":"agent/epoch2-p2-standalone-build-facade","head":BASE_HEAD,"tree":BASE_TREE})
    ce=decision.get("collector_evidence",{})
    ck("collector_identity",ce.get("work_id")=="20260716-stage3-custom-ndk-python3145-audit-v1" and ce.get("archive_sha256")=="f24470ae0bb1450b1c555fbd63bbb9584c5e8dcc5fb72663075fda3de9c301b3" and ce.get("drive_file_id")=="18nhxfAbbg5QYBKrGPMCwCRhr11WoA8Tx")
    ck("collector_counts",ce.get("tracked_match_line_count")==426 and ce.get("tracked_matched_path_count")==126)
    ck("a2b_status",a2b.get("status")=="accepted")
    ck("a2b_class",a2b.get("authority_class")=="scoped-exact-binary-producer-toolchain")
    ck("a2b_scope",a2b.get("base_design",{}).get("historical_first_product_authority_unchanged") is True)
    ck("a2b_remote",a2b.get("authority_remote")=="gdrive:HW-T/cpython-android-cli/authorities/gate4a/toolchains/android-ndk-custom/r27/android-aarch64")
    prod=a2b.get("producer",{}); asset=prod.get("asset",{}); flow=prod.get("workflow",{})
    ck("ndk_revision",prod.get("ndk_revision")=="27.3.13750724")
    ck("ndk_host",prod.get("host_class")=="termux-native-android-bionic-aarch64" and prod.get("prebuilt_host")=="linux-arm64")
    ck("asset_identity",asset.get("name")=="android-ndk-r27d-aarch64-linux-android.tar.xz" and asset.get("size")==156427268 and asset.get("sha256")=="7aac94c85931c698ef13f8679c3472d3d6c7a4566e4c8bff112be91aff527bd7" and asset.get("md5")=="ab87309abc53830892e0556b91438fa5")
    ck("producer_binding",flow.get("run_id")==29265009312 and flow.get("job_id")==86867844060 and flow.get("commit")=="63b097b4db9b1d2ab445d6637eab16718f6c513b")
    overlay=a2b.get("toolchain_overlay",{}); patch=overlay.get("patch",{})
    ck("overlay_boundary",overlay.get("ephemeral") is True and overlay.get("original_ndk_mutated") is False)
    ck("overlay_original",overlay.get("original_lld_sha256")=="cf9f6f56dfcb286d52425a73f5ba7c7a17966cc2c71bea0ccb0f16c21d07b15b")
    ck("overlay_patch",patch.get("offset")==392 and patch.get("before")==8 and patch.get("after")==64 and patch.get("semantic")=="ELF64 PT_TLS p_align")
    ck("overlay_patched",overlay.get("patched_lld_sha256")=="eee71a33b1c9924eeb576673d033008b1e520f84a112a7102cc9482142bf5a09")
    not_accepted=a2b.get("claim_boundary",{}).get("not_accepted",[])
    ck("no_source_rebuild_claim","source-rebuild reproducibility of android-ndk-custom" in not_accepted)
    ck("no_official_equivalence_claim","equivalence with the official Linux-host NDK binary set" in not_accepted)
    ck("a6_status",a6.get("status")=="frozen-pass")
    product=a6.get("product",{})
    ck("product_version",product.get("python_version")=="3.14.5")
    ck("product_source",product.get("source_commit")=="5607950ef232dad16d75c0cf53101d9649d89115")
    ck("product_target",product.get("target_host")=="aarch64-linux-android" and product.get("canonical_host")=="aarch64-unknown-linux-android")
    ck("product_platform",product.get("android_api")==24 and product.get("ndk_version")=="27.3.13750724" and product.get("soabi")=="cpython-314-aarch64-linux-android")
    ck("product_fingerprint",product.get("runtime_fingerprint")=="6ce6e4cad493c1334fb10d893d7bcc6d49564cbe44081422ea346ce4c73ca537")
    arts=a6.get("artifacts",{})
    ck("runtime_artifact",arts.get("runtime-base",{}).get("archive_sha256")=="d01e142dae90cdca8681c6674999acc197d05bb1bec9a75468fe9b8cf4fff52d")
    ck("development_artifact",arts.get("development-addon",{}).get("archive_sha256")=="623d776bd9a987aac0417c360746b4917d666a5829a522ef43574b66493387e0")
    ck("test_artifact",arts.get("test-addon",{}).get("archive_sha256")=="7d397ab12cf1d70b2922754b8121936ae56270c45c7929f69656984cd6a0eb1d")
    ck("a6_external_status",a6audit.get("status")=="second-product-authority-freeze-approved")
    a3=a6audit.get("details",{}).get("archives",{}).get("a3",{})
    ck("a3_archive",a3.get("sha256")=="bfd241f959cb081a91f4866cb07cf2773d1028919de0ea0959ed0d95c8984202" and a3.get("size")==62379269)
    ck("gate6_status",gate6.get("status")=="accepted-bounded-feasibility")
    gate6_strings=set(strings(gate6))
    ck("gate6_key","cpython-3.14.5-linux-aarch64-none" in "\n".join(gate6_strings))
    gate6_doc=(root/"docs/evidence/STAGE3D_GATE6_MANAGED_PYTHON_FEASIBILITY_RESULT.md").read_text(encoding="utf-8")
    ck("gate6_consumer_boundary","Gate 6 proves feasibility, not productization" in gate6_doc)
    ck("stage3b_lock",lock.get("python_version")=="3.14.6" and lock.get("ndk_version")=="27.3.13750724")
    ck("facade_predecessor",facade.get("predecessor",{}).get("stage3b_authority")=="docs/stages/STAGE3B_FINAL.md")
    tracked={r.get("path"):r.get("blob_sha") for r in facade.get("tracked_inputs",[]) if isinstance(r,dict)}
    ck("facade_lock_pinned",tracked.get("config/products/cpython-3.14.6-aarch64-linux-android.lock.json")=="4b31a1f6c7c843ba8c5b652047a24e813c63fade")
    steps=[r.get("path") for r in facade.get("operations",{}).get("build",{}).get("steps",[]) if isinstance(r,dict)]
    ck("facade_stage3b_steps",steps==["experiments/stage3b-upstream-replay/prepare-replay.sh","experiments/stage3b-upstream-replay/run-replay.sh","experiments/stage3b-product-promotion/promote-replay-package.sh","scripts/build/build-launcher.sh"])
    finding=decision.get("custom_ndk_producer_finding",{})
    ck("decision_custom_use_proven",finding.get("proven") is True and finding.get("scope")=="stage3c-gate4a-second-product-cpython-3.14.5")
    promotion=decision.get("canonical_promotion_finding",{})
    ck("decision_no_global_promotion",promotion.get("project_wide_custom_ndk_canonical") is False and promotion.get("stage3b_python3146_producer_replaced") is False)
    e2=decision.get("e2p2_decision",{})
    ck("decision_facade_unchanged",e2.get("facade_inputs_change") is False and e2.get("tracked_product_lock")=="config/products/cpython-3.14.6-aarch64-linux-android.lock.json")
    ck("decision_gate2_unblocked",e2.get("gate2_unblocked") is True and e2.get("gate2_producer")=="frozen-stage3b-workstation-cpython-3.14.6")
    ck("decision_unqualified",e2.get("qualification")=="not-qualified" and e2.get("selectable") is False)
    current=(root/"docs/CURRENT_CONTEXT.md").read_text(encoding="utf-8")
    orientation=(root/"docs/PROJECT_ORIENTATION.md").read_text(encoding="utf-8")
    roadmap=(root/"docs/roadmap/EPOCH2_ROADMAP.md").read_text(encoding="utf-8")
    index=(root/"docs/INDEX.md").read_text(encoding="utf-8")
    evidence=(root/"docs/evidence/E2P2_GATE1_CUSTOM_NDK_PYTHON3145_PROVENANCE_AUDIT.md").read_text(encoding="utf-8")
    handoff=(root/"docs/handoff/2026-07-17-e2p2-custom-ndk-provenance-audit.md").read_text(encoding="utf-8")
    ck("current_context","Gate 2 is unblocked only for the pinned Stage 3-B producer" in current)
    ck("orientation","did not become the project-wide canonical NDK" in orientation)
    ck("roadmap","Gate 2 provenance precondition" in roadmap and "unchanged Stage 3-B CPython 3.14.6" in roadmap)
    ck("index_links","E2P2_GATE1_CUSTOM_NDK_PYTHON3145_PROVENANCE_AUDIT.md" in index and "2026-07-17-e2p2-custom-ndk-provenance-audit.md" in index)
    ck("evidence_doc","FROZEN REPOSITORY AUDIT PASS" in evidence and "custom-NDK use is therefore real but scoped" in evidence)
    ck("handoff_doc","E2-P2 Gate 2 is now unblocked" in handoff)
    ck("branch",git(root,"symbolic-ref","--quiet","--short","HEAD")=="agent/epoch2-p2-standalone-build-facade")
    ck("diff_check",subprocess.run(["git","diff","--check","HEAD"],cwd=root).returncode==0)
    failed=sorted(k for k,v in checks.items() if not v)
    return {"schema_version":1,"verification_kind":"e2p2-custom-ndk-python3145-provenance-audit","pass":not failed and not errors,"check_count":len(checks),"pass_count":sum(checks.values()),"failed_checks":failed,"parse_errors":errors,"checks":dict(sorted(checks.items())),"claim_boundary":"Repository-only provenance audit. It proves scoped custom-NDK use for the exact CPython 3.14.5 Gate 4A product, rejects project-wide canonical promotion, and preserves unchanged Stage 3-B CPython 3.14.6 E2-P2 façade inputs."}

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]); ns=ap.parse_args()
    result=verify(ns.root); print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result["pass"] else 1
if __name__=="__main__": raise SystemExit(main())

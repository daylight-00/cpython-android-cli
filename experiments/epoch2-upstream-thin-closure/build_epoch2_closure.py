#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

OUT_REL = Path('experiments/epoch2-upstream-thin-closure')
AUTH = {
 'epoch1_closure': 'docs/epochs/EPOCH1_CLOSURE.md',
 'project_model': 'docs/agent/PROJECT_MODEL.md',
 'epoch2_charter': 'docs/epochs/EPOCH2_CHARTER.md',
 'epoch3_charter': 'docs/epochs/EPOCH3_CHARTER.md',
 'adr0006': 'docs/decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md',
 'plan': 'experiments/epoch2-upstream-thin-plan/plan-authority.json',
 'control': 'experiments/epoch2-upstream-thin-control/upstream-control-authority.json',
 'artifact': 'experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json',
 'loader': 'experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json',
 'sdk': 'experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json',
 'data': 'experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json',
 'feature': 'experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json',
 'platform': 'experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json',
 'evolution': 'experiments/epoch2-upstream-thin-upstream-evolution/upstream-evolution-authority.json',
 'api36': 'experiments/epoch2-upstream-thin-api36-controlled-comparison/api36-controlled-comparison-authority.json',
}
EXPECTED = {
 'plan': '62b3b07f37a90b497747562bb00a9db5a3d78b3b2cb45df8f66db22818f5eafa',
 'control': '6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c',
 'artifact': '387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306',
 'loader': '05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2',
 'sdk': '6cff1984d4601a37e8b57762bb170a57e695cb64d516c1dab0023b7e809dc808',
 'data': 'be25e52aba1d6c9d0b2e25fec2bd1d8a0a0d9eb870436f00e81f347e90d012b7',
 'feature': '3b56a38898a3a2384cf9419fe3cd124faa8dbf367cdd5532724b3424092a62e5',
 'platform': 'b21eddfee574343772d0875a7b6f26aa7b5dd494ccf0a5f1be9b8c09201276f4',
 'evolution': 'a45566c4ea0e9dbb1aed53e27d07398e81835f6221da2ce28f78471c2467ace5',
 'api36': '576f0f833164a2748a5c494780f429b4c22af5cb07d331248ac7572611b1339e',
}

def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p: Path) -> Any: return json.loads(p.read_text(encoding='utf-8'))
def dump(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)+'\n', encoding='utf-8')

def binding(root: Path, key: str) -> dict[str, Any]:
    p = root / AUTH[key]
    return {'path': AUTH[key], 'sha256': sha(p)}

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root', type=Path, default=Path('.')); a=ap.parse_args()
    root=a.root.resolve(); out=root/OUT_REL; out.mkdir(parents=True, exist_ok=True)
    docs={k:root/v for k,v in AUTH.items()}
    for k,h in EXPECTED.items():
        actual=sha(docs[k])
        if actual!=h: raise SystemExit(f'required authority mismatch:{k}:{actual}')
    # Epoch boundary status amendments are stable-policy updates triggered by closure.
    e2p=docs['epoch2_charter']; e2t=e2p.read_text(encoding='utf-8')
    old_e2='> **Status:** ACTIVE — recalibrated 2026-07-19'
    new_e2='> **Status:** CLOSED — producer-independent evidence export frozen 2026-07-21'
    if e2t.count(old_e2)!=1: raise SystemExit('Epoch 2 charter status anchor mismatch')
    e2p.write_text(e2t.replace(old_e2,new_e2),encoding='utf-8')
    e3p=docs['epoch3_charter']; e3t=e3p.read_text(encoding='utf-8')
    old_e3='> **Status:** PLANNED'
    new_e3='> **Status:** READY FOR INITIALIZATION — selection not started'
    if e3t.count(old_e3)!=1: raise SystemExit('Epoch 3 charter status anchor mismatch')
    e3p.write_text(e3t.replace(old_e3,new_e3),encoding='utf-8')
    planp=root/'docs/roadmap/EPOCH2_PROGRAM_PLAN.md'; plant=planp.read_text(encoding='utf-8')
    old_plan='> **Lifecycle:** canonical active plan'
    new_plan='> **Lifecycle:** historical completed plan — closed by E2-CLOSURE'
    if plant.count(old_plan)!=1: raise SystemExit('Epoch 2 program plan lifecycle anchor mismatch')
    planp.write_text(plant.replace(old_plan,new_plan),encoding='utf-8')
    control=load(docs['control']); artifact=load(docs['artifact']); loader=load(docs['loader']); sdk=load(docs['sdk']); data=load(docs['data']); feature=load(docs['feature']); platform=load(docs['platform']); evolution=load(docs['evolution']); api36=load(docs['api36']); plan=load(docs['plan'])
    upstream=control['official_input']
    bindings={k:binding(root,k) for k in AUTH}

    gates=[
      {'id':'E2-G1','name':'Exact upstream control','status':'resolved-pass','finding':'Official Python.org Android input, dependency closure, provenance, and mutation-free intake are exact.','evidence':['control'],'criteria':{'official_upstream_identity':control['claim_boundary']['official_upstream_identity'],'no_mutation_fingerprint':control['claim_boundary']['no_mutation_fingerprint'],'unresolved_dependencies':control['inventory']['unresolved_dependencies']}},
      {'id':'E2-G2','name':'Direct-adaptation viability','status':'resolved-pass','finding':'Exact official bytes admit a bounded standalone launcher, relative native lookup, relocation, and fully enumerated local deltas.','evidence':['loader','sdk','data'],'criteria':{'launcher_variant':loader['selection']['launcher_variant'],'loader_variant':loader['selection']['loader_variant'],'whole_prefix_relocation_pass':loader['relocation']['whole_prefix_relocation_pass'],'runtime_paths_reroot_after_movement':sdk['normalization']['runtime_paths_reroot_after_movement']}},
      {'id':'E2-G3','name':'Clean loader and relocation decision','status':'resolved-pass','finding':'LR-3 with LA-2 removes project-required LD_LIBRARY_PATH and loader-bootstrap re-execution while preserving 16 KiB static alignment.','evidence':['loader'],'criteria':loader['selection']['exit_condition']},
      {'id':'E2-G4','name':'Truthful Astral artifact contract','status':'resolved-pass-with-epoch3-flavor-decision','finding':'Full/install-only/stripped/PYTHON.json semantics and unavailable fields are defined; duplicate stripped bytes remain an Epoch 3 packaging decision.','evidence':['artifact'],'criteria':{'format_version':artifact['python_json']['format_version'],'artifact_flavors':[x['flavor'] for x in artifact['artifact_set']['artifacts']],'stripped_changed_count':artifact['flavor_decision_inputs']['stripped_changed_count'],'selectable':artifact['artifact_set']['selectable']}},
      {'id':'E2-G5','name':'Runtime and SDK evidence','status':'resolved-pass-bounded','finding':'Runtime metadata relocation and an on-device native-extension SDK are proven; cross-build SDK is explicitly unavailable/deferred.','evidence':['sdk'],'criteria':{'exit_condition':sdk['exit_condition'],'sdk_flavor_decision':sdk['sdk_flavor_decision']}},
      {'id':'E2-G6','name':'Capability and data decision inputs','status':'resolved-pass-as-selection-input','finding':'Data/state and feature surfaces have complete bounded evidence dispositions without converting experiment success into product inclusion.','evidence':['data','feature'],'criteria':{'data_exit':data['exit_condition'],'feature_exit':feature['exit_condition'],'epoch3_selection_made':feature['epoch3_selection_made']}},
      {'id':'E2-G7','name':'Platform and evolution evidence','status':'resolved-pass-with-explicit-withholding','finding':'Current-target runtime, static 16 KiB, API-36 comparison, patch update, and 3.15 preview evidence are complete; minimum API, runtime 16 KiB device, and broad-context claims remain withheld.','evidence':['platform','evolution','api36'],'criteria':{'platform_exit':platform['exit_condition'],'evolution_exit':evolution['exit_condition'],'api36_exit':api36['exit_condition'],'withheld_claims':platform['withheld_claims']}},
      {'id':'E2-G8','name':'Producer-independent evidence export','status':'resolved-pass','finding':'The closure namespace freezes exact inputs, local delta, invariants, selection candidates, claims, risks, accepted seed, and Epoch 4 producer deferrals.','evidence':['closure-output-set'],'criteria':{'required_sections':['exact_upstream_inputs','exact_local_delta','mandatory_invariants','selectable_item_evidence','selection_candidates_and_tradeoffs','supported_and_withheld_claims','artifact_and_metadata_contract','qualification_contract','unresolved_risks','accepted_product_seed','epoch4_deferred_questions']}}
    ]
    gate_matrix={'schema_version':1,'matrix_kind':'epoch2-closure-gate-matrix','status':'resolved-pass-8-of-8','predecessor_authority':bindings['api36'],'gate_count':8,'resolved_count':8,'all_resolved':True,'closure_decision':'close-epoch2-and-enable-epoch3-initialization-without-product-selection','epoch3_selection_made':False,'gates':gates,'authority_bindings':bindings}
    dump(out/'closure-gate-matrix.json',gate_matrix)

    ref={'schema_version':1,'reference_hierarchy_kind':'epoch3-two-axis-reference-policy','status':'frozen-input-to-epoch3-initialization','overall_primary_reference':'Astral python-build-standalone','primary_reference_scope':['standalone product architecture','artifact family','archive layout','PYTHON.json and consumer metadata semantics'],'secondary_references':['Python.org / CPython Android prebuilt products','CPython source releases','BeeWare dependency products selected by CPython'],'android_input_authority':'Python.org / CPython Android release process','axes':[
      {'axis':'consumer-product-structure','primary':'Astral python-build-standalone','governs':['artifact family','archive layout','PYTHON.json semantics','release index','consumer metadata'],'android_authority':False},
      {'axis':'android-runtime-provenance','primary':'Python.org / CPython Android release process','secondary':'CPython source plus BeeWare dependency products selected by CPython','governs':['runtime bytes','Android ABI','module surface','dependency topology','official API policy'],'android_authority':True},
      {'axis':'full-source-producer','primary':'Epoch 4 project-owned producer','secondary':'Epoch 2 Class B/C controlled evidence','governs':['CPython/dependency source builds','NDK/API producer policy','source-level optimization'],'available_in_epoch3':False}
    ],'conflict_resolution':['Android ABI/runtime provenance overrides structural-reference assumptions.','Astral structure governs product representation only where truthful for upstream-derived Android inputs.','Every local byte mutation requires explicit manifest and justification.'],'bound_policy_documents':[bindings['project_model'],bindings['epoch3_charter'],bindings['adr0006']]}
    dump(out/'reference-hierarchy.json',ref)

    invariants=[
      ('INV-01','verified-upstream-provenance',['control']),('INV-02','pure-bionic-and-android-public-native-closure',['control','loader']),('INV-03','no-required-termux-native-provider-or-hard-coded-termux-identity',['data','platform']),('INV-04','fresh-extraction-execution',['loader','platform']),('INV-05','whole-prefix-relocation',['loader','sdk']),('INV-06','no-project-required-LD_LIBRARY_PATH',['loader']),('INV-07','no-loader-bootstrap-self-reexecution',['loader']),('INV-08','truthful-astral-structured-artifacts-and-PYTHON.json',['artifact']),('INV-09','exact-mutation-provenance-license-checksum-and-qualification-accounting',['artifact','evolution','api36']),('INV-10','runtime-and-subprocess-identity',['loader','feature']),('INV-11','native-extension-and-DT_NEEDED-closure',['control','loader','sdk']),('INV-12','externalized-writable-state-and-independent-data-lifecycle',['data']),('INV-13','update-rollback-and-acquisition-lineage-inherited-or-revalidated',['epoch1_closure','evolution']),('INV-14','experiment-success-does-not-imply-product-inclusion',['plan','feature','api36'])]
    inv={'schema_version':1,'invariant_set_kind':'epoch2-to-epoch3-mandatory-invariants','status':'frozen-input-to-selection','invariant_count':len(invariants),'invariants':[{'id':i,'name':n,'requirement':'mandatory','evidence':[bindings[k] for k in ks],'epoch3_obligation':'preserve-or-explicitly-revalidate'} for i,n,ks in invariants]}
    dump(out/'mandatory-invariants.json',inv)

    epoch1_items=[
      ('E1-I01','runtime-and-subprocess-identity','mandatory-revalidate-in-clean-product'),('E1-I02','native-closure-and-extension-surface','mandatory-revalidate-in-clean-product'),('E1-I03','CA-and-timezone-boundaries','selection-required'),('E1-I04','uv-and-venv-behavior','selection-required'),('E1-I05','whole-prefix-relocation','mandatory-preserve'),('E1-I06','archive-and-manifest-identity','mandatory-preserve'),('E1-I07','ownership-and-dependency-policy','initialization-input-not-seed-code'),('E1-I08','transaction-recovery-residual-and-transition-semantics','release-operations-obligation'),('E1-I09','publication-and-acquisition-identity','release-operations-obligation'),('E1-I10','source-producer-reconstruction','defer-to-epoch4')]
    e1={'schema_version':1,'matrix_kind':'epoch1-inheritance-to-epoch3','source':bindings['epoch1_closure'],'status':'frozen-handoff-input','items':[{'id':i,'inherited_contract':n,'epoch3_disposition_class':d,'automatic_implementation_import':False} for i,n,d in epoch1_items]}
    dump(out/'epoch1-inheritance-matrix.json',e1)

    options=[
      ('SEL-01','base-pip','feature',feature),('SEL-02','pip-command-wrappers','feature',feature),('SEL-03','CA-payload-policy','data',data),('SEL-04','timezone-payload-policy','data',data),('SEL-05','runtime-only-mode','sdk',sdk),('SEL-06','on-device-SDK-mode','sdk',sdk),('SEL-07','cross-build-SDK-mode','sdk',sdk),('SEL-08','subprocess-secondary-surface','feature',feature),('SEL-09','venv-relocation-and-update-cases','feature',feature),('SEL-10','multiprocessing-primitives','feature',feature),('SEL-11','uv-system-versus-managed-integration','feature',feature),('SEL-12','install_only_stripped-separate-artifact-or-alias','artifact',artifact),('SEL-13','symbols-debug-test-artifacts','artifact',artifact),('SEL-14','official-API-floor-versus-API36-input','api36',api36),('SEL-15','minimum-supported-Android-API','platform',platform),('SEL-16','runtime-16KiB-device-support','platform',platform),('SEL-17','supported-Termux-ADB-root-APK-contexts','platform',platform),('SEL-18','supported-version-and-release-cadence','evolution',evolution)
    ]
    opt_rows=[]
    for i,n,k,obj in options:
        evidence_disposition='pass' if k not in {'platform','feature','sdk'} else 'bounded-pass'
        if n in {'cross-build-SDK-mode','multiprocessing-primitives','minimum-supported-Android-API','runtime-16KiB-device-support','supported-Termux-ADB-root-APK-contexts'}: evidence_disposition='unavailable-or-bounded-unresolved'
        opt_rows.append({'id':i,'item':n,'evidence_disposition':evidence_disposition,'selection_status':'pending-epoch3','allowed_product_dispositions':['adopt','adopt-with-redesign','exclude','defer-to-epoch4'],'evidence':[bindings[k]],'experiment_success_implies_inclusion':False})
    selectable={'schema_version':1,'register_kind':'epoch3-selection-input-register','status':'complete-evidence-input-selection-not-started','item_count':len(opt_rows),'selection_complete':False,'product_selection_made':False,'items':opt_rows}
    dump(out/'selectable-options.json',selectable)

    deviations=[
      ('DEV-P01','minimal-Py_BytesMain-launcher','product-delta','required-for-standalone-CLI','include-bounded-overlay'),
      ('DEV-P02','per-object-relative-RUNPATH-closure','product-delta','required-for-relocatable-standalone-Bionic-loading','include-only-when-byte-change-required'),
      ('DEV-P03','runtime-sysconfig-relocation-normalization','product-delta','required-for-correct-relocated-runtime-metadata','include-minimal-runtime-subset'),
      ('DEV-P04','SDK-consumer-metadata-normalization','optional-product-delta','required-only-for-on-device-SDK','exclude-from-runtime-only-flavor'),
      ('DEV-P05','upstream-derived-full-semantics','representation-delta','official-package-lacks-Astral-producer-object-tree','name-and-document-truthfully'),
      ('DEV-P06','external-DATA_ROOT-and-STATE_ROOT-policy','product-policy','required-for-host-neutral-read-only-install','include-contract-not-unselected-payloads'),
      ('DEV-X01','custom-r30-beta2-SDK-overlay','experiment-only','API36-controlled-source-build-on-Termux','exclude-from-default-Epoch3-product'),
      ('DEV-X02','Termux-host-compiler-and-linker-argument-filtering','producer-only','prevent-host-libc-and-libz-contamination','defer-to-Epoch4-producer'),
      ('DEV-X03','source-deps-android-env-NDK-and-API36-precedence','producer-only','materialize-Class-C-controlled-build','defer-to-Epoch4-producer'),
      ('DEV-X04','libffi-configure-cache-fallback','producer-only','cross-configure-declaration-false-positive','replace-with-upstream-or-config-site-fix-in-Epoch4'),
      ('DEV-X05','CPython-android.py-environment-capture-portability','producer-only','Termux-shell-export-format','upstream-candidate-or-Epoch4-ephemeral-patch'),
      ('DEV-X06','exact-BeeWare-development-asset-prepopulation','experiment-control','official-final-package-is-not-a-complete-rebuild-SDK','retain-as-evidence-not-product-code')
    ]
    dev={'schema_version':1,'register_kind':'reference-deviation-and-reduction-register','status':'frozen-closure-review','deviations':[{'id':i,'change':c,'class':cl,'necessity':n,'epoch3_default_action':a} for i,c,cl,n,a in deviations],'reduction_opportunities':['Do not run patchelf on verified-unchanged ELF objects; record changed, verified-unchanged, and not-applicable separately.','Preserve exact upstream package bytes in an immutable input subtree and derive overlays into a separate install tree.','Split runtime metadata normalization from optional SDK metadata normalization.','Decide whether install_only_stripped is an alias, omitted duplicate, or separately meaningful artifact.','If API36 is selected, reproduce with a stable official NDK and non-Termux producer before product adoption.']}
    dump(out/'reference-deviation-register.json',dev)

    producer={'schema_version':1,'register_kind':'epoch4-deferred-producer-questions','status':'deferred-not-blocking-epoch2-closure','questions':[
      {'id':'P-01','question':'stable official NDK and API policy for source production','source_evidence':[bindings['api36']]},
      {'id':'P-02','question':'host-isolated CPython and six-dependency source producer','source_evidence':[bindings['api36']]},
      {'id':'P-03','question':'upstreamable android.py environment-capture portability','source_evidence':[bindings['api36']]},
      {'id':'P-04','question':'libffi declaration-aware configure solution replacing tactical cache override','source_evidence':[bindings['api36']]},
      {'id':'P-05','question':'cross-build SDK and relocatable NDK/sysroot contract','source_evidence':[bindings['sdk']]},
      {'id':'P-06','question':'source-level optimization, PGO/LTO, static/shared policy, and reproducible object-tree artifacts','source_evidence':[bindings['project_model'],bindings['epoch3_charter']]}
    ],'epoch3_product_contract_must_not_depend_on_resolution':True}
    dump(out/'producer-only-deferred-register.json',producer)

    seed={'schema_version':1,'boundary_kind':'epoch3-accepted-product-seed','status':'accepted-for-epoch3-initialization-not-selectable-release','seed_id':'pythonorg-cpython-3.14.6-android-aarch64-upstream-thin-v1','official_input':upstream,'structural_reference':'Astral python-build-standalone','android_runtime_reference':'Python.org / CPython Android plus BeeWare dependency topology selected by CPython','included_bounded_overlays':[{'id':'LA-2','kind':'minimal-standalone-launcher','sha256':loader['selection']['launcher_sha256']},{'id':'LR-3','kind':'relative-native-lookup-plan','requirements':loader['selection']['exit_condition']},{'id':'runtime-metadata-minimum','kind':'relocation-aware-runtime-metadata','requirements':sdk['exit_condition']},{'id':'immutable-input-derived-install','kind':'deterministic-transformation-and-mutation-manifest'},{'id':'three-root-contract','kind':'immutable-install-updateable-data-writable-state','requirements':data['exit_condition']}],'excluded_from_seed':['API36 Class B or C as default product input','custom NDK overlays and source-build wrappers','source dependency recipes or source producer code','unselected pip, CA, timezone, multiprocessing, uv, SDK, symbols, debug, test, or context claims','publication and product selectability'],'artifact_boundary':{'full':'upstream-derived reconstruction and audit input; not a project-owned CPython/dependency object tree','install_only':'derived runtime/product tree','install_only_stripped':'selection required because prototype bytes equal install_only','python_json_format':artifact['python_json']['format_version']},'acceptance_reason':'Smallest content-addressed upstream-derived seed that satisfies mandatory standalone and relocation invariants without importing producer-only experimental machinery.','epoch3_selection_made':False,'release_product':False,'evidence':[bindings['control'],bindings['artifact'],bindings['loader'],bindings['sdk'],bindings['data']]}
    dump(out/'accepted-product-seed-boundary.json',seed)

    risks=[
      ('R-01','minimum-supported-Android-API-unselected','selection-required',False),('R-02','runtime-16KiB-device-support-unqualified','additional-direct-device-evidence-or-exclude-claim',False),('R-03','ADB-root-APK-and-non-Termux-contexts-unqualified','select-and-qualify-only-supported-contexts',False),('R-04','emulator-unqualified-and-waived','retain-unclaimed-or-run-new-evidence',False),('R-05','other-Android-ABIs-unqualified','exclude-until-evidenced',False),('R-06','CA-and-timezone-payload-provider-and-update-policy-unselected','epoch3-selection',False),('R-07','multiprocessing-environment-inadequate','exclude-or-redesign-and-retest',False),('R-08','pre-existing-venv-after-base-relocation-fails','document-support-boundary-or-redesign',False),('R-09','install_only_stripped-duplicates-install_only','artifact-selection',False),('R-10','runtime-only-versus-on-device-SDK-versus-cross-SDK-unselected','epoch3-selection',False),('R-11','uv-system-versus-managed-contract-unselected','epoch3-selection',False),('R-12','API36-production-input-would-require-stable-official-NDK-reproduction','conditional-on-API36-selection',False),('R-13','upstream-derived-full-differs-from-Astral-source-producer-full','truthful-metadata-and-documentation-required',False),('R-14','supported-version-release-cadence-security-and-data-update-operations-unselected','epoch3-contract-freeze',False),('R-15','source-producer-host-isolation-and-libffi-fix-deferred','epoch4',False),('R-16','publication-not-authorized','release-governance',False)
    ]
    risk={'schema_version':1,'register_kind':'epoch2-closure-unresolved-risk-register','status':'complete-no-hidden-closure-blocker','risk_count':len(risks),'closure_blocker_count':sum(1 for *_,b in risks if b),'risks':[{'id':i,'risk':n,'required_disposition':d,'blocks_epoch2_closure':b} for i,n,d,b in risks],'claim_policy':'Unresolved risks constrain Epoch 3 selection and release claims; they do not become implicit product support.'}
    dump(out/'unresolved-risk-register.json',risk)

    export={'schema_version':1,'export_kind':'epoch2-producer-independent-evidence-export','status':'frozen-complete-for-epoch3-initialization','producer_independent':True,'epoch3_selection_made':False,'exact_upstream_inputs':[upstream],'authority_bindings':bindings,'reference_hierarchy':{'path':str(OUT_REL/'reference-hierarchy.json')},'exact_local_delta':{'path':str(OUT_REL/'reference-deviation-register.json')},'mandatory_invariants':{'path':str(OUT_REL/'mandatory-invariants.json'),'count':len(invariants)},'epoch1_inheritance':{'path':str(OUT_REL/'epoch1-inheritance-matrix.json'),'count':len(epoch1_items)},'selectable_item_evidence':{'path':str(OUT_REL/'selectable-options.json'),'count':len(opt_rows),'selection_complete':False},'selection_candidates_and_tradeoffs':{'path':str(OUT_REL/'selectable-options.json')},'supported_platform_claims':platform['supported_contexts'],'withheld_platform_claims':platform['withheld_claims'],'artifact_and_metadata_contract':seed['artifact_boundary'],'qualification_contract':{'fresh_extraction':True,'whole_prefix_relocation':True,'native_closure':True,'required_extensions':True,'runtime_sysconfig':True,'selected_feature_tests_only':True,'minimum_api_and_runtime_16k_require_explicit_selection_and_evidence':True},'unresolved_risks':{'path':str(OUT_REL/'unresolved-risk-register.json'),'count':len(risks)},'accepted_product_seed':{'path':str(OUT_REL/'accepted-product-seed-boundary.json'),'seed_id':seed['seed_id']},'epoch4_deferred_questions':{'path':str(OUT_REL/'producer-only-deferred-register.json'),'count':len(producer['questions'])},'closure_gate_matrix':{'path':str(OUT_REL/'closure-gate-matrix.json'),'resolved':'8/8'},'consumer_rule':'Epoch 3 must consume this export without importing the full laboratory history and must complete the selection register before implementation expands.'}
    dump(out/'producer-independent-evidence-export.json',export)

    init={'schema_version':1,'contract_kind':'epoch3-initialization-contract','status':'ready-not-started','input_export':str(OUT_REL/'producer-independent-evidence-export.json'),'accepted_seed':str(OUT_REL/'accepted-product-seed-boundary.json'),'reference_hierarchy':str(OUT_REL/'reference-hierarchy.json'),'mandatory_invariants':str(OUT_REL/'mandatory-invariants.json'),'required_initialization_gates':['E3-I1 accepted evidence export','E3-I2 complete selection register','E3-I3 clean repository boundary','E3-I4 contract freeze'],'required_selection_item_ids':[x['id'] for x in opt_rows],'clean_repository_boundary':{'import':['product code','bounded provenance','selected tests','release automation','accepted documentation'],'exclude':['complete laboratory history','producer-only experimental wrappers','unselected capabilities and claims']},'implementation_may_expand_before_selection_complete':False,'epoch3_selection_started':False,'next_action_class':'initialize-epoch3-from-accepted-evidence-export'}
    dump(out/'epoch3-initialization-contract.json',init)

    (out/'README.md').write_text('''# Epoch 2 Closure and Epoch 3 Initialization Export\n\nThis frozen namespace resolves E2-G1 through E2-G8 and provides a producer-independent, content-addressed input for a separate Epoch 3 initialization session. It accepts one minimal upstream-derived seed, preserves all product choices as pending, separates product deltas from custom-NDK and source-producer experiments, carries Epoch 1 inherited obligations forward, and records every unresolved risk without converting it into an implicit support claim.\n\nEpoch 2 closure does not start feature selection, make a product selectable, authorize publication, choose API 36, establish a minimum Android API, qualify runtime 16 KiB devices, or import the complete laboratory history into Epoch 3.\n''',encoding='utf-8')
    print(json.dumps({'pass':True,'output':str(out),'gate_count':8,'selection_item_count':len(opt_rows),'risk_count':len(risks)},indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())

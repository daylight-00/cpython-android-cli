#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

PRIMARY = [
    'gate-contract.json','upstream-input-manifest.json','package-and-file-hashes.json',
    'elf-and-extension-inventory.json','dependency-provider-map.json','sysconfig-census.json',
    'package-layout-map.json','provenance-map.json','producer-delta.json','independent-audit.json',
]
NEW_DOCS = [
    'README.md','gate-contract.json','upstream-input-manifest.json','package-and-file-hashes.json',
    'elf-and-extension-inventory.json','dependency-provider-map.json','sysconfig-census.json',
    'package-layout-map.json','provenance-map.json','producer-delta.json','independent-audit.json',
    'upstream-control-authority.json','evidence-freeze.md',
]

def load(p: Path): return json.loads(p.read_text(encoding='utf-8'))
def dump(p: Path, o): p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p: Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def update_transport_protocol(root: Path) -> tuple[int, str]:
    path=root/'docs/agent/SESSION_PROTOCOL.md'
    text=path.read_text(encoding='utf-8')
    text=re.sub(r'^> \*\*Revision:\*\* \d+\s*$', '> **Revision:** 2', text, count=1, flags=re.M)
    old='''## SP-03 — Google Drive first

Use the Google Drive connector as the first attempt for project artifact discovery, result retrieval, direct-child folder inspection, and raw-byte readback when the connector is available. Resolve duplicate names with parent, folder ID, creation time, and direct-child listing. Compare reported size and SHA-256 whenever raw bytes can be fetched.

## SP-04 — Connector failure boundary

For assistant-generated files, attempt the normal raw-file Drive path once when supported. If it fails, do not retry through format conversion, native Google files, unrelated endpoints, or repeated calls. Expose the exact artifact under `/mnt/data` with its real filename. A later retry requires a later turn or an explicit request.
'''
    new='''## SP-03 — Directional Google Drive transport

The transport direction determines the responsible interface:

- **agent → owner:** the agent attempts one raw-file upload through the Google Drive connector. The owner receives the package with `rclone` from the designated Drive location.
- **owner → agent:** the owner uploads one complete result archive and sidecar with `rclone` to the designated Drive folder. The agent discovers the folder, lists direct children when needed, and fetches the exact raw bytes through the Google Drive connector.

The Google Drive connector is always the agent's first transport and receipt-readback interface when available. Resolve duplicate names with parent, folder ID, creation time, and direct-child listing. Compare reported size and SHA-256 whenever raw bytes can be fetched.

## SP-04 — Connector failure boundary

For agent-generated files, attempt the normal raw-file Drive upload exactly once when supported. If that connector call fails, do not retry, convert formats, use a native Google file, call another endpoint, invoke command-line upload, or attempt another transport. Expose the exact artifact under `/mnt/data` with its real filename as the user-visible fallback.

For owner-generated results, attempt retrieval through the Google Drive connector. If connector discovery or raw-byte fetch fails, stop and report the exact connector failure. Do not substitute `curl`, `wget`, network Git, assistant-side `rclone`, web download, or an unrelated attachment path in the same turn.
'''
    if old not in text:
        if new not in text: raise SystemExit('session transport block not found')
    else:
        text=text.replace(old,new)
    old_loop='''execution result
  owner -> agent: one complete receipt/result .tar.zst + sidecar, normally uploaded to Drive
```

Group related artifacts into one archive per direction whenever practical. Binary connector mounts may use a `.bin` suffix; content identity, not suffix, is authority.
'''
    new_loop='''execution result
  owner -> agent: owner uploads one complete receipt/result .tar.zst + sidecar with rclone;
                  agent retrieves it through the Google Drive connector
```

The designated default exchange folder is `HW-T-results` unless a task explicitly names another folder. Group related artifacts into one archive per direction whenever practical. Binary connector mounts may use a `.bin` suffix; content identity, not suffix, is authority. A connector-fetched `.bin` file is accepted only after its SHA-256 matches the owner-supplied sidecar.
'''
    if old_loop not in text:
        if new_loop not in text: raise SystemExit('session transport loop not found')
    else:
        text=text.replace(old_loop,new_loop)
    path.write_text(text,encoding='utf-8')
    return 2, sha(path)

def completion_contract(action: str, successor_action: str, successor_id: str):
    return {
      'always': {
        'all_required_verifiers_must_pass': True,
        'clean_main_and_bundle_export_ready_on_close': True,
        'forbidden_new_authority_bindings': ['docs/current/STATE.json','docs/current/AGENT_TASK.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'],
        'generated_views_must_be_regenerated': True,
        'new_markdown_or_json_requires_registry_update': True,
        'one_runner_and_complete_receipt_required': True,
      },
      'contract_version': 1,
      'fail': {
        'allowed_action_policy':'retain-current-action-or-select-cataloged-bounded-correction',
        'complete_receipt_required':True,
        'correction_task_must_be_cataloged':True,
        'correction_task_must_resume_action_class':action,
        'required_failure_records':['first-meaningful-failure','failure-classification','blocked-downstream','claim-boundary'],
        'required_state_updates':['state_revision','predecessor','active_work_package','blockers','unresolved_risks','updated_by_transaction'],
      },
      'pass': {
        'required_catalog_updates':['bind-accepted-ut1-authority-into-successor','activate-successor-task','define-successor-completion-contract-before-selection'],
        'required_output_namespace':'experiments/epoch2-upstream-thin-artifact-prototype/',
        'required_output_roles':['artifact-contract','python-json-schema-mapping','unavailable-field-policy','deterministic-derivation-rules','archive-root-and-path-contract','member-manifests-and-checksums','artifact-flavor-decision-inputs','consumer-extraction-contract','independent-audit','machine-authority','evidence-freeze'],
        'required_state_updates':['state_revision','predecessor','accepted_authorities','program.gate','program.next_action_class','next_action_class','control_work.next_action_class','control_work.resume_program_action_class','unresolved_risks','updated_by_transaction'],
        'successor_action_class':successor_action,'successor_must_exist':True,'successor_task_id':successor_id,
      },
    }

def registry_entry(path: str):
    is_md=path.endswith('.md')
    name=Path(path).name
    if name=='independent-audit.json': domain='audit'
    elif name=='gate-contract.json': domain='machine_contract'
    elif name=='upstream-control-authority.json': domain='machine_authority'
    else: domain='claim_evidence' if is_md else 'machine_evidence'
    return {
      'authority_domain':domain,'format':'md' if is_md else 'json','lifecycle_class':'FROZEN_AUTHORITY',
      'machine_binding_policy':'allowed','migration_action':'e2-r1-ut0-exact-official-upstream-control',
      'mutability':'immutable','onboarding_visibility':'secondary' if is_md else 'machine','owner':'epoch2-research',
      'path':path,'planned_canonical_parent':'docs/authorities/experiments/INDEX.md' if is_md else 'docs/authorities/machine/INDEX.md',
      'rationale':'','supersession_rule':'Explicit successor experiment or authority only.','update_trigger':'Never edit after freeze; create successor authority.',
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--output-dir',default='experiments/epoch2-upstream-thin-control'); ap.add_argument('--predecessor-head',required=True); ap.add_argument('--predecessor-tree',required=True); x=ap.parse_args()
    root=Path(x.root).resolve(); out=root/x.output_dir
    audit=load(out/'independent-audit.json')
    if audit.get('pass') is not True: raise SystemExit('independent audit is not PASS')
    manifest=load(out/'upstream-input-manifest.json'); hashes=load(out/'package-and-file-hashes.json'); elf=load(out/'elf-and-extension-inventory.json'); dep=load(out/'dependency-provider-map.json'); sysc=load(out/'sysconfig-census.json')
    file_ids={f:sha(out/f) for f in PRIMARY}
    readme=f'''# E2-R1/UT-0 — Exact official upstream control

This experiment freezes the exact unmodified Python.org CPython 3.14.6 Android aarch64 embeddable package as the sole upstream runtime input for the next research gate.

It records archive and member identities, safe no-mutation extraction, ELF and native-extension topology, dependency providers, sysconfig and minimum-API surfaces, package layout, source/dependency/license provenance, and the bounded delta against the reconstructed Termux-native producer authority.

The accepted claim is binary and metadata identity only. Runtime execution, relocation, launcher behavior, device qualification, product selection, and publication remain outside this authority.
'''
    (out/'README.md').write_text(readme,encoding='utf-8')
    authority={
      'schema_version':1,'authority_kind':'e2-r1-ut0-exact-official-upstream-control','status':'frozen-pass-exact-official-upstream-control',
      'predecessor':{'commit':x.predecessor_head,'tree':x.predecessor_tree},
      'official_input':{'filename':manifest['filename'],'url':manifest['package_url'],'sha256':manifest['sha256'],'size':manifest['size'],'version':manifest['version'],'target':manifest['target'],'minimum_android_api':manifest['minimum_android_api']},
      'inventory':{'archive_members':hashes['archive_member_count'],'regular_files':hashes['regular_file_count'],'prefix_snapshot_sha256':hashes['prefix_snapshot_sha256'],'elf_objects':elf['elf_count'],'native_extensions':elf['native_extension_count'],'inherited_dependency_products':sorted(q['soname'] for q in dep['dependency_products'] if q['classification']=='beeware-inherited-dependency'),'unresolved_dependencies':len(dep['unresolved_edges']),'unclassified_packaged_elf':len(dep['unclassified_packaged_elf']),'build_details_count':len(sysc['build_details'])},
      'file_identities':file_ids,
      'claim_boundary':{'official_upstream_identity':True,'no_mutation_fingerprint':True,'complete_package_topology':True,'dependency_provider_closure':True,'provenance_closure':True,'android_runtime':False,'relocation':False,'launcher':False,'device_qualification':False,'product_selection':False,'publication':False},
      'verification':{'independent_audit':f"{audit['pass_count']}/{audit['check_count']}",'focused_verifier':'required-after-finalization','negative_fixtures':'required-before-transaction'},
      'next_action_class':'execute-e2-r1-ut1-astral-artifact-and-metadata-prototype',
    }
    dump(out/'upstream-control-authority.json',authority)
    authority_sha=sha(out/'upstream-control-authority.json')
    freeze=f'''# E2-R1/UT-0 Evidence Freeze

```text
authority       experiments/epoch2-upstream-thin-control/upstream-control-authority.json
authority sha   {authority_sha}
package         {manifest['filename']}
package sha     {manifest['sha256']}
version         {manifest['version']}
target          {manifest['target']}
minimum API     {manifest['minimum_android_api']}
members         {hashes['archive_member_count']}
ELF objects     {elf['elf_count']}
extensions      {elf['native_extension_count']}
audit           {audit['pass_count']}/{audit['check_count']} PASS
```

Accepted: exact official package identity, no-mutation member fingerprint, package topology, inherited dependency provider closure, sysconfig surface, provenance map, and bounded producer delta.

Not accepted: Android runtime behavior, relocation, launcher/getpath behavior, device qualification, Epoch 3 selection, product selectability, or publication.
'''
    (out/'evidence-freeze.md').write_text(freeze,encoding='utf-8')

    catalog_path=root/'docs/agent/TASK_CATALOG.json'; catalog=load(catalog_path)
    ut1=next(t for t in catalog['tasks'] if t['task_id']=='E2-R1-UT-1')
    ut1['activation']={'prerequisites_satisfied':True,'accepted_authority_path':f'{x.output_dir}/upstream-control-authority.json','accepted_authority_sha256':authority_sha,'required_predecessor_action_class':'execute-e2-r1-ut0-exact-official-upstream-control','required_authority_role':'exact-official-upstream-control','status':'ready'}
    ut1['claim_boundary']['official_upstream_identity_claim']=True
    req={'path':f'{x.output_dir}/upstream-control-authority.json','reason':'Frozen exact official Python.org Android package, topology, dependency, and provenance authority.','sha256':authority_sha}
    if not any(q.get('path')==req['path'] for q in ut1['required_authorities']): ut1['required_authorities'].append(req)
    ut1['completion_contract']=completion_contract(ut1['action_class'],'execute-e2-r1-ut2-loader-relocation-launcher-getpath','E2-R1-UT-2')
    if not any(t.get('task_id')=='E2-R1-UT-2' for t in catalog['tasks']):
      catalog['tasks'].append({
        'action_class':'execute-e2-r1-ut2-loader-relocation-launcher-getpath',
        'activation':{'prerequisites_satisfied':False,'required_authority_role':'astral-artifact-and-metadata-prototype','required_predecessor_action_class':ut1['action_class'],'status':'blocked-on-predecessor-authority'},
        'claim_boundary':{'android_runtime_claim':False,'device_qualification_claim':False,'epoch3_selection_claim':False,'official_upstream_identity_claim':True,'product_selectability_claim':False,'publication_claim':False},
        'default_exclusions':ut1['default_exclusions'],'deliverable':ut1['deliverable'],
        'goal':'Determine whether the official binaries satisfy the standalone relocation contract without process-global loader workarounds, and select only evidenced launcher/getpath behavior.',
        'input_routing':ut1['input_routing'],'required_authorities':ut1['required_authorities'],
        'required_reads':[{'path':'docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md','reason':'Loader, relocation, launcher, getpath variants, evidence, and exit condition.','scope':'section','section_heading':'## UT-2 — Loader, relocation, launcher, and getpath','stop_before_heading':'## UT-3 — CLI semantics, supported upstream limits, and one unsupported experiment'}],
        'task_id':'E2-R1-UT-2','title':'Loader, relocation, launcher, and getpath','work_class':'L',
      })
    dump(catalog_path,catalog)
    catalog_sha=sha(catalog_path)

    protocol_revision, protocol_sha=update_transport_protocol(root)
    state_path=root/'docs/current/STATE.json'; state=load(state_path)
    state['state_revision']=state['state_revision']+1
    state['agent_onboarding']['session_protocol_revision']=protocol_revision
    state['agent_onboarding']['session_output']='agent-connector-upload-owner-rclone-download-owner-rclone-upload-agent-connector-readback'
    state['session_protocol']={'path':'docs/agent/SESSION_PROTOCOL.md','revision':protocol_revision,'sha256':protocol_sha}
    state['predecessor']={'commit':x.predecessor_head,'tree':x.predecessor_tree}
    state['accepted_authorities'].append({'id':'e2-r1-ut0-exact-official-upstream-control','path':f'{x.output_dir}/upstream-control-authority.json','role':'exact official Python.org Android package, topology, dependency, and provenance control','sha256':authority_sha})
    action=ut1['action_class']
    state['program']['gate']={'id':'E2-R1/UT-1','name':'Astral artifact and metadata prototype','status':'ready'}
    state['program']['next_action_class']=action; state['next_action_class']=action
    state['control_work']['next_action_class']=action; state['control_work']['resume_program_action_class']=action
    state['blockers']=[]; state['active_work_package']=None
    state['unresolved_risks']=['UT-1 must represent the binary-derived official upstream runtime truthfully without fabricating unavailable build, object, static-link, or relinkable surfaces']
    state['updated_by_transaction']='20260720-e2-r1-ut0-exact-official-upstream-control-v2'
    state['task_catalog']['sha256']=catalog_sha
    state['task_completion']['current_action_class']=action
    state['task_completion']['pass_successor_action_class']='execute-e2-r1-ut2-loader-relocation-launcher-getpath'
    dump(state_path,state)

    reg_path=root/'docs/documentation/document-registry.json'; reg=load(reg_path); existing={d['path'] for d in reg['documents']}
    for name in NEW_DOCS:
      p=f'{x.output_dir}/{name}'
      if p not in existing: reg['documents'].append(registry_entry(p)); existing.add(p)
    reg['basis']['next_action_class']=action
    reg['basis']['predecessor_head']=x.predecessor_head; reg['basis']['predecessor_tree']=x.predecessor_tree
    reg['basis']['tracked_document_count']=len(reg['documents'])
    reg['basis']['task_catalog_schema_version']=catalog['schema_version']
    dump(reg_path,reg)

    p=subprocess.run([sys.executable,str(root/'experiments/agent-task-completion/render-document-views.py'),'--root',str(root)],text=True)
    if p.returncode: return p.returncode
    print(json.dumps({'pass':True,'authority_sha256':authority_sha,'state_revision':state['state_revision'],'next_action_class':action,'registered_documents':len(NEW_DOCS)},indent=2,sort_keys=True))
    return 0
if __name__=='__main__': sys.exit(main())

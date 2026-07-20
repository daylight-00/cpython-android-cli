#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
from typing import Any
OUTPUT_REL='experiments/epoch2-upstream-thin-upstream-evolution'
PRIMARY=['input-identities.json','patch-update-rehearsal.json','configuration-only-delta.json','layout-and-extension-delta.json','runpath-and-sysconfig-delta.json','wheel-and-pip-delta.json','python315-preview-delta.json','security-ownership.json','ut7-gate-diagnostics.json','independent-audit.json']
SCRIPTS=['run_upstream_evolution_experiment.py','audit_upstream_evolution.py','verify_upstream_evolution.py','test_verify_upstream_evolution.py','finalize_upstream_evolution.py','run-ut7-upstream-evolution.sh']
DOCS=['README.md',*PRIMARY,'upstream-evolution-authority.json','evidence-freeze.md']
AUTH=[
 ('plan_authority','experiments/epoch2-upstream-thin-plan/plan-authority.json','62b3b07f37a90b497747562bb00a9db5a3d78b3b2cb45df8f66db22818f5eafa'),('upstream_control_authority','experiments/epoch2-upstream-thin-control/upstream-control-authority.json','6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c'),('artifact_prototype_authority','experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json','387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306'),('loader_relocation_authority','experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json','05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2'),('sysconfig_sdk_authority','experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json','6cff1984d4601a37e8b57762bb170a57e695cb64d516c1dab0023b7e809dc808'),('android_data_policy_authority','experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json','be25e52aba1d6c9d0b2e25fec2bd1d8a0a0d9eb870436f00e81f347e90d012b7'),('feature_qualification_authority','experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json','3b56a38898a3a2384cf9419fe3cd124faa8dbf367cdd5532724b3424092a62e5'),('platform_portability_authority','experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json','b21eddfee574343772d0875a7b6f26aa7b5dd494ccf0a5f1be9b8c09201276f4')]
def load(p:Path)->Any:return json.loads(p.read_text())
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=None);ap.add_argument('--expected-predecessor-head');ap.add_argument('--expected-predecessor-tree');a=ap.parse_args();root=(a.root if a.root is not None else Path.cwd()).resolve();o=root/OUTPUT_REL;checks={};details={}
 def ck(n:str,c:bool,d:Any=None):checks[n]=bool(c);details[n]=d
 for n in DOCS+SCRIPTS:ck('file:'+n,(o/n).is_file(),str(o/n))
 if not all(checks.values()):
  print(json.dumps({'pass':False,'checks':checks,'failed':[k for k,v in checks.items() if not v]},indent=2));return 1
 ev={n:load(o/n) for n in PRIMARY};authority=load(o/'upstream-evolution-authority.json');state=load(root/'docs/current/STATE.json');taskdoc=load(root/'docs/current/AGENT_TASK.json');cat=load(root/'docs/agent/TASK_CATALOG.json');reg=load(root/'docs/documentation/document-registry.json')
 audit=ev['independent-audit.json'];gate=ev['ut7-gate-diagnostics.json'];preview=ev['python315-preview-delta.json'];rehearsal=ev['patch-update-rehearsal.json'];config=ev['configuration-only-delta.json'];security=ev['security-ownership.json'];inputs=ev['input-identities.json']
 ck('audit-pass',audit.get('pass') is True,audit)
 ck('audit-count-consistent',audit.get('pass_count')==audit.get('check_count') and audit.get('check_count',0)>=70,audit)
 ck('audit-failed-empty',audit.get('failed_checks')==[],audit)
 ck('gate-pass',gate.get('pass') is True,gate)
 ck('gate-failed-empty',gate.get('failed_gate_conditions')==[],gate)
 ck('gate-all-true',all(v is True for v in gate.get('gate_condition',{}).values()) and len(gate.get('gate_condition',{}))==13,gate)
 ck('inputs-pass',inputs.get('pass') is True and inputs.get('all_sigstore_digest_bound') is True and inputs.get('all_exact_owner_inputs') is True,inputs)
 ck('inputs-owner-mode',all(x.get('acquisition_scope')=='bounded-owner-local' and x.get('exact_identity_verified') is True and x.get('acquisition_mode') in {'owner-local-cache-reuse','owner-local-bounded-download'} and isinstance(x.get('network_acquisition'),bool) for x in inputs.get('inputs',[])),inputs.get('inputs'))
 ck('inputs-exact-versions',[x.get('version') for x in inputs.get('inputs',[])]==['3.14.6','3.14.5','3.15.0b4'],inputs)
 ck('patch-pass',rehearsal.get('pass') is True,rehearsal)
 ck('patch-records-all',rehearsal.get('every_non_identity_delta_recorded') is True,rehearsal)
 ck('patch-pair',rehearsal.get('from_version')=='3.14.5' and rehearsal.get('to_version')=='3.14.6',rehearsal)
 ck('config-pass',config.get('pass') is True,config)
 ck('config-no-bypass',config.get('automation_boundary',{}).get('configuration_only_may_not_bypass_runtime_qualification') is True,config)
 ck('version-assumptions',config.get('version_specific_assumptions',{}).get('files_with_version_literals',0)>0,config)
 ck('preview-pass',preview.get('pass') is True,preview)
 ck('preview-exact',preview.get('preview_version')=='3.15.0b4' and preview.get('preview_only') is True,preview)
 ck('preview-release-false',preview.get('release_claim') is False,preview)
 ck('preview-runtime-false',preview.get('runtime_support_claim') is False,preview)
 ck('preview-product-false',preview.get('product_selection') is False,preview)
 ck('preview-pidfd-static',preview.get('pidfd_related_subprocess_behavior',{}).get('direct_runtime_qualified') is False,preview)
 ck('security-pass',security.get('pass') is True and len(security.get('ownership',[]))>=5,security)
 ck('automatic-release-false',security.get('maintenance_model',{}).get('automatic_release_on_green') is False,security)
 ck('authority-kind',authority.get('authority_kind')=='e2-r1-ut7-upstream-evolution-and-maintenance-portability',authority)
 ck('authority-status',authority.get('status')=='frozen-pass-bounded-patch-update-and-preview-delta',authority)
 ck('authority-predecessor',authority.get('predecessor')=={'commit':a.expected_predecessor_head,'tree':a.expected_predecessor_tree} if a.expected_predecessor_head and a.expected_predecessor_tree else True,authority.get('predecessor'))
 ck('authority-preview-boundary',authority.get('python315_preview',{}).get('release_claim') is False and authority.get('python315_preview',{}).get('runtime_support_claim') is False,authority)
 ck('authority-owner-input-boundary',authority.get('acquisition_boundary',{}).get('scope')=='bounded-owner-local' and authority.get('acquisition_boundary',{}).get('input_count')==3 and authority.get('acquisition_boundary',{}).get('exact_identity_required') is True,authority.get('acquisition_boundary'))
 ck('authority-no-epoch3',authority.get('epoch3_selection_made') is False,authority)
 ck('authority-next',authority.get('next_action_class')=='execute-e2-r1-api36-controlled-source-equivalent-comparison',authority)
 op=authority.get('operation_protocol',{})
 ck('authority-operation-protocol',op.get('revision')==3 and op.get('owner_local_network_acquisition_allowed') is True and op.get('assistant_network_assumed') is False and op.get('single_archive_exchange') is True and op.get('embedded_runner_required') is True,op)
 ck('authority-operation-protocol-sha',op.get('session_protocol_sha256')==sha(root/'docs/agent/SESSION_PROTOCOL.md') and op.get('bootstrap_contract_sha256')==sha(root/'docs/agent/BOOTSTRAP_CONTRACT.json'),op)
 for key,path,h in AUTH:
  ck('required-authority-file:'+key,sha(root/path)==h,{'path':path,'expected':h,'actual':sha(root/path) if (root/path).is_file() else None})
  ck('authority-binding:'+key,authority.get(key)=={'path':path,'sha256':h},authority.get(key))
 file_ids=authority.get('file_identities',{})
 ck('authority-file-id-set',set(file_ids)==set(PRIMARY+SCRIPTS),sorted(file_ids))
 for n in PRIMARY+SCRIPTS:ck('authority-file-id:'+n,file_ids.get(n)==sha(o/n),{'expected':file_ids.get(n),'actual':sha(o/n)})
 ck('state-revision',state.get('state_revision')==14,state.get('state_revision'))
 ck('state-predecessor',state.get('predecessor')==authority.get('predecessor'),state.get('predecessor'))
 ck('state-gate',state.get('program',{}).get('gate')=={'id':'E2-R1/API36-1','name':'API-36 controlled source-equivalent comparison','status':'ready'},state.get('program',{}).get('gate'))
 ck('state-next',state.get('next_action_class')=='execute-e2-r1-api36-controlled-source-equivalent-comparison',state.get('next_action_class'))
 ck('state-program-next',state.get('program',{}).get('next_action_class')==state.get('next_action_class'),state.get('program'))
 ck('state-control-next',state.get('control_work',{}).get('next_action_class')==state.get('next_action_class') and state.get('control_work',{}).get('resume_program_action_class')==state.get('next_action_class'),state.get('control_work'))
 ck('state-updated',state.get('updated_by_transaction')=='20260720-e2-r1-ut7-upstream-evolution-v4',state.get('updated_by_transaction'))
 ck('session-protocol-revision',state.get('agent_onboarding',{}).get('session_protocol_revision')==3 and state.get('session_protocol',{}).get('revision')==3,state.get('session_protocol'))
 protocol_path=root/state.get('session_protocol',{}).get('path','docs/agent/SESSION_PROTOCOL.md');protocol_text=protocol_path.read_text();contract=load(root/'docs/agent/BOOTSTRAP_CONTRACT.json')
 ck('session-protocol-sha',state.get('session_protocol',{}).get('sha256')==sha(protocol_path),state.get('session_protocol'))
 ck('owner-network-boundary','owner local environment may use bounded network acquisition' in protocol_text.lower() and 'assistant environment' in protocol_text.lower(),None)
 ck('single-archive-transport',all(x in protocol_text for x in ['one self-contained `.tar.zst` package','embedded `RUN.sh`','one complete receipt/result `.tar.zst`']),None)
 ck('contract-single-archive',contract.get('session_transport',{}).get('agent_output')=='one-self-contained-tar-zst-with-embedded-runner' and contract.get('session_transport',{}).get('owner_result')=='one-receipt-tar-zst-with-out-of-band-sha256',contract.get('session_transport'))
 accepted=[x for x in state.get('accepted_authorities',[]) if x.get('id')=='e2-r1-ut7-upstream-evolution-and-maintenance-portability'];ck('state-authority-one',len(accepted)==1,accepted)
 if accepted:ck('state-authority-sha',accepted[0].get('sha256')==sha(o/'upstream-evolution-authority.json'),accepted[0])
 task=next((x for x in cat.get('tasks',[]) if x.get('task_id')=='E2-R1-API36-1'),None);ck('catalog-successor-exists',isinstance(task,dict),task)
 if task:
  act=task.get('activation',{});ck('catalog-successor-ready',act.get('status')=='ready' and act.get('prerequisites_satisfied') is True,act)
  ck('catalog-successor-binding',act.get('accepted_authority_path')==f'{OUTPUT_REL}/upstream-evolution-authority.json' and act.get('accepted_authority_sha256')==sha(o/'upstream-evolution-authority.json'),act)
  ck('catalog-successor-contract',isinstance(task.get('completion_contract'),dict) and task['completion_contract'].get('pass',{}).get('required_output_namespace')=='experiments/epoch2-upstream-thin-api36-controlled-comparison/',task.get('completion_contract'))
  ck('catalog-authority-required',any(x.get('path')==f'{OUTPUT_REL}/upstream-evolution-authority.json' and x.get('sha256')==sha(o/'upstream-evolution-authority.json') for x in task.get('required_authorities',[])),task.get('required_authorities'))
 ck('agent-task-gate',taskdoc.get('program_gate')=={'id':'E2-R1/API36-1','name':'API-36 controlled source-equivalent comparison','status':'ready'},taskdoc.get('program_gate'))
 ck('agent-task-state-revision',taskdoc.get('state_revision')==14,taskdoc.get('state_revision'))
 ck('agent-task-action',taskdoc.get('task',{}).get('action_class')=='execute-e2-r1-api36-controlled-source-equivalent-comparison',taskdoc.get('task'))
 registry={x.get('path') for x in reg.get('documents',[])}
 for n in DOCS:ck('registry:'+n,f'{OUTPUT_REL}/{n}' in registry,f'{OUTPUT_REL}/{n}')
 exp=(root/'experiments/README.md').read_text();ck('experiments-index','epoch2-upstream-thin-upstream-evolution/' in exp,None)
 freeze=(o/'evidence-freeze.md').read_text();ck('freeze-authority-sha',sha(o/'upstream-evolution-authority.json') in freeze,None);ck('freeze-preview-false','preview release claim     false' in freeze,None)
 readme=(o/'README.md').read_text().lower();ck('readme-preview-boundary','preview-only' in readme and 'not a release claim' in readme,readme)
 failed=[k for k,v in checks.items() if not v];result={'schema_version':1,'verifier':'ut7-focused','check_count':len(checks),'pass_count':sum(checks.values()),'checks':checks,'failed_checks':failed,'details':{k:details[k] for k in failed},'pass':not failed};print(json.dumps(result,indent=2,sort_keys=True));return 0 if not failed else 1
if __name__=='__main__':raise SystemExit(main())

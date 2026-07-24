#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
B='experiments/epoch3-upstream-thin-release-blockers/'
APP=B+'rb1-successor-r3-owner-approval.json'
INS=B+'rb1-successor-r3-owner-approval-return-inspection.json'
AUD=B+'epoch3-release-blocker-closure-independent-audit.json'
AUTH=B+'rb1-successor-r3-owner-approval-authority.json'
TEMP=B+'rb1-successor-r3-owner-approval-temporal-verifier-amendment.json'
NEXT=B+'epoch3-release-candidate-integration-contract.json'
EXPECTED={APP:'113b843321fa2e6abbb3a24c7662845de80f1cb14355032f04086d6ccca86b0e',INS:'aeed14240489eae4055d5323e1323829b316be77d61ea99851f0de29694c52c0',AUD:'fadb0421be91e2d1bb6ca14cd0d0a864029ebf624d8bb72d4aae5bfa468fb079',AUTH:'6794102f1941ec1b1715dfaa1b6a7bf4935c6f7c6798d5a731846cfd9843aceb',TEMP:'2acd72ff02e974314ef3af3297ea73ca6efaba6fdd5bba1e6af7625d3cd97efd',NEXT:'f009738479a43410e47c9eb5d9b0222d464e77be67e6120e8cf6a698181af13a'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def verify(root:Path|None=None):
 root=(root or ROOT).resolve(); req=list(EXPECTED)+['docs/current/STATE.json','docs/current/AGENT_TASK.json','docs/agent/TASK_CATALOG.json','docs/documentation/document-registry.json',B+'blocker-register.json','config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-canonical-family-r1.lock.json']
 missing=[p for p in req if not (root/p).is_file()]
 if missing:return {'schema_version':1,'verifier_kind':'epoch3-rb1-successor-r3-owner-approval','pass':False,'failed_checks':['required_inputs'],'missing_inputs':missing}
 d={p:load(root/p) for p in EXPECTED}; s=load(root/'docs/current/STATE.json');t=load(root/'docs/current/AGENT_TASK.json');c=load(root/'docs/agent/TASK_CATALOG.json');r=load(root/(B+'blocker-register.json'));reg=load(root/'docs/documentation/document-registry.json');lock=load(root/'config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-canonical-family-r1.lock.json')
 a=d[APP];i=d[INS];u=d[AUD];h=d[AUTH];tm=d[TEMP];n=d[NEXT];b=s['claim_boundaries'];rb1=next(x for x in r['blockers'] if x['id']=='RB-1');task=next(x for x in c['tasks'] if x['action_class']=='integrate-epoch3-selectable-release-candidate'); registered={x['path'] for x in reg['documents']}
 checks={
  'file_identities':all(sha(root/p)==v for p,v in EXPECTED.items()),
  'approval_explicit':a['approved'] is True and a['approval_kind']=='epoch3-rb1-successor-r3-explicit-owner-approval' and a['statement']=='I approve the exact canonical successor r3 release and the exact bound notice set for the accepted support scope.',
  'approver_identity':a['approver']=={'human_name':'David Hyunyoo Jang','github_owner_id':'daylight-00','git_identity':{'name':'daylight-00','email':'hwjang00@snu.ac.kr'}},
  'repo_role':a['repository_role']['id']=='epoch3-experiment-decision-and-completion' and a['repository_role']['distribution_repository_separate'] is True and a['repository_role']['distribution_repository_created'] is False and a['repository_role']['publication_approved'] is False and a['repository_role']['selectability_approved'] is False,
  'exact_release':a['exact_binding']['release_id']=='cpython-3.14.6+e3-r3-aarch64-linux-android' and a['exact_binding']['release_file_count']==128 and a['exact_binding']['release_sha256']=='2c31578f95a11291eee1693db80048568a7b533e77877f36a8b1570241ce1e1c' and a['exact_binding']['third_party_notices_sha256']=='80cf82a6b6957fd830701e2559755d1eecdf01c61cbcb4f8f8843b9735eaf613',
  'support_scope':a['accepted_support_scope']['minimum_supported_android_api']==24 and a['accepted_support_scope']['api24_runtime_supported'] is True and a['accepted_support_scope']['api24_runtime_device_validated'] is False and a['accepted_support_scope']['app_uid_non_termux_runtime_qualified'] is True and a['accepted_support_scope']['other_non_termux_android_contexts_supported'] is False and a['accepted_support_scope']['actual_16k_runtime_supported'] is False,
  'normalization':i['status']=='accepted-explicit-owner-approval' and i['normalization']['rules'][0]['canonical_value']=='hwjang00@snu.ac.kr' and i['normalization']['rules'][0]['semantic_change'] is False,
  'audit':u['pass'] is True and all(u['checks'].values()) and u['claim_boundary']['selectable'] is False and u['claim_boundary']['publication'] is False,
  'authority':h['status']=='accepted-owner-approved-rb1-closed' and h['closure']['rb1_closed'] is True and h['closure']['all_release_blockers_closed'] is True and h['claim_boundary']['selectable'] is False and h['claim_boundary']['publication'] is False,
  'temporal':tm['status']=='frozen-verifier-only-release-blocker-closure-routing' and tm['allowed_progression']['state_revision']==60,
  'state':s['state_revision']==60 and s['blockers']==[] and s['active_work_package']==NEXT and s['next_action_class']=='integrate-epoch3-selectable-release-candidate' and b['owner_approved'] is True and b['rb1_closed'] is True and b['all_release_blockers_closed'] is True and b['selectable'] is False and b['publication_authorized'] is False and b['distribution_repository_created'] is False,
  'register':rb1['status']=='closed-explicit-owner-approved' and rb1['evidence']['owner_approval_authority_sha256']==EXPECTED[AUTH],
  'task':t['state_revision']==60 and t['task']['action_class']=='integrate-epoch3-selectable-release-candidate' and t['deliverable']['current_bounded_transition']=='epoch3-selectable-release-candidate-integration',
  'catalog':task['activation']['status']=='ready' and task['activation']['accepted_authority_sha256']==EXPECTED[AUTH],
  'next_contract':n['status']=='authorized-not-started' and n['required_predecessor']['owner_approval_authority_sha256']==EXPECTED[AUTH] and n['claim_boundary']['selectable'] is False,
  'registry':set(EXPECTED).issubset(registered),
  'canonical_lock':lock['claim_boundary']['rb1_closed'] is False and lock['claim_boundary']['selectable'] is False,
 }
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {'schema_version':1,'verifier_kind':'epoch3-rb1-successor-r3-owner-approval','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'checks':dict(sorted(checks.items())),'failed_checks':failed}
def main():
 x=verify();print(json.dumps(x,indent=2,sort_keys=True));return 0 if x['pass'] else 1
if __name__=='__main__':raise SystemExit(main())

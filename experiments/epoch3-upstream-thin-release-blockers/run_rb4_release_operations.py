#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/epoch3-upstream-thin-release-blockers'
OUT=BASE/'rb4-release-operations-authority-evidence'

def load(rel:str)->Any:return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def dump(path:Path,obj:Any)->None:path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def snapshot(c:dict[str,Any])->str:
 return hashlib.sha256((json.dumps(c,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
def register(c:dict[str,Any],kind:str,item:dict[str,Any])->tuple[bool,str]:
 entries=c.setdefault('entries',{}).setdefault(kind,{})
 rid=item['release_id']
 if rid in entries:
  if entries[rid]==item:return True,'idempotent-exact'
  return False,'ambiguous-identity-replacement-denied'
 entries[rid]=copy.deepcopy(item);return True,'registered'
def activate(c:dict[str,Any],kind:str,rid:str)->tuple[bool,str]:
 item=c['entries'][kind].get(rid)
 if item is None:return False,'unregistered-identity'
 if item.get('revoked') is True:return False,'revoked-identity-selection-denied'
 c['active'][kind]=rid;return True,'activated'
def revoke(c:dict[str,Any],kind:str,rid:str,reason:str,sequence:int)->tuple[bool,str]:
 item=c['entries'][kind].get(rid)
 if item is None:return False,'unregistered-identity'
 if item.get('revoked') is True:
  return (item.get('revocation',{}).get('reason')==reason,'already-revoked-same-reason' if item.get('revocation',{}).get('reason')==reason else 'revocation-rewrite-denied')
 item['revoked']=True;item['revocation']={'reason':reason,'sequence':sequence};return True,'revoked'
def main()->int:
 contract=load('experiments/epoch3-upstream-thin-release-blockers/rb4-release-operations-contract.json')
 fixture=load('experiments/epoch3-upstream-thin-release-blockers/rb4-release-operations-fixture.json')
 patch=load('experiments/epoch2-upstream-thin-upstream-evolution/patch-update-rehearsal.json')
 security=load('experiments/epoch2-upstream-thin-upstream-evolution/security-ownership.json')
 canonical=load('config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-canonical-family-r1.lock.json')
 data_auth=load('experiments/epoch3-upstream-thin-release-blockers/rb2-data-product-authority.json')
 supersession=load('experiments/epoch3-upstream-thin-release-blockers/rb3-successor-predecessor-supersession-m-authority.json')
 full_auth=load('experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-authority.json')
 install_auth=load('experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-authority.json')
 stripped_auth=load('experiments/epoch3-upstream-thin-release-blockers/rb3-successor-stripped-m-authority.json')
 technical_auth=load('experiments/epoch3-upstream-thin-release-blockers/rb3-successor-technical-family-m-authority.json')
 legal_auth=load('experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-family-m-authority.json')
 rebinding_auth=load('experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-data-rebinding-m-authority.json')
 OUT.mkdir(parents=True,exist_ok=True)
 official={x['version']:x for x in patch['official_inputs']}
 ffrom=fixture['official_patch_inputs']['from'];fto=fixture['official_patch_inputs']['to']
 patch_checks={
  'authority_patch_rehearsal_pass':patch.get('pass') is True,
  'from_version':patch.get('from_version')=='3.14.5',
  'to_version':patch.get('to_version')=='3.14.6',
  'from_identity':all(official['3.14.5'].get(k)==ffrom.get(k if k!='size_bytes' else 'size') for k in ('filename','sha256','sigstore_sha256','version','size_bytes')),
  'to_identity':all(official['3.14.6'].get(k)==fto.get(k if k!='size_bytes' else 'size') for k in ('filename','sha256','sigstore_sha256','version','size_bytes')),
  'non_configuration_delta_reviewed':patch.get('configuration_only_candidate') is False and patch.get('every_non_identity_delta_recorded') is True,
  'qualification_replay_required':set(patch.get('qualification_replay_required',[]))=={'loader and native closure','relocation','sysconfig and native SDK','Android data and state policy','feature qualification','platform portability'},
  'canonical_binds_to_official_3146':canonical['canonical_family']['release_id']==fixture['python_families']['canonical']['release_id'] and canonical['canonical_family']['release_sha256']==fixture['python_families']['canonical']['release_sha256'],
  'epoch3_full_replay_complete':full_auth.get('claim_boundary',{}).get('successor_full_accepted') is True,
  'epoch3_install_only_replay_complete':install_auth.get('claim_boundary',{}).get('successor_install_only_accepted') is True,
  'epoch3_stripped_replay_complete':stripped_auth.get('claim_boundary',{}).get('successor_stripped_accepted') is True,
  'epoch3_technical_family_replay_complete':technical_auth.get('claim_boundary',{}).get('successor_technical_family_accepted') is True,
  'epoch3_legal_family_replay_complete':legal_auth.get('claim_boundary',{}).get('successor_legal_family_accepted') is True,
  'epoch3_data_rebinding_replay_complete':rebinding_auth.get('claim_boundary',{}).get('successor_legal_data_rebinding_accepted') is True,
  'epoch3_canonical_closure_complete':supersession.get('claim_boundary',{}).get('rb3_closed') is True and supersession.get('claim_boundary',{}).get('successor_family_canonical') is True,
 }
 patch_binding={'schema_version':1,'receipt_kind':'epoch3-rb4-official-patch-update-binding','from':ffrom,'to':fto,'checks':patch_checks,'pass':all(patch_checks.values()),'non_claims':['no Epoch 3 3.14.5 release family was produced','patch delta evidence does not substitute for target runtime qualification','no automatic release-on-green claim']}
 dump(OUT/'patch-update-binding.json',patch_binding)
 catalog={'schema_version':1,'catalog_kind':'epoch3-rb4-production-baseline','revision':1,'entries':{'python_families':{},'data_products':{},'official_inputs':{}},'active':{},'policies':contract['catalog_rules']}
 transitions=[]
 for role in ('rollback','canonical'):
  ok,msg=register(catalog,'python_families',dict(fixture['python_families'][role],revoked=False));transitions.append({'operation':'register-python-family','role':role,'ok':ok,'result':msg})
 for role in ('rollback','current'):
  ok,msg=register(catalog,'data_products',dict(fixture['data_products'][role],revoked=False));transitions.append({'operation':'register-data-product','role':role,'ok':ok,'result':msg})
 for role in ('from','to'):
  item=copy.deepcopy(fixture['official_patch_inputs'][role]);item['release_id']='pythonorg-android-'+item['version'];item['support_status']='historical-input' if role=='from' else 'current-upstream-input';item['revoked']=False
  ok,msg=register(catalog,'official_inputs',item);transitions.append({'operation':'register-official-input','role':role,'ok':ok,'result':msg})
 for kind,rid in [('python_families',fixture['python_families']['canonical']['release_id']),('data_products',fixture['data_products']['current']['release_id'])]:
  ok,msg=activate(catalog,kind,rid);transitions.append({'operation':'activate-production-baseline','kind':kind,'release_id':rid,'ok':ok,'result':msg})
 baseline_sha=snapshot(catalog)
 # exact idempotency and ambiguous replacement denial
 exact=copy.deepcopy(fixture['python_families']['canonical']);exact['revoked']=False
 idem_ok,idem_msg=register(catalog,'python_families',exact)
 bad=copy.deepcopy(exact);bad['release_sha256']='0'*64
 bad_ok,bad_msg=register(catalog,'python_families',bad)
 catalog_checks={
  'all_registrations_and_activation_pass':all(t['ok'] for t in transitions),
  'active_python_is_canonical':catalog['active']['python_families']==fixture['python_families']['canonical']['release_id'],
  'active_data_is_current':catalog['active']['data_products']==fixture['data_products']['current']['release_id'],
  'exact_reregistration_idempotent':idem_ok and idem_msg=='idempotent-exact',
  'ambiguous_replacement_denied':not bad_ok and bad_msg=='ambiguous-identity-replacement-denied',
  'all_prior_entries_retained':len(catalog['entries']['python_families'])==2 and len(catalog['entries']['data_products'])==2 and len(catalog['entries']['official_inputs'])==2,
 }
 catalog_receipt={'schema_version':1,'receipt_kind':'epoch3-rb4-production-catalog-baseline','catalog':catalog,'catalog_sha256':baseline_sha,'transitions':transitions,'checks':catalog_checks,'pass':all(catalog_checks.values())}
 dump(OUT/'catalog-transition-receipt.json',catalog_receipt)
 # rollback drill, production catalog unchanged
 drill=copy.deepcopy(catalog);before=snapshot(drill);events=[]
 seq=[('python_families',fixture['python_families']['rollback']['release_id'],'family-rollback'),('python_families',fixture['python_families']['canonical']['release_id'],'family-restore'),('data_products',fixture['data_products']['rollback']['release_id'],'data-rollback'),('data_products',fixture['data_products']['current']['release_id'],'data-restore')]
 for kind,rid,label in seq:
  prior=drill['active'][kind];ok,msg=activate(drill,kind,rid);events.append({'operation':label,'kind':kind,'from':prior,'to':rid,'ok':ok,'result':msg,'catalog_sha256':snapshot(drill)})
 rollback_checks={
  'all_operations_pass':all(e['ok'] for e in events),
  'family_rollback_exact':events[0]['to']==fixture['python_families']['rollback']['release_id'],
  'family_restored':drill['active']['python_families']==fixture['python_families']['canonical']['release_id'],
  'data_rollback_exact':events[2]['to']==fixture['data_products']['rollback']['release_id'],
  'data_restored':drill['active']['data_products']==fixture['data_products']['current']['release_id'],
  'retained_entry_counts_unchanged':{k:len(v) for k,v in drill['entries'].items()}=={k:len(v) for k,v in catalog['entries'].items()},
  'production_baseline_unchanged':snapshot(catalog)==baseline_sha,
  'drill_restored_to_baseline':snapshot(drill)==before,
 }
 rollback={'schema_version':1,'receipt_kind':'epoch3-rb4-release-and-data-rollback-drill','before_catalog_sha256':before,'events':events,'after_catalog_sha256':snapshot(drill),'checks':rollback_checks,'pass':all(rollback_checks.values())}
 dump(OUT/'rollback-receipt.json',rollback)
 # emergency revocation drill in isolated lineage
 rev=copy.deepcopy(catalog);before_rev=snapshot(rev);target=fixture['python_families']['canonical']['release_id'];fallback=fixture['python_families']['rollback']['release_id']
 rv_ok,rv_msg=revoke(rev,'python_families',target,'emergency-drill-security-revocation',1)
 sel_ok,sel_msg=activate(rev,'python_families',target)
 fb_ok,fb_msg=activate(rev,'python_families',fallback)
 rewrite_ok,rewrite_msg=revoke(rev,'python_families',target,'different-reason-forbidden',2)
 readback=rev['entries']['python_families'][target]
 rev_checks={
  'revocation_applied':rv_ok and rv_msg=='revoked',
  'revoked_selection_denied':not sel_ok and sel_msg=='revoked-identity-selection-denied',
  'fallback_activation_pass':fb_ok and fb_msg=='activated' and rev['active']['python_families']==fallback,
  'revocation_readback_exact':readback.get('revoked') is True and readback.get('revocation')=={'reason':'emergency-drill-security-revocation','sequence':1},
  'revocation_rewrite_denied':not rewrite_ok and rewrite_msg=='revocation-rewrite-denied',
  'revoked_bytes_retained':readback.get('release_sha256')==fixture['python_families']['canonical']['release_sha256'],
  'production_baseline_unchanged':snapshot(catalog)==baseline_sha,
 }
 revocation={'schema_version':1,'receipt_kind':'epoch3-rb4-emergency-revocation-readback-drill','drill_only':True,'production_revocation_applied':False,'before_catalog_sha256':before_rev,'target_release_id':target,'revocation_result':rv_msg,'selection_result':sel_msg,'fallback_result':fb_msg,'rewrite_result':rewrite_msg,'readback':readback,'after_catalog_sha256':snapshot(rev),'checks':rev_checks,'pass':all(rev_checks.values())}
 dump(OUT/'revocation-readback.json',revocation)
 # security ownership expansion
 ownership=copy.deepcopy(security['ownership'])
 ownership.extend([
  {'surface':'versioned CA and timezone provider bytes','owner':'certifi and IANA/tzdata upstream providers','local_obligation':'pin exact provider identities, preserve licenses, and qualify current and rollback products'},
  {'surface':'data product assembly, activation, rollback and corruption handling','owner':'local cpython-android-cli maintainers','local_obligation':'keep data outside the immutable Python tree and preserve atomic verified activation'},
  {'surface':'release catalog support status, emergency revocation and publication decision','owner':'local release operators with independent reviewer','local_obligation':'record exact immutable identities, require explicit reasoned revocation, deny revoked selection, and never infer publication from green tests'},
 ] )
 sec={'schema_version':1,'receipt_kind':'epoch3-rb4-security-ownership-and-support-policy','ownership':ownership,'support_policy':{
  fixture['python_families']['canonical']['release_id']:'supported-canonical-not-yet-selectable-or-published',
  fixture['python_families']['rollback']['release_id']:'immutable-historical-valid-rollback-only',
  fixture['data_products']['current']['release_id']:'supported-current-data',
  fixture['data_products']['rollback']['release_id']:'immutable-historical-valid-data-rollback',
  'pythonorg-android-3.14.5':'historical-upstream-patch-predecessor-input',
  'pythonorg-android-3.14.6':'current-frozen-upstream-input'
 },'maintenance_model':security['maintenance_model'],'checks':{'source_security_policy_pass':security.get('pass') is True,'minimum_two_roles':set(security['maintenance_model']['minimum_roles'])=={'implementation maintainer','independent reviewer'},'automatic_release_forbidden':security['maintenance_model']['automatic_release_on_green'] is False,'all_operational_surfaces_assigned':len(ownership)>=8},'pass':True}
 sec['pass']=all(sec['checks'].values());dump(OUT/'security-ownership.json',sec)
 result={'schema_version':1,'result_kind':'epoch3-rb4-release-operations-local-qualification','pass':all([patch_binding['pass'],catalog_receipt['pass'],rollback['pass'],revocation['pass'],sec['pass']]),'evidence':{'patch_update_binding':'patch-update-binding.json','catalog_transition':'catalog-transition-receipt.json','rollback':'rollback-receipt.json','revocation':'revocation-readback.json','security_ownership':'security-ownership.json'},'claim_boundary':contract['claim_boundary'],'production_catalog_sha256':baseline_sha}
 dump(OUT/'result.json',result)
 return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())

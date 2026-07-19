#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
B=Path('AGENT_BOOTSTRAP.md');C=Path('docs/agent/BOOTSTRAP_CONTRACT.json');S=Path('docs/current/STATE.json');T=Path('docs/current/AGENT_TASK.json');K=Path('docs/agent/TASK_CATALOG.json');R=Path('docs/documentation/document-registry.json');M=Path('docs/history/pre-agent-bootstrap-session-system/snapshot-map.json')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--render-result');x=ap.parse_args();r=Path(x.root).resolve();checks={};errors={}
 def ck(n,v,e=''):checks[n]=bool(v);errors.update({n:e} if not v and e else {})
 try:c=load(r/C);s=load(r/S);t=load(r/T);k=load(r/K);reg=load(r/R);sm=load(r/M);boot=(r/B).read_text();protocol=(r/'docs/agent/SESSION_PROTOCOL.md').read_text();model=(r/'docs/agent/PROJECT_MODEL.md').read_text();ck('parse',True)
 except Exception as e:c={};s={};t={};k={};reg={};sm={};boot=protocol=model='';ck('parse',False,str(e))
 ck('contract_identity',c.get('contract_kind')=='immutable-agent-bootstrap-contract' and c.get('schema_version')==1)
 ck('bootstrap_digest',c.get('bootstrap',{}).get('sha256')==sha(r/B))
 ck('bootstrap_immutable',c.get('bootstrap',{}).get('mutability')=='immutable-in-place')
 mandatory=['docs/agent/PROJECT_MODEL.md','docs/agent/SESSION_PROTOCOL.md','docs/current/STATE.json','docs/current/AGENT_TASK.json'];ck('mandatory_order',c.get('mandatory_read_order')==mandatory)
 ck('mandatory_files',all((r/p).is_file() for p in mandatory))
 ck('bootstrap_links',all(p in boot for p in mandatory))
 ck('bootstrap_no_temporal_identity',not re.search(r'\b[0-9a-f]{40}\b|\b[0-9a-f]{64}\b|\b20\d\d-\d\d-\d\d\b|\bE\d(?:-|\b)',boot))
 ck('bootstrap_guardrails',all(x in boot for x in ['Google Drive connector','GitHub connector','curl','wget','onboarding certificate']))
 project_ids=[f'PM-{i:02d}' for i in range(1,9)];session_ids=[f'SP-{i:02d}' for i in range(1,21)]
 ck('project_rule_ids',c.get('required_project_rule_ids')==project_ids and all(x in model for x in project_ids))
 ck('session_rule_ids',c.get('required_session_rule_ids')==session_ids and all(x in protocol for x in session_ids))
 ck('protocol_drive_first','Google Drive connector as the first attempt' in protocol)
 ck('protocol_github_forbidden',all(x in protocol for x in ['Do not use the GitHub connector','GitHub API','network Git']))
 ck('protocol_dns_boundary',all(x in protocol for x in ['curl','wget','Do not assume DNS']))
 ck('protocol_bundle_loop',all(x in protocol for x in ['full Git bundle','one .tar.zst package','one complete receipt/result']))
 ck('protocol_one_runner','one command' in protocol and 'one-runner' in protocol)
 ck('protocol_no_handoff','Ordinary mandatory handoff packages are retired' in protocol)
 ao=s.get('agent_onboarding',{});ck('state_bootstrap_paths',ao.get('bootstrap_path')=='AGENT_BOOTSTRAP.md' and ao.get('project_model_path')==mandatory[0] and ao.get('session_protocol_path')==mandatory[1] and ao.get('task_manifest_path')==mandatory[3])
 ck('state_bootstrap_digest',ao.get('bootstrap_sha256')==sha(r/B))
 ck('state_task_alignment',s.get('state_revision')==t.get('state_revision') and s.get('next_action_class')==t.get('task',{}).get('action_class'))
 ck('state_gate_alignment',s.get('program',{}).get('gate')==t.get('program_gate'))
 matches=[z for z in k.get('tasks',[]) if z.get('action_class')==s.get('next_action_class')];ck('catalog_resolution',len(matches)==1 and matches[0].get('task_id')==t.get('task',{}).get('id'))
 sections=True
 for q in t.get('required_reads',[]):
  p=r/q.get('path','')
  if not p.is_file():sections=False;break
  text=p.read_text(encoding='utf-8');a=q.get('section_heading');b=q.get('stop_before_heading')
  if q.get('scope')=='section' and (text.count(a)!=1 or text.count(b)!=1 or text.index(a)>=text.index(b)):sections=False;break
 ck('task_section_boundaries',sections)
 auth=True
 for q in t.get('required_authorities',[]):
  p=r/q.get('path','')
  if not p.is_file() or sha(p)!=q.get('sha256'):auth=False;break
 ck('task_authorities',auth)
 excluded=set(t.get('default_exclusions',[]));ck('default_exclusions',{'docs/history/**','docs/handoff/**','docs/stages/**','unrelated-evidence','unrelated-experiments','roadmap-outside-selected-section'}.issubset(excluded))
 forbidden=('docs/history/','docs/handoff/','docs/stages/')
 ck('task_reads_not_historical',all(not q.get('path','').startswith(forbidden) for q in t.get('required_reads',[])))
 redirects=c.get('compatibility_redirects',[]);ck('redirects_exist',all((r/p).is_file() for p in redirects))
 ck('redirects_are_bounded',all(len((r/p).read_text(encoding='utf-8').splitlines())<=14 and 'compatibility redirect' in (r/p).read_text(encoding='utf-8').lower() for p in redirects))
 ck('snapshot_map',sm.get('entry_count')==13 and all((r/e['snapshot_path']).is_file() and sha(r/e['snapshot_path'])==e['sha256'] for e in sm.get('entries',[])))
 docs=reg.get('documents',[]);paths=[d.get('path') for d in docs];tracked=subprocess.check_output(['git','-C',str(r),'ls-files','--','*.md','*.json'],text=True).splitlines();ck('registry_coverage',sorted(paths)==sorted(tracked) and len(paths)==len(set(paths)))
 by={d.get('path'):d for d in docs};ck('registry_bootstrap_class',by.get('AGENT_BOOTSTRAP.md',{}).get('lifecycle_class')=='FROZEN_AUTHORITY' and by.get('AGENT_BOOTSTRAP.md',{}).get('mutability')=='immutable')
 ck('registry_task_class',by.get('docs/current/AGENT_TASK.json',{}).get('lifecycle_class')=='GENERATED_VIEW')
 ck('registry_protocol_primary',by.get('docs/agent/SESSION_PROTOCOL.md',{}).get('onboarding_visibility')=='primary')
 ck('navigation_agent_index','docs/agent/README.md' in s.get('render_targets',{}).get('navigation',[]))
 ck('export_runner',(r/'tools/export-agent-session-bundle.sh').is_file())
 ck('onboard_tool',(r/'tools/agent_onboard.py').is_file())
 if x.render_result:
  try:z=load(Path(x.render_result));ck('render_result',z.get('pass') is True and z.get('target_count')==20 and z.get('mismatched_targets')==[])
  except Exception as e:ck('render_result',False,str(e))
 else:
  p=subprocess.run([sys.executable,str(r/'experiments/agent-bootstrap/render-document-views.py'),'--root',str(r),'--check'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);ck('render_result',p.returncode==0,p.stderr or p.stdout)
 failed=[k for k,v in checks.items() if not v];out={'schema_version':1,'verifier_kind':'immutable-agent-bootstrap-and-session-protocol','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())

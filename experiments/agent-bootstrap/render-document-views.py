#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
from collections import Counter,defaultdict
STATE=Path('docs/current/STATE.json');REG=Path('docs/documentation/document-registry.json');TARGETS=Path('experiments/agent-bootstrap/navigation-targets.json');CATALOG=Path('docs/agent/TASK_CATALOG.json')
BEGIN='<!-- BEGIN GENERATED CURRENT STATE -->';END='<!-- END GENERATED CURRENT STATE -->'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def rel(src,dst):return os.path.relpath(dst,start=str(Path(src).parent)).replace(os.sep,'/')
def link(src,dst):return f'[`{dst}`]({rel(src,dst)})'
def replace(text,block):
 if text.count(BEGIN)!=1 or text.count(END)!=1:raise ValueError('generated markers missing or non-unique')
 return text.split(BEGIN,1)[0].rstrip()+'\n\n'+BEGIN+'\n'+block.rstrip()+'\n'+END+'\n\n'+text.split(END,1)[1].lstrip('\n')
def entry(src,d):
 suffix=''
 if d['lifecycle_class']=='HISTORICAL_SNAPSHOT':suffix=' · snapshot-relative; never current authority'
 return f"- {link(src,d['path'])} — `{d['lifecycle_class']}` · `{d['authority_domain']}` · owner `{d['owner']}`{suffix}"
def assignment(d,targets):
 p=d['path']
 if p in targets:return 'docs/navigation/README.md'
 pairs=[('docs/agent/','docs/agent/README.md'),('docs/current/','docs/current/README.md'),('docs/documentation/','docs/documentation/README.md'),('docs/decisions/','docs/decisions/README.md'),('docs/epochs/','docs/epochs/README.md'),('docs/architecture/','docs/architecture/README.md'),('docs/roadmap/','docs/roadmap/README.md'),('docs/contracts/','docs/contracts/README.md'),('docs/evidence/','docs/evidence/README.md'),('docs/stages/','docs/stages/README.md'),('docs/handoff/','docs/handoff/README.md'),('docs/history/','docs/history/README.md'),('docs/references/','docs/references/README.md'),('experiments/','experiments/README.md')]
 for pre,t in pairs:
  if p.startswith(pre):return t
 return 'docs/navigation/README.md'
def task_manifest(state,catalog):
 matches=[x for x in catalog['tasks'] if x['action_class']==state['next_action_class']]
 if len(matches)!=1:raise ValueError('current action must resolve to exactly one task catalog entry')
 x=matches[0]
 return {'schema_version':1,'manifest_kind':'generated-current-agent-task','generated_from':{'state':'docs/current/STATE.json','task_catalog':'docs/agent/TASK_CATALOG.json'},'state_revision':state['state_revision'],'program_gate':state['program']['gate'],'task':{'id':x['task_id'],'action_class':x['action_class'],'work_class':x['work_class'],'title':x['title'],'goal':x['goal']},'required_reads':x['required_reads'],'required_authorities':x['required_authorities'],'input_routing':x['input_routing'],'default_exclusions':x['default_exclusions'],'claim_boundary':x['claim_boundary'],'deliverable':x['deliverable'],'onboarding_certificate_required':True}
def current_block(s,src):
 a=s['agent_onboarding'];p=s['program'];claims=s['claim_boundaries'];auth='\n'.join(f"- {link(src,x['path'])}: {x['role']} (`{x['sha256']}`)" for x in s['accepted_authorities']);risks='\n'.join('- '+x for x in s['unresolved_risks']) or 'none';blockers='none' if not s['blockers'] else '\n'.join('- '+x for x in s['blockers'])
 return f'''## Current project coordinates

> Generated from {link(src,'docs/current/STATE.json')}. Do not hand-edit this block.

```text
agent bootstrap       established — {a['bootstrap_path']}
session transport     full Git bundle -> one runner -> complete receipt
immediate action      {s['next_action_class']}
program epoch         {p['epoch']['id']} — {p['epoch']['name']}
program gate          {p['gate']['id']} — {p['gate']['name']}
```

### Current claim boundary

```text
dual-device claim     accepted — AArch64 Termux compatibility
emulator qualified    {str(claims['emulator_qualified']).lower()}
selectable            {str(claims['selectable']).lower()}
publication           {str(claims['publication_authorized']).lower()}
Epoch 3 selection     {str(claims['epoch3_feature_selection_started']).lower()}
```

### Active blockers

{blockers}

### Unresolved risks

{risks}

### Accepted authorities

{auth}

### Agent entry

- {link(src,'AGENT_BOOTSTRAP.md')}
- {link(src,'docs/current/AGENT_TASK.json')}
- {link(src,'docs/agent/PROJECT_MODEL.md')}
- {link(src,'docs/agent/SESSION_PROTOCOL.md')}
'''
def render_current(s):
 src='docs/CURRENT_CONTEXT.md';p=s['program'];a=s['agent_onboarding'];risks='\n'.join('- '+x for x in s['unresolved_risks']) or 'None.';auth='\n'.join(f"{i}. {link(src,x['path'])} — {x['role']}" for i,x in enumerate(s['accepted_authorities'],1))
 return f'''# Current Project Context

> **Generated view:** {link(src,'docs/current/STATE.json')} is the sole temporal authority.
> **State revision:** {s['state_revision']}
> **Agent sessions:** start at {link(src,'AGENT_BOOTSTRAP.md')}.
> **Do not hand-edit.**

## Current agent route

```text
bootstrap       {a['bootstrap_path']}
task manifest   {a['task_manifest_path']}
action          {s['next_action_class']}
work gate       {p['gate']['id']} — {p['gate']['name']}
```

## Mandatory project and session modules

- {link(src,a['project_model_path'])}
- {link(src,a['session_protocol_path'])}
- {link(src,'docs/current/STATE.json')}
- {link(src,a['task_manifest_path'])}

## Program position

```text
epoch   {p['epoch']['id']} — {p['epoch']['name']}
gate    {p['gate']['id']} — {p['gate']['name']}
status  {p['gate']['status']}
```

## Accepted authorities

{auth}

## Blockers

{'None.' if not s['blockers'] else chr(10).join('- '+x for x in s['blockers'])}

## Unresolved risks

{risks}

History, handoffs, stages, unrelated evidence, unrelated experiments, and unselected roadmap sections are excluded from onboarding unless the generated task manifest requires them.
'''
def generic(src,title,desc,items,reverse=False):
 items=sorted(items,key=lambda d:d['path'],reverse=reverse);counts=Counter(d['lifecycle_class'] for d in items);body='\n'.join(entry(src,d) for d in items) or '- None.'
 return f'''# {title}

> **Generated view:** document registry v6. Do not hand-edit.
> {desc}

```text
entry count  {len(items)}
lifecycle    {', '.join(f'`{k}` {v}' for k,v in sorted(counts.items())) or 'none'}
```

{body}
'''
def render_index(s,r):
 src='docs/INDEX.md';return f'''# Repository Index

> **Generated view:** {link(src,'docs/documentation/document-registry.json')} + {link(src,'docs/current/STATE.json')}.
> **Agent onboarding:** {link(src,'AGENT_BOOTSTRAP.md')}.

## Current task

- {link(src,'docs/current/AGENT_TASK.json')}
- action class: `{s['next_action_class']}`
- gate: `{s['program']['gate']['id']}` — {s['program']['gate']['name']}

## Mandatory agent modules

- {link(src,'docs/agent/PROJECT_MODEL.md')}
- {link(src,'docs/agent/SESSION_PROTOCOL.md')}

## Human and lookup views

- {link(src,'docs/CURRENT_CONTEXT.md')}
- {link(src,'docs/navigation/README.md')}
- tracked Markdown/JSON: `{len(r['documents'])}`

Historical and exhaustive indexes are lookup-only during ordinary onboarding.
'''
def navigation(s,r,m):
 docs=r['documents'];targets={x['path'] for x in m['targets']};by=defaultdict(list)
 for d in docs:by[assignment(d,targets)].append(d)
 out={};root='docs/navigation/README.md';counts=Counter(d['lifecycle_class'] for d in docs);links='\n'.join(f"- {link(root,t['path'])} — {t['role']}" for t in m['targets'] if t['path']!=root);extras='\n'.join(entry(root,d) for d in sorted(by[root],key=lambda x:x['path']) if d['path'] not in targets)
 out[root]=f'''# Documentation Navigation

> **Generated lookup root:** registry v6 + {link(root,'docs/current/STATE.json')}.
> Agent sessions do not start here. Start at {link(root,'AGENT_BOOTSTRAP.md')}.

## Current coordinates

```text
action       {s['next_action_class']}
gate         {s['program']['gate']['id']} — {s['program']['gate']['name']}
tracked docs {len(docs)}
indexes      {len(targets)}
```

## Generated indexes

{links}

## Other canonical roots

{extras or '- None.'}

## Interpretation

Current state and the generated task manifest control onboarding. Stable modules control rules. Frozen authority controls accepted claims. History remains snapshot-relative.
'''
 titles={'docs/agent/README.md':('Agent Bootstrap System','Mandatory stable agent modules, immutable contract, and task catalog.'),'docs/current/README.md':('Current State','Sole temporal source, generated agent task, and versioned schemas.'),'docs/decisions/README.md':('Architecture Decisions','Stable decision records.'),'docs/epochs/README.md':('Epoch Charters and History','Epoch-level governance and history.'),'docs/architecture/README.md':('Architecture','Stable architecture and ownership documents.'),'docs/contracts/README.md':('Contracts','Frozen claim and experiment contracts.'),'docs/evidence/README.md':('Evidence','Frozen evidence records; ordering implies no precedence.'),'docs/stages/README.md':('Stage Snapshots','Historical stage scope and completion snapshots.'),'docs/handoff/README.md':('Historical Session Handoffs','Retired ordinary handoffs and historical exceptions.'),'docs/references/README.md':('References','Interpreted references and byte-preserved raw captures.'),'docs/history/README.md':('History','Snapshot-relative project, session, stage, and compatibility records.')}
 for t,(title,desc) in titles.items():out[t]=generic(t,title,desc,[d for d in by[t] if d['path']!=t],t=='docs/handoff/README.md')
 t='docs/documentation/README.md';items=[d for d in by[t] if d['path']!=t];out[t]=generic(t,'Documentation Governance','Stable rules, schemas, completed migration authorities, and bootstrap architecture.',items)
 t='docs/roadmap/README.md';items=[d for d in by[t] if d['path']!=t];active=[d for d in items if d['lifecycle_class']=='ACTIVE_PLAN'];hist=[d for d in items if d['lifecycle_class']=='HISTORICAL_SNAPSHOT'];other=[d for d in items if d not in active+hist];out[t]='# Plans and Roadmaps\n\n> **Generated view:** registry v6. Current progress belongs to STATE.json.\n\n## Canonical active plans\n\n'+('\n'.join(entry(t,d) for d in sorted(active,key=lambda x:x['path'])) or '- None.')+'\n\n## Historical plan snapshots\n\n'+('\n'.join(entry(t,d) for d in sorted(hist,key=lambda x:x['path'])) or '- None.')+'\n\n## Other records\n\n'+('\n'.join(entry(t,d) for d in sorted(other,key=lambda x:x['path'])) or '- None.')+'\n'
 t='experiments/README.md';items=[d for d in by[t] if d['path']!=t];groups=defaultdict(list)
 for d in items:groups[d['path'].split('/')[1]].append(d)
 out[t]=('# Experiments\n\n> **Generated view:** registry v6. Do not hand-edit.\n> Experiments are excluded from onboarding unless AGENT_TASK selects them.\n\n'+''.join(f"## `{g}`\n\n"+'\n'.join(entry(t,d) for d in sorted(ds,key=lambda x:x['path']))+'\n\n' for g,ds in sorted(groups.items()))).rstrip()+'\n'
 return out
def expected(root):
 s=load(root/STATE);r=load(root/REG);m=load(root/TARGETS);c=load(root/CATALOG);task=task_manifest(s,c);out={}
 out['docs/current/AGENT_TASK.json']=json.dumps(task,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
 out['README.md']=replace((root/'README.md').read_text(encoding='utf-8'),current_block(s,'README.md'))
 out['docs/CURRENT_CONTEXT.md']=render_current(s)
 out['docs/INDEX.md']=render_index(s,r)
 out.update(navigation(s,r,m));return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--check',action='store_true');x=ap.parse_args();root=Path(x.root).resolve();out=expected(root);bad=[]
 for p,b in out.items():
  q=root/p
  if x.check:
   if not q.is_file() or q.read_text(encoding='utf-8')!=b:bad.append(p)
  else:q.parent.mkdir(parents=True,exist_ok=True);q.write_text(b,encoding='utf-8')
 result={'pass':not bad,'current_target_count':4,'navigation_target_count':16,'target_count':20,'mismatched_targets':bad};print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['pass'] else 1
if __name__=='__main__':sys.exit(main())

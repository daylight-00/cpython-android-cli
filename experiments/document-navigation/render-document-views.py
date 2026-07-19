#!/usr/bin/env python3
# Render current views and complete registry-derived navigation for Phase 3.
from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
from collections import Counter,defaultdict
from typing import Any
STATE=Path("docs/current/STATE.json"); REGISTRY=Path("docs/documentation/document-registry.json"); TARGETS=Path("experiments/document-navigation/navigation-targets.json")
BEGIN="<!-- BEGIN GENERATED CURRENT STATE -->"; END="<!-- END GENERATED CURRENT STATE -->"

def load(p:Path)->Any:return json.loads(p.read_text(encoding="utf-8"))
def rel(src:str,dst:str)->str:return os.path.relpath(dst,start=str(Path(src).parent)).replace(os.sep,"/")
def mdlink(src:str,dst:str)->str:return f"[`{dst}`]({rel(src,dst)})"
def replace_block(text:str,block:str)->str:
 if text.count(BEGIN)!=1 or text.count(END)!=1 or text.index(BEGIN)>text.index(END):raise ValueError("generated markers missing or non-unique")
 return text.split(BEGIN,1)[0].rstrip()+"\n\n"+BEGIN+"\n"+block.rstrip()+"\n"+END+"\n\n"+text.split(END,1)[1].lstrip("\n")
def state_block(state:dict[str,Any],src:str)->str:
 p=state["program"];c=state["control_work"];claims=state["claim_boundaries"]
 auth="\n".join(f"- {mdlink(src,a['path'])}: {a['role']} (`{a['sha256']}`)" for a in state["accepted_authorities"])
 risks="\n".join(f"- {x}" for x in state["unresolved_risks"])
 blockers="none" if not state["blockers"] else "\n".join(f"- {x}" for x in state["blockers"])
 return f'''## Current project coordinates

> Generated from {mdlink(src,'docs/current/STATE.json')}. Do not hand-edit this block.

```text
immediate repository action  {c['next_action_class']}
document migration           Phase {c['completed_phase']} complete; Phase {c['next_phase']} ready
program epoch                {p['epoch']['id']} — {p['epoch']['name']}
program gate held ready      {p['gate']['id']} — {p['gate']['name']}
program resume action        {p['next_action_class']}
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
'''
def render_readme(root:Path,state:dict[str,Any])->str:
 base=(root/'README.md').read_text(encoding='utf-8')
 block=state_block(state,'README.md')+'''\n### Current entry points

- [`docs/CURRENT_CONTEXT.md`](docs/CURRENT_CONTEXT.md)
- [`docs/INDEX.md`](docs/INDEX.md)
- [`docs/navigation/README.md`](docs/navigation/README.md)
- [`docs/SESSION_ONBOARDING.md`](docs/SESSION_ONBOARDING.md)
- [`docs/documentation/CURRENT_STATE_AUTHORITY.md`](docs/documentation/CURRENT_STATE_AUTHORITY.md)
- [`docs/documentation/GENERATED_NAVIGATION.md`](docs/documentation/GENERATED_NAVIGATION.md)
'''
 return replace_block(base,block)
def render_current(state:dict[str,Any])->str:
 src='docs/CURRENT_CONTEXT.md';p=state['program'];c=state['control_work']
 auth='\n'.join(f"{i}. {mdlink(src,a['path'])} — {a['role']}" for i,a in enumerate(state['accepted_authorities'],1))
 risks='\n'.join(f"- {x}" for x in state['unresolved_risks']); blockers='None.' if not state['blockers'] else '\n'.join(f"- {x}" for x in state['blockers'])
 return f'''# Current Project Context

> **Generated view:** {mdlink(src,'docs/current/STATE.json')} is the sole temporal authority.
> **State revision:** {state['state_revision']}
> **Do not hand-edit this file.** Run the Phase 3 renderer after a state or registry transition.

## Immediate repository work

```text
control work        {c['name']}
completed phase     {c['completed_phase']}
next phase          {c['next_phase']}
next action         {state['next_action_class']}
```

## Program position held ready

```text
current epoch       {p['epoch']['id']} — {p['epoch']['name']}
program status      {p['epoch']['status']}
program gate        {p['gate']['id']} — {p['gate']['name']}
gate status         {p['gate']['status']}
resume action       {p['next_action_class']}
```

Documentation control work does not advance or replace the research gate.

## Current E2-P3 claim boundary

```text
S22 Ultra / API 36 / qcom             accepted and frozen
Galaxy Note9 / API 29 / Exynos 9810  accepted and frozen
dual-device claim                     accepted — AArch64 Termux compatibility
Android Emulator                      waived, unqualified, unclaimed
selectability                         false
publication                           not authorized
```

## Active plan

- {mdlink(src,state['active_plan']['path'])}
- SHA-256: `{state['active_plan']['sha256']}`

## Accepted authorities

{auth}

## Blockers

{blockers}

## Unresolved risks

{risks}

## Immediate reading path

1. {mdlink(src,'docs/current/STATE.json')}
2. {mdlink(src,'docs/navigation/README.md')}
3. {mdlink(src,'docs/documentation/GENERATED_NAVIGATION.md')}
4. {mdlink(src,'docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md')}
5. {mdlink(src,'docs/INDEX.md')}
'''

def entry_line(src:str,d:dict[str,Any])->str:
 return f"- {mdlink(src,d['path'])} — `{d['lifecycle_class']}` · `{d['authority_domain']}` · owner `{d['owner']}`"
def assignment(path:str,targets:set[str])->str:
 if path in targets:return 'docs/navigation/README.md'
 pairs=[('docs/current/','docs/current/README.md'),('docs/documentation/','docs/documentation/README.md'),('docs/decisions/','docs/decisions/README.md'),('docs/epochs/','docs/epochs/README.md'),('docs/architecture/','docs/architecture/README.md'),('docs/roadmap/','docs/roadmap/README.md'),('docs/contracts/','docs/contracts/README.md'),('docs/evidence/','docs/evidence/README.md'),('docs/stages/','docs/stages/README.md'),('docs/handoff/','docs/handoff/README.md'),('docs/references/','docs/references/README.md'),('experiments/','experiments/README.md')]
 for prefix,target in pairs:
  if path.startswith(prefix):return target
 return 'docs/navigation/README.md'
def generic_index(src:str,title:str,description:str,entries:list[dict[str,Any]],reverse:bool=False)->str:
 entries=sorted(entries,key=lambda d:d['path'],reverse=reverse)
 body='\n'.join(entry_line(src,d) for d in entries) or '- None.'
 counts=Counter(d['lifecycle_class'] for d in entries); summary=', '.join(f"`{k}` {v}" for k,v in sorted(counts.items())) or 'none'
 return f'''# {title}

> **Generated view:** registry v3. Do not hand-edit.
> {description}

```text
entry count  {len(entries)}
lifecycle    {summary}
```

{body}
'''
def render_navigation(state:dict[str,Any],reg:dict[str,Any],manifest:dict[str,Any])->dict[str,str]:
 docs=reg['documents']; targets={x['path'] for x in manifest['targets']}; by_target=defaultdict(list)
 for d in docs:by_target[assignment(d['path'],targets)].append(d)
 out={}
 root='docs/navigation/README.md'; counts=Counter(d['lifecycle_class'] for d in docs)
 links='\n'.join(f"- {mdlink(root,t['path'])} — {t['role']}" for t in manifest['targets'] if t['path']!=root)
 extras='\n'.join(entry_line(root,d) for d in sorted(by_target[root],key=lambda x:x['path']) if d['path'] not in targets)
 lifecycle='\n'.join(f"- `{k}`: {v}" for k,v in sorted(counts.items()))
 out[root]=f'''# Documentation Navigation

> **Generated root:** registry v3 + {mdlink(root,'docs/current/STATE.json')}.
> Every tracked Markdown or JSON document is a generated entrypoint or has one canonical index assignment.

## Current coordinates

```text
immediate action  {state['next_action_class']}
program gate      {state['program']['gate']['id']} — {state['program']['gate']['name']}
program resume    {state['program']['next_action_class']}
tracked docs      {len(docs)}
index targets     {len(targets)}
```

## Lifecycle distribution

{lifecycle}

## Generated entrypoints

{links}

## Other canonical roots

{extras}

## Interpretation rule

Generated navigation creates no claim. Frozen authority answers what was proven; historical snapshots answer what a past boundary recorded; `STATE.json` answers where the project is now.
'''
 titles={
 'docs/current/README.md':('Current State','Sole temporal source, schemas, and current-state records.'),
 'docs/documentation/README.md':('Documentation Governance','Lifecycle, current-state, registry, and navigation governance.'),
 'docs/decisions/README.md':('Architecture Decisions','Stable decision records.'),
 'docs/epochs/README.md':('Epoch Charters and History','Epoch-level charters and historical indexes.'),
 'docs/architecture/README.md':('Architecture','Stable architecture and ownership documents.'),
 'docs/roadmap/README.md':('Plans and Roadmaps','Plans define gates and stop conditions; live completion status belongs to STATE.json.'),
 'docs/contracts/README.md':('Contracts','Frozen claim and experiment contracts.'),
 'docs/evidence/README.md':('Evidence','Frozen evidence records. Generated index ordering does not imply authority precedence.'),
 'docs/stages/README.md':('Stage Snapshots','Historical stage scope and completion snapshots.'),
 'docs/handoff/README.md':('Session Handoffs','Historical handoffs, newest filename first. Current state is not owned here.'),
 'docs/references/README.md':('References','Interpreted references and byte-preserved raw source captures.'),
 }
 for target,(title,desc) in titles.items():out[target]=generic_index(target,title,desc,[d for d in by_target[target] if d['path']!=target],target=='docs/handoff/README.md')
 # Experiments grouped by experiment directory.
 src='experiments/README.md'; groups=defaultdict(list)
 for d in by_target[src]:
  if d['path']==src:continue
  parts=d['path'].split('/'); groups['/'.join(parts[:2])].append(d)
 sections=[]
 for g in sorted(groups):sections.append(f"## `{g}`\n\n"+'\n'.join(entry_line(src,d) for d in sorted(groups[g],key=lambda x:x['path'])))
 out[src]=f'''# Experiments

> **Generated view:** registry v3. Do not hand-edit.
> Experiment-local documents may be frozen authority or historical snapshots; the lifecycle column governs interpretation.

```text
experiment directories  {len(groups)}
document entries         {sum(len(v) for v in groups.values())}
```

'''+"\n\n".join(sections)+"\n"
 return out
def render_index(state:dict[str,Any],reg:dict[str,Any])->str:
 src='docs/INDEX.md';docs=reg['documents']
 primary='\n'.join(entry_line(src,d) for d in sorted(docs,key=lambda x:x['path']) if d['onboarding_visibility']=='primary' and d['path'] not in {'README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'}) or '- None.'
 plans='\n'.join(entry_line(src,d) for d in sorted(docs,key=lambda x:x['path']) if d['lifecycle_class']=='ACTIVE_PLAN') or '- None.'
 auth='\n'.join(f"- {mdlink(src,a['path'])} — {a['role']}" for a in state['accepted_authorities'])
 return f'''# Documentation Index

> **Generated view:** registry v3 + {mdlink(src,'docs/current/STATE.json')}.
> **Do not hand-edit.** Exhaustive navigation starts at {mdlink(src,'docs/navigation/README.md')}.

## Current

```text
immediate action  {state['next_action_class']}
program gate      {state['program']['gate']['id']} — {state['program']['gate']['name']}
program resume    {state['program']['next_action_class']}
blocker count     {len(state['blockers'])}
```

- {mdlink(src,'docs/current/STATE.json')}
- {mdlink(src,'docs/CURRENT_CONTEXT.md')}
- {mdlink(src,'docs/SESSION_ONBOARDING.md')}
- {mdlink(src,'docs/navigation/README.md')}
- {mdlink(src,'docs/documentation/GENERATED_NAVIGATION.md')}

## Primary reading set

{primary}

## Active plans

{plans}

## Accepted current authorities

{auth}

## Complete generated indexes

- {mdlink(src,'docs/current/README.md')}
- {mdlink(src,'docs/documentation/README.md')}
- {mdlink(src,'docs/decisions/README.md')}
- {mdlink(src,'docs/epochs/README.md')}
- {mdlink(src,'docs/architecture/README.md')}
- {mdlink(src,'docs/roadmap/README.md')}
- {mdlink(src,'docs/contracts/README.md')}
- {mdlink(src,'docs/evidence/README.md')}
- {mdlink(src,'docs/stages/README.md')}
- {mdlink(src,'docs/handoff/README.md')}
- {mdlink(src,'docs/references/README.md')}
- {mdlink(src,'experiments/README.md')}

Historical files may contain snapshot-relative `active`, `next`, or `pending` language. They do not override `STATE.json`.
'''
def render_onboarding(root:Path,state:dict[str,Any])->str:
 base=(root/'docs/SESSION_ONBOARDING.md').read_text(encoding='utf-8');p=state['program'];c=state['control_work'];src='docs/SESSION_ONBOARDING.md'
 block=f'''## Current reading path

> Generated from {mdlink(src,'docs/current/STATE.json')}.

1. {mdlink(src,'docs/current/STATE.json')}
2. {mdlink(src,'docs/CURRENT_CONTEXT.md')}
3. {mdlink(src,'docs/navigation/README.md')}
4. {mdlink(src,'docs/documentation/GENERATED_NAVIGATION.md')}
5. {mdlink(src,'docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md')}
6. {mdlink(src,'docs/INDEX.md')}

```text
immediate repository action  {c['next_action_class']}
program gate held ready      {p['gate']['id']} — {p['gate']['name']}
program resume action        {p['next_action_class']}
```
'''
 return replace_block(base,block)
def expected(root:Path)->dict[Path,str]:
 state=load(root/STATE);reg=load(root/REGISTRY);manifest=load(root/TARGETS)
 out={root/'README.md':render_readme(root,state),root/'docs/CURRENT_CONTEXT.md':render_current(state),root/'docs/INDEX.md':render_index(state,reg),root/'docs/SESSION_ONBOARDING.md':render_onboarding(root,state)}
 out.update({root/p:t for p,t in render_navigation(state,reg,manifest).items()});return out
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--check',action='store_true');a=p.parse_args();root=Path(a.root).resolve();bad=[]
 for path,text in expected(root).items():
  if a.check:
   if not path.is_file() or path.read_text(encoding='utf-8')!=text:bad.append(str(path.relative_to(root)))
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
 result={'pass':not bad,'mismatched_targets':bad,'current_target_count':4,'navigation_target_count':13,'target_count':17};print(json.dumps(result,indent=2,sort_keys=True))
 return 0 if not bad else 1
if __name__=='__main__':sys.exit(main())

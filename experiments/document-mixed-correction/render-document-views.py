#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
from collections import Counter,defaultdict
from typing import Any
STATE=Path('docs/current/STATE.json');REG=Path('docs/documentation/document-registry.json');TARGETS=Path('experiments/document-mixed-correction/navigation-targets.json')
BEGIN='<!-- BEGIN GENERATED CURRENT STATE -->';END='<!-- END GENERATED CURRENT STATE -->'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def rel(src,dst):return os.path.relpath(dst,start=str(Path(src).parent)).replace(os.sep,'/')
def link(src,dst):return f'[`{dst}`]({rel(src,dst)})'
def replace(text,block):
 if text.count(BEGIN)!=1 or text.count(END)!=1:raise ValueError('generated markers missing or non-unique')
 return text.split(BEGIN,1)[0].rstrip()+'\n\n'+BEGIN+'\n'+block.rstrip()+'\n'+END+'\n\n'+text.split(END,1)[1].lstrip('\n')
def entry(src,d):
 suffix=''
 if d['lifecycle_class']=='HISTORICAL_SNAPSHOT':suffix=' · snapshot-relative status; does not override STATE.json'
 return f"- {link(src,d['path'])} — `{d['lifecycle_class']}` · `{d['authority_domain']}` · owner `{d['owner']}`{suffix}"
def assignment(d,targets):
 p=d['path']
 if p in targets:return 'docs/navigation/README.md'
 if d['lifecycle_class']=='HISTORICAL_SNAPSHOT' and p.startswith('docs/PROJECT_'):return 'docs/history/README.md'
 pairs=[('docs/current/','docs/current/README.md'),('docs/documentation/','docs/documentation/README.md'),('docs/decisions/','docs/decisions/README.md'),('docs/epochs/','docs/epochs/README.md'),('docs/architecture/','docs/architecture/README.md'),('docs/roadmap/','docs/roadmap/README.md'),('docs/contracts/','docs/contracts/README.md'),('docs/evidence/','docs/evidence/README.md'),('docs/stages/','docs/stages/README.md'),('docs/handoff/','docs/handoff/README.md'),('docs/history/','docs/history/README.md'),('docs/references/','docs/references/README.md'),('experiments/','experiments/README.md')]
 for pre,t in pairs:
  if p.startswith(pre):return t
 return 'docs/navigation/README.md'
def current_block(state,src):
 p=state['program'];c=state['control_work'];claims=state['claim_boundaries']
 auth='\n'.join(f"- {link(src,a['path'])}: {a['role']} (`{a['sha256']}`)" for a in state['accepted_authorities'])
 risks='\n'.join(f'- {x}' for x in state['unresolved_risks']) or 'none'; blockers='none' if not state['blockers'] else '\n'.join(f'- {x}' for x in state['blockers'])
 return f'''## Current project coordinates

> Generated from {link(src,'docs/current/STATE.json')}. Do not hand-edit this block.

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

### Current entry points

- {link(src,'docs/PROJECT_GUIDE.md')}
- {link(src,'docs/CURRENT_CONTEXT.md')}
- {link(src,'docs/INDEX.md')}
- {link(src,'docs/navigation/README.md')}
- {link(src,'docs/SESSION_ONBOARDING.md')}
'''
def render_current(s):
 src='docs/CURRENT_CONTEXT.md';p=s['program'];c=s['control_work'];auth='\n'.join(f"{i}. {link(src,a['path'])} — {a['role']}" for i,a in enumerate(s['accepted_authorities'],1));risks='\n'.join(f'- {x}' for x in s['unresolved_risks']) or 'None.'
 return f'''# Current Project Context

> **Generated view:** {link(src,'docs/current/STATE.json')} is the sole temporal authority.
> **State revision:** {s['state_revision']}
> **Do not hand-edit.** Run the Phase 4 renderer after a state or registry transition.

## Immediate repository work

```text
completed phase  {c['completed_phase']}
next phase       {c['next_phase']}
next action      {s['next_action_class']}
```

## Program position held ready

```text
epoch          {p['epoch']['id']} — {p['epoch']['name']}
gate           {p['gate']['id']} — {p['gate']['name']}
resume action  {p['next_action_class']}
```

## Stable orientation and active plan

- Project guide: {link(src,s['project_guide']['path'])}
- Program plan: {link(src,s['active_plan']['path'])}
- Detailed plan: {link(src,s['active_plan']['detail_path'])}

## Current claim boundary

```text
S22 Ultra and Galaxy Note9 evidence  accepted and frozen
bounded dual-device claim            AArch64 Termux compatibility
Android Emulator                     waived, unqualified, unclaimed
selectability                         false
publication                           not authorized
```

## Accepted authorities

{auth}

## Blockers

{'None.' if not s['blockers'] else chr(10).join('- '+x for x in s['blockers'])}

## Unresolved risks

{risks}

## Immediate reading path

1. {link(src,'docs/PROJECT_GUIDE.md')}
2. {link(src,'docs/current/STATE.json')}
3. {link(src,'docs/roadmap/EPOCH2_PROGRAM_PLAN.md')}
4. {link(src,'docs/navigation/README.md')}
5. {link(src,'docs/INDEX.md')}
'''
def generic(src,title,desc,items,reverse=False):
 items=sorted(items,key=lambda d:d['path'],reverse=reverse);counts=Counter(d['lifecycle_class'] for d in items);body='\n'.join(entry(src,d) for d in items) or '- None.'
 return f'''# {title}

> **Generated view:** registry v4. Do not hand-edit.
> {desc}

```text
entry count  {len(items)}
lifecycle    {', '.join(f'`{k}` {v}' for k,v in sorted(counts.items())) or 'none'}
```

{body}
'''
def navigation(s,r,m):
 docs=r['documents'];targets={x['path'] for x in m['targets']};by=defaultdict(list)
 for d in docs:by[assignment(d,targets)].append(d)
 out={};root='docs/navigation/README.md';counts=Counter(d['lifecycle_class'] for d in docs);links='\n'.join(f"- {link(root,t['path'])} — {t['role']}" for t in m['targets'] if t['path']!=root);extras='\n'.join(entry(root,d) for d in sorted(by[root],key=lambda x:x['path']) if d['path'] not in targets)
 out[root]=f'''# Documentation Navigation

> **Generated root:** registry v4 + {link(root,'docs/current/STATE.json')}.
> Start with the stable project guide, then use typed indexes for current state, plans, authority, and history.

## Primary entry

- {link(root,'docs/PROJECT_GUIDE.md')}

## Current coordinates

```text
immediate action  {s['next_action_class']}
program gate      {s['program']['gate']['id']} — {s['program']['gate']['name']}
tracked docs      {len(docs)}
index targets     {len(targets)}
```

## Lifecycle distribution

{chr(10).join(f'- `{k}`: {v}' for k,v in sorted(counts.items()))}

## Generated entrypoints

{links}

## Other canonical roots

{extras or '- None.'}

## Interpretation rule

`STATE.json` owns present coordinates. Active plans own future structure. Frozen authority owns accepted claims. Historical status language is snapshot-relative and never overrides current state.
'''
 titles={'docs/current/README.md':('Current State','Sole temporal source and versioned schemas.'),'docs/decisions/README.md':('Architecture Decisions','Stable decision records.'),'docs/epochs/README.md':('Epoch Charters and History','Epoch-level governance and history.'),'docs/architecture/README.md':('Architecture','Stable architecture and ownership documents.'),'docs/contracts/README.md':('Contracts','Frozen claim and experiment contracts.'),'docs/evidence/README.md':('Evidence','Frozen evidence records; ordering implies no precedence.'),'docs/stages/README.md':('Stage Snapshots','Historical stage scope and completion snapshots.'),'docs/handoff/README.md':('Session Handoffs','Historical handoffs, newest filename first.'),'docs/references/README.md':('References','Interpreted references and byte-preserved raw captures.')}
 for t,(title,desc) in titles.items():out[t]=generic(t,title,desc,[d for d in by[t] if d['path']!=t],t=='docs/handoff/README.md')
 # Documentation index separates enduring rules and completed phase contracts.
 t='docs/documentation/README.md';items=[d for d in by[t] if d['path']!=t];stable=[d for d in items if d['lifecycle_class']=='STABLE'];frozen=[d for d in items if d['lifecycle_class']=='FROZEN_AUTHORITY'];other=[d for d in items if d not in stable+frozen]
 out[t]='# Documentation Governance\n\n> **Generated view:** registry v4. Do not hand-edit.\n\n## Stable ongoing rules\n\n'+('\n'.join(entry(t,d) for d in sorted(stable,key=lambda x:x['path'])) or '- None.')+'\n\n## Completed phase contracts and schemas\n\n'+('\n'.join(entry(t,d) for d in sorted(frozen,key=lambda x:x['path'])) or '- None.')+'\n\n## Other records\n\n'+('\n'.join(entry(t,d) for d in sorted(other,key=lambda x:x['path'])) or '- None.')+'\n'
 # Roadmap index separates active and historical.
 t='docs/roadmap/README.md';items=[d for d in by[t] if d['path']!=t];active=[d for d in items if d['lifecycle_class']=='ACTIVE_PLAN'];hist=[d for d in items if d['lifecycle_class']=='HISTORICAL_SNAPSHOT'];other=[d for d in items if d not in active+hist]
 out[t]='# Plans and Roadmaps\n\n> **Generated view:** registry v4. Do not hand-edit.\n> Current progress belongs to STATE.json; historical plan status is snapshot-relative.\n\n## Canonical active plans\n\n'+('\n'.join(entry(t,d) for d in sorted(active,key=lambda x:x['path'])) or '- None.')+'\n\n## Historical plan snapshots\n\n'+('\n'.join(entry(t,d) for d in sorted(hist,key=lambda x:x['path'])) or '- None.')+'\n\n## Other\n\n'+('\n'.join(entry(t,d) for d in sorted(other,key=lambda x:x['path'])) or '- None.')+'\n'
 # History root.
 t='docs/history/README.md';items=[d for d in by[t] if d['path']!=t]
 out[t]='# Historical Snapshots\n\n> **Generated view:** registry v4. Do not hand-edit.\n> Every `active`, `next`, `pending`, or `current` statement below is relative to the file\'s recorded snapshot. Present coordinates come only from [`docs/current/STATE.json`](../current/STATE.json).\n\n## Current successors\n\n- [`docs/PROJECT_GUIDE.md`](../PROJECT_GUIDE.md) — stable project meaning\n- [`docs/current/STATE.json`](../current/STATE.json) — present coordinates\n- [`docs/roadmap/EPOCH2_PROGRAM_PLAN.md`](../roadmap/EPOCH2_PROGRAM_PLAN.md) — canonical program plan\n\n## Snapshot inventory\n\n'+('\n'.join(entry(t,d) for d in sorted(items,key=lambda x:x['path'])) or '- None.')+'\n'
 # Experiments.
 t='experiments/README.md';groups=defaultdict(list)
 for d in by[t]:
  if d['path']==t:continue
  groups['/'.join(d['path'].split('/')[:2])].append(d)
 out[t]='# Experiments\n\n> **Generated view:** registry v4. Do not hand-edit.\n\n'+ '\n\n'.join(f"## `{g}`\n\n"+'\n'.join(entry(t,d) for d in sorted(v,key=lambda x:x['path'])) for g,v in sorted(groups.items()))+'\n'
 return out
def render_index(s,r):
 src='docs/INDEX.md';docs=r['documents'];primary='\n'.join(entry(src,d) for d in docs if d['onboarding_visibility']=='primary' and d['path'] not in {'README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'});plans='\n'.join(entry(src,d) for d in docs if d['lifecycle_class']=='ACTIVE_PLAN');auth='\n'.join(f"- {link(src,a['path'])} — {a['role']}" for a in s['accepted_authorities'])
 return f'''# Documentation Index

> **Generated view:** registry v4 + {link(src,'docs/current/STATE.json')}.
> Exhaustive navigation starts at {link(src,'docs/navigation/README.md')}.

## Current

```text
immediate action  {s['next_action_class']}
program gate      {s['program']['gate']['id']} — {s['program']['gate']['name']}
blocker count     {len(s['blockers'])}
```

- {link(src,'docs/PROJECT_GUIDE.md')}
- {link(src,'docs/current/STATE.json')}
- {link(src,'docs/CURRENT_CONTEXT.md')}
- {link(src,'docs/navigation/README.md')}

## Primary reading set

{primary}

## Active plans

{plans}

## Accepted authorities

{auth}

## Layer indexes

- {link(src,'docs/documentation/README.md')}
- {link(src,'docs/roadmap/README.md')}
- {link(src,'docs/evidence/README.md')}
- {link(src,'docs/history/README.md')}
- {link(src,'experiments/README.md')}

Historical files never override `STATE.json`.
'''
def onboarding(root,s):
 src='docs/SESSION_ONBOARDING.md';base=(root/src).read_text(encoding='utf-8');p=s['program'];c=s['control_work'];block=f'''## Current reading path

> Generated from {link(src,'docs/current/STATE.json')}.

1. {link(src,'docs/PROJECT_GUIDE.md')}
2. {link(src,'docs/current/STATE.json')}
3. {link(src,'docs/CURRENT_CONTEXT.md')}
4. {link(src,'docs/roadmap/EPOCH2_PROGRAM_PLAN.md')}
5. {link(src,'docs/navigation/README.md')}
6. {link(src,'docs/INDEX.md')}

```text
immediate repository action  {c['next_action_class']}
program gate held ready      {p['gate']['id']} — {p['gate']['name']}
program resume action        {p['next_action_class']}
```
''';return replace(base,block)
def expected(root):
 s=load(root/STATE);r=load(root/REG);m=load(root/TARGETS);out={root/'README.md':replace((root/'README.md').read_text(encoding='utf-8'),current_block(s,'README.md')),root/'docs/CURRENT_CONTEXT.md':render_current(s),root/'docs/INDEX.md':render_index(s,r),root/'docs/SESSION_ONBOARDING.md':onboarding(root,s)};out.update({root/p:v for p,v in navigation(s,r,m).items()});return out
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default='.');a.add_argument('--check',action='store_true');x=a.parse_args();root=Path(x.root).resolve();bad=[]
 for p,t in expected(root).items():
  if x.check:
   if not p.is_file() or p.read_text(encoding='utf-8')!=t:bad.append(str(p.relative_to(root)))
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding='utf-8')
 out={'pass':not bad,'mismatched_targets':bad,'current_target_count':4,'navigation_target_count':14,'target_count':18};print(json.dumps(out,indent=2,sort_keys=True));return 0 if not bad else 1
if __name__=='__main__':sys.exit(main())

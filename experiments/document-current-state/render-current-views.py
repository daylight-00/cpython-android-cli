#!/usr/bin/env python3
"""Render deterministic current-state views from STATE.json and document registry v2."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

STATE=Path("docs/current/STATE.json")
REGISTRY=Path("docs/documentation/document-registry.json")
BEGIN="<!-- BEGIN GENERATED CURRENT STATE -->"
END="<!-- END GENERATED CURRENT STATE -->"


def load(path:Path)->Any: return json.loads(path.read_text(encoding="utf-8"))

def replace_block(text:str, block:str)->str:
    if text.count(BEGIN)!=1 or text.count(END)!=1 or text.index(BEGIN)>text.index(END):
        raise ValueError("generated markers missing or non-unique")
    before=text.split(BEGIN,1)[0].rstrip()
    after=text.split(END,1)[1].lstrip("\n")
    return before+"\n\n"+BEGIN+"\n"+block.rstrip()+"\n"+END+"\n\n"+after

def state_lines(state:dict[str,Any], prefix:str="") -> str:
    p=state["program"]; c=state["control_work"]; claims=state["claim_boundaries"]
    blockers=state["blockers"]
    risks=state["unresolved_risks"]
    auth="\n".join(f"- [`{a['id']}`]({prefix}{a['path']}): {a['role']} (`{a['sha256']}`)" for a in state["accepted_authorities"])
    blocker_text="none" if not blockers else "\n".join(f"- {x}" for x in blockers)
    risk_text="\n".join(f"- {x}" for x in risks)
    return f"""## Current project coordinates

> Generated from [`docs/current/STATE.json`]({prefix}docs/current/STATE.json). Do not hand-edit this block.

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

{blocker_text}

### Unresolved risks

{risk_text}

### Accepted authorities

{auth}
"""

def render_readme(root:Path,state:dict[str,Any])->str:
    base=(root/"README.md").read_text(encoding="utf-8")
    block=state_lines(state,"") + """
### Current entry points

- [`docs/CURRENT_CONTEXT.md`](docs/CURRENT_CONTEXT.md)
- [`docs/INDEX.md`](docs/INDEX.md)
- [`docs/SESSION_ONBOARDING.md`](docs/SESSION_ONBOARDING.md)
- [`docs/documentation/CURRENT_STATE_AUTHORITY.md`](docs/documentation/CURRENT_STATE_AUTHORITY.md)
- [`docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)
"""
    return replace_block(base,block)

def render_current(state:dict[str,Any])->str:
    p=state["program"]; c=state["control_work"]
    authority_links="\n".join(f"{i}. [`{a['id']}`]({a['path'].replace('docs/','',1) if a['path'].startswith('docs/') else '../'+a['path']}) — {a['role']}" for i,a in enumerate(state["accepted_authorities"],1))
    risks="\n".join(f"- {x}" for x in state["unresolved_risks"])
    blockers="None." if not state["blockers"] else "\n".join(f"- {x}" for x in state["blockers"])
    return f"""# Current Project Context

> **Generated view:** [`current/STATE.json`](current/STATE.json) is the sole temporal authority.
> **State revision:** {state['state_revision']}
> **Do not hand-edit this file.** Run `render-current-views.py` after a state transition.

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

Documentation control work does not close, advance, or replace the research gate. After the lifecycle migration is complete, the program resumes at E2-R1 / UT-0.

## Current E2-P3 claim boundary

```text
S22 Ultra / API 36 / qcom     accepted and frozen
Galaxy Note9 / API 29 / Exynos 9810  accepted and frozen
dual-device claim     accepted — AArch64 Termux compatibility
Android Emulator      waived, unqualified, unclaimed
selectability         false
publication           not authorized
```

## Active plan

- [`{state['active_plan']['path'].replace('docs/','',1)}`]({state['active_plan']['path'].replace('docs/','',1)})
- SHA-256: `{state['active_plan']['sha256']}`

## Accepted authorities

{authority_links}

## Blockers

{blockers}

## Unresolved risks

{risks}

## Immediate reading path

1. [`current/STATE.json`](current/STATE.json)
2. [`documentation/CURRENT_STATE_AUTHORITY.md`](documentation/CURRENT_STATE_AUTHORITY.md)
3. [`roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)
4. [`INDEX.md`](INDEX.md)

## Update rule

Change temporal facts only in `current/STATE.json`, update the registry if inventory or lifecycle metadata changes, then render and verify all views in the same transaction.
"""

def link_for_docs(path:str)->str:
    return path[5:] if path.startswith("docs/") else "../"+path

def render_index(state:dict[str,Any],registry:dict[str,Any])->str:
    docs=registry["documents"]
    def rows(pred):
        selected=sorted((d for d in docs if pred(d)),key=lambda d:d["path"])
        return "\n".join(f"- [`{d['path']}`]({link_for_docs(d['path'])}) — `{d['lifecycle_class']}`" for d in selected) or "- None."
    primary=rows(lambda d:d["onboarding_visibility"]=="primary" and d["path"] not in {"README.md","docs/CURRENT_CONTEXT.md","docs/INDEX.md"})
    stable=rows(lambda d:d["onboarding_visibility"]=="secondary" and d["lifecycle_class"] in {"STABLE","STABLE_WITH_GENERATED_SECTION","APPEND_ONLY_LOG"})
    plans=rows(lambda d:d["lifecycle_class"]=="ACTIVE_PLAN")
    inputs=rows(lambda d:d["lifecycle_class"]=="CURRENT_INPUT_LOCK")
    auth="\n".join(f"- [`{a['id']}`]({link_for_docs(a['path'])}) — {a['role']}" for a in state["accepted_authorities"])
    return f"""# Documentation Index

> **Generated view:** registry v{registry['schema_version']} + [`current/STATE.json`](current/STATE.json).
> **Do not hand-edit this file.** Directory-level exhaustive indexes remain Phase 3 work.

## Current

```text
immediate action  {state['next_action_class']}
program gate      {state['program']['gate']['id']} — {state['program']['gate']['name']}
program resume    {state['program']['next_action_class']}
blocker count     {len(state['blockers'])}
```

- [`current/STATE.json`](current/STATE.json)
- [`CURRENT_CONTEXT.md`](CURRENT_CONTEXT.md)
- [`SESSION_ONBOARDING.md`](SESSION_ONBOARDING.md)
- [`documentation/CURRENT_STATE_AUTHORITY.md`](documentation/CURRENT_STATE_AUTHORITY.md)

## Primary reading set

{primary}

## Active plans

{plans}

## Accepted current authorities

{auth}

## Stable governance and operations

{stable}

## Current input locks

{inputs}

## Historical collections

- [`epochs/EPOCH1_INDEX.md`](epochs/EPOCH1_INDEX.md)
- [`stages/`](stages/)
- [`evidence/`](evidence/)
- [`handoff/`](handoff/)
- [`../experiments/`](../experiments/)
- [`PROJECT_CONTEXT_STAGE3F.md`](PROJECT_CONTEXT_STAGE3F.md)

Historical files may contain `active`, `next`, or `pending` language relative to their original commit. They do not override `current/STATE.json`.

## References

- [`references/`](references/)
- [`references/raw/`](references/raw/)

## Registry

- [`documentation/document-registry.json`](documentation/document-registry.json)
- [`documentation/document-registry-v2.schema.json`](documentation/document-registry-v2.schema.json)
- [`documentation/DOCUMENT_LIFECYCLE.md`](documentation/DOCUMENT_LIFECYCLE.md)
"""

def render_onboarding(root:Path,state:dict[str,Any])->str:
    base=(root/"docs/SESSION_ONBOARDING.md").read_text(encoding="utf-8")
    p=state["program"]; c=state["control_work"]
    block=f"""## Current reading path

> Generated from [`current/STATE.json`](current/STATE.json).

1. [`current/STATE.json`](current/STATE.json)
2. [`CURRENT_CONTEXT.md`](CURRENT_CONTEXT.md)
3. [`documentation/CURRENT_STATE_AUTHORITY.md`](documentation/CURRENT_STATE_AUTHORITY.md)
4. [`roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)
5. [`INDEX.md`](INDEX.md)

```text
immediate repository action  {c['next_action_class']}
program gate held ready      {p['gate']['id']} — {p['gate']['name']}
program resume action        {p['next_action_class']}
```
"""
    return replace_block(base,block)

def expected(root:Path)->dict[Path,str]:
    state=load(root/STATE); registry=load(root/REGISTRY)
    return {root/"README.md":render_readme(root,state),root/"docs/CURRENT_CONTEXT.md":render_current(state),root/"docs/INDEX.md":render_index(state,registry),root/"docs/SESSION_ONBOARDING.md":render_onboarding(root,state)}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--root",default="."); p.add_argument("--check",action="store_true"); a=p.parse_args(); root=Path(a.root).resolve()
    bad=[]
    for path,text in expected(root).items():
        if a.check:
            if not path.is_file() or path.read_text(encoding="utf-8")!=text: bad.append(str(path.relative_to(root)))
        else:
            path.write_text(text,encoding="utf-8")
    if a.check:
        print(json.dumps({"pass":not bad,"mismatched_targets":bad,"target_count":4},indent=2,sort_keys=True))
        return 0 if not bad else 1
    return 0
if __name__=="__main__": sys.exit(main())

#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

REQUIRED = [
    'START_HERE.md','PROJECT_ORIENTATION.md','HANDOFF_MANIFEST.json','SHA256SUMS','tools/handoff_cycle.py'
]
STALE = ('file-not-uploaded','not uploaded during','folder-created; file-not-uploaded')
LINK_RE = re.compile(r'(?<!!)\[[^\]]+\]\(([^)]+)\)')

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def root_path(value: str) -> Path:
    p=Path(value).resolve()
    if (p/'HANDOFF_MANIFEST.json').is_file(): return p
    children=[x for x in p.iterdir() if x.is_dir()] if p.is_dir() else []
    if len(children)==1 and (children[0]/'HANDOFF_MANIFEST.json').is_file(): return children[0]
    raise SystemExit(f'cannot identify handoff root: {p}')

def load(root: Path):
    m=json.loads((root/'HANDOFF_MANIFEST.json').read_text())
    return m

def verify(root: Path) -> dict:
    errors=[]
    missing=[x for x in REQUIRED if not (root/x).is_file()]
    if missing: errors.append('missing required: '+', '.join(missing))
    try: m=load(root)
    except Exception as e: return {'pass':False,'errors':[f'manifest: {e}']}
    for key in ('schema_version','handoff_id','package_class','project','repository','gate_state','immediate_task','reading_order','audit_order','delivery_intent','full_cycle'):
        if key not in m: errors.append(f'manifest missing key: {key}')
    if m.get('package_class')!='mandatory-handoff': errors.append('package_class is not mandatory-handoff')
    sums={}
    for line in (root/'SHA256SUMS').read_text().splitlines() if (root/'SHA256SUMS').is_file() else []:
        if not line.strip(): continue
        try: digest, rel=line.split('  ',1)
        except ValueError: errors.append(f'bad SHA256SUMS line: {line}'); continue
        sums[rel]=digest
    actual=sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    if sorted(sums)!=actual:
        errors.append(f'SHA256SUMS coverage mismatch missing={sorted(set(actual)-set(sums))} extra={sorted(set(sums)-set(actual))}')
    for rel,digest in sums.items():
        p=root/rel
        if p.is_file() and sha(p)!=digest: errors.append(f'hash mismatch: {rel}')
    for rel in m.get('reading_order',[]):
        if not (root/rel).is_file(): errors.append(f'reading_order target missing: {rel}')
    for md in root.rglob('*.md'):
        text=md.read_text(encoding='utf-8')
        low=text.lower()
        for phrase in STALE:
            if phrase in low: errors.append(f'stale delivery phrase in {md.relative_to(root)}: {phrase}')
        for target in LINK_RE.findall(text):
            if target.startswith(('http://','https://','#','repo:')): continue
            clean=target.split('#',1)[0]
            if not clean: continue
            resolved=(md.parent/clean).resolve()
            try: resolved.relative_to(root)
            except ValueError: errors.append(f'link escapes package: {md.relative_to(root)} -> {target}'); continue
            if not resolved.exists(): errors.append(f'broken package link: {md.relative_to(root)} -> {target}')
    for rel in ('reference-docs/session-operations/SESSION_CYCLE.md','reference-docs/session-operations/SESSION_CLOSE_INITIALIZATION.md','reference-docs/session-operations/HANDOFF_PACKAGE_SPEC.md','reference-docs/session-operations/templates/HANDOFF_MANIFEST.example.json','reference-docs/session-operations/templates/DATED_HANDOFF_TEMPLATE.md'):
        if not (root/rel).is_file(): errors.append(f'full-cycle asset missing: {rel}')
    return {'pass':not errors,'error_count':len(errors),'errors':errors,'file_count':len(actual)+1,'handoff_id':m.get('handoff_id')}

def onboard(root: Path):
    m=load(root)
    print(f"HANDOFF_ID={m.get('handoff_id')}")
    print('READING_ORDER:')
    for i,x in enumerate(m.get('reading_order',[]),1): print(f'  {i}. {x}')
    print('IMMEDIATE_TASK:')
    print('  '+str(m.get('immediate_task','')))
    print('GATE_STATE:')
    for k,v in m.get('gate_state',{}).items(): print(f'  {k}={v}')

def close_readiness(root: Path):
    result=verify(root)
    assets={
      'cycle': root/'reference-docs/session-operations/SESSION_CYCLE.md',
      'close': root/'reference-docs/session-operations/SESSION_CLOSE_INITIALIZATION.md',
      'spec': root/'reference-docs/session-operations/HANDOFF_PACKAGE_SPEC.md',
      'manifest_template': root/'reference-docs/session-operations/templates/HANDOFF_MANIFEST.example.json',
      'dated_template': root/'reference-docs/session-operations/templates/DATED_HANDOFF_TEMPLATE.md',
    }
    ok=result['pass'] and all(p.is_file() for p in assets.values())
    print('CLOSE_READINESS='+('PASS' if ok else 'FAIL'))
    for k,p in assets.items(): print(f'{k}={"present" if p.is_file() else "missing"}')
    return 0 if ok else 1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('command',choices=['verify','onboard','close-readiness']); ap.add_argument('root',nargs='?',default='.')
    a=ap.parse_args(); root=root_path(a.root)
    if a.command=='verify':
        r=verify(root); print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r['pass'] else 1
    if a.command=='onboard': onboard(root); return 0
    return close_readiness(root)
if __name__=='__main__': raise SystemExit(main())

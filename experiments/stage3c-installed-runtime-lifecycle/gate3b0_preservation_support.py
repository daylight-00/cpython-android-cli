#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,shutil,stat,subprocess,sys
from pathlib import Path
from typing import Any

EXPECTED_GATE2R_INDEX='69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c'
EXPECTED_CONTRACT_INDEX='79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3'
EXPECTED_ENGINE_SHA='33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a'
EXPECTED_OPS_SHA='61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021'
REGULAR_CANDIDATE='lib/python3.14/LICENSE.txt'; SYMLINK_CANDIDATE='bin/python'
UNOWNED_FILE='lib/python3.14/site-packages/gate3b0-user-file.txt'
UNOWNED_DIR='lib/python3.14/site-packages/gate3b0-user-dir'

def cjson(v:Any)->bytes:return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def read_json(p:Path)->dict[str,Any]:
 v=json.loads(p.read_text());
 if not isinstance(v,dict):raise ValueError(p)
 return v
def write_json(p:Path,v:dict[str,Any])->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(cjson(v))
def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def kind(p:Path)->str:
 try:m=p.lstat().st_mode
 except FileNotFoundError:return 'absent'
 if stat.S_ISLNK(m):return 'symlink'
 if stat.S_ISREG(m):return 'regular'
 if stat.S_ISDIR(m):return 'directory'
 return 'special'
def snapshot(p:Path)->dict[str,Any]:
 k=kind(p);r={'path':str(p),'type':k}
 if k=='absent':return r
 s=p.lstat();r['mode']=f'{stat.S_IMODE(s.st_mode):04o}'
 if k=='regular':r.update(size=s.st_size,sha256=sha256_file(p))
 elif k=='symlink':r['target']=os.readlink(p)
 elif k=='directory':
  rows=[]
  for q in sorted(p.rglob('*'),key=lambda x:x.relative_to(p).as_posix()):
   rel=q.relative_to(p).as_posix();qk=kind(q);qs=q.lstat();row={'path':rel,'type':qk,'mode':f'{stat.S_IMODE(qs.st_mode):04o}'}
   if qk=='regular':row.update(size=qs.st_size,sha256=sha256_file(q))
   elif qk=='symlink':row['target']=os.readlink(q)
   rows.append(row)
  r['entries']=rows
 return r
def registry(root:Path)->dict[str,Any]:
 p=root/'.cpython-android-cli/registry.json';data=p.read_bytes();v=json.loads(data)
 return {'sha256':hashlib.sha256(data).hexdigest(),'size':len(data),'artifact_count':len(v.get('artifacts',[])),'owned_path_count':len(v.get('owned_paths',[])),'value':v}
def transactions(root:Path)->list[dict[str,Any]]:
 tx=root/'.cpython-android-cli/transactions'
 if not tx.is_dir():return []
 return [{'name':p.name,'journal':read_json(p/'journal.json') if (p/'journal.json').is_file() else None} for p in sorted(x for x in tx.iterdir() if x.is_dir())]
def record_snapshot(prefix:Path,row:dict[str,Any])->dict[str,Any]:
 s=snapshot(prefix/row['path']);r={'relative':row['path'],'type':s.get('type'),'mode':s.get('mode')}
 if row['type']=='regular':r.update(size=s.get('size'),sha256=s.get('sha256'))
 elif row['type']=='symlink':r['target']=s.get('target')
 return r
def owned_digest(root:Path,rows:list[dict[str,Any]])->str:
 records=[record_snapshot(root/'prefix',r) for r in sorted(rows,key=lambda x:x['path'])]
 return hashlib.sha256(cjson(records)).hexdigest()
def invoke_engine(*,runner:Path,engine:Path,contract:Path,root:Path,operation:str,output:Path,artifact:str|None=None)->dict[str,Any]:
 cmd=[sys.executable,'-I','-B','-S',str(runner),str(engine),'--installation-root',str(root),'--operation',operation,'--output',str(output)]
 if operation=='install':cmd+=['--contract-results',str(contract)]
 if artifact:cmd+=['--artifact',artifact]
 cp=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},check=False)
 output.parent.mkdir(parents=True,exist_ok=True);output.with_suffix('.log').write_text(cp.stdout);result=read_json(output)
 process={'returncode':cp.returncode,'result':result,'log':output.with_suffix('.log').name};write_json(output.with_name(output.stem+'-process.json'),process);return process
def clone_seed(seed:Path,dst:Path,probes:list[str])->dict[str,bool]:
 shutil.copytree(seed,dst,symlinks=True,copy_function=shutil.copy2)
 r={'root_inode_separate':seed.stat().st_ino!=dst.stat().st_ino,'registry_inode_separate':(seed/'.cpython-android-cli/registry.json').stat().st_ino!=(dst/'.cpython-android-cli/registry.json').stat().st_ino}
 for rel in probes:r['probe_'+rel.replace('/','_').replace('.','_')+'_inode_separate']=(seed/'prefix'/rel).lstat().st_ino!=(dst/'prefix'/rel).lstat().st_ino
 return r
def exact_match(s:dict[str,Any],row:dict[str,Any])->bool:
 if s.get('type')!=row.get('type') or s.get('mode')!=row.get('mode'):return False
 if row.get('type')=='regular':return s.get('size')==row.get('size') and s.get('sha256')==row.get('sha256')
 if row.get('type')=='symlink':return s.get('target')==row.get('target')
 return True
def mutate_owned(root:Path,row:dict[str,Any],name:str)->dict[str,Any]:
 p=root/'prefix'/row['path'];before=snapshot(p)
 if name.endswith('regular'):p.write_bytes(b'gate3b0-user-modified-regular\n');os.chmod(p,int(row['mode'],8))
 else:p.unlink();os.symlink('gate3b0-user-modified-target',p)
 return {'before':before,'after':snapshot(p)}
def create_sentinel(root:Path,name:str)->tuple[str,dict[str,Any]]:
 if name.endswith('file'):
  rel=UNOWNED_FILE;p=root/'prefix'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'gate3b0-unowned-file\n');os.chmod(p,0o600)
 else:
  rel=UNOWNED_DIR;p=root/'prefix'/rel;p.mkdir(parents=True,mode=0o700);q=p/'payload.txt';q.write_bytes(b'gate3b0-unowned-directory\n');os.chmod(q,0o600)
 return rel,snapshot(p)
def remaining_registered_leaves(root:Path,rows:list[dict[str,Any]])->list[str]:return sorted(r['path'] for r in rows if r['type']!='directory' and kind(root/'prefix'/r['path'])!='absent')

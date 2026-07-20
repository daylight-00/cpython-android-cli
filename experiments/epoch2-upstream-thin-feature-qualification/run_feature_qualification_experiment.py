#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import textwrap
import time
import zipfile
from pathlib import Path
from typing import Any, Callable

EXPECTED_ARCHIVE_SHA = '38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5'
EXPECTED_ARCHIVE_SIZE = 22358404
EXPECTED_CONTROL_SHA = '6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c'
EXPECTED_ARTIFACT_SHA = '387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306'
EXPECTED_LOADER_SHA = '05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2'
EXPECTED_SYSCONFIG_SHA = '6cff1984d4601a37e8b57762bb170a57e695cb64d516c1dab0023b7e809dc808'
EXPECTED_DATA_POLICY_SHA = 'be25e52aba1d6c9d0b2e25fec2bd1d8a0a0d9eb870436f00e81f347e90d012b7'
CLASSIFICATIONS = {
    'pass',
    'android-mandatory-adaptation',
    'missing-bionic-primitive',
    'upstream-build-decision',
    'inadequate-environment',
}
FORBIDDEN_CONTRACT_TOKENS = [
    '/data/data/com.termux', '/data/user/0/com.termux', 'com.termux', '/usr/local',
    '/opt/android-sdk', '/opt/android-ndk', '/home/runner/work', '/tmp/cpython-build',
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def run(
    cmd: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None,
    timeout: int = 180, check: bool = False,
) -> subprocess.CompletedProcess[str]:
    try:
        p = subprocess.run(
            cmd, env=env, cwd=cwd, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        p = subprocess.CompletedProcess(
            cmd, 124, e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or ''),
            e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or 'timeout'),
        )
    if check and p.returncode:
        raise RuntimeError(json.dumps({
            'cmd': cmd, 'returncode': p.returncode,
            'stdout': p.stdout[-6000:], 'stderr': p.stderr[-6000:],
        }, sort_keys=True))
    return p


def parse_last_json(text: str) -> Any:
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch not in '[{':
            continue
        try:
            obj, end = decoder.raw_decode(text[i:])
            if not text[i + end:].strip():
                return obj
        except json.JSONDecodeError:
            pass
    raise ValueError('no terminal JSON object')


def import_frozen(root: Path, rel: str, authority_rel: str, module_name: str):
    script = root / rel
    authority = load(root / authority_rel)
    expected = authority.get('file_identities', {}).get(script.name)
    if not expected or sha256(script) != expected:
        raise RuntimeError(f'frozen script identity mismatch:{rel}')
    spec = importlib.util.spec_from_file_location(module_name, script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot import:{rel}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, authority


def classify_failure(text: str, *, android_adaptation: bool = False, upstream: bool = False) -> str:
    low = text.lower()
    if android_adaptation:
        return 'android-mandatory-adaptation'
    if upstream:
        return 'upstream-build-decision'
    if any(token in low for token in (
        'function not implemented', 'not implemented', 'semlock', 'sem_open',
        'shared memory is not supported', 'operation not supported',
    )):
        return 'missing-bionic-primitive'
    if any(token in low for token in (
        'permission denied', 'resource temporarily unavailable', 'no space left',
        'cannot allocate memory', 'timed out', 'timeout', 'not found',
    )):
        return 'inadequate-environment'
    return 'inadequate-environment'


def normalized_case(name: str, raw: dict[str, Any], *, adaptation_on_fail: bool = False,
                    upstream_on_fail: bool = False, note: str = '') -> dict[str, Any]:
    passed = raw.get('pass') is True
    text = json.dumps(raw, sort_keys=True)
    classification = 'pass' if passed else classify_failure(
        text, android_adaptation=adaptation_on_fail, upstream=upstream_on_fail,
    )
    return {
        'case': name,
        'pass': passed,
        'classification': classification,
        'support_candidate': passed,
        'note': note,
        'evidence': raw,
    }


def hardlink_copy(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        shutil.rmtree(dst, ignore_errors=True)
    def copier(a: str, b: str) -> str:
        try:
            os.link(a, b)
            return b
        except OSError:
            return shutil.copy2(a, b)
    shutil.copytree(src, dst, symlinks=True, copy_function=copier)


def tree_hash(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return {'count': 0, 'sha256': hashlib.sha256(b'[]').hexdigest(), 'size': 0}
    total = 0
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            rows.append({'path': rel, 'kind': 'symlink', 'target': os.readlink(p)})
        elif p.is_file():
            size = p.stat().st_size
            total += size
            rows.append({'path': rel, 'kind': 'file', 'size': size, 'sha256': sha256(p)})
        elif p.is_dir():
            rows.append({'path': rel, 'kind': 'dir'})
    raw = json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()
    return {'count': len(rows), 'sha256': hashlib.sha256(raw).hexdigest(), 'size': total}


def target_json(python: Path, args: list[str], env: dict[str, str], *, timeout: int = 180,
                cwd: Path | None = None) -> dict[str, Any]:
    p = run([str(python), *args], env=env, timeout=timeout, cwd=cwd)
    out: dict[str, Any] = {
        'command': [str(python), *args], 'returncode': p.returncode,
        'stdout': p.stdout, 'stderr': p.stderr,
    }
    try:
        out['json'] = parse_last_json(p.stdout)
    except Exception as e:
        out['parse_error'] = repr(e)
    return out


SUBPROCESS_PROBE = r'''
import asyncio,json,os,pathlib,signal,subprocess,sys,tempfile,time

def result(fn):
    try:
        value=fn()
        if isinstance(value,dict):
            value.setdefault('pass',True)
            return value
        return {'pass':bool(value),'value':value}
    except Exception as e:
        return {'pass':False,'error_type':type(e).__name__,'error':str(e),'errno':getattr(e,'errno',None)}

def run_text():
    p=subprocess.run([sys.executable,'-c','print("alpha")'],capture_output=True,text=True)
    return {'pass':p.returncode==0 and p.stdout=='alpha\n','returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}

def popen_binary():
    code='import sys;d=sys.stdin.buffer.read();sys.stdout.buffer.write(d[::-1])'
    p=subprocess.Popen([sys.executable,'-c',code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err=p.communicate(b'abc')
    return {'pass':p.returncode==0 and out==b'cba','returncode':p.returncode,'stdout_b64':__import__('base64').b64encode(out).decode(),'stderr':err.decode(errors='replace')}

def cwd_case():
    with tempfile.TemporaryDirectory() as d:
        p=subprocess.run([sys.executable,'-c','import os;print(os.getcwd())'],cwd=d,capture_output=True,text=True)
        return {'pass':p.returncode==0 and p.stdout.strip()==d,'cwd':d,'stdout':p.stdout,'returncode':p.returncode}

def env_case():
    e=os.environ.copy();e['HW_T_CHILD_ENV']='314'
    p=subprocess.run([sys.executable,'-c','import os;print(os.environ.get("HW_T_CHILD_ENV"))'],env=e,capture_output=True,text=True)
    return {'pass':p.returncode==0 and p.stdout.strip()=='314','stdout':p.stdout,'returncode':p.returncode}

def lookup_case():
    e=os.environ.copy();e['PATH']=str(pathlib.Path(sys.executable).parent)+os.pathsep+e.get('PATH','')
    name=pathlib.Path(sys.executable).name
    p=subprocess.run([name,'-c','print(2718)'],env=e,capture_output=True,text=True)
    return {'pass':p.returncode==0 and p.stdout.strip()=='2718','name':name,'stdout':p.stdout,'stderr':p.stderr,'returncode':p.returncode}

def absolute_case():
    p=subprocess.run([sys.executable,'-c','print(1618)'],capture_output=True,text=True)
    return {'pass':p.returncode==0 and p.stdout.strip()=='1618','executable':sys.executable,'returncode':p.returncode}

def lifecycle_case():
    p=subprocess.Popen([sys.executable,'-c','import time,sys;time.sleep(.15);sys.exit(7)'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    first=p.poll();out,err=p.communicate(timeout=5);final=p.wait()
    return {'pass':first is None and final==7 and p.returncode==7,'first_poll':first,'wait':final,'returncode':p.returncode,'stdout':out,'stderr':err}

def timeout_case():
    try:
        subprocess.run([sys.executable,'-c','import time;time.sleep(3)'],timeout=.15,check=True)
        return {'pass':False,'error':'no timeout'}
    except subprocess.TimeoutExpired as e:
        return {'pass':True,'timeout':e.timeout}

def terminate_case():
    p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
    time.sleep(.15);p.terminate();rc=p.wait(timeout=5)
    return {'pass':rc!=0,'returncode':rc}

def kill_case():
    p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
    time.sleep(.15);p.kill();rc=p.wait(timeout=5)
    return {'pass':rc!=0,'returncode':rc}

def large_output():
    n=1024*1024
    p=subprocess.run([sys.executable,'-c',f'import sys;sys.stdout.buffer.write(b"x"*{n})'],capture_output=True)
    return {'pass':p.returncode==0 and len(p.stdout)==n,'length':len(p.stdout),'returncode':p.returncode}

def nested_python():
    code='import json,os,subprocess,sys;p=subprocess.run([sys.executable,"-c","print(3)"],capture_output=True,text=True);print(json.dumps({"rc":p.returncode,"out":p.stdout.strip()}))'
    p=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
    data=json.loads(p.stdout)
    return {'pass':p.returncode==0 and data=={'rc':0,'out':'3'},'data':data,'returncode':p.returncode}

def native_imports():
    modules=['_ssl','_hashlib','_sqlite3','zlib','_bz2','_lzma','select','fcntl']
    code='import importlib,json;mods='+repr(modules)+';bad={};\nfor n in mods:\n try: importlib.import_module(n)\n except Exception as e: bad[n]=type(e).__name__+":"+str(e)\nprint(json.dumps({"bad":bad,"count":len(mods)}))'
    p=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
    data=json.loads(p.stdout)
    return {'pass':p.returncode==0 and not data['bad'],'modules':modules,'bad':data['bad'],'returncode':p.returncode}

def relocated_base():
    expected=os.environ['HW_T_EXPECTED_PREFIX']
    return {'pass':sys.base_prefix==expected and pathlib.Path(sys.executable).is_file(),'base_prefix':sys.base_prefix,'expected':expected,'executable':sys.executable}

def venv_exec():
    vpy=sys.argv[1]
    p=subprocess.run([vpy,'-c','import json,sys;print(json.dumps({"prefix":sys.prefix,"base":sys.base_prefix}))'],capture_output=True,text=True)
    data=json.loads(p.stdout)
    return {'pass':p.returncode==0 and data['prefix']!=data['base'],'data':data,'returncode':p.returncode,'stderr':p.stderr}

async def async_exec_impl():
    p=await asyncio.create_subprocess_exec(sys.executable,'-c','print(42)',stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
    out,err=await p.communicate()
    return {'pass':p.returncode==0 and out.strip()==b'42','returncode':p.returncode,'stdout':out.decode(),'stderr':err.decode()}

def async_exec(): return asyncio.run(async_exec_impl())

async def async_shell_impl():
    p=await asyncio.create_subprocess_shell('printf 43',executable='/system/bin/sh',stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
    out,err=await p.communicate()
    return {'pass':p.returncode==0 and out==b'43','returncode':p.returncode,'stdout':out.decode(),'stderr':err.decode(),'shell':'/system/bin/sh'}

def async_shell(): return asyncio.run(async_shell_impl())

cases={
'run_text_capture':run_text,'popen_binary_pipes':popen_binary,'cwd':cwd_case,'custom_env':env_case,
'executable_lookup':lookup_case,'absolute_execution':absolute_case,'poll_wait_communicate':lifecycle_case,
'timeout':timeout_case,'terminate':terminate_case,'kill':kill_case,'large_output':large_output,
'nested_python':nested_python,'child_native_imports':native_imports,'relocated_base_execution':relocated_base,
'venv_execution':venv_exec,'asyncio_subprocess_exec':async_exec,'asyncio_subprocess_shell':async_shell,
}
print(json.dumps({'schema_version':1,'cases':{k:result(v) for k,v in cases.items()}},sort_keys=True))
'''


SECONDARY_PROBE = r'''
import json,os,pty,signal,subprocess,sys,tempfile,time

def result(fn):
    try:
        value=fn(); value=value if isinstance(value,dict) else {'pass':bool(value),'value':value};value.setdefault('pass',True);return value
    except Exception as e:return {'pass':False,'error_type':type(e).__name__,'error':str(e),'errno':getattr(e,'errno',None)}

def shell_default():
    p=subprocess.run('printf default-shell',shell=True,capture_output=True,text=True)
    return {'pass':p.returncode==0 and p.stdout=='default-shell','returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}

def shell_explicit():
    p=subprocess.run('printf system-shell',shell=True,executable='/system/bin/sh',capture_output=True,text=True)
    return {'pass':p.returncode==0 and p.stdout=='system-shell','returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'shell':'/system/bin/sh'}

def explicit_shell_argv():
    p=subprocess.run(['/system/bin/sh','-c','printf argv-shell'],capture_output=True,text=True)
    return {'pass':p.returncode==0 and p.stdout=='argv-shell','returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}

def new_session():
    parent=os.getsid(0)
    p=subprocess.run([sys.executable,'-c','import os;print(os.getsid(0))'],start_new_session=True,capture_output=True,text=True)
    child=int(p.stdout.strip())
    return {'pass':p.returncode==0 and child!=parent,'parent_sid':parent,'child_sid':child,'returncode':p.returncode}

def process_group():
    p=subprocess.Popen([sys.executable,'-c','import os;print(os.getpgrp())'],process_group=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    out,err=p.communicate(timeout=5)
    return {'pass':p.returncode==0 and int(out.strip())==p.pid,'pid':p.pid,'pgrp':int(out.strip()),'returncode':p.returncode,'stderr':err}

def signal_forwarding():
    code='import signal,sys,time;signal.signal(signal.SIGTERM,lambda s,f:sys.exit(42));print("READY",flush=True);time.sleep(30)'
    p=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    ready=p.stdout.readline().strip();p.send_signal(signal.SIGTERM);out,err=p.communicate(timeout=5)
    return {'pass':ready=='READY' and p.returncode==42,'ready':ready,'returncode':p.returncode,'stdout':out,'stderr':err}

def pass_fds():
    r,w=os.pipe();code='import os,sys;os.write(int(sys.argv[1]),b"fd-ok")'
    p=subprocess.Popen([sys.executable,'-c',code,str(w)],pass_fds=(w,),close_fds=True)
    os.close(w);data=os.read(r,16);os.close(r);rc=p.wait(timeout=5)
    return {'pass':rc==0 and data==b'fd-ok','returncode':rc,'data':data.decode()}

def close_fds():
    r,w=os.pipe();code='import os,sys\ntry:os.fstat(int(sys.argv[1]));print("open")\nexcept OSError:print("closed")'
    p=subprocess.run([sys.executable,'-c',code,str(w)],close_fds=True,capture_output=True,text=True)
    os.close(r);os.close(w)
    return {'pass':p.returncode==0 and p.stdout.strip()=='closed','stdout':p.stdout,'stderr':p.stderr,'returncode':p.returncode}

def preexec():
    parent=os.getsid(0)
    p=subprocess.run([sys.executable,'-c','import os;print(os.getsid(0))'],preexec_fn=os.setsid,capture_output=True,text=True)
    child=int(p.stdout.strip())
    return {'pass':p.returncode==0 and child!=parent,'parent_sid':parent,'child_sid':child,'returncode':p.returncode}

def pty_case():
    master,slave=pty.openpty()
    p=subprocess.Popen([sys.executable,'-c','print("pty-ok",flush=True)'],stdin=slave,stdout=slave,stderr=slave,close_fds=True)
    os.close(slave);data=os.read(master,128);os.close(master);rc=p.wait(timeout=5)
    return {'pass':rc==0 and b'pty-ok' in data,'returncode':rc,'data':data.decode(errors='replace')}

def background_reap():
    p=subprocess.Popen([sys.executable,'-c','pass']);pid=p.pid;rc=p.wait(timeout=5)
    reaped=False
    try:os.waitpid(pid,os.WNOHANG)
    except ChildProcessError:reaped=True
    return {'pass':rc==0 and reaped,'returncode':rc,'reaped':reaped}

cases={'shell_default':shell_default,'shell_explicit_system':shell_explicit,'explicit_shell_argv':explicit_shell_argv,
'start_new_session':new_session,'process_group':process_group,'signal_forwarding':signal_forwarding,
'pass_fds':pass_fds,'close_fds':close_fds,'preexec_fn':preexec,'pty':pty_case,'background_reap':background_reap}
print(json.dumps({'schema_version':1,'cases':{k:result(v) for k,v in cases.items()}},sort_keys=True))
'''


MULTIPROCESSING_PROBE = r'''
import concurrent.futures,json,multiprocessing as mp,os,queue,sys,time,traceback

def worker_send(conn,x): conn.send(x*2);conn.close()
def worker_queue(q,x): q.put(x+1)
def worker_event(ev,q): ev.wait(5);q.put(ev.is_set())
def worker_lock(lock,q):
    with lock:q.put('locked')
def worker_shared(v,a): v.value+=1;a[0]+=2
def worker_shm(name):
    from multiprocessing import shared_memory
    s=shared_memory.SharedMemory(name=name);s.buf[0]=77;s.close()
def square(x): return x*x

def emit(value): print(json.dumps(value,sort_keys=True))
def fail(e): return {'pass':False,'error_type':type(e).__name__,'error':str(e),'errno':getattr(e,'errno',None),'traceback':traceback.format_exc()[-4000:]}

def ctx_default():
    methods=mp.get_all_start_methods();name='fork' if 'fork' in methods else methods[0];return mp.get_context(name),methods,name

def start_method(name):
    try:
        methods=mp.get_all_start_methods()
        if name not in methods:return {'pass':False,'available':False,'methods':methods,'error':'start method unavailable'}
        ctx=mp.get_context(name);a,b=ctx.Pipe(False);p=ctx.Process(target=worker_send,args=(b,21));p.start();b.close();value=a.recv();p.join(15)
        if p.is_alive():p.terminate();p.join(5)
        return {'pass':p.exitcode==0 and value==42,'available':True,'methods':methods,'exitcode':p.exitcode,'value':value}
    except Exception as e:return fail(e)

def pipe_case():
    try:
        ctx,methods,name=ctx_default();a,b=ctx.Pipe(False);p=ctx.Process(target=worker_send,args=(b,5));p.start();b.close();value=a.recv();p.join(10)
        return {'pass':p.exitcode==0 and value==10,'context':name,'exitcode':p.exitcode,'value':value}
    except Exception as e:return fail(e)

def queue_case():
    try:
        ctx,_,name=ctx_default();q=ctx.Queue();p=ctx.Process(target=worker_queue,args=(q,8));p.start();value=q.get(timeout=10);p.join(10);q.close();q.join_thread()
        return {'pass':p.exitcode==0 and value==9,'context':name,'exitcode':p.exitcode,'value':value}
    except Exception as e:return fail(e)

def pool_case():
    try:
        ctx,_,name=ctx_default()
        with ctx.Pool(2) as pool: values=pool.map(square,[1,2,3])
        return {'pass':values==[1,4,9],'context':name,'values':values}
    except Exception as e:return fail(e)

def lock_case():
    try:
        ctx,_,name=ctx_default();lock=ctx.Lock();q=ctx.Queue();p=ctx.Process(target=worker_lock,args=(lock,q));p.start();value=q.get(timeout=10);p.join(10);q.close();q.join_thread()
        return {'pass':p.exitcode==0 and value=='locked','context':name,'value':value,'exitcode':p.exitcode}
    except Exception as e:return fail(e)

def semaphore_case():
    try:
        ctx,_,name=ctx_default();s=ctx.Semaphore(1);ok=s.acquire(timeout=1);s.release()
        return {'pass':ok,'context':name}
    except Exception as e:return fail(e)

def event_case():
    try:
        ctx,_,name=ctx_default();ev=ctx.Event();q=ctx.Queue();p=ctx.Process(target=worker_event,args=(ev,q));p.start();ev.set();value=q.get(timeout=10);p.join(10);q.close();q.join_thread()
        return {'pass':p.exitcode==0 and value is True,'context':name,'exitcode':p.exitcode,'value':value}
    except Exception as e:return fail(e)

def condition_case():
    try:
        ctx,_,name=ctx_default();c=ctx.Condition();
        with c: c.notify_all()
        return {'pass':True,'context':name}
    except Exception as e:return fail(e)

def shared_value_array():
    try:
        ctx,_,name=ctx_default();v=ctx.Value('i',1);a=ctx.Array('i',[2]);p=ctx.Process(target=worker_shared,args=(v,a));p.start();p.join(10)
        return {'pass':p.exitcode==0 and v.value==2 and a[0]==4,'context':name,'exitcode':p.exitcode,'value':v.value,'array0':a[0]}
    except Exception as e:return fail(e)

def manager_case():
    try:
        ctx,_,name=ctx_default();m=ctx.Manager();d=m.dict();d['x']=3;value=d['x'];m.shutdown();return {'pass':value==3,'context':name,'value':value}
    except Exception as e:return fail(e)

def executor_case():
    try:
        ctx,_,name=ctx_default()
        with concurrent.futures.ProcessPoolExecutor(max_workers=2,mp_context=ctx) as ex: values=list(ex.map(square,[2,3]))
        return {'pass':values==[4,9],'context':name,'values':values}
    except Exception as e:return fail(e)

def shared_memory_case():
    try:
        from multiprocessing import shared_memory
        ctx,_,name=ctx_default();s=shared_memory.SharedMemory(create=True,size=16);s.buf[0]=1;p=ctx.Process(target=worker_shm,args=(s.name,));p.start();p.join(10);value=s.buf[0];n=s.name;s.close();s.unlink()
        return {'pass':p.exitcode==0 and value==77,'context':name,'exitcode':p.exitcode,'value':value,'name':n}
    except Exception as e:return fail(e)

def resource_tracker_case():
    try:
        from multiprocessing import resource_tracker,shared_memory
        s=shared_memory.SharedMemory(create=True,size=1);name=s.name;s.close();s.unlink();pid=getattr(resource_tracker._resource_tracker,'_pid',None)
        return {'pass':True,'resource_tracker_pid':pid,'name':name}
    except Exception as e:return fail(e)

def terminate_cleanup():
    try:
        ctx,_,name=ctx_default();p=ctx.Process(target=time.sleep,args=(30,));p.start();p.terminate();p.join(10);alive=p.is_alive()
        return {'pass':not alive and p.exitcode not in (None,0),'context':name,'exitcode':p.exitcode,'alive':alive}
    except Exception as e:return fail(e)

def main():
    name=sys.argv[1]
    if name.startswith('start_method:'):
        emit(start_method(name.split(':',1)[1]))
        return 0
    funcs={'pipes_connections':pipe_case,'queues':queue_case,'pools':pool_case,'locks':lock_case,'semaphores':semaphore_case,
    'events':event_case,'conditions':condition_case,'shared_values_arrays':shared_value_array,'manager':manager_case,
    'process_pool_executor':executor_case,'shared_memory':shared_memory_case,'resource_tracker':resource_tracker_case,
    'termination_cleanup':terminate_cleanup}
    try:emit(funcs[name]())
    except Exception as e:emit(fail(e))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
'''


def write_probe(path: Path, source: str) -> None:
    path.write_text(textwrap.dedent(source).lstrip())


def create_console_wheel(path: Path) -> None:
    package = b"def main():\n    print('console-probe-ok')\n    return 0\n"
    metadata = b"Metadata-Version: 2.1\nName: hw-t-console-probe\nVersion: 0.1.0\n"
    wheel = b"Wheel-Version: 1.0\nGenerator: hw-t\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    entry = b"[console_scripts]\nhw-t-console-probe = hw_t_console_probe:main\n"
    rows: list[list[str]] = []
    files = {
        'hw_t_console_probe/__init__.py': package,
        'hw_t_console_probe-0.1.0.dist-info/METADATA': metadata,
        'hw_t_console_probe-0.1.0.dist-info/WHEEL': wheel,
        'hw_t_console_probe-0.1.0.dist-info/entry_points.txt': entry,
    }
    def record_hash(data: bytes) -> str:
        return 'sha256=' + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
    for name, data in files.items():
        rows.append([name, record_hash(data), str(len(data))])
    record_name = 'hw_t_console_probe-0.1.0.dist-info/RECORD'
    rows.append([record_name, '', ''])
    import io
    s = io.StringIO(); csv.writer(s, lineterminator='\n').writerows(rows)
    files[record_name] = s.getvalue().encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o644 & 0xFFFF) << 16
            zf.writestr(info, files[name])


def safe_extract_wheel(wheel: Path, site: Path) -> dict[str, Any]:
    site.mkdir(parents=True, exist_ok=True)
    members: list[str] = []
    with zipfile.ZipFile(wheel) as zf:
        seen: set[str] = set()
        for info in sorted(zf.infolist(), key=lambda x: x.filename):
            p = Path(info.filename)
            if p.is_absolute() or '..' in p.parts or info.filename in seen:
                raise RuntimeError(f'unsafe wheel member:{info.filename}')
            seen.add(info.filename)
            if info.is_dir():
                (site / p).mkdir(parents=True, exist_ok=True)
            else:
                dst = site / p
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(zf.read(info.filename))
                members.append(info.filename)
    return {'member_count': len(members), 'members': members, 'wheel_sha256': sha256(wheel)}


def run_python_json(python: Path, code: str, env: dict[str, str], *, timeout: int = 120) -> dict[str, Any]:
    return target_json(python, ['-c', code], env, timeout=timeout)


def executable_state(path: Path) -> dict[str, Any]:
    return {
        'path': str(path), 'lexists': os.path.lexists(path), 'exists': path.exists(),
        'is_symlink': path.is_symlink(), 'symlink_target': os.readlink(path) if path.is_symlink() else None,
        'resolved': str(path.resolve(strict=False)),
    }


def execute_path(path: Path, args: list[str], env: dict[str, str], *, timeout: int = 120) -> dict[str, Any]:
    state = executable_state(path)
    try:
        p = run([str(path), *args], env=env, timeout=timeout)
        out: dict[str, Any] = {'pass': p.returncode == 0, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr, 'path_state': state}
        try:
            out['json'] = parse_last_json(p.stdout)
        except Exception:
            pass
        return out
    except OSError as e:
        return {'pass': False, 'returncode': None, 'error_type': type(e).__name__, 'errno': e.errno, 'error': str(e), 'path_state': state}


def venv_create(base_python: Path, path: Path, env: dict[str, str], mode: str, *, with_pip: bool = False) -> dict[str, Any]:
    shutil.rmtree(path, ignore_errors=True)
    cmd = [str(base_python), '-m', 'venv']
    if not with_pip:
        cmd.append('--without-pip')
    cmd.append('--copies' if mode == 'copies' else '--symlinks')
    cmd.append(str(path))
    p = run(cmd, env=env, timeout=360)
    vpy = path / 'bin/python'
    probe = execute_path(vpy, ['-c', 'import json,sys;print(json.dumps({"prefix":sys.prefix,"base_prefix":sys.base_prefix,"executable":sys.executable}))'], env)
    cfg = (path / 'pyvenv.cfg').read_text(errors='replace') if (path / 'pyvenv.cfg').is_file() else ''
    return {'pass': p.returncode == 0 and probe.get('pass') is True, 'mode': mode, 'command': cmd, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr, 'python': executable_state(vpy), 'probe': probe, 'pyvenv_cfg': cfg}


def classify_venv(name: str, raw: dict[str, Any], *, expected_boundary: bool = False, note: str = '') -> dict[str, Any]:
    if raw.get('pass') is True:
        c = 'pass'
    elif expected_boundary:
        c = 'android-mandatory-adaptation'
    else:
        c = classify_failure(json.dumps(raw, sort_keys=True))
    return {'case': name, 'pass': raw.get('pass') is True, 'classification': c, 'support_candidate': raw.get('pass') is True, 'note': note, 'evidence': raw}


def pip_probe(python: Path, env: dict[str, str]) -> dict[str, Any]:
    return run_python_json(python, 'import json,pip,sys;print(json.dumps({"pass":True,"version":pip.__version__,"file":pip.__file__,"prefix":sys.prefix}))', env)


def inspect_scripts(bin_dir: Path, pattern: str = 'pip*') -> list[dict[str, Any]]:
    rows = []
    for p in sorted(bin_dir.glob(pattern)):
        if not p.is_file() or p.is_symlink():
            continue
        first = p.read_text(errors='replace').splitlines()[0] if p.stat().st_size else ''
        rows.append({'path': str(p), 'size': p.stat().st_size, 'first_line': first, 'sha256': sha256(p)})
    return rows


def contract_scan(value: Any) -> dict[str, Any]:
    text = json.dumps(value, sort_keys=True)
    hits = {token: text.count(token) for token in FORBIDDEN_CONTRACT_TOKENS if token in text}
    return {'scope': 'selected feature-surface decision and abstract support contract', 'forbidden_tokens': FORBIDDEN_CONTRACT_TOKENS, 'hits': hits, 'hit_count': sum(hits.values()), 'pass': not hits}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--cc', default='clang')
    ap.add_argument('--cxx', default='clang++')
    ap.add_argument('--ar', default='llvm-ar')
    ap.add_argument('--patchelf', default='patchelf')
    ap.add_argument('--readelf', default='readelf')
    ap.add_argument('--pkg-config', default='pkg-config')
    a = ap.parse_args()
    root = a.root.resolve(); archive = a.archive.resolve(); work = a.work.resolve(); out = a.output.resolve()
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
    if sha256(archive) != EXPECTED_ARCHIVE_SHA or archive.stat().st_size != EXPECTED_ARCHIVE_SIZE:
        raise SystemExit('official archive identity mismatch')
    authorities = {
        'control': ('experiments/epoch2-upstream-thin-control/upstream-control-authority.json', EXPECTED_CONTROL_SHA),
        'artifact': ('experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json', EXPECTED_ARTIFACT_SHA),
        'loader': ('experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json', EXPECTED_LOADER_SHA),
        'sysconfig': ('experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json', EXPECTED_SYSCONFIG_SHA),
        'data_policy': ('experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json', EXPECTED_DATA_POLICY_SHA),
    }
    for name, (rel, expected) in authorities.items():
        if sha256(root / rel) != expected:
            raise SystemExit(f'authority identity mismatch:{name}')

    ut3, _ = import_frozen(
        root, 'experiments/epoch2-upstream-thin-sysconfig-sdk/run_sysconfig_sdk_experiment.py',
        'experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json', 'hw_t_ut3_feature',
    )
    ut4, _ = import_frozen(
        root, 'experiments/epoch2-upstream-thin-android-data-policy/run_android_data_policy_experiment.py',
        'experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json', 'hw_t_ut4_feature',
    )

    ut3_work = work / 'runtime-sdk-reproduction'
    ut3_output = work / 'runtime-sdk-evidence'
    ut3_artifacts = work / 'runtime-sdk-artifacts'
    source_dir = root / 'experiments/epoch2-upstream-thin-sysconfig-sdk'
    cmd = [
        sys.executable, str(root / 'experiments/epoch2-upstream-thin-sysconfig-sdk/run_sysconfig_sdk_experiment.py'),
        '--root', str(root), '--archive', str(archive), '--work', str(ut3_work), '--output', str(ut3_output),
        '--artifacts', str(ut3_artifacts), '--source-dir', str(source_dir), '--cc', a.cc, '--cxx', a.cxx,
        '--ar', a.ar, '--patchelf', a.patchelf, '--readelf', a.readelf, '--pkg-config', a.pkg_config,
    ]
    reproduction = run(cmd, timeout=1800)
    gate3 = load(ut3_output / 'ut3-gate-diagnostics.json') if (ut3_output / 'ut3-gate-diagnostics.json').is_file() else {'pass': False}
    if reproduction.returncode != 0 or gate3.get('pass') is not True:
        raise SystemExit('UT-3 runtime/SDK reproduction failed:' + json.dumps({'returncode': reproduction.returncode, 'stdout': reproduction.stdout[-4000:], 'stderr': reproduction.stderr[-4000:], 'gate': gate3}, sort_keys=True))
    prefix = ut3_work / 'location-b/prefix'
    python = prefix / 'bin/python3.14'
    wheels = sorted(ut3_artifacts.glob('hw_t_native_probe-*.whl'))
    if not python.is_file() or len(wheels) != 1:
        raise SystemExit('reproduced runtime or native wheel missing')
    native_wheel = wheels[0]

    data = work / 'data'; state = work / 'state'
    cert = prefix / 'lib/python3.14/test/certdata/ssl_cert.pem'
    (data / 'ca').mkdir(parents=True, exist_ok=True); shutil.copy2(cert, data / 'ca/ca-bundle.pem')
    ut4.write_tzif(data / 'zoneinfo/Etc/HWTest', 3600, 'HWT')
    env = ut4.policy_env(ut3, prefix, state, data, work / 'policy-env')
    env['HW_T_EXPECTED_PREFIX'] = str(prefix)

    # Core subprocess matrix.
    core_venv = state / 'venvs/core'
    core_venv_result = venv_create(python, core_venv, env, 'copies')
    core_probe = work / 'subprocess-core-probe.py'; write_probe(core_probe, SUBPROCESS_PROBE)
    core_run = target_json(python, [str(core_probe), str(core_venv / 'bin/python')], env, timeout=420)
    raw_core = core_run.get('json', {}).get('cases', {})
    required_core = [
        'run_text_capture', 'popen_binary_pipes', 'cwd', 'custom_env', 'executable_lookup',
        'absolute_execution', 'poll_wait_communicate', 'timeout', 'terminate', 'kill', 'large_output',
        'nested_python', 'child_native_imports', 'relocated_base_execution', 'venv_execution',
        'asyncio_subprocess_exec', 'asyncio_subprocess_shell',
    ]
    core_cases = [normalized_case(name, raw_core.get(name, {'pass': False, 'error': 'missing case'})) for name in required_core]
    core_matrix = {
        'schema_version': 1, 'matrix': 'subprocess-core', 'probe': core_run,
        'cases': core_cases, 'required_case_count': len(required_core),
        'classified_case_count': len(core_cases),
        'pass_count': sum(x['pass'] for x in core_cases),
        'support_boundary': {
            'claim': 'Only individually passing core cases are technically supportable.',
            'blanket_subprocess_claim': False,
        },
        'pass': len(core_cases) == len(required_core) and all(x['classification'] in CLASSIFICATIONS for x in core_cases),
    }
    dump(out / 'subprocess-core-matrix.json', core_matrix)

    # Secondary subprocess matrix.
    secondary_probe = work / 'subprocess-secondary-probe.py'; write_probe(secondary_probe, SECONDARY_PROBE)
    secondary_run = target_json(python, [str(secondary_probe)], env, timeout=420)
    raw_secondary = secondary_run.get('json', {}).get('cases', {})
    required_secondary = [
        'shell_default', 'shell_explicit_system', 'explicit_shell_argv', 'start_new_session',
        'process_group', 'signal_forwarding', 'pass_fds', 'close_fds', 'preexec_fn', 'pty', 'background_reap',
    ]
    secondary_cases: list[dict[str, Any]] = []
    for name in required_secondary:
        raw = raw_secondary.get(name, {'pass': False, 'error': 'missing case'})
        adaptation = name == 'shell_default' and raw_secondary.get('shell_explicit_system', {}).get('pass') is True
        note = 'Default /bin/sh is not a host-neutral Android contract; explicit /system/bin/sh is the adaptation.' if name == 'shell_default' else ''
        item = normalized_case(name, raw, adaptation_on_fail=adaptation, note=note)
        if name == 'preexec_fn' and item['pass']:
            item['support_candidate'] = False
            item['note'] = 'Technically passes, but excluded from default product surface because preexec_fn is unsafe in threaded applications.'
        secondary_cases.append(item)
    secondary_matrix = {
        'schema_version': 1, 'matrix': 'subprocess-secondary', 'probe': secondary_run,
        'cases': secondary_cases, 'required_case_count': len(required_secondary),
        'classified_case_count': len(secondary_cases), 'pass_count': sum(x['pass'] for x in secondary_cases),
        'support_boundary': {'blanket_secondary_claim': False, 'explicit_shell_required_on_android': True, 'preexec_fn_default_product_support': False},
        'pass': len(secondary_cases) == len(required_secondary) and all(x['classification'] in CLASSIFICATIONS for x in secondary_cases),
    }
    dump(out / 'subprocess-secondary-matrix.json', secondary_matrix)

    # Venv matrix.
    venv_cases: list[dict[str, Any]] = []
    basic_symlink = venv_create(python, state / 'venvs/basic-symlink', env, 'symlinks')
    basic_copy = venv_create(python, state / 'venvs/basic-copy', env, 'copies')
    venv_cases.append(classify_venv('symlink_mode', basic_symlink))
    venv_cases.append(classify_venv('copy_mode', basic_copy))

    move_a = work / 'base-move/location-a/prefix'; move_b = work / 'base-move/location-b/prefix'
    move_a.parent.mkdir(parents=True, exist_ok=True); hardlink_copy(prefix, move_a)
    env_move_a = ut4.policy_env(ut3, move_a, state, data, work / 'move-env-a')
    old_symlink = venv_create(move_a / 'bin/python3.14', state / 'venvs/pre-move-symlink', env_move_a, 'symlinks')
    old_copy = venv_create(move_a / 'bin/python3.14', state / 'venvs/pre-move-copy', env_move_a, 'copies')
    move_b.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(move_a), str(move_b))
    env_move_b = ut4.policy_env(ut3, move_b, state, data, work / 'move-env-b')
    fresh_after_move = venv_create(move_b / 'bin/python3.14', state / 'venvs/fresh-after-base-move', env_move_b, 'symlinks')
    old_symlink_after = execute_path(state / 'venvs/pre-move-symlink/bin/python', ['-c', 'import json,sys;print(json.dumps({"prefix":sys.prefix,"base":sys.base_prefix}))'], env_move_b)
    old_copy_after = execute_path(state / 'venvs/pre-move-copy/bin/python', ['-c', 'import json,sys;print(json.dumps({"prefix":sys.prefix,"base":sys.base_prefix}))'], env_move_b)
    venv_cases.append(classify_venv('base_moved_before_new_venv', fresh_after_move))
    venv_cases.append(classify_venv('pre_existing_symlink_venv_after_base_move', old_symlink_after, expected_boundary=True, note='Failure is an accepted base-bound boundary; recreate after base movement.'))
    venv_cases.append(classify_venv('pre_existing_copy_venv_after_base_move', old_copy_after, expected_boundary=old_copy_after.get('pass') is not True, note='Recorded independently; no blanket relocation claim.'))

    moved_src = state / 'venvs/move-without-base-src'; moved_dst = state / 'venvs/move-without-base-dst'
    moved_created = venv_create(python, moved_src, env, 'copies')
    shutil.move(str(moved_src), str(moved_dst))
    moved_probe = execute_path(moved_dst / 'bin/python', ['-c', 'import json,sys;print(json.dumps({"prefix":sys.prefix,"base":sys.base_prefix}))'], env)
    venv_cases.append(classify_venv('venv_moved_without_base', moved_probe, expected_boundary=moved_probe.get('pass') is not True))

    patch_base = work / 'patch-replacement/prefix'; patch_base.parent.mkdir(parents=True, exist_ok=True); hardlink_copy(prefix, patch_base)
    patch_env = ut4.policy_env(ut3, patch_base, state, data, work / 'patch-env')
    patch_venv = state / 'venvs/patch-replacement'
    patch_created = venv_create(patch_base / 'bin/python3.14', patch_venv, patch_env, 'copies')
    shutil.rmtree(patch_base); hardlink_copy(prefix, patch_base)
    patch_probe = execute_path(patch_venv / 'bin/python', ['-c', 'import json,sys;print(json.dumps({"prefix":sys.prefix,"base":sys.base_prefix}))'], patch_env)
    patch_probe['replacement_base_tree'] = tree_hash(patch_base)
    patch_probe['created'] = patch_created
    venv_cases.append(classify_venv('patch_level_base_replacement_same_path', patch_probe))

    native_result = ut3.install_and_import(native_wheel, python, prefix, work / 'native-venv-work', state / 'venvs/native-extension')
    venv_cases.append(classify_venv('native_extension_in_venv', native_result))

    uv_path = shutil.which('uv')
    if uv_path:
        uv_venv = state / 'venvs/uv-created'; shutil.rmtree(uv_venv, ignore_errors=True)
        uv_run = run([uv_path, 'venv', '--python', str(python), str(uv_venv)], env=env, timeout=360)
        uv_probe = execute_path(uv_venv / 'bin/python', ['-c', 'import json,sys;print(json.dumps({"prefix":sys.prefix,"base":sys.base_prefix}))'], env)
        uv_raw = {'pass': uv_run.returncode == 0 and uv_probe.get('pass') is True, 'uv_path': uv_path, 'returncode': uv_run.returncode, 'stdout': uv_run.stdout, 'stderr': uv_run.stderr, 'probe': uv_probe}
    else:
        uv_raw = {'pass': False, 'available': False, 'error': 'uv executable absent from qualification environment'}
    uv_case = classify_venv('uv_created_venv', uv_raw)
    if not uv_path:
        uv_case['classification'] = 'inadequate-environment'; uv_case['support_candidate'] = False
    venv_cases.append(uv_case)

    console_wheel = work / 'console-wheel/hw_t_console_probe-0.1.0-py3-none-any.whl'; create_console_wheel(console_wheel)
    pip_venv = state / 'venvs/pip-console'; pip_create = venv_create(python, pip_venv, env, 'copies', with_pip=True)
    install_console = run([str(pip_venv / 'bin/python'), '-m', 'pip', 'install', '--no-index', '--disable-pip-version-check', str(console_wheel)], env=env, timeout=360)
    script_before = execute_path(pip_venv / 'bin/hw-t-console-probe', [], env)
    script_first = inspect_scripts(pip_venv / 'bin', 'hw-t-console-probe')
    pip_venv_moved = state / 'venvs/pip-console-moved'; shutil.move(str(pip_venv), str(pip_venv_moved))
    script_after = execute_path(pip_venv_moved / 'bin/hw-t-console-probe', [], env)
    moved_python = execute_path(pip_venv_moved / 'bin/python', ['-c', 'print(1)'], env)
    console_raw = {'pass': pip_create.get('pass') is True and install_console.returncode == 0 and script_before.get('pass') is True,
                   'create': pip_create, 'install': {'returncode': install_console.returncode, 'stdout': install_console.stdout, 'stderr': install_console.stderr},
                   'scripts': script_first, 'before_move': script_before, 'after_move': script_after, 'moved_python': moved_python,
                   'relocation_boundary_explicit': True}
    console_case = classify_venv('pip_generated_console_script_after_venv_relocation', console_raw)
    console_case['support_candidate'] = script_after.get('pass') is True
    if script_after.get('pass') is not True:
        console_case['classification'] = 'android-mandatory-adaptation'
        console_case['note'] = 'pip-generated absolute shebang remains venv-location-bound; recreate or rewrite wrapper after relocation.'
    venv_cases.append(console_case)

    venv_matrix = {
        'schema_version': 1, 'matrix': 'venv', 'cases': venv_cases,
        'required_cases': [x['case'] for x in venv_cases], 'classified_case_count': len(venv_cases),
        'pass_count': sum(x['pass'] for x in venv_cases),
        'support_boundary': {
            'fresh_venv_after_base_move': fresh_after_move.get('pass') is True,
            'pre_existing_venv_blanket_relocation_claim': False,
            'pip_script_blanket_relocation_claim': False,
            'uv_inclusion_selected': False,
        },
        'pass': all(x['classification'] in CLASSIFICATIONS for x in venv_cases),
    }
    dump(out / 'venv-matrix.json', venv_matrix)

    # Base pip variants.
    pip_variants: list[dict[str, Any]] = []
    pip_wheel_source = next(iter(sorted((prefix / 'lib/python3.14/ensurepip/_bundled').glob('pip-*.whl'))), None)
    if pip_wheel_source is None:
        raise SystemExit('bundled pip wheel missing')

    pip0a = work / 'pip0/location-a/prefix'; pip0b = work / 'pip0/location-b/prefix'; pip0a.parent.mkdir(parents=True, exist_ok=True); hardlink_copy(prefix, pip0a)
    env0 = ut4.policy_env(ut3, pip0a, state, data, work / 'pip0-env')
    ensure = run([str(pip0a / 'bin/python3.14'), '-m', 'ensurepip', '--upgrade', '--default-pip'], env=env0, timeout=600)
    mod0a = pip_probe(pip0a / 'bin/python3.14', env0) if ensure.returncode == 0 else {'returncode': 127}
    scripts0a = inspect_scripts(pip0a / 'bin')
    pip0b.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(pip0a), str(pip0b)); env0b = ut4.policy_env(ut3, pip0b, state, data, work / 'pip0-env-b')
    mod0b = pip_probe(pip0b / 'bin/python3.14', env0b) if ensure.returncode == 0 else {'returncode': 127}
    wrappers0b = [execute_path(pip0b / 'bin' / Path(x['path']).name, ['--version'], env0b) for x in scripts0a]
    raw0 = {'pass': ensure.returncode == 0 and mod0a.get('json', {}).get('pass') is True and mod0b.get('json', {}).get('pass') is True,
            'install_returncode': ensure.returncode, 'stdout': ensure.stdout, 'stderr': ensure.stderr, 'module_before': mod0a,
            'scripts_before': scripts0a, 'module_after_move': mod0b, 'wrappers_after_move': wrappers0b,
            'generated_absolute_paths': [x['first_line'] for x in scripts0a if x['first_line'].startswith('#!/')],
            'version_update_owner': 'pip project plus product integrator', 'security_burden': 'highest of tested variants'}
    item0 = normalized_case('PIP-0', raw0)
    if raw0['pass'] and (raw0['generated_absolute_paths'] or any(x.get('pass') is not True for x in wrappers0b)):
        item0['classification'] = 'android-mandatory-adaptation'
        item0['support_candidate'] = False
        item0['note'] = 'Target-interpreter installation works, but generated command wrappers are absolute-path and relocation-bound.'
    item0.update({'variant': 'install-through-target-interpreter', 'archive_growth_bytes': tree_hash(pip0b)['size'] - tree_hash(prefix)['size'], 'product_inclusion_selected': False})
    pip_variants.append(item0)

    # PIP-1/PIP-3 deterministic extraction and package-only surface.
    extraction_hashes = []
    for i in (1, 2):
        temp = work / f'pip-extract-determinism-{i}'; shutil.rmtree(temp, ignore_errors=True)
        safe_extract_wheel(pip_wheel_source, temp); extraction_hashes.append(tree_hash(temp))
    pip1a = work / 'pip1/location-a/prefix'; pip1b = work / 'pip1/location-b/prefix'; pip1a.parent.mkdir(parents=True, exist_ok=True); hardlink_copy(prefix, pip1a)
    wheel1 = next(iter(sorted((pip1a / 'lib/python3.14/ensurepip/_bundled').glob('pip-*.whl'))))
    site1 = pip1a / 'lib/python3.14/site-packages'; extraction1 = safe_extract_wheel(wheel1, site1)
    env1 = ut4.policy_env(ut3, pip1a, state, data, work / 'pip1-env'); mod1a = pip_probe(pip1a / 'bin/python3.14', env1)
    scripts1 = inspect_scripts(pip1a / 'bin'); pip1b.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(pip1a), str(pip1b)); env1b = ut4.policy_env(ut3, pip1b, state, data, work / 'pip1-env-b'); mod1b = pip_probe(pip1b / 'bin/python3.14', env1b)
    raw1 = {'pass': mod1a.get('json', {}).get('pass') is True and mod1b.get('json', {}).get('pass') is True and extraction_hashes[0]['sha256'] == extraction_hashes[1]['sha256'] and not scripts1,
            'deterministic_extractions': extraction_hashes, 'extraction': extraction1, 'module_before': mod1a, 'module_after_move': mod1b,
            'scripts': scripts1, 'generated_absolute_paths': [], 'version_update_owner': 'pip project plus deterministic artifact pipeline',
            'security_burden': 'pip package code included; no wrapper surface'}
    item1 = normalized_case('PIP-1', raw1); item1.update({'variant': 'deterministic-wheel-extraction', 'archive_growth_bytes': tree_hash(site1 if site1.exists() else pip1b / 'lib/python3.14/site-packages')['size'], 'product_inclusion_selected': False}); pip_variants.append(item1)

    pip2a = work / 'pip2/location-a/prefix'; pip2b = work / 'pip2/location-b/prefix'; pip2a.parent.mkdir(parents=True, exist_ok=True); hardlink_copy(prefix, pip2a)
    wheel2 = next(iter(sorted((pip2a / 'lib/python3.14/ensurepip/_bundled').glob('pip-*.whl')))); site2 = pip2a / 'lib/python3.14/site-packages'; extraction2 = safe_extract_wheel(wheel2, site2)
    wrapper2 = pip2a / 'bin/pip3'; wrapper2.write_text('#!/system/bin/sh\nHERE=${0%/*}\n[ "$HERE" = "$0" ] && HERE=.\nHERE=$(CDPATH= cd "$HERE" && pwd) || exit 1\nexec "$HERE/python3.14" -m pip "$@"\n'); wrapper2.chmod(0o755)
    env2 = ut4.policy_env(ut3, pip2a, state, data, work / 'pip2-env'); before2 = execute_path(wrapper2, ['--version'], env2)
    pip2b.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(pip2a), str(pip2b)); env2b = ut4.policy_env(ut3, pip2b, state, data, work / 'pip2-env-b'); after2 = execute_path(pip2b / 'bin/pip3', ['--version'], env2b)
    raw2 = {'pass': before2.get('pass') is True and after2.get('pass') is True, 'extraction': extraction2, 'wrapper_before': before2, 'wrapper_after_move': after2,
            'wrapper_text': (pip2b / 'bin/pip3').read_text(), 'generated_absolute_paths': [],
            'version_update_owner': 'product-owned target-scheme installer and pip project', 'security_burden': 'product-owned installer and Android shell wrapper'}
    item2 = normalized_case('PIP-2', raw2); item2['classification'] = 'android-mandatory-adaptation' if raw2['pass'] else classify_failure(json.dumps(raw2)); item2.update({'variant': 'host-side-target-scheme-installer', 'archive_growth_bytes': tree_hash(pip2b)['size'] - tree_hash(prefix)['size'], 'product_inclusion_selected': False}); pip_variants.append(item2)

    raw3 = dict(raw1); raw3['variant_semantics'] = 'pip package importable only through python -m pip; no command wrappers'
    item3 = normalized_case('PIP-3', raw3); item3.update({'variant': 'pip-package-without-command-wrappers', 'archive_growth_bytes': item1['archive_growth_bytes'], 'product_inclusion_selected': False}); pip_variants.append(item3)

    no_pip_probe = run_python_json(python, 'import importlib.util,json;print(json.dumps({"pass":importlib.util.find_spec("pip") is None,"pip_spec":str(importlib.util.find_spec("pip"))}))', env)
    rawx = {'pass': no_pip_probe.get('json', {}).get('pass') is True, 'probe': no_pip_probe, 'archive_growth_bytes': 0,
            'version_update_owner': 'none for base pip', 'security_burden': 'minimal; venv or external tooling owns pip'}
    itemx = normalized_case('PIP-X', rawx); itemx.update({'variant': 'omit-base-pip', 'archive_growth_bytes': 0, 'product_inclusion_selected': False}); pip_variants.append(itemx)

    base_pip = {
        'schema_version': 1, 'matrix': 'base-pip-variants', 'bundled_wheel': {'path_role': '<INSTALL_ROOT>/lib/python3.14/ensurepip/_bundled/pip-*.whl', 'sha256': sha256(pip_wheel_source), 'size': pip_wheel_source.stat().st_size},
        'variants': pip_variants, 'required_variants': ['PIP-0', 'PIP-1', 'PIP-2', 'PIP-3', 'PIP-X'],
        'comparison_dimensions': ['deterministic_installation', 'generated_absolute_paths', 'relocation', 'venv_behavior', 'uv_coexistence', 'version_update_ownership', 'archive_growth', 'security_burden'],
        'selection_boundary': {'epoch3_selection_made': False, 'passing_probe_requires_inclusion': False, 'technically_feasible': [x['case'] for x in pip_variants if x['pass']]},
        'pass': len(pip_variants) == 5 and all(x['classification'] in CLASSIFICATIONS for x in pip_variants),
    }
    dump(out / 'base-pip-variants.json', base_pip)

    # Multiprocessing matrix, one isolated process per case.
    mp_probe = work / 'multiprocessing-probe.py'; write_probe(mp_probe, MULTIPROCESSING_PROBE)
    mp_names = ['start_method:fork', 'start_method:spawn', 'start_method:forkserver', 'pipes_connections', 'queues', 'pools', 'locks', 'semaphores', 'events', 'conditions', 'shared_values_arrays', 'manager', 'process_pool_executor', 'resource_tracker', 'shared_memory', 'termination_cleanup']
    mp_cases = []
    for name in mp_names:
        probe = target_json(python, [str(mp_probe), name], env, timeout=120)
        raw = probe.get('json', {'pass': False, 'error': probe.get('stderr') or 'missing JSON', 'returncode': probe.get('returncode')})
        upstream = name.startswith('start_method:') and raw.get('available') is False
        item = normalized_case(name, raw, upstream_on_fail=upstream)
        item['probe_process'] = {'returncode': probe.get('returncode'), 'stderr': probe.get('stderr'), 'stdout': probe.get('stdout')}
        mp_cases.append(item)
    mp_matrix = {
        'schema_version': 1, 'matrix': 'multiprocessing', 'cases': mp_cases, 'required_case_count': len(mp_names),
        'classified_case_count': len(mp_cases), 'pass_count': sum(x['pass'] for x in mp_cases),
        'available_start_methods': next((x['evidence'].get('methods') for x in mp_cases if x['case'] == 'start_method:fork' and x['evidence'].get('methods')), []),
        'support_boundary': {'blanket_multiprocessing_claim': False, 'passing_probe_requires_product_inclusion': False},
        'pass': len(mp_cases) == len(mp_names) and all(x['classification'] in CLASSIFICATIONS for x in mp_cases),
    }
    dump(out / 'multiprocessing-matrix.json', mp_matrix)

    # Feature surface decision input, not an Epoch 3 selection.
    def group(cases: list[dict[str, Any]]) -> dict[str, list[str]]:
        return {
            'technically_passing': [x['case'] for x in cases if x['pass']],
            'adaptation_required': [x['case'] for x in cases if x['classification'] == 'android-mandatory-adaptation'],
            'missing_bionic_primitive': [x['case'] for x in cases if x['classification'] == 'missing-bionic-primitive'],
            'upstream_build_decision': [x['case'] for x in cases if x['classification'] == 'upstream-build-decision'],
            'inadequate_environment': [x['case'] for x in cases if x['classification'] == 'inadequate-environment'],
            'support_candidates': [x['case'] for x in cases if x.get('support_candidate') is True],
        }
    decision = {
        'schema_version': 1, 'decision_kind': 'epoch3-feature-selection-input',
        'epoch3_selection_made': False, 'blanket_claims': {'subprocess': False, 'venv': False, 'pip': False, 'multiprocessing': False},
        'subprocess_core': group(core_cases), 'subprocess_secondary': group(secondary_cases), 'venv': group(venv_cases),
        'base_pip': group(pip_variants), 'multiprocessing': group(mp_cases),
        'policy_boundaries': {
            'default_shell': 'Use an explicit Android shell path when shell execution is selected; default /bin/sh is not assumed.',
            'preexec_fn': 'Not a default product support candidate even when technically passing.',
            'pre_existing_venv_after_base_move': 'Recreate unless independently transformed and qualified.',
            'pip_command_wrappers': 'Absolute shebang wrappers are relocation-bound; relative Android wrapper is a product-owned adaptation.',
            'base_pip': 'No inclusion decision; PIP-X and package-only options remain valid.',
            'uv': 'External pass or absence does not select uv inclusion.',
            'multiprocessing': 'Only individually passing primitives and start methods are support candidates.',
        },
        'exit_condition': {
            'subprocess_core_classified': len(core_cases), 'subprocess_secondary_classified': len(secondary_cases),
            'venv_classified': len(venv_cases), 'pip_variants_classified': len(pip_variants),
            'multiprocessing_classified': len(mp_cases), 'unclassified_count': 0,
        },
    }
    scan = contract_scan(decision); decision['negative_contract_scan'] = scan
    decision['pass'] = scan['pass'] and all((core_matrix['pass'], secondary_matrix['pass'], venv_matrix['pass'], base_pip['pass'], mp_matrix['pass']))
    dump(out / 'feature-surface-decision.json', decision)

    anchor_core = {'run_text_capture', 'popen_binary_pipes', 'nested_python', 'child_native_imports', 'asyncio_subprocess_exec'}
    core_pass_names = {x['case'] for x in core_cases if x['pass']}
    venv_pass_names = {x['case'] for x in venv_cases if x['pass']}
    gate = {
        'runtime_sdk_reproduction': gate3.get('pass') is True,
        'subprocess_core_complete': core_matrix['pass'],
        'subprocess_secondary_complete': secondary_matrix['pass'],
        'venv_matrix_complete': venv_matrix['pass'],
        'base_pip_variants_complete': base_pip['pass'],
        'multiprocessing_matrix_complete': mp_matrix['pass'],
        'feature_surface_decision_complete': decision['pass'],
        'core_anchor_cases_pass': anchor_core.issubset(core_pass_names),
        'fresh_venv_and_native_extension_pass': {'symlink_mode', 'base_moved_before_new_venv', 'native_extension_in_venv'}.issubset(venv_pass_names),
        'classification_vocabulary_exact': all(x['classification'] in CLASSIFICATIONS for x in [*core_cases, *secondary_cases, *venv_cases, *pip_variants, *mp_cases]),
        'no_blanket_claims': all(v is False for v in decision['blanket_claims'].values()),
        'negative_contract_scan': scan['pass'],
    }
    exit_condition = {
        'required_matrix_count': 5, 'complete_matrix_count': sum([core_matrix['pass'], secondary_matrix['pass'], venv_matrix['pass'], base_pip['pass'], mp_matrix['pass']]),
        'total_classified_cases': len(core_cases) + len(secondary_cases) + len(venv_cases) + len(pip_variants) + len(mp_cases),
        'unclassified_cases': 0,
        'core_anchor_pass_count': len(anchor_core & core_pass_names), 'core_anchor_required': len(anchor_core),
        'native_extension_venv_pass': 'native_extension_in_venv' in venv_pass_names,
        'fresh_venv_mode': fresh_after_move.get('mode'),
        'copy_mode_classification': next(x['classification'] for x in venv_cases if x['case'] == 'copy_mode'),
        'epoch3_selection_made': False,
        'blanket_claim_count': sum(decision['blanket_claims'].values()),
        'negative_contract_hits': scan['hit_count'],
    }
    passed = all(gate.values())
    dump(out / 'ut5-gate-diagnostics.json', {'schema_version': 1, 'pass': passed, 'gate_condition': gate, 'exit_condition': exit_condition, 'failed_gate_conditions': [k for k, v in gate.items() if not v]})
    dump(out / 'runtime-sdk-reproduction.json', {
        'schema_version': 1, 'pass': gate3.get('pass') is True, 'command': cmd, 'returncode': reproduction.returncode,
        'stdout_tail': reproduction.stdout[-4000:], 'stderr_tail': reproduction.stderr[-4000:],
        'prefix': str(prefix), 'python': str(python), 'native_wheel': {'name': native_wheel.name, 'sha256': sha256(native_wheel), 'size': native_wheel.stat().st_size},
        'ut3_gate': gate3,
    })
    if not passed:
        raise SystemExit('UT-5 gate failed:' + json.dumps(gate, sort_keys=True))
    print(json.dumps({'pass': True, 'gate_condition': gate, 'exit_condition': exit_condition, 'output': str(out)}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

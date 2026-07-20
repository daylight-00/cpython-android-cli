#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, shutil, socket, ssl, stat, struct, subprocess, sys, threading, time
from datetime import datetime
from pathlib import Path
from typing import Any

EXPECTED_ARCHIVE_SHA='38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5'
EXPECTED_ARCHIVE_SIZE=22358404
EXPECTED_CONTROL_SHA='6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c'
EXPECTED_ARTIFACT_SHA='387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306'
EXPECTED_LOADER_SHA='05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2'
EXPECTED_SYSCONFIG_SHA='6cff1984d4601a37e8b57762bb170a57e695cb64d516c1dab0023b7e809dc808'
FORBIDDEN=['/data/data/com.termux','/data/user/0/com.termux','com.termux','/usr/local','/opt/android-sdk','/opt/android-ndk','/home/runner/work','/tmp/cpython-build']


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def load(path: Path) -> Any: return json.loads(path.read_text())

def run(cmd:list[str],*,env:dict[str,str]|None=None,cwd:Path|None=None,timeout:int=180,check:bool=False)->subprocess.CompletedProcess[str]:
    p=subprocess.run(cmd,env=env,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(json.dumps({'cmd':cmd,'returncode':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-4000:]},sort_keys=True))
    return p

def parse_last_json(text:str)->Any:
    dec=json.JSONDecoder()
    for i,ch in enumerate(text):
        if ch not in '[{': continue
        try:
            obj,end=dec.raw_decode(text[i:])
            if not text[i+end:].strip(): return obj
        except json.JSONDecodeError: pass
    raise ValueError('no terminal JSON object')

def import_ut3(root:Path):
    path=root/'experiments/epoch2-upstream-thin-sysconfig-sdk/run_sysconfig_sdk_experiment.py'
    authority=load(root/'experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json')
    if sha256(path)!=authority['file_identities'][path.name]: raise RuntimeError('UT-3 script identity mismatch')
    spec=importlib.util.spec_from_file_location('hw_t_ut3_runtime',path)
    if spec is None or spec.loader is None: raise RuntimeError('cannot import UT-3 module')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m,authority

def write_tzif(path:Path,offset:int,abbr:str)->None:
    ab=(abbr[:7].encode('ascii')+b'\0')
    header=b'TZif\0'+b'\0'*15+struct.pack('>6l',0,0,0,0,1,len(ab))
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(header+struct.pack('>lbb',offset,0,0)+ab)

def policy_env(ut3:Any,prefix:Path,state:Path,data:Path,work:Path,*,ca_override:Path|None=None,user_site:bool=False)->dict[str,str]:
    env=ut3.clean_env(prefix,work)
    for k in ('SSL_CERT_DIR','TZ','TMP','TEMP','TMPDIR','XDG_CACHE_HOME','PYTHONUSERBASE','PYTHONNOUSERSITE','PYTHONDONTWRITEBYTECODE'):
        env.pop(k,None)
    for p in (state/'tmp',state/'cache',state/'pycache',state/'userbase',state/'home',state/'venvs'):
        p.mkdir(parents=True,exist_ok=True)
    env['HOME']=str(state/'home')
    env['TMPDIR']=str(state/'tmp')
    env['XDG_CACHE_HOME']=str(state/'cache')
    env['PIP_CACHE_DIR']=str(state/'cache/pip')
    env['PYTHONPYCACHEPREFIX']=str(state/'pycache')
    env['PYTHONUSERBASE']=str(state/'userbase')
    env['PYTHONTZPATH']=str(data/'zoneinfo')
    env['SSL_CERT_FILE']=str(ca_override if ca_override is not None else data/'ca/ca-bundle.pem')
    if user_site: env.pop('PYTHONNOUSERSITE',None)
    else: env['PYTHONNOUSERSITE']='1'
    env['HW_T_ANDROID_STATE_ROOT']=str(state)
    env['HW_T_ANDROID_DATA_ROOT']=str(data)
    return env

def target_json(python:Path,code:str,env:dict[str,str],*,timeout:int=180)->dict[str,Any]:
    p=run([str(python),'-c',code],env=env,timeout=timeout)
    result={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    try: result['json']=parse_last_json(p.stdout)
    except Exception as e: result['parse_error']=repr(e)
    return result

TLS_CLIENT=r'''
import json,socket,ssl,sys
host='127.0.0.1';port=int(sys.argv[1])
out={'ssl_cert_file':__import__('os').environ.get('SSL_CERT_FILE')}
try:
 c=ssl.create_default_context()
 with socket.create_connection((host,port),timeout=10) as raw:
  with c.wrap_socket(raw,server_hostname='localhost') as s:
   s.sendall(b'x');out['reply']=s.recv(1).decode();out['pass']=out['reply']=='y'
except Exception as e:
 out.update({'pass':False,'error_type':type(e).__name__,'error':str(e)})
print(json.dumps(out,sort_keys=True))
'''

def tls_probe(python:Path,env:dict[str,str],cert:Path,key:Path)->dict[str,Any]:
    listener=socket.socket();listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);listener.bind(('127.0.0.1',0));listener.listen(1)
    port=listener.getsockname()[1];server={'accepted':False,'error':None}
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(str(cert),str(key))
    def serve():
        try:
            conn,_=listener.accept();server['accepted']=True
            with ctx.wrap_socket(conn,server_side=True) as s:
                s.recv(1);s.sendall(b'y')
        except Exception as e: server['error']=f'{type(e).__name__}:{e}'
        finally: listener.close()
    t=threading.Thread(target=serve,daemon=True);t.start()
    p=run([str(python),'-c',TLS_CLIENT,str(port)],env=env,timeout=30)
    try:j=parse_last_json(p.stdout)
    except Exception as e:j={'pass':False,'parse_error':repr(e)}
    t.join(5)
    return {'returncode':p.returncode,'client':j,'server':server,'stderr':p.stderr}

TZ_CODE=r'''
import json,os
from datetime import datetime
from zoneinfo import ZoneInfo
out={'tzpath':os.environ.get('PYTHONTZPATH')}
try:
 z=ZoneInfo('Etc/HWTest');d=datetime(2026,1,1,tzinfo=z);out.update({'pass':True,'offset_seconds':int(d.utcoffset().total_seconds()),'tzname':d.tzname()})
except Exception as e:out.update({'pass':False,'error_type':type(e).__name__,'error':str(e)})
print(json.dumps(out,sort_keys=True))
'''

STATE_CODE=r'''
import json,os,pathlib,site,subprocess,sys,tempfile
cache=pathlib.Path(os.environ['XDG_CACHE_HOME']);cache.mkdir(parents=True,exist_ok=True);marker=cache/'hw-t-cache-marker';marker.write_text('ok')
fd,tmp=tempfile.mkstemp(prefix='hw-t-');os.close(fd)
import hw_t_data_policy_probe as probe
child_code="import json,os,site,tempfile;print(json.dumps({'tmp':tempfile.gettempdir(),'cache':os.environ.get('XDG_CACHE_HOME'),'pycache':os.environ.get('PYTHONPYCACHEPREFIX'),'userbase':site.getuserbase(),'ssl':os.environ.get('SSL_CERT_FILE'),'tz':os.environ.get('PYTHONTZPATH'),'state':os.environ.get('HW_T_ANDROID_STATE_ROOT'),'data':os.environ.get('HW_T_ANDROID_DATA_ROOT')},sort_keys=True))"
p=subprocess.run([sys.executable,'-c',child_code],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
out={'pass':p.returncode==0,'prefix':sys.prefix,'base_prefix':sys.base_prefix,'executable':sys.executable,'tmpdir':tempfile.gettempdir(),'temp_file':tmp,'cache_marker':str(marker),'module_value':probe.VALUE,'module_cached':probe.__cached__,'userbase':site.getuserbase(),'usersite':site.getusersitepackages(),'enable_user_site':site.ENABLE_USER_SITE,'env':{k:os.environ.get(k) for k in ['TMPDIR','XDG_CACHE_HOME','PIP_CACHE_DIR','PYTHONPYCACHEPREFIX','PYTHONUSERBASE','PYTHONNOUSERSITE','SSL_CERT_FILE','PYTHONTZPATH','HW_T_ANDROID_STATE_ROOT','HW_T_ANDROID_DATA_ROOT']},'child_returncode':p.returncode,'child_stdout':p.stdout,'child_stderr':p.stderr}
print(json.dumps(out,sort_keys=True))
'''

def tree_snapshot(root:Path)->dict[str,Any]:
    rows=[]
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root).as_posix();st=p.lstat()
        if p.is_symlink(): rows.append({'path':rel,'kind':'symlink','target':os.readlink(p)})
        elif p.is_file(): rows.append({'path':rel,'kind':'file','sha256':sha256(p),'size':st.st_size,'mode':stat.S_IMODE(st.st_mode)})
        elif p.is_dir(): rows.append({'path':rel,'kind':'dir','mode':stat.S_IMODE(st.st_mode)})
    raw=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
    return {'count':len(rows),'sha256':hashlib.sha256(raw).hexdigest(),'rows':rows}

def make_read_only(root:Path)->None:
    for p in sorted(root.rglob('*'),reverse=True):
        if p.is_symlink(): continue
        mode=p.stat().st_mode
        if p.is_dir(): p.chmod(0o555)
        elif mode & 0o111: p.chmod(0o555)
        else: p.chmod(0o444)
    root.chmod(0o555)

def make_writable(root:Path)->None:
    if not root.exists(): return
    root.chmod(stat.S_IMODE(root.stat().st_mode)|0o700)
    for p in sorted(root.rglob('*')):
        if p.is_symlink(): continue
        mode=stat.S_IMODE(p.stat().st_mode)
        if p.is_dir(): p.chmod(mode|0o700)
        else: p.chmod(mode|0o600)

def relocate_read_only_tree(source:Path,destination:Path)->None:
    make_writable(source)
    try:
        shutil.move(str(source),str(destination))
    except Exception:
        if source.exists(): make_writable(source)
        if destination.exists(): make_writable(destination)
        raise
    make_read_only(destination)

def contract_scan(value:Any)->dict[str,Any]:
    text=json.dumps(value,sort_keys=True)
    hits={token:[i for i in range(len(text)) if text.startswith(token,i)][:8] for token in FORBIDDEN if token in text}
    return {'scope':'selected host-neutral policy contract and normalized active metadata only','forbidden_tokens':FORBIDDEN,'hits':hits,'hit_count':sum(len(v) for v in hits.values()),'pass':not hits}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--cc',default='clang');ap.add_argument('--patchelf',default='patchelf');ap.add_argument('--readelf',default='readelf');a=ap.parse_args()
    root=a.root.resolve();archive=a.archive.resolve();work=a.work.resolve();out=a.output.resolve();work.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    if sha256(archive)!=EXPECTED_ARCHIVE_SHA or archive.stat().st_size!=EXPECTED_ARCHIVE_SIZE: raise SystemExit('official archive identity mismatch')
    auths={'control':('experiments/epoch2-upstream-thin-control/upstream-control-authority.json',EXPECTED_CONTROL_SHA),'artifact':('experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json',EXPECTED_ARTIFACT_SHA),'loader':('experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json',EXPECTED_LOADER_SHA),'sysconfig':('experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json',EXPECTED_SYSCONFIG_SHA)}
    for k,(rel,h) in auths.items():
        if sha256(root/rel)!=h: raise SystemExit(f'authority mismatch:{k}')
    ut3,ut3_authority=import_ut3(root);ut2,_=ut3.import_ut2_module(root)
    official=work/'official';shutil.rmtree(official,ignore_errors=True);extraction=ut2.safe_extract(archive,official);verification=ut2.verify_official_prefix(official,root/'experiments/epoch2-upstream-thin-control')
    if not verification['pass']: raise SystemExit('official extraction verification failed')
    prefix_a=work/'location-a/prefix';prefix_a.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(official/'prefix',prefix_a,symlinks=True)
    modules=set(load(root/'experiments/epoch2-upstream-thin-control/elf-and-extension-inventory.json')['native_extensions'])
    native=ut2.patch_objects(prefix_a,'lr3',a.patchelf,a.readelf,modules)
    launcher=ut3.compile_selected_launcher(ut2,root/'experiments/epoch2-upstream-thin-loader-relocation/launcher_la2_programs_python.c',prefix_a,work/'launcher-build',a.cc,a.patchelf,a.readelf)
    python_a=ut2.install_launcher(prefix_a,Path(launcher['binary']))
    startup=ut2.execute_runtime_probe(python_a,prefix_a,work,[Path(x).name.split('.',1)[0] for x in modules])
    if not(startup['startup_pass'] and startup['required_extension_failures']==0 and startup['ld_library_path_absent'] and startup['self_reexec_absent']): raise SystemExit('runtime reproduction failed')
    mutations=ut3.normalize_runtime(prefix_a,python_a,work)
    runtime=ut3.runtime_probe(python_a,prefix_a,work)
    if not runtime['pass'] or not ut3.runtime_paths_within(runtime,prefix_a): raise SystemExit('runtime normalization failed')
    dump(out/'runtime-reproduction.json',{'schema_version':1,'extraction':extraction,'verification':verification,'launcher':launcher,'native_object_count':len(native),'lr3_exact_and_16k':all(x['exact_mutation_check'] and x['alignment_16k_compatible'] for x in native),'startup':startup,'sysconfig_normalization':mutations,'runtime':runtime})

    certdir=prefix_a/'lib/python3.14/test/certdata';server_cert=certdir/'ssl_cert.pem';server_key=certdir/'ssl_key.pem';invalid_ca=certdir/'keycert2.pem'
    for p in (server_cert,server_key,invalid_ca):
        if not p.is_file(): raise SystemExit(f'missing TLS probe input:{p.name}')
    data1=work/'data-v1';data2=work/'data-v2';external=work/'caller-override';state=work/'state'
    for d in (data1,data2): (d/'ca').mkdir(parents=True,exist_ok=True);shutil.copy2(server_cert,d/'ca/ca-bundle.pem')
    external.mkdir(parents=True,exist_ok=True);shutil.copy2(server_cert,external/'caller-ca.pem');shutil.copy2(invalid_ca,external/'invalid-ca.pem')
    write_tzif(data1/'zoneinfo/Etc/HWTest',3600,'HWT1');write_tzif(data2/'zoneinfo/Etc/HWTest',7200,'HWT2')
    dump(data1/'data-manifest.json',{'schema_version':1,'dataset_version':'probe-v1','ca_provenance':'CPython test self-signed certificate; mechanism probe only','timezone_provenance':'generated fixed-offset TZif representing IANA-style raw zoneinfo mechanics','update_owner':'standalone data release process','python_update_independent':True})
    dump(data2/'data-manifest.json',{'schema_version':1,'dataset_version':'probe-v2','ca_provenance':'same mechanism probe certificate','timezone_provenance':'generated fixed-offset TZif update','update_owner':'standalone data release process','python_update_independent':True})

    default_env=policy_env(ut3,prefix_a,state,data1,work/'env-default')
    ca_default=tls_probe(python_a,default_env,server_cert,server_key)
    ca_invalid=tls_probe(python_a,policy_env(ut3,prefix_a,state,data1,work/'env-invalid',ca_override=external/'invalid-ca.pem'),server_cert,server_key)
    ca_external=tls_probe(python_a,policy_env(ut3,prefix_a,state,data1,work/'env-external',ca_override=external/'caller-ca.pem'),server_cert,server_key)
    ca_policy={'schema_version':1,'selected':'bundled-default-with-caller-override','candidates':{'caller-supplied-only':{'selected':False,'reason':'no deterministic default'},'pinned-bundled-ca-bundle':{'selected':False,'reason':'must preserve caller override'},'bundled-default-with-caller-override':{'selected':True},'generic-android-trust-extraction':{'selected':False,'reason':'host layout and update semantics are not portable'},'native-android-trust-bridge':{'selected':False,'reason':'requires Android-specific native adaptation not evidenced here'}},'contract':{'source':'<DATA_ROOT>/ca/ca-bundle.pem','caller_override':'SSL_CERT_FILE','provenance':'public CA program bundle chosen in Epoch 3; probe certificate is not production data','update_owner':'standalone data release process','relocation':'data root is independent of install root','failure_mode':'fail TLS verification; never silently fall back to host-private paths','host_neutral':True},'probe':{'default':ca_default,'invalid_override':ca_invalid,'valid_external_override':ca_external},'pass':ca_default['client'].get('pass') is True and ca_invalid['client'].get('pass') is False and ca_external['client'].get('pass') is True}
    dump(out/'ca-trust-candidates.json',ca_policy)

    tz1=target_json(python_a,TZ_CODE,default_env);tz2=target_json(python_a,TZ_CODE,policy_env(ut3,prefix_a,state,data2,work/'env-tz2'))
    nohost=default_env.copy();nohost['PYTHONTZPATH']=''
    tz_none=target_json(python_a,TZ_CODE,nohost)
    tz_policy={'schema_version':1,'selected':'bundled-raw-zoneinfo-tree','candidates':{'pinned-tzdata-in-install-tree':{'selected':False,'reason':'couples data update to Python update'},'required-companion-dependency':{'selected':False,'reason':'selection deferred to Epoch 3'},'bundled-raw-zoneinfo-tree':{'selected':True},'host-discovery':{'selected':False,'reason':'not portable or provenance-stable'}},'contract':{'source':'<DATA_ROOT>/zoneinfo','environment':'PYTHONTZPATH','provenance':'IANA tzdata release selected in Epoch 3','update_owner':'standalone data release process','relocation':'data root independent of install root','failure_mode':'ZoneInfoNotFoundError for absent key/data; no implicit host discovery','host_neutral':True},'probe':{'v1':tz1,'v2':tz2,'host_discovery_disabled':tz_none},'pass':tz1.get('json',{}).get('offset_seconds')==3600 and tz2.get('json',{}).get('offset_seconds')==7200 and tz_none.get('json',{}).get('pass') is False}
    dump(out/'timezone-candidates.json',tz_policy)

    probe_module=prefix_a/'lib/python3.14/hw_t_data_policy_probe.py';probe_module.write_text('VALUE = 314\n')
    make_read_only(prefix_a);before=tree_snapshot(prefix_a)
    state_default=target_json(python_a,STATE_CODE,default_env)
    state_user=target_json(python_a,STATE_CODE,policy_env(ut3,prefix_a,state,data1,work/'env-user',user_site=True))
    temp_policy={'schema_version':1,'selected':'caller-owned-app-private-state-root','contract':{'path':'<STATE_ROOT>/tmp','environment':'TMPDIR','provenance':'caller-supplied app-private writable root','update_owner':'runtime caller/application','relocation':'independent of install root','failure_mode':'tempfile operation fails without writable root; no host-private fallback','host_neutral':True},'probe':state_default,'pass':state_default.get('json',{}).get('tmpdir')==str(state/'tmp') and str(state/'tmp') in state_default.get('json',{}).get('temp_file','')}
    dump(out/'temporary-directory-policy.json',temp_policy)
    sj=state_default.get('json',{});uj=state_user.get('json',{})
    pycache=str(sj.get('module_cached',''));cache_marker=str(sj.get('cache_marker',''))
    cache_policy={'schema_version':1,'contract':{'cache':'<STATE_ROOT>/cache via XDG_CACHE_HOME and PIP_CACHE_DIR','bytecode':'<STATE_ROOT>/pycache via PYTHONPYCACHEPREFIX','user_site_default':'disabled via PYTHONNOUSERSITE=1','user_site_opt_in':'<STATE_ROOT>/userbase via PYTHONUSERBASE','provenance':'caller-supplied app-private writable root','update_owner':'runtime caller/application','relocation':'independent of install root','failure_mode':'disable optional cache/user-site or fail write; never write install tree','host_neutral':True},'probe':{'default':state_default,'explicit_user_site':state_user},'pass':cache_marker.startswith(str(state/'cache')) and pycache.startswith(str(state/'pycache')) and sj.get('enable_user_site') is False and str(uj.get('userbase','')).startswith(str(state/'userbase')) and uj.get('enable_user_site') is not False and not any(prefix_a.rglob('__pycache__'))}
    dump(out/'cache-bytecode-and-user-site-policy.json',cache_policy)

    venv_a=state/'venvs/base-a';p=run([str(python_a),'-m','venv','--without-pip',str(venv_a)],env=default_env,timeout=300)
    vpy_a=venv_a/'bin/python';venv_probe_a=target_json(vpy_a,STATE_CODE,default_env,timeout=180) if p.returncode==0 and (vpy_a.exists() or vpy_a.is_symlink()) else {'returncode':127,'stderr':'venv creation failed'}
    cfg_a=(venv_a/'pyvenv.cfg').read_text() if (venv_a/'pyvenv.cfg').is_file() else ''
    prefix_b=work/'location-b/prefix'
    prefix_b.parent.mkdir(parents=True,exist_ok=True)
    relocate_read_only_tree(prefix_a,prefix_b)
    python_b=prefix_b/'bin/python3.14'
    env_b=policy_env(ut3,prefix_b,state,data2,work/'env-b')
    relocated_state=target_json(python_b,STATE_CODE,env_b)
    relocated_tz=target_json(python_b,TZ_CODE,env_b)
    if vpy_a.exists() or vpy_a.is_symlink():
        try:
            old_venv=target_json(vpy_a,'import json,sys;print(json.dumps({\"pass\":True,\"prefix\":sys.prefix,\"base_prefix\":sys.base_prefix}))',env_b)
        except OSError as e:
            old_venv={'returncode':127,'json':{'pass':False,'error_type':type(e).__name__,'errno':getattr(e,'errno',None),'error':str(e)}}
    else:
        old_venv={'returncode':127,'json':{'pass':False,'error':'missing-or-dangling'}}
    venv_b=state/'venvs/base-b';p2=run([str(python_b),'-m','venv','--without-pip',str(venv_b)],env=env_b,timeout=300);vpy_b=venv_b/'bin/python';venv_probe_b=target_json(vpy_b,STATE_CODE,env_b) if p2.returncode==0 and (vpy_b.exists() or vpy_b.is_symlink()) else {'returncode':127,'stderr':'fresh venv creation failed'}
    after=tree_snapshot(prefix_b)
    venv_policy={'schema_version':1,'contract':{'path':'<STATE_ROOT>/venvs/<name>','provenance':'created by selected runtime from caller-owned writable root','update_owner':'runtime caller/application','relocation':'new venv after base movement is supported; pre-existing venv is base-bound and must be recreated unless independently proven relocatable','failure_mode':'stale pyvenv.cfg or dangling launcher after base movement','host_neutral':True},'probe':{'create_a_returncode':p.returncode,'location_a':venv_probe_a,'pyvenv_cfg_a':cfg_a,'pre_existing_after_base_move':old_venv,'create_b_returncode':p2.returncode,'fresh_after_move':venv_probe_b},'pass':p.returncode==0 and venv_probe_a.get('json',{}).get('pass') is True and p2.returncode==0 and venv_probe_b.get('json',{}).get('pass') is True and str(venv_probe_b.get('json',{}).get('base_prefix',''))==str(prefix_b)}
    dump(out/'venv-writable-state-policy.json',venv_policy)

    read_only={'schema_version':1,'contract':{'install_root':'<INSTALL_ROOT> is immutable after assembly','writable_root':'<STATE_ROOT> is mandatory for temp/cache/bytecode/user-site/venv','data_root':'<DATA_ROOT> is independently updateable','provenance':'official Python artifact plus frozen transformations','update_owner':'Python artifact release process; data release process is separate','relocation':'whole install root may move; state/data roots remain caller-selected','failure_mode':'fail closed when required writable or data roots are absent','host_neutral':True},'snapshot_before':{'count':before['count'],'sha256':before['sha256']},'snapshot_after':{'count':after['count'],'sha256':after['sha256']},'location_a_state_probe':state_default,'location_b_state_probe':relocated_state,'location_b_timezone_probe':relocated_tz,'prefix_unchanged':before['sha256']==after['sha256'],'pass':before['sha256']==after['sha256'] and relocated_state.get('json',{}).get('pass') is True and relocated_tz.get('json',{}).get('offset_seconds')==7200}
    dump(out/'read-only-installation-behavior.json',read_only)

    data_update={'schema_version':1,'python_prefix_snapshot_unchanged':before['sha256']==after['sha256'],'dataset_v1':load(data1/'data-manifest.json'),'dataset_v2':load(data2/'data-manifest.json'),'timezone_before_seconds':tz1.get('json',{}).get('offset_seconds'),'timezone_after_seconds':relocated_tz.get('json',{}).get('offset_seconds'),'python_update_required':False,'pass':before['sha256']==after['sha256'] and tz1.get('json',{}).get('offset_seconds')==3600 and relocated_tz.get('json',{}).get('offset_seconds')==7200}
    dump(out/'data-update-evidence.json',data_update)

    contract={'ca':ca_policy['contract'],'timezone':tz_policy['contract'],'temporary':temp_policy['contract'],'cache_bytecode_user_site':cache_policy['contract'],'venv':venv_policy['contract'],'read_only_install':read_only['contract']}
    scan=contract_scan(contract);active=ut3.scan_text_surfaces(prefix_b,str(prefix_b));scan['active_metadata_classification_counts']=active['classification_counts'];scan['active_metadata_unknown_absolute_zero']=active['classification_counts'].get('unknown-absolute',0)==0;scan['active_metadata_stale_install_zero']=active['classification_counts'].get('stale-install-prefix',0)==0;scan['pass']=scan['pass'] and scan['active_metadata_unknown_absolute_zero'] and scan['active_metadata_stale_install_zero'];dump(out/'negative-path-scans.json',scan)
    policies=[ca_policy,tz_policy,temp_policy,cache_policy,venv_policy,read_only]
    complete=all(all(k in p['contract'] for k in ('provenance','update_owner','relocation','failure_mode','host_neutral')) for p in policies)
    child=state_default.get('json',{}).get('child_stdout','');child_ok=all(str(x) in child for x in (state/'tmp',state/'cache',data1/'ca/ca-bundle.pem',data1/'zoneinfo'))
    gate={'ca_policy':ca_policy['pass'],'timezone_policy':tz_policy['pass'],'temporary_policy':temp_policy['pass'],'cache_bytecode_user_site_policy':cache_policy['pass'],'venv_policy':venv_policy['pass'],'read_only_installation':read_only['pass'],'data_update_independent':data_update['pass'],'subprocess_inheritance':child_ok,'negative_path_scans':scan['pass'],'policy_completeness':complete,'runtime_reproduction':startup['startup_pass'] is True,'lr3_exact_and_16k':all(x['exact_mutation_check'] and x['alignment_16k_compatible'] for x in native)}
    exit_condition={'required_policy_count':6,'complete_policy_count':sum(1 for p in policies if all(k in p['contract'] for k in ('provenance','update_owner','relocation','failure_mode','host_neutral'))),'negative_path_hits':scan['hit_count'],'read_only_prefix_unchanged':read_only['prefix_unchanged'],'relocated_runtime_pass':relocated_state.get('json',{}).get('pass') is True,'fresh_venv_after_move_pass':venv_probe_b.get('json',{}).get('pass') is True,'data_update_without_python_update':data_update['pass']}
    passed=all(gate.values());dump(out/'ut4-gate-diagnostics.json',{'schema_version':1,'pass':passed,'exit_condition':exit_condition,'gate_condition':gate,'failed_gate_conditions':[k for k,v in gate.items() if not v]})
    if not passed: raise SystemExit('UT-4 gate failed:'+json.dumps(gate,sort_keys=True))
    print(json.dumps({'pass':True,'gate_condition':gate,'exit_condition':exit_condition,'output':str(out)},indent=2,sort_keys=True));return 0

if __name__=='__main__':raise SystemExit(main())

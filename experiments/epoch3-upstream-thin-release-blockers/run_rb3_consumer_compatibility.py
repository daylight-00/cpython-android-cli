#!/usr/bin/env python3
"""Qualify exact E3 artifacts as Astral-shaped and uv system/managed Python inputs."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
LIB=ROOT/'components/upstream-thin/lib'; sys.path.insert(0,str(LIB))
from archive import safe_extract_tar, sha256_file, write_json  # noqa:E402
from owner_approval_review import verify_family  # noqa:E402

FULL={'filename':'cpython-3.14.6+e3-full-r4-aarch64-linux-android-full.tar.zst','sha256':'20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12','size_bytes':39408292}
INSTALL={'filename':'cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only.tar.gz','sha256':'84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76','size_bytes':23841726}
KEY='cpython-3.14.6-linux-aarch64-none'

def identity(path:Path)->dict[str,Any]: return {'filename':path.name,'sha256':sha256_file(path),'size_bytes':path.stat().st_size}
def snapshot(root:Path)->list[dict[str,Any]]:
    if not root.exists(): return []
    rows=[]
    for p in sorted(root.rglob('*'),key=lambda x:x.relative_to(root).as_posix()):
        rel=p.relative_to(root).as_posix()
        if p.is_symlink(): rows.append({'path':rel,'type':'symlink','target':os.readlink(p)})
        elif p.is_dir(): rows.append({'path':rel,'type':'directory'})
        elif p.is_file(): rows.append({'path':rel,'type':'file','sha256':sha256_file(p),'size_bytes':p.stat().st_size})
    return rows

def catalog_row(archive:Path)->dict[str,Any]:
    return {'name':'cpython','arch':{'family':'aarch64','variant':None},'os':'linux','libc':'none','major':3,'minor':14,'patch':6,'prerelease':'','url':archive.resolve().as_uri(),'sha256':sha256_file(archive),'variant':None,'build':'hw-t-e3-rb3'}

def exact(path:Path,expected:dict[str,Any])->None:
    if not path.is_file() or identity(path)!=expected: raise ValueError(f'exact artifact mismatch: {path}: {identity(path) if path.exists() else None} != {expected}')

def extract_zst(archive:Path,destination:Path,zstd:str)->None:
    with tempfile.TemporaryDirectory(prefix='rb3-zst-') as tmp:
        tar=Path(tmp)/'payload.tar'
        p=subprocess.run([zstd,'-q','-d','-c',str(archive)],stdout=tar.open('wb'),stderr=subprocess.PIPE)
        if p.returncode: raise RuntimeError(p.stderr.decode(errors='replace'))
        safe_extract_tar(tar,destination,'r:')

def run_capture(name:str,cmd:list[str],cwd:Path,env:dict[str,str],out:Path)->dict[str,Any]:
    p=subprocess.run(cmd,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    row={'name':name,'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    write_json(out/f'{name}.json',row); return row

def parse_identity(text:str)->dict[str,Any]:
    value=json.loads(text.strip());
    if not isinstance(value,dict): raise ValueError('identity output not object')
    return value

def identity_code()->str:
    return "import json,platform,sys,sysconfig;print(json.dumps({'executable':sys.executable,'real_executable':__import__('os').path.realpath(sys.executable),'version':platform.python_version(),'implementation':platform.python_implementation(),'soabi':sysconfig.get_config_var('SOABI'),'multiarch':sysconfig.get_config_var('MULTIARCH'),'platform':sysconfig.get_platform(),'prefix':sys.prefix,'base_prefix':sys.base_prefix},sort_keys=True))"

def identity_ok(row:dict[str,Any],expected_python:Path|None=None)->bool:
    if row.get('returncode')!=0: return False
    try: v=parse_identity(row['stdout'])
    except Exception: return False
    base=v.get('implementation')=='CPython' and v.get('version')=='3.14.6' and v.get('soabi')=='cpython-314-aarch64-linux-android' and v.get('multiarch')=='aarch64-linux-android' and v.get('platform')=='android-24-arm64_v8a'
    if expected_python is not None: base=base and Path(v.get('real_executable','')).resolve()==expected_python.resolve()
    return base

def isolated_env(base:Path,managed:Path|None=None,policy:str='never',catalog:Path|None=None)->dict[str,str]:
    home=base/'home'; data=base/'data'; config=base/'config'; cache=base/'cache'
    for p in (home,data,config,cache): p.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy(); env.update({'HOME':str(home),'XDG_DATA_HOME':str(data),'XDG_CONFIG_HOME':str(config),'XDG_CACHE_HOME':str(cache),'UV_CACHE_DIR':str(cache/'uv'),'UV_OFFLINE':'1','UV_NO_CONFIG':'1','UV_PYTHON_DOWNLOADS':policy,'VIRTUAL_ENV':'','PYTHONHOME':'','PYTHONPATH':''})
    if managed is not None: env['UV_PYTHON_INSTALL_DIR']=str(managed)
    if catalog is not None: env['UV_PYTHON_DOWNLOADS_JSON_URL']=catalog.resolve().as_uri()
    return env

def run(family:Path,output:Path,uv:Path,zstd:str='zstd')->dict[str,Any]:
    family=family.resolve(); output=output.resolve(); uv=uv.resolve()
    fv=verify_family(family,ROOT)
    if not fv['pass']: raise ValueError(f'invalid family: {fv}')
    full=family/FULL['filename']; install=family/INSTALL['filename']; exact(full,FULL); exact(install,INSTALL)
    before_family=snapshot(family)
    real_managed=Path(os.environ.get('UV_PYTHON_INSTALL_DIR',str(Path.home()/'.local/share/uv/python'))).resolve(); before_real=snapshot(real_managed)
    if output.exists(): shutil.rmtree(output)
    (output/'process').mkdir(parents=True); (output/'research').mkdir(); (output/'artifacts').mkdir()
    uv_id={'path':str(uv),'version':subprocess.check_output([str(uv),'--version'],text=True).strip(),'sha256':sha256_file(uv),'size_bytes':uv.stat().st_size}
    if 'aarch64-linux-android' not in uv_id['version']: raise ValueError(f'uv is not Android aarch64: {uv_id}')
    write_json(output/'research/uv.json',uv_id)
    with tempfile.TemporaryDirectory(prefix='e3-rb3-') as tmp:
        t=Path(tmp); install_root=t/'system-product'; safe_extract_tar(install,install_root,'r:gz')
        python=install_root/'python/bin/python3.14'
        if not python.is_file() or not os.access(python,os.X_OK): raise ValueError('exact interpreter missing')
        full_root=t/'full-product'; extract_zst(full,full_root,zstd)
        pyjson=json.loads((full_root/'python/PYTHON.json').read_text())
        astral_checks={'format_version':pyjson.get('version')==8,'python_exe_relative':pyjson.get('python_exe') in {'install/bin/python3.14','install/bin/python','install/bin/python3'},'target_android':pyjson.get('target_triple')=='aarch64-linux-android','shared_libpython':pyjson.get('libpython_link_mode')=='shared','no_fabricated_static_core':not bool(pyjson.get('build_info',{}).get('core',{}).get('static_lib'))}
        write_json(output/'research/astral-metadata.json',{'checks':astral_checks,'pass':all(astral_checks.values()),'python_json_sha256':sha256_file(full_root/'python/PYTHON.json')})
        sysenv=isolated_env(t/'system-session')
        procs=[]
        procs.append(run_capture('system-identity',[str(python),'-c',identity_code()],t,sysenv,output/'process'))
        procs.append(run_capture('system-find',[str(uv),'python','find',str(python),'--resolve-links','--no-python-downloads','--offline','--no-managed-python','--system','--no-config','--color','never'],t,sysenv,output/'process'))
        sysvenv=t/'system-venv'; procs.append(run_capture('system-venv',[str(uv),'venv',str(sysvenv),'--python',str(python),'--no-python-downloads','--offline','--no-managed-python','--no-cache','--no-config','--color','never'],t,sysenv,output/'process'))
        procs.append(run_capture('system-venv-identity',[str(sysvenv/'bin/python'),'-c',identity_code()],t,sysenv,output/'process'))
        procs.append(run_capture('system-run',[str(uv),'run','--python',str(python),'--no-python-downloads','--offline','--no-managed-python','--no-project','--no-sync','--no-config','--color','never','--','python','-c',identity_code()],t,sysenv,output/'process'))
        project=t/'sync-project'; project.mkdir(); (project/'pyproject.toml').write_text('[project]\nname="rb3-probe"\nversion="0.0.0"\nrequires-python=">=3.14,<3.15"\ndependencies=[]\n')
        syncvenv=t/'sync-venv'; syncenv=dict(sysenv); syncenv['UV_PROJECT_ENVIRONMENT']=str(syncvenv)
        procs.append(run_capture('system-sync',[str(uv),'sync','--project',str(project),'--python',str(python),'--no-python-downloads','--offline','--no-managed-python','--no-cache','--no-config','--color','never'],project,syncenv,output/'process'))
        procs.append(run_capture('system-sync-identity',[str(syncvenv/'bin/python'),'-c',identity_code()],project,syncenv,output/'process'))
        catalog=t/'custom-downloads.json'; write_json(catalog,{KEY:catalog_row(install)})
        shutil.copyfile(catalog,output/'artifacts/custom-downloads.json')
        managed=t/'managed-root'; menv=isolated_env(t/'managed-session',managed,'manual',catalog)
        procs.append(run_capture('managed-catalog',[str(uv),'python','list','3.14','--python-downloads-json-url',catalog.resolve().as_uri(),'--output-format','json','--show-urls','--offline','--no-config','--color','never'],t,menv,output/'process'))
        procs.append(run_capture('managed-install',[str(uv),'python','install',KEY,'--install-dir',str(managed),'--no-bin','--python-downloads-json-url',catalog.resolve().as_uri(),'--offline','--no-config','--color','never'],t,menv,output/'process'))
        findenv=isolated_env(t/'managed-find-session',managed,'never',catalog)
        procs.append(run_capture('managed-find',[str(uv),'python','find','3.14.6','--managed-python','--no-python-downloads','--offline','--python-downloads-json-url',catalog.resolve().as_uri(),'--no-config','--color','never'],t,findenv,output/'process'))
        managed_python=Path(procs[-1]['stdout'].strip()) if procs[-1]['returncode']==0 else managed/'missing'
        procs.append(run_capture('managed-identity',[str(managed_python),'-c',identity_code()],t,findenv,output/'process'))
        mvenv=t/'managed-venv'; procs.append(run_capture('managed-venv',[str(uv),'venv',str(mvenv),'--python','3.14.6','--managed-python','--no-python-downloads','--offline','--no-cache','--no-config','--color','never'],t,findenv,output/'process'))
        procs.append(run_capture('managed-venv-identity',[str(mvenv/'bin/python'),'-c',identity_code()],t,findenv,output/'process'))
        installed_before=snapshot(managed)
        menv2=isolated_env(t/'managed-reinstall-session',managed,'manual',catalog)
        procs.append(run_capture('managed-reinstall',[str(uv),'python','install',KEY,'--install-dir',str(managed),'--no-bin','--python-downloads-json-url',catalog.resolve().as_uri(),'--offline','--no-config','--color','never'],t,menv2,output/'process'))
        installed_after=snapshot(managed)
        procs.append(run_capture('managed-uninstall',[str(uv),'python','uninstall','3.14.6','--install-dir',str(managed),'--offline','--no-config','--color','never'],t,findenv,output/'process'))
        procs.append(run_capture('managed-find-empty',[str(uv),'python','find','3.14.6','--managed-python','--no-python-downloads','--offline','--python-downloads-json-url',catalog.resolve().as_uri(),'--no-config','--color','never'],t,findenv,output/'process'))
        process={r['name']:r for r in procs}
        checks={
          'exact_family':fv['pass'],'astral_metadata':all(astral_checks.values()),'uv_android':True,
          'system_identity':identity_ok(process['system-identity'],python),
          'system_find':process['system-find']['returncode']==0 and Path(process['system-find']['stdout'].strip()).resolve()==python.resolve(),
          'system_venv':process['system-venv']['returncode']==0 and identity_ok(process['system-venv-identity']),
          'system_run':identity_ok(process['system-run'],python),
          'system_sync':process['system-sync']['returncode']==0 and identity_ok(process['system-sync-identity']),
          'managed_catalog':process['managed-catalog']['returncode']==0 and KEY in process['managed-catalog']['stdout'],
          'managed_install':process['managed-install']['returncode']==0,
          'managed_find':process['managed-find']['returncode']==0 and managed_python.is_file(),
          'managed_identity':identity_ok(process['managed-identity']),
          'managed_venv':process['managed-venv']['returncode']==0 and identity_ok(process['managed-venv-identity']),
          'managed_reinstall_noop':process['managed-reinstall']['returncode']==0 and installed_before==installed_after,
          'managed_uninstall':process['managed-uninstall']['returncode']==0 and process['managed-find-empty']['returncode']!=0,
          'exact_archive_direct':catalog_row(install)['sha256']==INSTALL['sha256'] and catalog_row(install)['url']==install.resolve().as_uri(),
        }
    after_family=snapshot(family); after_real=snapshot(real_managed)
    checks['frozen_family_unchanged']=before_family==after_family
    checks['real_managed_root_unchanged']=before_real==after_real
    failed=sorted(k for k,v in checks.items() if v is not True)
    result={'schema_version':1,'result_kind':'epoch3-rb3-astral-uv-consumer-compatibility-owner-result','pass':not failed,'checks':checks,'failed_checks':failed,'uv':uv_id,'catalog_key':KEY,'system_interpreter':str(python),'managed_archive':identity(install),'claim_boundary':{'rb3_closed':False,'built_in_uv_android_catalog':False,'automatic_network_download':False,'upstream_uv_android_support':False,'selectable':False,'publication':False}}
    write_json(output/'rb3-consumer-compatibility-result.json',result)
    write_json(output/'protected-state.json',{'family_unchanged':before_family==after_family,'real_managed_root':str(real_managed),'real_managed_root_unchanged':before_real==after_real})
    return result

def main():
    p=argparse.ArgumentParser(); p.add_argument('--family-dir',type=Path,required=True); p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--uv',type=Path,default=Path(shutil.which('uv') or 'uv')); p.add_argument('--zstd',default='zstd'); a=p.parse_args()
    try:r=run(a.family_dir,a.output_dir,a.uv,a.zstd)
    except Exception as e:r={'schema_version':1,'pass':False,'error':f'{type(e).__name__}: {e}'}
    print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r.get('pass') is True else 1
if __name__=='__main__': raise SystemExit(main())

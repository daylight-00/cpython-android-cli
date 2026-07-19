#!/usr/bin/env python3
"""Positive and negative fixtures for current-state/registry v2."""
from __future__ import annotations
import importlib.util,json,os,shutil,subprocess,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location("v",HERE/"verify-current-state.py");mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def run_git(argv:list[str],cwd:Path,**kwargs):
 env=os.environ.copy();env.update({"GIT_CONFIG_NOSYSTEM":"1","GIT_OPTIONAL_LOCKS":"0"})
 return subprocess.run(["git","-c","gc.auto=0","-c","maintenance.auto=false",*argv],cwd=cwd,env=env,check=True,**kwargs)
def materialize(dst:Path):
 dst.mkdir(parents=True)
 prefix=str(dst.resolve())+"/"
 selected=subprocess.run(["git","-C",str(ROOT),"ls-files","-z","--","*.md","*.json","experiments/document-current-state/render-current-views.py"],check=True,stdout=subprocess.PIPE).stdout
 subprocess.run(["git","-C",str(ROOT),"checkout-index","--force",f"--prefix={prefix}","--stdin","-z"],check=True,input=selected)
 run_git(["init","-q"],dst);run_git(["add","-A"],dst)
 return (dst/".git/index").read_bytes()
def restore(dst:Path,index:bytes):
 (dst/".git/index").write_bytes(index)
 run_git(["clean","-fdx","-q"],dst)
 run_git(["checkout-index","--force","--all"],dst)
def cleanup(path:Path):
 for _ in range(5):
  shutil.rmtree(path,ignore_errors=True)
  if not path.exists():return
  time.sleep(0.05)
def edit(path:Path,fn):
 o=json.loads(path.read_text());fn(o);path.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
def nop(r):pass
def add_binding(r):
 p=r/"experiments/document-current-state/document-current-state-authority.json";edit(p,lambda o:o.setdefault("file_identities",{}).__setitem__("docs/current/STATE.json","0"*64))
def unregistered(r):
 p=r/"docs/unregistered.json";p.write_text("{}\n");run_git(["add",str(p)],r)
cases=[
 ("valid",nop,True),
 ("missing-state",lambda r:(r/"docs/current/STATE.json").unlink(),False),
 ("duplicate-current-source",lambda r:edit(r/"docs/documentation/document-registry.json",lambda o:o["documents"][0].update({"lifecycle_class":"CURRENT_SOURCE"})),False),
 ("wrong-gate",lambda r:edit(r/"docs/current/STATE.json",lambda o:o["program"]["gate"].update({"id":"WRONG"})),False),
 ("wrong-plan-digest",lambda r:edit(r/"docs/current/STATE.json",lambda o:o["active_plan"].update({"sha256":"0"*64})),False),
 ("duplicate-authority-id",lambda r:edit(r/"docs/current/STATE.json",lambda o:o["accepted_authorities"].append(dict(o["accepted_authorities"][0]))),False),
 ("generated-view-drift",lambda r:(r/"docs/CURRENT_CONTEXT.md").write_text((r/"docs/CURRENT_CONTEXT.md").read_text()+"drift\n"),False),
 ("orientation-reclassified-live",lambda r:edit(r/"docs/documentation/document-registry.json",lambda o:next(d for d in o["documents"] if d["path"]=="docs/PROJECT_ORIENTATION.md").update({"lifecycle_class":"STABLE"})),False),
 ("new-live-binding",add_binding,False),
 ("unregistered-document",unregistered,False),
]
td=Path(tempfile.mkdtemp(prefix="document-current-state-fixture-"));results=[]
try:
 r=td/"r";base_index=materialize(r)
 for name,mutate,expected in cases:
  restore(r,base_index);mutate(r);got=mod.verify(r)["pass"]
  results.append({"name":name,"expected":expected,"actual":got,"pass":got==expected})
finally:cleanup(td)
failed=[c for c in results if not c["pass"]]
result={"schema_version":1,"test_kind":"document-current-state-negative-fixtures-v1","pass":not failed,"check_count":len(results),"pass_count":len(results)-len(failed),"failed_checks":[c["name"] for c in failed],"checks":results,"fixture_materialization":{"source":"staged-index","repository_count":1,"git_commit_created":False,"index_restored_per_case":True,"cleanup_affects_verdict":False}}
print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(0 if result["pass"] else 1)

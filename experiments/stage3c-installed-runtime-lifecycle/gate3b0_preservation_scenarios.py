#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
from gate3b0_preservation_support import *

def run_reinstall(*,name:str,root:Path,rows:list[dict[str,Any]],candidate:dict[str,Any]|None,runner:Path,engine:Path,contract:Path,out:Path)->dict[str,Any]:
 before_reg=registry(root);before_owned=owned_digest(root,rows)
 if candidate is not None:mutation=mutate_owned(root,candidate,name);subject=candidate['path'];before_subject=mutation['after']
 else:subject,before_subject=create_sentinel(root,name);mutation={'before':{'type':'absent'},'after':before_subject}
 op=invoke_engine(runner=runner,engine=engine,contract=contract,root=root,operation='install',artifact='runtime-base',output=out/'install.json')
 verify=invoke_engine(runner=runner,engine=engine,contract=contract,root=root,operation='verify',output=out/'verify.json')
 after_reg=registry(root);after_subject=snapshot(root/'prefix'/subject);after_owned=owned_digest(root,rows)
 if candidate is not None:
  classification='ENFORCED_REPAIR';passed=op['returncode']==0 and op['result'].get('action_counts')=={'noop':713,'repair':1} and op['result'].get('mutation_count')==2 and exact_match(after_subject,candidate) and after_owned==before_owned
 else:
  classification='PRESERVED_NOOP';passed=op['returncode']==0 and op['result'].get('noop') is True and op['result'].get('action_counts')=={'noop':714} and op['result'].get('mutation_count')==0 and after_subject==before_subject and after_owned==before_owned
 passed=passed and verify['returncode']==0 and verify['result'].get('bad_paths')==[] and after_reg['sha256']==before_reg['sha256'] and transactions(root)==[]
 result={'schema_version':1,'scenario':name,'operation':'reinstall','classification':classification,'subject':subject,'candidate':candidate,'mutation':mutation,'subject_before_operation':before_subject,'install':op,'verify':verify,'registry_before':before_reg,'registry_after':after_reg,'owned_digest_before':before_owned,'owned_digest_after':after_owned,'subject_after':after_subject,'transactions_after':transactions(root),'pass':passed}
 write_json(out/'scenario.json',result);return result

def run_uninstall(*,name:str,root:Path,rows:list[dict[str,Any]],candidate:dict[str,Any]|None,runner:Path,engine:Path,contract:Path,out:Path)->dict[str,Any]:
 before_reg=registry(root)
 if candidate is not None:mutation=mutate_owned(root,candidate,name);subject=candidate['path'];before_subject=mutation['after']
 else:subject,before_subject=create_sentinel(root,name);mutation={'before':{'type':'absent'},'after':before_subject}
 op=invoke_engine(runner=runner,engine=engine,contract=contract,root=root,operation='uninstall',artifact='runtime-base',output=out/'uninstall.json')
 verify=invoke_engine(runner=runner,engine=engine,contract=contract,root=root,operation='verify',output=out/'verify.json')
 after_reg=registry(root);after_subject=snapshot(root/'prefix'/subject);remaining=remaining_registered_leaves(root,rows);preserved=op['result'].get('preserved',[])
 if candidate is not None:classification='PRESERVED_AND_DEREGISTERED';expected=[candidate['path']];passed=candidate['path'] in preserved and after_subject==before_subject
 else:classification='UNOWNED_PRESERVED';expected=[];passed=after_subject==before_subject
 passed=passed and op['returncode']==0 and after_reg['artifact_count']==0 and after_reg['owned_path_count']==0 and remaining==expected and verify['returncode']==0 and verify['result'].get('artifact_count')==0 and verify['result'].get('owned_path_count')==0 and verify['result'].get('bad_paths')==[] and transactions(root)==[]
 result={'schema_version':1,'scenario':name,'operation':'uninstall','classification':classification,'subject':subject,'candidate':candidate,'mutation':mutation,'subject_before_operation':before_subject,'uninstall':op,'verify':verify,'registry_before':before_reg,'registry_after':after_reg,'subject_after':after_subject,'remaining_registered_leaves':remaining,'preserved_rows':preserved,'transactions_after':transactions(root),'pass':passed}
 write_json(out/'scenario.json',result);return result

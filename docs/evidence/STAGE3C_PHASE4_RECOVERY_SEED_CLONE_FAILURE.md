# Stage 3-C Phase 4 Recovery Seed Clone Failure

> **Status:** FAIL preserved — corrective rerun required
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase4-installation-recovery-results-20260712-002240.tgz`

## Result archive identity

```text
sha256
  6f236834ea8afbdc7b63dece41c5134c847c24c333b8a2b651c9befc5a9c6635

members
  102

regular files
  88

directories
  14

unsafe member names
  0

special archive entries
  0
```

Result index:

```text
sha256
  1ea69b80eb2c597be59e619f52afa1908cb60c98806a2db3b9a98049e1b2eeb7

indexed files
  85

independent hash, size, and mode mismatches
  0
```

## Workflow result

```text
recovery_scenarios          1
input_mutation              0
independent_verification  125

STAGE3C_PHASE4_INSTALLATION_RECOVERY=FAIL rc=1
```

The independent verifier was correctly blocked because the scenario runner failed before producing `scenario.json`.

## Proven successful prefix

Before the failure, the corrected recovery engine successfully created and verified the runtime seed:

```text
runtime-base install
  create 714
  mutations 715
  PASS

runtime-base registry
  artifacts 1
  owned paths 714
  bad paths 0
  PASS

registry sha256
  4fb42e5ceeabb4eb8a6c321b88446ccc67a1153bd3a4dafb9279b506b39b04d8
```

No crash-recovery scenario had started yet.

## Exact failure

The scenario harness attempted to derive `runtime-development-seed` from `runtime-seed` using:

```python
shutil.copytree(
    source,
    destination,
    symlinks=True,
    copy_function=os.link,
)
```

Termux/Android rejected hardlink creation with `PermissionError: [Errno 13] Permission denied` for regular payload and state files, including:

```text
prefix/bin/python3.14
prefix/lib/engines-3/*.so
prefix/lib/ossl-modules/legacy.so
prefix/lib/python3.14/*.py
prefix/lib/*.so
.cpython-android-cli/lock
.cpython-android-cli/registry.json
```

`shutil.copytree` aggregated those failures and raised `shutil.Error`. The scenario stopped after retained logs 01 and 02.

## Root cause

The failure is in test-root materialization, not in journal recovery, rollback, registry handling, or lock contention.

Hardlinks were also semantically inappropriate for this gate. Even on a filesystem that permits them, they make supposedly isolated crash roots share regular-file inodes with the seed. That weakens the claim that mutation in one scenario root cannot affect another root.

## Corrective contract

Recovery scenario roots must be independent filesystem copies:

```text
regular files
  copy bytes and metadata with shutil.copy2

symlinks
  preserve symlink identity and target

regular-file inode identity
  source and destination must differ

hardlinks between seed and scenario roots
  forbidden
```

The corrected helper performs an inode-independence assertion after every seed clone.

## Local corrective validation

Using the same extracted Gate 2 input, the corrected independent-copy implementation completed the full non-authoritative local matrix:

```text
recovery scenarios       55/55 PASS
retained logs             40/40
independent verifier      82/82 PASS
failed checks                 []
```

This validates the correction logic but does not replace the authoritative Termux rerun.

## Input mutation

```text
input entries before/after
  87 / 87

input fingerprint before/after
  5abf67d8e4d8b23ce569b61aba8ce1e96e69d6c894afcb7e6078ef9842d59d0a

mutation check
  PASS
```

## Claim boundary

This failure result proves only that the original hardlink-based scenario seed clone is invalid on the target and that the workflow failed closed without mutating the copied Gate 2 evidence. It neither proves nor disproves the Gate 3 crash-recovery and lock-contention claims. Those remain pending a corrected target rerun.

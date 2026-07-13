# Stage 3-C Phase 5 Gate 3C Archive Integrity Correction

> **Status:** FROZEN CORRECTION PASS — corrected Termux archive accepted

## Independent inspection result

The first complete Gate 3C target execution preserved valid lifecycle evidence but did not satisfy the archive acceptance boundary.

```text
archive
  stage3c-phase5-gate3c-addon-lifecycle-results-20260713T020629Z.tar.zst

archive sha256
  e92c2de3537c1258910b77301d52ef4a671e7775282061013a5f5b8f76094609

archive members
  824 total
  745 regular
  75 directories
  4 symlinks
  0 special
  0 unsafe member paths

root result-index sha256
  9fc7de3b604dc52fb99b823c465a03221b38e80982fa400f1ecbfc4e023bcf20

scenario / verifier / workflow
  50/50 PASS
  102/102 PASS
  rc 0

external acceptance audit
  26/28 PASS
```

## Acceptance blockers

```text
external absolute symlink
  target-results/scenarios/B06/smoke-results/venv/bin/python
  -> /data/data/com.termux/files/home/.cache/hw-t-results/.../target-work/scenarios/B06/prefix/bin/python

root-index omission
  target-results/scenarios/B06/smoke-results/venv/lib64 -> lib
```

The omission occurred because result-index generation tested `path.is_dir()` before `path.is_symlink()`. A symlink to a directory was therefore skipped. The external venv symlink made the archive non-self-contained and unsuitable for the strict safe-extraction boundary.

## Correction

```text
B06 smoke scratch output
  moved from archived scenario output to non-archived scenario work root

result-tree safety
  reject absolute symlink targets
  reject lexically escaping relative symlink targets
  reject special filesystem entries
  emit canonical result-tree-safety.json

root result-index
  inspect lstat type first
  index safe symlinks before directory recursion
  include symlink-directory entries
  regenerate after final workflow/wrapper status
```

The corrected repository verifier adds `smoke_transient_not_archived`, increasing the target evidence verifier surface from 102 to 103 checks.

## Preserved authority

The correction does not change:

```text
Gate 3B authority archive or index
50-scenario Gate 3C matrix
artifact manifests or archives
installation/recovery engine
registry or journal schema
prerequisite and collision policy
rollback tombstone semantics
Gate 3D or upgrade/downgrade boundaries
```

The first archive remains immutable non-accepting evidence. A fresh corrected target archive must be generated and independently checked before Gate 3C can close.


## Corrected rerun acceptance

```text
archive
  stage3c-phase5-gate3c-addon-lifecycle-results-20260713T033412Z.tar.zst

archive sha256
  43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a

archive members
  801 total / 732 regular / 69 directories
  0 symlinks / 0 hardlinks / 0 special / 0 unsafe

result-tree-safety sha256
  ab338579025da63dec1750e3a7649c9a5f260cd4556f60ab3b3ade6140187bb9

root result-index sha256
  fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c

indexed files
  731/731 exact

scenario / verifier / external audit
  50/50 PASS / 103/103 PASS / 27/27 PASS
```

The corrected archive contains no links or special entries. The external audit independently recomputed root-index membership and all recorded regular-file identities. The correction is therefore frozen as accepted; the first archive remains immutable diagnostic evidence.

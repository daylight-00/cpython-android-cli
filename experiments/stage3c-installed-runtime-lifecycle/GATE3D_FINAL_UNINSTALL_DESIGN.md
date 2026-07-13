# Stage 3-C Phase 5 Gate 3D: Final Uninstall and Ownership Boundary Design

> **Status:** DESIGN FROZEN — target evidence pending
> **Prerequisites:** frozen Gate 3B preserve-and-report acceptance and frozen Gate 3C addon lifecycle acceptance
> **Target:** Termux on Android arm64

## Product question

> Can the complete frozen three-artifact product be reduced through valid addon removal to runtime-only and then uninstall runtime-base while preserving exact ownership, approved residuals, recovery semantics, and final registry/filesystem audit boundaries?

Gate 3D consumes Gate 3B and Gate 3C as immutable authorities. It does not reopen the transaction engine, registry schema, manifest identities, runtime preservation policy, or addon dependency policy.

## Frozen authorities

```text
Gate 3B archive
  stage3c-phase5-gate3b-preservation-acceptance-results-20260713-024946.tgz
  sha256 0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b
  root result-index f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9
  29/29 scenarios + 62/62 verifier PASS

Gate 3C archive
  stage3c-phase5-gate3c-addon-lifecycle-results-20260713T033412Z.tar.zst
  sha256 43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a
  root result-index fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c
  result-tree-safety ab338579025da63dec1750e3a7649c9a5f260cd4556f60ab3b3ade6140187bb9
  50/50 scenarios + 103/103 verifier + 27/27 external audit PASS
```

## State boundary

```text
empty                    0 artifacts      0 owned paths
runtime                  1 artifact     714 owned paths
runtime + development    2 artifacts   1168 owned paths
runtime + test           2 artifacts   2502 owned paths
composed                 3 artifacts   2956 owned paths
```

Runtime-base removal is valid only from `runtime`. From either one-addon state or the fully composed state, removal must reject before mutation.

The valid composed-product teardown orders remain exactly:

```text
composed -> remove test -> remove development -> remove runtime
composed -> remove development -> remove test -> remove runtime
```

The intermediate runtime removal attempt remains invalid while the other addon is installed.

## Final-state distinctions

Gate 3D must report these independently:

```text
registry empty
owned payload absent
approved residuals present or absent
transaction inventory / rollback tombstone state
prefix root physically empty or non-empty
```

They are not synonyms.

### Exact-owned teardown

```text
registry empty
all matching owned payload absent
approved residual inventory empty
transactions empty
prefix root contains no payload entries
```

### Modified-owned residual

```text
modified regular or symlink preserved exactly
preserved leaf reported and deregistered
registry empty
all other matching owned payload absent
only required non-empty ancestor directories retained
prefix root non-empty
```

### Unowned sentinel residual

```text
sentinel preserved, unowned, and unchanged
registry empty
all matching owned payload absent
only required non-empty ancestor directories retained
prefix root non-empty
```

### Mixed approved residual

A modified-owned leaf and an unowned sentinel may coexist. Both identities and only their required ancestors are retained; the registry remains empty.

## Canonical subjects

```text
modified runtime-owned regular
  lib/python3.14/LICENSE.txt

modified runtime-owned symlink
  bin/python

unowned file sentinel
  lib/python3.14/site-packages/gate3d-user-file.txt

unowned directory sentinel
  lib/python3.14/site-packages/gate3d-user-dir
```

The shared structural namespace remains:

```text
lib
lib/python3.14
```

It is runtime-owned, never adopted by an addon, removed when empty, and retained only when a surviving residual descendant requires it.

## Acceptance matrix

The canonical machine matrix contains exactly 44 scenarios:

```text
preflight rejection                6
valid and guarded teardown         8
residual ownership                10
crash recovery                    12
lock exclusion                     2
final-state and evidence audit     6
```

Canonical matrix:

```text
experiments/stage3c-installed-runtime-lifecycle/gate3d-final-uninstall-matrix.json
```

### Preflight

The matrix rejects runtime-base uninstall before mutation from:

```text
composed
runtime + development
runtime + test
composed after removing only test
composed after removing only development
empty / runtime-base not installed
```

### Teardown

The matrix covers both complete composed teardown orders, both one-addon starting states, runtime-only exact removal, guarded intermediate rejection followed by completion, and repeated final uninstall rejection without mutation.

### Residual ownership

The matrix covers modified regular and symlink leaves, unowned file and directory sentinels, unowned descendants inside runtime-owned directories, shared structural namespace retention, combined approved residuals, and later reinstall rejection over a deregistered preserved residual.

### Crash recovery

Four final-uninstall subjects are crossed with all three accepted crash boundaries:

```text
subjects
  exact owned
  modified-owned regular
  modified-owned symlink
  unowned file sentinel

boundaries
  PREPARED       rc 90
  late APPLYING  rc 93
  COMMITTED      rc 92
```

PREPARED and late APPLYING restore the exact prior runtime-only state and retain one `ROLLED_BACK` audit tombstone. The second recovery reports `NOOP_ROLLED_BACK`.

COMMITTED recovery finalizes the exact accepted final residual class, removes the transaction, and the second recovery observes zero transactions.

### Lock exclusion

Final runtime uninstall and recovery must reject lock contention with rc 44 and zero mutation.

## Evidence contract

The future Termux wrapper must:

```text
verify exact Gate 3B and Gate 3C input hashes
extract authorities freshly
create inode-separated scenario roots
capture stdout and stderr synchronously
preserve real process return codes
record before/after registry and payload snapshots
record residual and transaction inventories
record first and second recovery outcomes
write canonical JSON
write result-tree-safety.json
recompute a complete root result-index
create a .tar.zst archive on PASS or FAIL
run an independent verifier
state the claim boundary explicitly
```

Historical `.tgz` evidence remains immutable.

## Local design verification

```text
bash experiments/stage3c-installed-runtime-lifecycle/run-gate3d-final-uninstall-design.sh
```

## Target implementation readiness

The frozen matrix now has a target runner, independent verifier, result-tree safety/index finalizer, and one-command Termux wrapper. Local semantic validation passes 44/44 scenarios and 138/138 verifier checks. The local development run used fast-success only for successful setup operations; the target wrapper preserves real target operations and does not set that development flag.

```text
gate3d_final_uninstall_support.py
run-gate3d-final-uninstall.py
verify-gate3d-final-uninstall.py
finalize-gate3d-evidence.py
run-gate3d-final-uninstall-termux.sh
```

This is implementation readiness, not target acceptance.

## Claim boundary

A design PASS proves only that the frozen authorities and 44-scenario matrix are internally consistent and policy-bounded. It does not prove target final uninstall, close Gate 3D, or authorize upgrade/downgrade. Gate 3D closes only after a complete Termux `.tar.zst` archive is independently inspected. Gate 4 remains deferred until a second complete frozen product identity exists.

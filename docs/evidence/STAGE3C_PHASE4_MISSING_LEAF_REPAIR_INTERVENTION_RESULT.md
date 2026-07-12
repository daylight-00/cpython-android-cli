# Stage 3-C Phase 4I: Missing Registered Leaf Repair Intervention Result

> **Status:** FROZEN PASS
> **Target:** Termux on Android arm64
> **Gate 3A product acceptance:** NOT CLAIMED

## Executive result

```text
PHASE4I_EXACT_REINSTALL_NOOP=PASS
PHASE4I_IN_PLACE_REPAIR_REGRESSION=4/4 PASS
PHASE4I_MISSING_LEAF_REPAIR=2/2 PASS
PHASE4I_CRASH_RECOVERY=12/12 PASS
PHASE4I_INTERVENTION_VERIFICATION=51/51 PASS
PHASE4I_GATE3A_PRODUCT_ACCEPTANCE=NOT_CLAIMED
STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION=PASS
```

The intervention is recovery-safe for missing registered regular and symlink leaves at all tested success and crash boundaries. This result freezes the correction itself, not the complete installed-runtime product acceptance claim.

## Authoritative archive identity

```text
archive
  stage3c-phase4-missing-leaf-repair-intervention-results-20260712-180237.tgz

sha256
  d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a

size
  23,980,515 bytes

members
  580

regular files / directories
  530 / 50

symlinks / hardlinks / special / unsafe paths
  0 / 0 / 0 / 0
```

## Result-index identities

```text
Phase 4I root result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6

Phase 4I root indexed files
  523 / 523 exact

accepted Phase 4 result-index sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

accepted Phase 4 indexed files
  294 / 294 exact

nested Phase 4 indices
  165 / 165 exact
  154 / 154 exact
  134 / 134 exact
   75 /  75 exact

hash, size, mode, missing, duplicate, and coverage mismatches
  0
```

## Workflow and input immutability

```text
workflow return codes
  scenarios       0
  input mutation  0
  verification    0

Phase 4 copied input entries
  324 / 324

Phase 4 copied input fingerprint before / after
  77501afe6128de9df21405cace0004a1d54bebf880d64ef920768727606fb80d
  exact
```

All 157 generated JSON files were canonical. Raw process records and scenario-embedded records were exact.

## Seed authority

```text
fresh runtime-base install
  create actions       714
  mutations            715
  PASS

engine verify
  artifacts              1
  owned rows            714
  bad paths               0

portable payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

payload shape
  714 entries
  57 directories
  654 regular files
  3 symlinks
  0 special

registry sha256
  4fb42e5ceeabb4eb8a6c321b88446ccc67a1153bd3a4dafb9279b506b39b04d8

transaction residue
  0
```

Nineteen scenario roots were independent copies. Root, registry, and representative payload inodes were separate in all nineteen roots.

## Success and regression scenarios

Seven scenarios passed:

```text
exact-noop
regular-bytes
regular-mode
regular-wrong-type
symlink-target
missing-regular
missing-symlink
```

### Exact reinstall

```text
action counts
  noop 714

mutation count
  0

registry identity
  unchanged

portable identity
  unchanged

transaction residue
  0
```

### Existing-path repair regressions

All four prior supported repair classes remained exact:

```text
regular byte corruption
regular mode corruption
registered regular replaced by directory
symlink target corruption
```

For each:

```text
pre-repair bad paths
  exactly 1

install actions
  noop 713
  repair 1

mutation count
  2

post-repair bad paths
  0

registry identity
  unchanged

portable identity
  exact

transaction residue
  0
```

### Missing registered leaf repair

Both missing classes succeeded:

```text
missing registered regular
  lib/python3.14/LICENSE.txt

missing registered symlink
  bin/python
```

For each:

```text
pre-repair verify
  rc 44
  exactly one bad path

install
  PASS
  noop 713
  repair 1
  mutation count 2

post-repair verify
  PASS
  bad paths 0

registry identity
  unchanged

portable payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

transaction residue
  0
```

Final repaired identities matched the frozen manifest and source archive:

```text
regular candidate
  lib/python3.14/LICENSE.txt
  mode 0600
  size 13804
  sha256 b0e25a78cffb43f4d92de8b61ccfa1f1f98ecbc22330b54b5251e7b6ba010231

symlink candidate
  bin/python
  mode 0777
  target python3
```

## Crash-recovery matrix

Each missing leaf type was tested at six boundaries:

```text
prepared
intent-1
mutation-1
intent-2
mutation-2
committed
```

Total:

```text
2 leaf types × 6 boundaries = 12 / 12 PASS
```

### Pre-commit recovery

```text
prepared
  state PREPARED
  mutations []
  recovery ROLLED_BACK
  restored_count 0

intent-1
  state APPLYING
  created INTENT
  recovery ROLLED_BACK
  restored_count 0

mutation-1
  state APPLYING
  created APPLIED
  recovery ROLLED_BACK
  restored_count 1

intent-2
  state APPLYING
  created APPLIED
  registry INTENT
  recovery ROLLED_BACK
  restored_count 2

mutation-2
  state APPLYING
  created APPLIED
  registry APPLIED
  recovery ROLLED_BACK
  restored_count 2
```

All ten pre-commit scenarios restored:

```text
original missing leaf state
prior registry identity
post-recovery verify with the original single missing path
retained ROLLED_BACK journal
second recovery NOOP_ROLLED_BACK
```

### Committed recovery

For regular and symlink committed boundaries:

```text
crash return code
  92

journal
  COMMITTED
  created APPLIED
  registry APPLIED

first recovery
  FINALIZED_COMMIT

final leaf
  exact manifest identity

registry
  exact

engine verify
  PASS

transaction residue
  0

second recovery
  transaction_count 0
```

## Independent verification

```text
scenario checks
  39 / 39

independent checks
  51 / 51

failed checks
  0

missing files
  0
```

Independent inspection also reconfirmed every raw process result, journal mutation status, recovery action, restored count, final candidate identity, registry identity, portable fingerprint, and clone inode-separation result.

## Frozen correction boundary

The accepted correction is:

```text
existing registered mismatch
  replaced mutation
  move current path to backup
  publish frozen member

missing registered non-directory
  created mutation
  skip nonexistent backup move
  publish frozen member
```

The correction reuses the existing `created` rollback semantics. It introduces no new journal schema, registry schema, manifest, archive, ownership, uninstall, or addon policy.

## Claim boundary

This PASS proves:

```text
missing regular repair
missing symlink repair
existing repair regression safety
exact reinstall NOOP regression
recovery safety at twelve crash boundaries
```

It does not yet prove:

```text
Gate 3A installed-runtime product acceptance
post-repair Python runtime behavior
HTTPS
uv venv or uv run
native closure
extension imports
Gate 1 regression under the accepted correction
Gate 2 relocation regression under the accepted correction
```

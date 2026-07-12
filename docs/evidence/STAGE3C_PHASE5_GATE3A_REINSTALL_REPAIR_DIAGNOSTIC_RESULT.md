# Stage 3-C Phase 5 Gate 3A0: Reinstall and Repair Diagnostic Result

> **Status:** FROZEN DIAGNOSTIC PASS
> **Product acceptance:** BLOCKED
> **Target:** Termux on Android arm64

## Executive result

```text
GATE3A_EXACT_REINSTALL_NOOP=714/714 PASS
GATE3A_IN_PLACE_REPAIRS=4/4 CLASSIFIED
GATE3A_MISSING_LEAF_REPAIR=2/2 UNSUPPORTED_CLASSIFIED
GATE3A_RECOVERY_RESIDUE=2/2 CLASSIFIED
GATE3A_DIAGNOSTIC_VERIFICATION=31/31 PASS
GATE3A_PRODUCT_ACCEPTANCE=NOT_CLAIMED
STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC=PASS
```

The diagnostic result matches the source-derived behavior matrix. It does not establish Gate 3A product acceptance.

## Authoritative archive identity

```text
stage3c-phase5-gate3a-reinstall-repair-diagnostic-results-20260712-172353.tgz

sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2

size
  23,954,673 bytes

members
  409

regular files / directories
  372 / 37

symlinks / hardlinks / special / unsafe paths
  0 / 0 / 0 / 0
```

## Result-index identities

```text
Gate 3A0 root result-index sha256
  a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b

Gate 3A0 root indexed files
  365 / 365 exact

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
  diagnostic      0
  verification    0
  input mutation  0

Phase 4 copied input entries
  324 / 324

Phase 4 copied input fingerprint before / after
  77501afe6128de9df21405cace0004a1d54bebf880d64ef920768727606fb80d
  exact
```

All generated diagnostic and verifier JSON files were canonical.

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

transaction residue
  0
```

Seven scenario roots were independent copies. Root, registry, and representative payload inodes were separate in all seven scenarios.

## Exact same-version reinstall

```text
action counts
  noop 714

mutation count
  0

registry identity
  unchanged

portable payload identity
  unchanged

transaction residue
  0

engine verify
  PASS
```

Classification:

```text
exact-same-version-noop
```

## Supported in-place repairs

The frozen engine repaired all four existing-path mismatch classes:

```text
regular byte corruption
regular mode corruption
symlink target corruption
registered regular replaced by directory
```

For every scenario:

```text
pre-repair bad paths
  exactly 1

action counts
  noop 713
  repair 1

mutation count
  2

post-repair bad paths
  0

registry identity
  unchanged

portable payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

transaction residue
  0
```

Final candidate identities matched both the frozen manifest and runtime-base archive:

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

Classification:

```text
in-place-registered-repair-supported
```

## Missing registered leaf result

Two missing-leaf classes were tested independently:

```text
missing registered regular
  lib/python3.14/LICENSE.txt

missing registered symlink
  bin/python
```

Both produced the same authoritative sequence:

```text
pre-repair verify
  rc 44
  exactly one bad path

install
  rc 44
  FileNotFoundError(2, 'No such file or directory')

journal before recovery
  state APPLYING
  one replaced mutation in INTENT state

first recovery
  action ROLLED_BACK
  restored_count 0

journal after first recovery
  state ROLLED_BACK
  retained

second recovery
  action NOOP_ROLLED_BACK
  restored_count 0

post-recovery verify
  rc 44
  same bad path

registry row
  retained

leaf
  absent
```

Classification:

```text
missing-leaf-repair-unsupported
```

## Independent verifier

```text
scenario checks
  17 / 17

independent checks
  31 / 31

failed checks
  0

missing files
  0
```

The independent verifier reopened raw engine outputs, journal inventories, registry identities, clone-separation evidence, candidate identities, and all scenario outputs rather than trusting scenario-level `pass` fields.

## Architecture conclusion

Gate 3A product acceptance is blocked by a confirmed frozen-engine defect:

```text
registered missing non-directory
  planned as repair
  recorded as replaced
  durable_move(absent source, backup)
  FileNotFoundError
```

The correct recovery-safe mutation class for a missing registered leaf is `created`, not `replaced`:

```text
record created intent
publish frozen archive member
rollback removes a published replacement when applied
rollback is a no-op when failure occurs before publication
```

This requires an explicit, narrowly scoped Phase 4 architecture intervention and downstream revalidation. It must not be presented as a Phase 5-only test correction.

## Claim boundary

This diagnostic PASS proves:

```text
exact same-version NOOP
four supported in-place registered repair classes
missing regular repair unsupported
missing symlink repair unsupported
recovery transition and retained residue after each failure
```

It does not prove:

```text
Gate 3A product acceptance
missing-leaf repair
modified owned-leaf preservation
unowned sentinel preservation
addon lifecycle
uninstall
upgrade or downgrade
```

# Stage 3-C Phase 5 Gate 3B0 Preservation Diagnostic Result

> **Status:** FROZEN DIAGNOSTIC PASS
> **Target:** Termux on Android arm64
> **Accepted evidence:** complete independently inspected TGZ

## Archive identity

```text
archive
  stage3c-phase5-gate3b0-preservation-diagnostic-results-20260712-211837.tgz

sha256
  ed5cb08cc576e74cacac4077cf9c9d7f3164a34913197aae9ef10cc8c113801a

size
  22,701,335 bytes

members
  131

regular files / directories
  111 / 20

unsafe / link / special entries
  0 / 0 / 0
```

## Result-index authority

```text
root result-index sha256
  7a8e982a44118dac3f232b2fefb578d22bedc0c7d32a6267ab3cd55c5e8deb27

root indexed files
  110/110 exact

accepted Gate 2R result-index sha256
  69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c

Phase 4 contract-index sha256
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3

contract-index files
  7/7 exact
```

The root index had zero hash, size, mode, target, type, missing, duplicate, or coverage mismatches.

## Verification

```text
scenario checks
  16/16 PASS

independent verifier
  40/40 PASS

scenario runner return code
  0

independent verifier return code
  0

workflow / wrapper return code
  0 / 0

raw process mismatches
  0

generated machine JSON
  59/59 canonical

transaction residue
  0 in all scenarios
```

## Accepted input and engine authority

```text
Gate 2R archive sha256
  8e2c131567d78a4208e7c8eb02e783a479713f6d867a3e5cd98eae60aa5738a7

recovery_engine_missing_leaf.py sha256
  33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a

recovery_operations_missing_leaf.py sha256
  61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021

seed installation
  create 714 / mutations 715

seed registry
  1 artifact / 714 owned rows
```

All eight scenario roots were inode-separated from the seed for the root, registry, registered regular probe, and registered symlink probe.

## Frozen current-behavior census

```text
reinstall-owned-regular
  ENFORCED_REPAIR

reinstall-owned-symlink
  ENFORCED_REPAIR

reinstall-unowned-file
  PRESERVED_NOOP

reinstall-unowned-directory
  PRESERVED_NOOP

uninstall-owned-regular
  PRESERVED_AND_DEREGISTERED

uninstall-owned-symlink
  PRESERVED_AND_DEREGISTERED

uninstall-unowned-file
  UNOWNED_PRESERVED

uninstall-unowned-directory
  UNOWNED_PRESERVED
```

### Reinstall behavior

Both modified registered leaves produced:

```text
planner actions
  noop 713 / repair 1

mutation count
  2

candidate identity
  restored exactly

registry
  byte exact before and after

registry-owned digest
  exact before and after

engine verify
  0 bad paths
```

Both unowned sentinels produced:

```text
planner actions
  noop 714

mutation count
  0

sentinel identity
  exact before and after

registry-owned digest
  exact before and after

registry
  byte exact
```

The unowned directory sentinel recursively preserved its child mode, size, and SHA256.

### Uninstall behavior

Both modified registered leaves were preserved exactly while registry ownership transitioned from one artifact and 714 rows to zero artifacts and zero rows.

```text
modified regular residual
  lib/python3.14/LICENSE.txt

modified symlink residual
  bin/python
```

The uninstall result reported each modified leaf in `preserved`. Non-empty parent directories were also reported as preserved where appropriate.

Both unowned sentinels were preserved exactly. No originally registered leaf remained in those scenarios. Empty-registry verification returned PASS with zero owned rows and zero bad paths.

## Contract decision

The frozen installation contract already specifies the observed behavior:

```text
registry.local_modification_uninstall_policy
  preserve-and-report

uninstall.modified_regular_or_symlink
  PRESERVE_AND_REPORT

uninstall.owned_directory
  REMOVE_ONLY_WHEN_EMPTY

uninstall.structural_parent
  PRESERVE_NAMESPACE

uninstall.unowned_descendant
  PRESERVE
```

Therefore Gate 3B0 does not authorize an intervention. The diagnostic matches the frozen contract.

## Identity boundary

Registry-owned directory identity is type plus mode only. Unowned descendants are a separate evidence surface and are recursively fingerprinted when needed. A full-prefix portable fingerprint is not the sole identity once intentional unowned sentinels exist.

## Next boundary

Gate 3B product acceptance must validate the frozen preserve-and-report contract, including exact reporting and residual identity, registry transitions, unaffected-path behavior, and crash recovery around preserved-path uninstall boundaries.

## Claim boundary

This PASS freezes the current-behavior census and its agreement with the frozen installation contract. It does not yet claim preserved-path crash recovery, Gate 3B product acceptance, addon lifecycle, final uninstall, upgrade, or downgrade.

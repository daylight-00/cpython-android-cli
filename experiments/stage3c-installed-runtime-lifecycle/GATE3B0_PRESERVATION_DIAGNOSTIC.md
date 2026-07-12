# Stage 3-C Phase 5 Gate 3B0: Preservation Boundary Diagnostic

> **Status:** ACTIVE — authoritative Termux evidence pending
> **Prerequisite:** frozen Gate 2R corrected-engine relocation
> **Target:** Termux on Android arm64

## Diagnostic question

> How does the accepted corrected engine currently treat modified registered leaves and unowned sentinels during same-version reinstall and runtime-base uninstall?

This is a diagnostic census. It does not accept or change preservation policy.

## Frozen input

```text
Gate 2R archive
  stage3c-phase5-gate2r-corrected-engine-relocation-results-20260712-202419.tgz

archive sha256
  8e2c131567d78a4208e7c8eb02e783a479713f6d867a3e5cd98eae60aa5738a7

Gate 2R result-index sha256
  69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c

Phase 4 contract-index sha256
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

Corrected-engine identities:

```text
recovery_engine_missing_leaf.py
  33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a

recovery_operations_missing_leaf.py
  61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021
```

## Scenario matrix

One fresh corrected-engine seed is copied into eight inode-separated roots:

```text
reinstall-owned-regular
reinstall-owned-symlink
reinstall-unowned-file
reinstall-unowned-directory
uninstall-owned-regular
uninstall-owned-symlink
uninstall-unowned-file
uninstall-unowned-directory
```

Deterministic registered candidates:

```text
regular
  lib/python3.14/LICENSE.txt

symlink
  bin/python
```

Unowned sentinels:

```text
file
  lib/python3.14/site-packages/gate3b0-user-file.txt

directory
  lib/python3.14/site-packages/gate3b0-user-dir/
```

The directory sentinel includes recursively fingerprinted content.

## Expected current-behavior classification

```text
registered mismatch + reinstall
  ENFORCED_REPAIR

unowned sentinel + reinstall
  PRESERVED_NOOP

modified registered leaf + uninstall
  PRESERVED_AND_DEREGISTERED

unowned sentinel + uninstall
  UNOWNED_PRESERVED
```

These names classify observed behavior only. They are not policy approval.

## Identity boundary

Gate 3B0 deliberately separates:

```text
registry-owned identity
  registered directory = type + mode
  registered regular = type + mode + size + SHA256
  registered symlink = type + mode + target

unowned sentinel identity
  independent exact snapshot
  directory content recursively fingerprinted
```

A full-prefix portable fingerprint is not a valid sole identity once unowned sentinels are intentionally present. Registry-owned identity and unowned residual identity must be reported separately.

## Required evidence

For each reinstall scenario:

```text
mutation/sentinel before operation
planner result and action counts
registry before/after
registry-owned digest before/after
subject after operation
engine verify
transaction residue
```

For each uninstall scenario:

```text
subject before operation
uninstall preserved rows
registry transition to 0 artifacts / 0 owned rows
remaining originally registered leaves
subject after operation
empty-registry engine verify
transaction residue
```

## Verification

```text
scenario checks
  16

independent verifier checks
  40
```

The verifier reopens raw engine process outputs, accepted Gate 2R and contract identities, seed installation, clone separation, all eight scenario records, registry transitions, residual leaves, subject snapshots, canonical generated JSON, and diagnostic claim boundaries.

## One-command Termux runner

```text
experiments/stage3c-installed-runtime-lifecycle/run-gate3b0-preservation-diagnostic-termux.sh
```

The wrapper performs accepted Gate 2R TGZ hash verification, fresh extraction, execution, synchronous log capture, status and result-index generation, and TGZ packaging on PASS or FAIL.

## Expected markers

```text
GATE3B0_SCENARIO_CENSUS=16/16 PASS
GATE3B0_INDEPENDENT_VERIFICATION=40/40 PASS
GATE3B0_PRODUCT_ACCEPTANCE=NOT_CLAIMED
STAGE3C_PHASE5_GATE3B0_PRESERVATION_DIAGNOSTIC=PASS

TERMUX_EVIDENCE_ARCHIVE=...
TERMUX_EVIDENCE_ARCHIVE_SHA256=...
TERMUX_EVIDENCE_ARCHIVE_SIZE=...
TERMUX_WORKFLOW_RETURN_CODE=0
```

## Claim boundary

A PASS freezes the current-behavior census only. It does not accept uninstall preservation policy, crash-recovery behavior for preserved paths, addon lifecycle, final uninstall, upgrade, or downgrade.

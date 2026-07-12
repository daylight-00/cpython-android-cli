# Phase 5 Gate 3B0 Preservation Diagnostic Handoff — 2026-07-12

> **Status:** FROZEN DIAGNOSTIC PASS
> **Accepted evidence:** complete independently inspected Termux TGZ
> **Next boundary:** Gate 3B preserve-and-report product acceptance

## Frozen evidence identity

```text
archive
  stage3c-phase5-gate3b0-preservation-diagnostic-results-20260712-211837.tgz

archive sha256
  ed5cb08cc576e74cacac4077cf9c9d7f3164a34913197aae9ef10cc8c113801a

archive size
  22,701,335 bytes

archive members
  131

root result-index sha256
  7a8e982a44118dac3f232b2fefb578d22bedc0c7d32a6267ab3cd55c5e8deb27

root indexed files
  110/110 exact
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3B0_PRESERVATION_DIAGNOSTIC_RESULT.md
```

## Frozen authority

```text
Gate 2R result-index sha256
  69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c

Phase 4 contract-index sha256
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3

corrected engine sha256
  33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a

corrected operations sha256
  61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021
```

## Frozen verification

```text
scenario checks
  16/16 PASS

independent verifier
  40/40 PASS

workflow / wrapper rc
  0 / 0

raw process mismatches
  0

generated JSON
  59/59 canonical

transaction residue
  0
```

## Frozen current-behavior census

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

Exact scenarios:

```text
reinstall-owned-regular       ENFORCED_REPAIR
reinstall-owned-symlink       ENFORCED_REPAIR
reinstall-unowned-file        PRESERVED_NOOP
reinstall-unowned-directory   PRESERVED_NOOP
uninstall-owned-regular       PRESERVED_AND_DEREGISTERED
uninstall-owned-symlink       PRESERVED_AND_DEREGISTERED
uninstall-unowned-file        UNOWNED_PRESERVED
uninstall-unowned-directory   UNOWNED_PRESERVED
```

## Contract decision

The frozen installation contract explicitly defines:

```text
local modification uninstall policy
  preserve-and-report

modified regular or symlink
  PRESERVE_AND_REPORT

owned directory
  REMOVE_ONLY_WHEN_EMPTY

structural parent
  PRESERVE_NAMESPACE

unowned descendant
  PRESERVE
```

The Termux census matches this contract exactly. No intervention is authorized or required.

## Identity boundary

Registry-owned identity and unowned residual identity are separate evidence surfaces. Registered directory identity is type plus mode; intentional unowned descendants are captured independently and recursively. A full-prefix portable fingerprint is not the sole identity when unowned sentinels are present.

## Next Gate 3B requirements

Gate 3B product acceptance must prove the existing preserve-and-report contract rather than change it:

```text
exact preserved path reporting
exact modified-leaf residual identity
exact unowned sentinel residual identity
registry 1/714 → 0/0
all matching owned leaves removed
only contract-approved parent directories preserved
unaffected-path identity
transaction residue 0
pre-commit rollback restores installed state and registry
committed recovery preserves residual state and empty registry
idempotent second recovery
```

Reinstall enforcement and unowned sentinel preservation should remain regression checks.

## Claim boundary

Gate 3B0 proves only the current-behavior census and its agreement with the frozen contract. Preserved-path crash recovery, Gate 3B product acceptance, addon lifecycle, final uninstall, upgrade, and downgrade remain unproved.

# Phase 5 Gate 3B0 Preservation Diagnostic Handoff — 2026-07-12

> **Status:** ACTIVE — authoritative Termux evidence pending
> **Prerequisite:** frozen Gate 2R corrected-engine relocation
> **Target:** Termux on Android arm64

## Frozen input authority

```text
Gate 2R archive
  stage3c-phase5-gate2r-corrected-engine-relocation-results-20260712-202419.tgz

archive sha256
  8e2c131567d78a4208e7c8eb02e783a479713f6d867a3e5cd98eae60aa5738a7

result-index sha256
  69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c

Phase 4 contract-index sha256
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

Corrected engine:

```text
recovery_engine_missing_leaf.py
  33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a

recovery_operations_missing_leaf.py
  61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021
```

## Frozen-code census before target execution

Current installer behavior:

```text
registered exact path
  noop

registered mismatch
  repair / repair-dir

unowned non-colliding path
  ignored by reinstall planner
```

Current uninstaller behavior:

```text
registered leaf matching registry
  remove

registered leaf not matching registry
  preserve path and remove registry ownership

unowned path
  untouched

owned directory that is non-empty or wrong type
  preserve
```

An empty registry verifies successfully even when deregistered residual paths remain. This is current behavior, not accepted preservation policy.

## Diagnostic matrix

Create one corrected-engine seed and eight inode-separated roots:

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
lib/python3.14/LICENSE.txt
bin/python
```

Unowned sentinels:

```text
lib/python3.14/site-packages/gate3b0-user-file.txt
lib/python3.14/site-packages/gate3b0-user-dir/
```

## Expected current-behavior classifications

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

These labels classify observed behavior only.

## Identity boundary

Do not use a full-prefix portable fingerprint as the sole identity after intentionally adding unowned sentinels.

Use two independent surfaces:

```text
registry-owned identity
  registered directories: type + mode
  registered regular files: type + mode + size + SHA256
  registered symlinks: type + mode + target

unowned sentinel identity
  exact independent snapshot
  directory content recursively fingerprinted
```

This prevents an unowned child from being misclassified as a mutation of an owned parent directory.

## Verification contract

```text
scenario checks
  16

independent verifier checks
  40
```

The verifier must reopen accepted Gate 2R evidence, contract identity, corrected-engine identity, seed install/verify, clone separation, raw process outputs, all eight scenario records, registry transitions, residual registered leaves, sentinel snapshots, canonical JSON, and the diagnostic-only claim boundary.

## Published implementation identities

```text
gate3b0_preservation_support.py
  9f6d7cef64af85ac7a4232e0bc697eff60b9257c

gate3b0_preservation_scenarios.py
  944dc36c6c9ed9419bb4736a652f9cc134d6cfd2

run-gate3b0-preservation-diagnostic.py
  6aa45fad8429815f4b94966da33122027656ed6f

verify-gate3b0-preservation-diagnostic.py
  64d1004f1b64e757af8db0c1faa932558faafecd

run-gate3b0-preservation-diagnostic-termux.sh
  7be11ca5d3990c394bd6184a7e6ef4f3a736eadf
```

## Local orchestration validation

Using the accepted Gate 2R contract/archive and a local executor implementing the same install/uninstall/verify CLI semantics:

```text
scenario runner
  16/16 PASS

independent verifier
  40/40 PASS

eight classifications
  exact

raw process cross-check
  PASS
```

This is not target authority. Only a complete Termux TGZ can freeze Gate 3B0.

## Termux execution policy

Use the single wrapper:

```text
experiments/stage3c-installed-runtime-lifecycle/run-gate3b0-preservation-diagnostic-termux.sh
```

It verifies the accepted Gate 2R archive, performs fresh extraction, executes the diagnostic, captures logs synchronously, writes workflow/wrapper status and result-index evidence, and packages a TGZ on PASS or FAIL.

## Claim boundary

A Gate 3B0 PASS freezes the current-behavior census only. It does not accept uninstall preservation policy, preserved-path crash recovery, addon lifecycle, final uninstall semantics, upgrade, or downgrade.

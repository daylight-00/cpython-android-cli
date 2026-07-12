# Phase 5 Gate 3B Preserve-and-Report Product Acceptance Handoff — 2026-07-12

> **Status:** FROZEN PASS — authoritative Termux evidence accepted
> **Prerequisite:** frozen Gate 3B0 preservation diagnostic
> **Target:** Termux on Android arm64

## Frozen prerequisite

```text
Gate 3B0 archive
  stage3c-phase5-gate3b0-preservation-diagnostic-results-20260712-211837.tgz

archive sha256
  ed5cb08cc576e74cacac4077cf9c9d7f3164a34913197aae9ef10cc8c113801a

result-index sha256
  7a8e982a44118dac3f232b2fefb578d22bedc0c7d32a6267ab3cd55c5e8deb27

scenario checks
  16/16

independent verifier
  40/40
```

## Accepted policy

The frozen installation contract already specifies:

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

No policy intervention is required.

## Product-acceptance matrix

Happy paths:

```text
modified registered regular + reinstall
modified registered symlink + reinstall
unowned file + reinstall
unowned directory + reinstall
modified registered regular + uninstall
modified registered symlink + uninstall
unowned file + uninstall
unowned directory + uninstall
```

Crash subjects:

```text
modified registered regular
modified registered symlink
unowned file sentinel
unowned directory sentinel
```

Crash boundaries per subject:

```text
crash after PREPARED
late APPLYING crash after registry INTENT is persisted and before registry write
crash after COMMITTED before cleanup
```

Total topology:

```text
happy roots
  8

crash roots
  12

inode-separated roots
  20

scenario checks
  29

independent verifier checks
  62
```

## Late APPLYING authority

A successful uninstall reports `mutation_count`, but failed owned-directory `rmdir` attempts create an intent and then remove it from the journal without incrementing the applied mutation count. Therefore the registry-intent ordinal is:

```text
registry_intent_ordinal =
  happy_uninstall.mutation_count
  + count(preserved paths that are registered directories)
```

The crash command is:

```text
--crash-after-intents=<registry_intent_ordinal>
```

At this point:

```text
all payload traversal is complete
all preserved reporting is complete
all prior journal mutations are APPLIED
the final journal mutation is registry / INTENT
the registry write has not occurred
process return code is 93
```

`mutation_count - 1` with `--crash-after-mutations` is not accepted because it may exit before later non-mutating parent-directory preservation records are written.

Journal `preserved` rows are recorded in encounter order. Contract comparison therefore uses `sorted(set(preserved))`.

## Pre-commit requirements

For PREPARED and late APPLYING crashes:

```text
recovery action
  ROLLED_BACK

prior registry
  restored byte-exact
  1 artifact / 714 owned rows

registered state
  complete 714 paths restored

subject
  original modification or unowned sentinel preserved exactly

verify
  modified-owned: exactly the modified leaf is bad / rc 44
  unowned sentinel: clean / rc 0

transaction
  one ROLLED_BACK transaction retained

second recovery
  NOOP_ROLLED_BACK
  no state change
  verify return code remains exact
```

A modified owned leaf is intentionally retained after rollback, so engine verification is expected to fail with exactly that path and return code 44. This is accepted evidence, not a product failure.

## Committed requirements

For COMMITTED crashes:

```text
journal before recovery
  COMMITTED

registry before recovery
  0 artifacts / 0 owned rows

residual state
  exact modified leaf or unowned sentinel
  exact contract-approved parent directories
  no other registered path

recovery action
  FINALIZED_COMMIT

transaction after recovery
  removed

second recovery
  transaction_count 0
  no state change

verify
  empty-registry PASS / rc 0
```

## Identity surfaces

```text
registry-owned identity
  directories: type + mode
  regular files: type + mode + size + SHA256
  symlinks: type + mode + target

residual identity
  modified leaf exact snapshot
  unowned file exact snapshot
  unowned directory recursive exact snapshot
```

A full-prefix portable fingerprint is not the sole identity after intentional residuals exist.

## Published implementation identities

```text
gate3b_preservation_acceptance_support.py
  7ffd6332b394bf60183d62f8f1d16e17021bf153

gate3b_preservation_acceptance_scenarios.py
  8fca079e21b80b0c04a9ab80918cf75b39ea2f8f

run-gate3b-preservation-acceptance.py
  1633c19575ea1a715205f010a048ece0dd1b79d3

verify-gate3b-preservation-acceptance.py
  d5d1dfca5c129cb5b2227cb065bb942c1369268b

run-gate3b-preservation-acceptance-termux.sh
  e70ec7cd61e2ea4baf774f0a6f06a2c329b7f48d
```

## Local validation

```text
Python compile
  PASS

wrapper bash -n
  PASS

actual Gate 3B0 authority and contract identities
  exact

reduced same-topology integration fixture
  happy scenarios 8/8
  crash scenarios 12/12
  scenario checks 29/29
  independent checks 62/62
  raw process cross-check PASS

verify return-code audit
  modified-owned pre-commit rc 44
  unowned pre-commit rc 0
  committed rc 0
```

The reduced fixture validates orchestration and crash-state transitions only. Target authority still requires a complete Termux TGZ using the original 714-entry contract.

## One-command Termux workflow

```text
experiments/stage3c-installed-runtime-lifecycle/run-gate3b-preservation-acceptance-termux.sh
```

It verifies the accepted Gate 3B0 TGZ, freshly extracts it, executes all 20 roots, captures logs synchronously, writes workflow/wrapper status and result-index evidence, and creates a TGZ on PASS or FAIL.

## Accepted evidence

```text
archive
  stage3c-phase5-gate3b-preservation-acceptance-results-20260713-024946.tgz

archive sha256
  0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b

root result-index sha256
  f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9

checks
  29/29 scenario / 62/62 independent / 8 happy / 12 crash
```

Successor boundary:

```text
docs/handoff/PHASE5_GATE3C_ADDON_LIFECYCLE_HANDOFF_20260713.md
```

## Claim boundary

A PASS accepts the frozen preserve-and-report uninstall and recovery contract for runtime-base only. Addon lifecycle, final multi-artifact uninstall, upgrade, and downgrade remain separate gates.

# Stage 3-C Phase 5 Gate 3B: Preserve-and-Report Product Acceptance

> **Status:** ACTIVE — authoritative Termux evidence pending
> **Prerequisite:** frozen Gate 3B0 preservation diagnostic
> **Target:** Termux on Android arm64

## Product question

> Does the accepted corrected engine enforce registered ownership on reinstall while preserving, reporting, and crash-recovering contract-approved residual paths during runtime-base uninstall?

## Frozen input

```text
Gate 3B0 archive
  stage3c-phase5-gate3b0-preservation-diagnostic-results-20260712-211837.tgz

archive sha256
  ed5cb08cc576e74cacac4077cf9c9d7f3164a34913197aae9ef10cc8c113801a

result-index sha256
  7a8e982a44118dac3f232b2fefb578d22bedc0c7d32a6267ab3cd55c5e8deb27

Gate 3B0 checks
  16/16 + 40/40

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

## Frozen policy

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

Gate 3B validates this policy. It does not change it.

## Scenario topology

One fresh corrected-engine seed is copied into 20 inode-separated roots.

Happy paths:

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

Crash subjects:

```text
owned-regular
owned-symlink
unowned-file
unowned-directory
```

Crash boundaries:

```text
prepared
applying-late
committed
```

Totals:

```text
happy roots              8
crash roots             12
scenario checks         29
independent checks      62
```

## Reinstall acceptance

Registered mismatches must produce:

```text
noop 713 / repair 1
mutation count 2
candidate identity restored exactly
registry byte-exact
registry-owned identity restored
verify clean
transaction residue 0
```

Unowned sentinels must produce:

```text
noop 714
mutation count 0
sentinel identity exact
registry byte-exact
registry-owned identity unchanged
verify clean
transaction residue 0
```

## Happy uninstall acceptance

Every uninstall must prove:

```text
operation PASS
registry 1 artifact / 714 rows → 0 / 0
empty-registry verify PASS
transaction residue 0
preserved rows exact
remaining registered paths exact
subject residual identity exact
```

Modified-owned subjects retain the modified leaf plus registered ancestor directories that remain non-empty. Unowned subjects retain the sentinel plus registered ancestor directories that remain non-empty. All other registered paths must be absent.

## Late APPLYING boundary

The late APPLYING crash ordinal is not just the applied mutation count. Failed owned-directory removals record an intent, then remove it from the journal without incrementing applied mutations.

```text
registry_intent_ordinal =
  happy mutation_count
  + count(preserved rows that are registered directories)
```

Invoke:

```text
--crash-after-intents=<registry_intent_ordinal>
```

Required journal shape:

```text
state APPLYING
preserved rows exact after set-normalization
all payload mutations APPLIED
final mutation registry / INTENT
registry still 1 artifact / 714 rows
process rc 93
```

## Recovery acceptance

### PREPARED and late APPLYING

```text
process rc 90 / 93
recovery ROLLED_BACK
registry byte-exact restored
all 714 registered paths restored
original modification or sentinel exact
modified-owned verify reports only the modified leaf
unowned verify clean
one ROLLED_BACK transaction retained
second recovery NOOP_ROLLED_BACK
second recovery changes nothing
```

### COMMITTED

```text
process rc 92
journal COMMITTED
registry already 0 / 0
accepted residual state exact
recovery FINALIZED_COMMIT
transaction removed
second recovery transaction_count 0
empty-registry verify PASS
```

## Identity boundary

Registry-owned identity and residual identity are separate evidence surfaces.

```text
registered directory
  type + mode

registered regular
  type + mode + size + SHA256

registered symlink
  type + mode + target

unowned directory residual
  recursive exact snapshot
```

A full-prefix portable fingerprint is not the sole identity after intentional residuals exist.

## One-command Termux run

```sh
cd "$HOME/projects/cpython-android-cli" && \
git fetch origin agent/phase5-gate3b-product-acceptance && \
git switch --detach origin/agent/phase5-gate3b-product-acceptance && \
bash \
  experiments/stage3c-installed-runtime-lifecycle/run-gate3b-preservation-acceptance-termux.sh
```

The wrapper verifies and extracts the accepted Gate 3B0 TGZ, runs all scenarios, captures logs synchronously, writes workflow/wrapper status and result-index evidence, and creates a TGZ on PASS or FAIL.

## Expected markers

```text
GATE3B_REINSTALL_REGRESSIONS=4/4 PASS
GATE3B_HAPPY_UNINSTALL=4/4 PASS
GATE3B_CRASH_RECOVERY=12/12 PASS
GATE3B_SCENARIO_VERIFICATION=29/29 PASS
GATE3B_INDEPENDENT_VERIFICATION=62/62 PASS
STAGE3C_PHASE5_GATE3B_PRESERVATION_ACCEPTANCE=PASS

TERMUX_EVIDENCE_ARCHIVE=...
TERMUX_EVIDENCE_ARCHIVE_SHA256=...
TERMUX_EVIDENCE_ARCHIVE_SIZE=...
TERMUX_WORKFLOW_RETURN_CODE=0
```

## Claim boundary

A PASS accepts preserve-and-report reinstall, uninstall, and crash recovery for runtime-base. Addon lifecycle, final multi-artifact uninstall, upgrade, and downgrade remain separate gates.

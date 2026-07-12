# Phase 5 Gate 3B Preserve-and-Report Product Acceptance Handoff — 2026-07-12

> **Status:** DESIGNING
> **Prerequisite:** frozen Gate 3B0 preservation diagnostic
> **Target:** Termux on Android arm64

## Frozen prerequisite

```text
Gate 3B0 archive sha256
  ed5cb08cc576e74cacac4077cf9c9d7f3164a34913197aae9ef10cc8c113801a

Gate 3B0 result-index sha256
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

Subjects:

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

Total crash scenarios:

```text
4 × 3 = 12
```

## Pre-commit requirements

For PREPARED and late APPLYING crashes:

```text
recovery action ROLLED_BACK
prior registry restored exactly
1 artifact / 714 owned rows
complete registered state restored
original modification or sentinel preserved exactly
modified-owned verify bad path exactly the modified leaf
unowned-sentinel verify clean
one ROLLED_BACK transaction retained
second recovery NOOP_ROLLED_BACK
second recovery changes nothing
```

The late APPLYING boundary must be derived from a successful uninstall `mutation_count` and use:

```text
--crash-after-intents=<happy uninstall mutation_count>
```

At this point all payload traversal and `preserved` reporting are complete. The final registry mutation exists as an `INTENT`, but the registry write has not occurred. The expected process return code is 93.

Using `mutation_count - 1` with `--crash-after-mutations` is not accepted because the process exits immediately after the last payload mutation and may do so before later non-mutating parent-directory preservation records are written.

## Committed requirements

For COMMITTED crashes:

```text
journal state COMMITTED before recovery
registry already 0 artifacts / 0 owned rows
accepted residual state already exact
recovery action FINALIZED_COMMIT
transaction directory removed
second recovery transaction_count 0
empty-registry verify PASS
```

Modified-owned scenarios must retain exactly the modified leaf plus contract-approved parent directories. Unowned scenarios must retain the exact sentinel plus contract-approved parent directories and no originally registered leaf.

## Identity surfaces

```text
registry-owned identity
  type/mode for directories
  type/mode/size/SHA256 for regular files
  type/mode/target for symlinks

residual identity
  modified leaf exact snapshot
  unowned file exact snapshot
  unowned directory recursive exact snapshot
```

A full-prefix portable fingerprint is not the sole identity after intentional residuals exist.

## Evidence policy

Gate 3B product acceptance requires a complete independently inspected Termux TGZ. The target-only workflow must use one wrapper that verifies the accepted Gate 3B0 TGZ, performs fresh extraction, executes all scenarios, captures logs synchronously, writes status and result-index evidence, and packages a TGZ on PASS or FAIL.

No target command is authoritative until the workflow implementation, independent verifier, and one-command wrapper have completed repository review and static validation.

## Claim boundary

A PASS will accept the frozen preserve-and-report uninstall and recovery contract for runtime-base only. Addon lifecycle, final multi-artifact uninstall, upgrade, and downgrade remain separate gates.

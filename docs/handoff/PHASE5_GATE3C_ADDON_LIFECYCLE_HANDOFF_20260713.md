# Phase 5 Gate 3C Addon Lifecycle and Dependency Enforcement Handoff — 2026-07-13

> **Status:** ACTIVE — design and target evidence pending
> **Prerequisite:** frozen Gate 3B preserve-and-report product acceptance
> **Target:** Termux on Android arm64

## Frozen prerequisite

```text
Gate 3B archive
  stage3c-phase5-gate3b-preservation-acceptance-results-20260713-024946.tgz

archive sha256
  0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b

root result-index sha256
  f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9

scenario / independent checks
  29/29 / 62/62 PASS

happy / crash topology
  8/8 / 12/12 PASS
```

## Gate 3C question

> Can the frozen development-addon and test-addon artifacts compose over runtime-base, enforce dependency order and ownership boundaries, recover transactionally, and leave runtime-base exact and functional after addon removal?

## Required lifecycle

```text
install runtime-base
install development-addon
install test-addon
reject removal or installation orders that violate declared dependencies
remove test-addon
remove development-addon
revalidate runtime-base
```

## Required evidence surfaces

```text
accepted archive and manifest identities for all three artifacts
registry artifact and owned-path transitions after every operation
exact addon-owned path identity and unaffected-owner identity
shared-path collision-policy decisions
rejected dependency operations with zero payload, registry, or transaction mutation
crash recovery at PREPARED, late APPLYING, and COMMITTED where applicable
second-recovery idempotence
runtime-base verification and behavioral probes after addon removal
archive safety, root result-index recomputation, raw process cross-checks, canonical JSON
```

## Policy boundaries

Gate 3C may enforce dependencies already represented by frozen manifests and the installation contract. It must not silently invent final-runtime-uninstall policy, broaden preserve-and-report semantics, or claim upgrade/downgrade.

```text
Gate 3D
  final multi-artifact/runtime-base uninstall and ownership boundary

Gate 4
  upgrade and downgrade with a second frozen product identity
```

## Execution rule

A future target workflow must use one Termux wrapper that verifies accepted inputs, extracts them freshly, captures stdout/stderr synchronously, writes machine status and a root result-index, and emits a new `.tar.zst` archive on PASS or FAIL. Historical `.tgz` inputs remain immutable and valid.

## Immediate repository task

Design the Gate 3C matrix and verifier against the frozen runtime-base, development-addon, and test-addon manifests before authorizing any target claim. Local fixtures may validate orchestration, but only a complete independently inspected Termux archive can close Gate 3C.

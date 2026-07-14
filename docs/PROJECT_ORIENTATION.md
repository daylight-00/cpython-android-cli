# Project Orientation

This is the minimum conceptual model required before acting on `HW-T/cpython-android-cli`.

## Identity

The project is a CLI adaptation of an upstream CPython Android build for Termux, with uv integration and an evidence-driven distribution lifecycle. It preserves normal CPython CLI behavior while adapting launcher, discovery, packaging, installation, recovery, and ownership boundaries for the Android/Termux environment.

It is not a Termux Python replacement, a general-purpose distribution, a CPython fork, a synthetic version relabel, or an upgrade runner built before both products are independently frozen.

## Governing method

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

Use the smallest justified dependency, mutation, helper, exception, and claim. A success in one domain never proves another domain.

## Authority hierarchy

```text
1. complete independently inspected Termux target evidence
2. frozen repository contracts and exact identities
3. independent local reconstruction
4. static source analysis
5. assumptions or chat memory
```

A console `PASS`, filename, or verifier exit code alone never closes a target gate.

## Claim and non-reopening discipline

Always state what a result proves and does not prove. Keep runtime behavior, native closure, source/build provenance, archive identity, ownership, transaction/recovery, and consumer integration separate.

Do not silently reopen frozen launcher/PyConfig architecture, first-product identities, ownership policy, addon dependency policy, final-uninstall policy, or accepted transaction/recovery behavior. A policy change needs its own authority decision.

## Product model

A complete product has three independently owned artifacts:

```text
runtime-base
development-addon
test-addon
```

The addons require the exact runtime-base. Product identity includes exact archives, manifests, product lock, ownership contract, provenance, native closure, runtime behavior, and SHA-256 identities—not only a version string.

## Current boundary at this handoff

```text
A1 selection/design                 FROZEN PASS
A2 inputs/toolchain                 FROZEN PASS
A3 clean upstream Android replay    FROZEN PASS
A4 three-artifact materialization   RESULT EXISTS — UNAUDITED
A5 standalone validation            BLOCKED
A6 independent audit/freeze         pending
```

The immediate task is to audit the existing A4 result. Do not rebuild or advance A5 unless that exact result requires it.

## Authoritative repository reading path

After verifying the repository identity, read only as needed:

```text
docs/PROJECT_CONTEXT_STAGE3C.md
docs/stages/STAGE3C_PHASE5_SCOPE.md
docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md
docs/handoff/2026-07-14-gate4a-a4-pending-result.md
experiments/stage3c-gate4-second-product-authority/GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN.md
```

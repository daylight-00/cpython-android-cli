# Epoch 2 Upstream-Thin Program Plan

> **Lifecycle:** historical completed plan — closed by E2-CLOSURE
> **Decision authorities:** ADR-0006 and ADR-0007
> **Detailed work:** [`EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)
> **Live progress:** [`../current/STATE.json`](../current/STATE.json)

## Objective

Produce sufficient evidence and producer-independent contracts for an upstream-derived, Astral-structured Android/Bionic standalone CPython product. Epoch 2 determines feasibility and boundaries; Epoch 3 performs feature and policy selection; Epoch 4 may implement a full source producer.

## Work sequence

```text
E2-R1  exact official upstream control and Astral artifact prototype
E2-R2  loader, relocation, launcher, getpath, sysconfig, and SDK evidence
E2-R3  Android data policy and capability matrices
E2-R4  platform-floor and update-portability evidence
E2-R5  controlled API-level source-equivalent comparisons
E2-R6  evidence export, completion gates, and Epoch 3 product seed
```

## Mandatory product invariants

- verified direct derivation from pinned upstream products;
- enumerated local byte mutations;
- Bionic and Android-public native closure without Termux native providers;
- fresh-extraction execution and accepted whole-prefix relocation;
- no project-required loader bootstrap workaround in the selected product;
- truthful Astral-compatible archive and metadata structure;
- exact provenance, licenses, checksums, and qualification identities;
- explicit target, ABI, minimum-platform, and consumer boundaries.

## Evidence and selection rule

```text
Epoch 2 evidence
  pass / bounded-pass / fail / unavailable
        ↓
Epoch 3 selection
  adopt / adopt-with-redesign / exclude / defer-to-epoch4
```

Optional capabilities—including pip, trust and timezone data, SDK modes, multiprocessing, venv cases, uv integration, optional artifacts, and API-level-derived inputs—require explicit product selection even when experiments pass.

## Plan update rule

This document changes only when the work decomposition, ordering, mandatory invariants, or acceptance model changes. Current completion, immediate execution, blockers, and accepted result identities belong to `STATE.json` and frozen evidence.

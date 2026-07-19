# Component ownership across Epoch 2, Epoch 3, and Epoch 4

> **Status:** recalibrated by ADR-0006 and ADR-0007

## Permanent research laboratory — `cpython-android-cli`

Owns:

- historical experiments, failures, contracts, evidence, and handoffs;
- upstream and Android adaptation research;
- API-level comparisons and source-producer experiments;
- UT-0 through UT-7 evidence and E2-G1 through E2-G8 closure;
- rejected alternatives and architecture decisions;
- the future Epoch 4 full source producer;
- raw external research inputs and adjudication records.

The laboratory produces evidence dispositions and product-selection inputs. It does not automatically authorize Epoch 3 inclusion.

## Epoch 3 clean release repository

Owns:

- pinned Python.org Android input discovery and checksums;
- inherited BeeWare dependency identity;
- the complete selection register;
- project launcher and bounded standalone adaptation;
- deterministic artifact transformation;
- selected Astral-structured `full`, `install_only`, `install_only_stripped`, and optional products;
- selected runtime, SDK, CA, timezone, pip, uv, venv, and capability surface;
- metadata, release index, checksums, licenses, qualification, CI, and releases;
- consumer documentation and maintenance of project-owned delta and bundled data.

Every selectable item must be marked `adopt`, `adopt-with-redesign`, `exclude`, or `defer-to-epoch4`. Passing Epoch 2 evidence is not automatic inclusion.

Does not own:

- CPython source production;
- dependency source recipes;
- independent NDK/API/linkage policy without a separate product decision;
- producer PGO/LTO.

## Epoch 4 source producer

Owns:

- CPython and dependency source inputs;
- NDK/toolchain and build recipes;
- Android patches and extension configuration;
- linkage policy, optimization, reproducibility, and source attestations;
- full source-build artifacts and install-only derivation.

It must preserve the selected Epoch 3 consumer-facing contract unless a separate ADR changes the product.

## Consumer boundary

Termux, uv, direct extraction, adb, root, installer/lifecycle tooling, and later APK consumers consume released artifacts and versioned metadata. They do not consume producer workspaces.

Termux is a primary execution profile, not an ELF ABI provider.

## Historical ownership

Existing Epoch 1 and early Epoch 2 paths retain their original authority. This document changes future responsibility; it does not relabel prior evidence.

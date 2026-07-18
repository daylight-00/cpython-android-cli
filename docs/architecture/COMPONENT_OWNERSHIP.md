# Component ownership across Epoch 2, Epoch 3, and Epoch 4

> **Status:** recalibrated by ADR-0006

## Permanent research laboratory — `cpython-android-cli`

Owns:

- historical experiments, failures, contracts, evidence, and handoffs;
- upstream and Android adaptation research;
- API-level comparisons and source-producer experiments;
- rejected alternatives and architecture decisions;
- the future Epoch 4 full source producer;
- raw external research inputs and adjudication records.

## Epoch 3 clean release repository

Owns:

- pinned Python.org Android input discovery and checksums;
- inherited BeeWare dependency identity;
- project launcher and bounded standalone adaptation;
- deterministic artifact transformation;
- Astral-structured `full`, `install_only`, and `install_only_stripped` products;
- metadata, release index, checksums, licenses, qualification, CI, and releases;
- uv-facing and direct-consumer documentation;
- maintenance of project-owned delta.

Does not own:

- CPython source production;
- dependency source recipes;
- independent NDK/API/linkage policy;
- producer PGO/LTO.

## Epoch 4 source producer

Owns:

- CPython and dependency source inputs;
- NDK/toolchain and build recipes;
- Android patches and extension configuration;
- linkage policy, optimization, reproducibility, and source attestations;
- full source-build artifacts and install-only derivation.

It must preserve the Epoch 3 consumer-facing contract unless a separate ADR changes the product.

## Consumer boundary

Termux, uv, direct extraction, adb, root, installer/lifecycle tooling, and later APK consumers consume released artifacts and versioned metadata. They do not consume producer workspaces.

Termux is a primary execution profile, not an ELF ABI provider.

## Historical ownership

Existing Epoch 1 and early Epoch 2 paths retain their original authority. This document changes future responsibility; it does not relabel prior evidence.

# Epoch 4 Charter: Full Astral-like Android source producer

> **Status:** PLANNED
> **Host repository:** `cpython-android-cli` research laboratory
> **Output contract:** consumer-equivalent to Epoch 3

## Mission

Build a complete Android/Bionic source producer whose build-system and artifact architecture primarily follow Astral's `python-build-standalone`, while preserving the accepted Epoch 3 product surface.

## Source-production ownership

Epoch 4 owns:

- CPython source acquisition and patch provenance;
- BeeWare dependency source revisions and recipe adaptation;
- pinned NDK/toolchain materialization;
- host/target build separation;
- extension-module configuration and generated metadata;
- static/shared and `libpython` linkage decisions;
- reproducible build profiles;
- PGO/LTO where justified;
- source, binary, license, SBOM, and build attestations;
- canonical full source-build archives and install-only derivation.

## Structural reference

The producer should resemble Astral structurally, not merely conceptually: target configuration, dependency graph, extension metadata, profile vocabulary, full/install-only transformations, machine-readable metadata, and release assembly should follow Astral where Android permits.

Android-only differences must be explicit, reviewed, and verified.

## Equivalence rule

Epoch 4 may differ from Epoch 3 in source-production provenance and retained build material. It should not silently differ in:

- target and API identity;
- archive names, roots, and runtime paths;
- standard-library and extension surface;
- dependency ABI and wheel behavior;
- fresh-extraction relocation;
- uv and direct-consumer contract;
- metadata semantics and release qualification.

A difference in these surfaces is a product architecture change and requires a separate ADR.

## Role of Epoch 3

Epoch 3 is the behavioral and distribution oracle. Epoch 4 replaces the upstream binary producer with a project-owned source producer while retaining the accepted product contract.
